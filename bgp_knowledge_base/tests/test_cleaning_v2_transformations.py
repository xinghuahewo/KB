import copy
import importlib
import importlib.util
import json

from bgpkb import paths


MODULE = "bgpkb.cleaning_v2.transformations"
TRANSFORMATION_SCHEMA = paths.SCHEMAS_DIR / "cleaning_transformation_v2.schema.json"
DECISION_SCHEMA = paths.SCHEMAS_DIR / "cleaning_review_decision_v2.schema.json"


def load_module():
    assert importlib.util.find_spec(MODULE) is not None, "清洗转换治理尚未实现"
    return importlib.import_module(MODULE)


def block(block_id, text, **overrides):
    result = {
        "block_id": block_id,
        "doc_id": "doc-1",
        "page_number": 1,
        "block_type": "paragraph",
        "raw_text": text,
        "cleaned_text": text,
        "review_status": "auto_approved",
        "quality": {"confidence": 1.0, "ocr_used": False, "issues": []},
    }
    result.update(overrides)
    return result


def test_governance_schemas_require_complete_audit_and_human_decision_fields():
    transformation = json.loads(TRANSFORMATION_SCHEMA.read_text(encoding="utf-8"))
    decision = json.loads(DECISION_SCHEMA.read_text(encoding="utf-8"))

    assert transformation["additionalProperties"] is False
    assert {"transformation_id", "rule_id", "rule_version", "rule_level", "operation", "input_block_ids", "output_block_ids", "before", "after", "evidence", "confidence", "generated_by"} <= set(transformation["required"])
    assert decision["additionalProperties"] is False
    assert {"decision_id", "block_id", "decision", "reviewer", "reviewed_at", "input_fingerprint"} <= set(decision["required"])


def test_lossless_normalization_is_auto_approved_and_audited_without_mutating_raw():
    module = load_module()
    raw = [block("b1", "ＲＯＶ\r\n  validates   routes  ")]
    snapshot = copy.deepcopy(raw)

    result = module.apply_rules(raw, [module.CleaningRule("unicode_whitespace", "1", "lossless")], {})

    assert raw == snapshot
    assert result["cleaned_blocks"][0]["cleaned_text"] == "ROV\nvalidates routes"
    assert result["cleaned_blocks"][0]["review_status"] == "auto_approved"
    assert result["transformations"][0]["before"] != result["transformations"][0]["after"]
    assert result["review_items"] == []


def test_structural_header_heading_cross_page_paragraph_and_table_rules_are_audited():
    module = load_module()
    raw = [
        block("h1", "RFC 8205", block_type="page_header", page_number=1),
        block("h2", "RFC 8205", block_type="page_header", page_number=2),
        block("title", "Route Origin Validation", block_type="heading", heading_level=3),
        block("p1", "inter-", page_number=1, continues_to_next=True),
        block("p2", "domain routing", page_number=2),
        block("t1", "", block_type="table", page_number=1, table={"rows": 2, "columns": 2, "cells": [{"text": "A"}]}),
        block("t2", "", block_type="table", page_number=2, continues_from_previous=True, table={"rows": 1, "columns": 2, "cells": [{"text": "B"}]}),
    ]
    rules = [
        module.CleaningRule("remove_repeated_header_footer", "1", "structural"),
        module.CleaningRule("correct_heading_level", "1", "structural", options={"levels": {"title": 2}}),
        module.CleaningRule("merge_cross_page_paragraph", "1", "structural"),
        module.CleaningRule("merge_cross_page_table", "1", "structural"),
    ]

    result = module.apply_rules(raw, rules, {})
    by_id = {row["block_id"]: row for row in result["cleaned_blocks"]}

    assert by_id["h1"]["cleaned_text"] == by_id["h2"]["cleaned_text"] == ""
    assert by_id["title"]["heading_level"] == 2
    assert by_id["p1"]["cleaned_text"] == "interdomain routing"
    assert by_id["p2"]["cleaned_text"] == ""
    assert by_id["t1"]["table"]["rows"] == 3
    assert by_id["t2"]["cleaned_text"] == ""
    assert {row["rule_id"] for row in result["transformations"]} == {rule.rule_id for rule in rules}
    assert all(item["review_status"] == "pending_review" for item in result["review_items"])


def test_semantic_rule_never_rewrites_cleaned_text_and_only_creates_review_item():
    module = load_module()
    raw = [block("b1", "RPKI prevents all hijacks")]

    result = module.apply_rules(raw, [module.CleaningRule("rewrite_claim", "1", "semantic")], {})

    assert result["cleaned_blocks"][0]["cleaned_text"] == raw[0]["cleaned_text"]
    assert result["transformations"] == []
    assert result["review_items"][0]["reason"] == "semantic_change_forbidden"


def test_review_queue_and_publishable_filter_isolate_governance_risks():
    module = load_module()
    blocks = [
        block("approved", "ok", review_status="approved"),
        block("pending", "wait", review_status="pending_review"),
        block("fallback", "legacy", quality={"confidence": 1.0, "ocr_used": False, "issues": ["fallback_parser"]}),
        block("ocr", "unclear", quality={"confidence": 0.4, "ocr_used": True, "issues": ["low_confidence_ocr"]}),
        block("conflict", "x", review_status="conflict"),
    ]

    queue = module.build_review_queue(blocks)

    assert {item["block_id"] for item in queue} == {"pending", "fallback", "ocr", "conflict"}
    assert [item["block_id"] for item in module.publishable_blocks(blocks)] == ["approved"]


def test_heading_inference_is_audited_as_structural_change_without_mutating_raw():
    module = load_module()
    raw = [
        block("title", "Paper title", block_type="heading", heading_level=1),
        block("section", "1 Method", block_type="heading", heading_level=1),
        block("sub", "1.1 Input", block_type="heading", heading_level=1),
    ]
    snapshot = copy.deepcopy(raw)
    rule = module.CleaningRule(
        "infer_heading_hierarchy", "1", "structural", options={"source_format": "pdf"}
    )

    result = module.apply_rules(raw, [rule], {})
    by_id = {row["block_id"]: row for row in result["cleaned_blocks"]}

    assert raw == snapshot
    assert [by_id[name]["heading_level"] for name in ["title", "section", "sub"]] == [1, 2, 3]
    assert by_id["sub"]["parent_block_id"] == "section"
    assert by_id["section"]["review_status"] == "pending_review"
    assert result["transformations"][0]["evidence"]["candidates"]
    assert result["review_items"][0]["reason"] == "structural_change_requires_review"


def test_heading_inference_promotes_deterministic_fallback_paragraph():
    module = load_module()
    raw = [
        block("meta", "Network Working Group"),
        block("title", "A Border Gateway Protocol 4 (BGP-4)"),
        block("section", "1. Introduction"),
    ]
    rule = module.CleaningRule(
        "infer_heading_hierarchy", "1", "structural", options={"source_format": "txt"}
    )

    result = module.apply_rules(raw, [rule], {})
    by_id = {row["block_id"]: row for row in result["cleaned_blocks"]}

    assert by_id["title"]["block_type"] == "heading"
    assert by_id["section"]["block_type"] == "heading"
    assert by_id["section"]["heading_level"] == 2
