#!/usr/bin/env python3
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from bgpkb import paths
from bgpkb.ingestion.legacy_canonical_adapter import read_legacy_read_only


ROOT = paths.PROJECT_ROOT
DATASET_DIR = paths.DATASETS_DIR
REPORT = paths.report_path("case_observation_report")
JSONL_OUTPUT = DATASET_DIR / "case_observations.jsonl"
CSV_OUTPUT = DATASET_DIR / "case_observations.csv"

OBSERVATION_PATTERNS = [
    ("ipv4_prefix", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}/(?:[0-9]|[12][0-9]|3[0-2])\b")),
    ("asn", re.compile(r"\bAS\s?([0-9]{1,10})\b", re.IGNORECASE)),
    ("iso_date", re.compile(r"\b20[0-9]{2}-[01][0-9]-[0-3][0-9]\b")),
    (
        "month_date",
        re.compile(
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
            r"\s+[0-3]?[0-9](?:st|nd|rd|th)?(?:,?\s+20[0-9]{2})?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "day_month_date",
        re.compile(
            r"\b[0-3]?[0-9]\s+"
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
            r"\s+20[0-9]{2}\b",
            re.IGNORECASE,
        ),
    ),
    ("bgp4mp_timestamp", re.compile(r"\bBGP4MP\|[0-9]{2}/[0-9]{2}/[0-9]{2}\s+[0-9]{2}:[0-9]{2}:[0-9]{2}\b")),
    ("utc_time", re.compile(r"\b[0-2][0-9]:[0-5][0-9](?::[0-5][0-9])?\s?UTC\b", re.IGNORECASE)),
]


def load_sources():
    with (paths.INVENTORY_DIR / "sources.csv").open(newline="", encoding="utf-8") as handle:
        return [row for row in csv.DictReader(handle)]


def cleaned_case_path(source_id):
    return paths.CLEANED_DIR / "cases" / f"{source_id}.md"


def normalize_value(observation_type, match):
    if observation_type == "asn":
        return f"AS{match.group(1)}"
    return match.group(0).strip()


def context_window(text, start, end, radius=120):
    prefix_start = max(0, start - radius)
    suffix_end = min(len(text), end + radius)
    context = text[prefix_start:suffix_end]
    context = re.sub(r"\s+", " ", context).strip()
    return context


def extract_observations(source):
    source_id = source["source_id"]
    path = cleaned_case_path(source_id)
    if not path.exists():
        return [], {"source_id": source_id, "status": "missing_cleaned"}

    legacy = read_legacy_read_only(path, allow_legacy=True)
    text = legacy["content"]
    diagnostic_code = legacy["diagnostic"]["code"]
    seen = set()
    records = []
    for observation_type, pattern in OBSERVATION_PATTERNS:
        for match in pattern.finditer(text):
            value = normalize_value(observation_type, match)
            key = (source_id, observation_type, value)
            if key in seen:
                continue
            seen.add(key)
            records.append({
                "source_id": source_id,
                "title": source["title"],
                "observation_type": observation_type,
                "value": value,
                "context": context_window(text, match.start(), match.end()),
                "source_ref": f"data/corpus/cleaned/cases/{source_id}.md",
                "review_status": "pending",
                "input_mode": legacy["mode"],
                "legacy_diagnostic_code": diagnostic_code,
            })
    records.sort(key=lambda item: (item["observation_type"], item["value"]))
    return records, {
        "source_id": source_id,
        "status": "processed",
        "count": len(records),
        "input_mode": legacy["mode"],
        "diagnostic_code": diagnostic_code,
    }


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    fields = [
        "source_id", "title", "observation_type", "value", "context", "source_ref",
        "review_status", "input_mode", "legacy_diagnostic_code",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def write_report(records, case_statuses, total_cases):
    by_type = Counter(record["observation_type"] for record in records)
    by_case = defaultdict(Counter)
    for record in records:
        by_case[record["source_id"]][record["observation_type"]] += 1

    missing = [item["source_id"] for item in case_statuses if item["status"] == "missing_cleaned"]
    lines = [
        "# 案例观察值抽取报告",
        "",
        "## 范围",
        "",
        "本报告只记录从已清洗案例文本中用正则规则直接抽取到的观察值，不进行语义判断，不推断 AS 角色，不判断攻击者/受害者，不写入结构化 Case 实体。",
        "这些输入通过显式 legacy 只读适配器读取，只能用于历史审计，不能进入新 release 的治理决定。",
        "",
        "## 摘要",
        "",
        f"- 案例来源数：{total_cases}",
        f"- 已处理 cleaned 案例数：{total_cases - len(missing)}",
        f"- 缺失 cleaned 案例数：{len(missing)}",
        f"- 观察值总数：{len(records)}",
        f"- JSONL 输出：`data/derived/datasets/case_observations.jsonl`",
        f"- CSV 输出：`data/derived/datasets/case_observations.csv`",
        "",
        "## 按观察类型统计",
        "",
    ]
    if by_type:
        for observation_type, count in sorted(by_type.items()):
            lines.append(f"- {observation_type}：{count}")
    else:
        lines.append("- 无")

    lines.extend(["", "## 按案例统计", ""])
    for source_id in sorted(by_case):
        summary = "，".join(f"{key}={value}" for key, value in sorted(by_case[source_id].items()))
        lines.append(f"- {source_id}：{summary}")
    if missing:
        lines.extend(["", "## 缺失 cleaned 案例", ""])
        lines.extend(f"- {source_id}" for source_id in missing)

    lines.extend([
        "",
        "## 跳过边界",
        "",
        "- 未抽取事件责任方、受害方、泄露方、攻击方等角色，因为这需要语义判断。",
        "- 未抽取证据强度和影响范围，因为这需要结合上下文解释。",
        "- 未自动更新 `data/knowledge/entities/cases.jsonl`，观察值仍需人工核验后才能进入结构化实体。",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    sources = [row for row in load_sources() if row.get("source_type") == "case_report"]
    all_records = []
    statuses = []
    for source in sources:
        records, status = extract_observations(source)
        all_records.extend(records)
        statuses.append(status)

    all_records.sort(key=lambda item: (item["source_id"], item["observation_type"], item["value"]))
    write_jsonl(all_records)
    write_csv(all_records)
    write_report(all_records, statuses, len(sources))
    print(f"Wrote {JSONL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {CSV_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
