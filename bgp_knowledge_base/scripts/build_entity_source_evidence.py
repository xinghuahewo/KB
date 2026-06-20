#!/usr/bin/env python3
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTITY_DIR = ROOT / "entities"
DATASET_DIR = ROOT / "datasets"
REPORT = ROOT / "reports" / "entity_source_evidence_report.md"
JSONL_OUTPUT = DATASET_DIR / "entity_source_evidence.jsonl"
CSV_OUTPUT = DATASET_DIR / "entity_source_evidence.csv"
CHUNK_SAMPLE_LIMIT = 20
STOP_TERMS = {
    "as",
    "bgp",
    "case",
    "event",
    "evidence",
    "hijack",
    "leak",
    "origin",
    "path",
    "prefix",
    "route",
    "routing",
    "source",
    "target",
    "update",
}


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def load_entities():
    records = []
    for path in sorted(ENTITY_DIR.glob("*.jsonl")):
        for record in load_jsonl(path):
            records.append(record)
    return records


def load_source_statuses():
    return {
        record["source_id"]: record
        for record in load_jsonl(DATASET_DIR / "source_processing_status.jsonl")
    }


def load_chunks_by_doc():
    chunks_by_doc = defaultdict(list)
    for path in sorted((ROOT / "chunks").glob("*.jsonl")):
        for record in load_jsonl(path):
            doc_id = record.get("doc_id")
            chunk_id = record.get("chunk_id")
            if doc_id and chunk_id:
                chunks_by_doc[doc_id].append(record)
    return {
        doc_id: sorted(records, key=lambda item: item.get("chunk_id", ""))
        for doc_id, records in chunks_by_doc.items()
    }


def load_case_observation_counts():
    counts = Counter()
    for record in load_jsonl(DATASET_DIR / "case_observations.jsonl"):
        source_id = record.get("source_id")
        if source_id:
            counts[source_id] += 1
    return counts


def parsed_path_for(source_id):
    matches = sorted((ROOT / "parsed").glob(f"*/{source_id}.json"))
    if matches:
        return matches[0].relative_to(ROOT).as_posix()
    return ""


def cleaned_path_for(source_id):
    matches = sorted((ROOT / "cleaned").glob(f"*/{source_id}.md"))
    if matches:
        return matches[0].relative_to(ROOT).as_posix()
    return ""


def normalize_text(value):
    return str(value).lower().replace("_", " ").replace("-", " ")


def compact_text(value):
    return "".join(str(value).lower().split())


def add_term(terms, value):
    value = str(value).strip()
    normalized = normalize_text(value)
    if len(value) >= 3 and normalized not in STOP_TERMS:
        terms.add(value.lower())


def entity_terms(entity):
    primary_terms = set()
    secondary_terms = set()
    for field in ("id", "name", "paper", "applies_to"):
        value = entity.get(field)
        if isinstance(value, str):
            add_term(primary_terms, value)
            for token in normalize_text(value).split():
                add_term(primary_terms, token)
    for field in ("event_type", "date"):
        value = entity.get(field)
        if isinstance(value, str):
            add_term(secondary_terms, value)
            for token in normalize_text(value).split():
                add_term(secondary_terms, token)
    for field in ("aliases", "affected_prefixes", "required_evidence", "optional_evidence", "evidence"):
        value = entity.get(field)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    target = primary_terms if field in {"aliases", "affected_prefixes"} else secondary_terms
                    add_term(target, item)
                    for token in normalize_text(item).split():
                        add_term(target, token)
    for item in entity.get("involved_ases", []):
        if isinstance(item, dict):
            for value in item.values():
                add_term(primary_terms, value)
    return primary_terms, secondary_terms


def chunk_score(chunk, terms):
    content = chunk.get("content", "")
    content_normalized = normalize_text(content)
    content_compact = compact_text(content)
    score = 0
    for term in terms:
        term_normalized = normalize_text(term)
        term_compact = compact_text(term)
        if term_normalized and term_normalized in content_normalized:
            score += 2
        elif term_compact and len(term_compact) >= 6 and term_compact in content_compact:
            score += 1
    return score


def sample_chunk_ids(entity, chunk_records):
    primary_terms, secondary_terms = entity_terms(entity)
    ranked = []
    fallback = []
    for index, chunk in enumerate(chunk_records):
        chunk_id = chunk.get("chunk_id", "")
        if not chunk_id:
            continue
        primary_score = chunk_score(chunk, primary_terms)
        secondary_score = chunk_score(chunk, secondary_terms)
        score = primary_score + secondary_score
        if score > 0:
            ranked.append((primary_score, score, index, chunk_id))
        else:
            fallback.append((index, chunk_id))
    selected = []
    seen = set()
    for _, _, _, chunk_id in sorted(ranked, key=lambda item: (-item[0], -item[1], item[2])):
        if chunk_id not in seen:
            selected.append(chunk_id)
            seen.add(chunk_id)
        if len(selected) >= CHUNK_SAMPLE_LIMIT:
            return selected
    for _, chunk_id in fallback:
        if chunk_id not in seen:
            selected.append(chunk_id)
            seen.add(chunk_id)
        if len(selected) >= CHUNK_SAMPLE_LIMIT:
            break
    return selected


