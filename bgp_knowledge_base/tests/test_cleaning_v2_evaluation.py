from bgpkb.cleaning_v2 import evaluation


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


def test_evaluation_thresholds_fail_closed_for_pending_or_low_metrics():
    pending = evaluation.evaluate_acceptance([], expected_document_count=12)
    assert pending["passed"] is False
    assert pending["blocking_issues"] == ["gold_annotations_incomplete"]

    rows = [
        {
            "annotation_status": "completed",
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
