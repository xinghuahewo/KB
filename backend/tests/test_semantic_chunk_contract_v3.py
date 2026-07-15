import copy
import json

import jsonschema
import pytest
import yaml

from bgpkb import paths


def _identity_parts() -> dict:
    return {
        "source_snapshot_id": "snapshot_" + "1" * 64,
        "section_path": ["2. Route Leak Definition"],
        "source_block_hashes": ["sha256:" + "2" * 64, "sha256:" + "3" * 64],
        "chunker_version": "3.0.0",
        "config_fingerprint": "sha256:" + "4" * 64,
        "content_hash": "sha256:" + "5" * 64,
    }


def test_semantic_chunk_schema_is_closed_and_requires_traceable_versioned_identity():
    schema_path = paths.SCHEMAS_DIR / "semantic_chunk_v3.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    required = set(schema["required"])
    assert {
        "chunk_id",
        "source_snapshot_id",
        "source_object_digest",
        "source_block_ids",
        "source_block_hashes",
        "content_hash",
        "chunker",
        "document_profile",
    } <= required
    assert schema["properties"]["chunker"]["additionalProperties"] is False

    invalid = {
        "schema_version": "semantic_chunk_v3",
        "chunk_id": "semantic_chunk_v3_" + "1" * 64,
        "unexpected": True,
    }
    assert list(jsonschema.Draft202012Validator(schema).iter_errors(invalid))


def test_versioned_config_routes_every_supported_document_profile():
    from bgpkb.ingestion.semantic_chunking_v3 import load_semantic_chunking_config, resolve_profile

    config_path = paths.CONFIG_DIR / "semantic_chunking_v3.yaml"
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config = load_semantic_chunking_config(config_path)

    assert raw["schema_version"] == "semantic_chunking_config_v1"
    assert config.config_version == raw["config_version"]
    assert config.config_fingerprint.startswith("sha256:")
    assert {
        "rfc": "rfc_semantic",
        "document": "rfc_semantic",
        "plain_text": "rfc_semantic",
        "html": "html_semantic",
        "pdf": "pdf_semantic",
        "paper": "pdf_semantic",
        "pdf_table": "pdf_semantic",
        "openapi": "openapi_semantic",
        "yaml": "openapi_semantic",
        "openapi_yaml": "openapi_semantic",
    } == {profile: resolve_profile(profile, config).chunker_name for profile in raw["profiles"]}
    with pytest.raises(ValueError, match="不支持的 document_profile"):
        resolve_profile("spreadsheet", config)


def test_every_source_registry_document_profile_has_a_production_route():
    from bgpkb.ingestion.semantic_chunking_v3 import load_semantic_chunking_config, resolve_profile

    registry = yaml.safe_load(paths.SOURCE_REGISTRY_PATH.read_text(encoding="utf-8"))
    config = load_semantic_chunking_config()

    profiles = {source["document_profile"] for source in registry["sources"]}
    assert profiles
    assert {profile: resolve_profile(profile, config).chunker_name for profile in profiles} == {
        "rfc": "rfc_semantic",
        "html": "html_semantic",
        "openapi_yaml": "openapi_semantic",
        "pdf_table": "pdf_semantic",
        "plain_text": "rfc_semantic",
    }


def test_chunk_identity_is_stable_and_changes_for_each_authoritative_identity_input():
    from bgpkb.ingestion.semantic_chunking_v3 import build_semantic_chunk_id

    parts = _identity_parts()
    expected = build_semantic_chunk_id(**parts)

    assert expected == build_semantic_chunk_id(**copy.deepcopy(parts))
    assert expected.startswith("semantic_chunk_v3_")
    replacements = {
        "source_snapshot_id": "snapshot_" + "9" * 64,
        "section_path": ["2.1. Operational Consequences"],
        "source_block_hashes": ["sha256:" + "8" * 64],
        "chunker_version": "3.0.1",
        "config_fingerprint": "sha256:" + "7" * 64,
        "content_hash": "sha256:" + "6" * 64,
    }
    for key, value in replacements.items():
        changed = dict(parts)
        changed[key] = value
        assert build_semantic_chunk_id(**changed) != expected, key
