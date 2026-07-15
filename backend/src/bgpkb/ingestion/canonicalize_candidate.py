"""从冻结 Canonical 语料构建候选 Canonical Document v2 闭包。"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

import yaml

from bgpkb import paths
from bgpkb.ingestion.canonical_contract import validate_canonical_document
from bgpkb.ingestion.canonical_migration import (
    _legacy_metadata_upgrade_safe,
    upgrade_legacy_canonical_metadata,
)
from bgpkb.ingestion.cleaning_v2.contracts import atomic_write_json


DEFAULT_REPROCESS_POLICY = paths.CONFIG_DIR / "canonical_reprocess_policy_v1.yaml"


class CanonicalizeCandidateError(ValueError):
    """候选 Canonical 输入、路由或闭包不满足生产约束。"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_json(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _safe_relative_path(value: str, *, field: str) -> Path:
    path = Path(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise CanonicalizeCandidateError(f"{field} 不是受控相对路径：{value}")
    return path


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


def load_reprocess_policy(path: Path = DEFAULT_REPROCESS_POLICY) -> dict:
    path = Path(path)
    try:
        policy = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise CanonicalizeCandidateError(f"无法读取 Canonical 重处理策略：{exc}") from exc
    if not isinstance(policy, dict) or policy.get("schema_version") != "canonical_reprocess_policy_v1":
        raise CanonicalizeCandidateError("Canonical 重处理策略 schema_version 非法")
    if not isinstance(policy.get("policy_version"), str) or not policy["policy_version"]:
        raise CanonicalizeCandidateError("Canonical 重处理策略缺少 policy_version")
    affected = policy.get("affected_source_ids")
    if not isinstance(affected, list) or any(not isinstance(item, str) or not item for item in affected):
        raise CanonicalizeCandidateError("affected_source_ids 必须是 source_id 数组")
    if len(set(affected)) != len(affected):
        raise CanonicalizeCandidateError("affected_source_ids 不得重复")
    docling = policy.get("docling")
    if not isinstance(docling, dict):
        raise CanonicalizeCandidateError("Canonical 重处理策略缺少 Docling 路由")
    if docling.get("gpu_index") != 1 or docling.get("device") != "nvidia.com/gpu=1":
        raise CanonicalizeCandidateError("Docling 重处理必须固定路由到服务器 GPU 1")
    if docling.get("network") != "none":
        raise CanonicalizeCandidateError("Docling 重处理必须使用 network=none")
    for field in ("ssh_target", "image", "image_digest"):
        if not isinstance(docling.get(field), str) or not docling[field]:
            raise CanonicalizeCandidateError(f"Docling 路由缺少 {field}")
    pipeline_revision = docling.get("pipeline_revision", "docling-html-reprocess-v1")
    if not isinstance(pipeline_revision, str) or not pipeline_revision:
        raise CanonicalizeCandidateError("Docling 路由缺少 pipeline_revision")
    docling["pipeline_revision"] = pipeline_revision
    return policy


def _load_reprocess_manifest(
    path: Path | None,
    *,
    source_manifest_path: Path,
    frozen_canonical_root: Path,
    release_id: str,
    policy: dict,
) -> dict[str, dict]:
    affected = set(policy["affected_source_ids"])
    if not affected or path is None or not Path(path).is_file():
        return {}
    path = Path(path).resolve()
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CanonicalizeCandidateError(
            f"Docling reprocess manifest 不可读：{exc}"
        ) from exc
    if (
        manifest.get("schema_version") != "docling_reprocess_manifest_v1"
        or manifest.get("status") != "complete"
        or manifest.get("release_id") != release_id
    ):
        raise CanonicalizeCandidateError("Docling reprocess manifest 身份或状态非法")
    expected_source_hash = "sha256:" + _sha256_file(source_manifest_path)
    if manifest.get("source_ingest_manifest_sha256") != expected_source_hash:
        raise CanonicalizeCandidateError(
            "Docling reprocess manifest 未绑定当前 source-ingest"
        )
    route = policy["docling"]
    expected_runtime = {
        "pipeline_revision": route["pipeline_revision"],
        "parser_version": "2.107.0",
        "image": route["image"],
        "image_digest": route["image_digest"],
        "gpu_index": route["gpu_index"],
        "device": route["device"],
        "network": route["network"],
    }
    if manifest.get("runtime") != expected_runtime:
        raise CanonicalizeCandidateError(
            "Docling reprocess runtime 与锁定策略不一致"
        )
    rows = manifest.get("documents")
    if not isinstance(rows, list):
        raise CanonicalizeCandidateError("Docling reprocess documents 非法")
    by_source: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("source_id"), str):
            raise CanonicalizeCandidateError("Docling reprocess document entry 非法")
        source_id = row["source_id"]
        if source_id in by_source:
            raise CanonicalizeCandidateError(
                f"Docling reprocess source_id 重复：{source_id}"
            )
        relative = _safe_relative_path(
            str(row.get("canonical_path") or ""),
            field="reprocess canonical_path",
        )
        canonical_path = (path.parent / relative).resolve()
        if canonical_path.parent != frozen_canonical_root:
            raise CanonicalizeCandidateError(
                f"Docling reprocess canonical path 越界：{source_id}"
            )
        if not canonical_path.is_file():
            raise CanonicalizeCandidateError(
                f"Docling reprocess Canonical 缺失：{source_id}"
            )
        if row.get("canonical_sha256") != "sha256:" + _sha256_file(canonical_path):
            raise CanonicalizeCandidateError(
                f"Docling reprocess Canonical hash 不匹配：{source_id}"
            )
        by_source[source_id] = {**row, "resolved_path": canonical_path}
    extras = sorted(set(by_source) - affected)
    if extras:
        raise CanonicalizeCandidateError(
            "Docling reprocess manifest 包含未授权来源：" + ", ".join(extras)
        )
    return by_source


