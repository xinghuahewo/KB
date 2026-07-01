"""高风险人工金标集的结构与 OCR 评测指标。"""

from __future__ import annotations


def heading_hierarchy_f1(gold, predicted):
    gold_items = {(str(row["text"]).strip(), int(row["level"])) for row in gold}
    predicted_items = {(str(row["text"]).strip(), int(row["level"])) for row in predicted}
    if not gold_items and not predicted_items:
        return 1.0
    true_positive = len(gold_items & predicted_items)
    precision = true_positive / len(predicted_items) if predicted_items else 0.0
    recall = true_positive / len(gold_items) if gold_items else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def reading_order_accuracy(gold_ids, predicted_ids):
    common = [item for item in gold_ids if item in set(predicted_ids)]
    if len(common) < 2:
        return 1.0 if list(gold_ids) == list(predicted_ids) else 0.0
    predicted_position = {item: index for index, item in enumerate(predicted_ids)}
    pairs = [(left, right) for index, left in enumerate(common) for right in common[index + 1 :]]
    correct = sum(predicted_position[left] < predicted_position[right] for left, right in pairs)
    return correct / len(pairs)


def _cell_identity(cell):
    return (
        int(cell.get("row", 0)), int(cell.get("column", 0)),
        int(cell.get("row_span", 1)), int(cell.get("column_span", 1)),
        " ".join(str(cell.get("text", "")).split()),
    )


def table_structure_accuracy(gold_cells, predicted_cells):
    gold = {_cell_identity(cell) for cell in gold_cells}
    predicted = {_cell_identity(cell) for cell in predicted_cells}
    if not gold and not predicted:
        return 1.0
    denominator = max(len(gold), len(predicted))
    return len(gold & predicted) / denominator if denominator else 0.0


def _levenshtein(left, right):
    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + (left_char != right_char),
                )
            )
        previous = current
    return previous[-1]


def ocr_character_error_rate(gold_text, predicted_text):
    if not gold_text:
        return 0.0 if not predicted_text else 1.0
    return _levenshtein(gold_text, predicted_text) / len(gold_text)


def evaluate_acceptance(rows, *, expected_document_count=12):
    if len(rows) != expected_document_count or any(row.get("annotation_status") != "completed" for row in rows):
        return {"passed": False, "blocking_issues": ["gold_annotations_incomplete"], "metrics": {}}
    metrics = {
        "heading_hierarchy_f1": sum(row["heading_hierarchy_f1"] for row in rows) / len(rows),
        "reading_order_accuracy": sum(row["reading_order_accuracy"] for row in rows) / len(rows),
        "table_structure_accuracy": sum(row["table_structure_accuracy"] for row in rows) / len(rows),
        "ocr_character_error_rate": sum(row["ocr_character_error_rate"] for row in rows) / len(rows),
    }
    issues = []
    if metrics["heading_hierarchy_f1"] < 0.95:
        issues.append("heading_hierarchy_f1_below_threshold")
    if metrics["reading_order_accuracy"] < 0.98:
        issues.append("reading_order_accuracy_below_threshold")
    if metrics["table_structure_accuracy"] < 0.95:
        issues.append("table_structure_accuracy_below_threshold")
    if metrics["ocr_character_error_rate"] > 0.02:
        issues.append("ocr_character_error_rate_above_threshold")
    return {"passed": not issues, "blocking_issues": issues, "metrics": metrics}
