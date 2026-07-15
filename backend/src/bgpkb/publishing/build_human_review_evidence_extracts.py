#!/usr/bin/env python3
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from bgpkb import paths
from bgpkb.ingestion.legacy_canonical_adapter import read_legacy_read_only


ROOT = paths.PROJECT_ROOT
CHUNK_DIR = paths.CHUNKS_DIR
DATASET_DIR = paths.DATASETS_DIR
REPORT = paths.report_path("human_review_evidence_extracts_report")
JSONL_OUTPUT = DATASET_DIR / "human_review_evidence_extracts.jsonl"
CSV_OUTPUT = DATASET_DIR / "human_review_evidence_extracts.csv"

MAX_EXTRACTS_PER_ENTITY = 6
EXCERPT_LIMIT = 650

STOPWORDS = {
    "and",
    "for",
    "from",
    "into",
    "that",
    "the",
    "this",
    "with",
    "uses",
    "used",
    "using",
    "route",
    "routing",
    "bgp",
}


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def tokenize(value):
    tokens = []
    for token in re.findall(r"[A-Za-z0-9_./:-]+", str(value).lower()):
        normalized = token.strip("_./:-")
        if len(normalized) < 3:
            continue
        if normalized in STOPWORDS:
            continue
        tokens.append(normalized)
    return tokens


def collect_terms(value):
    terms = []
    if isinstance(value, dict):
        for nested in value.values():
            terms.extend(collect_terms(nested))
    elif isinstance(value, list):
        for nested in value:
            terms.extend(collect_terms(nested))
    elif isinstance(value, str):
        terms.extend(tokenize(value))
    return terms


def entity_terms(workbook_record, packet_record):
    terms = []
    for field in ("entity_id", "entity_type", "display_name"):
        terms.extend(tokenize(workbook_record.get(field, "")))
    for ref in workbook_record.get("source_refs", []):
        terms.extend(tokenize(ref))
    terms.extend(collect_terms(packet_record.get("entity_payload", {})))
    counts = Counter(terms)
    return [term for term, _count in counts.most_common(24)]


def load_chunks_by_id():
    chunks = {}
    for path in sorted(CHUNK_DIR.rglob("*.jsonl")):
        legacy = read_legacy_read_only(path, allow_legacy=True)
        for record in legacy["content"]:
            chunk_id = record.get("chunk_id")
            if chunk_id:
                chunks[chunk_id] = {
                    **record,
                    "chunk_file": path.relative_to(ROOT).as_posix(),
                    "input_mode": legacy["mode"],
                    "legacy_diagnostic_code": legacy["diagnostic"]["code"],
                }
    return chunks


def excerpt_for(content, matched_terms):
    text = str(content).replace("\x00", " ")
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    lower = text.lower()
    positions = [lower.find(term.lower()) for term in matched_terms if lower.find(term.lower()) >= 0]
    if positions:
        start = max(0, min(positions) - 120)
    else:
        start = 0
    end = min(len(text), start + EXCERPT_LIMIT)
    excerpt = text[start:end].strip()
    if start > 0:
        excerpt = "..." + excerpt
    if end < len(text):
        excerpt = excerpt + "..."
    return excerpt


def score_chunk(chunk, terms):
    content = chunk.get("content", "")
    haystack = " ".join([
        content,
        chunk.get("chunk_id", ""),
        chunk.get("doc_id", ""),
        chunk.get("title", ""),
        " ".join(chunk.get("topics", [])),
        " ".join(chunk.get("section_path", [])),
    ]).lower()
    matched = []
    for term in terms:
        if term.lower() in haystack:
            matched.append(term)
    score = len(set(matched))
    return score, sorted(set(matched))


def load_packets_by_entity():
    return {
        record.get("entity_id"): record
        for record in load_jsonl(DATASET_DIR / "entity_review_packets.jsonl")
        if record.get("entity_id")
    }


