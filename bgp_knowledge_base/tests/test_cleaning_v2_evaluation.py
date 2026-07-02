import json

import pytest

from bgpkb.cleaning_v2 import evaluation


def test_load_annotations_reads_pretty_json_array_and_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "annotations.json"
    path.write_text(json.dumps([{"doc_id": "a"}, {"doc_id": "b"}], indent=2), encoding="utf-8")

    assert [row["doc_id"] for row in evaluation.load_annotations(path)] == ["a", "b"]

    path.write_text(json.dumps([{"doc_id": "a"}, {"doc_id": "a"}], indent=2), encoding="utf-8")
    with pytest.raises(ValueError, match="重复 doc_id"):
        evaluation.load_annotations(path)


def test_heading_hierarchy_f1_matches_text_and_level():
    gold = [{"text": "Scope", "level": 1}, {"text": "Limits", "level": 2}]
    predicted = [{"text": "Scope", "level": 1}, {"text": "Limits", "level": 3}]

    assert evaluation.heading_hierarchy_f1(gold, predicted) == 0.5


def test_reading_order_accuracy_uses_pairwise_order_not_only_item_presence():
    gold = ["a", "b", "c"]
    predicted = ["a", "c", "b"]

    assert evaluation.reading_order_accuracy(gold, predicted) == 2 / 3


def test_table_structure_accuracy_scores_coordinates_spans_and_text():
    gold = [
        {"row": 0, "column": 0, "row_span": 1, "column_span": 1, "text": "State"},
        {"row": 1, "column": 0, "row_span": 1, "column_span": 2, "text": "Valid"},
    ]
    predicted = [gold[0], {**gold[1], "column_span": 1}]

    assert evaluation.table_structure_accuracy(gold, predicted) == 0.5


def test_ocr_character_error_rate_uses_levenshtein_distance():
    assert evaluation.ocr_character_error_rate("route origin", "route orxgin") == 1 / 12
    assert evaluation.ocr_character_error_rate("", "") == 0.0


def test_assisted_annotation_builds_reviewable_hierarchy_order_and_table_cells():
    template = {"doc_id": "paper", "annotation_status": "pending", "notes": ""}
    document = {
        "blocks": [
            {"block_id": "title", "block_type": "title", "cleaned_text": "Paper title", "heading_level": 1},
            {"block_id": "section", "block_type": "heading", "cleaned_text": "II. METHOD", "heading_level": 1},
            {"block_id": "sub", "block_type": "heading", "cleaned_text": "A. Input", "heading_level": 1},
            {"block_id": "table", "block_type": "table", "cleaned_text": "", "table": {"cells": [{"row": 0, "column": 0, "row_span": 1, "column_span": 1, "text": "Metric"}]}},
        ]
    }

    row = evaluation.build_assisted_annotation(template, document)

    assert row["annotation_method"] == "codex_assisted"
    assert row["verification_status"] == "pending"
    assert row["annotation_status"] == "completed"
    assert [item["level"] for item in row["headings"]] == [1, 2, 3]
    assert row["reading_order"] == ["title", "section", "sub", "table"]
    assert row["table_cells"][0]["text"] == "Metric"
    assert evaluation.build_assisted_annotation(row, document) == row


def test_assisted_annotation_recovers_rfc_and_yaml_headings_from_fallback_paragraphs():
    rfc = evaluation.build_assisted_annotation(
        {"doc_id": "rfc", "source_format": "txt", "notes": ""},
        {"blocks": [
            {"block_id": "meta", "block_type": "paragraph", "cleaned_text": "Network Working Group"},
            {"block_id": "title", "block_type": "paragraph", "cleaned_text": "A Border Gateway Protocol 4 (BGP-4)"},
            {"block_id": "s1", "block_type": "paragraph", "cleaned_text": "1. Introduction"},
            {"block_id": "s11", "block_type": "paragraph", "cleaned_text": "1.1. Terms"},
        ]},
    )
    yaml_row = evaluation.build_assisted_annotation(
        {"doc_id": "api", "source_format": "yaml", "notes": ""},
        {"blocks": [
            {"block_id": "info", "block_type": "paragraph", "cleaned_text": "info:\n  title: Example API"},
            {"block_id": "paths", "block_type": "paragraph", "cleaned_text": "paths:\n  /items: {}"},
        ]},
    )

    assert rfc["headings"] == [
        {"text": "A Border Gateway Protocol 4 (BGP-4)", "level": 1},
        {"text": "1. Introduction", "level": 2},
        {"text": "1.1. Terms", "level": 3},
    ]
    assert [item["text"] for item in yaml_row["headings"]] == ["Example API", "info", "paths"]


def test_evaluation_thresholds_fail_closed_for_pending_or_low_metrics():
    pending = evaluation.evaluate_acceptance([], expected_document_count=12)
    assert pending["passed"] is False
    assert pending["blocking_issues"] == ["gold_annotations_incomplete"]

    assisted = [
        {
            "annotation_status": "completed",
            "verification_status": "codex_assisted",
            "heading_hierarchy_f1": 1.0,
            "reading_order_accuracy": 1.0,
            "table_structure_accuracy": 1.0,
            "ocr_character_error_rate": 0.0,
        }
        for _ in range(12)
    ]
    assert evaluation.evaluate_acceptance(assisted, expected_document_count=12)["blocking_issues"] == [
        "gold_annotations_not_human_verified"
    ]

    rows = [
        {
            "annotation_status": "completed",
            "verification_status": "human_verified",
            "heading_hierarchy_f1": 0.94,
            "reading_order_accuracy": 0.99,
            "table_structure_accuracy": 0.96,
            "ocr_character_error_rate": 0.01,
        }
        for _ in range(12)
    ]
    result = evaluation.evaluate_acceptance(rows, expected_document_count=12)
    assert result["passed"] is False
    assert result["blocking_issues"] == ["heading_hierarchy_f1_below_threshold"]
