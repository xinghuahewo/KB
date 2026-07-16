import copy
import hashlib
import json
from pathlib import Path

from bgpkb.ingestion.canonical_contract import canonical_processing_fingerprint


FIXTURES = Path(__file__).parent / "fixtures" / "rag_evidence_pipeline_v2"


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _block(
    doc_id: str,
    block_type: str,
    text: str,
    order: int,
    *,
    heading_level: int | None = None,
    page_number: int | None = None,
    parent_block_id: str | None = None,
    table: dict | None = None,
) -> dict:
    digest = _digest(f"{doc_id}|{block_type}|{order}|{text}")
    source_digest = "a" * 64
    return {
        "block_id": "block_v2_" + digest,
        "doc_id": doc_id,
        "page_id": f"page-{page_number}" if page_number else None,
        "page_number": page_number,
        "parent_block_id": parent_block_id,
        "block_type": block_type,
        "heading_level": heading_level,
        "reading_order": order,
        "bbox": None,
        "raw_text": text,
        "cleaned_text": text,
        "language": "en",
        "quality": {"confidence": 1.0, "ocr_used": False, "issues": []},
        "provenance": {
            "source_snapshot_id": "snapshot_" + "1" * 64,
            "source_object_digest": "sha256:" + source_digest,
            "source_anchor": f"#/blocks/{order}",
        },
        "parse_status": "parsed",
        "content_quality_status": "approved",
        "table": table,
        "asset_refs": [],
        "generated_by": "gold-fixture-v1",
    }


def _document(doc_id: str, blocks: list[dict], *, mime_type: str = "text/plain") -> dict:
    source_digest = "a" * 64
    config_digest = "3" * 64
    document = {
        "schema_version": "canonical_document_v2",
        "doc_id": doc_id,
        "source": {
            "schema_version": "source_snapshot_v1",
            "snapshot_id": "snapshot_" + "1" * 64,
            "source_id": doc_id,
            "registry_version": "gold-fixture-v1",
            "object_digest": "sha256:" + source_digest,
            "object_path": "objects/sha256/" + source_digest,
            "byte_size": sum(len(block["raw_text"].encode("utf-8")) for block in blocks),
            "mime_type": mime_type,
            "acquired_at": "2026-07-14T00:00:00Z",
            "acquisition_status": "imported",
            "origin_locator": f"fixtures/{doc_id}",
            "license": {"status": "unknown", "identifier": None, "notes": "fixture"},
            "http": {"status_code": None, "etag": None, "last_modified": None},
        },
        "runtime": {
            "schema_version": "canonical_runtime_v1",
            "pipeline_revision": "gold-fixture-v1",
            "parser": {"name": "gold-fixture", "version": "1"},
            "environment_fingerprint": "sha256:" + "2" * 64,
        },
        "config_fingerprint": "sha256:" + config_digest,
        "processing_fingerprint": "",
        "parse_status": "parsed",
        "content_quality_status": "approved",
        "blocks": blocks,
        "assets": [],
        "diagnostics": [],
        "parser_mode": "docling",
    }
    document["processing_fingerprint"] = canonical_processing_fingerprint(
        document["source"], document["runtime"], document["config_fingerprint"]
    )
    return document


def _build(document: dict, profile: str):
    from bgpkb.ingestion.semantic_chunking_v3 import build_semantic_chunks

    return build_semantic_chunks(document, document_profile=profile)