def _load_source_manifest(path: Path, source_store_root: Path) -> tuple[dict, dict[str, dict]]:
    try:
        manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CanonicalizeCandidateError(f"无法读取 source-ingest manifest：{exc}") from exc
    if manifest.get("schema_version") != "source_ingest_manifest_v1" or manifest.get("status") != "complete":
        raise CanonicalizeCandidateError("canonicalize 只接受 complete 的 source-ingest manifest")
    rows = manifest.get("sources")
    if not isinstance(rows, list) or not rows:
        raise CanonicalizeCandidateError("source-ingest manifest 没有来源")
    snapshots: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("status") not in {"imported", "downloaded", "not_modified"}:
            raise CanonicalizeCandidateError(f"来源没有可用终态：{row!r}")
        source_id = row.get("source_id")
        snapshot = row.get("snapshot")
        if not isinstance(source_id, str) or not isinstance(snapshot, dict):
            raise CanonicalizeCandidateError("来源记录缺少 source_id 或 snapshot")
        if source_id in snapshots:
            raise CanonicalizeCandidateError(f"source_id 重复：{source_id}")
        if snapshot.get("source_id") != source_id:
            raise CanonicalizeCandidateError(f"snapshot source_id 不闭合：{source_id}")
        object_path = source_store_root / _safe_relative_path(
            str(snapshot.get("object_path") or ""), field="snapshot object_path"
        )
        if not object_path.is_file():
            raise CanonicalizeCandidateError(f"snapshot object 缺失：{source_id}")
        actual_digest = _sha256_file(object_path)
        if snapshot.get("object_digest") != f"sha256:{actual_digest}":
            raise CanonicalizeCandidateError(f"snapshot object hash 不匹配：{source_id}")
        if snapshot.get("byte_size") != object_path.stat().st_size:
            raise CanonicalizeCandidateError(f"snapshot object byte_size 不匹配：{source_id}")
        snapshots[source_id] = snapshot
    return manifest, snapshots


def _copy_assets(
    document: dict,
    *,
    source_id: str,
    frozen_assets_root: Path,
    output_assets_root: Path,
) -> int:
    copied = 0
    for asset in document.get("assets", []):
        relative = _safe_relative_path(str(asset.get("path") or ""), field="asset path")
        source = frozen_assets_root / source_id / relative
        if not source.is_file():
            raise CanonicalizeCandidateError(f"asset 缺失：{source_id}/{relative.as_posix()}")
        actual = _sha256_file(source)
        if asset.get("sha256") != actual:
            raise CanonicalizeCandidateError(
                f"asset hash 不匹配：{source_id}/{relative.as_posix()}"
            )
        target = output_assets_root / source_id / relative
        if target.is_file() and _sha256_file(target) == actual:
            continue
        _atomic_copy(source, target)
        copied += 1
    return copied


