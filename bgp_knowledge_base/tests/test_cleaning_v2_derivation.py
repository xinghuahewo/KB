import copy
import hashlib
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
    assert "# BGP Security" in markdown
    assert "| State | Count |" in markdown
    assert "![Workflow](assets/figure.png)" in markdown
    assert {row["source_ref"] for row in chunks} == {
        "data/sources/raw/doc.pdf#/texts/body",
        "data/sources/raw/doc.pdf#/texts/table",
    }
    assert all(row["schema_version"] == "chunk_v2_hierarchical" for row in chunks)
    assert all(row["parent_section_id"] == result["sections"][1]["section_id"] for row in chunks)
    assert result["sections"][1]["child_chunk_ids"] == [row["chunk_id"] for row in chunks]
    assert [row["asset_id"] for row in assets] == ["asset-1"]
    assert result["excluded_block_count"] == 2


def test_derivation_is_stable_and_does_not_mutate_authoritative_document(tmp_path):
    document = _document()
    snapshot = copy.deepcopy(document)

    first = derivation.derive_document(document, tmp_path / "first", maximum_chunk_chars=24)
    second = derivation.derive_document(document, tmp_path / "second", maximum_chunk_chars=24)

    assert document == snapshot
    assert first["content_digest"] == second["content_digest"]
    assert first["sections"] == second["sections"]
    assert first["chunks"] == second["chunks"]
    assert all(row["chunk_id"].startswith("chunk_v2_") for row in first["chunks"])
    digest_payload = json.dumps(
        {
            "markdown": first["markdown"],
            "assets": first["assets"],
            "sections": first["sections"],
            "chunks": first["chunks"],
            "retrieval_excluded_blocks": first["retrieval_excluded_blocks"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert first["content_digest"] == "sha256:" + hashlib.sha256(digest_payload).hexdigest()


def test_retrieval_exclusion_audit_is_stable_digested_and_persisted(tmp_path):
    document = _document()
    document["blocks"] = [
        _block("picture", "picture", "", asset_refs=[]),
        _block("caption", "caption", "图注"),
        _block("header", "page_header", "页眉"),
        _block("unknown", "mystery", "未知类型"),
        _block("empty-code", "code", ""),
    ]

    first = derivation.build_derivatives(document)
    second = derivation.build_derivatives(document)

    assert first["excluded_block_count"] == 0
    assert first["retrieval_excluded_blocks"] == second["retrieval_excluded_blocks"]
    assert first["content_digest"] == second["content_digest"]
    assert [(row["block_id"], row["reason"]) for row in first["retrieval_excluded_blocks"]] == [
        ("picture", "asset_reference_only"),
        ("caption", "non_retrievable_block_type"),
        ("header", "non_retrievable_block_type"),
        ("unknown", "unknown_block_type"),
        ("empty-code", "empty_content"),
    ]
    audit_payload = json.dumps(
        {
            "markdown": first["markdown"],
            "assets": first["assets"],
            "sections": first["sections"],
            "chunks": first["chunks"],
            "retrieval_excluded_blocks": first["retrieval_excluded_blocks"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert first["content_digest"] == "sha256:" + hashlib.sha256(audit_payload).hexdigest()
    payload_without_audit = json.dumps(
        {
            "markdown": first["markdown"],
            "assets": first["assets"],
            "sections": first["sections"],
            "chunks": first["chunks"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert first["content_digest"] != "sha256:" + hashlib.sha256(payload_without_audit).hexdigest()

    derived = derivation.derive_document(document, tmp_path / "derived")
    manifest = json.loads(
        (tmp_path / "derived" / "doc-1" / "derivation_manifest.json").read_text(encoding="utf-8")
    )
    published = derivation.publish_derivatives(
        document,
        markdown_root=tmp_path / "markdown",
        assets_root=tmp_path / "assets",
        chunks_root=tmp_path / "chunks",
    )
    assert manifest["retrieval_excluded_blocks"] == first["retrieval_excluded_blocks"]
    assert derived["retrieval_excluded_blocks"] == published["retrieval_excluded_blocks"]


def test_derivation_preserves_existing_chunk_id_algorithm_for_retrievable_blocks():
    document = _document()
    document["blocks"] = [_block("body", "paragraph", "abcdefghij")]

    result = derivation.build_derivatives(document, maximum_chunk_chars=5)

    expected = [
        "chunk_v2_" + hashlib.sha256(f"doc-1|body|{index}|{content}".encode("utf-8")).hexdigest()
        for index, content in enumerate(["abcde", "fghij"], start=1)
    ]
    assert [row["chunk_id"] for row in result["chunks"]] == expected
    assert result["sections"][0]["child_chunk_ids"] == expected


def test_empty_textual_blocks_do_not_emit_markdown_markers_or_trailing_spaces():
    document = _document()
    document["blocks"] = [
        _block("empty-title", "title", "", level=1),
        _block("empty-list", "list_item", ""),
        _block("body", "paragraph", "Body"),
    ]

    result = derivation.build_derivatives(document)

    assert result["markdown"] == "Body\n"
    assert all(line == line.rstrip() for line in result["markdown"].splitlines())


def test_publish_derivatives_uses_versioned_markdown_assets_and_chunk_roots(tmp_path):
    asset_source = tmp_path / "authority"
    (asset_source / "assets").mkdir(parents=True)
    (asset_source / "assets" / "figure.png").write_bytes(b"figure")
    result = derivation.publish_derivatives(
        _document(),
        markdown_root=tmp_path / "markdown_v2",
        assets_root=tmp_path / "assets_v2",
        chunks_root=tmp_path / "chunks_v2",
        asset_source_root=asset_source,
    )

    assert (tmp_path / "markdown_v2" / "doc-1.md").is_file()
    assert (tmp_path / "assets_v2" / "doc-1" / "assets.json").is_file()
    assert (tmp_path / "assets_v2" / "doc-1" / "assets" / "figure.png").read_bytes() == b"figure"
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


def test_body_coverage_normalizes_unicode_case_punctuation_and_line_hyphenation():
    document = _document()
    document["blocks"] = [_block("body", "paragraph", "BGP routing protects prefixes")]

    diff = derivation.compare_v1_v2("ＢＧＰ ROUTING protects pre-\nfixes.", document, [], [], [])

    assert diff["body"]["coverage_ratio"] == 1.0
    assert diff["removed_content"]["unattributed_char_count"] == 0


def test_snapshot_transformation_attributes_removed_block_text():
    document = _document()
    document["blocks"] = [_block("body", "paragraph", "Body")]
    transformations = [
        {
            "rule_id": "remove_repeated_header_footer",
            "rule_level": "structural",
            "before": [
                {"block_id": "body", "cleaned_text": "Body"},
                {"block_id": "header", "cleaned_text": "RFC Header"},
            ],
            "after": [
                {"block_id": "body", "cleaned_text": "Body"},
                {"block_id": "header", "cleaned_text": ""},
            ],
        }
    ]

    diff = derivation.compare_v1_v2("Body RFC Header", document, [], [], transformations)

    assert diff["removed_content"]["unattributed_char_count"] == 0


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


def test_migration_gate_accepts_reviewed_fallback_and_evidenced_difference_decision():
    document = _document()
    document["parser_mode"] = "fallback"
    document["fallback_review_status"] = "approved"
    diff = {
        "body": {"coverage_ratio": 0.98, "v2_character_count": 100},
        "removed_content": {"unattributed_char_count": 5},
    }
    decision = {
        "decision": "approved",
        "reason_code": "reviewed_layout_difference",
        "evidence": {"v1_digest": "sha256:a", "v2_digest": "sha256:b"},
    }

    result = derivation.evaluate_migration_gates(
        document,
        diff,
        current_digest="sha256:a",
        repeated_digest="sha256:a",
        migration_decision=decision,
    )

    assert result == {"passed": True, "blocking_issues": []}
