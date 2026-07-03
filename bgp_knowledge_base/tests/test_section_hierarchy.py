import copy
import json
from pathlib import Path

import jsonschema


def _block(block_id, block_type, text, *, level=None, order=0, **extra):
    row = {
        "block_id": block_id,
        "doc_id": "doc-1",
        "block_type": block_type,
        "heading_level": level,
        "reading_order": order,
        "cleaned_text": text,
        "language": "zh",
        "review_status": "approved",
        "quality": {"confidence": 1.0, "ocr_used": False, "issues": []},
        "provenance": {
            "source_path": "data/sources/raw/doc.pdf",
            "source_anchor": f"#/blocks/{block_id}",
        },
        "asset_refs": [],
    }
    row.update(extra)
    return row


def _document(blocks):
    return {
        "schema_version": "canonical_document_v2",
        "doc_id": "doc-1",
        "source": {"source_path": "data/sources/raw/doc.pdf", "source_type": "standard"},
        "blocks": blocks,
        "assets": [],
    }


def test_builds_root_nested_and_jump_sections_with_stable_links():
    from bgpkb.cleaning_v2.section_hierarchy import build_hierarchy

    document = _document(
        [
            _block("preface", "paragraph", "标题前正文", order=0),
            _block("h1", "title", "第一章", level=1, order=1),
            _block("p1", "paragraph", "第一章正文", order=2),
            _block("h2", "heading", "第二节", level=2, order=3),
            _block("h3", "heading", "第三层", level=3, order=4),
            _block("jump", "heading", "跳到二级", level=2, order=5),
            _block("jump-deep", "heading", "直接到四级", level=4, order=6),
        ]
    )

    result = build_hierarchy(document)
    sections = result.sections

    assert [row["heading"] for row in sections] == ["", "第一章", "第二节", "第三层", "跳到二级", "直接到四级"]
    assert [row["section_order"] for row in sections] == list(range(6))
    assert sections[0]["section_path"] == []
    assert sections[0]["block_ids"] == ["preface"]
    assert sections[0]["source_ref"] == "data/sources/raw/doc.pdf"
    assert sections[1]["source_ref"] == "data/sources/raw/doc.pdf#/blocks/h1"
    assert sections[1]["parent_section_id"] == sections[0]["section_id"]
    assert sections[2]["parent_section_id"] == sections[1]["section_id"]
    assert sections[3]["parent_section_id"] == sections[2]["section_id"]
    assert sections[4]["parent_section_id"] == sections[1]["section_id"]
    assert sections[5]["parent_section_id"] == sections[4]["section_id"]
    assert sections[0]["child_section_ids"] == [sections[1]["section_id"]]
    assert sections[1]["child_section_ids"] == [sections[2]["section_id"], sections[4]["section_id"]]
    assert sections[2]["child_section_ids"] == [sections[3]["section_id"]]
    assert sections[4]["child_section_ids"] == [sections[5]["section_id"]]
    for previous, current, following in zip([None, *sections], sections, [*sections[1:], None]):
        assert current["previous_section_id"] == (previous["section_id"] if previous else None)
        assert current["next_section_id"] == (following["section_id"] if following else None)


def test_duplicate_full_paths_are_numbered_and_body_changes_only_content_hash():
    from bgpkb.cleaning_v2.section_hierarchy import build_hierarchy, build_section_id

    blocks = [
        _block("h1-a", "heading", "A", level=1, order=0),
        _block("h2-a", "heading", "B", level=2, order=1),
        _block("body-a", "paragraph", "正文一", order=2),
        _block("h1-b", "heading", "A", level=1, order=3),
        _block("h2-b", "heading", "B", level=2, order=4),
        _block("body-b", "paragraph", "正文二", order=5),
    ]
    before = build_hierarchy(_document(blocks))
    changed_blocks = copy.deepcopy(blocks)
    changed_blocks[-1]["cleaned_text"] = "正文二（已修改）"
    after = build_hierarchy(_document(changed_blocks))

    repeated_before = [row for row in before.sections if row["section_path"] == ["A", "B"]]
    repeated_after = [row for row in after.sections if row["section_path"] == ["A", "B"]]
    assert [row["section_id"] for row in repeated_before] == [
        build_section_id("doc-1", ["A", "B"], 1),
        build_section_id("doc-1", ["A", "B"], 2),
    ]
    assert repeated_before[0]["section_id"] != repeated_before[1]["section_id"]
    assert [row["section_id"] for row in repeated_before] == [row["section_id"] for row in repeated_after]
    assert repeated_before[0]["content_hash"] == repeated_after[0]["content_hash"]
    assert repeated_before[1]["content_hash"] != repeated_after[1]["content_hash"]
    assert all(row["section_id"].startswith("section_v2_") for row in before.sections)
    assert all(row["content_hash"].startswith("sha256:") for row in before.sections)


def test_hierarchy_does_not_mutate_authoritative_document():
    from bgpkb.cleaning_v2.section_hierarchy import build_hierarchy

    document = _document([_block("body", "paragraph", "正文")])
    snapshot = copy.deepcopy(document)

    build_hierarchy(document)

    assert document == snapshot


def test_invalid_document_or_block_identity_is_rejected():
    from bgpkb.cleaning_v2.section_hierarchy import build_hierarchy

    document = _document([_block("body", "paragraph", "正文")])
    document["doc_id"] = ""
    try:
        build_hierarchy(document)
    except ValueError as error:
        assert "doc_id" in str(error)
    else:
        raise AssertionError("缺失 doc_id 时必须拒绝派生")

    document = _document([_block("", "paragraph", "正文")])
    try:
        build_hierarchy(document)
    except ValueError as error:
        assert "block_id/doc_id" in str(error)
    else:
        raise AssertionError("缺失 block_id 时必须拒绝派生")