def test_rfc_gold_merges_adjacent_paragraphs_inside_the_same_section():
    fixture = (FIXTURES / "rfc_excerpt.txt").read_text(encoding="utf-8")
    first = (
        "A route leak is the propagation of routing announcement(s) beyond their intended scope. "
        "The result of a route leak can be redirection of traffic through an unintended path."
    )
    second = (
        "Operators SHOULD preserve the intended customer-provider boundary. Detection evidence "
        "needs the announced prefix, origin ASN, AS path, observation time, and collector identity."
    )
    assert "A route leak is the propagation" in fixture
    document = _document(
        "fixture_rfc",
        [
            _block("fixture_rfc", "heading", "2. Route Leak Definition", 0, heading_level=1),
            _block("fixture_rfc", "paragraph", first, 1),
            _block("fixture_rfc", "paragraph", second, 2),
        ],
    )

    result = _build(document, "rfc")

    assert len(result.chunks) == 1
    assert result.chunks[0]["section_path"] == ["2. Route Leak Definition"]
    assert first in result.chunks[0]["content"]
    assert second in result.chunks[0]["content"]
    assert result.chunks[0]["source_block_ids"] == [
        document["blocks"][1]["block_id"],
        document["blocks"][2]["block_id"],
    ]


def test_rfc_chunks_respect_heading_boundaries_and_max_tokens_without_losing_content(tmp_path):
    from bgpkb.ingestion.semantic_chunking_v3 import (
        build_semantic_chunks,
        load_semantic_chunking_config,
    )

    config_path = tmp_path / "semantic_chunking_v3.yaml"
    config_path.write_text(
        """schema_version: semantic_chunking_config_v1
config_version: test-small-rfc-v1
chunker_version: 3.0.0
profiles:
  rfc:
    chunker_name: rfc_semantic
    target_min_tokens: 8
    target_max_tokens: 20
short_content:
  minimum_chars: 1
  allowlist: []
deduplication:
  exact_normalization_version: exact-normalization-v1
  near_duplicate_mode: diagnostic_only
""",
        encoding="utf-8",
    )
    first_text = " ".join(f"alpha{i}" for i in range(24))
    second_text = " ".join(f"beta{i}" for i in range(7))
    document = _document(
        "fixture_rfc_limits",
        [
            _block("fixture_rfc_limits", "heading", "Section A", 0, heading_level=1),
            _block("fixture_rfc_limits", "paragraph", first_text, 1),
            _block("fixture_rfc_limits", "heading", "Section B", 2, heading_level=1),
            _block("fixture_rfc_limits", "paragraph", second_text, 3),
        ],
    )

    result = build_semantic_chunks(
        document,
        document_profile="rfc",
        config=load_semantic_chunking_config(config_path),
    )

    section_a = [chunk for chunk in result.chunks if chunk["section_path"] == ["Section A"]]
    section_b = [chunk for chunk in result.chunks if chunk["section_path"] == ["Section B"]]
    assert section_a and section_b
    assert all(chunk["estimated_tokens"] <= 20 for chunk in result.chunks)
    assert " ".join(chunk["content"] for chunk in section_a).split() == first_text.split()
    assert " ".join(chunk["content"] for chunk in section_b).split() == second_text.split()
    assert {chunk["source_id"] for chunk in result.chunks} == {document["source"]["source_id"]}


def test_rfc_infers_numbered_section_boundaries_from_legacy_paragraph_blocks():
    first_heading = "3.1. Type 1: Hairpin Turn with Full Prefix"
    second_heading = "3.2. Type 2: Lateral ISP-ISP-ISP Leak"
    first_body = "A multihomed AS propagates a route learned from one transit provider to another provider."
    second_body = "An ISP leaks a route learned from one peer or provider laterally to another ISP."
    document = _document(
        "fixture_rfc_inferred_headings",
        [
            _block("fixture_rfc_inferred_headings", "paragraph", first_heading, 0),
            _block("fixture_rfc_inferred_headings", "paragraph", first_body, 1),
            _block("fixture_rfc_inferred_headings", "paragraph", second_heading, 2),
            _block("fixture_rfc_inferred_headings", "paragraph", second_body, 3),
        ],
    )

    result = _build(document, "rfc")

    assert len(result.chunks) == 2
    assert result.chunks[0]["section_path"] == [first_heading]
    assert result.chunks[1]["section_path"] == [second_heading]
    assert first_heading in result.chunks[0]["content"]
    assert first_body in result.chunks[0]["content"]
    assert second_heading in result.chunks[1]["content"]
    assert second_body in result.chunks[1]["content"]
    assert {
        block_id
        for chunk in result.chunks
        for block_id in chunk["source_block_ids"]
    } == {block["block_id"] for block in document["blocks"]}


