#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
DATASET_DIR = paths.DATASETS_DIR
REVIEW_INPUT_DIR = paths.REVIEW_INPUTS_DIR
TEMPLATE_CSV = REVIEW_INPUT_DIR / "human_review_decisions_template.csv"
DECISIONS_CSV = REVIEW_INPUT_DIR / "human_review_decisions.csv"
REPORT = paths.report_path("human_review_decision_template_report")

FIELDS = [
    "entity_id",
    "review_decision",
    "reviewer",
    "reviewed_at",
    "decision_note",
]

TEMPLATE_FIELDS = [
    *FIELDS,
    "entity_type",
    "display_name",
    "review_batch",
    "review_bucket",
    "source_paths",
    "cleaned_paths",
    "chunk_sample_ids",
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


def write_decision_input_if_missing():
    REVIEW_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    created = False
    if not DECISIONS_CSV.exists():
        with DECISIONS_CSV.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
        created = True
    return created


def write_template(records):
    REVIEW_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    with TEMPLATE_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TEMPLATE_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow({
                "entity_id": record.get("entity_id", ""),
                "review_decision": "",
                "reviewer": "",
                "reviewed_at": "",
                "decision_note": "",
                "entity_type": record.get("entity_type", ""),
                "display_name": record.get("display_name", ""),
                "review_batch": record.get("review_batch", ""),
                "review_bucket": record.get("review_bucket", ""),
                "source_paths": "|".join(record.get("source_paths", [])),
                "cleaned_paths": "|".join(record.get("cleaned_paths", [])),
                "chunk_sample_ids": "|".join(record.get("chunk_sample_ids", [])),
                "decision_instructions": record.get("decision_instructions", ""),
            })


def write_report(records, created_decision_file):
    by_batch = Counter(record.get("review_batch", "unknown") for record in records)
    lines = [
        "# 人工复核决策输入模板报告",
        "",
        "## 范围",
        "",
        "本报告记录人工复核决策输入区的确定性生成结果。模板可被覆盖再生成；人工填写文件只在不存在时初始化表头，不会被流水线覆盖。",
        "",
        "## 摘要",
        "",
        f"- 模板记录数：{len(records)}",
        f"- 模板输出：`data/review_inputs/human_review_decisions_template.csv`",
        f"- 人工填写文件：`data/review_inputs/human_review_decisions.csv`",
        f"- 本次是否初始化人工填写文件：{'是' if created_decision_file else '否'}",
        "- 允许的 review_decision：`approved`、`rejected`、`needs_source`、`needs_semantic_review`；留空或 `unreviewed` 表示不应用。",
        "",
        "## 按复核批次统计",
        "",
    ]
    for batch, count in sorted(by_batch.items()):
        lines.append(f"- {batch}：{count}")
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未判断任何实体是否应批准或拒绝。",
        "- 未修改 `data/knowledge/entities/*.jsonl`。",
        "- `needs_semantic_review` 只作为人工标记进入审计，后续仍按规则跳过语义/LLM 处理。",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    records = load_jsonl(DATASET_DIR / "human_review_workbook.jsonl")
    created_decision_file = write_decision_input_if_missing()
    write_template(records)
    write_report(records, created_decision_file)
    print(f"Wrote {TEMPLATE_CSV.relative_to(ROOT)}")
    print(f"Checked {DECISIONS_CSV.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
