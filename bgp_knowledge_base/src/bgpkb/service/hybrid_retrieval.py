"""BGE-M3、关键词和元数据融合检索。"""

import math
from pathlib import Path

from bgpkb import paths
from . import retrieval_framework
from .bge_m3_remote_client import BgeM3RemoteClient
from .chunk_store import ChunkStore
from .context_assembler import ContextAssembler
from .query_type_resolver import resolve_query_type
from .retrieval_model_client import RerankerProviderChain
from .retrievers import Bm25Retriever, DenseRetriever, RetrievalChannelResult


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


class RetrievalUnavailable(RuntimeError):
    """所有召回通道都发生技术故障。"""

    def __init__(self, channel_errors):
        super().__init__(f"混合召回不可用：{channel_errors}")
        self.channel_errors = channel_errors


class RerankUnavailable(RuntimeError):
    """精排模型在 require_model=true 时不可用。"""

    def __init__(self, error):
        super().__init__(f"Reranker 不可用：{error}")
        self.error = error


def validate_top_n(top_n=None):
    if top_n is None:
        return 5
    if isinstance(top_n, bool) or not isinstance(top_n, int) or not 5 <= top_n <= 8:
        raise ValueError("top_n 必须是 5 到 8 的整数")
    return top_n


def _candidate_document(item):
    return "\n".join([
        str(item.get("title", "")),
        str(item.get("content", item.get("content_preview", ""))),
    ]).strip()


def _rrf_ranked(candidates):
    return sorted(
        [dict(item) for item in candidates],
        key=lambda item: (-float(item.get("rrf_score", item.get("fusion_score", item.get("score", 0.0)))), item.get("chunk_id", "")),
    )


def rerank_candidates(query, candidates, top_n=None, reranker=None, require_model=False):
    requested_top_n = validate_top_n(top_n)
    pool = _rrf_ranked(candidates)[:20]
    if not pool:
        return {
            "results": [],
            "rerank_status": "empty",
            "requested_top_n": requested_top_n,
            "candidate_count": 0,
            "degraded": False,
            "degraded_reason": None,
        }
    effective_top_n = min(requested_top_n, len(pool))
    documents = [_candidate_document(item) for item in pool]
    provider = reranker or RerankerProviderChain.from_env()
    response = provider.rerank(query, documents, effective_top_n, require_model=require_model)
    if not response.get("ok"):
        if require_model:
            raise RerankUnavailable(response)
        fallback = pool[:requested_top_n]
        for item in fallback:
            item["rerank_score"] = None
            item["rerank_rank"] = None
        return {
            "results": fallback,
            "rerank_status": "degraded_to_rrf",
            "requested_top_n": requested_top_n,
            "candidate_count": len(pool),
            "provider": response.get("provider", "provider_chain"),
            "model": response.get("model", ""),
            "revision": response.get("revision", ""),
            "degraded": True,
            "degraded_reason": response.get("degraded_reason") or response.get("error") or "reranker_unavailable",
            "attempts": response.get("attempts", []),
        }

    indexed = []
    for result in response.get("results", []):
        index = result.get("index")
        score = result.get("relevance_score")
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(pool):
            if require_model:
                raise RerankUnavailable({"error": "reranker 返回 index 越界"})
            continue
        item = dict(pool[index])
        item["_original_rrf_rank"] = index + 1
        item["rerank_score"] = float(score)
        indexed.append(item)
    indexed.sort(key=lambda item: (-item["rerank_score"], item["_original_rrf_rank"], item.get("chunk_id", "")))
    results = []
    for rank, item in enumerate(indexed[:requested_top_n], start=1):
        item.pop("_original_rrf_rank", None)
        item["rerank_rank"] = rank
        item["score"] = item["rerank_score"]
        results.append(item)
    return {
        "results": results,
        "rerank_status": "complete",
        "requested_top_n": requested_top_n,
        "candidate_count": len(pool),
        "provider": response.get("provider", ""),
        "model": response.get("model", ""),
        "revision": response.get("revision", ""),
        "latency_ms": response.get("latency_ms"),
        "degraded": bool(response.get("degraded", False)),
        "degraded_reason": response.get("degraded_reason"),
        "attempts": response.get("attempts", []),
    }


