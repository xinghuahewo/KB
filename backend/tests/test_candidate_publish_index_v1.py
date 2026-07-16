from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )


def _retrieval_document(chunk_id: str) -> dict:
    text = "title: RFC 7908\nsection: 2\ncontent: Route leak evidence."
    return {
        "schema_version": "retrieval_document_v1",
        "retrieval_doc_id": "retrieval_document_v1_" + "b" * 64,
        "chunk_id": chunk_id,
        "doc_id": "rfc7908",
        "source_id": "rfc7908",
        "source_snapshot_id": "snapshot-1",
        "title": "RFC 7908",
        "document_profile": "rfc",
        "section_path": ["2"],
        "semantic_unit": "paragraph",
        "source_ref": "https://example.test/rfc7908#section-2",
        "source_refs": ["https://example.test/rfc7908#section-2"],
        "retrieval_text": text,
        "retrieval_text_hash": "sha256:"
        + hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "retrieval_text_version": "retrieval_text_v1",
        "content_preview": text,
        "governance": {
            "parse_status": "parsed",
            "content_quality_status": "approved",
            "source_trust_status": "pending",
            "semantic_review_status": "unknown",
        },
        "eligibility": {
            "status": "eligible_with_caution",
            "policy_version": "retrieval_eligibility_v1",
            "rule_id": "retrieval.pending_governance_caution",
            "reason": "test",
            "audit": {},
        },
    }


def _semantic_chunk(chunk_id: str) -> dict:
    return {
        "schema_version": "semantic_chunk_v3",
        "chunk_id": chunk_id,
        "doc_id": "rfc7908",
        "source_id": "rfc7908",
        "source_snapshot_id": "snapshot-1",
        "source_object_digest": "sha256:" + "a" * 64,
        "source_refs": ["https://example.test/rfc7908#section-2"],
        "source_block_ids": ["block-1"],
        "source_block_hashes": ["sha256:" + "c" * 64],
        "title": "RFC 7908",
        "document_profile": "rfc",
        "section_path": ["2"],
        "semantic_unit": "paragraph",
        "content": "Route leak evidence.",
        "content_hash": "sha256:" + "d" * 64,
        "exact_content_hash": "sha256:" + "e" * 64,
        "language": "en",
        "estimated_tokens": 4,
        "short_content_rule_id": None,
        "chunker": {
            "name": "rfc_semantic",
            "version": "3.0.0",
            "config_version": "v1",
            "config_fingerprint": "sha256:" + "f" * 64,
        },
    }


def _candidate_inputs(tmp_path: Path) -> tuple[Path, Path, str]:
    data_dir = tmp_path / "release-a" / "data"
    published = data_dir / "published"
    chunk_id = "semantic_chunk_v3_" + "a" * 64
    _write_json(
        data_dir / "manifests" / "source_ingest.json",
        {
            "schema_version": "source_ingest_manifest_v1",
            "registry_version": "registry-v1",
            "sources": [
                {
                    "source_id": "rfc7908",
                    "status": "imported",
                    "required": True,
                    "snapshot": {
                        "snapshot_id": "snapshot-1",
                        "source_id": "rfc7908",
                        "object_digest": "sha256:" + "a" * 64,
                        "object_path": "objects/sha256/" + "a" * 64,
                        "origin_locator": "https://example.test/rfc7908",
                        "mime_type": "text/plain",
                        "byte_size": 10,
                        "acquired_at": "2026-07-15T00:00:00Z",
                        "acquisition_status": "imported",
                        "registry_version": "registry-v1",
                        "schema_version": "source_snapshot_v1",
                        "license": {
                            "status": "unknown",
                            "identifier": None,
                            "notes": "test",
                        },
                        "http": {
                            "status_code": None,
                            "etag": None,
                            "last_modified": None,
                        },
                    },
                }
            ],
        },
    )
    _write_jsonl(published / "semantic_chunks_v3.jsonl", [_semantic_chunk(chunk_id)])
    _write_jsonl(
        published / "retrieval_documents_v1.jsonl",
        [_retrieval_document(chunk_id)],
    )
    registry = tmp_path / "registry.yaml"
    registry.write_text(
        """schema_version: source_registry_v1
registry_version: registry-v1
sources:
  - source_id: rfc7908
    acquisition: {method: http, origin_locator: 'https://example.test/rfc7908'}
    source_type: standard
    document_profile: rfc
    authority_org: RFC Editor
    language: en
    license: {status: unknown, identifier: null, notes: test}
    expected_content_types: [text/plain]
    legacy_path: standards/rfc7908.txt
    required: true
""",
        encoding="utf-8",
    )
    return data_dir, registry, chunk_id