def test_html_gold_excludes_navigation_and_footer_template_blocks():
    fixture = (FIXTURES / "html_page.html").read_text(encoding="utf-8")
    assert "Home Documentation Login" in fixture
    assert "Copyright and repeated navigation links" in fixture
    document = _document(
        "fixture_html",
        [
            _block("fixture_html", "page_header", "Home Documentation Login", 0),
            _block("fixture_html", "title", "Route Origin Validation", 1, heading_level=1),
            _block("fixture_html", "heading", "Validation states", 2, heading_level=2),
            _block(
                "fixture_html",
                "paragraph",
                "A route is Valid, Invalid, or NotFound after comparison with validated ROA payloads.",
                3,
            ),
            _block("fixture_html", "page_footer", "Copyright and repeated navigation links", 4),
        ],
        mime_type="text/html",
    )

    result = _build(document, "html")

    combined = "\n".join(chunk["content"] for chunk in result.chunks)
    assert "Route Origin Validation" in result.chunks[0]["title"]
    assert "Validation states" in result.chunks[0]["section_path"]
    assert "validated ROA payloads" in combined
    assert "Home Documentation Login" not in combined
    assert "Copyright and repeated navigation links" not in combined
    assert {row["reason"] for row in result.excluded_blocks} >= {
        "html_template_navigation",
        "html_template_footer",
    }


def test_html_isolates_repeated_short_navigation_run_even_when_legacy_blocks_are_lists():
    navigation = [
        "Toggle navigation",
        "Home",
        "News",
        "Components",
        "Download",
        "Documentation",
        "Overview",
        "Install",
        "APIs",
        "Tutorials",
        "Overview",
        "Install",
        "APIs",
        "Tutorials",
    ]
    blocks = [_block("fixture_html_legacy_nav", "title", "BGPStream", 0, heading_level=1)]
    blocks.extend(
        _block(
            "fixture_html_legacy_nav",
            "paragraph" if index == 1 else "list_item",
            text,
            index,
        )
        for index, text in enumerate(navigation, 1)
    )
    blocks.append(
        _block(
            "fixture_html_legacy_nav",
            "title",
            "BGPStream Framework Overview",
            len(blocks),
            heading_level=1,
        )
    )
    document = _document("fixture_html_legacy_nav", blocks, mime_type="text/html")

    result = _build(document, "html")

    assert result.chunks == []
    assert len(result.excluded_blocks) == len(navigation)
    assert {row["reason"] for row in result.excluded_blocks} == {
        "html_template_navigation"
    }


def test_html_uses_repeated_page_title_as_boundary_for_long_navigation_cards():
    page_title = "Autonomous System Provider Authorization (ASPA)"
    document = _document(
        "fixture_html_repeated_title",
        [
            _block(
                "fixture_html_repeated_title",
                "title",
                page_title + " - Registry Home",
                0,
                heading_level=1,
            ),
            _block("fixture_html_repeated_title", "paragraph", "IPs & ASNs", 1),
            _block(
                "fixture_html_repeated_title",
                "paragraph",
                "We distribute Internet number resources and provide tools for allocations and assignments.",
                2,
            ),
            _block("fixture_html_repeated_title", "list_item", "IPv4", 3),
            _block("fixture_html_repeated_title", "list_item", "IPv6", 4),
            _block("fixture_html_repeated_title", "list_item", "AS Numbers", 5),
            _block("fixture_html_repeated_title", "list_item", "Documentation", 6),
            _block(
                "fixture_html_repeated_title",
                "title",
                page_title,
                7,
                heading_level=1,
            ),
        ],
        mime_type="text/html",
    )

    result = _build(document, "html")

    assert result.chunks == []
    assert {row["block_id"] for row in result.excluded_blocks} == {
        block["block_id"] for block in document["blocks"][1:7]
    }
    assert {row["reason"] for row in result.excluded_blocks} == {
        "html_template_navigation"
    }


