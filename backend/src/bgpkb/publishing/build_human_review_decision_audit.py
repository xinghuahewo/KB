#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
ENTITY_DIR = paths.ENTITIES_DIR
DATASET_DIR = paths.DATASETS_DIR
REVIEW_INPUT_DIR = paths.REVIEW_INPUTS_DIR
DECISION_INPUT = REVIEW_INPUT_DIR / "human_review_decisions.csv"
REPORT = paths.report_path("human_review_decision_audit_report")
JSONL_OUTPUT = DATASET_DIR / "human_review_decision_audit.jsonl"
CSV_OUTPUT = DATASET_DIR / "human_review_decision_audit.csv"
ALLOWED_DECISIONS = {"unreviewed", "approved", "rejected", "needs_source", "needs_semantic_review"}


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def load_entities_by_id():
    entities = {}
    for path in sorted(ENTITY_DIR.glob("*.jsonl")):
        for record in load_jsonl(path):
            entity_id = record.get("id")
            if entity_id:
                entities[entity_id] = {
                    "record": record,
                    "entity_file": path.relative_to(ROOT).as_posix(),
                }
    return entities


def load_review_input_decisions():
    decisions = {}
    errors = []
    duplicate_ids = set()
    if not DECISION_INPUT.exists():
        return decisions, errors, duplicate_ids
    with DECISION_INPUT.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row_number, row in enumerate(reader, start=2):
            entity_id = (row.get("entity_id") or "").strip()
            decision = (row.get("review_decision") or "").strip()
            if not entity_id and not decision:
                continue
            if not entity_id:
                errors.append(f"row {row_number}: 缺少 entity_id")
                continue
            if not decision or decision == "unreviewed":
                continue
            if decision not in ALLOWED_DECISIONS:
                errors.append(f"row {row_number}: review_decision `{decision}` 不在允许范围内")
                continue
            if entity_id in decisions:
                duplicate_ids.add(entity_id)
                errors.append(f"row {row_number}: entity_id `{entity_id}` 重复")
                continue
            decisions[entity_id] = {
                "review_decision": decision,
                "reviewer": (row.get("reviewer") or "").strip(),
                "reviewed_at": (row.get("reviewed_at") or "").strip(),
                "decision_note": (row.get("decision_note") or "").strip(),
                "row_number": row_number,
            }
    return decisions, errors, duplicate_ids


def audit_status(workbook_record, entity_record):
    decision = workbook_record.get("review_decision", "unreviewed")
    needs_llm = workbook_record.get("needs_llm") is True or decision == "needs_semantic_review"
    if entity_record is None:
        return "pending", "blocked_invalid_entity", False, "工作簿引用的实体不存在。", needs_llm
    current_status = entity_record.get("review_status", "pending")
    if decision == "unreviewed":
        return current_status, "no_op", False, "尚未人工复核，不应用任何实体状态变更。", needs_llm
    if decision == "approved":
        return "approved", "ready_to_apply", True, "人工已标记 approved；可由显式应用脚本更新实体 review_status。", needs_llm
    if decision == "rejected":
        return "rejected", "ready_to_apply", True, "人工已标记 rejected；可由显式应用脚本更新实体 review_status。", needs_llm
    if decision == "needs_source":
        return current_status, "manual_followup", False, "人工标记需要补充来源，实体应保持当前状态。", needs_llm
    if decision == "needs_semantic_review":
        return current_status, "blocked_by_llm", False, "该决策需要语义流程或 LLM，按当前规则跳过。", True
    return current_status, "manual_followup", False, "未知人工决策，实体应保持当前状态。", needs_llm


