#!/usr/bin/env python3
import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime

from bgpkb import paths
from bgpkb.workflows import plan_incremental_run


REPORT = paths.report_path("incremental_run_report")


def run_step(step):
    start = datetime.now()
    result = subprocess.run(
        shlex.split(step["command"]),
        cwd=paths.PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "id": step["id"],
        "command": step["command"],
        "returncode": result.returncode,
        "started_at": start.isoformat(timespec="seconds"),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def render_report(plan, results, executed):
    ok = all(item["returncode"] == 0 for item in results)
    lines = [
        "# 增量流水线执行报告",
        "",
        "## 摘要",
        "",
        f"- 执行模式：{'已执行' if executed else 'dry-run'}",
        f"- 建议步骤数：{plan['step_count']}",
        f"- 已执行步骤数：{len(results)}",
        f"- 总体状态：{'通过' if ok else '失败'}",
        "",
        "## 步骤",
        "",
        "| 步骤 | 状态 | 命令 |",
        "| --- | --- | --- |",
    ]
    if executed:
        for item in results:
            status = "通过" if item["returncode"] == 0 else f"失败({item['returncode']})"
            lines.append(f"| `{item['id']}` | {status} | `{item['command']}` |")
    else:
        for step in plan["steps"]:
            lines.append(f"| `{step['id']}` | dry-run | `{step['command']}` |")
    lines.extend([
        "",
        "## 边界",
        "",
        "- 该入口不会自动应用人工复核决策。",
        "- 增量执行后仍需全量流水线或发布门禁兜底。",
    ])
    return "\n".join(lines).rstrip() + "\n"


def _parse_args():
    parser = argparse.ArgumentParser(description="按增量计划执行步骤；默认只 dry-run。")
    parser.add_argument("--changed", action="append", default=[], help="显式指定变更路径，可重复。")
    parser.add_argument("--plan", default="", help="读取已有计划 JSON。")
    parser.add_argument("--execute", action="store_true", help="显式执行计划步骤。")
    return parser.parse_args()


def main():
    args = _parse_args()
    if args.plan:
        plan = json.loads((paths.PROJECT_ROOT / args.plan).read_text(encoding="utf-8"))
    else:
        plan = plan_incremental_run.build_plan(args.changed)
    results = []
    if args.execute:
        for step in plan["steps"]:
            result = run_step(step)
            results.append(result)
            if result["returncode"] != 0:
                break
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render_report(plan, results, args.execute), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(paths.PROJECT_ROOT)}")
    if any(item["returncode"] != 0 for item in results):
        raise SystemExit(1)
    if not args.execute:
        print("Dry-run only. Add --execute to run planned steps.")


if __name__ == "__main__":
    main()
