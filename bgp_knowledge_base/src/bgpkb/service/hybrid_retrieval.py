"""BGE-M3、关键词和元数据融合检索。"""

import math

from bgpkb import paths
from . import retrieval_framework
from .bge_m3_remote_client import BgeM3RemoteClient


BGE_INDEX_PATH = paths.PUBLISHED_DIR / "bge_m3_vector_index.jsonl"
MOCK_INDEX_PATH = paths.PUBLISHED_DIR / "rag_mock_vector_index.jsonl"
ENTITY_EVIDENCE_PATH = paths.DATASETS_DIR / "entity_source_evidence.jsonl"
SOURCE_CATALOG_PATH = paths.PUBLISHED_DIR / "source_catalog.jsonl"


def _trusted_chunk_ids():
    trusted = set()
    for item in retrieval_framework.load_jsonl(ENTITY_EVIDENCE_PATH):
        if item.get("entity_review_status") == "approved":
            trusted.update(item.get("chunk_sample_ids", []))
    return trusted


def _retrieval_eligible_doc_ids():
    eligible = set()
    for item in retrieval_framework.load_jsonl(SOURCE_CATALOG_PATH):
        if (
            item.get("processing_status") == "complete_deterministic"
            and item.get("trust_level") in {"high", "medium"}
        ):
            eligible.add(item.get("source_id", ""))
    return eligible


def _trust_basis(item, trusted_chunk_ids, eligible_doc_ids):
    if item.get("review_status") == "approved":
        return "approved_record"
    if item.get("trusted") is True or item.get("chunk_id") in trusted_chunk_ids:
        return "approved_entity_evidence"
    if item.get("doc_id") in eligible_doc_ids:
        return "processed_source_with_traceability"
    return ""


def _is_trusted(item, trusted_chunk_ids, eligible_doc_ids):
    return (
        bool(_trust_basis(item, trusted_chunk_ids, eligible_doc_ids))
    )


def _metadata_boost(item, query):
    intent = retrieval_framework.query_intent(query)
    source_type = item.get("source_type", "")
    if intent == "standard" and source_type == "standard":
        return 0.02
    if intent == "case" and source_type == "case_report":
        return 0.02
    if intent == "paper" and source_type == "paper":
        return 0.02
    if intent == "data" and source_type in {"data_doc", "tool_doc"}:
        return 0.02
    return 0.0


def rrf_fuse(query, lexical_results, vector_results, limit=20, rrf_k=60):
    fused = {}
    for method, results in (("lexical", lexical_results), ("vector", vector_results)):
        for rank, item in enumerate(results, start=1):
            key = item.get("chunk_id") or item.get("doc_id")
            if not key:
                continue
            current = fused.setdefault(key, dict(item))
            current.setdefault("lexical_score", 0.0)
            current.setdefault("vector_score", 0.0)
            current.setdefault("match_reasons", [])
            current.setdefault("rrf_score", 0.0)
            current["rrf_score"] += 1.0 / (rrf_k + rank)
            score_key = "lexical_score" if method == "lexical" else "vector_score"
            current[score_key] = max(float(current.get(score_key, 0.0)), float(item.get("score", 0.0)))
            if method not in current["match_reasons"]:
                current["match_reasons"].append(method)

    results = []
    for item in fused.values():
        boost = _metadata_boost(item, query)
        if boost:
            item["match_reasons"].append("metadata_intent")
        item["metadata_boost"] = boost
        item["fusion_score"] = item["rrf_score"] + boost
        item["score"] = item["fusion_score"]
        item["retrieval_method"] = "hybrid_rrf"
        item["match_reasons"].sort()
        results.append(item)
    results.sort(key=lambda item: (-item["fusion_score"], item.get("doc_id", ""), item.get("chunk_id", "")))
    return results[:limit]


def _lexical_search(query, limit, trusted_chunk_ids, eligible_doc_ids):
    normalized = retrieval_framework.normalize_query(query)
    uris = retrieval_framework.semantic_uri_map("chunk")
    results = []
    for chunk in retrieval_framework.load_jsonl(retrieval_framework.PUBLISHED / "chunk_catalog.jsonl"):
        chunk_id = chunk.get("chunk_id", "")
        if not _is_trusted(chunk, trusted_chunk_ids, eligible_doc_ids):
            continue
        score = retrieval_framework.score_chunk(chunk, normalized)
        if score <= 0:
            continue
        results.append({
            "@id": uris.get(chunk_id, ""),
            "doc_id": chunk.get("doc_id", ""),
            "chunk_id": chunk_id,
            "kind": "chunk",
            "title": chunk.get("title", ""),
            "source_ref": chunk.get("source_ref", ""),
            "source_type": chunk.get("source_type", ""),
            "review_status": chunk.get("review_status", ""),
            "lifecycle_status": "approved_evidence",
            "trusted": True,
            "trust_basis": _trust_basis(chunk, trusted_chunk_ids, eligible_doc_ids),
            "content_preview": chunk.get("content_preview", ""),
            "score": score,
        })
    results.sort(key=lambda item: (-item["score"], item["doc_id"], item["chunk_id"]))
    return results[:limit]


def cosine_similarity(left, right):
    if not left or len(left) != len(right):
        return 0.0
    denominator = math.sqrt(sum(value * value for value in left)) * math.sqrt(sum(value * value for value in right))
    if denominator == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / denominator


