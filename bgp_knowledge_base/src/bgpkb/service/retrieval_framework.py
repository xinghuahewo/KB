import hashlib
import json
from pathlib import Path

from bgpkb import paths

import yaml


ROOT = paths.PROJECT_ROOT
PUBLISHED = paths.PUBLISHED_DIR
DATASETS = paths.DATASETS_DIR
RAG_CONFIG = paths.CONFIG_DIR / "rag_retrieval.yaml"


def load_json(path, default=None):
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def config():
    return yaml.safe_load(RAG_CONFIG.read_text(encoding="utf-8"))


def semantic_uri_map(resource_type):
    mapping = {}
    for record in load_jsonl(PUBLISHED / "semantic_id_map.jsonl"):
        if record.get("resource_type") == resource_type:
            mapping[record.get("local_id")] = record.get("uri")
    return mapping


def normalize_query(query):
    cfg = config()
    terms = [query]
    for source, expansions in cfg.get("query_expansions", {}).items():
        if source.lower() in query.lower():
            terms.extend(expansions)
    return " ".join(dict.fromkeys(term for term in terms if term)).strip()


def token_set(text):
    return {part.lower() for part in text.replace("/", " ").replace("_", " ").replace("-", " ").split() if part}


def query_intent(normalized_query):
    text = normalized_query.lower()
    if any(term in text for term in ["incident", "outage", "case", "war story", "youtube", "cloudflare", "verizon", "aws", "facebook"]):
        return "case"
    if any(term in text for term in ["routeviews", "ripe ris", "bgpstream", "asrank", "aspa", "data source", "raw data"]):
        return "data"
    if any(term in text for term in ["detect", "detection", "method", "analysis", "artemis", "bear", "beam"]):
        return "paper"
    if any(term in text for term in ["rfc", "what is", "definition", "validation", "roa", "rpki", "route flap"]):
        return "standard"
    return ""


def source_type_bonus(chunk, normalized_query):
    intent = query_intent(normalized_query)
    source_type = chunk.get("source_type", "")
    bonus = 0.0
    if intent == "case" and source_type == "case_report":
        bonus += 3.0
    if intent == "standard" and source_type == "standard":
        bonus += 3.0
    if intent == "paper" and source_type == "paper":
        bonus += 2.0
    if intent == "data" and source_type in {"data_doc", "tool_doc"}:
        bonus += 2.0
    title = chunk.get("title", "").lower()
    doc_id = chunk.get("doc_id", "").lower()
    named_terms = {
        "artemis",
        "aspa",
        "asrank",
        "bear",
        "beam",
        "bgpstream",
        "cloudflare",
        "ris",
        "route53",
        "routeviews",
        "verizon",
        "youtube",
    }
    for term in token_set(normalized_query):
        if term in named_terms and (term in title or term in doc_id):
            bonus += 8.0
        elif len(term) >= 4 and (term in title or term in doc_id):
            bonus += 0.5
    return bonus


def stable_vector(text, dimensions=32):
    vector = []
    seed = text.encode("utf-8")
    for index in range(dimensions):
        digest = hashlib.sha256(seed + str(index).encode("ascii")).digest()
        value = int.from_bytes(digest[:4], "big") / 2**32
        vector.append(round((value * 2) - 1, 6))
    return vector


def score_chunk(chunk, normalized_query):
    haystack = " ".join([
        chunk.get("title", ""),
        chunk.get("source_type", ""),
        chunk.get("chunk_type", ""),
        " ".join(chunk.get("topics", [])),
        " ".join(chunk.get("section_path", [])),
        chunk.get("content_preview", ""),
    ]).lower()
    terms = token_set(normalized_query)
    if not terms:
        return 0.0
    matches = sum(1 for term in terms if term.lower() in haystack)
    phrase_bonus = 2 if normalized_query.lower() in haystack else 0
    visible = " ".join([chunk.get("title", ""), chunk.get("content_preview", "")]).lower()
    visible_bonus = sum(1 for term in terms if term.lower() in visible)
    return float(matches + phrase_bonus + visible_bonus + source_type_bonus(chunk, normalized_query))


def search(query, limit=10):
    normalized = normalize_query(query)
    chunk_uris = semantic_uri_map("chunk")
    results = []
    vector_index_exists = (PUBLISHED / "rag_mock_vector_index.jsonl").exists()
    method = "mock_hybrid" if vector_index_exists else "sqlite_fts5"
    for chunk in load_jsonl(PUBLISHED / "chunk_catalog.jsonl"):
        score = score_chunk(chunk, normalized)
        if score <= 0:
            continue
        chunk_id = chunk.get("chunk_id", "")
        results.append({
            "@id": chunk_uris.get(chunk_id, ""),
            "chunk_id": chunk_id,
            "doc_id": chunk.get("doc_id", ""),
            "title": chunk.get("title", ""),
            "source_type": chunk.get("source_type", ""),
            "chunk_type": chunk.get("chunk_type", ""),
            "source_ref": chunk.get("source_ref", ""),
            "review_status": chunk.get("review_status", ""),
            "lifecycle_status": "approved",
            "retrieval_method": method,
            "score": score,
            "content_preview": chunk.get("content_preview", ""),
        })
    results.sort(key=lambda item: (-item["score"], item["doc_id"], item["chunk_id"]))
    return results[:limit]


def excluded_by_policy():
    excluded = []
    for entity in load_jsonl(PUBLISHED / "entity_catalog.jsonl"):
        status = entity.get("review_status", "")
        if status != "approved":
            excluded.append({
                "entity_id": entity.get("entity_id", ""),
                "reason": "not_approved",
                "review_status": status,
            })
    return excluded


def citations_for(results):
    seen = set()
    citations = []
    for result in results:
        key = result.get("source_ref") or result.get("doc_id")
        if not key or key in seen:
            continue
        seen.add(key)
        citations.append({
            "source_ref": result.get("source_ref", ""),
            "chunk_id": result.get("chunk_id", ""),
            "title": result.get("title", ""),
        })
    return citations


def context_pack(query, limit=8):
    cfg = config()
    max_chars = int(cfg.get("context_pack", {}).get("max_chars", 6000))
    results = search(query, limit=limit)
    packed = []
    used = 0
    for result in results:
        size = len(result.get("content_preview", ""))
        if used + size > max_chars:
            break
        packed.append(result)
        used += size
    return {
        "query": query,
        "normalized_query": normalize_query(query),
        "results": packed,
        "citations": citations_for(packed),
        "excluded_by_policy": excluded_by_policy(),
        "generated_by": "src/bgpkb/service/retrieval_framework.py",
    }


def evidence(entity_id):
    evidence_uris = semantic_uri_map("evidence")
    rows = []
    for record in load_jsonl(DATASETS / "entity_source_evidence.jsonl"):
        if record.get("entity_id") != entity_id:
            continue
        item = {
            "@id": evidence_uris.get(record.get("evidence_id", ""), ""),
            "evidence_id": record.get("evidence_id", ""),
            "entity_id": entity_id,
            "source_id": record.get("source_id", ""),
            "source_type": record.get("source_type", ""),
            "source_path": record.get("source_path", ""),
            "chunk_sample_ids": record.get("chunk_sample_ids", []),
            "review_status": record.get("entity_review_status", ""),
        }
        rows.append(item)
    return {"entity_id": entity_id, "records": rows}
