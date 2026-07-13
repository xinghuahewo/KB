#!/usr/bin/env python3
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
DATASET_DIR = paths.DATASETS_DIR
REPORT = paths.report_path("human_review_session_status_report")
JSONL_OUTPUT = DATASET_DIR / "human_review_session_status.jsonl"
CSV_OUTPUT = DATASET_DIR / "human_review_session_status.csv"

QUEUE_INPUT = DATASET_DIR / "human_review_session_queue.jsonl"
DECISION_INPUT_PATH = "data/review_inputs/human_review_decisions.csv"
GENERATED_BY = "src/bgpkb/pipeline/build_human_review_session_status.py"

QUEUE_STATUSES = [
    "awaiting_human_review",
    "ready_to_apply",
    "manual_followup",
    "blocked_by_llm",
]
DECISIONS = [
    "unreviewed",
    "approved",
    "rejected",
    "needs_source",
    "needs_semantic_review",
]


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def next_record(records):
    for status in QUEUE_STATUSES:
        for record in records:
            if record.get("queue_status") == status:
                return record
    return None


def build_records():
    grouped = defaultdict(list)
    for record in load_jsonl(QUEUE_INPUT):
        grouped[record.get("session_id", "")].append(record)

    status_records = []
    for session_id in sorted(grouped):
        items = sorted(
            grouped[session_id],
            key=lambda item: (
                item.get("within_session_order", 999999),
                item.get("global_review_order", 999999),
                item.get("entity_id", ""),
            ),
        )
        queue_counts = Counter(item.get("queue_status", "") for item in items)
        decision_counts = Counter(item.get("review_decision", "") for item in items)
        item_count = len(items)
        completed_count = decision_counts["approved"] + decision_counts["rejected"]
        next_item = next_record(items)
        session_order = items[0].get("session_order", 0) if items else 0
        status_records.append({
            "session_status_id": f"{session_id}_status",
            "session_id": session_id,
            "session_order": session_order,
            "item_count": item_count,
            "awaiting_human_review_count": queue_counts["awaiting_human_review"],
            "ready_to_apply_count": queue_counts["ready_to_apply"],
            "manual_followup_count": queue_counts["manual_followup"],
            "blocked_by_llm_count": queue_counts["blocked_by_llm"],
            "unreviewed_decision_count": decision_counts["unreviewed"],
            "approved_decision_count": decision_counts["approved"],
            "rejected_decision_count": decision_counts["rejected"],
            "needs_source_decision_count": decision_counts["needs_source"],
            "needs_semantic_review_decision_count": decision_counts["needs_semantic_review"],
            "completion_percent": round((completed_count / item_count) * 100, 2) if item_count else 0.0,
            "next_entity_id": next_item.get("entity_id", "") if next_item else "none",
            "next_display_name": next_item.get("display_name", "") if next_item else "无",
            "decision_input_path": items[0].get("decision_input_path", DECISION_INPUT_PATH) if items else DECISION_INPUT_PATH,
            "needs_llm_count": sum(1 for item in items if item.get("needs_llm") is True),
            "generated_by": GENERATED_BY,
        })
    status_records.sort(key=lambda item: (item["session_order"], item["session_id"]))
    return status_records


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "session_status_id",
        "session_id",
        "session_order",
        "item_count",
        "awaiting_human_review_count",
        "ready_to_apply_count",
        "manual_followup_count",
        "blocked_by_llm_count",
        "unreviewed_decision_count",
        "approved_decision_count",
        "rejected_decision_count",
        "needs_source_decision_count",
        "needs_semantic_review_decision_count",
        "completion_percent",
        "next_entity_id",
        "next_display_name",
        "decision_input_path",
        "needs_llm_count",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def write_report(records):
    total_items = sum(record["item_count"] for record in records)
    total_ready = sum(record["ready_to_apply_count"] for record in records)
    total_followup = sum(record["manual_followup_count"] for record in records)
    total_blocked = sum(record["blocked_by_llm_count"] for record in records)
    total_awaiting = sum(record["awaiting_human_review_count"] for record in records)
    total_completed = sum(
        record["approved_decision_count"] + record["rejected_decision_count"]
        for record in records
    )
    completion = round((total_completed / total_items) * 100, 2) if total_items else 0.0

    lines = [
        "# 人工复核会话状态报告",
        "",
        "## 范围",
        "",
        "本报告从人工复核会话队列机械汇总每个 session 的进度、状态计数和下一条待处理实体。它不判断证据充分性，不批准或拒绝实体，也不调用 LLM。",
        "",
        "## 摘要",
        "",
        f"- 会话数：{len(records)}",
        f"- 队列实体数：{total_items}",
        f"- 已完成决策数（approved/rejected）：{total_completed}",
        f"- 总完成率：{completion}%",
        f"- 等待人工复核数：{total_awaiting}",
        f"- 可显式应用数：{total_ready}",
        f"- 需人工补充数：{total_followup}",
        f"- LLM/语义流程阻塞数：{total_blocked}",
        f"- JSONL 输出：`data/derived/datasets/human_review_session_status.jsonl`",
        f"- CSV 输出：`data/derived/datasets/human_review_session_status.csv`",
        f"- 人工决策输入：`{DECISION_INPUT_PATH}`",
        "",
        "## Session 状态",
        "",
        "| Session | 条目 | 完成率 | 等待人工 | 可应用 | 需补充 | LLM 阻塞 | 下一实体 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for record in records:
        lines.append(
            f"| `{record['session_id']}` | {record['item_count']} | {record['completion_percent']}% | "
            f"{record['awaiting_human_review_count']} | {record['ready_to_apply_count']} | "
            f"{record['manual_followup_count']} | {record['blocked_by_llm_count']} | "
            f"`{record['next_entity_id']}` / {record['next_display_name']} |"
        )
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未自动批准、拒绝或改写实体。",
        "- 未判断摘录是否足以支持实体字段。",
        "- 需要 LLM 或语义判断的条目只统计为阻塞，不在本流程处理。",
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
