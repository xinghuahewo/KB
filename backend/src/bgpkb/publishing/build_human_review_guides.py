#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
DATASET_DIR = paths.DATASETS_DIR
REPORT_DIR = paths.report_path("human_review_guides")
README = REPORT_DIR / "README.md"
BATCH_FILES = {
    "01_ready_without_manual_note": REPORT_DIR / "01_ready_without_manual_note.md",
    "02_ready_with_manual_note": REPORT_DIR / "02_ready_with_manual_note.md",
    "99_not_ready": REPORT_DIR / "99_not_ready.md",
}


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def md_list(values):
    if not values:
        return "无"
    return "<br>".join(f"`{value}`" for value in values)


def md_text(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def workbook_records():
    records = load_jsonl(DATASET_DIR / "human_review_workbook.jsonl")
    return sorted(records, key=lambda item: item.get("review_order", 999999))


def skipped_semantic_actions():
    return [
        record
        for record in load_jsonl(DATASET_DIR / "next_action_queue.jsonl")
        if record.get("action_type") == "semantic_task_skipped"
    ]


def write_readme(records, skipped_actions):
    by_batch = Counter(record.get("review_batch", "unknown") for record in records)
    by_type = Counter(record.get("entity_type", "UNKNOWN") for record in records)
    by_decision = Counter(record.get("review_decision", "unknown") for record in records)
    lines = [
        "# 人工复核指南",
        "",
        "## 范围",
        "",
        "本目录从人工复核工作簿机械生成，只用于把 pending 实体按批次展开为可读复核入口。生成过程不使用 LLM、不做语义判断、不下载资料、不修改实体状态。",
        "",
        "## 文件入口",
        "",
    ]
    for batch, path in BATCH_FILES.items():
        if by_batch.get(batch, 0):
            lines.append(f"- `{path.relative_to(ROOT).as_posix()}`：{by_batch[batch]} 条")

    lines.extend(["", "## 复核规则", ""])
    lines.extend([
        "- 先打开 `cleaned_paths` 和 `parsed_paths`，再用 `chunk_sample_ids` 定位具体片段。",
        "- `context_2026` 只作为项目范围提示，不能单独作为批准依据。",
        "- 若实体字段被非 manual_note 来源直接支持，可在 `data/derived/datasets/human_review_workbook.*` 中把 `review_decision` 改为 `approved`，之后再运行决策审计。",
        "- 若来源不支持实体字段，或需要解释、归纳、判定证据强度，应保持 `unreviewed` 或记录为后续人工处理；不要用 LLM 补判。",
        "",
        "## 统计",
        "",
        f"- 复核实体总数：{len(records)}",
    ])
    for batch, count in sorted(by_batch.items()):
        lines.append(f"- {batch}：{count}")
    for decision, count in sorted(by_decision.items()):
        lines.append(f"- review_decision={decision}：{count}")

    lines.extend(["", "## 按实体类型统计", ""])
    for entity_type, count in sorted(by_type.items()):
        lines.append(f"- {entity_type}：{count}")

    lines.extend(["", "## 已按规则跳过的语义事项", ""])
    if not skipped_actions:
        lines.append("- 无")
    else:
        for action in skipped_actions:
            lines.append(
                f"- `{action.get('action_id')}`：{action.get('display_name')}；"
                f"原因：{action.get('skip_reason')}"
            )

    README.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_batch_file(batch, records):
    path = BATCH_FILES[batch]
    lines = [
        f"# {batch} 复核清单",
        "",
        "## 说明",
        "",
        "本文件只展开人工复核入口。表内路径和 chunk ID 均来自现有流水线数据，未经过语义扩展。",
        "",
    ]
    for record in records:
        title = md_text(record.get("display_name", "")) or record.get("entity_id", "")
        lines.extend([
            f"## {record.get('review_order')}. {title}",
            "",
            f"- 实体 ID：`{record.get('entity_id')}`",
            f"- 实体类型：{record.get('entity_type')}",
            f"- 当前决策：`{record.get('review_decision')}`",
            f"- 当前状态：`{record.get('review_status')}`",
            f"- 复核指令：{md_text(record.get('decision_instructions', ''))}",
            "- 来源：",
        ])
        for value in record.get("source_refs", []):
            lines.append(f"  - `{value}`")
        lines.append("- cleaned 路径：")
        for value in record.get("cleaned_paths", []):
            lines.append(f"  - `{value}`")
        lines.append("- parsed 路径：")
        for value in record.get("parsed_paths", []):
            lines.append(f"  - `{value}`")
        lines.append("- chunk 样例：")
        for value in record.get("chunk_sample_ids", []):
            lines.append(f"  - `{value}`")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    records = workbook_records()
    skipped_actions = skipped_semantic_actions()
    write_readme(records, skipped_actions)
    by_batch = {}
    for record in records:
        by_batch.setdefault(record.get("review_batch", "99_not_ready"), []).append(record)
    for batch, batch_records in sorted(by_batch.items()):
        if batch not in BATCH_FILES:
            batch = "99_not_ready"
        write_batch_file(batch, batch_records)
    print(f"Wrote {README.relative_to(ROOT)}")
    for batch, path in sorted(BATCH_FILES.items()):
        if path.exists():
            print(f"Wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