def test_pdf_gold_keeps_table_caption_page_and_source_blocks_together():
    fixture = json.loads((FIXTURES / "pdf_table_canonical_v2.json").read_text(encoding="utf-8"))
    caption_text = fixture["blocks"][0]["cleaned_text"]
    fixture_table = fixture["blocks"][1]["table"]
    table = {
        "table_id": "table-fixture-2",
        "rows": 4,
        "columns": 2,
        "cells": [
            {"row": row, "column": column, "text": text}
            for row, values in enumerate([fixture_table["columns"], *fixture_table["rows"]])
            for column, text in enumerate(values)
        ],
        "source_pages": [3],
        "caption": caption_text,
    }
    caption = _block(
        "fixture_pdf_table", "heading", caption_text, 0, heading_level=2, page_number=3
    )
    table_block = _block(
        "fixture_pdf_table",
        "table",
        fixture["blocks"][1]["cleaned_text"],
        1,
        page_number=3,
        parent_block_id=caption["block_id"],
        table=table,
    )
    document = _document("fixture_pdf_table", [caption, table_block], mime_type="application/pdf")

    result = _build(document, "pdf")

    assert len(result.chunks) == 1
    chunk = result.chunks[0]
    assert caption_text in chunk["content"]
    assert "| State | Meaning |" in chunk["content"]
    assert "| NotFound | No covering ROA |" in chunk["content"]
    assert chunk["page_numbers"] == [3]
    assert chunk["source_block_ids"] == [caption["block_id"], table_block["block_id"]]


def test_pdf_long_table_repeats_header_for_each_bounded_row_group(tmp_path):
    from bgpkb.ingestion.semantic_chunking_v3 import (
        build_semantic_chunks,
        load_semantic_chunking_config,
    )

    config_path = tmp_path / "semantic_chunking_v3.yaml"
    config_path.write_text(
        """schema_version: semantic_chunking_config_v1
config_version: test-small-pdf-v1
chunker_version: 3.0.0
profiles:
  pdf:
    chunker_name: pdf_semantic
    target_min_tokens: 8
    target_max_tokens: 60
short_content:
  minimum_chars: 1
  allowlist: []
deduplication:
  exact_normalization_version: exact-normalization-v1
  near_duplicate_mode: diagnostic_only
""",
        encoding="utf-8",
    )
    caption = _block(
        "fixture_pdf_rows", "heading", "Table 7: Validation actions", 0, heading_level=2, page_number=7
    )
    rows = [["State", "Operator action"]] + [
        [f"State-{index}", f"Investigate route origin and record evidence number {index}"]
        for index in range(1, 7)
    ]
    table = {
        "table_id": "table-fixture-7",
        "rows": len(rows),
        "columns": 2,
        "cells": [
            {"row": row, "column": column, "text": text}
            for row, values in enumerate(rows)
            for column, text in enumerate(values)
        ],
        "source_pages": [7],
        "caption": caption["cleaned_text"],
    }
    table_block = _block(
        "fixture_pdf_rows",
        "table",
        "\n".join(" | ".join(row) for row in rows),
        1,
        page_number=7,
        parent_block_id=caption["block_id"],
        table=table,
    )
    document = _document("fixture_pdf_rows", [caption, table_block], mime_type="application/pdf")

    result = build_semantic_chunks(
        document,
        document_profile="pdf",
        config=load_semantic_chunking_config(config_path),
    )

    assert len(result.chunks) > 1
    assert all("| State | Operator action |" in chunk["content"] for chunk in result.chunks)
    assert all(caption["cleaned_text"] in chunk["content"] for chunk in result.chunks)
    assert all(chunk["estimated_tokens"] <= 60 for chunk in result.chunks)
    assert all(chunk["page_numbers"] == [7] for chunk in result.chunks)
    combined = "\n".join(chunk["content"] for chunk in result.chunks)
    assert all(combined.count(f"State-{index}") == 1 for index in range(1, 7))


