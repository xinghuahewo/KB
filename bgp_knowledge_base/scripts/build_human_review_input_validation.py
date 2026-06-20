#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "datasets"
REVIEW_INPUT = ROOT / "review_inputs" / "human_review_decisions.csv"
REPORT = ROOT / "reports" / "human_review_input_validation_report.md"
JSONL_OUTPUT = DATASET_DIR / "human_review_input_validation.jsonl"
CSV_OUTPUT = DATASET_DIR / "human_review_input_validation.csv"

REQUIRED_COLUMNS = ["entity_id", "review_decision", "reviewer", "reviewed_at", "decision_note"]
ALLOWED_DECISIONS = {"", "unreviewed", "approved", "rejected", "needs_source", "needs_semantic_review"}


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def load_entity_ids():
    ids = set()
    for path in sorted((ROOT / "entities").glob("*.jsonl")):
        for record in load_jsonl(path):
            if record.get("id"):
                ids.add(record["id"])
    return ids


def read_input_rows():
    if not REVIEW_INPUT.exists():
        return [], [], ["文件不存在"]
    with REVIEW_INPUT.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        rows = []
        for row_number, row in enumerate(reader, start=2):
            normalized = {key: (row.get(key) or "").strip() for key in columns}
            if any(normalized.values()):
                normalized["row_number"] = row_number
                rows.append(normalized)
    return columns, rows, []


def status_for(issue_count, severity):
    if issue_count == 0:
        return "pass"
    if severity == "error":
        return "fail"
    if severity == "warning":
        return "warning"
    return "info"


def build_check(check_order, check_type, severity, checked_count, issues, message, suggested_action, needs_llm=False):
    affected_entity_ids = sorted({issue.get("entity_id", "") for issue in issues if issue.get("entity_id")})
    affected_rows = sorted({issue.get("row_number", 0) for issue in issues if issue.get("row_number")})
    return {
        "validation_id": f"human_review_input_validation_{check_order:02d}_{check_type}",
        "check_order": check_order,
        "input_path": REVIEW_INPUT.relative_to(ROOT).as_posix(),
        "check_type": check_type,
        "status": status_for(len(issues), severity),
        "severity": severity,
        "checked_count": checked_count,
        "issue_count": len(issues),
        "affected_entity_ids": affected_entity_ids,
        "affected_rows": affected_rows,
        "message": message,
        "suggested_action": suggested_action,
        "needs_llm": needs_llm,
        "generated_by": "scripts/build_human_review_input_validation.py",
    }


def build_records():
    entity_ids = load_entity_ids()
    columns, rows, read_errors = read_input_rows()
    records = []

    missing_file_issues = [{"row_number": 0, "entity_id": ""} for _ in read_errors]
    records.append(build_check(
        1,
        "input_file_exists",
        "error",
        1,
        missing_file_issues,
        "主人工决策输入文件存在且可读取。" if not read_errors else "主人工决策输入文件缺失或不可读取。",
        "运行 `python3 scripts/build_human_review_decision_template.py` 初始化模板。",
    ))

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in columns]
    records.append(build_check(
        2,
        "required_columns",
        "error",
        len(REQUIRED_COLUMNS),
        [{"row_number": 1, "entity_id": column} for column in missing_columns],
        "主人工决策输入包含必需列。" if not missing_columns else "主人工决策输入缺少必需列。",
        "按模板补齐列：entity_id, review_decision, reviewer, reviewed_at, decision_note。",
    ))

    if read_errors or missing_columns:
        return records

    row_entity_ids = [row.get("entity_id", "") for row in rows if row.get("entity_id")]
    entity_id_counts = Counter(row_entity_ids)
    duplicate_issues = [
        {"row_number": row["row_number"], "entity_id": row.get("entity_id", "")}
        for row in rows
        if row.get("entity_id") and entity_id_counts[row["entity_id"]] > 1
    ]
    records.append(build_check(
        3,
        "duplicate_entity_id",
        "error",
        len(rows),
        duplicate_issues,
        "每个 entity_id 在主人工决策输入中最多出现一次。",
        "删除重复行，或先在 session 模板中合并后再导入主决策文件。",
    ))

    missing_entity_id_issues = [
        {"row_number": row["row_number"], "entity_id": ""}
        for row in rows
        if not row.get("entity_id")
    ]
    records.append(build_check(
        4,
        "missing_entity_id",
        "error",
        len(rows),
        missing_entity_id_issues,
        "非空人工决策行必须填写 entity_id。",
        "从人工复核工作簿或 session 模板复制 entity_id。",
    ))

    unknown_entity_issues = [
        {"row_number": row["row_number"], "entity_id": row.get("entity_id", "")}
        for row in rows
        if row.get("entity_id") and row["entity_id"] not in entity_ids
    ]
    records.append(build_check(
        5,
        "known_entity_id",
        "error",
        len(row_entity_ids),
        unknown_entity_issues,
        "人工决策行引用的 entity_id 都存在于当前实体库。",
        "核对实体 ID；若是新增实体，先按实体 schema 加入 entities/*.jsonl 并重跑流水线。",
    ))

    invalid_decision_issues = [
        {"row_number": row["row_number"], "entity_id": row.get("entity_id", "")}
        for row in rows
        if row.get("review_decision", "") not in ALLOWED_DECISIONS
    ]
    records.append(build_check(
        6,
        "allowed_review_decision",
        "error",
        len(rows),
        invalid_decision_issues,
        "review_decision 均在允许枚举内。",
        "只填写 approved、rejected、needs_source、needs_semantic_review、unreviewed 或留空。",
    ))

    semantic_issues = [
        {"row_number": row["row_number"], "entity_id": row.get("entity_id", "")}
        for row in rows
        if row.get("review_decision") == "needs_semantic_review"
    ]
    records.append(build_check(
        7,
        "semantic_review_boundary",
        "warning",
        len(rows),
        semantic_issues,
        "需要语义流程的人工决策会被记录并阻塞自动应用。",
        "按当前规则跳过该类记录；只有获得明确语义/LLM 处理许可后再处理。",
        needs_llm=bool(semantic_issues),
    ))

    ready_to_apply_issues = [
        {"row_number": row["row_number"], "entity_id": row.get("entity_id", "")}
        for row in rows
        if row.get("review_decision") in {"approved", "rejected"}
    ]
    records.append(build_check(
        8,
        "ready_to_apply_preview",
        "info",
        len(rows),
        ready_to_apply_issues,
        "本检查只统计显式 approved/rejected 行，提示后续可由应用脚本处理。",
        "先运行决策审计确认 can_apply，再显式运行应用脚本；不要自动批准。",
    ))

    return records


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "validation_id",
        "check_order",
        "input_path",
        "check_type",
        "status",
        "severity",
        "checked_count",
        "issue_count",
        "affected_entity_ids",
        "affected_rows",
        "message",
        "suggested_action",
        "needs_llm",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["affected_entity_ids"] = "|".join(record["affected_entity_ids"])
            row["affected_rows"] = "|".join(str(item) for item in record["affected_rows"])
            writer.writerow(row)


