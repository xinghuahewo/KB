from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bgpkb.ingestion.canonical_migration import upgrade_legacy_canonical_metadata


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return "sha256:" + _sha256_bytes(path.read_bytes())


def _snapshot(source_id: str, payload: bytes) -> dict:
    digest = _sha256_bytes(payload)
    return {
        "schema_version": "source_snapshot_v1",
        "source_id": source_id,
        "snapshot_id": "snapshot_" + "1" * 64,
        "registry_version": "fixture-registry-v1",
        "object_digest": f"sha256:{digest}",
        "object_path": f"objects/sha256/{digest}",
        "byte_size": len(payload),
        "mime_type": "text/plain",
        "acquired_at": "2026-07-15T00:00:00Z",
        "acquisition_status": "imported",
        "origin_locator": "https://example.invalid/fixture.txt",
        "license": {"status": "known", "identifier": "MIT", "notes": "fixture"},
        "http": {"status_code": None, "etag": None, "last_modified": None},
    }


def _legacy_document(source_id: str, payload: bytes, content: str) -> dict:
    return {
        "schema_version": "canonical_document_v2",
        "doc_id": source_id,
        "source": {
            "doc_id": source_id,
            "source_path": f"/frozen/{source_id}.txt",
            "source_sha256": _sha256_bytes(payload),
        },
        "runtime": {"pipeline_revision": "block_isolation_v2", "docling": "2.107.0"},
        "document_status": "parsed",
        "parser_mode": "docling",
        "blocks": [
            {
                "block_id": "block_v2_" + "2" * 64,
                "doc_id": source_id,
                "page_id": None,
                "page_number": None,
                "parent_block_id": None,
                "block_type": "heading",
                "heading_level": 1,
                "reading_order": 0,
                "bbox": None,
                "raw_text": "Fixture section",
                "cleaned_text": "Fixture section",
                "language": "en",
                "quality": {"confidence": 1.0, "ocr_used": False, "issues": []},
                "provenance": {"source_anchor": "#/texts/0"},
                "review_status": "auto_approved",
                "asset_refs": [],
                "generated_by": "fixture",
            },
            {
                "block_id": "block_v2_" + "3" * 64,
                "doc_id": source_id,
                "page_id": None,
                "page_number": None,
                "parent_block_id": None,
                "block_type": "paragraph",
                "heading_level": None,
                "reading_order": 1,
                "bbox": None,
                "raw_text": content,
                "cleaned_text": content,
                "language": "en",
                "quality": {"confidence": 1.0, "ocr_used": False, "issues": []},
                "provenance": {"source_anchor": "#/texts/1"},
                "review_status": "auto_approved",
                "asset_refs": [],
                "generated_by": "fixture",
            },
        ],
        "assets": [],
        "diagnostics": [],
    }


