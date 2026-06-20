#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "datasets"
REPORT = ROOT / "reports" / "human_review_handoff_report.md"
JSONL_OUTPUT = DATASET_DIR / "human_review_handoff.jsonl"
CSV_OUTPUT = DATASET_DIR / "human_review_handoff.csv"

GENERATED_BY = "scripts/build_human_review_handoff.py"


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def path_exists(path_value):
    if not path_value:
        return False
    return (ROOT / path_value).exists()


def expected_output_for(task):
    task_type = task.get("task_type", "")
    session_id = task.get("session_id", "")
    if task_type == "review_session":
        return (
            "先在 "
            f"review_inputs/human_review_session_decision_templates/{session_id}_decisions_template.csv "
            "中填写人工判断，再显式导入到 review_inputs/human_review_decisions.csv。"
        )
    if task_type == "review_source":
        return "按来源核验证据后，把实体级人工判断写入 review_inputs/human_review_decisions.csv 或对应 session 模板。"
    if task_type == "validate_input":
        return "生成 reports/human_review_input_validation_report.md 和 datasets/human_review_input_validation.*，只校验主决策输入。"
    if task_type == "audit_decisions":
        return "生成 reports/human_review_decision_audit_report.md 和 datasets/human_review_decision_audit.*，只审计不应用。"
    if task_type == "apply_decisions":
        return "显式应用已审计通过且不需要 LLM 的 approved/rejected 决策，并生成应用报告。"
    return "人工确认下一步输出。"


def verification_command_for(task):
    task_type = task.get("task_type", "")
    if task_type == "review_session":
        return "python3 scripts/build_human_review_session_status.py"
    if task_type == "review_source":
        return "python3 scripts/build_human_review_source_matrix.py"
    if task_type == "validate_input":
        return "python3 scripts/build_human_review_decision_audit.py"
    if task_type == "audit_decisions":
        return "python3 scripts/build_human_review_progress.py"
    if task_type == "apply_decisions":
        return "python3 scripts/run_pipeline.py"
    return "python3 scripts/quality_check.py"


def skip_note_for(task):
    task_type = task.get("task_type", "")
    if task_type == "review_source":
        return "只做来源定位和人工核验入口整理；证据充分性判断由人工完成。"
    if task_type == "validate_input":
        return "只做 CSV 结构、枚举、重复项、未知实体和语义边界校验；不判断实体内容。"
    if task_type == "apply_decisions":
        return "只有人工决策审计通过后才可显式运行；needs_semantic_review 继续跳过。"
    return "不调用 LLM，不自动审批，不下载新来源。"


def build_records():
    records = []
    for task in load_jsonl(DATASET_DIR / "human_review_task_board.jsonl"):
        task_type = task.get("task_type", "")
        write_command = task.get("write_command", "")
        dry_run_command = task.get("suggested_command", "")
        can_write = bool(write_command and task_type in {"review_session", "apply_decisions"})
        primary_input = task.get("primary_input", "")
        secondary_input = task.get("secondary_input", "")
        records.append({
            "handoff_id": f"handoff_{task.get('task_id', '')}",
            "task_id": task.get("task_id", ""),
            "task_order": task.get("task_order", 0),
            "task_type": task_type,
            "handoff_status": "ready_for_human",
            "title": task.get("title", ""),
            "primary_input": primary_input,
            "primary_input_exists": path_exists(primary_input),
            "secondary_input": secondary_input,
            "secondary_input_exists": path_exists(secondary_input),
            "expected_manual_output": expected_output_for(task),
            "dry_run_command": dry_run_command,
            "write_command": write_command,
            "verification_command": verification_command_for(task),
            "can_write": can_write,
            "requires_human_decision": task_type in {"review_session", "review_source", "apply_decisions"},
            "needs_llm": False,
            "skip_note": skip_note_for(task),
            "generated_by": GENERATED_BY,
        })
    records.sort(key=lambda item: (item["task_order"], item["task_id"]))
    return records


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "handoff_id",
        "task_id",
        "task_order",
        "task_type",
        "handoff_status",
        "title",
        "primary_input",
        "primary_input_exists",
        "secondary_input",
        "secondary_input_exists",
        "expected_manual_output",
        "dry_run_command",
        "write_command",
        "verification_command",
        "can_write",
        "requires_human_decision",
        "needs_llm",
        "skip_note",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def write_report(records):
    by_type = Counter(record["task_type"] for record in records)
    writable_count = sum(1 for record in records if record["can_write"])
    missing_primary = [
        record for record in records
        if record["primary_input"] and not record["primary_input_exists"]
    ]
    missing_secondary = [
        record for record in records
        if record["secondary_input"]
        and record["task_type"] in {"review_session", "review_source", "audit_decisions", "apply_decisions"}
        and not record["secondary_input_exists"]
    ]
    lines = [
        "# 人工复核交接清单报告",
        "",
        "## 范围",
        "",
        "本报告把人工复核任务板转换为交接清单，逐项列出输入、人工输出目标、dry-run/写入命令和验证命令。它不执行命令，不调用 LLM，不下载来源，也不改变实体状态。",
        "",
        "## 摘要",
        "",
        f"- 交接项数：{len(records)}",
        f"- 可显式写入项：{writable_count}",
        f"- 主输入缺失数：{len(missing_primary)}",
        f"- 辅助输入缺失数：{len(missing_secondary)}",
        f"- JSONL 输出：`datasets/human_review_handoff.jsonl`",
        f"- CSV 输出：`datasets/human_review_handoff.csv`",
        "",
        "## 按任务类型统计",
        "",
    ]
    for task_type, count in sorted(by_type.items()):
        lines.append(f"- `{task_type}`：{count}")

    lines.extend([
        "",
        "## 交接清单",
        "",
        "| 顺序 | 类型 | 标题 | 主输入 | 人工输出目标 | 验证命令 |",
        "| ---: | --- | --- | --- | --- | --- |",
    ])
    for record in records:
        lines.append(
            f"| {record['task_order']} | `{record['task_type']}` | {record['title']} | "
            f"`{record['primary_input']}` | {record['expected_manual_output']} | "
            f"`{record['verification_command']}` |"
        )

    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未执行 dry-run、写入或验证命令。",
        "- 未自动批准、拒绝或改写实体。",
        "- 未调用 LLM，也不下载新来源。",
        "- `needs_semantic_review` 仍按规则跳过并记录。",
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
