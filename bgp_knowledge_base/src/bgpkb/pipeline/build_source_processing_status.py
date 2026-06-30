#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
DATASET_DIR = paths.DATASETS_DIR
REPORT = paths.report_path("source_processing_status_report")
JSONL_OUTPUT = DATASET_DIR / "source_processing_status.jsonl"
CSV_OUTPUT = DATASET_DIR / "source_processing_status.csv"


def load_sources():
    with (paths.INVENTORY_DIR / "sources.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_output_dirs(raw_path):
    rel = raw_path.as_posix()
    if rel.startswith("data/sources/raw/standards/"):
        return "standards", "standards"
    if rel.startswith("data/sources/raw/data_docs/") or rel.startswith("data/sources/raw/tools_docs/"):
        return "data_docs", "data_docs"
    if rel.startswith("data/sources/raw/papers/"):
        return "papers", "papers"
    if rel.startswith("data/sources/raw/cases/"):
        return "cases", "cases"
    return None, None


def is_parseable(raw_path):
    return raw_path.suffix in {".txt", ".html", ".pdf", ".yaml", ".yml"}


def load_jsonl_count_by_field(path, field):
    counts = Counter()
    if not path.exists():
        return counts
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        counts[record.get(field)] += 1
    return counts


def load_chunk_counts():
    counts = Counter()
    for path in (paths.CHUNKS_DIR).glob("*.jsonl"):
        counts.update(load_jsonl_count_by_field(path, "doc_id"))
    return counts


def build_record(source, chunk_counts, observation_counts):
    source_id = source["source_id"]
    source_type = source["source_type"]
    source_path = source.get("path", "")
    notes = []

    raw_status = "unarchived"
    parseable = False
    parsed_status = "not_applicable"
    cleaned_status = "not_applicable"

    if not source_path:
        notes.append("inventory 未登记本地 path")
    else:
        resolved = (ROOT / source_path).resolve()
        if not resolved.exists():
            raw_status = "missing"
            notes.append("inventory path 指向的文件不存在")
        elif source_path.startswith("../"):
            raw_status = "external_note"
            notes.append("来源位于知识库目录外")
        else:
            raw_status = "archived"
            rel_path = resolved.relative_to(ROOT)
            parseable = is_parseable(rel_path)
            if parseable:
                parsed_subdir, cleaned_subdir = parse_output_dirs(rel_path)
                parsed_status = "present" if (paths.PARSED_DIR / parsed_subdir / f"{rel_path.stem}.json").exists() else "missing"
                cleaned_status = "present" if (paths.CLEANED_DIR / cleaned_subdir / f"{rel_path.stem}.md").exists() else "missing"
            else:
                notes.append("当前确定性解析器不支持该文件格式")

    chunk_count = chunk_counts.get(source_id, 0)
    case_observation_count = observation_counts.get(source_id, 0)

    if source_type == "manual_note":
        processing_status = "manual_note"
    elif raw_status == "unarchived":
        processing_status = "unarchived"
    elif raw_status == "missing":
        processing_status = "incomplete"
    elif parseable and parsed_status == "present" and cleaned_status == "present" and chunk_count > 0:
        processing_status = "complete_deterministic"
    elif raw_status == "archived" and not parseable:
        processing_status = "raw_only_unparseable"
    else:
        processing_status = "incomplete"

    return {
        "source_id": source_id,
        "source_type": source_type,
        "path": source_path,
        "raw_status": raw_status,
        "parseable": parseable,
        "parsed_status": parsed_status,
        "cleaned_status": cleaned_status,
        "chunk_count": chunk_count,
        "case_observation_count": case_observation_count,
        "processing_status": processing_status,
        "notes": "；".join(notes),
    }


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
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
        "notes",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def write_report(records):
    by_status = Counter(record["processing_status"] for record in records)
    by_type = Counter(record["source_type"] for record in records)
    lines = [
        "# 来源处理状态报告",
        "",
        "## 范围",
        "",
        "本报告按 `data/sources/inventory/sources.csv` 的 source_id 汇总确定性处理状态，只根据文件存在性和已生成产物统计，不进行语义判断。",
        "",
        "## 摘要",
        "",
        f"- 来源总数：{len(records)}",
        f"- JSONL 输出：`data/derived/datasets/source_processing_status.jsonl`",
        f"- CSV 输出：`data/derived/datasets/source_processing_status.csv`",
        "",
        "## 按处理状态统计",
        "",
    ]
    for status, count in sorted(by_status.items()):
        lines.append(f"- {status}：{count}")
    lines.extend(["", "## 按来源类型统计", ""])
    for source_type, count in sorted(by_type.items()):
        lines.append(f"- {source_type}：{count}")

    lines.extend(["", "## 未完成或未归档来源", ""])
    incomplete = [
        record
        for record in records
        if record["processing_status"] not in {"complete_deterministic", "manual_note"}
    ]
    if incomplete:
        for record in incomplete:
            lines.append(
                f"- {record['source_id']}：{record['processing_status']}；"
                f"raw={record['raw_status']}；parsed={record['parsed_status']}；"
                f"cleaned={record['cleaned_status']}；chunks={record['chunk_count']}；{record['notes']}"
            )
    else:
        lines.append("- 无")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    sources = load_sources()
    chunk_counts = load_chunk_counts()
    observation_counts = load_jsonl_count_by_field(DATASET_DIR / "case_observations.jsonl", "source_id")
    records = [build_record(source, chunk_counts, observation_counts) for source in sources]
    records.sort(key=lambda item: item["source_id"])
    write_jsonl(records)
    write_csv(records)
    write_report(records)
    print(f"Wrote {JSONL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {CSV_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
