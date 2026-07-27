"""在锁定 Docling 容器内批量生成候选重处理 payload。"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import shutil
import tempfile

from bgpkb.ingestion.canonicalize_candidate import _load_source_manifest
from bgpkb.ingestion.cleaning_v2.contracts import atomic_write_json
from bgpkb.ingestion.cleaning_v2.runtime_pipeline import _default_docling_parser


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _suffix(mime_type: str) -> str:
    fixed = {
        "text/html": ".html",
        "application/pdf": ".pdf",
        "text/plain": ".txt",
        "text/markdown": ".md",
        "application/yaml": ".yaml",
        "text/yaml": ".yaml",
    }
    return fixed.get(mime_type) or mimetypes.guess_extension(mime_type) or ".bin"


def _atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            with source.open("rb") as source_handle:
                shutil.copyfileobj(source_handle, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def run_payload_worker(
    *,
    plan_path: Path,
    source_manifest_path: Path,
    source_store_root: Path,
    output_root: Path,
    input_work_root: Path,
    receipt_path: Path,
    runtime_evidence_path: Path,
    release_id: str,
    parser=_default_docling_parser,
) -> dict:
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    runtime_evidence = json.loads(
        Path(runtime_evidence_path).read_text(encoding="utf-8")
    )
    _manifest, snapshots = _load_source_manifest(
        source_manifest_path, Path(source_store_root).resolve()
    )
    if (
        plan.get("schema_version") != "docling_reprocess_plan_v1"
        or plan.get("release_id") != release_id
        or plan.get("status") != "ready"
    ):
        raise ValueError("Docling 重处理计划身份或状态非法")
    rows = plan.get("sources")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Docling 重处理计划没有来源")

    output_root = Path(output_root).resolve()
    input_root = Path(input_work_root).resolve()
    input_root.mkdir(parents=True, exist_ok=True)
    documents = []
    for row in rows:
        source_id = str(row.get("source_id") or "")
        snapshot = snapshots.get(source_id)
        record = {
            "source_id": source_id,
            "status": "failed",
            "source_sha256": row.get("object_digest"),
            "payload_path": f"{source_id}.json",
            "payload_sha256": None,
            "parser_version": "2.107.0",
            "pipeline_revision": runtime_evidence["runtime"]["pipeline_revision"],
            "diagnostics": [],
        }
        try:
            if not snapshot or snapshot["object_digest"] != row.get("object_digest"):
                raise ValueError("计划与 source snapshot hash 不一致")
            source_path = (
                Path(source_store_root).resolve() / snapshot["object_path"]
            ).resolve()
            if not source_path.is_file():
                raise ValueError("source snapshot object 缺失")
            before = _sha256(source_path)
            if before != snapshot["object_digest"]:
                raise ValueError("source snapshot object hash 不匹配")
            named_input = input_root / f"{source_id}{_suffix(snapshot['mime_type'])}"
            _atomic_copy(source_path, named_input)
            payload = parser(named_input)
            payload_path = output_root / record["payload_path"]
            atomic_write_json(payload_path, payload, indent=2)
            if _sha256(source_path) != before:
                raise ValueError("source snapshot 在解析期间发生变化")
            record["payload_sha256"] = _sha256(payload_path)
            record["status"] = "complete"
        except Exception as exc:
            record["diagnostics"] = [
                {
                    "code": "docling_conversion_failed",
                    "detail": str(exc) or exc.__class__.__name__,
                }
            ]
        documents.append(record)

    failed = sum(row["status"] != "complete" for row in documents)
    result = {
        "schema_version": "docling_payload_manifest_v1",
        "release_id": release_id,
        "status": "complete" if not failed else "failed",
        "runtime": runtime_evidence["runtime"],
        "model_evidence": runtime_evidence["preflight"].get("models", []),
        "summary": {
            "requested": len(documents),
            "complete": len(documents) - failed,
            "failed": failed,
        },
        "documents": documents,
    }
    atomic_write_json(Path(receipt_path), result, indent=2)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-store", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--input-work-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--runtime-evidence", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_payload_worker(
            plan_path=args.plan,
            source_manifest_path=args.source_manifest,
            source_store_root=args.source_store,
            output_root=args.output_root,
            input_work_root=args.input_work_root,
            receipt_path=args.receipt,
            runtime_evidence_path=args.runtime_evidence,
            release_id=args.release_id,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc))
        return 2
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "complete" else 3


if __name__ == "__main__":
    raise SystemExit(main())
