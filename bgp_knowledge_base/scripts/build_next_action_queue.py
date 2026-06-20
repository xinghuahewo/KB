#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "datasets"
REPORT = ROOT / "reports" / "next_action_queue_report.md"
JSONL_OUTPUT = DATASET_DIR / "next_action_queue.jsonl"
CSV_OUTPUT = DATASET_DIR / "next_action_queue.csv"


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def action_for_requirement(record):
    priority = 1 if record["requirement_type"] == "external_authoritative_source_needed" else 2
    return {
        "action_id": f"action_source_intake_{record['entity_id']}",
        "action_order": 0,
        "priority": priority,
        "action_type": "authoritative_source_intake",
        "status": "open",
        "scope_id": record["entity_id"],
        "entity_id": record["entity_id"],
        "entity_type": record["entity_type"],
        "display_name": record["display_name"],
        "review_bucket": record["review_bucket"],
        "source_refs": record.get("current_source_refs", []),
        "related_dataset": "datasets/authoritative_source_requirements.jsonl",
        "blocking_reason": "实体目前仅有 context_2026/manual_note 来源，不能进入批准复核。",
        "suggested_action": record["suggested_action"],
        "needs_llm": False,
        "skip_reason": "",
        "generated_by": "scripts/build_next_action_queue.py",
    }


def action_for_packet(record):
    priority = 3 if record["review_bucket"] == "ready_without_manual_note" else 4
    return {
        "action_id": f"action_entity_review_{record['entity_id']}",
        "action_order": 0,
        "priority": priority,
        "action_type": "entity_human_review",
        "status": "open",
        "scope_id": record["entity_id"],
        "entity_id": record["entity_id"],
        "entity_type": record["entity_type"],
        "display_name": record["display_name"],
        "review_bucket": record["review_bucket"],
        "source_refs": record.get("source_refs", []),
        "related_dataset": "datasets/entity_review_packets.jsonl",
        "blocking_reason": "实体仍为 pending，需要人工打开证据路径核验。",
        "suggested_action": record["suggested_action"],
        "needs_llm": False,
        "skip_reason": "",
        "generated_by": "scripts/build_next_action_queue.py",
    }


def skipped_semantic_actions():
    return [
        {
            "action_id": "action_skipped_paper_method_expansion",
            "action_order": 0,
            "priority": 90,
            "action_type": "semantic_task_skipped",
            "status": "skipped_by_policy",
            "scope_id": "paper_method_target_gap",
            "entity_id": "",
            "entity_type": "PaperMethod",
            "display_name": "PaperMethod 目标缺口",
            "review_bucket": "semantic_skip",
            "source_refs": [],
            "related_dataset": "entities/papers.jsonl",
            "blocking_reason": "PaperMethod 当前 3 条，目标 5 条。",
            "suggested_action": "明确允许语义流程后，再从论文正文扩展结构化方法。",
            "needs_llm": True,
            "skip_reason": "从论文正文扩展结构化方法需要语义判断或 LLM 介入，按用户要求跳过。",
            "generated_by": "scripts/build_next_action_queue.py",
        },
        {
            "action_id": "action_skipped_case_semantic_review",
            "action_order": 0,
            "priority": 91,
            "action_type": "semantic_task_skipped",
            "status": "skipped_by_policy",
            "scope_id": "case_observation_semantic_review",
            "entity_id": "",
            "entity_type": "CaseObservation",
            "display_name": "案例观察值语义核验",
            "review_bucket": "semantic_skip",
            "source_refs": [],
            "related_dataset": "datasets/case_observations.jsonl",
            "blocking_reason": "案例观察值已有 148 条，但事件角色、证据强度和影响范围需要语义判断。",
            "suggested_action": "明确允许语义流程后，再决定是否写入 entities/cases.jsonl 或扩展案例字段。",
            "needs_llm": True,
            "skip_reason": "事件角色、证据强度和影响范围判断需要语义流程或 LLM 介入，按用户要求跳过。",
            "generated_by": "scripts/build_next_action_queue.py",
        },
    ]


def build_records():
    records = []
    for requirement in load_jsonl(DATASET_DIR / "authoritative_source_requirements.jsonl"):
        records.append(action_for_requirement(requirement))
    for packet in load_jsonl(DATASET_DIR / "entity_review_packets.jsonl"):
        if packet.get("review_bucket") in {"ready_without_manual_note", "ready_with_manual_note"}:
            records.append(action_for_packet(packet))
    records.extend(skipped_semantic_actions())
    records.sort(key=lambda item: (item["priority"], item["action_type"], item["display_name"].lower(), item["scope_id"]))
    for index, record in enumerate(records, start=1):
        record["action_order"] = index
    return records


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "action_id",
        "action_order",
        "priority",
        "action_type",
        "status",
        "scope_id",
        "entity_id",
        "entity_type",
        "display_name",
        "review_bucket",
        "source_refs",
        "related_dataset",
        "blocking_reason",
        "suggested_action",
        "needs_llm",
        "skip_reason",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["source_refs"] = "|".join(row["source_refs"])
            writer.writerow(row)


def write_report(records):
    by_type = Counter(record["action_type"] for record in records)
    by_status = Counter(record["status"] for record in records)
    by_priority = Counter(record["priority"] for record in records)
    llm_skipped = [record for record in records if record["needs_llm"]]
    lines = [
        "# 下一步行动队列报告",
        "",
        "## 范围",
        "",
        "本报告把权威来源补充需求、实体人工复核包和必须跳过的语义任务合并成统一行动队列。该步骤只读已有结构化数据，不联网、不下载、不判断来源语义是否充分。",
        "",
        "## 摘要",
        "",
        f"- 行动记录数：{len(records)}",
        f"- JSONL 输出：`datasets/next_action_queue.jsonl`",
        f"- CSV 输出：`datasets/next_action_queue.csv`",
        f"- 因需要 LLM/语义判断而跳过的记录数：{len(llm_skipped)}",
        "",
        "## 按行动类型统计",
        "",
    ]
    for action_type, count in sorted(by_type.items()):
        lines.append(f"- {action_type}：{count}")
    lines.extend(["", "## 按状态统计", ""])
    for status, count in sorted(by_status.items()):
        lines.append(f"- {status}：{count}")
    lines.extend(["", "## 按优先级统计", ""])
    for priority, count in sorted(by_priority.items()):
        lines.append(f"- P{priority}：{count}")
    lines.extend([
        "",
        "## 前 30 条开放行动",
        "",
        "| 顺序 | 优先级 | 类型 | 范围 | 名称 | 建议动作 |",
        "| ---: | ---: | --- | --- | --- | --- |",
    ])
    for record in [item for item in records if item["status"] == "open"][:30]:
        lines.append(
            f"| {record['action_order']} | {record['priority']} | {record['action_type']} | "
            f"`{record['scope_id']}` | {record['display_name']} | {record['suggested_action']} |"
        )
    lines.extend(["", "## 跳过事项", ""])
    for record in llm_skipped:
        lines.append(f"- `{record['action_id']}`：{record['skip_reason']}")
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
