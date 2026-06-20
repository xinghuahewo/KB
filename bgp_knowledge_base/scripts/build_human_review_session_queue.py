#!/usr/bin/env python3
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "datasets"
REPORT = ROOT / "reports" / "human_review_session_queue_report.md"
JSONL_OUTPUT = DATASET_DIR / "human_review_session_queue.jsonl"
CSV_OUTPUT = DATASET_DIR / "human_review_session_queue.csv"

SESSION_SIZE = 10
TOP_EXTRACT_LIMIT = 3
DECISION_INPUT_PATH = "review_inputs/human_review_decisions.csv"


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def audit_by_entity():
    return {
        record.get("entity_id"): record
        for record in load_jsonl(DATASET_DIR / "human_review_decision_audit.jsonl")
        if record.get("entity_id")
    }


def extracts_by_entity():
    grouped = defaultdict(list)
    for record in load_jsonl(DATASET_DIR / "human_review_evidence_extracts.jsonl"):
        entity_id = record.get("entity_id")
        if entity_id:
            grouped[entity_id].append(record)
    for records in grouped.values():
        records.sort(key=lambda item: (item.get("chunk_rank", 999999), -item.get("match_score", 0), item.get("chunk_id", "")))
    return grouped


def queue_status_for(audit_record):
    status = audit_record.get("application_status", "no_op")
    if status == "ready_to_apply":
        return "ready_to_apply"
    if status == "blocked_by_llm":
        return "blocked_by_llm"
    if status == "manual_followup":
        return "manual_followup"
    return "awaiting_human_review"


def next_step_for(queue_status):
    if queue_status == "ready_to_apply":
        return "显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。"
    if queue_status == "blocked_by_llm":
        return "该项需要语义流程或 LLM，按当前规则跳过并保留记录。"
    if queue_status == "manual_followup":
        return "补充来源或记录人工说明；不要自动批准。"
    return f"打开摘录和来源路径，人工核验后在 {DECISION_INPUT_PATH} 填写决策。"


def build_records():
    audits = audit_by_entity()
    extracts = extracts_by_entity()
    workbook_records = sorted(
        load_jsonl(DATASET_DIR / "human_review_workbook.jsonl"),
        key=lambda item: (item.get("review_batch", ""), item.get("review_order", 999999), item.get("entity_id", "")),
    )
    records = []
    for index, workbook in enumerate(workbook_records, start=1):
        entity_id = workbook.get("entity_id", "")
        audit = audits.get(entity_id, {})
        queue_status = queue_status_for(audit)
        top_extracts = extracts.get(entity_id, [])[:TOP_EXTRACT_LIMIT]
        session_number = (index - 1) // SESSION_SIZE + 1
        within_session_order = (index - 1) % SESSION_SIZE + 1
        records.append({
            "session_item_id": f"review_session_item_{index:04d}",
            "session_id": f"review_session_{session_number:03d}",
            "session_order": session_number,
            "within_session_order": within_session_order,
            "global_review_order": index,
            "entity_id": entity_id,
            "entity_type": workbook.get("entity_type", ""),
            "display_name": workbook.get("display_name", ""),
            "review_batch": workbook.get("review_batch", ""),
            "review_bucket": workbook.get("review_bucket", ""),
            "review_status": workbook.get("review_status", ""),
            "review_decision": audit.get("review_decision", workbook.get("review_decision", "unreviewed")),
            "application_status": audit.get("application_status", "no_op"),
            "queue_status": queue_status,
            "source_refs": workbook.get("source_refs", []),
            "cleaned_paths": workbook.get("cleaned_paths", []),
            "parsed_paths": workbook.get("parsed_paths", []),
            "top_extract_ids": [record.get("extract_id", "") for record in top_extracts],
            "top_chunk_ids": [record.get("chunk_id", "") for record in top_extracts],
            "top_match_scores": [record.get("match_score", 0) for record in top_extracts],
            "decision_input_path": DECISION_INPUT_PATH,
            "next_step": next_step_for(queue_status),
            "needs_llm": queue_status == "blocked_by_llm",
            "generated_by": "scripts/build_human_review_session_queue.py",
        })
    return records


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "session_item_id",
        "session_id",
        "session_order",
        "within_session_order",
        "global_review_order",
        "entity_id",
        "entity_type",
        "display_name",
        "review_batch",
        "review_bucket",
        "review_status",
        "review_decision",
        "application_status",
        "queue_status",
        "source_refs",
        "cleaned_paths",
        "parsed_paths",
        "top_extract_ids",
        "top_chunk_ids",
        "top_match_scores",
        "decision_input_path",
        "next_step",
        "needs_llm",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = dict(record)
            for field in ("source_refs", "cleaned_paths", "parsed_paths", "top_extract_ids", "top_chunk_ids", "top_match_scores"):
                row[field] = "|".join(str(value) for value in row[field])
            writer.writerow(row)


def write_report(records):
    by_session = Counter(record["session_id"] for record in records)
    by_status = Counter(record["queue_status"] for record in records)
    by_type = Counter(record["entity_type"] for record in records)
    lines = [
        "# 人工复核会话队列报告",
        "",
        "## 范围",
        "",
        "本报告把人工复核工作簿和证据摘录机械切分为小批次会话。它只安排人工处理顺序，不判断实体是否应批准或拒绝。",
        "",
        "## 摘要",
        "",
        f"- 队列记录数：{len(records)}",
        f"- 会话大小：{SESSION_SIZE}",
        f"- 会话数：{len(by_session)}",
        f"- 每项最多引用摘录数：{TOP_EXTRACT_LIMIT}",
        f"- JSONL 输出：`datasets/human_review_session_queue.jsonl`",
        f"- CSV 输出：`datasets/human_review_session_queue.csv`",
        f"- 人工决策输入：`{DECISION_INPUT_PATH}`",
        "",
        "## 按队列状态统计",
        "",
    ]
    for status, count in sorted(by_status.items()):
        lines.append(f"- {status}：{count}")
    lines.extend(["", "## 按实体类型统计", ""])
    for entity_type, count in sorted(by_type.items()):
        lines.append(f"- {entity_type}：{count}")
    lines.extend(["", "## 前 5 个会话", ""])
    for session_id, count in sorted(by_session.items())[:5]:
        lines.append(f"- {session_id}：{count} 条")
    lines.extend([
        "",
        "## 第一会话条目",
        "",
        "| 顺序 | 实体 | 类型 | 名称 | 摘录 | 下一步 |",
        "| ---: | --- | --- | --- | --- | --- |",
    ])
    for record in records[:SESSION_SIZE]:
        extracts = "<br>".join(f"`{value}`" for value in record["top_extract_ids"]) or "无"
        lines.append(
            f"| {record['within_session_order']} | `{record['entity_id']}` | {record['entity_type']} | "
            f"{record['display_name']} | {extracts} | {record['next_step']} |"
        )
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未自动批准、拒绝或改写实体。",
        "- 未判断摘录是否足以支持实体字段。",
        "- `blocked_by_llm` 只作为状态保留，当前不执行语义流程或 LLM。",
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
