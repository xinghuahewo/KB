#!/usr/bin/env python3
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
DATASET_DIR = paths.DATASETS_DIR
REPORT_DIR = paths.report_path("case_observation_guides")
README = REPORT_DIR / "README.md"


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def load_case_sources():
    path = paths.INVENTORY_DIR / "sources.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            row
            for row in csv.DictReader(handle)
            if row.get("source_type") == "case_report"
        ]


def safe_filename(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "unknown"


def md_text(value):
    return str(value).replace("\n", " ").strip()


def grouped_observations(case_sources):
    grouped = defaultdict(list)
    for record in load_jsonl(DATASET_DIR / "case_observations.jsonl"):
        grouped[record.get("source_id", "unknown")].append(record)
    for records in grouped.values():
        records.sort(key=lambda item: (item.get("observation_type", ""), item.get("value", "")))
    for source in case_sources:
        grouped.setdefault(source.get("source_id", "unknown"), [])
    return dict(sorted(grouped.items()))


def skipped_case_actions():
    return [
        record
        for record in load_jsonl(DATASET_DIR / "next_action_queue.jsonl")
        if record.get("action_type") == "semantic_task_skipped"
        and record.get("entity_type") in {"CaseObservation", "Case"}
    ]


def write_readme(grouped, source_by_id, skipped_actions):
    all_records = [record for records in grouped.values() for record in records]
    by_type = Counter(record.get("observation_type", "unknown") for record in all_records)
    lines = [
        "# 案例观察值人工核验指南",
        "",
        "## 范围",
        "",
        "本目录从 `data/derived/datasets/case_observations.jsonl` 机械生成，用于人工逐案例核验正则抽取出的 ASN、前缀、日期和时间等观察值。生成过程不使用 LLM、不做语义判断、不下载资料、不写入 `data/knowledge/entities/cases.jsonl`。",
        "",
        "## 核验规则",
        "",
        "- 先打开对应 `source_ref`，再用观察值和原文上下文定位证据。",
        "- 只确认观察值是否真实出现在该案例来源中。",
        "- 不在本步骤判断攻击者、受害者、泄露方、影响范围、证据强度或事件因果关系。",
        "- 若这些判断必须依赖语义理解，继续按用户要求跳过并保留记录。",
        "",
        "## 摘要",
        "",
        f"- 案例来源数：{len(grouped)}",
        f"- 观察值总数：{len(all_records)}",
    ]
    if by_type:
        for observation_type, count in sorted(by_type.items()):
            lines.append(f"- {observation_type}：{count}")
    else:
        lines.append("- 无")

    lines.extend(["", "## 案例入口", ""])
    for source_id, records in grouped.items():
        filename = f"{safe_filename(source_id)}.md"
        title = records[0].get("title", "") if records else source_by_id.get(source_id, {}).get("title", "")
        lines.append(
            f"- `data/generated/reports/review/case_observation_guides/{filename}`："
            f"{source_id}，{len(records)} 条，{title}"
        )

    lines.extend(["", "## 已按规则跳过的语义事项", ""])
    if not skipped_actions:
        lines.append("- 无")
    for action in skipped_actions:
        lines.append(
            f"- `{action.get('action_id')}`：{action.get('display_name')}；"
            f"原因：{action.get('skip_reason')}"
        )

    README.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_case_file(source_id, records, source):
    filename = f"{safe_filename(source_id)}.md"
    path = REPORT_DIR / filename
    title = records[0].get("title", "") if records else source.get("title", "")
    source_ref = records[0].get("source_ref", "") if records else f"data/corpus/cleaned/cases/{source_id}.md"
    by_type = Counter(record.get("observation_type", "unknown") for record in records)
    lines = [
        f"# {source_id} 案例观察值核验",
        "",
        "## 来源",
        "",
        f"- 标题：{md_text(title)}",
        f"- 来源文本：`{source_ref}`",
        f"- 观察值数量：{len(records)}",
        "",
        "## 类型统计",
        "",
    ]
    if by_type:
        for observation_type, count in sorted(by_type.items()):
            lines.append(f"- {observation_type}：{count}")
    else:
        lines.append("- 无")
    lines.extend([
        "",
        "## 核验边界",
        "",
        "- 本文件只列出正则直接抽取的观察值和原文上下文。",
        "- 事件角色、证据强度、影响范围和因果解释需要语义判断，本步骤跳过。",
        "",
        "## 观察值清单",
        "",
    ])
    if not records:
        lines.append("- 无正则观察值命中；人工如需继续分析，应打开来源文本手动确认，不能用 LLM 补判。")
    else:
        for index, record in enumerate(records, start=1):
            lines.extend([
                f"### {index}. {record.get('observation_type')}：`{record.get('value')}`",
                "",
                f"- review_status：`{record.get('review_status')}`",
                f"- source_ref：`{record.get('source_ref')}`",
                "- 原文上下文：",
                "",
                f"> {md_text(record.get('context', ''))}",
                "",
            ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    case_sources = load_case_sources()
    source_by_id = {source.get("source_id", "unknown"): source for source in case_sources}
    grouped = grouped_observations(case_sources)
    skipped_actions = skipped_case_actions()
    write_readme(grouped, source_by_id, skipped_actions)
    for source_id, records in grouped.items():
        write_case_file(source_id, records, source_by_id.get(source_id, {}))
    print(f"Wrote {README.relative_to(ROOT)}")
    for source_id in grouped:
        print(f"Wrote {(REPORT_DIR / (safe_filename(source_id) + '.md')).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