def test_openapi_gold_aggregates_method_path_parameters_and_responses():
    fixture = (FIXTURES / "peeringdb_openapi.yaml").read_text(encoding="utf-8")
    document = _document(
        "fixture_openapi",
        [_block("fixture_openapi", "code", fixture, 0)],
        mime_type="application/yaml",
    )

    result = _build(document, "openapi")

    operation_chunks = [chunk for chunk in result.chunks if chunk["semantic_unit"] == "operation"]
    assert len(operation_chunks) == 1
    content = operation_chunks[0]["content"]
    assert "GET /net/{id}" in content
    assert "network_retrieve" in content
    assert "id" in content and "depth" in content
    assert "200" in content and "404" in content
    schema_chunks = [chunk for chunk in result.chunks if chunk["semantic_unit"] == "schema"]
    assert len(schema_chunks) == 1
    assert "Schema Network" in schema_chunks[0]["content"]
    assert all(field in schema_chunks[0]["content"] for field in ["id", "name", "asn"])
    assert not any(chunk["content"].strip() in {"id", "depth", "200", "404", ":", "-"} for chunk in result.chunks)


def test_openapi_nested_inline_request_schema_partitions_on_property_boundaries(tmp_path):
    from bgpkb.ingestion.semantic_chunking_v3 import (
        build_semantic_chunks,
        load_semantic_chunking_config,
    )

    config_path = tmp_path / "semantic_chunking_v3.yaml"
    config_path.write_text(
        """schema_version: semantic_chunking_config_v1
config_version: test-openapi-bounded-v1
chunker_version: 3.0.0
profiles:
  openapi_yaml:
    chunker_name: openapi_semantic
    target_min_tokens: 8
    target_max_tokens: 90
short_content:
  minimum_chars: 1
  allowlist: []
deduplication:
  exact_normalization_version: exact-normalization-v1
  near_duplicate_mode: diagnostic_only
quality_gates:
  max_same_source_exact_duplicate_rate: 0.02
""",
        encoding="utf-8",
    )
    nested_properties = "\n".join(
        f"                    field_{index}:\n                      type: string\n                      description: Nested field number {index} with bounded semantic context."
        for index in range(1, 9)
    )
    source = f"""openapi: 3.0.3
info: {{title: Nested fixture, version: v1}}
paths:
  /objects:
    post:
      operationId: create_object
      summary: Create an object
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                nested:
                  type: object
                  properties:
{nested_properties}
      responses:
        '201': {{description: Created}}
"""
    document = _document(
        "fixture_openapi_nested",
        [_block("fixture_openapi_nested", "code", source, 0)],
        mime_type="application/yaml",
    )

    result = build_semantic_chunks(
        document,
        document_profile="openapi_yaml",
        config=load_semantic_chunking_config(config_path),
    )

    body_chunks = [
        chunk for chunk in result.chunks
        if chunk["semantic_unit"] == "operation" and "parameters:body" in chunk["section_path"]
    ]
    assert len(body_chunks) > 1
    assert all(chunk["estimated_tokens"] <= 90 for chunk in body_chunks)
    combined = "\n".join(chunk["content"] for chunk in body_chunks)
    assert all(combined.count(f"nested.field_{index}") == 1 for index in range(1, 9))