def _vector_item(record, score, trusted_chunk_ids, eligible_doc_ids):
    metadata = record.get("metadata", {})
    kind = record.get("kind", "chunk")
    raw_doc_id = record.get("doc_id", "")
    chunk_id = metadata.get("chunk_id") or record.get("chunk_id", "")
    if not chunk_id and kind == "chunk" and raw_doc_id.startswith("chunk:"):
        chunk_id = raw_doc_id.split(":", 1)[1]
    item = {
        "@id": record.get("@id", ""),
        "doc_id": metadata.get("doc_id") or raw_doc_id,
        "chunk_id": chunk_id or raw_doc_id,
        "kind": kind,
        "title": metadata.get("title") or raw_doc_id,
        "source_ref": record.get("source_ref") or metadata.get("source_ref", ""),
        "source_type": record.get("source_type") or metadata.get("source_type", kind),
        "review_status": record.get("review_status") or metadata.get("review_status", ""),
        "lifecycle_status": record.get("lifecycle_status", "candidate"),
        "trusted": record.get("trusted", False),
        "trust_basis": record.get("trust_basis", ""),
        "content_preview": metadata.get("content_preview") or record.get("text", ""),
        "score": score,
    }
    item["trust_basis"] = item["trust_basis"] or _trust_basis(item, trusted_chunk_ids, eligible_doc_ids)
    item["trusted"] = bool(item["trust_basis"])
    return item


def vector_search(
    query_vector,
    index_records,
    limit=50,
    trusted_chunk_ids=None,
    eligible_doc_ids=None,
    min_similarity=-1.0,
):
    trusted_chunk_ids = set(trusted_chunk_ids or [])
    eligible_doc_ids = set(eligible_doc_ids or [])
    results = []
    for record in index_records:
        score = cosine_similarity(query_vector, record.get("vector", []))
        if score < min_similarity:
            continue
        item = _vector_item(record, score, trusted_chunk_ids, eligible_doc_ids)
        if not item["trusted"]:
            continue
        results.append(item)
    results.sort(key=lambda item: (-item["score"], item["doc_id"], item["chunk_id"]))
    return results[:limit]


def _vector_results(query, normalized, limit, trusted_chunk_ids, eligible_doc_ids, client=None):
    if BGE_INDEX_PATH.exists():
        active_client = client or BgeM3RemoteClient.from_env("siliconflow_bge_m3")
        response = active_client.embed_texts([normalized])
        if not response.get("ok"):
            if response.get("error_code") in {"missing_api_key", "missing_endpoint"} and MOCK_INDEX_PATH.exists():
                records = retrieval_framework.load_jsonl(MOCK_INDEX_PATH)
                dimensions = len(records[0].get("vector", [])) if records else 32
                query_vector = retrieval_framework.stable_vector(normalized, dimensions=dimensions)
                return vector_search(
                    query_vector,
                    records,
                    limit,
                    trusted_chunk_ids,
                    eligible_doc_ids,
                ), "offline_mock"
            return [], response.get("error_code", "unavailable")
        records = retrieval_framework.load_jsonl(BGE_INDEX_PATH)
        threshold = float(
            retrieval_framework.config().get("hybrid_retrieval", {}).get("min_vector_similarity", 0.5)
        )
        return vector_search(
            response["vectors"][0],
            records,
            limit,
            trusted_chunk_ids,
            eligible_doc_ids,
            min_similarity=threshold,
        ), "complete"
    if MOCK_INDEX_PATH.exists():
        records = retrieval_framework.load_jsonl(MOCK_INDEX_PATH)
        dimensions = len(records[0].get("vector", [])) if records else 32
        query_vector = retrieval_framework.stable_vector(normalized, dimensions=dimensions)
        return vector_search(query_vector, records, limit, trusted_chunk_ids, eligible_doc_ids), "offline_mock"
    return [], "index_unavailable"


def search(query, limit=20, lexical_top_k=50, vector_top_k=50, rrf_k=60, vector_enabled=True, client=None):
    normalized = retrieval_framework.normalize_query(query)
    trusted_chunk_ids = _trusted_chunk_ids()
    eligible_doc_ids = _retrieval_eligible_doc_ids()
    lexical_results = _lexical_search(query, lexical_top_k, trusted_chunk_ids, eligible_doc_ids)
    if vector_enabled:
        vector_results, vector_status = _vector_results(
            query,
            normalized,
            vector_top_k,
            trusted_chunk_ids,
            eligible_doc_ids,
            client=client,
        )
        if vector_status == "offline_mock" and not lexical_results:
            vector_results = []
    else:
        vector_results, vector_status = [], "disabled"
    return {
        "query": query,
        "normalized_query": normalized,
        "results": rrf_fuse(normalized, lexical_results, vector_results, limit=limit, rrf_k=rrf_k),
        "lexical_count": len(lexical_results),
        "vector_count": len(vector_results),
        "vector_status": vector_status,
        "vector_min_similarity": (
            float(retrieval_framework.config().get("hybrid_retrieval", {}).get("min_vector_similarity", 0.5))
            if vector_status == "complete" else None
        ),
        "trusted_chunk_policy": "approved_entity_evidence_or_processed_source_with_traceability",
        "generated_by": "src/bgpkb/service/hybrid_retrieval.py",
    }


def context_pack(query, limit=8, client=None, vector_enabled=True):
    payload = search(query, limit=limit, client=client, vector_enabled=vector_enabled)
    payload["citations"] = retrieval_framework.citations_for(payload["results"])
    payload["excluded_by_policy"] = retrieval_framework.excluded_by_policy()
    return payload