def write_report(records):
    status_counts = Counter(record["status"] for record in records)
    total_issues = sum(record["issue_count"] for record in records if record["severity"] == "error")
    warning_issues = sum(record["issue_count"] for record in records if record["severity"] == "warning")
    info_issues = sum(record["issue_count"] for record in records if record["severity"] == "info")
    lines = [
        "# 人工复核输入校验报告",
        "",
        "## 范围",
        "",
        "本报告只校验 `review_inputs/human_review_decisions.csv` 的结构和机械一致性，不判断实体内容是否应批准或拒绝。",
        "",
        "该步骤不联网、不下载、不调用 LLM、不做语义判断，也不修改 entities/*.jsonl。",
        "",
        "## 摘要",
        "",
        f"- 校验记录数：{len(records)}",
        f"- 错误问题数：{total_issues}",
        f"- 警告问题数：{warning_issues}",
        f"- 信息提示数：{info_issues}",
        f"- 状态统计：{json.dumps(dict(sorted(status_counts.items())), ensure_ascii=False, sort_keys=True)}",
        "- JSONL 输出：`datasets/human_review_input_validation.jsonl`",
        "- CSV 输出：`datasets/human_review_input_validation.csv`",
        "- 人工决策输入：`review_inputs/human_review_decisions.csv`",
        "",
        "## 校验项",
        "",
        "| 顺序 | 类型 | 状态 | 严重度 | 检查数 | 问题数 | 是否需要 LLM | 说明 |",
        "| ---: | --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for record in records:
        lines.append(
            f"| {record['check_order']} | `{record['check_type']}` | {record['status']} | "
            f"{record['severity']} | {record['checked_count']} | {record['issue_count']} | "
            f"{'是' if record['needs_llm'] else '否'} | {record['message']} |"
        )
    lines.extend(["", "## 需处理问题", ""])
    problem_records = [record for record in records if record["issue_count"]]
    if problem_records:
        for record in problem_records:
            rows = ", ".join(str(item) for item in record["affected_rows"]) or "无"
            entity_ids = ", ".join(f"`{item}`" for item in record["affected_entity_ids"]) or "无"
            lines.append(f"- `{record['check_type']}`：{record['issue_count']} 项；行：{rows}；实体：{entity_ids}；建议：{record['suggested_action']}")
    else:
        lines.append("- 无")
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未自动批准、拒绝或修改实体。",
        "- `needs_semantic_review` 只记录为语义流程边界，当前规则下不自动处理。",
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
    if any(record["status"] == "fail" for record in records):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
