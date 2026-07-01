import importlib
import importlib.util
import json

import pytest
import yaml

from bgpkb import paths


CONFIG = paths.CONFIG_DIR / "docling_cleaning_v2.yaml"
SCHEMA_NAMES = {
    "preflight": "cleaning_v2_preflight.schema.json",
    "document": "canonical_document_v2.schema.json",
    "block": "canonical_block_v2.schema.json",
    "table": "cleaning_v2_table.schema.json",
    "asset": "cleaning_v2_asset.schema.json",
    "provenance": "cleaning_v2_provenance.schema.json",
}
MODULE = "bgpkb.cleaning_v2.contracts"
REQUIRED_BLOCK_FIELDS = {
    "block_id",
    "doc_id",
    "page_id",
    "parent_block_id",
    "block_type",
    "heading_level",
    "reading_order",
    "bbox",
    "raw_text",
    "cleaned_text",
    "language",
    "quality",
    "provenance",
    "review_status",
    "generated_by",
}


def load_contracts():
    assert importlib.util.find_spec(MODULE) is not None, "Canonical Block v2 契约模块尚未实现"
    return importlib.import_module(MODULE)


def test_cleaning_config_declares_runtime_routes_governance_and_v2_paths():
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))

    assert config["version"] == "docling_cleaning_v2"
    assert {
        "runtime",
        "formats",
        "ocr",
        "resource_budgets",
        "fallback",
        "retry",
        "rules",
        "quality_gates",
        "paths",
    } <= set(config)
    assert config["runtime"]["default_parser"] == "docling"
    assert config["runtime"]["offline_required"] is True
    assert config["runtime"]["ocr_backend"] == "torch"
    assert config["fallback"]["explicit_only"] is True
    assert config["fallback"]["requires_review"] is True
    assert config["quality_gates"]["unreviewed_fallback_published"] == 0
    assert all("_v2" in value for value in config["paths"].values())


def test_v2_schemas_are_closed_and_require_traceable_structures():
    schemas = {
        name: json.loads((paths.SCHEMAS_DIR / filename).read_text(encoding="utf-8"))
        for name, filename in SCHEMA_NAMES.items()
    }

    assert set(SCHEMA_NAMES) == set(schemas)
    assert all(schema["additionalProperties"] is False for schema in schemas.values())
    assert REQUIRED_BLOCK_FIELDS <= set(schemas["block"]["required"])
    assert {"table", "code", "formula", "picture"} <= set(
        schemas["block"]["properties"]["block_type"]["enum"]
    )
    assert {"rows", "columns", "cells", "source_pages"} <= set(schemas["table"]["required"])
    assert {"asset_id", "doc_id", "asset_type", "path", "sha256", "bbox", "provenance"} <= set(
        schemas["asset"]["required"]
    )
    assert {"source_path", "source_sha256", "parser", "runtime", "source_anchor"} <= set(
        schemas["provenance"]["required"]
    )
    assert {"schema_version", "doc_id", "source", "runtime", "blocks", "assets"} <= set(
        schemas["document"]["required"]
    )


def test_block_id_is_stable_and_sensitive_to_source_identity():
    contracts = load_contracts()
    arguments = ("rfc8205", 3, 12, "paragraph", "#/texts/7")

    first = contracts.build_block_id(*arguments)
    second = contracts.build_block_id(*arguments)

    assert first == second
    assert first.startswith("block_v2_")
    assert len(first) == len("block_v2_") + 64
    assert contracts.build_block_id("rfc8205", 3, 13, "paragraph", "#/texts/7") != first
    assert contracts.build_block_id("rfc8205", 3, 12, "table", "#/texts/7") != first


def test_contract_validation_rejects_missing_fields_bad_bbox_and_duplicate_ids():
    contracts = load_contracts()
    block = {
        "block_id": contracts.build_block_id("doc-1", 1, 0, "paragraph", "#/texts/0"),
        "doc_id": "doc-1",
        "page_id": "doc-1_page_1",
        "parent_block_id": None,
        "block_type": "paragraph",
        "heading_level": None,
        "reading_order": 0,
        "bbox": {"left": 0.1, "top": 0.2, "right": 0.8, "bottom": 0.9, "coord_origin": "top_left"},
        "raw_text": "BGP route",
        "cleaned_text": "BGP route",
        "language": "en",
        "quality": {"confidence": 0.99, "ocr_used": False, "issues": []},
        "provenance": {"source_anchor": "#/texts/0"},
        "review_status": "approved",
        "generated_by": "bgpkb.cleaning_v2.contracts",
    }

    assert contracts.validate_blocks([block]) == []
    assert "missing_fields:raw_text" in contracts.validate_blocks([{key: value for key, value in block.items() if key != "raw_text"}])
    bad_bbox = {**block, "bbox": {**block["bbox"], "right": 0.0}}
    assert "invalid_bbox:" + block["block_id"] in contracts.validate_blocks([bad_bbox])
    assert "duplicate_block_id:" + block["block_id"] in contracts.validate_blocks([block, dict(block)])


def test_bbox_vertical_order_respects_coordinate_origin():
    contracts = load_contracts()

    assert contracts.valid_bbox(
        {"left": 10, "top": 790, "right": 400, "bottom": 750, "coord_origin": "bottom_left"}
    )
    assert not contracts.valid_bbox(
        {"left": 10, "top": 750, "right": 400, "bottom": 790, "coord_origin": "bottom_left"}
    )


def test_blocks_sort_deterministically_by_page_reading_order_and_id():
    contracts = load_contracts()
    blocks = [
        {"page_number": 2, "reading_order": 0, "block_id": "block_v2_c"},
        {"page_number": 1, "reading_order": 1, "block_id": "block_v2_b"},
        {"page_number": 1, "reading_order": 1, "block_id": "block_v2_a"},
    ]

    assert [row["block_id"] for row in contracts.sort_blocks(blocks)] == [
        "block_v2_a",
        "block_v2_b",
        "block_v2_c",
    ]


def test_contract_validation_rejects_orphan_parent():
    contracts = load_contracts()
    block = {field: None for field in REQUIRED_BLOCK_FIELDS}
    block.update(
        {
            "block_id": "block_v2_" + "a" * 64,
            "doc_id": "doc-1",
            "parent_block_id": "block_v2_" + "b" * 64,
            "reading_order": 0,
            "bbox": None,
        }
    )

    assert "orphan_parent:" + block["block_id"] in contracts.validate_blocks([block])


def test_atomic_json_write_preserves_previous_authority_on_failure(tmp_path):
    contracts = load_contracts()
    target = tmp_path / "document.json"
    target.write_text("canary\n", encoding="utf-8")

    with pytest.raises(TypeError):
        contracts.atomic_write_json(target, {"not_serializable": {1, 2}})

    assert target.read_text(encoding="utf-8") == "canary\n"
    contracts.atomic_write_json(target, {"doc_id": "doc-1", "blocks": []})
    assert json.loads(target.read_text(encoding="utf-8"))["doc_id"] == "doc-1"
    assert not list(tmp_path.glob("*.tmp"))
