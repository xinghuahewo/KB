"""为候选 Canonical 阶段生成显式 Docling 重处理计划。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from bgpkb.ingestion.canonicalize_candidate import (
    _load_source_manifest,
    load_reprocess_policy,
    run_candidate_canonicalize,
)
from bgpkb.ingestion.cleaning_v2.contracts import atomic_write_json


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def build_docling_reprocess_plan(
    *,
    source_manifest_path: Path,
    source_store_root: Path,
    frozen_canonical_root: Path,
    frozen_assets_root: Path,
    probe_output_root: Path,
    probe_assets_root: Path,
    probe_manifest_path: Path,
    plan_path: Path,
    reprocess_policy_path: Path,
    release_id: str,
) -> dict:
    """复用 Canonical 判定器，只把重处理队列转成候选内正式计划。"""

    result = run_candidate_canonicalize(
        source_manifest_path=source_manifest_path,
        source_store_root=source_store_root,
        frozen_canonical_root=frozen_canonical_root,
        frozen_assets_root=frozen_assets_root,
        output_root=probe_output_root,
        output_assets_root=probe_assets_root,
        manifest_path=probe_manifest_path,
        reprocess_policy_path=reprocess_policy_path,
        reprocess_manifest_path=None,
        release_id=release_id,
    )
    _manifest, snapshots = _load_source_manifest(
        source_manifest_path, Path(source_store_root).resolve()
    )
    policy = load_reprocess_policy(reprocess_policy_path)
    rows = []
    for queued in result["docling_reprocess_queue"]:
        source_id = queued["source_id"]
        snapshot = snapshots[source_id]
        rows.append(
            {
                "source_id": source_id,
                "snapshot_id": snapshot["snapshot_id"],
                "object_digest": snapshot["object_digest"],
                "object_path": snapshot["object_path"],
                "byte_size": snapshot["byte_size"],
                "mime_type": snapshot["mime_type"],
                "reason": queued["reason"],
                "diagnostics": queued.get("strict_errors", []),
            }
        )
    plan = {
        "schema_version": "docling_reprocess_plan_v1",
        "release_id": release_id,
        "status": "ready" if rows else "not_required",
        "source_ingest_manifest_sha256": _sha256(source_manifest_path),
        "reprocess_policy": {
            "policy_version": policy["policy_version"],
            "sha256": _sha256(reprocess_policy_path),
            "affected_source_ids": list(policy["affected_source_ids"]),
        },
        "summary": {"requested": len(rows)},
        "sources": rows,
    }
    atomic_write_json(Path(plan_path), plan, indent=2)
    return plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-store", type=Path, required=True)
    parser.add_argument("--frozen-canonical-root", type=Path, required=True)
    parser.add_argument("--frozen-assets-root", type=Path, required=True)
    parser.add_argument("--probe-output-root", type=Path, required=True)
    parser.add_argument("--probe-assets-root", type=Path, required=True)
    parser.add_argument("--probe-manifest", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--reprocess-policy", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_docling_reprocess_plan(
        source_manifest_path=args.source_manifest,
        source_store_root=args.source_store,
        frozen_canonical_root=args.frozen_canonical_root,
        frozen_assets_root=args.frozen_assets_root,
        probe_output_root=args.probe_output_root,
        probe_assets_root=args.probe_assets_root,
        probe_manifest_path=args.probe_manifest,
        plan_path=args.plan,
        reprocess_policy_path=args.reprocess_policy,
        release_id=args.release_id,
    )
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
