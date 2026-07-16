import copy
import json
from pathlib import Path

import pytest

from bgpkb import paths
from bgpkb.ingestion.canonical_contract import (
    CanonicalContractError,
    canonical_processing_fingerprint,
    is_canonical_stale,
    require_production_canonical,
    validate_canonical_document,
)
from bgpkb.ingestion.canonical_migration import main as canonical_migration_main
from bgpkb.ingestion.canonical_migration import scan_canonical_corpus
from bgpkb.ingestion.canonical_migration import upgrade_legacy_canonical_metadata
from bgpkb.ingestion.legacy_canonical_adapter import LegacyCanonicalAccessError, read_legacy_read_only
from bgpkb.ingestion.production_canonical_inputs import iter_production_canonical


def _snapshot(source_id="rfc4271", digest="a" * 64):
    return {
        "schema_version": "source_snapshot_v1",
        "snapshot_id": "snapshot_" + "1" * 64,
        "source_id": source_id,
        "registry_version": "fixture-v1",
        "object_digest": "sha256:" + digest,
        "object_path": "objects/sha256/" + digest,
        "byte_size": 12,
        "mime_type": "text/plain",
        "acquired_at": "2026-07-14T00:00:00Z",
        "acquisition_status": "imported",
        "origin_locator": "standards/rfc4271.txt",
        "license": {"status": "unknown", "identifier": None, "notes": "fixture"},
        "http": {"status_code": None, "etag": None, "last_modified": None},
    }


def _runtime():
    return {
        "schema_version": "canonical_runtime_v1",
        "pipeline_revision": "fixture-v1",
        "parser": {"name": "docling", "version": "2.107.0"},
        "environment_fingerprint": "sha256:" + "2" * 64,
    }


def canonical_document():
    source = _snapshot()
    runtime = _runtime()
    config_fingerprint = "sha256:" + "3" * 64
    fingerprint = canonical_processing_fingerprint(source, runtime, config_fingerprint)
    return {
        "schema_version": "canonical_document_v2",
        "doc_id": "rfc4271",
        "source": source,
        "runtime": runtime,
        "config_fingerprint": config_fingerprint,
        "processing_fingerprint": fingerprint,
        "parse_status": "parsed",
        "content_quality_status": "approved",
        "blocks": [{
            "block_id": "block_v2_" + "4" * 64,
            "doc_id": "rfc4271",
            "page_id": None,
            "page_number": None,
            "parent_block_id": None,
            "block_type": "paragraph",
            "heading_level": None,
            "reading_order": 0,
            "bbox": None,
            "raw_text": "BGP is an inter-Autonomous System routing protocol.",
            "cleaned_text": "BGP is an inter-Autonomous System routing protocol.",
            "language": "en",
            "quality": {"confidence": 1.0, "ocr_used": False, "issues": []},
            "provenance": {
                "source_snapshot_id": source["snapshot_id"],
                "source_object_digest": source["object_digest"],
                "source_anchor": "#/sections/1",
            },
            "parse_status": "parsed",
            "content_quality_status": "approved",
            "asset_refs": [],
            "generated_by": "fixture-v1",
        }],
        "assets": [],
        "diagnostics": [],
        "parser_mode": "docling",
    }