def test_headings_are_structure_and_paragraphs_and_lists_split_into_chunks():
    from bgpkb.cleaning_v2.section_hierarchy import build_hierarchy

    result = build_hierarchy(
        _document(
            [
                _block("title", "title", "标题", level=1, order=0),
                _block("paragraph", "paragraph", "abcdefghijKLMNOP", order=1),
                _block("list", "list_item", "1234567890XYZ", order=2),
            ]
        ),
        maximum_chunk_chars=10,
    )

    assert [row["content"] for row in result.chunks] == ["abcdefghij", "KLMNOP", "1234567890", "XYZ"]
    assert [row["source_block_ids"] for row in result.chunks] == [
        ["paragraph"], ["paragraph"], ["list"], ["list"]
    ]
    assert all(row["schema_version"] == "chunk_v2_hierarchical" for row in result.chunks)
    assert all(row["hierarchy_status"] == "resolved" for row in result.chunks)
    assert all(row["parent_section_id"] == result.sections[1]["section_id"] for row in result.chunks)
    assert result.sections[1]["block_ids"] == ["title", "paragraph", "list"]
    assert result.sections[1]["child_chunk_ids"] == [row["chunk_id"] for row in result.chunks]
    assert result.sections[1]["content_chars"] == sum(len(row["content"]) for row in result.chunks)
    assert result.sections[1]["estimated_tokens"] == 15


def test_code_formula_and_table_are_never_split_even_over_limit():
    from bgpkb.cleaning_v2.section_hierarchy import build_hierarchy

    table = {
        "rows": 2,
        "columns": 2,
        "cells": [
            {"row": 0, "column": 0, "text": "A"},
            {"row": 0, "column": 1, "text": "B"},
            {"row": 1, "column": 0, "text": "C"},
            {"row": 1, "column": 1, "text": "D"},
        ],
    }
    result = build_hierarchy(
        _document(
            [
                _block("code", "code", "0123456789ABCDEF", order=0),
                _block("formula", "formula", "x = 0123456789", order=1),
                _block("table", "table", "", order=2, table=table),
            ]
        ),
        maximum_chunk_chars=5,
    )

    assert len(result.chunks) == 3
    assert [row["chunk_type"] for row in result.chunks] == ["canonical_code", "canonical_formula", "canonical_table"]
    assert result.chunks[0]["content"] == "0123456789ABCDEF"
    assert result.chunks[1]["content"] == "x = 0123456789"
    assert result.chunks[2]["content"] == "| A | B |\n| --- | --- |\n| C | D |"
    assert all(len(row["content"]) > 5 for row in result.chunks)


def test_nonsemantic_and_unknown_blocks_are_audited_but_remain_section_references():
    from bgpkb.cleaning_v2.section_hierarchy import build_hierarchy

    block_types = ["picture", "page_header", "page_footer", "unsupported", "caption", "footnote", "mystery"]
    blocks = [
        _block(block_type, block_type, f"{block_type} text", order=index, asset_refs=["asset-1"] if block_type == "picture" else [])
        for index, block_type in enumerate(block_types)
    ]

    result = build_hierarchy(_document(blocks))

    assert result.chunks == []
    assert result.sections[0]["block_ids"] == block_types
    assert [row["block_id"] for row in result.excluded_blocks] == block_types
    assert {row["reason"] for row in result.excluded_blocks} == {
        "asset_reference_only", "non_retrievable_block_type", "unknown_block_type"
    }


def test_chunk_adjacency_is_reciprocal_and_never_crosses_sections():
    from bgpkb.cleaning_v2.section_hierarchy import build_hierarchy

    result = build_hierarchy(
        _document(
            [
                _block("root-body", "paragraph", "rootroot", order=0),
                _block("h1", "heading", "一", level=1, order=1),
                _block("a", "paragraph", "aaaabbbb", order=2),
                _block("h2", "heading", "二", level=2, order=3),
                _block("b", "paragraph", "ccccdddd", order=4),
            ]
        ),
        maximum_chunk_chars=4,
    )

    by_parent = {}
    for chunk in result.chunks:
        by_parent.setdefault(chunk["parent_section_id"], []).append(chunk)
    assert [row["chunk_order"] for row in by_parent[result.sections[0]["section_id"]]] == [0, 1]
    assert [row["chunk_order"] for row in by_parent[result.sections[1]["section_id"]]] == [0, 1]
    assert [row["chunk_order"] for row in by_parent[result.sections[2]["section_id"]]] == [0, 1]
    for siblings in by_parent.values():
        assert siblings[0]["previous_chunk_id"] is None
        assert siblings[-1]["next_chunk_id"] is None
        for left, right in zip(siblings, siblings[1:]):
            assert left["next_chunk_id"] == right["chunk_id"]
            assert right["previous_chunk_id"] == left["chunk_id"]


def test_hierarchy_results_validate_against_existing_json_schemas_and_are_stable():
    from bgpkb.cleaning_v2.section_hierarchy import build_hierarchy

    document = _document(
        [
            _block("heading", "heading", "结构", level=1, order=0),
            _block("body", "paragraph", "可检索正文", order=1),
        ]
    )
    first = build_hierarchy(document)
    second = build_hierarchy(document)
    root = Path(__file__).parents[1]
    section_schema = json.loads((root / "metadata/schemas/section_catalog.schema.json").read_text(encoding="utf-8"))
    chunk_schema = json.loads((root / "metadata/schemas/chunk.schema.json").read_text(encoding="utf-8"))

    assert first == second
    for section in first.sections:
        jsonschema.Draft202012Validator(section_schema).validate(section)
    for chunk in first.chunks:
        jsonschema.Draft202012Validator(chunk_schema).validate(chunk)
