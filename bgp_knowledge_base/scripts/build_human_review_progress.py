#!/usr/bin/env python3
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "datasets"
REPORT = ROOT / "reports" / "human_review_progress_report.md"
JSONL_OUTPUT = DATASET_DIR / "human_review_progress.jsonl"
CSV_OUTPUT = DATASET_DIR / "human_review_progress.csv"


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def rows_by_entity(records):
    return {record.get("entity_id"): record for record in records if record.get("entity_id")}


def count_review_status(records):
    counts = Counter(record.get("review_status", "unknown") for record in records)
    return {
        "pending_count": counts.get("pending", 0),
        "approved_count": counts.get("approved", 0),
        "rejected_count": counts.get("rejected", 0),
    }


def count_decisions(audit_records):
    decision_counts = Counter(record.get("review_decision", "unknown") for record in audit_records)
    status_counts = Counter(record.get("application_status", "unknown") for record in audit_records)
    return {
        "unreviewed_decision_count": decision_counts.get("unreviewed", 0),
        "approved_decision_count": decision_counts.get("approved", 0),
        "rejected_decision_count": decision_counts.get("rejected", 0),
        "needs_source_decision_count": decision_counts.get("needs_source", 0),
        "needs_semantic_review_decision_count": decision_counts.get("needs_semantic_review", 0),
        "ready_to_apply_count": status_counts.get("ready_to_apply", 0),
        "manual_followup_count": status_counts.get("manual_followup", 0),
        "blocked_by_llm_count": status_counts.get("blocked_by_llm", 0),
        "no_op_count": status_counts.get("no_op", 0),
    }


def completion_percent(status_counts):
    total = sum(status_counts.values())
    if not total:
        return 0.0
    done = status_counts.get("approved_count", 0) + status_counts.get("rejected_count", 0)
    return round(done * 100.0 / total, 2)


def next_step_for(status_counts, decision_counts):
    if decision_counts["ready_to_apply_count"]:
        return "运行 scripts/apply_human_review_decisions.py 显式应用已审计通过的 approved/rejected 决策。"
    if decision_counts["blocked_by_llm_count"]:
        return "needs_semantic_review 需要语义流程或 LLM，按当前规则继续跳过并记录。"
    if status_counts["pending_count"]:
        return "人工核验来源路径，在 review_inputs/human_review_decisions.csv 中填写 approved/rejected/needs_source/needs_semantic_review。"
    return "当前范围没有待处理实体。"


def build_progress_rows():
    workbook_records = load_jsonl(DATASET_DIR / "human_review_workbook.jsonl")
    audit_records = load_jsonl(DATASET_DIR / "human_review_decision_audit.jsonl")
    audit_by_entity = rows_by_entity(audit_records)

    grouped = defaultdict(lambda: {"workbook": [], "audit": []})
    for workbook in workbook_records:
        entity_id = workbook.get("entity_id")
        audit = audit_by_entity.get(entity_id, {})
        groups = [
            ("overall", "all"),
            ("entity_type", workbook.get("entity_type", "unknown")),
            ("review_batch", workbook.get("review_batch", "unknown")),
            ("review_bucket", workbook.get("review_bucket", "unknown")),
        ]
        for scope_type, scope_value in groups:
            grouped[(scope_type, scope_value)]["workbook"].append(workbook)
            if audit:
                grouped[(scope_type, scope_value)]["audit"].append(audit)

    records = []
    for (scope_type, scope_value), group in sorted(grouped.items()):
        workbook_group = group["workbook"]
        audit_group = group["audit"]
        status_counts = count_review_status(workbook_group)
        decision_counts = count_decisions(audit_group)
        records.append({
            "progress_id": f"human_review_progress_{scope_type}_{str(scope_value).lower()}",
            "scope_type": scope_type,
            "scope_value": scope_value,
            "entity_count": len(workbook_group),
            **status_counts,
            **decision_counts,
            "completion_percent": completion_percent(status_counts),
            "needs_llm_count": sum(1 for record in audit_group if record.get("needs_llm") is True),
            "next_step": next_step_for(status_counts, decision_counts),
            "generated_by": "scripts/build_human_review_progress.py",
        })
    records.sort(key=lambda item: (item["scope_type"], item["scope_value"]))
    return records


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "progress_id",
        "scope_type",
        "scope_value",
        "entity_count",
        "pending_count",
        "approved_count",
        "rejected_count",
        "unreviewed_decision_count",
        "approved_decision_count",
        "rejected_decision_count",
        "needs_source_decision_count",
        "needs_semantic_review_decision_count",
        "ready_to_apply_count",
        "manual_followup_count",
        "blocked_by_llm_count",
        "no_op_count",
        "completion_percent",
        "needs_llm_count",
        "next_step",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def write_report(records):
    overall = next((record for record in records if record["scope_type"] == "overall"), {})
    lines = [
        "# 人工复核进度报告",
        "",
        "## 范围",
        "",
        "本报告从人工复核工作簿和人工复核决策审计结果机械汇总，只统计状态和下一步动作，不判断来源是否足以批准实体。",
        "",
        "## 摘要",
        "",
        f"- 复核范围实体数：{overall.get('entity_count', 0)}",
        f"- pending：{overall.get('pending_count', 0)}",
        f"- approved：{overall.get('approved_count', 0)}",
        f"- rejected：{overall.get('rejected_count', 0)}",
        f"- 可显式应用决策：{overall.get('ready_to_apply_count', 0)}",
        f"- 需要 LLM/语义流程阻塞：{overall.get('blocked_by_llm_count', 0)}",
        f"- 完成率：{overall.get('completion_percent', 0.0)}%",
        f"- JSONL 输出：`datasets/human_review_progress.jsonl`",
        f"- CSV 输出：`datasets/human_review_progress.csv`",
        "",
        "## 下一步",
        "",
        f"- {overall.get('next_step', '无')}",
        "",
        "## 分组进度",
        "",
        "| 范围 | 值 | 实体数 | pending | approved | rejected | 可应用 | LLM 阻塞 | 完成率 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for record in records:
        if record["scope_type"] == "overall":
            continue
        lines.append(
            f"| {record['scope_type']} | {record['scope_value']} | {record['entity_count']} | "
            f"{record['pending_count']} | {record['approved_count']} | {record['rejected_count']} | "
            f"{record['ready_to_apply_count']} | {record['blocked_by_llm_count']} | {record['completion_percent']}% |"
        )
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未自动批准、拒绝或改写任何实体。",
        "- 未判断证据充分性。",
        "- 未处理 `needs_semantic_review`，该类仍需语义流程或 LLM，按当前规则跳过并记录。",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    records = build_progress_rows()
    write_jsonl(records)
    write_csv(records)
    write_report(records)
    print(f"Wrote {JSONL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {CSV_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