def test_openapi_long_overview_preserves_description_while_partitioning_paragraphs(tmp_path):
    from bgpkb.ingestion.semantic_chunking_v3 import (
        build_semantic_chunks,
        load_semantic_chunking_config,
    )

    config_path = tmp_path / "semantic_chunking_v3.yaml"
    config_path.write_text(
        """schema_version: semantic_chunking_config_v1
config_version: test-openapi-overview-v1
chunker_version: 3.0.0
profiles:
  openapi_yaml:
    chunker_name: openapi_semantic
    target_min_tokens: 8
    target_max_tokens: 80
short_content: {minimum_chars: 1, allowlist: []}
deduplication: {exact_normalization_version: exact-normalization-v1, near_duplicate_mode: diagnostic_only}
quality_gates: {max_same_source_exact_duplicate_rate: 0.02}
""",
        encoding="utf-8",
    )
    paragraphs = [
        f"Paragraph {index} explains a distinct operational constraint and preserves all evidence words for audit."
        for index in range(1, 13)
    ]
    description = "\n\n".join(paragraphs)
    payload = {
        "openapi": "3.0.3",
        "info": {"title": "Overview fixture", "version": "v1"},
        "paths": {
            "/overview": {
                "get": {
                    "operationId": "overview_fixture",
                    "summary": "Read overview",
                    "description": description,
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }
    import yaml
    document = _document(
        "fixture_openapi_overview",
        [_block("fixture_openapi_overview", "code", yaml.safe_dump(payload, sort_keys=False), 0)],
        mime_type="application/yaml",
    )

    result = build_semantic_chunks(
        document,
        document_profile="openapi_yaml",
        config=load_semantic_chunking_config(config_path),
    )

    overview_chunks = [
        chunk for chunk in result.chunks
        if chunk["semantic_unit"] == "operation" and "overview" in chunk["section_path"]
    ]
    assert len(overview_chunks) > 1
    assert all(chunk["estimated_tokens"] <= 80 for chunk in overview_chunks)
    combined = "\n".join(chunk["content"] for chunk in overview_chunks)
    assert all(combined.count(paragraph) == 1 for paragraph in paragraphs)


def test_short_noise_gold_is_isolated_with_a_traceable_diagnostic():
    document = _document(
        "fixture_short",
        [
            _block("fixture_short", "heading", "Markers", 0, heading_level=1),
            _block("fixture_short", "paragraph", "()", 1),
        ],
    )

    result = _build(document, "rfc")

    assert result.chunks == []
    assert result.excluded_blocks == [{
        "block_id": document["blocks"][1]["block_id"],
        "reason": "short_unmeaningful_content",
        "document_profile": "rfc",
        "section_path": ["Markers"],
        "content": "()",
    }]


def test_short_sibling_merges_and_controlled_term_allowlist_is_audited(tmp_path):
    from bgpkb.ingestion.semantic_chunking_v3 import (
        build_semantic_chunks,
        load_semantic_chunking_config,
    )

    config_path = tmp_path / "semantic_chunking_v3.yaml"
    config_path.write_text(
        """schema_version: semantic_chunking_config_v1
config_version: test-short-policy-v1
chunker_version: 3.0.0
profiles:
  rfc:
    chunker_name: rfc_semantic
    target_min_tokens: 8
    target_max_tokens: 100
short_content:
  minimum_chars: 20
  allowlist:
    - rule_id: protocol-term-bgp-v1
      exact: BGP
      profiles: [rfc]
deduplication:
  exact_normalization_version: exact-normalization-v1
  near_duplicate_mode: diagnostic_only
""",
        encoding="utf-8",
    )
    config = load_semantic_chunking_config(config_path)
    merged_document = _document(
        "fixture_short_merge",
        [
            _block("fixture_short_merge", "heading", "Validation", 0, heading_level=1),
            _block("fixture_short_merge", "paragraph", "RPKI", 1),
            _block(
                "fixture_short_merge",
                "paragraph",
                "validates whether the announced origin is authorized by a matching ROA payload.",
                2,
            ),
        ],
    )
    allowlisted_document = _document(
        "fixture_short_allowlist",
        [
            _block("fixture_short_allowlist", "heading", "Protocol term", 0, heading_level=1),
            _block("fixture_short_allowlist", "paragraph", "BGP", 1),
        ],
    )

    merged = build_semantic_chunks(merged_document, document_profile="rfc", config=config)
    allowlisted = build_semantic_chunks(allowlisted_document, document_profile="rfc", config=config)

    assert len(merged.chunks) == 1
    assert merged.chunks[0]["content"].startswith("RPKI\n\nvalidates")
    assert merged.chunks[0]["source_block_ids"] == [
        merged_document["blocks"][1]["block_id"],
        merged_document["blocks"][2]["block_id"],
    ]
    assert len(allowlisted.chunks) == 1
    assert allowlisted.chunks[0]["semantic_unit"] == "term"
    assert allowlisted.chunks[0]["short_content_rule_id"] == "protocol-term-bgp-v1"
    assert allowlisted.excluded_blocks == []


def test_semantic_chunk_identity_is_stable_for_the_same_snapshot_blocks_and_config():
    document = _document(
        "fixture_stable",
        [
            _block("fixture_stable", "heading", "Stable identity", 0, heading_level=1),
            _block(
                "fixture_stable",
                "paragraph",
                "A stable semantic unit must keep the same identity when all authoritative inputs are unchanged.",
                1,
            ),
        ],
    )

    first = _build(document, "rfc")
    second = _build(copy.deepcopy(document), "rfc")

    assert first.chunks == second.chunks
    assert first.excluded_blocks == second.excluded_blocks
    assert first.chunks[0]["chunk_id"].startswith("semantic_chunk_v3_")
    assert first.chunks[0]["source_snapshot_id"] == document["source"]["snapshot_id"]
    assert first.chunks[0]["source_block_ids"] == [document["blocks"][1]["block_id"]]


def test_exact_dedupe_merges_same_source_refs_but_preserves_cross_source_and_near_duplicates():
    from bgpkb.ingestion.semantic_chunking_v3 import deduplicate_semantic_chunks

    exact_text = "Retrieve one network by its numeric identifier and return the complete JSON representation."
    first_document = _document(
        "fixture_dedup",
        [
            _block("fixture_dedup", "heading", "Network endpoint", 0, heading_level=1),
            _block("fixture_dedup", "paragraph", exact_text, 1),
        ],
    )
    repeated_document = _document(
        "fixture_dedup",
        [
            _block("fixture_dedup", "heading", "Network endpoint", 0, heading_level=1),
            _block("fixture_dedup", "paragraph", exact_text, 2),
        ],
    )
    other_source_document = _document(
        "fixture_independent",
        [
            _block("fixture_independent", "heading", "Network endpoint", 0, heading_level=1),
            _block("fixture_independent", "paragraph", exact_text, 1),
        ],
    )
    near_fixture = json.loads((FIXTURES / "duplicate_templates.json").read_text(encoding="utf-8"))
    near_documents = [
        _document(
            "fixture_dedup",
            [
                _block("fixture_dedup", "heading", "Near templates", 10, heading_level=1),
                _block("fixture_dedup", "paragraph", row["text"], 11 + index),
            ],
        )
        for index, row in enumerate(near_fixture["same_source_template_near"])
    ]
    exact_chunks = [
        _build(first_document, "rfc").chunks[0],
        _build(repeated_document, "rfc").chunks[0],
        _build(other_source_document, "rfc").chunks[0],
    ]
    near_chunks = [_build(document, "rfc").chunks[0] for document in near_documents]

    result = deduplicate_semantic_chunks([*exact_chunks, *near_chunks])

    same_source_exact = [
        chunk
        for chunk in result.chunks
        if chunk["source_id"] == "fixture_dedup" and chunk["content"] == exact_text
    ]
    assert len(same_source_exact) == 1
    assert same_source_exact[0]["source_block_ids"] == [
        first_document["blocks"][1]["block_id"],
        repeated_document["blocks"][1]["block_id"],
    ]
    assert any(
        chunk["source_id"] == "fixture_independent" and chunk["content"] == exact_text
        for chunk in result.chunks
    )
    assert all(row["text"] in {chunk["content"] for chunk in result.chunks} for row in near_fixture["same_source_template_near"])
    assert any(row["code"] == "same_source_exact_deduplicated" for row in result.diagnostics)
    near_diagnostics = [row for row in result.diagnostics if row["code"] == "near_duplicate_diagnostic"]
    assert near_diagnostics
    assert all(row["auto_collapsed"] is False for row in near_diagnostics)
