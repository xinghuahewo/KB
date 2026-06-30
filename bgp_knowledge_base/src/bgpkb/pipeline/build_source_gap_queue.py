#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
DATASET_DIR = paths.DATASETS_DIR
REPORT = paths.report_path("source_gap_queue_report")
JSONL_OUTPUT = DATASET_DIR / "source_gap_queue.jsonl"
CSV_OUTPUT = DATASET_DIR / "source_gap_queue.csv"

COMPLETE_STATUSES = {"complete_deterministic", "manual_note"}


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def gap_type_for(record):
    status = record.get("processing_status")
    if status == "unarchived":
        return "unarchived_source"
    if record.get("raw_status") == "missing":
        return "missing_raw_file"
    if status == "raw_only_unparseable":
        return "unsupported_format"
    return "incomplete_parse_or_chunk"


def suggested_action_for(record, gap_type):
    source_id = record.get("source_id", "")
    path = record.get("path", "")
    if gap_type == "unarchived_source":
        return "archive_source"
    if gap_type == "missing_raw_file":
        return "fix_missing_raw_path"
    if gap_type == "unsupported_format" and path.endswith(".pdf"):
        return "add_pdf_text_extractor"
    if source_id == "peeringdb_api_docs":
        return "decide_yaml_or_api_schema_policy"
    return "inspect_parse_output"


def build_item(record):
    gap_type = gap_type_for(record)
    return {
        "gap_id": f"gap_{record['source_id']}",
        "source_id": record["source_id"],
        "source_type": record.get("source_type", ""),
        "path": record.get("path", ""),
        "raw_status": record.get("raw_status", ""),
        "parseable": bool(record.get("parseable")),
        "parsed_status": record.get("parsed_status", ""),
        "cleaned_status": record.get("cleaned_status", ""),
        "chunk_count": int(record.get("chunk_count", 0)),
        "case_observation_count": int(record.get("case_observation_count", 0)),
        "processing_status": record.get("processing_status", ""),
        "gap_type": gap_type,
        "suggested_action": suggested_action_for(record, gap_type),
        "notes": record.get("notes", ""),
        "generated_by": "src/bgpkb/pipeline/build_source_gap_queue.py",
    }


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "gap_id",
        "source_id",
        "source_type",
        "path",
        "raw_status",
        "parseable",
        "parsed_status",
        "cleaned_status",
        "chunk_count",
        "case_observation_count",
        "processing_status",
        "gap_type",
        "suggested_action",
        "notes",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def write_report(records):
    by_gap_type = Counter(record["gap_type"] for record in records)
    by_action = Counter(record["suggested_action"] for record in records)
    lines = [
        "# 来源缺口队列报告",
        "",
        "## 范围",
        "",
        "本报告从 `data/derived/datasets/source_processing_status.jsonl` 机械生成来源层缺口队列。该步骤不联网、不归档缺失来源，只把未完成来源转成后续动作清单。",
        "",
        "## 摘要",
        "",
        f"- 队列记录数：{len(records)}",
        f"- JSONL 输出：`data/derived/datasets/source_gap_queue.jsonl`",
        f"- CSV 输出：`data/derived/datasets/source_gap_queue.csv`",
        "",
        "## 按缺口类型统计",
        "",
    ]
    for gap_type, count in sorted(by_gap_type.items()):
        lines.append(f"- {gap_type}：{count}")
    if not by_gap_type:
        lines.append("- 无")
    lines.extend(["", "## 按建议动作统计", ""])
    for action, count in sorted(by_action.items()):
        lines.append(f"- {action}：{count}")
    if not by_action:
        lines.append("- 无")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    source_statuses = load_jsonl(DATASET_DIR / "source_processing_status.jsonl")
    records = [
        build_item(record)
        for record in source_statuses
        if record.get("processing_status") not in COMPLETE_STATUSES
    ]
    records.sort(key=lambda item: (item["suggested_action"], item["source_id"]))
    write_jsonl(records)
    write_csv(records)
    write_report(records)
    print(f"Wrote {JSONL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {CSV_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
