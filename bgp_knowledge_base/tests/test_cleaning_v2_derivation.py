import copy
import json

from bgpkb.cleaning_v2 import derivation


def _block(block_id, block_type, text, *, status="approved", level=None, issues=None, **extra):
    row = {
        "block_id": block_id,
        "doc_id": "doc-1",
        "block_type": block_type,
        "heading_level": level,
        "reading_order": len(block_id),
        "cleaned_text": text,
        "language": "en",
        "review_status": status,
        "quality": {"confidence": 1.0, "ocr_used": False, "issues": issues or []},
        "provenance": {"source_path": "data/sources/raw/doc.pdf", "source_anchor": f"#/texts/{block_id}"},
        "asset_refs": [],
    }
    row.update(extra)
    return row


def _document():
    return {
        "schema_version": "canonical_document_v2",
        "doc_id": "doc-1",
        "source": {"source_path": "data/sources/raw/doc.pdf", "source_type": "standard"},
        "parser_mode": "docling",
        "blocks": [
            _block("title", "title", "BGP Security", level=1),
            _block("body", "paragraph", "Route origin validation protects origin authorization."),
            _block("pending", "paragraph", "unreviewed", status="pending_review"),
            _block("fallback", "paragraph", "legacy", issues=["fallback_parser"]),
            _block(
                "table", "table", "", table={
                    "rows": 2, "columns": 2,
                    "cells": [
                        {"text": "State", "row": 0, "column": 0, "row_span": 1, "column_span": 1},
                        {"text": "Count", "row": 0, "column": 1, "row_span": 1, "column_span": 1},
                        {"text": "Valid", "row": 1, "column": 0, "row_span": 1, "column_span": 1},
                        {"text": "42", "row": 1, "column": 1, "row_span": 1, "column_span": 1},
                    ],
                },
            ),
            _block("picture", "picture", "", asset_refs=["asset-1"]),
        ],
        "assets": [
            {"asset_id": "asset-1", "path": "assets/figure.png", "caption": "Workflow"},
            {"asset_id": "orphan", "path": "assets/orphan.png", "caption": "Orphan"},
        ],
    }


def test_derivation_excludes_unapproved_blocks_and_preserves_source_refs_and_assets(tmp_path):
    result = derivation.derive_document(_document(), tmp_path, maximum_chunk_chars=80)

    markdown = (tmp_path / "doc-1" / "document.md").read_text(encoding="utf-8")
    chunks = [json.loads(line) for line in (tmp_path / "doc-1" / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    assets = json.loads((tmp_path / "doc-1" / "assets.json").read_text(encoding="utf-8"))

    assert "unreviewed" not in markdown and "legacy" not in markdown
    assert "| State | Count |" in markdown
    assert "![Workflow](assets/figure.png)" in markdown
    assert {row["source_ref"] for row in chunks} == {
        "data/sources/raw/doc.pdf#/texts/title",
        "data/sources/raw/doc.pdf#/texts/body",
        "data/sources/raw/doc.pdf#/texts/table",
        "data/sources/raw/doc.pdf#/texts/picture",
    }
    assert [row["asset_id"] for row in assets] == ["asset-1"]
    assert result["excluded_block_count"] == 2


def test_derivation_is_stable_and_does_not_mutate_authoritative_document(tmp_path):
    document = _document()
    snapshot = copy.deepcopy(document)

    first = derivation.derive_document(document, tmp_path / "first", maximum_chunk_chars=24)
    second = derivation.derive_document(document, tmp_path / "second", maximum_chunk_chars=24)

    assert document == snapshot
    assert first["content_digest"] == second["content_digest"]
    assert first["chunks"] == second["chunks"]
    assert all(row["chunk_id"].startswith("chunk_v2_") for row in first["chunks"])


def test_publish_derivatives_uses_versioned_markdown_assets_and_chunk_roots(tmp_path):
    result = derivation.publish_derivatives(
        _document(),
        markdown_root=tmp_path / "markdown_v2",
        assets_root=tmp_path / "assets_v2",
        chunks_root=tmp_path / "chunks_v2",
    )

    assert (tmp_path / "markdown_v2" / "doc-1.md").is_file()
    assert (tmp_path / "assets_v2" / "doc-1" / "assets.json").is_file()
    assert (tmp_path / "chunks_v2" / "doc-1.jsonl").is_file()
    assert result["content_digest"].startswith("sha256:")


def test_document_diff_covers_structure_chunks_sources_and_attributed_removals():
    document = _document()
    document["blocks"] = document["blocks"][:2]
    derived = derivation.build_derivatives(document, maximum_chunk_chars=200)
    v1 = "# BGP Security\n\nRoute origin validation protects origin authorization. Boilerplate"
    transformations = [{"operation": "remove_header", "before": "Boilerplate", "after": "", "rule_level": "structural"}]

    diff = derivation.compare_v1_v2(v1, document, [], derived["chunks"], transformations)

    assert {"body", "titles", "sections", "tables", "pictures", "chunks", "source_refs", "removed_content"} <= set(diff)
    assert diff["removed_content"]["attributed_char_count"] >= len("Boilerplate")
    assert diff["removed_content"]["unattributed_char_count"] == 0


def test_body_coverage_measures_retained_v1_content_without_penalizing_v2_additions():
    document = _document()
    document["blocks"] = [_block("body", "paragraph", "Existing body with verified addition")]

    diff = derivation.compare_v1_v2("Existing body", document, [], [], [])

    assert diff["body"]["coverage_ratio"] == 1.0


def test_migration_gates_block_coverage_unattributed_removal_fallback_and_instability():
    document = _document()
    document["parser_mode"] = "fallback"
    diff = {
        "body": {"coverage_ratio": 0.90, "v2_character_count": 10},
        "removed_content": {"unattributed_char_count": 4},
    }

    result = derivation.evaluate_migration_gates(
        document, diff, current_digest="sha256:a", repeated_digest="sha256:b", minimum_coverage=0.995
    )

    assert result["passed"] is False
    assert set(result["blocking_issues"]) == {
        "body_coverage_below_threshold", "unattributed_content_removal",
        "fallback_document", "unstable_repeated_derivation",
    }