def _best_channel_items(result):
    best = {}
    for position, item in enumerate(result.items[:50], start=1):
        chunk_id = item.get("chunk_id")
        if not chunk_id:
            continue
        rank = item.get("raw_rank", position)
        if isinstance(rank, bool) or not isinstance(rank, int) or rank < 1:
            rank = position
        candidate = dict(item)
        candidate["raw_rank"] = rank
        previous = best.get(chunk_id)
        if previous is None or (rank, chunk_id) < (previous["raw_rank"], chunk_id):
            best[chunk_id] = candidate
    return best


def _rrf_channel_results(lexical_result, vector_result, limit=20, rrf_k=60):
    fused = {}
    for result in (lexical_result, vector_result):
        for chunk_id, item in _best_channel_items(result).items():
            current = fused.setdefault(chunk_id, dict(item))
            rank = item["raw_rank"]
            raw_score = float(item.get("raw_score", item.get("score", 0.0)))
            current[f"{result.channel}_raw_rank"] = rank
            current[f"{result.channel}_raw_score"] = raw_score
            current.setdefault("match_channels", []).append(result.channel)
            current["rrf_score"] = current.get("rrf_score", 0.0) + 1.0 / (rrf_k + rank)
            for key, value in item.items():
                current.setdefault(key, value)
    items = list(fused.values())
    for item in items:
        item["match_channels"] = sorted(set(item["match_channels"]))
        item["score"] = item["rrf_score"]
        item["fusion_score"] = item["rrf_score"]
        item["retrieval_method"] = "hybrid_rrf"
    items.sort(key=lambda item: (-item["rrf_score"], item["chunk_id"]))
    return items[:limit]


def search(
    query,
    limit=20,
    lexical_top_k=50,
    vector_top_k=50,
    rrf_k=60,
    vector_enabled=True,
    client=None,
    lexical_retriever=None,
    dense_retriever=None,
):
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError("limit 必须是 1 到 20 的整数")
    if (lexical_top_k, vector_top_k, rrf_k) != (50, 50, 60):
        raise ValueError("v2 召回契约固定为 lexical=50、vector=50、rrf_k=60")
    normalized = retrieval_framework.normalize_query(query)
    trusted_chunk_ids = _trusted_chunk_ids()
    eligible_doc_ids = _retrieval_eligible_doc_ids()
    lexical = (lexical_retriever or Bm25Retriever()).search(normalized, 50)
    for item in lexical.items:
        item["trust_basis"] = item.get("trust_basis") or _trust_basis(item, trusted_chunk_ids, eligible_doc_ids)
        item["trusted"] = bool(item["trust_basis"])
        item.setdefault("lifecycle_status", "approved_evidence" if item["trusted"] else "candidate")
    if vector_enabled:
        vector = (dense_retriever or DenseRetriever(provider=client)).search(normalized, 50)
        for item in vector.items:
            item["trust_basis"] = item.get("trust_basis") or _trust_basis(item, trusted_chunk_ids, eligible_doc_ids)
            item["trusted"] = bool(item["trust_basis"])
    else:
        vector = RetrievalChannelResult("vector", metadata={"disabled": True})
    channel_results = {"lexical": lexical, "vector": vector}
    channel_errors = {
        channel: result.error for channel, result in channel_results.items() if result.error is not None
    }
    technical_channels = [result for result in channel_results.values() if not result.metadata.get("disabled")]
    if technical_channels and all(result.error is not None for result in technical_channels):
        raise RetrievalUnavailable(channel_errors)
    results = _rrf_channel_results(lexical, vector, limit=limit, rrf_k=60)
    channel_status = {
        channel: (
            "disabled" if result.metadata.get("disabled") else
            "failed" if result.error else
            "complete" if result.items else "empty"
        )
        for channel, result in channel_results.items()
    }
    return {
        "query": query,
        "normalized_query": normalized,
        "results": results,
        "lexical_count": len(lexical.items),
        "vector_count": len(vector.items),
        "vector_status": channel_status["vector"],
        "vector_min_similarity": None,
        "degraded": bool(channel_errors),
        "channel_errors": channel_errors,
        "channel_status": channel_status,
        "channel_metadata": {channel: result.metadata for channel, result in channel_results.items()},
        "retrieval_contract": {"lexical_top_k": 50, "vector_top_k": 50, "rrf_k": 60, "fused_top_k": 20},
        "trusted_chunk_policy": "approved_entity_evidence_or_processed_source_with_traceability",
        "generated_by": "src/bgpkb/service/hybrid_retrieval.py",
    }


