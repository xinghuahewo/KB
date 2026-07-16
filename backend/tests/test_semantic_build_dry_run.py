import hashlib
import json


def _legacy_document(digest: str) -> dict:
    return {
        "schema_version": "canonical_document_v2",
        "doc_id": "fixture_source",
        "source": {
            "doc_id": "fixture_source",
            "source_path": "/workspace/data/sources/raw/standards/fixture.txt",
            "source_sha256": digest,
        },
        "runtime": {"pipeline_revision": "block_isolation_v2", "docling": "2.107.0"},
        "document_status": "parsed",
        "fallback_reason": None,
        "fallback_review_status": None,
        "parser_mode": "docling",
        "blocks": [{
            "block_id": "block_v2_" + "1" * 64,
            "doc_id": "fixture_source",
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
            "generated_by": "legacy-fixture-v2",
        }, {
            "block_id": "block_v2_" + "2" * 64,
            "doc_id": "fixture_source",
            "page_id": None,
            "page_number": None,
            "parent_block_id": None,
            "block_type": "paragraph",
            "heading_level": None,
            "reading_order": 1,
            "bbox": None,
            "raw_text": "This paragraph is long enough to become one production semantic chunk.",
            "cleaned_text": "This paragraph is long enough to become one production semantic chunk.",
            "language": "en",
            "quality": {"confidence": 1.0, "ocr_used": False, "issues": []},
            "provenance": {"source_anchor": "#/texts/1"},
            "review_status": "auto_approved",
            "asset_refs": [],
            "generated_by": "legacy-fixture-v2",
        }],
        "assets": [],
        "diagnostics": [],
    }


def test_semantic_build_dry_run_is_read_only_stable_and_writes_a_complete_candidate(tmp_path):
    from bgpkb.ingestion.semantic_build_dry_run import run_semantic_build_dry_run

    raw_root = tmp_path / "raw"
    canonical_root = tmp_path / "canonical"
    output_root = tmp_path / "candidate"
    second_output = tmp_path / "candidate-second"
    raw_path = raw_root / "standards" / "fixture.txt"
    raw_path.parent.mkdir(parents=True)
    content = b"This paragraph is long enough to become one production semantic chunk.\n"
    raw_path.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    canonical_root.mkdir()
    canonical_path = canonical_root / "fixture_source.json"
    canonical_path.write_text(json.dumps(_legacy_document(digest)), encoding="utf-8")
    registry = {
        "schema_version": "source_registry_v1",
        "registry_version": "fixture-registry-v1",
        "sources": [{
            "source_id": "fixture_source",
            "acquisition": {"method": "http", "origin_locator": "https://example.invalid/fixture.txt"},
            "source_type": "standard",
            "document_profile": "rfc",
            "authority_org": "Fixture",
            "language": "en",
            "license": {"status": "unknown", "identifier": None, "notes": "fixture"},
            "expected_content_types": ["text/plain"],
            "legacy_path": "standards/fixture.txt",
            "required": True,
        }],
    }
    before_raw = raw_path.read_bytes()
    before_canonical = canonical_path.read_bytes()

    first = run_semantic_build_dry_run(
        registry,
        raw_root=raw_root,
        canonical_root=canonical_root,
        output_root=output_root,
        acquired_at="2026-07-14T00:00:00Z",
    )
    second = run_semantic_build_dry_run(
        registry,
        raw_root=raw_root,
        canonical_root=canonical_root,
        output_root=second_output,
        acquired_at="2026-07-14T00:00:00Z",
    )

    assert first["status"] == "complete"
    assert first["summary"] == {
        "sources": 1,
        "failed_sources": 0,
        "chunks_before_dedup": 1,
        "chunks_after_dedup": 1,
        "excluded_blocks": 0,
    }
    assert first["quality"]["status"] == "passed"
    assert first["document_profiles"]["rfc"]["chunks"] == 1
    assert first["sources"][0]["content_block_coverage"] == 1.0
    assert first == second
    assert raw_path.read_bytes() == before_raw
    assert canonical_path.read_bytes() == before_canonical
    assert (output_root / "semantic_chunks_v3.jsonl").read_bytes() == (
        second_output / "semantic_chunks_v3.jsonl"
    ).read_bytes()
    assert (output_root / "semantic_chunk_quality_v3.json").is_file()
    assert (output_root / "semantic_build_dry_run.json").is_file()