def build_record(entity, source_id, source_statuses, chunks_by_doc, observation_counts):
    status = source_statuses.get(source_id, {})
    chunk_records = chunks_by_doc.get(source_id, [])
    return {
        "evidence_id": f"{entity['id']}__{source_id}",
        "entity_id": entity["id"],
        "entity_type": entity.get("entity_type", ""),
        "entity_review_status": entity.get("review_status", "pending"),
        "source_id": source_id,
        "source_type": status.get("source_type", ""),
        "source_status": status.get("processing_status", "unknown_source"),
        "source_path": status.get("path", ""),
        "parsed_path": parsed_path_for(source_id),
        "cleaned_path": cleaned_path_for(source_id),
        "chunk_count": len(chunk_records),
        "chunk_sample_ids": sample_chunk_ids(entity, chunk_records),
        "case_observation_count": observation_counts.get(source_id, 0),
        "generated_by": "scripts/build_entity_source_evidence.py",
    }


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "evidence_id",
        "entity_id",
        "entity_type",
        "entity_review_status",
        "source_id",
        "source_type",
        "source_status",
        "source_path",
        "parsed_path",
        "cleaned_path",
        "chunk_count",
        "chunk_sample_ids",
        "case_observation_count",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["chunk_sample_ids"] = "|".join(record["chunk_sample_ids"])
            writer.writerow(row)


def write_report(records):
    by_entity_type = Counter(record["entity_type"] for record in records)
    by_source_status = Counter(record["source_status"] for record in records)
    by_source_type = Counter(record["source_type"] for record in records)
    rows_without_chunks = [
        record for record in records
        if record["source_status"] != "manual_note" and record["chunk_count"] == 0
    ]
    rows_without_parsed = [
        record for record in records
        if record["source_status"] != "manual_note" and not record["parsed_path"]
    ]
    lines = [
        "# 实体来源证据索引报告",
        "",
        "## 范围",
        "",
        "本报告从 `entities/*.jsonl`、来源处理状态、chunks 和案例观察值机械生成实体到来源的证据索引。该步骤不判断来源是否真正支持实体定义，也不改变审核状态，只列出人工复核可打开的证据位置。",
        "",
        "## 摘要",
        "",
        f"- 证据索引记录数：{len(records)}",
        f"- JSONL 输出：`datasets/entity_source_evidence.jsonl`",
        f"- CSV 输出：`datasets/entity_source_evidence.csv`",
        f"- chunk_sample_ids 每条最多保留：{CHUNK_SAMPLE_LIMIT}",
        "- chunk_sample_ids 选择规则：优先保留与实体 ID、名称、事件类型、AS 编号、prefix 等字段机械匹配的 chunk；不足时按文档顺序补齐。",
        f"- 非 manual note 且 chunk_count=0 的记录数：{len(rows_without_chunks)}",
        f"- 非 manual note 且缺失 parsed_path 的记录数：{len(rows_without_parsed)}",
        "",
        "## 按实体类型统计",
        "",
    ]
    for entity_type, count in sorted(by_entity_type.items()):
        lines.append(f"- {entity_type}：{count}")
    lines.extend(["", "## 按来源状态统计", ""])
    for status, count in sorted(by_source_status.items()):
        lines.append(f"- {status}：{count}")
    lines.extend(["", "## 按来源类型统计", ""])
    for source_type, count in sorted(by_source_type.items()):
        label = source_type or "unknown"
        lines.append(f"- {label}：{count}")
    lines.extend(["", "## 需要注意的机械缺口", ""])
    if rows_without_chunks or rows_without_parsed:
        for record in rows_without_chunks[:50]:
            lines.append(f"- {record['entity_id']} -> {record['source_id']}：chunk_count=0")
        for record in rows_without_parsed[:50]:
            lines.append(f"- {record['entity_id']} -> {record['source_id']}：缺失 parsed_path")
    else:
        lines.append("- 无")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    source_statuses = load_source_statuses()
    chunks_by_doc = load_chunks_by_doc()
    observation_counts = load_case_observation_counts()
    records = []
    for entity in load_entities():
        for source_id in entity.get("source_refs", []):
            source_id = str(source_id).strip()
            if source_id:
                records.append(build_record(entity, source_id, source_statuses, chunks_by_doc, observation_counts))
    records.sort(key=lambda item: (item["entity_type"], item["entity_id"], item["source_id"]))
    write_jsonl(records)
    write_csv(records)
    write_report(records)
    print(f"Wrote {JSONL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {CSV_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
