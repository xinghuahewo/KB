"""从候选 Canonical Document v2 构建完整 semantic-build 制品闭包。"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from bgpkb import paths
from bgpkb.indexing.retrieval_documents import (
    build_retrieval_input_manifest,
    derive_retrieval_documents,
)
from bgpkb.ingestion.canonical_contract import require_production_canonical
from bgpkb.ingestion.semantic_chunk_quality import profile_semantic_chunks
from bgpkb.ingestion.semantic_chunking_v3 import (
    build_chunk_id_migration,
    build_semantic_chunks,
    deduplicate_semantic_chunks,
    load_semantic_chunking_config,
    write_chunk_id_migration,
)
from bgpkb.ingestion.source_registry import load_source_registry, validate_source_registry
from bgpkb.workflows.replay_governance_migration import (
    MIGRATION_RECORDS_NAME,
    replay_governance_migration,
)


STRUCTURAL_BLOCK_TYPES = {"title", "heading"}
REVIEW_SOURCE_IDS = (
    "peeringdb_api_docs",
    "rfc7908",
    "bgpstream_docs",
    "artemis_2018",
    "manrs_netops_actions",
)


class CandidateSemanticBuildError(ValueError):
    """候选 semantic-build 输入、闭包或质量门禁失败。"""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


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


def _write_json(path: Path, payload: Any) -> None:
    _atomic_text(path, json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    _atomic_text(path, "".join(_canonical_json(record) + "\n" for record in records))


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if not Path(path).is_file():
        raise CandidateSemanticBuildError(f"缺少 {label}：{path}")
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateSemanticBuildError(f"{label} 不是合法 JSON：{path}") from exc
    if not isinstance(payload, dict):
        raise CandidateSemanticBuildError(f"{label} 顶层必须是对象：{path}")
    return payload


def _load_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    if not Path(path).is_file():
        raise CandidateSemanticBuildError(f"缺少 {label}：{path}")
    rows = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CandidateSemanticBuildError(
                f"{label} 第 {line_number} 行不是合法 JSON：{path}"
            ) from exc
        if not isinstance(row, dict):
            raise CandidateSemanticBuildError(f"{label} 第 {line_number} 行必须是对象")
        rows.append(row)
    return rows


def _load_legacy_chunks(root: Path) -> list[dict[str, Any]]:
    root = Path(root)
    if not root.is_dir():
        raise CandidateSemanticBuildError(f"缺少冻结旧 chunk 目录：{root}")
    files = sorted(root.glob("*.jsonl"))
    if not files:
        raise CandidateSemanticBuildError(f"冻结旧 chunk 目录为空：{root}")
    rows = []
    for path in files:
        rows.extend(_load_jsonl(path, f"旧 chunk {path.name}"))
    chunk_ids = [str(row.get("chunk_id") or "") for row in rows]
    if not all(chunk_ids) or len(chunk_ids) != len(set(chunk_ids)):
        raise CandidateSemanticBuildError("冻结旧 chunk_id 必须非空且唯一")
    return rows


def _validate_input_closure(
    registry: dict[str, Any],
    *,
    source_manifest: dict[str, Any],
    canonical_manifest: dict[str, Any],
    canonical_root: Path,
    release_id: str,
) -> tuple[list[dict[str, Any]], set[str]]:
    validate_source_registry(registry)
    if source_manifest.get("schema_version") != "source_ingest_manifest_v1":
        raise CandidateSemanticBuildError("source-ingest manifest schema_version 非法")
    if source_manifest.get("status") != "complete":
        raise CandidateSemanticBuildError("source-ingest manifest 未完成")
    if canonical_manifest.get("schema_version") != "canonical_documents_manifest_v2":
        raise CandidateSemanticBuildError("Canonical manifest schema_version 非法")
    if canonical_manifest.get("status") != "complete":
        raise CandidateSemanticBuildError("Canonical manifest 未完成")
    if canonical_manifest.get("release_id") != release_id:
        raise CandidateSemanticBuildError("Canonical manifest release_id 与候选不一致")

    registry_ids = {str(row["source_id"]) for row in registry["sources"]}
    source_rows = source_manifest.get("sources")
    canonical_rows = canonical_manifest.get("documents")
    if not isinstance(source_rows, list) or not isinstance(canonical_rows, list):
        raise CandidateSemanticBuildError("上游 manifest 缺少来源或文档明细")
    successful_sources = {
        str(row.get("source_id"))
        for row in source_rows
        if row.get("snapshot") and row.get("status") in {"imported", "reused"}
    }
    canonical_by_source = {
        str(row.get("source_id")): row for row in canonical_rows if row.get("source_id")
    }
    if successful_sources != registry_ids:
        raise CandidateSemanticBuildError("source-ingest 成功来源与注册表不闭合")
    if set(canonical_by_source) != registry_ids:
        raise CandidateSemanticBuildError("Canonical 文档与注册表来源不闭合")

    snapshot_ids = {
        str(row["snapshot"]["snapshot_id"])
        for row in source_rows
        if isinstance(row.get("snapshot"), dict) and row["snapshot"].get("snapshot_id")
    }
    documents = []
    for source_id in sorted(registry_ids):
        manifest_row = canonical_by_source[source_id]
        canonical_path = Path(canonical_root) / f"{source_id}.json"
        if not canonical_path.is_file():
            raise CandidateSemanticBuildError(f"Canonical 缺失：{source_id}")
        actual_hash = _sha256_file(canonical_path)
        if actual_hash != manifest_row.get("sha256"):
            raise CandidateSemanticBuildError(
                f"Canonical hash 漂移：{source_id}；expected={manifest_row.get('sha256')}；actual={actual_hash}"
            )
        document = _load_json(canonical_path, f"Canonical {source_id}")
        try:
            require_production_canonical(document, known_snapshot_ids=snapshot_ids)
        except ValueError as exc:
            raise CandidateSemanticBuildError(f"Canonical 生产校验失败：{source_id}：{exc}") from exc
        if document.get("doc_id") != source_id:
            raise CandidateSemanticBuildError(f"Canonical doc_id 与 source_id 不一致：{source_id}")
        if document.get("source", {}).get("snapshot_id") != manifest_row.get("snapshot_id"):
            raise CandidateSemanticBuildError(f"Canonical snapshot 闭包失败：{source_id}")
        documents.append(document)
    return documents, snapshot_ids


def _build_chunks(
    registry: dict[str, Any], documents: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    config = load_semantic_chunking_config()
    registry_by_id = {row["source_id"]: row for row in registry["sources"]}
    chunks_before_dedup: list[dict[str, Any]] = []
    excluded_blocks: list[dict[str, Any]] = []
    source_rows = []
    for document in documents:
        source_id = str(document["source"]["source_id"])
        source = registry_by_id[source_id]
        result = build_semantic_chunks(
            document,
            document_profile=str(source["document_profile"]),
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
            str(block["block_id"])
            for block in document["blocks"]
            if block["block_type"] not in STRUCTURAL_BLOCK_TYPES
        }
        covered_ids = {
            str(block_id)
            for chunk in source_chunks
            for block_id in chunk["source_block_ids"]
        } | {str(row["block_id"]) for row in source_excluded}
        missing_block_ids = sorted(content_block_ids - covered_ids)
        source_rows.append(
            {
                "source_id": source_id,
                "doc_id": document["doc_id"],
                "document_profile": source["document_profile"],
                "status": "complete" if not missing_block_ids else "failed",
                "canonical_blocks": len(document["blocks"]),
                "chunks_before_dedup": len(source_chunks),
                "excluded_blocks": len(source_excluded),
                "content_block_coverage": (
                    round((len(content_block_ids) - len(missing_block_ids)) / len(content_block_ids), 6)
                    if content_block_ids
                    else 1.0
                ),
                "missing_block_ids": missing_block_ids,
            }
        )
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
    chunks_by_source = Counter(str(row["source_id"]) for row in chunks)
    for row in source_rows:
        row["chunks_after_dedup"] = chunks_by_source[row["source_id"]]
    return chunks, excluded_blocks, diagnostics, source_rows


def _remap_entity_evidence(
    records: list[dict[str, Any]], migration: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    equivalent = {
        row["old_chunk_ids"][0]: row["new_chunk_ids"][0]
        for row in migration
        if row["relation"] == "equivalent"
        and len(row["old_chunk_ids"]) == 1
        and len(row["new_chunk_ids"]) == 1
    }
    remapped = []
    referenced = 0
    retained = 0
    for record in records:
        old_ids = [str(item) for item in record.get("chunk_sample_ids", [])]
        referenced += len(old_ids)
        new_ids = sorted({equivalent[item] for item in old_ids if item in equivalent})
        retained += len(new_ids)
        if not new_ids:
            continue
        row = dict(record)
        row["chunk_sample_ids"] = new_ids
        remapped.append(row)
    return remapped, {
        "legacy_evidence_chunk_refs": referenced,
        "equivalent_refs_replayed": retained,
        "non_equivalent_refs_not_replayed": referenced - retained,
    }


def _migration_report(
    old_chunks: list[dict[str, Any]],
    new_chunks: list[dict[str, Any]],
    migration: list[dict[str, Any]],
) -> dict[str, Any]:
    old_counts = Counter(
        chunk_id for row in migration for chunk_id in row.get("old_chunk_ids", [])
    )
    new_referenced = {
        chunk_id for row in migration for chunk_id in row.get("new_chunk_ids", [])
    }
    relation_counts = Counter(str(row["relation"]) for row in migration)
    old_ids = {str(row["chunk_id"]) for row in old_chunks}
    new_ids = {str(row["chunk_id"]) for row in new_chunks}
    duplicate_old_ids = sorted(chunk_id for chunk_id, count in old_counts.items() if count != 1)
    missing_old_ids = sorted(old_ids - set(old_counts))
    return {
        "schema_version": "chunk_id_migration_report_v1",
        "status": "passed" if not duplicate_old_ids and not missing_old_ids else "failed",
        "old_chunk_count": len(old_ids),
        "new_chunk_count": len(new_ids),
        "migration_record_count": len(migration),
        "relation_counts": dict(sorted(relation_counts.items())),
        "old_ids_covered_once": len(old_ids) - len(duplicate_old_ids) - len(missing_old_ids),
        "missing_old_ids": missing_old_ids,
        "duplicate_old_ids": duplicate_old_ids,
        "new_ids_referenced": len(new_referenced),
        "new_ids_without_proven_old_mapping": len(new_ids - new_referenced),
    }


def _review_samples(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks:
        by_source[str(chunk["source_id"])].append(chunk)
    samples = []
    for source_id in REVIEW_SOURCE_IDS:
        rows = by_source.get(source_id, [])
        if not rows:
            continue
        selected = sorted(rows, key=lambda row: (-int(row["estimated_tokens"]), row["chunk_id"]))[:3]
        samples.append(
            {
                "source_id": source_id,
                "document_profile": rows[0]["document_profile"],
                "chunk_count": len(rows),
                "semantic_units": dict(sorted(Counter(row["semantic_unit"] for row in rows).items())),
                "page_number_coverage": sum(bool(row.get("page_numbers")) for row in rows),
                "samples": [
                    {
                        "chunk_id": row["chunk_id"],
                        "section_path": row["section_path"],
                        "semantic_unit": row["semantic_unit"],
                        "estimated_tokens": row["estimated_tokens"],
                        "page_numbers": row["page_numbers"],
                        "source_block_count": len(row["source_block_ids"]),
                        "content": row["content"],
                    }
                    for row in selected
                ],
            }
        )
    return {"schema_version": "semantic_build_review_samples_v1", "sources": samples}


def _schema_errors(records: list[dict[str, Any]], schema_name: str) -> list[str]:
    schema = json.loads((paths.SCHEMAS_DIR / schema_name).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = []
    for record in records:
        record_id = str(record.get("retrieval_doc_id") or record.get("object_id") or "<missing>")
        for error in validator.iter_errors(record):
            errors.append(f"{record_id}:{'/'.join(map(str, error.absolute_path))}:{error.message}")
    return errors


def run_candidate_semantic_build(
    registry: dict[str, Any],
    *,
    source_manifest_path: Path,
    canonical_manifest_path: Path,
    canonical_root: Path,
    legacy_chunks_root: Path,
    source_catalog_path: Path,
    entity_evidence_path: Path,
    output_root: Path,
    manifest_path: Path,
    release_id: str,
) -> dict[str, Any]:
    source_manifest = _load_json(source_manifest_path, "source-ingest manifest")
    canonical_manifest = _load_json(canonical_manifest_path, "Canonical manifest")
    documents, _ = _validate_input_closure(
        registry,
        source_manifest=source_manifest,
        canonical_manifest=canonical_manifest,
        canonical_root=canonical_root,
        release_id=release_id,
    )
    source_catalog = _load_jsonl(source_catalog_path, "冻结来源治理目录")
    source_ids = {str(row.get("source_id") or "") for row in source_catalog}
    registry_ids = {str(row["source_id"]) for row in registry["sources"]}
    missing_source_governance = sorted(registry_ids - source_ids)
    if missing_source_governance:
        raise CandidateSemanticBuildError(
            "来源治理数据未覆盖注册表：" + ", ".join(missing_source_governance)
        )
    entity_evidence = _load_jsonl(entity_evidence_path, "冻结实体审核证据")
    old_chunks = _load_legacy_chunks(legacy_chunks_root)

    chunks, excluded_blocks, dedup_diagnostics, source_rows = _build_chunks(registry, documents)
    config = load_semantic_chunking_config()
    semantic_quality = profile_semantic_chunks(
        chunks, excluded_blocks=excluded_blocks, config=config
    )
    migration = build_chunk_id_migration(old_chunks, chunks)
    migration_report = _migration_report(old_chunks, chunks, migration)
    remapped_evidence, evidence_replay = _remap_entity_evidence(entity_evidence, migration)

    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    semantic_chunks_path = output_root / "semantic_chunks_v3.jsonl"
    excluded_path = output_root / "semantic_excluded_blocks_v3.jsonl"
    dedup_path = output_root / "semantic_dedup_diagnostics_v3.jsonl"
    semantic_quality_path = output_root / "semantic_chunk_quality_v3.json"
    migration_path = output_root / "chunk_id_migration.jsonl"
    migration_report_path = output_root / "chunk_id_migration_report_v1.json"
    review_path = output_root / "semantic_build_review_samples_v1.json"
    _write_jsonl(semantic_chunks_path, chunks)
    _write_jsonl(excluded_path, excluded_blocks)
    _write_jsonl(dedup_path, dedup_diagnostics)
    _write_json(semantic_quality_path, semantic_quality)
    write_chunk_id_migration(migration_path, migration)
    _write_json(migration_report_path, migration_report)
    _write_json(review_path, _review_samples(chunks))

    governance_report = replay_governance_migration(
        chunks,
        source_records=source_catalog,
        entity_evidence_records=remapped_evidence,
        output_root=output_root,
    )
    governance_rows = _load_jsonl(output_root / MIGRATION_RECORDS_NAME, "治理迁移记录")
    governance_states = [row["governance"] for row in governance_rows]
    governance_path = output_root / "evidence_governance_states_v1.jsonl"
    _write_jsonl(governance_path, governance_states)
    governance_by_chunk = {row["object_id"]: row for row in governance_states}
    eligibility_by_chunk = {
        chunk_id: row["retrieval_eligibility"]
        for chunk_id, row in governance_by_chunk.items()
    }
    retrieval_documents = derive_retrieval_documents(
        chunks,
        eligibility_by_chunk,
        governance_by_chunk,
    )
    retrieval_path = output_root / "retrieval_documents_v1.jsonl"
    retrieval_input_path = output_root / "retrieval_input_manifest_v1.json"
    _write_jsonl(retrieval_path, retrieval_documents)
    _write_json(retrieval_input_path, build_retrieval_input_manifest(retrieval_documents))

    governance_errors = _schema_errors(
        governance_states, "evidence_governance_state_v1.schema.json"
    )
    retrieval_errors = _schema_errors(
        retrieval_documents, "retrieval_document_v1.schema.json"
    )
    failed_sources = [row for row in source_rows if row["status"] != "complete"]
    eligible_chunk_ids = {
        chunk_id
        for chunk_id, eligibility in eligibility_by_chunk.items()
        if eligibility["status"] in {"eligible", "eligible_with_caution"}
    }
    retrieval_chunk_ids = {row["chunk_id"] for row in retrieval_documents}
    blocking_issues = []
    if failed_sources:
        blocking_issues.append({"code": "canonical_block_coverage_incomplete", "actual": len(failed_sources)})
    if semantic_quality["status"] != "passed":
        blocking_issues.append({"code": "semantic_chunk_quality_failed", "actual": len(semantic_quality["blocking_issues"])})
    if migration_report["status"] != "passed":
        blocking_issues.append({"code": "chunk_migration_closure_failed", "actual": 1})
    if governance_report["blockers"]:
        blocking_issues.append({"code": "governance_migration_blocked", "actual": len(governance_report["blockers"])})
    if governance_errors:
        blocking_issues.append({"code": "governance_schema_error", "actual": len(governance_errors)})
    if retrieval_errors:
        blocking_issues.append({"code": "retrieval_document_schema_error", "actual": len(retrieval_errors)})
    if eligible_chunk_ids != retrieval_chunk_ids:
        blocking_issues.append(
            {
                "code": "retrieval_eligibility_id_closure_failed",
                "missing": sorted(eligible_chunk_ids - retrieval_chunk_ids),
                "unexpected": sorted(retrieval_chunk_ids - eligible_chunk_ids),
            }
        )
    gate_report = {
        "schema_version": "semantic_build_quality_gate_v1",
        "status": "failed" if blocking_issues else "passed",
        "blocking_issues": blocking_issues,
        "semantic_quality": semantic_quality,
        "governance_schema_errors": governance_errors[:20],
        "retrieval_schema_errors": retrieval_errors[:20],
        "retrieval_eligibility_counts": dict(sorted(Counter(
            row["retrieval_eligibility"]["status"] for row in governance_states
        ).items())),
    }
    gate_path = output_root / "semantic_build_quality_gate_v1.json"
    _write_json(gate_path, gate_report)

    artifacts = [
        semantic_chunks_path,
        excluded_path,
        dedup_path,
        semantic_quality_path,
        migration_path,
        migration_report_path,
        review_path,
        output_root / MIGRATION_RECORDS_NAME,
        output_root / "evidence_governance_migration_diff_v1.json",
        output_root / "evidence_governance_migration_report_v1.md",
        governance_path,
        retrieval_path,
        retrieval_input_path,
        gate_path,
    ]
    candidate_root = Path(manifest_path).resolve().parents[2]
    manifest = {
        "schema_version": "semantic_build_manifest_v1",
        "status": "complete" if gate_report["status"] == "passed" else "failed",
        "release_id": release_id,
        "inputs": {
            "source_ingest_manifest": _sha256_file(source_manifest_path),
            "canonical_manifest": _sha256_file(canonical_manifest_path),
            "legacy_chunks": _sha256_bytes(_canonical_json([
                {"chunk_id": row["chunk_id"], "content": row.get("content"), "source_block_ids": row.get("source_block_ids")}
                for row in old_chunks
            ]).encode("utf-8")),
            "source_catalog": _sha256_file(source_catalog_path),
            "entity_evidence": _sha256_file(entity_evidence_path),
            "semantic_config": config.config_fingerprint,
        },
        "summary": {
            "sources": len(registry["sources"]),
            "failed_sources": len(failed_sources),
            "semantic_chunks": len(chunks),
            "excluded_blocks": len(excluded_blocks),
            "governance_records": len(governance_states),
            "retrieval_documents": len(retrieval_documents),
            "old_chunks": len(old_chunks),
            "migration_records": len(migration),
        },
        "evidence_replay": evidence_replay,
        "migration": migration_report,
        "sources": source_rows,
        "outputs": [
            {
                "path": path.resolve().relative_to(candidate_root).as_posix(),
                "sha256": _sha256_file(path),
                "byte_size": path.stat().st_size,
            }
            for path in artifacts
        ],
    }
    _write_json(manifest_path, manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="构建候选 SemanticChunk、治理状态与 Retrieval Document")
    parser.add_argument("--registry", type=Path, default=paths.SOURCE_REGISTRY_PATH)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--canonical-manifest", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--legacy-chunks-root", type=Path, required=True)
    parser.add_argument("--source-catalog", type=Path, required=True)
    parser.add_argument("--entity-evidence", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    args = parser.parse_args(argv)
    try:
        manifest = run_candidate_semantic_build(
            load_source_registry(args.registry),
            source_manifest_path=args.source_manifest,
            canonical_manifest_path=args.canonical_manifest,
            canonical_root=args.canonical_root,
            legacy_chunks_root=args.legacy_chunks_root,
            source_catalog_path=args.source_catalog,
            entity_evidence_path=args.entity_evidence,
            output_root=args.output_root,
            manifest_path=args.manifest,
            release_id=args.release_id,
        )
    except (CandidateSemanticBuildError, ValueError) as exc:
        print(str(exc))
        return 1
    print(json.dumps({"status": manifest["status"], "summary": manifest["summary"]}, ensure_ascii=False))
    return 0 if manifest["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