def build_records():
    chunks_by_id = load_chunks_by_id()
    packets_by_entity = load_packets_by_entity()
    records = []
    missing_chunks = []

    workbook_records = load_jsonl(DATASET_DIR / "human_review_workbook.jsonl")
    for workbook in workbook_records:
        entity_id = workbook.get("entity_id", "")
        packet = packets_by_entity.get(entity_id, {})
        terms = entity_terms(workbook, packet)
        scored_chunks = []
        for chunk_id in workbook.get("chunk_sample_ids", []):
            chunk = chunks_by_id.get(chunk_id)
            if not chunk:
                missing_chunks.append((entity_id, chunk_id))
                continue
            score, matched_terms = score_chunk(chunk, terms)
            scored_chunks.append((score, chunk_id, matched_terms, chunk))
        scored_chunks.sort(key=lambda item: (-item[0], item[1]))
        for rank, (score, chunk_id, matched_terms, chunk) in enumerate(scored_chunks[:MAX_EXTRACTS_PER_ENTITY], start=1):
            excerpt = excerpt_for(chunk.get("content", ""), matched_terms)
            records.append({
                "extract_id": f"extract_{entity_id}_{rank:02d}",
                "entity_id": entity_id,
                "entity_type": workbook.get("entity_type", ""),
                "display_name": workbook.get("display_name", ""),
                "review_order": workbook.get("review_order", 0),
                "review_batch": workbook.get("review_batch", ""),
                "review_bucket": workbook.get("review_bucket", ""),
                "chunk_rank": rank,
                "chunk_id": chunk_id,
                "chunk_file": chunk.get("chunk_file", ""),
                "doc_id": chunk.get("doc_id", ""),
                "source_ref": chunk.get("source_ref", ""),
                "chunk_type": chunk.get("chunk_type", ""),
                "section_path": chunk.get("section_path", []),
                "matched_terms": matched_terms[:12],
                "match_score": score,
                "excerpt": excerpt,
                "excerpt_char_count": len(excerpt),
                "needs_llm": False,
                "llm_skip_reason": "不需要 LLM；本记录只做确定性 chunk 摘录和词项匹配，不判断证据充分性。",
                "input_mode": chunk.get("input_mode", ""),
                "legacy_diagnostic_code": chunk.get("legacy_diagnostic_code", ""),
                "generated_by": "src/bgpkb/pipeline/build_human_review_evidence_extracts.py",
            })
    return records, missing_chunks


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "extract_id",
        "entity_id",
        "entity_type",
        "display_name",
        "review_order",
        "review_batch",
        "review_bucket",
        "chunk_rank",
        "chunk_id",
        "chunk_file",
        "doc_id",
        "source_ref",
        "chunk_type",
        "section_path",
        "matched_terms",
        "match_score",
        "excerpt",
        "excerpt_char_count",
        "needs_llm",
        "llm_skip_reason",
        "input_mode",
        "legacy_diagnostic_code",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["section_path"] = "|".join(row["section_path"])
            row["matched_terms"] = "|".join(row["matched_terms"])
            writer.writerow(row)


def write_report(records, missing_chunks):
    by_type = Counter(record["entity_type"] for record in records)
    by_batch = Counter(record["review_batch"] for record in records)
    entities = sorted({record["entity_id"] for record in records})
    zero_match = [record for record in records if record["match_score"] == 0]
    lines = [
        "# 人工复核证据摘录报告",
        "",
        "## 范围",
        "",
        "本报告从人工复核工作簿、实体复核包和现有 chunks 机械生成。它只摘录 chunk 文本并记录词项匹配，不判断来源是否支持实体字段。",
        "现有 chunks 通过显式 legacy 只读适配器读取，仅供历史审计，不得形成新的批准状态。",
        "",
        "## 摘要",
        "",
        f"- 覆盖实体数：{len(entities)}",
        f"- 摘录记录数：{len(records)}",
        f"- 每个实体最多摘录数：{MAX_EXTRACTS_PER_ENTITY}",
        f"- 缺失 chunk 引用数：{len(missing_chunks)}",
        f"- 零词项匹配摘录数：{len(zero_match)}",
        f"- JSONL 输出：`data/derived/datasets/human_review_evidence_extracts.jsonl`",
        f"- CSV 输出：`data/derived/datasets/human_review_evidence_extracts.csv`",
        "",
        "## 按实体类型统计",
        "",
    ]
    for entity_type, count in sorted(by_type.items()):
        lines.append(f"- {entity_type}：{count}")
    lines.extend(["", "## 按复核批次统计", ""])
    for batch, count in sorted(by_batch.items()):
        lines.append(f"- {batch}：{count}")
    lines.extend([
        "",
        "## 前 20 条摘录索引",
        "",
        "| 实体 | 名称 | chunk | 分数 | 匹配词项 |",
        "| --- | --- | --- | ---: | --- |",
    ])
    for record in records[:20]:
        terms = ", ".join(record["matched_terms"][:8])
        lines.append(
            f"| `{record['entity_id']}` | {record['display_name']} | `{record['chunk_id']}` | "
            f"{record['match_score']} | {terms} |"
        )
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未判断摘录是否足以批准实体。",
        "- 未从摘录中抽取新实体、关系或案例字段。",
        "- 未处理需要语义判断或 LLM 的复核事项。",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    records, missing_chunks = build_records()
    write_jsonl(records)
    write_csv(records)
    write_report(records, missing_chunks)
    print(f"Wrote {JSONL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {CSV_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    if missing_chunks:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