def _write_inputs(tmp_path: Path) -> dict[str, object]:
    source_id = "fixture_source"
    raw = b"immutable source bytes"
    snapshot = _snapshot(source_id, raw)
    content = " ".join(["A complete BGP semantic paragraph with stable source evidence."] * 8)
    canonical = upgrade_legacy_canonical_metadata(
        _legacy_document(source_id, raw, content), snapshot
    )
    candidate = tmp_path / "candidate"
    canonical_root = candidate / "data" / "corpus" / "canonical"
    canonical_root.mkdir(parents=True)
    canonical_path = canonical_root / f"{source_id}.json"
    canonical_path.write_text(json.dumps(canonical), encoding="utf-8")

    source_manifest = candidate / "data" / "manifests" / "source_ingest.json"
    source_manifest.parent.mkdir(parents=True, exist_ok=True)
    source_manifest.write_text(
        json.dumps(
            {
                "schema_version": "source_ingest_manifest_v1",
                "status": "complete",
                "registry_version": "fixture-registry-v1",
                "sources": [
                    {
                        "source_id": source_id,
                        "required": True,
                        "status": "imported",
                        "snapshot": snapshot,
                    }
                ],
                "summary": {"imported": 1, "missing": 0, "failed": 0},
            }
        ),
        encoding="utf-8",
    )
    canonical_manifest = candidate / "data" / "manifests" / "canonical_documents_v2.json"
    canonical_manifest.write_text(
        json.dumps(
            {
                "schema_version": "canonical_documents_manifest_v2",
                "status": "complete",
                "release_id": candidate.name,
                "documents": [
                    {
                        "source_id": source_id,
                        "doc_id": source_id,
                        "snapshot_id": snapshot["snapshot_id"],
                        "object_digest": snapshot["object_digest"],
                        "output_path": f"data/corpus/canonical/{source_id}.json",
                        "sha256": _sha256_file(canonical_path),
                        "block_count": 2,
                        "asset_count": 0,
                        "strategy": "metadata_upgraded",
                    }
                ],
                "summary": {"sources": 1, "documents_written": 1},
            }
        ),
        encoding="utf-8",
    )
    legacy_chunks = tmp_path / "legacy-chunks"
    legacy_chunks.mkdir()
    old_chunk_id = "chunk_v2_" + "4" * 64
    (legacy_chunks / f"{source_id}.jsonl").write_text(
        json.dumps(
            {
                "schema_version": "chunk_v2_hierarchical",
                "chunk_id": old_chunk_id,
                "doc_id": source_id,
                "source_id": source_id,
                "content": content,
                "source_block_ids": ["block_v2_" + "3" * 64],
                "review_status": "approved",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    source_catalog = tmp_path / "source_catalog.jsonl"
    source_catalog.write_text(
        json.dumps(
            {
                "source_id": source_id,
                "source_type": "standard",
                "review_status": "approved",
                "trust_level": "high",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    entity_evidence = tmp_path / "entity_source_evidence.jsonl"
    entity_evidence.write_text(
        json.dumps(
            {
                "entity_id": "bgp-fixture",
                "entity_review_status": "approved",
                "chunk_sample_ids": [old_chunk_id],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    registry = {
        "schema_version": "source_registry_v1",
        "registry_version": "fixture-registry-v1",
        "sources": [
            {
                "source_id": source_id,
                "acquisition": {
                    "method": "http",
                    "origin_locator": "https://example.invalid/fixture.txt",
                },
                "source_type": "standard",
                "document_profile": "rfc",
                "authority_org": "Fixture",
                "language": "en",
                "license": {"status": "known", "identifier": "MIT", "notes": "fixture"},
                "expected_content_types": ["text/plain"],
                "legacy_path": "standards/fixture.txt",
                "required": True,
            }
        ],
    }
    return {
        "candidate": candidate,
        "registry": registry,
        "source_manifest": source_manifest,
        "canonical_manifest": canonical_manifest,
        "canonical_root": canonical_root,
        "legacy_chunks": legacy_chunks,
        "source_catalog": source_catalog,
        "entity_evidence": entity_evidence,
        "canonical_path": canonical_path,
        "content": content,
        "old_chunk_id": old_chunk_id,
    }


def _run(inputs: dict[str, object]):
    from bgpkb.ingestion.semantic_build_candidate import run_candidate_semantic_build

    candidate = inputs["candidate"]
    return run_candidate_semantic_build(
        inputs["registry"],
        source_manifest_path=inputs["source_manifest"],
        canonical_manifest_path=inputs["canonical_manifest"],
        canonical_root=inputs["canonical_root"],
        legacy_chunks_root=inputs["legacy_chunks"],
        source_catalog_path=inputs["source_catalog"],
        entity_evidence_path=inputs["entity_evidence"],
        output_root=candidate / "data" / "published",
        manifest_path=candidate / "data" / "manifests" / "semantic_build_v1.json",
        release_id=candidate.name,
    )


def test_candidate_semantic_build_closes_chunks_governance_retrieval_and_migration(tmp_path):
    inputs = _write_inputs(tmp_path)

    manifest = _run(inputs)

    assert manifest["status"] == "complete"
    assert manifest["summary"] == {
        "sources": 1,
        "failed_sources": 0,
        "semantic_chunks": 1,
        "excluded_blocks": 0,
        "governance_records": 1,
        "retrieval_documents": 1,
        "old_chunks": 1,
        "migration_records": 1,
    }
    published = inputs["candidate"] / "data" / "published"
    retrieval = json.loads((published / "retrieval_documents_v1.jsonl").read_text())
    assert inputs["content"] in retrieval["retrieval_text"]
    assert len(retrieval["content_preview"]) == 240
    assert retrieval["governance"]["source_trust_status"] == "trusted"
    assert retrieval["governance"]["semantic_review_status"] == "approved"
    assert retrieval["eligibility"]["status"] == "eligible"
    migration = json.loads((published / "chunk_id_migration.jsonl").read_text())
    assert migration["relation"] == "equivalent"
    assert migration["old_chunk_ids"] == [inputs["old_chunk_id"]]
    assert (published / "semantic_chunk_quality_v3.json").is_file()
    assert (published / "retrieval_input_manifest_v1.json").is_file()
    assert (inputs["candidate"] / "data" / "manifests" / "semantic_build_v1.json").is_file()


def test_candidate_semantic_build_rejects_canonical_hash_drift(tmp_path):
    inputs = _write_inputs(tmp_path)
    inputs["canonical_path"].write_text("{}", encoding="utf-8")

    from bgpkb.ingestion.semantic_build_candidate import CandidateSemanticBuildError

    with pytest.raises(CandidateSemanticBuildError, match="Canonical hash"):
        _run(inputs)
