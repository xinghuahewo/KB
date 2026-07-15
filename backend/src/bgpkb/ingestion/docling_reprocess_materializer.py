"""把锁定 Docling JSON 输出物化为严格 Canonical Document v2。"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from bgpkb.ingestion.canonical_contract import validate_canonical_document
from bgpkb.ingestion.canonical_migration import upgrade_legacy_canonical_metadata
from bgpkb.ingestion.canonicalize_candidate import _load_source_manifest
from bgpkb.ingestion.cleaning_v2.contracts import atomic_write_json
from bgpkb.ingestion.cleaning_v2.docling_adapter import adapt_docling_document


class DoclingReprocessError(ValueError):
    """Docling 重处理输入、运行时或闭包不满足锁定契约。"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _validate_runtime(runtime: dict) -> dict:
    required = {
        "pipeline_revision",
        "parser_version",
        "image",
        "image_digest",
        "gpu_index",
        "device",
        "network",
    }
    missing = sorted(required - set(runtime))
    if missing:
        raise DoclingReprocessError("Docling runtime 缺少字段：" + ", ".join(missing))
    if runtime["gpu_index"] != 1 or runtime["device"] != "nvidia.com/gpu=1":
        raise DoclingReprocessError("Docling 重处理必须使用 GPU 1")
    if runtime["network"] != "none":
        raise DoclingReprocessError("Docling 重处理必须使用 network=none")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(runtime["image_digest"])):
        raise DoclingReprocessError("Docling image digest 必须是不可变 SHA-256")
    for field in ("pipeline_revision", "parser_version", "image"):
        if not isinstance(runtime[field], str) or not runtime[field]:
            raise DoclingReprocessError(f"Docling runtime {field} 非法")
    return {field: runtime[field] for field in sorted(required)}


def materialize_docling_reprocess(
    *,
    source_manifest_path: Path,
    source_store_root: Path,
    payload_root: Path,
    output_root: Path,
    manifest_path: Path,
    source_ids: list[str],
    release_id: str,
    runtime_identity: dict,
) -> dict:
    """把容器导出的 Docling payload 与当前 snapshot 严格绑定。"""

    runtime = _validate_runtime(dict(runtime_identity))
    if not source_ids or len(set(source_ids)) != len(source_ids):
        raise DoclingReprocessError("source_ids 必须是非空且不重复的列表")
    source_manifest_path = Path(source_manifest_path).resolve()
    source_store_root = Path(source_store_root).resolve()
    payload_root = Path(payload_root).resolve()
    output_root = Path(output_root).resolve()
    manifest_path = Path(manifest_path).resolve()
    _manifest, snapshots = _load_source_manifest(
        source_manifest_path, source_store_root
    )
    unknown = sorted(set(source_ids) - set(snapshots))
    if unknown:
        raise DoclingReprocessError("重处理来源未登记：" + ", ".join(unknown))

    output_root.mkdir(parents=True, exist_ok=True)
    documents: list[dict] = []
    for source_id in sorted(source_ids):
        payload_path = payload_root / f"{source_id}.json"
        if not payload_path.is_file():
            raise DoclingReprocessError(f"缺少 Docling payload：{source_id}")
        try:
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise DoclingReprocessError(
                f"Docling payload 不可读：{source_id}: {exc}"
            ) from exc
        if not isinstance(payload, dict):
            raise DoclingReprocessError(f"Docling payload 必须是对象：{source_id}")
        snapshot = snapshots[source_id]
        legacy = adapt_docling_document(
            payload,
            {
                "doc_id": source_id,
                "source_path": snapshot["object_path"],
                "source_sha256": str(snapshot["object_digest"]).removeprefix("sha256:"),
            },
            {
                "parser": "docling",
                "docling_version": runtime["parser_version"],
                "docling": runtime["parser_version"],
                "pipeline_revision": runtime["pipeline_revision"],
                "image": runtime["image"],
                "image_digest": runtime["image_digest"],
                "gpu_index": runtime["gpu_index"],
                "device": runtime["device"],
                "network": runtime["network"],
            },
            {},
        )
        strict = upgrade_legacy_canonical_metadata(legacy, snapshot)
        errors = validate_canonical_document(
            strict, known_snapshot_ids={snapshot["snapshot_id"]}
        )
        if errors:
            raise DoclingReprocessError(
                f"重处理 Canonical 校验失败：{source_id}: {'; '.join(errors)}"
            )
        output_path = output_root / f"{source_id}.json"
        atomic_write_json(output_path, strict, indent=2)
        documents.append(
            {
                "source_id": source_id,
                "snapshot_id": snapshot["snapshot_id"],
                "object_digest": snapshot["object_digest"],
                "payload_path": payload_path.relative_to(payload_root).as_posix(),
                "payload_sha256": _sha256(payload_path),
                "canonical_path": output_path.relative_to(manifest_path.parent).as_posix(),
                "canonical_sha256": _sha256(output_path),
                "block_count": len(strict["blocks"]),
                "text_char_count": sum(
                    len(str(block.get("cleaned_text") or ""))
                    for block in strict["blocks"]
                ),
            }
        )

    result = {
        "schema_version": "docling_reprocess_manifest_v1",
        "release_id": release_id,
        "status": "complete",
        "generated_at": _utc_now(),
        "source_ingest_manifest_sha256": _sha256(source_manifest_path),
        "runtime": runtime,
        "summary": {
            "requested": len(source_ids),
            "materialized": len(documents),
            "failed": 0,
        },
        "documents": documents,
    }
    atomic_write_json(manifest_path, result, indent=2)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="把锁定 Docling JSON 输出物化为严格 Canonical Document v2"
    )
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-store", type=Path, required=True)
    parser.add_argument("--payload-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--source-id", action="append", dest="source_ids", required=True)
    parser.add_argument("--pipeline-revision", default="docling-html-reprocess-v1")
    parser.add_argument("--parser-version", default="2.107.0")
    parser.add_argument("--image", required=True)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--gpu-index", type=int, default=1)
    parser.add_argument("--device", default="nvidia.com/gpu=1")
    parser.add_argument("--network", default="none")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = materialize_docling_reprocess(
            source_manifest_path=args.source_manifest,
            source_store_root=args.source_store,
            payload_root=args.payload_root,
            output_root=args.output_root,
            manifest_path=args.manifest,
            source_ids=args.source_ids,
            release_id=args.release_id,
            runtime_identity={
                "pipeline_revision": args.pipeline_revision,
                "parser_version": args.parser_version,
                "image": args.image,
                "image_digest": args.image_digest,
                "gpu_index": args.gpu_index,
                "device": args.device,
                "network": args.network,
            },
        )
    except DoclingReprocessError as exc:
        print(str(exc))
        return 2
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
