#!/usr/bin/env python3
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "datasets"
REPORT = ROOT / "reports" / "human_review_task_board_report.md"
JSONL_OUTPUT = DATASET_DIR / "human_review_task_board.jsonl"
CSV_OUTPUT = DATASET_DIR / "human_review_task_board.csv"

GENERATED_BY = "scripts/build_human_review_task_board.py"


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def session_tasks():
    tasks = []
    for status in load_jsonl(DATASET_DIR / "human_review_session_status.jsonl"):
        session_id = status.get("session_id", "")
        session_order = status.get("session_order", 0)
        tasks.append({
            "task_id": f"task_session_{session_id}",
            "task_order": session_order,
            "task_type": "review_session",
            "task_status": "pending" if status.get("awaiting_human_review_count", 0) else "no_pending_items",
            "title": f"复核 {session_id}",
            "session_id": session_id,
            "source_id": "",
            "entity_id": status.get("next_entity_id", ""),
            "item_count": status.get("item_count", 0),
            "field_check_count": 0,
            "priority_reason": "按 session_order 小批次推进人工复核。",
            "primary_input": f"reports/human_review_session_guides/{session_id}.md",
            "secondary_input": f"review_inputs/human_review_session_decision_templates/{session_id}_decisions_template.csv",
            "suggested_command": f"python3 scripts/import_human_review_session_decisions.py --session-id {session_id}",
            "write_command": f"python3 scripts/import_human_review_session_decisions.py --session-id {session_id} --write",
            "needs_llm": False,
            "generated_by": GENERATED_BY,
        })
    return tasks


def source_tasks(start_order):
    tasks = []
    source_records = [
        record for record in load_jsonl(DATASET_DIR / "human_review_source_matrix.jsonl")
        if record.get("source_type") != "manual_note"
    ][:10]
    for offset, source in enumerate(source_records, start=1):
        source_id = source.get("source_id", "")
        tasks.append({
            "task_id": f"task_source_{source_id}",
            "task_order": start_order + offset,
            "task_type": "review_source",
            "task_status": "pending",
            "title": f"按来源复核 {source_id}",
            "session_id": "|".join(source.get("session_ids", [])),
            "source_id": source_id,
            "entity_id": "|".join(source.get("sample_entity_ids", [])[:5]),
            "item_count": source.get("entity_count", 0),
            "field_check_count": source.get("field_check_count", 0),
            "priority_reason": "该来源复用度较高，先核验可减少后续实体级确认成本。",
            "primary_input": "reports/human_review_source_matrix_report.md",
            "secondary_input": source.get("source_path", ""),
            "suggested_command": "python3 scripts/build_human_review_source_matrix.py",
            "write_command": "",
            "needs_llm": False,
            "generated_by": GENERATED_BY,
        })
    return tasks


def workflow_tasks(start_order):
    return [
        {
            "task_id": "task_validate_input",
            "task_order": start_order + 1,
            "task_type": "validate_input",
            "task_status": "available",
            "title": "校验主人工决策输入",
            "session_id": "",
            "source_id": "",
            "entity_id": "",
            "item_count": 0,
            "field_check_count": 0,
            "priority_reason": "人工填写或导入决策后，先校验 CSV 结构和机械一致性。",
            "primary_input": "review_inputs/human_review_decisions.csv",
            "secondary_input": "reports/human_review_input_validation_report.md",
            "suggested_command": "python3 scripts/build_human_review_input_validation.py",
            "write_command": "",
            "needs_llm": False,
            "generated_by": GENERATED_BY,
        },
        {
            "task_id": "task_audit_decisions",
            "task_order": start_order + 2,
            "task_type": "audit_decisions",
            "task_status": "available",
            "title": "审计主人工决策文件",
            "session_id": "",
            "source_id": "",
            "entity_id": "",
            "item_count": 0,
            "field_check_count": 0,
            "priority_reason": "人工填写或导入决策后，先审计再考虑应用。",
            "primary_input": "review_inputs/human_review_decisions.csv",
            "secondary_input": "reports/human_review_decision_audit_report.md",
            "suggested_command": "python3 scripts/build_human_review_decision_audit.py",
            "write_command": "",
            "needs_llm": False,
            "generated_by": GENERATED_BY,
        },
        {
            "task_id": "task_apply_decisions_explicit",
            "task_order": start_order + 3,
            "task_type": "apply_decisions",
            "task_status": "manual_explicit_only",
            "title": "显式应用已审计通过的 approved/rejected 决策",
            "session_id": "",
            "source_id": "",
            "entity_id": "",
            "item_count": 0,
            "field_check_count": 0,
            "priority_reason": "只有审计通过且不需要 LLM 的人工决策才可显式应用。",
            "primary_input": "datasets/human_review_decision_audit.jsonl",
            "secondary_input": "reports/human_review_decision_apply_report.md",
            "suggested_command": "python3 scripts/apply_human_review_decisions.py",
            "write_command": "python3 scripts/apply_human_review_decisions.py --write",
            "needs_llm": False,
            "generated_by": GENERATED_BY,
        },
    ]


def build_tasks():
    tasks = session_tasks()
    tasks.extend(source_tasks(len(tasks)))
    tasks.extend(workflow_tasks(len(tasks)))
    tasks.sort(key=lambda item: item["task_order"])
    return tasks


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "task_id",
        "task_order",
        "task_type",
        "task_status",
        "title",
        "session_id",
        "source_id",
        "entity_id",
        "item_count",
        "field_check_count",
        "priority_reason",
        "primary_input",
        "secondary_input",
        "suggested_command",
        "write_command",
        "needs_llm",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def write_report(records):
    lines = [
        "# 人工复核任务板报告",
        "",
        "## 范围",
        "",
        "本报告把 session、来源矩阵、字段清单、输入校验、决策审计和显式应用入口整理为可执行任务板。它只给出下一步入口和命令提示，不执行命令，不调用 LLM，也不修改实体状态。",
        "",
        "## 摘要",
        "",
        f"- 任务数：{len(records)}",
        f"- JSONL 输出：`datasets/human_review_task_board.jsonl`",
        f"- CSV 输出：`datasets/human_review_task_board.csv`",
        "",
        "## 任务清单",
        "",
        "| 顺序 | 类型 | 标题 | 主输入 | 建议命令 |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for record in records:
        command = record["suggested_command"].replace("|", "\\|")
        lines.append(
            f"| {record['task_order']} | `{record['task_type']}` | {record['title']} | "
            f"`{record['primary_input']}` | `{command}` |"
        )
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未执行任务板中的命令。",
        "- 未自动批准、拒绝或改写实体。",
        "- 未调用 LLM，也不下载新来源。",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    tasks = build_tasks()
    write_jsonl(tasks)
    write_csv(tasks)
    write_report(tasks)
    print(f"Wrote {JSONL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {CSV_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
