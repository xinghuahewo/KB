#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "datasets"
REPORT = ROOT / "reports" / "human_review_workbook_report.md"
JSONL_OUTPUT = DATASET_DIR / "human_review_workbook.jsonl"
CSV_OUTPUT = DATASET_DIR / "human_review_workbook.csv"
CHUNK_SAMPLE_LIMIT = 12


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def action_by_entity():
    actions = {}
    for record in load_jsonl(DATASET_DIR / "next_action_queue.jsonl"):
        if record.get("action_type") == "entity_human_review" and record.get("entity_id"):
            actions[record["entity_id"]] = record
    return actions


def batch_for(packet):
    if packet.get("review_bucket") == "ready_without_manual_note":
        return "01_ready_without_manual_note"
    if packet.get("review_bucket") == "ready_with_manual_note":
        return "02_ready_with_manual_note"
    return "99_not_ready"


def decision_instructions_for(packet):
    if packet.get("review_bucket") == "ready_without_manual_note":
        return "人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。"
    if packet.get("review_bucket") == "ready_with_manual_note":
        return "人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。"
    return "该实体缺少可复核来源，应先补来源或保持 pending。"


def build_records():
    actions = action_by_entity()
    records = []
    for packet in load_jsonl(DATASET_DIR / "entity_review_packets.jsonl"):
        entity_id = packet.get("entity_id", "")
        action = actions.get(entity_id, {})
        priority = action.get("priority", 99)
        record = {
            "workbook_id": f"review_workbook_{entity_id}",
            "review_order": 0,
            "review_batch": batch_for(packet),
            "priority": priority,
            "entity_id": entity_id,
            "entity_type": packet.get("entity_type", ""),
            "display_name": packet.get("display_name", ""),
            "review_status": packet.get("review_status", "pending"),
            "review_bucket": packet.get("review_bucket", ""),
            "review_decision": "unreviewed",
            "source_refs": packet.get("source_refs", []),
            "source_paths": packet.get("source_paths", []),
            "parsed_paths": packet.get("parsed_paths", []),
            "cleaned_paths": packet.get("cleaned_paths", []),
            "chunk_sample_ids": packet.get("chunk_sample_ids", [])[:CHUNK_SAMPLE_LIMIT],
            "related_packet_id": packet.get("packet_id", ""),
            "related_action_id": action.get("action_id", ""),
            "needs_llm": False,
            "llm_skip_reason": "不需要 LLM；本记录只做人工来源复核入口。",
            "decision_instructions": decision_instructions_for(packet),
            "generated_by": "scripts/build_human_review_workbook.py",
        }
        records.append(record)

    records.sort(key=lambda item: (item["priority"], item["review_batch"], item["display_name"].lower(), item["entity_id"]))
    for index, record in enumerate(records, start=1):
        record["review_order"] = index
    return records


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "workbook_id",
        "review_order",
        "review_batch",
        "priority",
        "entity_id",
        "entity_type",
        "display_name",
        "review_status",
        "review_bucket",
        "review_decision",
        "source_refs",
        "source_paths",
        "parsed_paths",
        "cleaned_paths",
        "chunk_sample_ids",
        "related_packet_id",
        "related_action_id",
        "needs_llm",
        "llm_skip_reason",
        "decision_instructions",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = dict(record)
            for field in ("source_refs", "source_paths", "parsed_paths", "cleaned_paths", "chunk_sample_ids"):
                row[field] = "|".join(row[field])
            writer.writerow(row)


def write_report(records):
    by_batch = Counter(record["review_batch"] for record in records)
    by_type = Counter(record["entity_type"] for record in records)
    by_decision = Counter(record["review_decision"] for record in records)
    lines = [
        "# 人工复核工作簿报告",
        "",
        "## 范围",
        "",
        "本报告从实体人工复核包和下一步行动队列机械生成。该工作簿只提供人工复核入口，不自动批准、拒绝或改写任何实体。",
        "",
        "## 摘要",
        "",
        f"- 工作簿记录数：{len(records)}",
        f"- JSONL 输出：`datasets/human_review_workbook.jsonl`",
        f"- CSV 输出：`datasets/human_review_workbook.csv`",
        "- 默认 review_decision：`unreviewed`",
        f"- 每条最多保留 chunk_sample_ids：{CHUNK_SAMPLE_LIMIT}",
        "",
        "## 按复核批次统计",
        "",
    ]
    for batch, count in sorted(by_batch.items()):
        lines.append(f"- {batch}：{count}")
    lines.extend(["", "## 按实体类型统计", ""])
    for entity_type, count in sorted(by_type.items()):
        lines.append(f"- {entity_type}：{count}")
    lines.extend(["", "## 按人工决策状态统计", ""])
    for decision, count in sorted(by_decision.items()):
        lines.append(f"- {decision}：{count}")
    lines.extend([
        "",
        "## 前 30 条复核入口",
        "",
        "| 顺序 | 批次 | 实体类型 | 实体 ID | 名称 | 来源数 | chunk 样例数 |",
        "| ---: | --- | --- | --- | --- | ---: | ---: |",
    ])
    for record in records[:30]:
        lines.append(
            f"| {record['review_order']} | {record['review_batch']} | {record['entity_type']} | "
            f"`{record['entity_id']}` | {record['display_name']} | "
            f"{len(record['source_refs'])} | {len(record['chunk_sample_ids'])} |"
        )
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未使用 LLM 判断证据是否足以批准实体。",
        "- 未从论文正文或案例正文抽取新结构化字段。",
        "- 未自动修改 entities/*.jsonl 中的 review_status。",
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