class _OfflineRerankerFallback:
    def rerank(self, query, documents, top_n, require_model=False):
        return {
            "ok": False,
            "provider": "offline_fallback",
            "model": "BAAI/bge-reranker-v2-m3",
            "error": "离线默认路径不调用真实 reranker；保留 RRF 顺序",
            "degraded_reason": "reranker_offline_fallback",
        }


def _legacy_limit_to_top_n(limit):
    if limit is None:
        return None, {}
    return min(8, max(5, int(limit))), {"limit": "use top_n"}


def _default_section_catalog_path():
    candidates = [
        paths.DATASETS_DIR / "section_catalog.jsonl",
        paths.PUBLISHED_DIR / "section_catalog.jsonl",
    ]
    return next((path for path in candidates if path.exists()), candidates[0])


def _build_context_units(query, results, resolved_query_type, token_budget, store=None):
    section_path = _default_section_catalog_path()
    if store is None:
        if not section_path.exists():
            return [], [{"event": "context_assembly_skipped", "reason": "section_catalog_missing"}]
        store = ChunkStore(paths.PROJECT_ROOT, paths.PUBLISHED_DIR / "chunk_catalog.jsonl", section_path)
    assembler = ContextAssembler(store)
    try:
        pack = assembler.build(query, results, resolved_query_type, token_budget)
    except Exception as exc:
        return [], [{"event": "context_assembly_failed", "reason": str(exc)}]
    return pack["context_units"], pack["trim_events"]


def _citations_from_units(context_units):
    citations = []
    seen = set()
    for unit in context_units:
        for citation in unit.get("citations", []):
            key = (citation.get("chunk_id"), citation.get("source_ref"))
            if key not in seen:
                seen.add(key)
                citations.append(citation)
    return citations


def context_pack(
    query,
    limit=None,
    client=None,
    vector_enabled=True,
    top_n=None,
    query_type="auto",
    token_budget=6000,
    require_model=False,
    reranker=None,
    query_type_client=None,
    store=None,
    lexical_retriever=None,
    dense_retriever=None,
):
    alias_top_n, deprecated = _legacy_limit_to_top_n(limit)
    effective_top_n = validate_top_n(top_n if top_n is not None else alias_top_n)
    recall = search(
        query,
        limit=20,
        client=client,
        vector_enabled=vector_enabled,
        lexical_retriever=lexical_retriever,
        dense_retriever=dense_retriever,
    )
    reranked = rerank_candidates(
        query,
        recall["results"],
        top_n=effective_top_n,
        reranker=reranker or (_OfflineRerankerFallback() if not require_model else None),
        require_model=require_model,
    )
    query_type_payload = resolve_query_type(query, query_type, client=query_type_client)
    context_units, trim_events = _build_context_units(
        query, reranked["results"], query_type_payload["resolved_query_type"], token_budget, store=store,
    )
    citations = _citations_from_units(context_units) or retrieval_framework.citations_for(reranked["results"])
    payload = {
        **recall,
        "schema_version": "context_pack_v2",
        "results": reranked["results"],
        "citations": citations,
        "excluded_by_policy": retrieval_framework.excluded_by_policy(),
        "requested_query_type": query_type_payload["requested_query_type"],
        "resolved_query_type": query_type_payload["resolved_query_type"],
        "query_type_resolution": query_type_payload,
        "token_budget": token_budget,
        "context_units": context_units,
        "trim_events": trim_events,
        "provider": reranked.get("provider"),
        "model": reranked.get("model"),
        "degraded": bool(recall.get("degraded") or reranked.get("degraded") or query_type_payload.get("degraded")),
        "degraded_reason": reranked.get("degraded_reason") or query_type_payload.get("degraded_reason"),
        "rerank_status": reranked["rerank_status"],
        "reranked_chunk_count": len(reranked["results"]),
        "candidate_chunk_count": len(recall["results"]),
        "deprecated_parameters": deprecated,
    }
    return payload
