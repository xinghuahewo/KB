import copy

from bgpkb.cleaning_v2 import heading_hierarchy


def block(block_id, text, *, block_type="heading", level=1, order=0):
    return {
        "block_id": block_id,
        "block_type": block_type,
        "cleaned_text": text,
        "heading_level": level if block_type in {"title", "heading"} else None,
        "reading_order": order,
        "parent_block_id": None,
    }


def test_infers_roman_and_letter_hierarchy_when_docling_levels_are_degenerate():
    blocks = [
        block("title", "BEAR: BGP Event Analysis and Reporting", order=0),
        block("intro", "I. INTRODUCTION", order=1),
        block("background", "A. Background", order=2),
        block("method", "II. METHODOLOGY", order=3),
        block("input", "A. Input", order=4),
    ]
    snapshot = copy.deepcopy(blocks)

    candidates = heading_hierarchy.infer_heading_hierarchy(blocks, source_format="pdf")

    assert blocks == snapshot
    assert [row["level"] for row in candidates] == [1, 2, 3, 2, 3]
    assert candidates[2]["parent_block_id"] == "intro"
    assert candidates[4]["parent_block_id"] == "method"
    assert all(row["evidence"]["docling_level_degenerated"] for row in candidates)


def test_numeric_depth_and_appendix_are_deterministic():
    blocks = [
        block("title", "Paper title", order=0),
        block("s3", "3 Method", order=1),
        block("s31", "3.1 Input", order=2),
        block("s311", "3.1.1 Validation", order=3),
        block("appendix", "APPENDIX A", order=4),
    ]

    candidates = heading_hierarchy.infer_heading_hierarchy(blocks, source_format="pdf")

    assert [row["level"] for row in candidates] == [1, 2, 3, 4, 2]
    assert candidates[3]["parent_block_id"] == "s31"


def test_preserves_non_degenerate_docling_levels():
    blocks = [
        block("title", "Paper title", block_type="title", level=1, order=0),
        block("section", "Unnumbered section", level=2, order=1),
        block("sub", "Unnumbered subsection", level=3, order=2),
    ]

    candidates = heading_hierarchy.infer_heading_hierarchy(blocks, source_format="pdf")

    assert [row["level"] for row in candidates] == [1, 2, 3]
    assert all(row["evidence"]["source"] == "docling_level" for row in candidates)


def test_promotes_rfc_and_yaml_fallback_paragraphs_without_doc_id_rules():
    rfc = [
        block("meta", "Network Working Group", block_type="paragraph", order=0),
        block("title", "A Border Gateway Protocol 4 (BGP-4)", block_type="paragraph", order=1),
        block("intro", "1. Introduction", block_type="paragraph", order=2),
        block("terms", "1.1. Definition of Terms", block_type="paragraph", order=3),
    ]
    yaml_blocks = [
        block("info", "info:\n  title: PeeringDB API", block_type="paragraph", order=0),
        block("paths", "paths:\n  /items: {}", block_type="paragraph", order=1),
        block("components", "components:\n  schemas: {}", block_type="paragraph", order=2),
    ]

    rfc_candidates = heading_hierarchy.infer_heading_hierarchy(rfc, source_format="txt")
    yaml_candidates = heading_hierarchy.infer_heading_hierarchy(yaml_blocks, source_format="yaml")

    assert [(row["text"], row["level"]) for row in rfc_candidates] == [
        ("A Border Gateway Protocol 4 (BGP-4)", 1),
        ("1. Introduction", 2),
        ("1.1. Definition of Terms", 3),
    ]
    assert [(row["text"], row["level"]) for row in yaml_candidates] == [
        ("PeeringDB API", 1),
        ("info", 2),
        ("paths", 2),
        ("components", 2),
    ]
    assert all(row["promoted"] for row in rfc_candidates + yaml_candidates)


def test_promotes_explicit_action_subheadings_inside_structured_document():
    blocks = [
        block("title", "MANRS", order=0),
        block("section", "4. Compulsory Actions", order=1),
        block(
            "action",
            "Action 1: Prevent propagation of incorrect routing information",
            block_type="paragraph",
            order=2,
        ),
        block("discussion", "Discussion:", block_type="paragraph", order=3),
    ]

    candidates = heading_hierarchy.infer_heading_hierarchy(blocks, source_format="pdf")

    assert [(row["block_id"], row["level"]) for row in candidates] == [
        ("title", 1),
        ("section", 2),
        ("action", 3),
        ("discussion", 4),
    ]
    assert candidates[-1]["parent_block_id"] == "action"
