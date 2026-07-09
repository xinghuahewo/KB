#!/usr/bin/env python3
import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from bgpkb import paths

import yaml


ROOT = paths.PROJECT_ROOT
CONFIG = paths.CONFIG_DIR / "stage_acceptance_gates.yaml"


def load_config(path=CONFIG):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def find_stage(config, stage_id):
    for stage in config["stages"]:
        if stage["id"] == stage_id:
            return stage
    raise SystemExit(f"Unknown stage: {stage_id}")


def check_required_files(stage):
    rows = []
    for item in stage.get("required_files", []):
        path = ROOT / item
        rows.append({"path": item, "exists": path.exists()})
    return rows


def run_commands(stage, skip_commands=False):
    rows = []
    for item in stage.get("commands", []):
        if skip_commands:
            rows.append({
                "id": item["id"],
                "name": item["name"],
                "command": item["command"],
                "returncode": 0,
                "stdout": "SKIPPED",
                "stderr": "",
                "skipped": True,
            })
            continue
        result = subprocess.run(
            shlex.split(item["command"]),
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        rows.append({
            "id": item["id"],
            "name": item["name"],
            "command": item["command"],
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "skipped": False,
        })
    return rows


def check_reports(stage):
    rows = []
    for item in stage.get("report_checks", []):
        path = ROOT / item["path"]
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        missing = [needle for needle in item.get("must_contain", []) if needle not in text]
        rows.append({
            "id": item["id"],
            "path": item["path"],
            "exists": path.exists(),
            "missing": missing,
        })
    return rows


def decide(file_checks, command_results, report_checks, stage):
    failures = []
    failures.extend(f"missing file: {row['path']}" for row in file_checks if not row["exists"])
    failures.extend(
        f"command failed: {row['id']} ({row['returncode']})"
        for row in command_results
        if row["returncode"] != 0
    )
    for row in report_checks:
        if not row["exists"]:
            failures.append(f"missing report: {row['path']}")
        for needle in row["missing"]:
            failures.append(f"report check failed: {row['path']} missing {needle}")
    if failures:
        return "fail", failures

    human_items = stage.get("human_review_policy", {}).get("non_blocking_items", [])
    allow_needs_human = stage.get("human_review_policy", {}).get("allow_needs_human", False)
    if human_items and not allow_needs_human:
        return "needs_human", human_items
    return "pass", []


def render_bool(value):
    return "通过" if value else "失败"


def render_report(config, stage, file_checks, command_results, report_checks, decision, reasons):
    effect = stage.get("effect_review", {})
    human_items = stage.get("human_review_policy", {}).get("non_blocking_items", [])
    lines = [
        "# 阶段验收报告",
        "",
        "## 结论",
        "",
        f"- 阶段：{stage['name']} (`{stage['id']}`)",
        f"- 结论：{decision}",
        f"- 验收模式：`{stage.get('acceptance_mode', '')}`",
        f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
        "",
        effect.get("one_line", ""),
        "",
        "## 交付物验收",
        "",
        "| 文件 | 状态 |",
        "| --- | --- |",
    ]
    for row in file_checks:
        lines.append(f"| `{row['path']}` | {render_bool(row['exists'])} |")

    lines.extend(["", "## 效果验收", "", "### 新增能力", ""])
    for item in effect.get("new_capabilities", []):
        lines.append(f"- {item}")
    lines.extend(["", "### 使用者现在能做什么", ""])
    for item in effect.get("user_can_now", []):
        lines.append(f"- {item}")
    lines.extend(["", "### 后续阶段能依赖什么", ""])
    for item in effect.get("downstream_dependencies", []):
        lines.append(f"- {item}")

    lines.extend(["", "## 证据验收", "", "### 命令结果", "", "| 命令 | 状态 | 摘要 |", "| --- | --- | --- |"])
    for row in command_results:
        summary = row["stdout"].splitlines()[-1] if row["stdout"] else row["stderr"].splitlines()[-1] if row["stderr"] else ""
        lines.append(f"| `{row['command']}` | {'通过' if row['returncode'] == 0 else '失败'} | {summary} |")

    lines.extend(["", "### 报告检查", "", "| 报告 | 状态 | 缺失项 |", "| --- | --- | --- |"])
    for row in report_checks:
        ok = row["exists"] and not row["missing"]
        missing = "<br>".join(row["missing"]) if row["missing"] else "无"
        lines.append(f"| `{row['path']}` | {render_bool(ok)} | {missing} |")

    lines.extend(["", "## 风险与剩余人工事项", ""])
    if human_items:
        for item in human_items:
            lines.append(f"- {item}")
    else:
        lines.append("- 无已登记人工事项。")

    lines.extend(["", "## 建议", ""])
    if decision == "pass":
        lines.append("- 可进入下一阶段；保留人工事项不阻塞阶段通过。")
    elif decision == "needs_human":
        lines.append("- 需要人工处理已登记事项后再进入下一阶段。")
    else:
        lines.append("- 不建议进入下一阶段；需先修复失败项。")

    if reasons:
        lines.extend(["", "## 失败或阻塞原因", ""])
        for reason in reasons:
            lines.append(f"- {reason}")

    return "\n".join(lines) + "\n"


def write_jsonl(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    with path.open("w", encoding="utf-8") as fh:
        if existing.strip():
            fh.write(existing.rstrip() + "\n")
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run deterministic stage acceptance checks.")
    parser.add_argument("--stage", required=True)
    parser.add_argument("--skip-commands", action="store_true")
    args = parser.parse_args()

    config = load_config()
    stage = find_stage(config, args.stage)
    file_checks = check_required_files(stage)
    command_results = run_commands(stage, skip_commands=args.skip_commands)
    report_checks = check_reports(stage)
    decision, reasons = decide(file_checks, command_results, report_checks, stage)

    report_path = ROOT / config["generated_policy"]["report_path"]
    results_path = ROOT / config["generated_policy"]["results_path"]
    report_path.write_text(
        render_report(config, stage, file_checks, command_results, report_checks, decision, reasons),
        encoding="utf-8",
    )
    effect = stage.get("effect_review", {})
    record = {
        "stage_id": stage["id"],
        "stage_name": stage["name"],
        "decision": decision,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "file_checks_passed": sum(1 for row in file_checks if row["exists"]),
        "file_checks_total": len(file_checks),
        "commands_passed": sum(1 for row in command_results if row["returncode"] == 0),
        "commands_total": len(command_results),
        "report_checks_passed": sum(1 for row in report_checks if row["exists"] and not row["missing"]),
        "report_checks_total": len(report_checks),
        "effect_summary": {
            "one_line": effect.get("one_line", ""),
            "new_capabilities_count": len(effect.get("new_capabilities", [])),
            "user_can_now_count": len(effect.get("user_can_now", [])),
            "downstream_dependencies_count": len(effect.get("downstream_dependencies", [])),
        },
        "human_items_count": len(stage.get("human_review_policy", {}).get("non_blocking_items", [])),
        "reasons": reasons,
    }
    write_jsonl(results_path, record)
    print(f"Wrote {report_path.relative_to(ROOT)}")
    print(f"Wrote {results_path.relative_to(ROOT)}")
    if decision == "fail":
        raise SystemExit(1)
    if decision == "needs_human":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