def build_records():
    entities = load_entities_by_id()
    review_input_decisions, review_input_errors, duplicate_input_entity_ids = load_review_input_decisions()
    workbook_entity_ids = set()
    records = []
    for workbook in load_jsonl(DATASET_DIR / "human_review_workbook.jsonl"):
        entity_id = workbook.get("entity_id", "")
        workbook_entity_ids.add(entity_id)
        input_decision = review_input_decisions.get(entity_id)
        audit_source = "data/review_inputs/human_review_decisions.csv" if input_decision else "workbook_default"
        workbook_for_audit = dict(workbook)
        if input_decision:
            workbook_for_audit["review_decision"] = input_decision["review_decision"]
            workbook_for_audit["needs_llm"] = input_decision["review_decision"] == "needs_semantic_review"
        entity_info = entities.get(entity_id)
        entity_record = entity_info["record"] if entity_info else None
        target_status, application_status, can_apply, blocking_reason, needs_llm = audit_status(workbook_for_audit, entity_record)
        records.append({
            "audit_id": f"decision_audit_{entity_id}",
            "workbook_id": workbook.get("workbook_id", ""),
            "entity_id": entity_id,
            "entity_type": workbook.get("entity_type", ""),
            "display_name": workbook.get("display_name", ""),
            "entity_file": entity_info["entity_file"] if entity_info else "",
            "current_review_status": entity_record.get("review_status", "") if entity_record else "",
            "review_decision": workbook_for_audit.get("review_decision", "unreviewed"),
            "target_review_status": target_status,
            "application_status": application_status,
            "can_apply": can_apply and not needs_llm,
            "blocking_reason": blocking_reason,
            "needs_llm": needs_llm,
            "decision_source": audit_source,
            "decision_reviewer": input_decision["reviewer"] if input_decision else "",
            "decision_reviewed_at": input_decision["reviewed_at"] if input_decision else "",
            "decision_note": input_decision["decision_note"] if input_decision else "",
            "generated_by": "src/bgpkb/pipeline/build_human_review_decision_audit.py",
        })
    records.sort(key=lambda item: (item["application_status"], item["entity_type"], item["display_name"].lower(), item["entity_id"]))
    unknown_input_entity_ids = sorted(set(review_input_decisions) - workbook_entity_ids)
    if unknown_input_entity_ids:
        for entity_id in unknown_input_entity_ids:
            review_input_errors.append(f"entity_id `{entity_id}` 不在当前人工复核工作簿中")
    return {
        "records": records,
        "review_input_count": len(review_input_decisions),
        "review_input_errors": review_input_errors,
        "duplicate_input_entity_ids": sorted(duplicate_input_entity_ids),
        "unknown_input_entity_ids": unknown_input_entity_ids,
    }


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "audit_id",
        "workbook_id",
        "entity_id",
        "entity_type",
        "display_name",
        "entity_file",
        "current_review_status",
        "review_decision",
        "target_review_status",
        "application_status",
        "can_apply",
        "blocking_reason",
        "needs_llm",
        "decision_source",
        "decision_reviewer",
        "decision_reviewed_at",
        "decision_note",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def write_report(result):
    records = result["records"]
    by_status = Counter(record["application_status"] for record in records)
    by_decision = Counter(record["review_decision"] for record in records)
    by_type = Counter(record["entity_type"] for record in records)
    by_source = Counter(record["decision_source"] for record in records)
    ready_to_apply = [record for record in records if record["application_status"] == "ready_to_apply"]
    llm_blocked = [record for record in records if record["needs_llm"]]
    lines = [
        "# 人工复核决策审计报告",
        "",
        "## 范围",
        "",
        "本报告从人工复核工作簿机械生成，用于审计人工决策是否可以被后续显式应用。该步骤不修改 data/knowledge/entities/*.jsonl，不自动批准或拒绝实体。",
        "",
        "## 摘要",
        "",
        f"- 审计记录数：{len(records)}",
        f"- 可应用记录数：{len(ready_to_apply)}",
        f"- 需要 LLM/语义流程而阻塞的记录数：{len(llm_blocked)}",
        f"- 人工决策输入记录数：{result['review_input_count']}",
        f"- 人工决策输入错误数：{len(result['review_input_errors'])}",
        f"- JSONL 输出：`data/derived/datasets/human_review_decision_audit.jsonl`",
        f"- CSV 输出：`data/derived/datasets/human_review_decision_audit.csv`",
        f"- 人工决策输入：`data/review_inputs/human_review_decisions.csv`",
        "",
        "## 按应用状态统计",
        "",
    ]
    for status, count in sorted(by_status.items()):
        lines.append(f"- {status}：{count}")
    lines.extend(["", "## 按人工决策统计", ""])
    for decision, count in sorted(by_decision.items()):
        lines.append(f"- {decision}：{count}")
    lines.extend(["", "## 按决策来源统计", ""])
    for source, count in sorted(by_source.items()):
        lines.append(f"- {source}：{count}")
    lines.extend(["", "## 按实体类型统计", ""])
    for entity_type, count in sorted(by_type.items()):
        lines.append(f"- {entity_type}：{count}")
    lines.extend(["", "## 人工决策输入错误", ""])
    if result["review_input_errors"]:
        for error in result["review_input_errors"][:50]:
            lines.append(f"- {error}")
    else:
        lines.append("- 无")
    lines.extend([
        "",
        "## 可应用决策",
        "",
    ])
    if ready_to_apply:
        for record in ready_to_apply[:50]:
            lines.append(f"- `{record['entity_id']}` -> {record['target_review_status']}（{record['entity_file']}）")
    else:
        lines.append("- 无")
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未自动修改实体文件；只有显式运行应用脚本时才应写入 review_status。",
        "- `needs_semantic_review` 决策需要语义流程或 LLM，按当前规则阻塞并记录。",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    result = build_records()
    records = result["records"]
    write_jsonl(records)
    write_csv(records)
    write_report(result)
    print(f"Wrote {JSONL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {CSV_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    if result["review_input_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
