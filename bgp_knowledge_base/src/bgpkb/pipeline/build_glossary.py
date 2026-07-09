#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
ENTITY_DIR = paths.ENTITIES_DIR
DATASET_DIR = paths.DATASETS_DIR
REPORT = paths.report_path("glossary_report")
JSONL_OUTPUT = DATASET_DIR / "glossary.jsonl"
CSV_OUTPUT = DATASET_DIR / "glossary.csv"


def load_jsonl(path):
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def load_entities():
    records = []
    for path in sorted(ENTITY_DIR.glob("*.jsonl")):
        for record in load_jsonl(path):
            record["_entity_file"] = path.name
            records.append(record)
    return records


def list_value(value):
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def text_value(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "；".join(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if value is None:
        return ""
    return str(value)


def term_for(record):
    for field in ("name", "paper", "applies_to", "id"):
        value = text_value(record.get(field))
        if value:
            return value
    return ""


def definition_for(record):
    for field in ("definition", "description", "meaning", "problem"):
        value = text_value(record.get(field))
        if value:
            return value
    required_evidence = text_value(record.get("required_evidence"))
    if required_evidence:
        return required_evidence
    false_positive_checks = text_value(record.get("false_positive_checks"))
    if false_positive_checks:
        return false_positive_checks
    return text_value(record.get("id"))


def category_for(record):
    for field in ("category", "type", "event_type"):
        value = text_value(record.get(field))
        if value:
            return value
    return text_value(record.get("entity_type"))


def build_entry(record):
    entity_id = record["id"]
    return {
        "term_id": f"glossary_{entity_id}",
        "entity_id": entity_id,
        "entity_type": record.get("entity_type", ""),
        "term": term_for(record),
        "aliases": list_value(record.get("aliases")),
        "definition": definition_for(record),
        "category": category_for(record),
        "source_refs": list_value(record.get("source_refs")),
        "review_status": record.get("review_status", "pending"),
        "generated_by": "src/bgpkb/pipeline/build_glossary.py",
    }


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "term_id",
        "entity_id",
        "entity_type",
        "term",
        "aliases",
        "definition",
        "category",
        "source_refs",
        "review_status",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["aliases"] = "|".join(record["aliases"])
            row["source_refs"] = "|".join(record["source_refs"])
            writer.writerow(row)


def write_report(records):
    by_type = Counter(record["entity_type"] for record in records)
    by_status = Counter(record["review_status"] for record in records)
    lines = [
        "# 术语表报告",
        "",
        "## 范围",
        "",
        "本报告从 `data/knowledge/entities/*.jsonl` 机械派生术语表，只搬运已有实体字段，不新增语义解释、不做同义词推断、不改变审核状态。",
        "",
        "## 摘要",
        "",
        f"- 术语记录数：{len(records)}",
        f"- JSONL 输出：`data/derived/datasets/glossary.jsonl`",
        f"- CSV 输出：`data/derived/datasets/glossary.csv`",
        "",
        "## 按实体类型统计",
        "",
    ]
    for entity_type, count in sorted(by_type.items()):
        lines.append(f"- {entity_type}：{count}")
    lines.extend(["", "## 按审核状态统计", ""])
    for status, count in sorted(by_status.items()):
        lines.append(f"- {status}：{count}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    entries = [build_entry(record) for record in load_entities()]
    entries.sort(key=lambda item: (item["term"].casefold(), item["entity_id"]))
    write_jsonl(entries)
    write_csv(entries)
    write_report(entries)
    print(f"Wrote {JSONL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {CSV_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