def test_candidate_catalogs_use_only_v3_candidate_inputs_and_close_ids(tmp_path):
    from bgpkb.publishing.candidate_publish_index import build_candidate_catalogs

    data_dir, registry, chunk_id = _candidate_inputs(tmp_path)
    result = build_candidate_catalogs(
        data_dir=data_dir,
        registry_path=registry,
        release_id="release-a",
    )

    source = json.loads(
        (data_dir / "published" / "source_catalog.jsonl").read_text().splitlines()[0]
    )
    chunk = json.loads(
        (data_dir / "published" / "chunk_catalog.jsonl").read_text().splitlines()[0]
    )
    section = json.loads(
        (data_dir / "published" / "section_catalog.jsonl").read_text().splitlines()[0]
    )
    manifest = json.loads(
        (data_dir / "published" / "manifest.json").read_text(encoding="utf-8")
    )

    assert result["source_count"] == 1
    assert result["chunk_count"] == 1
    assert source["source_id"] == "rfc7908"
    assert source["snapshot_id"] == "snapshot-1"
    assert source["license_status"] == "unknown"
    assert source["chunk_count"] == 1
    assert chunk["chunk_id"] == chunk_id
    assert chunk["schema_version"] == "semantic_chunk_v3"
    assert chunk["source_block_ids"] == ["block-1"]
    assert chunk["retrieval_doc_id"].startswith("retrieval_document_v1_")
    assert chunk["parent_section_id"] == section["section_id"]
    assert section["child_chunk_ids"] == [chunk_id]
    assert section["section_path"] == ["2"]
    assert manifest["release_id"] == "release-a"
    assert manifest["corpus_version"] == "semantic_chunk_v3"
    assert manifest["legacy_inputs"] == []


def test_candidate_catalogs_fail_closed_on_retrieval_chunk_mismatch(tmp_path):
    from bgpkb.publishing.candidate_publish_index import (
        CandidatePublishIndexError,
        build_candidate_catalogs,
    )

    data_dir, registry, _ = _candidate_inputs(tmp_path)
    document = _retrieval_document("semantic_chunk_v3_" + "9" * 64)
    _write_jsonl(data_dir / "published" / "retrieval_documents_v1.jsonl", [document])

    with pytest.raises(CandidatePublishIndexError, match="chunk ID 集不闭合"):
        build_candidate_catalogs(
            data_dir=data_dir,
            registry_path=registry,
            release_id="release-a",
        )


def test_sqlite_bundle_report_creates_candidate_report_directory(tmp_path, monkeypatch):
    from bgpkb.publishing import build_sqlite_knowledge_base

    report = tmp_path / "generated" / "reports" / "publishing" / "sqlite.md"
    monkeypatch.setattr(build_sqlite_knowledge_base, "REPORT", report)

    build_sqlite_knowledge_base.write_bundle_report(
        {
            "release_id": "release-a",
            "serving": {
                "schema_version": "serving_sqlite_v1",
                "retrieval_document_count": 1,
            },
            "governance": {
                "schema_version": "governance_sqlite_v1",
                "record_count": 2,
            },
        }
    )

    assert report.is_file()
    assert "release-a" in report.read_text(encoding="utf-8")


def test_sqlite_candidate_output_display_does_not_require_project_root(tmp_path):
    from bgpkb.publishing import build_sqlite_knowledge_base

    candidate_output = tmp_path / "release-a" / "data" / "published" / "serving.sqlite"

    assert build_sqlite_knowledge_base._display_path(candidate_output) == str(
        candidate_output
    )
