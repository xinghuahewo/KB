#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTITY_DIR = ROOT / "entities"
DATASET_DIR = ROOT / "datasets"
REPORT = ROOT / "reports" / "entity_review_queue_report.md"
JSONL_OUTPUT = DATASET_DIR / "entity_review_queue.jsonl"
CSV_OUTPUT = DATASET_DIR / "entity_review_queue.csv"

READY_SOURCE_STATUSES = {"complete_deterministic", "manual_note"}


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def load_entities():
    records = []
    for path in sorted(ENTITY_DIR.glob("*.jsonl")):
        for record in load_jsonl(path):
            record["_entity_file"] = path.name
            records.append(record)
    return records


def load_source_statuses():
    statuses = {}
    for record in load_jsonl(DATASET_DIR / "source_processing_status.jsonl"):
        statuses[record["source_id"]] = record["processing_status"]
    return statuses


def text_value(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "；".join(str(item).strip() for item in value if str(item).strip())
    if value is None:
        return ""
    return str(value)


def name_for(record):
    for field in ("name", "paper", "applies_to", "id"):
        value = text_value(record.get(field))
        if value:
            return value
    return ""


def build_item(record, source_statuses):
    source_refs = [str(ref) for ref in record.get("source_refs", []) if str(ref).strip()]
    source_processing_statuses = [
        f"{source_id}:{source_statuses.get(source_id, 'unknown_source')}"
        for source_id in source_refs
    ]
    blocked_source_refs = [
        source_id
        for source_id in source_refs
        if source_statuses.get(source_id) not in READY_SOURCE_STATUSES
    ]
    if not source_refs:
        suggested_action = "add_source_refs_before_review"
    elif blocked_source_refs:
        suggested_action = "resolve_source_gaps_first"
    else:
        suggested_action = "human_review_ready"
    return {
        "queue_id": f"review_{record['id']}",
        "entity_id": record["id"],
        "entity_type": record.get("entity_type", ""),
        "name": name_for(record),
        "review_status": record.get("review_status", "pending"),
        "source_refs": source_refs,
        "source_ref_count": len(source_refs),
        "source_processing_statuses": source_processing_statuses,
        "blocked_source_refs": blocked_source_refs,
        "suggested_action": suggested_action,
        "generated_by": "scripts/build_entity_review_queue.py",
    }


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "queue_id",
        "entity_id",
        "entity_type",
        "name",
        "review_status",
        "source_refs",
        "source_ref_count",
        "source_processing_statuses",
        "blocked_source_refs",
        "suggested_action",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["source_refs"] = "|".join(record["source_refs"])
            row["source_processing_statuses"] = "|".join(record["source_processing_statuses"])
            row["blocked_source_refs"] = "|".join(record["blocked_source_refs"])
            writer.writerow(row)


def write_report(records):
    by_type = Counter(record["entity_type"] for record in records)
    by_action = Counter(record["suggested_action"] for record in records)
    lines = [
        "# 实体复核队列报告",
        "",
        "## 范围",
        "",
        "本报告从 `entities/*.jsonl` 和 `datasets/source_processing_status.jsonl` 机械生成待复核队列。该步骤不改变实体审核状态，不判断定义是否正确，只标出来源处理状态是否足以进入人工复核。",
        "",
        "## 摘要",
        "",
        f"- 队列记录数：{len(records)}",
        f"- JSONL 输出：`datasets/entity_review_queue.jsonl`",
        f"- CSV 输出：`datasets/entity_review_queue.csv`",
        "",
        "## 按建议动作统计",
        "",
    ]
    for action, count in sorted(by_action.items()):
        lines.append(f"- {action}：{count}")
    lines.extend(["", "## 按实体类型统计", ""])
    for entity_type, count in sorted(by_type.items()):
        lines.append(f"- {entity_type}：{count}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    source_statuses = load_source_statuses()
    entities = [
        record
        for record in load_entities()
        if record.get("review_status") == "pending"
    ]
    records = [build_item(record, source_statuses) for record in entities]
    records.sort(key=lambda item: (item["suggested_action"], item["entity_type"], item["entity_id"]))
    write_jsonl(records)
    write_csv(records)
    write_report(records)
    print(f"Wrote {JSONL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {CSV_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
