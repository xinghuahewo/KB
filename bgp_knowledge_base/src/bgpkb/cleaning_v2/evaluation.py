"""高风险人工金标集的结构与 OCR 评测指标。"""

from __future__ import annotations

import json
from pathlib import Path
import re


def load_annotations(path):
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("标注文件必须是 JSON 数组")
    doc_ids = [row.get("doc_id") for row in rows]
    duplicates = sorted({doc_id for doc_id in doc_ids if doc_ids.count(doc_id) > 1})
    if duplicates:
        raise ValueError("重复 doc_id: " + ", ".join(duplicates))
    return rows


def _assisted_heading_level(text, *, first_heading):
    text = " ".join(str(text).split())
    if first_heading:
        return 1
    if re.match(r"^(?:[IVXLCDM]+\.|\d+(?:\.\d+)*[.)]?)\s+", text, flags=re.IGNORECASE):
        depth = text.split(maxsplit=1)[0].count(".")
        return min(6, 2 + max(0, depth - 1))
    if re.match(r"^[A-Z][.)]\s+", text):
        return 3
    if text.upper() in {"REFERENCES", "APPENDIX", "ACKNOWLEDGMENTS", "ACKNOWLEDGEMENTS"}:
        return 2
    return 2


def build_assisted_annotation(template, document):
    row = dict(template)
    base_notes = str(row.get("notes", "")).split("；Codex 已生成辅助标注", 1)[0]
    if base_notes == "Codex 已生成辅助标注，待人工抽查确认。":
        base_notes = ""
    headings = []
    reading_order = []
    table_cells = []
    first_heading = True
    ocr_parts = []
    for block in document.get("blocks", []):
        block_type = block.get("block_type")
        text = " ".join(str(block.get("cleaned_text", "")).split())
        if block_type in {"title", "heading"} and text:
            headings.append(
                {"text": text, "level": _assisted_heading_level(text, first_heading=first_heading)}
            )
            first_heading = False
            reading_order.append(block["block_id"])
        elif block_type == "table":
            reading_order.append(block["block_id"])
            for cell in block.get("table", {}).get("cells", []):
                table_cells.append(
                    {
                        "table_block_id": block["block_id"],
                        "row": int(cell.get("row", 0)),
                        "column": int(cell.get("column", 0)),
                        "row_span": int(cell.get("row_span", 1)),
                        "column_span": int(cell.get("column_span", 1)),
                        "text": str(cell.get("text", "")),
                    }
                )
        if block.get("quality", {}).get("ocr_used"):
            ocr_text = block.get("provenance", {}).get("ocr_text") or text
            if ocr_text:
                ocr_parts.append(str(ocr_text))
    if not headings and row.get("source_format") == "txt":
        blocks = document.get("blocks", [])
        metadata_prefixes = ("Network Working Group", "Request for Comments:", "Obsoletes:", "Category:")
        title_block = next(
            (
                block for block in blocks[:20]
                if 20 <= len(" ".join(str(block.get("cleaned_text", "")).split())) <= 120
                and not " ".join(str(block.get("cleaned_text", "")).split()).startswith(metadata_prefixes)
            ),
            None,
        )
        if title_block is not None:
            title_text = " ".join(str(title_block.get("cleaned_text", "")).split())
            headings.append({"text": title_text, "level": 1})
            reading_order.append(title_block["block_id"])
        known = {
            "Introduction", "Acknowledgements", "References", "Security Considerations",
            "IANA Considerations", "Status of This Memo", "Copyright Notice", "Abstract",
        }
        for block in blocks:
            text = " ".join(str(block.get("cleaned_text", "")).split())
            match = re.match(r"^(\d+(?:\.\d+)*)\.\s+(.+)$", text)
            if match and len(text) <= 160 and "..." not in text:
                level = min(6, 1 + len(match.group(1).split(".")))
            elif text in known:
                level = 2
            else:
                continue
            if not any(item["text"] == text for item in headings):
                headings.append({"text": text, "level": level})
                reading_order.append(block["block_id"])
    elif not headings and row.get("source_format") in {"yaml", "yml"}:
        blocks = document.get("blocks", [])
        title = None
        for block in blocks:
            raw_text = str(block.get("cleaned_text", ""))
            match = re.search(r"^\s*title:\s*(.+)$", raw_text, flags=re.MULTILINE)
            if match:
                title = match.group(1).strip().strip('"\'')
                break
        if title:
            headings.append({"text": title, "level": 1})
        for block in blocks:
            raw_text = str(block.get("cleaned_text", ""))
            match = re.match(r"^([A-Za-z0-9_-]+):", raw_text)
            if match:
                headings.append({"text": match.group(1), "level": 2})
                reading_order.append(block["block_id"])
    row.update(
        {
            "annotation_status": "completed",
            "annotation_method": "codex_assisted",
            "verification_status": "pending",
            "annotator": "codex",
            "headings": headings,
            "reading_order": reading_order,
            "table_cells": table_cells,
            "ocr_gold_text": "\n".join(ocr_parts),
            "notes": (base_notes.rstrip("。") + "；Codex 已生成辅助标注，待人工抽查确认。").lstrip("；"),
        }
    )
    return row


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
    if any(row.get("verification_status") != "human_verified" for row in rows):
        return {"passed": False, "blocking_issues": ["gold_annotations_not_human_verified"], "metrics": {}}
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
