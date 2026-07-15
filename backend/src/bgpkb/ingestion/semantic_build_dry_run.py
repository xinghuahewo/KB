"""在隔离候选目录对现有 Canonical 语料执行 SemanticChunk v3 dry-run。"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import tempfile

from bgpkb import paths
from bgpkb.ingestion.canonical_contract import validate_canonical_document
from bgpkb.ingestion.canonical_migration import upgrade_legacy_canonical_metadata
from bgpkb.ingestion.semantic_chunk_quality import profile_semantic_chunks
from bgpkb.ingestion.semantic_chunking_v3 import (
    build_semantic_chunks,
    deduplicate_semantic_chunks,
    load_semantic_chunking_config,
)
from bgpkb.ingestion.source_registry import load_source_registry, validate_source_registry
from bgpkb.ingestion.source_store import (
    StoredObject,
    build_source_snapshot,
    hash_source_file,
)


STRUCTURAL_BLOCK_TYPES = {"title", "heading"}


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _write_json(path: Path, payload: dict) -> None:
    _atomic_text(path, json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    _atomic_text(
        path,
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
    )


def _load_candidate_document(
    source: dict,
    *,
    registry_version: str,
    raw_root: Path,
    canonical_root: Path,
    acquired_at: str,
) -> dict:
    raw_path = raw_root / source["legacy_path"]
    canonical_path = canonical_root / f"{source['source_id']}.json"
    if not raw_path.is_file():
        raise FileNotFoundError(f"raw 缺失：{raw_path}")
    if not canonical_path.is_file():
        raise FileNotFoundError(f"Canonical 缺失：{canonical_path}")
    digest, byte_size = hash_source_file(raw_path)
    stored = StoredObject(digest=digest, path=raw_path, byte_size=byte_size, created=False)
    snapshot = build_source_snapshot(
        source=source,
        registry_version=registry_version,
        stored_object=stored,
        acquired_at=acquired_at,
        mime_type=source["expected_content_types"][0],
        acquisition_status="imported",
        http={"status_code": None, "etag": None, "last_modified": None},
    )
    document = json.loads(canonical_path.read_text(encoding="utf-8"))
    strict_errors = validate_canonical_document(
        document,
        known_snapshot_ids={snapshot["snapshot_id"]},
    )
    if strict_errors:
        document = upgrade_legacy_canonical_metadata(document, snapshot)
    return document


def run_semantic_build_dry_run(
    registry: dict,
    *,
    raw_root: Path,
    canonical_root: Path,
    output_root: Path,
    acquired_at: str,
) -> dict:
    validate_source_registry(registry)
    raw_root = Path(raw_root)
    canonical_root = Path(canonical_root)
    output_root = Path(output_root)
    config = load_semantic_chunking_config()
    chunks_before_dedup: list[dict] = []
    excluded_blocks: list[dict] = []
    source_rows: list[dict] = []

    for source in registry["sources"]:
        source_id = source["source_id"]
        try:
            document = _load_candidate_document(
                source,
                registry_version=registry["registry_version"],
                raw_root=raw_root,
                canonical_root=canonical_root,
                acquired_at=acquired_at,
            )
            result = build_semantic_chunks(
                document,
                document_profile=source["document_profile"],
                config=config,
            )
            source_chunks = list(result.chunks)
            source_excluded = [
                {"source_id": source_id, "doc_id": document["doc_id"], **row}
                for row in result.excluded_blocks
            ]
            chunks_before_dedup.extend(source_chunks)
            excluded_blocks.extend(source_excluded)
            content_block_ids = {
                block["block_id"]
                for block in document["blocks"]
                if block["block_type"] not in STRUCTURAL_BLOCK_TYPES
            }
            covered_ids = {
                block_id
                for chunk in source_chunks
                for block_id in chunk["source_block_ids"]
            } | {row["block_id"] for row in source_excluded}
            coverage = (
                len(content_block_ids & covered_ids) / len(content_block_ids)
                if content_block_ids else 1.0
            )
            source_rows.append({
                "source_id": source_id,
                "document_profile": source["document_profile"],
                "status": "complete",
                "canonical_blocks": len(document["blocks"]),
                "chunks_before_dedup": len(source_chunks),
                "excluded_blocks": len(source_excluded),
                "content_block_coverage": round(coverage, 6),
            })
        except Exception as exc:
            source_rows.append({
                "source_id": source_id,
                "document_profile": source["document_profile"],
                "status": "failed",
                "error": str(exc),
            })

    deduplication = deduplicate_semantic_chunks(chunks_before_dedup, config=config)
    chunks = sorted(deduplication.chunks, key=lambda row: (row["source_id"], row["chunk_id"]))
    excluded_blocks.sort(key=lambda row: (row["source_id"], row["block_id"], row["reason"]))
    diagnostics = sorted(
        deduplication.diagnostics,
        key=lambda row: (
            row["code"],
            row.get("canonical_chunk_id", row.get("left_chunk_id", "")),
            row.get("right_chunk_id", ""),
        ),
    )
    quality = profile_semantic_chunks(chunks, excluded_blocks=excluded_blocks, config=config)
    failed_sources = sum(row["status"] == "failed" for row in source_rows)
    profile_counts: dict[str, dict] = {}
    chunks_by_profile = Counter(chunk["document_profile"] for chunk in chunks)
    excluded_by_profile = Counter(row["document_profile"] for row in source_rows for _ in range(row.get("excluded_blocks", 0)))
    for profile in sorted({source["document_profile"] for source in registry["sources"]}):
        profile_counts[profile] = {
            "sources": sum(source["document_profile"] == profile for source in registry["sources"]),
            "chunks": chunks_by_profile[profile],
            "excluded_blocks": excluded_by_profile[profile],
        }
    status = "complete" if not failed_sources and quality["status"] == "passed" else "failed"
    report = {
        "schema_version": "semantic_build_dry_run_v1",
        "status": status,
        "registry_version": registry["registry_version"],
        "source_snapshot_acquired_at": acquired_at,
        "chunker_version": config.chunker_version,
        "config_version": config.config_version,
        "config_fingerprint": config.config_fingerprint,
        "summary": {
            "sources": len(registry["sources"]),
            "failed_sources": failed_sources,
            "chunks_before_dedup": len(chunks_before_dedup),
            "chunks_after_dedup": len(chunks),
            "excluded_blocks": len(excluded_blocks),
        },
        "document_profiles": profile_counts,
        "sources": source_rows,
        "quality": quality,
    }
    _write_jsonl(output_root / "semantic_chunks_v3.jsonl", chunks)
    _write_jsonl(output_root / "semantic_excluded_blocks_v3.jsonl", excluded_blocks)
    _write_jsonl(output_root / "semantic_dedup_diagnostics_v3.jsonl", diagnostics)
    _write_json(output_root / "semantic_chunk_quality_v3.json", quality)
    _write_json(output_root / "semantic_build_dry_run.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="在隔离候选目录执行 SemanticChunk v3 dry-run")
    parser.add_argument("--registry", type=Path, default=paths.SOURCE_REGISTRY_PATH)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--acquired-at", default="2026-07-14T00:00:00Z")
    args = parser.parse_args(argv)
    report = run_semantic_build_dry_run(
        load_source_registry(args.registry),
        raw_root=args.raw_root,
        canonical_root=args.canonical_root,
        output_root=args.output_root,
        acquired_at=args.acquired_at,
    )
    print(json.dumps({"status": report["status"], "summary": report["summary"]}, ensure_ascii=False))
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