def run_candidate_canonicalize(
    *,
    source_manifest_path: Path,
    source_store_root: Path,
    frozen_canonical_root: Path,
    frozen_assets_root: Path,
    output_root: Path,
    output_assets_root: Path,
    manifest_path: Path,
    reprocess_policy_path: Path = DEFAULT_REPROCESS_POLICY,
    reprocess_manifest_path: Path | None = None,
    release_id: str,
) -> dict:
    source_manifest_path = Path(source_manifest_path)
    source_store_root = Path(source_store_root).resolve()
    frozen_canonical_root = Path(frozen_canonical_root).resolve()
    frozen_assets_root = Path(frozen_assets_root).resolve()
    output_root = Path(output_root).resolve()
    output_assets_root = Path(output_assets_root).resolve()
    manifest_path = Path(manifest_path).resolve()
    policy = load_reprocess_policy(reprocess_policy_path)
    source_manifest, snapshots = _load_source_manifest(source_manifest_path, source_store_root)
    affected_source_ids = set(policy["affected_source_ids"])
    unknown_affected = sorted(affected_source_ids - set(snapshots))
    if unknown_affected:
        raise CanonicalizeCandidateError(
            "重处理策略引用未登记来源：" + ", ".join(unknown_affected)
        )
    reprocessed = _load_reprocess_manifest(
        reprocess_manifest_path,
        source_manifest_path=source_manifest_path,
        frozen_canonical_root=frozen_canonical_root,
        release_id=release_id,
        policy=policy,
    )
    unexpected_inputs = sorted(
        path.stem
        for path in frozen_canonical_root.glob("*.json")
        if path.name != "docling_reprocess_manifest_v1.json"
        and path.stem not in snapshots
    )
    if unexpected_inputs:
        raise CanonicalizeCandidateError(
            "冻结 Canonical 包含未登记来源：" + ", ".join(unexpected_inputs)
        )

    known_snapshot_ids = {snapshot["snapshot_id"] for snapshot in snapshots.values()}
    documents = []
    reprocess_queue = []
    valid_reused = 0
    metadata_upgraded = 0
    docling_reprocessed = 0
    assets_copied = 0
    for source_id, snapshot in sorted(snapshots.items()):
        reprocessed_entry = reprocessed.get(source_id)
        input_path = (
            reprocessed_entry["resolved_path"]
            if reprocessed_entry is not None
            else frozen_canonical_root / f"{source_id}.json"
        )
        if not input_path.is_file():
            reprocess_queue.append({
                "source_id": source_id,
                "snapshot_id": snapshot["snapshot_id"],
                "reason": "canonical_missing",
                "strict_errors": [],
            })
            continue
        try:
            document = json.loads(input_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            reprocess_queue.append({
                "source_id": source_id,
                "snapshot_id": snapshot["snapshot_id"],
                "reason": "canonical_unreadable",
                "strict_errors": [str(exc)],
            })
            continue
        strict_errors = validate_canonical_document(
            document, known_snapshot_ids=known_snapshot_ids
        )
        strategy = "valid_reused"
        if source_id in affected_source_ids and reprocessed_entry is None:
            reprocess_queue.append({
                "source_id": source_id,
                "snapshot_id": snapshot["snapshot_id"],
                "reason": "policy_affected",
                "strict_errors": strict_errors,
            })
            continue
        if source_id in affected_source_ids:
            runtime = document.get("runtime", {})
            if strict_errors:
                reprocess_queue.append({
                    "source_id": source_id,
                    "snapshot_id": snapshot["snapshot_id"],
                    "reason": "reprocessed_canonical_invalid",
                    "strict_errors": strict_errors,
                })
                continue
            if (
                document.get("source") != snapshot
                or runtime.get("pipeline_revision")
                != policy["docling"]["pipeline_revision"]
                or runtime.get("parser")
                != {"name": "docling", "version": "2.107.0"}
            ):
                reprocess_queue.append({
                    "source_id": source_id,
                    "snapshot_id": snapshot["snapshot_id"],
                    "reason": "reprocessed_runtime_or_snapshot_mismatch",
                    "strict_errors": [],
                })
                continue
            strategy = "docling_reprocessed"
            docling_reprocessed += 1
        elif strict_errors:
            safe, reason = _legacy_metadata_upgrade_safe(document)
            if not safe:
                reprocess_queue.append({
                    "source_id": source_id,
                    "snapshot_id": snapshot["snapshot_id"],
                    "reason": reason,
                    "strict_errors": strict_errors,
                })
                continue
            try:
                document = upgrade_legacy_canonical_metadata(document, snapshot)
            except ValueError as exc:
                reprocess_queue.append({
                    "source_id": source_id,
                    "snapshot_id": snapshot["snapshot_id"],
                    "reason": "metadata_upgrade_failed",
                    "strict_errors": [*strict_errors, str(exc)],
                })
                continue
            strategy = "metadata_upgraded"
            metadata_upgraded += 1
        else:
            if document.get("source") != snapshot:
                reprocess_queue.append({
                    "source_id": source_id,
                    "snapshot_id": snapshot["snapshot_id"],
                    "reason": "snapshot_identity_mismatch",
                    "strict_errors": [],
                })
                continue
            valid_reused += 1
        final_errors = validate_canonical_document(
            document, known_snapshot_ids=known_snapshot_ids
        )
        if final_errors:
            raise CanonicalizeCandidateError(
                f"Canonical 输出校验失败：{source_id}: {'; '.join(final_errors)}"
            )
        assets_copied += _copy_assets(
            document,
            source_id=source_id,
            frozen_assets_root=frozen_assets_root,
            output_assets_root=output_assets_root,
        )
        output_path = output_root / f"{source_id}.json"
        atomic_write_json(output_path, document)
        documents.append({
            "source_id": source_id,
            "doc_id": document["doc_id"],
            "snapshot_id": snapshot["snapshot_id"],
            "object_digest": snapshot["object_digest"],
            "strategy": strategy,
            "output_path": output_path.relative_to(manifest_path.parents[2]).as_posix(),
            "sha256": "sha256:" + _sha256_file(output_path),
            "block_count": len(document["blocks"]),
            "asset_count": len(document.get("assets", [])),
        })

    status = "complete" if not reprocess_queue else "blocked_reprocess_required"
    result = {
        "schema_version": "canonical_documents_manifest_v2",
        "release_id": release_id,
        "status": status,
        "generated_at": _utc_now(),
        "source_ingest_manifest": {
            "path": str(source_manifest_path),
            "sha256": "sha256:" + _sha256_file(source_manifest_path),
            "registry_version": source_manifest["registry_version"],
        },
        "reprocess_policy": {
            "path": str(Path(reprocess_policy_path).resolve()),
            "policy_version": policy["policy_version"],
            "sha256": "sha256:" + _sha256_file(Path(reprocess_policy_path)),
            "affected_source_ids": sorted(affected_source_ids),
        },
        "docling": {
            "route": dict(policy["docling"]),
            "execution_count": docling_reprocessed,
            "reason": (
                "已消费锁定 Docling 重处理 manifest"
                if docling_reprocessed
                else "无需重处理"
                if not reprocess_queue
                else "存在待重处理文档，未执行隐式远端作业"
            ),
        },
        "summary": {
            "sources": len(snapshots),
            "valid_reused": valid_reused,
            "metadata_upgraded": metadata_upgraded,
            "docling_reprocess": len(reprocess_queue),
            "docling_reprocessed": docling_reprocessed,
            "documents_written": len(documents),
            "assets_copied": assets_copied,
        },
        "closure": {
            "source_ids": sorted(snapshots),
            "snapshot_ids": sorted(known_snapshot_ids),
            "document_source_ids": [row["source_id"] for row in documents],
            "complete": not reprocess_queue and len(documents) == len(snapshots),
        },
        "documents": documents,
        "docling_reprocess_queue": reprocess_queue,
    }
    atomic_write_json(manifest_path, result, indent=2)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="从冻结 Canonical 构建候选 Canonical v2")
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-store", type=Path, required=True)
    parser.add_argument("--frozen-canonical-root", type=Path, required=True)
    parser.add_argument("--frozen-assets-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output-assets-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--reprocess-policy", type=Path, default=DEFAULT_REPROCESS_POLICY)
    parser.add_argument("--reprocess-manifest", type=Path)
    parser.add_argument("--release-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_candidate_canonicalize(
            source_manifest_path=args.source_manifest,
            source_store_root=args.source_store,
            frozen_canonical_root=args.frozen_canonical_root,
            frozen_assets_root=args.frozen_assets_root,
            output_root=args.output_root,
            output_assets_root=args.output_assets_root,
            manifest_path=args.manifest,
            reprocess_policy_path=args.reprocess_policy,
            reprocess_manifest_path=args.reprocess_manifest,
            release_id=args.release_id,
        )
    except CanonicalizeCandidateError as exc:
        print(str(exc), file=os.sys.stderr)
        return 2
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "complete" else 3


if __name__ == "__main__":
    raise SystemExit(main())
