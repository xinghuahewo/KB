#!/usr/bin/env python3
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "datasets"
REPORT = ROOT / "reports" / "human_review_source_matrix_report.md"
JSONL_OUTPUT = DATASET_DIR / "human_review_source_matrix.jsonl"
CSV_OUTPUT = DATASET_DIR / "human_review_source_matrix.csv"

DECISION_INPUT_PATH = "review_inputs/human_review_decisions.csv"
GENERATED_BY = "scripts/build_human_review_source_matrix.py"


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def load_sources():
    with (ROOT / "inventory" / "sources.csv").open(newline="", encoding="utf-8") as handle:
        return {
            row.get("source_id"): row
            for row in csv.DictReader(handle)
            if row.get("source_id")
        }


def source_status_by_id():
    return {
        record.get("source_id"): record
        for record in load_jsonl(DATASET_DIR / "source_processing_status.jsonl")
        if record.get("source_id")
    }


def queue_by_entity():
    return {
        record.get("entity_id"): record
        for record in load_jsonl(DATASET_DIR / "human_review_session_queue.jsonl")
        if record.get("entity_id")
    }


def field_count_by_entity():
    counts = Counter()
    for record in load_jsonl(DATASET_DIR / "human_review_field_checklist.jsonl"):
        entity_id = record.get("entity_id")
        if entity_id:
            counts[entity_id] += 1
    return counts


def unique_sorted(values):
    return sorted({value for value in values if value})


def build_records():
    inventory = load_sources()
    statuses = source_status_by_id()
    queue = queue_by_entity()
    field_counts = field_count_by_entity()
    grouped = defaultdict(list)
    for evidence in load_jsonl(DATASET_DIR / "entity_source_evidence.jsonl"):
        entity_id = evidence.get("entity_id")
        source_id = evidence.get("source_id")
        if entity_id in queue and source_id:
            grouped[source_id].append(evidence)

    records = []
    for source_id in sorted(grouped):
        evidence_records = grouped[source_id]
        entity_ids = unique_sorted(record.get("entity_id") for record in evidence_records)
        queue_records = [queue[entity_id] for entity_id in entity_ids if entity_id in queue]
        source = inventory.get(source_id, {})
        status = statuses.get(source_id, {})
        records.append({
            "source_matrix_id": f"source_matrix_{source_id}",
            "source_id": source_id,
            "source_title": source.get("title", source_id),
            "source_type": source.get("source_type") or status.get("source_type", ""),
            "source_path": source.get("path") or status.get("path", ""),
            "trust_level": source.get("trust_level", ""),
            "inventory_review_status": source.get("review_status", ""),
            "processing_status": status.get("processing_status", ""),
            "raw_status": status.get("raw_status", ""),
            "parsed_status": status.get("parsed_status", ""),
            "cleaned_status": status.get("cleaned_status", ""),
            "source_chunk_count": status.get("chunk_count", 0),
            "evidence_record_count": len(evidence_records),
            "entity_count": len(entity_ids),
            "field_check_count": sum(field_counts.get(entity_id, 0) for entity_id in entity_ids),
            "session_ids": unique_sorted(record.get("session_id") for record in queue_records),
            "entity_types": unique_sorted(record.get("entity_type") for record in queue_records),
            "sample_entity_ids": entity_ids[:12],
            "cleaned_paths": unique_sorted(record.get("cleaned_path") for record in evidence_records),
            "parsed_paths": unique_sorted(record.get("parsed_path") for record in evidence_records),
            "chunk_sample_ids": unique_sorted(
                chunk_id
                for record in evidence_records
                for chunk_id in record.get("chunk_sample_ids", [])[:5]
            )[:20],
            "decision_input_path": DECISION_INPUT_PATH,
            "generated_by": GENERATED_BY,
        })
    records.sort(key=lambda item: (-item["entity_count"], -item["field_check_count"], item["source_id"]))
    return records


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "source_matrix_id",
        "source_id",
        "source_title",
        "source_type",
        "source_path",
        "trust_level",
        "inventory_review_status",
        "processing_status",
        "raw_status",
        "parsed_status",
        "cleaned_status",
        "source_chunk_count",
        "evidence_record_count",
        "entity_count",
        "field_check_count",
        "session_ids",
        "entity_types",
        "sample_entity_ids",
        "cleaned_paths",
        "parsed_paths",
        "chunk_sample_ids",
        "decision_input_path",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = dict(record)
            for field in ("session_ids", "entity_types", "sample_entity_ids", "cleaned_paths", "parsed_paths", "chunk_sample_ids"):
                row[field] = "|".join(row[field])
            writer.writerow(row)


def write_report(records):
    by_type = Counter(record["source_type"] for record in records)
    by_status = Counter(record["processing_status"] for record in records)
    total_entities = sum(record["entity_count"] for record in records)
    lines = [
        "# 人工复核来源矩阵报告",
        "",
        "## 范围",
        "",
        "本报告按来源聚合待人工复核实体、字段核验项、session 和证据路径，帮助人工按高复用来源批量核验。它不判断来源是否足够支持实体字段，不调用 LLM，也不修改实体状态。",
        "",
        "## 摘要",
        "",
        f"- 来源记录数：{len(records)}",
        f"- 来源-实体引用数：{total_entities}",
        f"- JSONL 输出：`datasets/human_review_source_matrix.jsonl`",
        f"- CSV 输出：`datasets/human_review_source_matrix.csv`",
        f"- 人工决策输入：`{DECISION_INPUT_PATH}`",
        "",
        "## 按来源类型统计",
        "",
    ]
    for source_type, count in sorted(by_type.items()):
        lines.append(f"- {source_type}：{count}")
    lines.extend(["", "## 按处理状态统计", ""])
    for status, count in sorted(by_status.items()):
        lines.append(f"- {status}：{count}")
    lines.extend([
        "",
        "## 高复用来源前 30 个",
        "",
        "| 来源 | 类型 | 实体数 | 字段核验项 | session | 路径 |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ])
    for record in records[:30]:
        sessions = "<br>".join(f"`{value}`" for value in record["session_ids"]) or "无"
        lines.append(
            f"| `{record['source_id']}` | {record['source_type']} | {record['entity_count']} | "
            f"{record['field_check_count']} | {sessions} | `{record['source_path']}` |"
        )
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未判断来源是否足以批准实体。",
        "- 未自动批准、拒绝或改写实体。",
        "- 需要解释、归纳或证据强度判断时，仍按规则记录为 `needs_semantic_review` 或保持 `unreviewed`。",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    records = build_records()
    write_jsonl(records)
    write_csv(records)
    write_report(records)
    print(f"Wrote {JSONL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {CSV_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
