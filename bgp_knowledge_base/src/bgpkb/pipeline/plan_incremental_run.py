#!/usr/bin/env python3
import argparse
from datetime import datetime
import fnmatch
import json
import subprocess
from pathlib import Path

from bgpkb import paths

import yaml


CONFIG = paths.CONFIG_DIR / "pipeline_dependencies.yaml"
PLAN_OUTPUT = paths.DATASETS_DIR / "incremental_run_plan.json"
REPORT = paths.report_path("incremental_run_plan_report")


def load_config(path=CONFIG):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _normalize(rel):
    return str(rel).replace("\\", "/").lstrip("./")


def _pattern_matches(path, pattern):
    path = _normalize(path)
    pattern = _normalize(pattern)
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-3].rstrip("/") + "/")
    return fnmatch.fnmatch(path, pattern)


def _changed_from_git():
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=paths.PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git diff 失败：{result.stderr.strip()}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _changed_from_mtime(since):
    threshold = datetime.fromisoformat(since).timestamp()
    changed = []
    for base in ("data", "metadata", "src", "tests", "docs"):
        root = paths.PROJECT_ROOT / base
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.stat().st_mtime >= threshold:
                changed.append(paths.rel(path))
    return sorted(changed)


def _direct_step_ids(changed_paths, steps):
    direct = []
    for step in steps:
        if any(
            _pattern_matches(path, pattern)
            for path in changed_paths
            for pattern in step.get("inputs", [])
        ):
            direct.append(step["id"])
    return direct


def _expand_downstream(direct_ids, steps_by_id):
    ordered = []
    seen = set()

    def visit(step_id):
        if step_id in seen:
            return
        if step_id not in steps_by_id:
            raise ValueError(f"pipeline_dependencies.yaml 引用了未知步骤：{step_id}")
        seen.add(step_id)
        ordered.append(step_id)
        for downstream_id in steps_by_id[step_id].get("downstream", []):
            visit(downstream_id)

    for step_id in direct_ids:
        visit(step_id)
    return ordered


def build_plan(changed_paths, config=None):
    config = config or load_config()
    changed_paths = sorted({_normalize(path) for path in changed_paths if str(path).strip()})
    steps = config.get("steps", [])
    steps_by_id = {step["id"]: step for step in steps}
    direct_ids = _direct_step_ids(changed_paths, steps)
    ordered_ids = _expand_downstream(direct_ids, steps_by_id)
    selected_steps = [
        {
            "id": step_id,
            "label": steps_by_id[step_id].get("label", step_id),
            "command": steps_by_id[step_id]["command"],
            "directly_affected": step_id in direct_ids,
            "safety": steps_by_id[step_id].get("safety", {}),
        }
        for step_id in ordered_ids
    ]
    return {
        "schema_version": "incremental_run_plan_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "generated_by": "src/bgpkb/pipeline/plan_incremental_run.py",
        "execution_mode": config.get("default_mode", "plan_only"),
        "changed_paths": changed_paths,
        "direct_step_ids": direct_ids,
        "steps": selected_steps,
        "step_count": len(selected_steps),
        "requires_full_pipeline_gate": bool(config.get("safety", {}).get("full_pipeline_remains_release_gate", True)),
        "full_pipeline_command": config.get("release_gate", {}).get("full_pipeline_command", "python3 -m bgpkb.pipeline.run_pipeline"),
        "notes": [
            "只生成计划，不直接执行。",
            "执行增量步骤后，最终发布仍需全量流水线或明确发布门禁兜底。",
        ],
    }


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_report(plan):
    lines = [
        "# 增量重跑计划",
        "",
        "## 摘要",
        "",
        "- 模式：只生成计划，不直接执行。",
        f"- 变更文件数：{len(plan['changed_paths'])}",
        f"- 建议步骤数：{plan['step_count']}",
        f"- 仍需全量发布门禁：{'是' if plan['requires_full_pipeline_gate'] else '否'}",
        "",
        "## 变更文件",
        "",
    ]
    if plan["changed_paths"]:
        lines.extend(f"- `{path}`" for path in plan["changed_paths"])
    else:
        lines.append("- 无变更文件。")
    lines.extend(["", "## 建议重跑步骤", "", "| 步骤 | 直接命中 | 命令 |", "| --- | --- | --- |"])
    for step in plan["steps"]:
        lines.append(
            f"| `{step['id']}` | {'是' if step['directly_affected'] else '否'} | `{step['command']}` |"
        )
    if not plan["steps"]:
        lines.append("| 无 | 否 | 无 |")
    lines.extend([
        "",
        "## 边界",
        "",
        "- 本计划不联网、不调用 LLM、不应用人工复核决策。",
        "- `run_incremental_pipeline.py --execute` 才会执行建议步骤。",
        f"- 最终一致性兜底命令：`{plan['full_pipeline_command']}`。",
    ])
    return "\n".join(lines).rstrip() + "\n"


def _parse_args():
    parser = argparse.ArgumentParser(description="根据变更文件生成增量重跑建议，不直接执行。")
    parser.add_argument("--changed", action="append", default=[], help="显式指定变更路径，可重复。")
    parser.add_argument("--from-git", action="store_true", help="读取 git diff --name-only HEAD。")
    parser.add_argument("--since", default="", help="按 ISO 时间戳扫描 mtime 变更。")
    parser.add_argument("--write", action="store_true", help="写入计划 JSON 和中文报告。")
    return parser.parse_args()


def main():
    args = _parse_args()
    changed = list(args.changed)
    if args.from_git:
        changed.extend(_changed_from_git())
    if args.since:
        changed.extend(_changed_from_mtime(args.since))
    plan = build_plan(changed)
    if args.write:
        write_json(PLAN_OUTPUT, plan)
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(render_report(plan), encoding="utf-8")
        print(f"Wrote {PLAN_OUTPUT.relative_to(paths.PROJECT_ROOT)}")
        print(f"Wrote {REPORT.relative_to(paths.PROJECT_ROOT)}")
    else:
        print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
