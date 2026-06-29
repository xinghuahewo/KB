#!/usr/bin/env python3
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
DATASET_DIR = paths.DATASETS_DIR
OUTPUT_DIR = paths.REVIEW_INPUTS_DIR / "human_review_session_decision_templates"
README = OUTPUT_DIR / "README.md"
REPORT = paths.report_path("human_review_session_decision_templates_report")
DECISION_INPUT = "data/review_inputs/human_review_decisions.csv"
GENERATED_BY = "src/bgpkb/pipeline/build_human_review_session_decision_templates.py"

DECISION_FIELDS = [
    "entity_id",
    "review_decision",
    "reviewer",
    "reviewed_at",
    "decision_note",
]

TEMPLATE_FIELDS = [
    *DECISION_FIELDS,
    "session_id",
    "within_session_order",
    "entity_type",
    "display_name",
    "queue_status",
    "review_status",
    "review_batch",
    "review_bucket",
    "source_refs",
    "cleaned_paths",
    "parsed_paths",
    "top_extract_ids",
    "decision_instructions",
]


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def cleanup_old_templates():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in OUTPUT_DIR.glob("review_session_*_decisions_template.csv"):
        path.unlink()


def decision_instructions(record):
    queue_status = record.get("queue_status", "")
    if queue_status == "ready_to_apply":
        return "该实体已有人工 approved/rejected 决策；再次确认后再显式应用。"
    if queue_status == "manual_followup":
        return "该实体需要补充来源或人工说明；不要自动批准。"
    if queue_status == "blocked_by_llm":
        return "该实体需要语义流程或 LLM；按当前规则跳过并记录。"
    return "人工打开 session 指南、来源路径和摘录；若来源直接支持实体字段，可在主决策 CSV 中填写 approved。"


def write_session_template(session_id, records):
    path = OUTPUT_DIR / f"{session_id}_decisions_template.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TEMPLATE_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow({
                "entity_id": record.get("entity_id", ""),
                "review_decision": "",
                "reviewer": "",
                "reviewed_at": "",
                "decision_note": "",
                "session_id": session_id,
                "within_session_order": record.get("within_session_order", ""),
                "entity_type": record.get("entity_type", ""),
                "display_name": record.get("display_name", ""),
                "queue_status": record.get("queue_status", ""),
                "review_status": record.get("review_status", ""),
                "review_batch": record.get("review_batch", ""),
                "review_bucket": record.get("review_bucket", ""),
                "source_refs": "|".join(record.get("source_refs", [])),
                "cleaned_paths": "|".join(record.get("cleaned_paths", [])),
                "parsed_paths": "|".join(record.get("parsed_paths", [])),
                "top_extract_ids": "|".join(record.get("top_extract_ids", [])),
                "decision_instructions": decision_instructions(record),
            })
    return path


def write_readme(grouped):
    lines = [
        "# 人工复核会话决策模板",
        "",
        "## 范围",
        "",
        "本目录按 session 生成可填写参考模板，方便逐批复核。模板可以由流水线覆盖；人工最终决策仍应写入主文件 `data/review_inputs/human_review_decisions.csv`。",
        "",
        "## 使用方式",
        "",
        "1. 打开对应 session 的指南和模板 CSV。",
        "2. 只把人工确认后的 `entity_id`、`review_decision`、`reviewer`、`reviewed_at`、`decision_note` 写入主决策文件。",
        "3. 如果先填写 session 模板，可运行 `python3 -m bgpkb.pipeline.import_human_review_session_decisions --session-id review_session_001` 做 dry-run；确认后显式加 `--write` 合并到主决策文件。",
        "4. 若需要语义判断或 LLM，填写 `needs_semantic_review` 或保持 `unreviewed`，当前流水线只记录并跳过。",
        "5. 填写主决策文件后运行 `python3 -m bgpkb.pipeline.build_human_review_decision_audit`。",
        "",
        "## 模板文件",
        "",
    ]
    for session_id, records in sorted(grouped.items()):
        lines.append(f"- `{session_id}_decisions_template.csv`：{len(records)} 条")
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未自动批准、拒绝或改写实体。",
        "- 未把 session 模板自动合并进主决策文件。",
        "- `src/bgpkb/pipeline/import_human_review_session_decisions.py` 默认 dry-run，只有显式 `--write` 才会写入主决策文件。",
        "- 未调用 LLM，也不下载新来源。",
    ])
    README.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(records, grouped, output_paths):
    by_status = Counter(record.get("queue_status", "unknown") for record in records)
    by_session_size = Counter(len(items) for items in grouped.values())
    lines = [
        "# 人工复核会话决策模板报告",
        "",
        "## 范围",
        "",
        "本报告记录按 session 生成的人工决策模板。它只切分和预填上下文字段，不判断实体是否应批准或拒绝，不覆盖主人工决策文件。",
        "",
        "## 摘要",
        "",
        f"- 模板文件数：{len(output_paths)}",
        f"- 模板记录数：{len(records)}",
        f"- 输出目录：`data/review_inputs/human_review_session_decision_templates/`",
        f"- 主人工决策文件：`{DECISION_INPUT}`",
        "",
        "## 按队列状态统计",
        "",
    ]
    for status, count in sorted(by_status.items()):
        lines.append(f"- {status}：{count}")
    lines.extend(["", "## 按 session 大小统计", ""])
    for size, count in sorted(by_session_size.items()):
        lines.append(f"- {size} 条/session：{count} 个")
    lines.extend(["", "## 模板清单", ""])
    for path in output_paths:
        lines.append(f"- `{path.relative_to(ROOT).as_posix()}`")
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未自动批准、拒绝或改写实体。",
        "- 未把 session 模板自动合并进 `data/review_inputs/human_review_decisions.csv`。",
        "- 未执行语义判断、LLM 或新来源下载。",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    records = load_jsonl(DATASET_DIR / "human_review_session_queue.jsonl")
    records.sort(key=lambda item: (item.get("session_order", 999999), item.get("within_session_order", 999999)))
    grouped = defaultdict(list)
    for record in records:
        grouped[record.get("session_id", "unknown")].append(record)

    cleanup_old_templates()
    output_paths = []
    for session_id, session_records in sorted(grouped.items()):
        output_paths.append(write_session_template(session_id, session_records))
    write_readme(grouped)
    write_report(records, grouped, output_paths)

    print(f"Wrote {len(output_paths)} templates in {OUTPUT_DIR.relative_to(ROOT)}")
    print(f"Wrote {README.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