def test_document_schema_uses_strict_refs_for_block_snapshot_asset_runtime_and_diagnostics():
    schema = json.loads((paths.SCHEMAS_DIR / "canonical_document_v2.schema.json").read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert schema["properties"]["source"]["$ref"].endswith("source-snapshot-v1.json")
    assert schema["properties"]["blocks"]["items"]["$ref"].endswith("canonical-block-v2.json")
    assert schema["properties"]["assets"]["items"]["$ref"].endswith("canonical-asset-v2.json")
    assert schema["properties"]["runtime"]["$ref"].endswith("canonical-runtime-v1.json")
    assert schema["properties"]["diagnostics"]["items"]["$ref"].endswith("canonical-diagnostic-v1.json")


def test_strict_canonical_validation_checks_block_and_snapshot_identity_closure():
    document = canonical_document()

    assert validate_canonical_document(document, known_snapshot_ids={document["source"]["snapshot_id"]}) == []

    bad_block = copy.deepcopy(document)
    bad_block["blocks"][0]["review_status"] = "approved"
    assert any("review_status" in error for error in validate_canonical_document(bad_block))

    assert any(
        "source_snapshot_not_registered" in error
        for error in validate_canonical_document(document, known_snapshot_ids={"snapshot_" + "9" * 64})
    )


def test_nested_table_and_asset_geometry_are_closed_contracts():
    bad_table = canonical_document()
    bad_table["blocks"][0]["table"] = {"unexpected": True}
    assert validate_canonical_document(bad_table)

    bad_asset = canonical_document()
    asset_id = "asset_v2_" + "5" * 64
    bad_asset["blocks"][0]["asset_refs"] = [asset_id]
    bad_asset["assets"] = [{
        "asset_id": asset_id,
        "doc_id": bad_asset["doc_id"],
        "asset_type": "picture",
        "path": "assets/figure.png",
        "sha256": "6" * 64,
        "bbox": {"unexpected": True},
        "caption": None,
        "provenance": bad_asset["blocks"][0]["provenance"],
    }]
    assert validate_canonical_document(bad_asset)


def test_document_source_and_block_identity_form_a_closed_graph():
    document = canonical_document()
    document["source"]["source_id"] = "other-source"
    document["processing_fingerprint"] = canonical_processing_fingerprint(
        document["source"], document["runtime"], document["config_fingerprint"]
    )

    assert "source_doc_id_mismatch:rfc4271:other-source" in validate_canonical_document(document)


def test_snapshot_digest_participates_in_processing_fingerprint_and_stale_decision():
    document = canonical_document()
    changed = _snapshot(digest="b" * 64)

    assert canonical_processing_fingerprint(document["source"], document["runtime"], document["config_fingerprint"]) == document["processing_fingerprint"]
    assert is_canonical_stale(document, document["source"]) is False
    assert is_canonical_stale(document, changed) is True
    assert canonical_processing_fingerprint(changed, document["runtime"], document["config_fingerprint"]) != document["processing_fingerprint"]


def test_production_loader_rejects_legacy_and_status_overreach():
    with pytest.raises(CanonicalContractError, match="Canonical Document v2"):
        require_production_canonical({"schema_version": "parsed_document_v1", "sections": []})

    document = canonical_document()
    document["blocks"][0]["source_trust_status"] = "trusted"
    with pytest.raises(CanonicalContractError, match="source_trust_status"):
        require_production_canonical(document)


def test_legacy_input_requires_explicit_read_only_adapter(tmp_path):
    legacy = tmp_path / "legacy.json"
    legacy.write_text(json.dumps({"schema_version": "parsed_document_v1", "sections": []}), encoding="utf-8")

    with pytest.raises(LegacyCanonicalAccessError, match="显式"):
        read_legacy_read_only(legacy)
    payload = read_legacy_read_only(legacy, allow_legacy=True)
    assert payload["mode"] == "legacy_read_only"
    assert payload["diagnostic"]["code"] == "deprecated_legacy_canonical_input"


def test_canonical_scan_separates_metadata_upgrade_from_docling_reprocess(tmp_path):
    canonical_root = tmp_path / "parsed_v2"
    canonical_root.mkdir()
    strict = canonical_document()
    (canonical_root / "strict.json").write_text(json.dumps(strict), encoding="utf-8")
    legacy = {
        "schema_version": "canonical_document_v2",
        "doc_id": "legacy",
        "source": {"doc_id": "legacy", "source_path": "standards/legacy.txt", "source_sha256": "a" * 64},
        "runtime": {"pipeline_revision": "legacy-v2"},
        "blocks": [],
        "assets": [],
        "diagnostics": [],
    }
    (canonical_root / "legacy.json").write_text(json.dumps(legacy), encoding="utf-8")
    invalid = copy.deepcopy(legacy)
    invalid["doc_id"] = "invalid"
    invalid["source"]["doc_id"] = "invalid"
    invalid["blocks"] = [{"block_id": "broken"}]
    (canonical_root / "invalid.json").write_text(json.dumps(invalid), encoding="utf-8")

    report = scan_canonical_corpus(canonical_root)

    assert report["summary"] == {
        "documents": 3,
        "valid": 1,
        "metadata_upgrade": 1,
        "docling_reprocess": 1,
    }
    assert report["metadata_upgrade_queue"][0]["doc_id"] == "legacy"
    assert report["docling_reprocess_queue"][0]["doc_id"] == "invalid"


def test_new_production_input_iterator_accepts_only_validated_canonical_v2(tmp_path):
    canonical_root = tmp_path / "canonical"
    canonical_root.mkdir()
    strict = canonical_document()
    (canonical_root / "strict.json").write_text(json.dumps(strict), encoding="utf-8")

    assert [row["doc_id"] for row in iter_production_canonical(canonical_root)] == ["rfc4271"]

    (canonical_root / "legacy.json").write_text(
        json.dumps({"schema_version": "parsed_document_v1", "sections": []}),
        encoding="utf-8",
    )
    with pytest.raises(CanonicalContractError, match="legacy.json"):
        list(iter_production_canonical(canonical_root))


def test_canonical_scan_cli_writes_atomic_report_and_can_block_reprocess(tmp_path):
    canonical_root = tmp_path / "canonical"
    canonical_root.mkdir()
    output = tmp_path / "reports" / "migration.json"
    (canonical_root / "broken.json").write_text("{}", encoding="utf-8")

    assert canonical_migration_main([
        "--root", str(canonical_root),
        "--output", str(output),
    ]) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["summary"]["docling_reprocess"] == 1
    assert canonical_migration_main([
        "--root", str(canonical_root),
        "--output", str(output),
        "--fail-on-reprocess",
    ]) == 1
    assert not list(output.parent.glob("*.tmp"))


def test_safe_legacy_canonical_metadata_upgrade_is_strict_stable_and_snapshot_bound():
    snapshot = _snapshot()
    legacy = {
        "schema_version": "canonical_document_v2",
        "doc_id": "rfc4271",
        "source": {
            "doc_id": "rfc4271",
            "source_path": "/workspace/data/sources/raw/standards/rfc4271.txt",
            "source_sha256": "a" * 64,
        },
        "runtime": {"pipeline_revision": "block_isolation_v2", "docling": "2.107.0"},
        "document_status": "parsed",
        "fallback_reason": None,
        "fallback_review_status": None,
        "parser_mode": "docling",
        "blocks": [{
            "block_id": "block_v2_" + "4" * 64,
            "doc_id": "rfc4271",
            "page_id": None,
            "page_number": None,
            "parent_block_id": None,
            "block_type": "paragraph",
            "heading_level": None,
            "reading_order": 0,
            "bbox": None,
            "raw_text": "BGP is an inter-Autonomous System routing protocol.",
            "cleaned_text": "BGP is an inter-Autonomous System routing protocol.",
            "language": "en",
            "quality": {"confidence": 1.0, "ocr_used": False, "issues": []},
            "provenance": {
                "source_path": "/workspace/data/sources/raw/standards/rfc4271.txt",
                "source_sha256": "a" * 64,
                "source_anchor": "#/texts/0",
            },
            "review_status": "auto_approved",
            "asset_refs": [],
            "generated_by": "legacy-fixture-v2",
        }],
        "assets": [],
        "diagnostics": [{"code": "legacy-note", "reason": "kept as warning"}],
    }

    first = upgrade_legacy_canonical_metadata(legacy, snapshot)
    second = upgrade_legacy_canonical_metadata(copy.deepcopy(legacy), copy.deepcopy(snapshot))

    assert first == second
    assert validate_canonical_document(first, known_snapshot_ids={snapshot["snapshot_id"]}) == []
    assert first["source"] == snapshot
    assert first["blocks"][0]["block_id"] == legacy["blocks"][0]["block_id"]
    assert first["blocks"][0]["content_quality_status"] == "approved"
    assert first["diagnostics"][0] == {
        "code": "legacy-note",
        "severity": "warning",
        "message": "kept as warning",
        "source_anchor": None,
        "block_id": None,
    }

    mismatched = copy.deepcopy(snapshot)
    mismatched["object_digest"] = "sha256:" + "b" * 64
    with pytest.raises(ValueError, match="digest"):
        upgrade_legacy_canonical_metadata(legacy, mismatched)
