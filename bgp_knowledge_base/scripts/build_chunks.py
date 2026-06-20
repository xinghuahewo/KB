#!/usr/bin/env python3
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHUNK_DIR = ROOT / "chunks"
MANUAL_CHUNK_SEED = CHUNK_DIR / "seeds" / "context_chunks.jsonl"
MAX_CHARS = 1800
MIN_CHARS = 220


def load_sources():
    sources = {}
    with (ROOT / "inventory" / "sources.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            sources[row["source_id"]] = row
    return sources


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_space(text):
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_content(text, max_chars=MAX_CHARS):
    text = normalize_space(text)
    if not text:
        return []
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks = []
    current = ""
    for para in paragraphs:
        if len(para) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            sentences = re.split(r"(?<=[.!?。！？])\s+", para)
            piece = ""
            for sentence in sentences:
                if len(sentence) > max_chars:
                    if piece:
                        chunks.append(piece.strip())
                        piece = ""
                    for start in range(0, len(sentence), max_chars):
                        chunks.append(sentence[start:start + max_chars].strip())
                    continue
                if len(piece) + len(sentence) + 1 <= max_chars:
                    piece = f"{piece} {sentence}".strip()
                else:
                    if piece:
                        chunks.append(piece.strip())
                    piece = sentence
            if piece:
                chunks.append(piece.strip())
            continue

        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            current = para

    if current:
        chunks.append(current.strip())
    return [chunk for chunk in chunks if len(chunk) >= MIN_CHARS]


def infer_topics(text, source_row):
    haystack = f"{source_row.get('title', '')} {source_row.get('domain', '')} {source_row.get('notes', '')} {text}".lower()
    topic_rules = [
        ("BGP", ["bgp", "border gateway protocol"]),
        ("AS_PATH", ["as_path", "as path"]),
        ("Route Leak", ["route leak", "leak"]),
        ("Prefix Hijack", ["hijack", "hijacking"]),
        ("RPKI", ["rpki", "roa", "rov", "vrp"]),
        ("BGPsec", ["bgpsec"]),
        ("ASPA", ["aspa", "provider authorization"]),
        ("Collector", ["collector", "routeviews", "ripe ris", "ris"]),
        ("BGPStream", ["bgpstream"]),
        ("AS Relationship", ["relationship", "customer", "provider", "peer"]),
        ("Outage", ["outage", "withdrawal", "disappeared"]),
        ("MOAS", ["moas", "multiple origin"]),
    ]
    topics = []
    for topic, needles in topic_rules:
        if any(needle in haystack for needle in needles):
            topics.append(topic)
    return topics[:8] or [source_row.get("domain") or "BGP"]


def chunk_type_for(source_type):
    return {
        "standard": "standard_section",
        "data_doc": "data_source_documentation",
        "tool_doc": "tool_documentation",
        "paper": "paper_method_source",
        "case_report": "case_report_source",
        "blog": "case_report_source",
        "manual_note": "manual_note",
    }.get(source_type, "source_text")


def output_file_for(source_type):
    if source_type == "standard":
        return "standard_chunks.jsonl"
    if source_type == "paper":
        return "paper_chunks.jsonl"
    if source_type in {"case_report", "blog"}:
        return "case_chunks.jsonl"
    return "bgp_chunks.jsonl"


def make_chunks_for_doc(path, sources):
    doc = load_json(path)
    doc_id = doc["doc_id"]
    source_row = sources.get(doc_id, {})
    source_type = source_row.get("source_type") or path.parent.name
    title = source_row.get("title") or doc.get("title") or doc_id
    records = []

    for section_index, section in enumerate(doc.get("sections", []), start=1):
        section_id = str(section.get("section_id") or section_index)
        heading = section.get("heading") or title
        parts = split_content(section.get("content", ""))
        for part_index, content in enumerate(parts, start=1):
            normalized_section_id = re.sub(r"[^A-Za-z0-9]+", "_", section_id).strip("_") or "section"
            chunk_id = f"{doc_id}_s{section_index:03d}_{normalized_section_id}_{part_index:03d}"
            records.append({
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "source_type": source_type,
                "title": title,
                "section_path": [heading],
                "chunk_type": chunk_type_for(source_type),
                "topics": infer_topics(content, source_row),
                "content": content,
                "source_ref": f"{doc.get('source_path', doc_id)}#{section_id}",
                "language": source_row.get("language") or "en",
                "review_status": "pending",
            })
    return output_file_for(source_type), records


def load_manual_context_chunks():
    if not MANUAL_CHUNK_SEED.exists():
        return []
    records = []
    for line in MANUAL_CHUNK_SEED.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("doc_id") == "context_2026":
            records.append(record)
    return records


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main():
    sources = load_sources()
    grouped = {
        "bgp_chunks.jsonl": load_manual_context_chunks(),
        "standard_chunks.jsonl": [],
        "paper_chunks.jsonl": [],
        "case_chunks.jsonl": [],
    }

    parsed_files = sorted((ROOT / "parsed").glob("*/*.json"))
    for path in parsed_files:
        output_name, records = make_chunks_for_doc(path, sources)
        grouped.setdefault(output_name, []).extend(records)

    for output_name, records in grouped.items():
        records.sort(key=lambda item: item["chunk_id"])
        write_jsonl(CHUNK_DIR / output_name, records)

    for output_name in sorted(grouped):
        print(f"{output_name}: {len(grouped[output_name])} chunks")


if __name__ == "__main__":
    main()
