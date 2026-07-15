"""BGE-M3、关键词和元数据融合检索。"""

from collections import Counter
import hashlib
import math
from pathlib import Path
import re
import time

from bgpkb import paths
from . import retrieval_framework
from bgpkb.infrastructure.bge_m3_remote_client import BgeM3RemoteClient
from .chunk_store import ChunkStore
from .context_assembler import ContextAssembler
from .query_type_resolver import resolve_query_type
from .retrieval_data import PublishedArtifactRetrievalData, RetrievalData
from bgpkb.infrastructure.retrieval_model_client import RerankerProviderChain
from bgpkb.indexing.retrieval_documents import verify_component_input_manifests
from .retrievers import Bm25Retriever, DenseRetriever, RetrievalChannelResult


def _published_path(filename: str) -> Path:
    return paths.require_runtime_data_dir() / "published" / filename


def _dataset_path(filename: str) -> Path:
    return paths.require_runtime_data_dir() / "derived" / "datasets" / filename


def _trusted_chunk_ids():
    trusted = set()
    for item in retrieval_framework.load_jsonl(_dataset_path("entity_source_evidence.jsonl")):
        if item.get("entity_review_status") == "approved":
            trusted.update(item.get("chunk_sample_ids", []))
    return trusted


def _retrieval_eligible_doc_ids():
    eligible = set()
    for item in retrieval_framework.load_jsonl(_published_path("source_catalog.jsonl")):
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
    for chunk in retrieval_framework.load_jsonl(retrieval_framework.published_dir() / "chunk_catalog.jsonl"):
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
    bge_index_path = _published_path("bge_m3_vector_index.jsonl")
    mock_index_path = _published_path("rag_mock_vector_index.jsonl")
    if bge_index_path.exists():
        active_client = client or BgeM3RemoteClient.from_env("siliconflow_bge_m3")
        response = active_client.embed_texts([normalized])
        if not response.get("ok"):
            if response.get("error_code") in {"missing_api_key", "missing_endpoint"} and mock_index_path.exists():
                records = retrieval_framework.load_jsonl(mock_index_path)
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
        records = retrieval_framework.load_jsonl(bge_index_path)
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
    if mock_index_path.exists():
        records = retrieval_framework.load_jsonl(mock_index_path)
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
    retrieval_text = item.get("retrieval_text")
    if retrieval_text is not None:
        if item.get("retrieval_text_version") != "retrieval_text_v1":
            raise ValueError("reranker 只接受当前 retrieval_text_v1")
        expected_hash = "sha256:" + hashlib.sha256(str(retrieval_text).encode("utf-8")).hexdigest()
        if item.get("retrieval_text_hash") != expected_hash:
            raise ValueError("reranker retrieval_text hash 非法")
        return str(retrieval_text)
    return "\n".join([
        str(item.get("title", "")),
        str(item.get("content", item.get("content_preview", ""))),
    ]).strip()


def _rrf_ranked(candidates):
    return sorted(
        [dict(item) for item in candidates],
        key=lambda item: (-float(item.get("rrf_score", item.get("fusion_score", item.get("score", 0.0)))), item.get("chunk_id", "")),
    )


def _source_identity(item):
    if item.get("doc_id"):
        return str(item["doc_id"])
    if item.get("source_id"):
        return str(item["source_id"])
    source_ref = str(item.get("source_ref", ""))
    return source_ref.split("#", 1)[0]


_SOURCE_ANCHOR_STOPWORDS = {
    "actions",
    "api",
    "archive",
    "bgp",
    "data",
    "doc",
    "docs",
    "framework",
    "global",
    "index",
    "outage",
    "paper",
    "raw",
    "review",
    "route",
    "routes",
    "routing",
    "source",
}


def _source_anchor_terms(item):
    identity = str(item.get("doc_id") or item.get("source_id") or "").casefold()
    return sorted({
        token
        for token in re.findall(r"[a-z0-9]+", identity)
        if (
            (len(token) >= 4 or token in {"ris"} or re.fullmatch(r"rfc\d+", token))
            and not token.isdigit()
            and token not in _SOURCE_ANCHOR_STOPWORDS
        )
    })


def _source_anchor(query, item):
    text = str(query).casefold()
    matched = [
        term
        for term in _source_anchor_terms(item)
        if re.search(
            rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])",
            text,
        )
    ]
    if not matched:
        return None
    return {
        "rule_id": "exact_named_source_preservation_v1",
        "matched_terms": matched,
    }


def suppress_retrieval_duplicates(
    candidates,
    *,
    per_document_limit=2,
    suppress_exact=True,
):
    kept = []
    diagnostics = []
    exact_seen = {}
    per_document_counts = {}
    for item in candidates:
        text_hash = item.get("retrieval_text_hash")
        exact_key = (text_hash, _source_identity(item)) if text_hash else None
        if suppress_exact and exact_key and exact_key in exact_seen:
            diagnostics.append({
                "chunk_id": item.get("chunk_id", ""),
                "kept_chunk_id": exact_seen[exact_key].get("chunk_id", ""),
                "doc_id": item.get("doc_id", ""),
                "rule_id": "exact_duplicate_same_source_v1",
                "retrieval_text_hash": text_hash,
            })
            continue
        doc_id = str(item.get("doc_id", ""))
        if (
            per_document_limit is not None
            and doc_id
            and per_document_counts.get(doc_id, 0) >= per_document_limit
        ):
            diagnostics.append({
                "chunk_id": item.get("chunk_id", ""),
                "kept_chunk_id": "",
                "doc_id": doc_id,
                "rule_id": "per_document_candidate_cap_v1",
                "limit": per_document_limit,
            })
            continue
        kept.append(item)
        if suppress_exact and exact_key:
            exact_seen[exact_key] = item
        if doc_id:
            per_document_counts[doc_id] = per_document_counts.get(doc_id, 0) + 1
    return kept, diagnostics


def rerank_candidates(
    query,
    candidates,
    top_n=None,
    reranker=None,
    require_model=False,
    component_manifest_hashes=None,
):
    requested_top_n = validate_top_n(top_n)
    pool, suppression_diagnostics = suppress_retrieval_duplicates(
        _rrf_ranked(candidates)[:20],
        per_document_limit=None,
    )
    reranker_input_manifest_hash = None
    if component_manifest_hashes is not None:
        reranker_input_manifest_hash = verify_component_input_manifests(component_manifest_hashes)
        candidate_hashes = {item.get("retrieval_input_manifest_hash") for item in pool}
        if candidate_hashes != {reranker_input_manifest_hash}:
            raise ValueError(
                "reranker 候选与当前 retrieval input manifest 不一致："
                f"candidates={sorted(str(item) for item in candidate_hashes)}"
            )
    if not pool:
        return {
            "results": [],
            "rerank_status": "empty",
            "requested_top_n": requested_top_n,
            "candidate_count": 0,
            "degraded": False,
            "degraded_reason": None,
            "reranker_input_manifest_hash": reranker_input_manifest_hash,
            "suppression_diagnostics": suppression_diagnostics,
        }
    documents = [_candidate_document(item) for item in pool]
    provider = reranker or RerankerProviderChain.from_env()
    response = provider.rerank(
        query,
        documents,
        min(requested_top_n, len(pool)),
        require_model=require_model,
    )
    if not response.get("ok"):
        if require_model:
            raise RerankUnavailable(response)
        fallback, fallback_diagnostics = suppress_retrieval_duplicates(
            pool,
            suppress_exact=False,
        )
        suppression_diagnostics.extend(fallback_diagnostics)
        fallback = fallback[:requested_top_n]
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
            "reranker_input_manifest_hash": reranker_input_manifest_hash,
            "suppression_diagnostics": suppression_diagnostics,
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
    indexed_by_chunk = {item.get("chunk_id"): item for item in indexed}
    anchored = []
    anchored_chunk_ids = set()
    for pool_item in pool:
        anchor = pool_item.get("source_anchor")
        if not isinstance(anchor, dict):
            continue
        chunk_id = pool_item.get("chunk_id")
        item = indexed_by_chunk.get(chunk_id, dict(pool_item))
        item["ranking_rule_id"] = anchor.get("rule_id")
        if chunk_id not in indexed_by_chunk:
            item["rerank_score"] = None
        anchored.append(item)
        anchored_chunk_ids.add(chunk_id)
    combined = [
        *anchored,
        *(item for item in indexed if item.get("chunk_id") not in anchored_chunk_ids),
    ]
    indexed, cap_diagnostics = suppress_retrieval_duplicates(
        combined,
        suppress_exact=False,
    )
    suppression_diagnostics.extend(cap_diagnostics)
    results = []
    for rank, item in enumerate(indexed[:requested_top_n], start=1):
        item.pop("_original_rrf_rank", None)
        item["rerank_rank"] = rank
        if item.get("rerank_score") is not None:
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
        "reranker_input_manifest_hash": reranker_input_manifest_hash,
        "suppression_diagnostics": suppression_diagnostics,
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


def _rrf_channel_results(lexical_result, vector_result, query="", limit=20, rrf_k=60):
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
    if query:
        for item in items:
            anchor = _source_anchor(query, item)
            if anchor:
                item["source_anchor"] = anchor
        items = [
            *[item for item in items if item.get("source_anchor")],
            *[item for item in items if not item.get("source_anchor")],
        ]
    selected = []
    deferred = []
    source_counts = Counter()
    for item in items:
        source_id = _source_identity(item) or str(item.get("chunk_id", ""))
        if source_counts[source_id] >= 1:
            deferred.append(item)
            continue
        selected.append(item)
        source_counts[source_id] += 1
        if len(selected) >= limit:
            break
    if len(selected) < limit:
        for item in deferred:
            source_id = _source_identity(item) or str(item.get("chunk_id", ""))
            if source_counts[source_id] >= 2:
                continue
            selected.append(item)
            source_counts[source_id] += 1
            if len(selected) >= limit:
                break
    return selected


def _governance_diagnostics(results):
    eligibility_counts = Counter()
    policy_versions = set()
    missing_governance_count = 0
    for item in results:
        governance = item.get("governance")
        eligibility = item.get("eligibility")
        if not isinstance(governance, dict):
            missing_governance_count += 1
            continue
        if not isinstance(eligibility, dict):
            eligibility = governance.get("retrieval_eligibility")
        if isinstance(eligibility, dict):
            status = eligibility.get("status")
            if status:
                eligibility_counts[str(status)] += 1
            policy_version = eligibility.get("policy_version")
            if policy_version:
                policy_versions.add(str(policy_version))
    return {
        "state_dimensions": [
            "parse_status",
            "content_quality_status",
            "source_trust_status",
            "semantic_review_status",
            "retrieval_eligibility",
        ],
        "retrieval_eligibility_counts": dict(sorted(eligibility_counts.items())),
        "policy_versions": sorted(policy_versions),
        "missing_governance_count": missing_governance_count,
    }


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
    trusted_chunk_ids=None,
    eligible_doc_ids=None,
    retrieval_data: RetrievalData | None = None,
):
    started = time.perf_counter()
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError("limit 必须是 1 到 20 的整数")
    if (lexical_top_k, vector_top_k, rrf_k) != (50, 50, 60):
        raise ValueError("v2 召回契约固定为 lexical=50、vector=50、rrf_k=60")
    normalized = retrieval_framework.normalize_query(query)
    active_data = retrieval_data
    if (
        trusted_chunk_ids is None
        or eligible_doc_ids is None
        or lexical_retriever is None
        or (vector_enabled and dense_retriever is None)
    ):
        active_data = active_data or PublishedArtifactRetrievalData.from_environment()
    trusted_chunk_ids = (
        active_data.trusted_chunk_ids() if trusted_chunk_ids is None else set(trusted_chunk_ids)
    )
    eligible_doc_ids = (
        active_data.eligible_doc_ids() if eligible_doc_ids is None else set(eligible_doc_ids)
    )
    lexical_started = time.perf_counter()
    lexical = (lexical_retriever or Bm25Retriever(retrieval_data=active_data)).search(normalized, 50)
    lexical.metadata.setdefault("latency_ms", round((time.perf_counter() - lexical_started) * 1000, 3))
    for item in lexical.items:
        item["trust_basis"] = item.get("trust_basis") or _trust_basis(item, trusted_chunk_ids, eligible_doc_ids)
        item["trusted"] = bool(item["trust_basis"])
        item.setdefault("lifecycle_status", "approved_evidence" if item["trusted"] else "candidate")
    if vector_enabled:
        vector_started = time.perf_counter()
        vector = (
            dense_retriever or DenseRetriever(retrieval_data=active_data, provider=client)
        ).search(normalized, 50)
        vector.metadata.setdefault("latency_ms", round((time.perf_counter() - vector_started) * 1000, 3))
        for item in vector.items:
            item["trust_basis"] = item.get("trust_basis") or _trust_basis(item, trusted_chunk_ids, eligible_doc_ids)
            item["trusted"] = bool(item["trust_basis"])
    else:
        vector = RetrievalChannelResult("vector", metadata={"disabled": True})
    channel_results = {"lexical": lexical, "vector": vector}
    channel_errors = {
        channel: result.error for channel, result in channel_results.items() if result.error is not None
    }
    degraded_channels = {
        channel: result.metadata.get("degraded_reason") or f"{channel}_degraded"
        for channel, result in channel_results.items()
        if result.metadata.get("degraded")
    }
    technical_channels = [result for result in channel_results.values() if not result.metadata.get("disabled")]
    if technical_channels and all(result.error is not None for result in technical_channels):
        raise RetrievalUnavailable(channel_errors)
    results = _rrf_channel_results(
        lexical,
        vector,
        query=normalized,
        limit=limit,
        rrf_k=60,
    )
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
        "degraded": bool(channel_errors or degraded_channels),
        "degraded_reason": next(iter(degraded_channels.values()), None),
        "channel_errors": channel_errors,
        "channel_status": channel_status,
        "channel_metadata": {channel: result.metadata for channel, result in channel_results.items()},
        "retrieval_latency_ms": round((time.perf_counter() - started) * 1000, 3),
        "retrieval_contract": {"lexical_top_k": 50, "vector_top_k": 50, "rrf_k": 60, "fused_top_k": 20},
        "governance_diagnostics": _governance_diagnostics(results),
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


def _default_section_catalog_path(retrieval_data: RetrievalData):
    return retrieval_data.section_catalog_path()


_CONTEXT_STORE_CACHE = {}


def clear_context_store_cache():
    _CONTEXT_STORE_CACHE.clear()


def _catalog_signature(path):
    resolved = Path(path).resolve()
    if not resolved.exists():
        return (str(resolved), -1, -1)
    stat = resolved.stat()
    return (str(resolved), stat.st_size, stat.st_mtime_ns)


def _default_context_store(section_path, retrieval_data: RetrievalData):
    chunk_catalog_path = retrieval_data.chunk_catalog_path()
    data_dir = chunk_catalog_path.parents[1]
    key = (
        str(data_dir.parent.resolve()),
        _catalog_signature(chunk_catalog_path),
        _catalog_signature(section_path),
    )
    cached = _CONTEXT_STORE_CACHE.get(key)
    if cached is None:
        cached = ChunkStore(data_dir.parent, chunk_catalog_path, section_path)
        _CONTEXT_STORE_CACHE.clear()
        _CONTEXT_STORE_CACHE[key] = cached
    return cached


def _build_context_units(
    query, results, resolved_query_type, token_budget, store=None, retrieval_data: RetrievalData | None = None
):
    if store is None:
        active_data = retrieval_data or PublishedArtifactRetrievalData.from_environment()
        section_path = _default_section_catalog_path(active_data)
        store = _default_context_store(section_path, active_data)
    assembler = ContextAssembler(store)
    try:
        pack = assembler.build(query, results, resolved_query_type, token_budget)
    except Exception as exc:
        return [], [{"event": "context_assembly_failed", "reason": str(exc)}]
    return pack["context_units"], pack["trim_events"]


def _build_structured_context(
    query, results, resolved_query_type, token_budget, store=None, retrieval_data: RetrievalData | None = None
):
    if not results:
        return {
            "context_units": [],
            "evidence": [],
            "context_groups": [],
            "trim_events": [],
        }
    if store is None:
        active_data = retrieval_data or PublishedArtifactRetrievalData.from_environment()
        section_path = _default_section_catalog_path(active_data)
        store = _default_context_store(section_path, active_data)
    assembler = ContextAssembler(store)
    try:
        return assembler.build(query, results, resolved_query_type, token_budget)
    except Exception as exc:
        return {
            "context_units": [],
            "evidence": [],
            "context_groups": [],
            "trim_events": [{"event": "context_assembly_failed", "reason": str(exc)}],
        }


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
    trusted_chunk_ids=None,
    eligible_doc_ids=None,
    retrieval_data: RetrievalData | None = None,
    progress=None,
):
    active_data = retrieval_data or PublishedArtifactRetrievalData.from_environment()
    alias_top_n, deprecated = _legacy_limit_to_top_n(limit)
    effective_top_n = validate_top_n(top_n if top_n is not None else alias_top_n)
    recall = search(
        query,
        limit=20,
        client=client,
        vector_enabled=vector_enabled,
        lexical_retriever=lexical_retriever,
        dense_retriever=dense_retriever,
        trusted_chunk_ids=trusted_chunk_ids,
        eligible_doc_ids=eligible_doc_ids,
        retrieval_data=active_data,
    )
    query_scope = retrieval_framework.assess_query_scope(query)
    recall["query_scope"] = query_scope
    if query_scope["status"] == "unsupported":
        recall["results"] = []
    if progress is not None:
        vector_metadata = recall.get("channel_metadata", {}).get("vector", {})
        progress({
            "stage": "retrieval",
            "status": "complete",
            "message": "候选证据召回完成",
            "candidate_count": len(recall.get("results", [])),
            "lexical_count": recall.get("lexical_count", 0),
            "vector_count": recall.get("vector_count", 0),
            "vector_status": recall.get("vector_status", "unknown"),
            "vector_index_mode": vector_metadata.get("index_mode"),
            "retrieval_latency_ms": recall.get("retrieval_latency_ms"),
            "vector_latency_ms": vector_metadata.get("latency_ms"),
            "degraded": bool(recall.get("degraded", False)),
        })
    lexical_manifest_hash = recall.get("channel_metadata", {}).get("lexical", {}).get(
        "retrieval_input_manifest_hash"
    )
    embedding_manifest_hash = recall.get("channel_metadata", {}).get("vector", {}).get(
        "retrieval_input_manifest_hash"
    )
    candidate_manifest_hashes = {
        item.get("retrieval_input_manifest_hash")
        for item in recall.get("results", [])
        if item.get("retrieval_input_manifest_hash")
    }
    component_manifest_hashes = None
    if lexical_manifest_hash or embedding_manifest_hash or candidate_manifest_hashes:
        if not lexical_manifest_hash or not embedding_manifest_hash:
            raise ValueError(
                "FTS/embedding/reranker retrieval input manifest 不完整："
                f"fts={lexical_manifest_hash}, embedding={embedding_manifest_hash}, "
                f"reranker={sorted(candidate_manifest_hashes)}"
            )
        if recall.get("results"):
            if len(candidate_manifest_hashes) != 1:
                raise ValueError(
                    "FTS/embedding/reranker retrieval input manifest 不完整："
                    f"fts={lexical_manifest_hash}, embedding={embedding_manifest_hash}, "
                    f"reranker={sorted(candidate_manifest_hashes)}"
                )
            component_manifest_hashes = {
                "fts": lexical_manifest_hash,
                "embedding": embedding_manifest_hash,
                "reranker": next(iter(candidate_manifest_hashes)),
            }
        elif lexical_manifest_hash != embedding_manifest_hash:
            raise ValueError(
                "空候选的 FTS/embedding retrieval input manifest 不一致："
                f"fts={lexical_manifest_hash}, embedding={embedding_manifest_hash}"
            )
    reranked = rerank_candidates(
        recall.get("normalized_query", query),
        recall["results"],
        top_n=effective_top_n,
        reranker=reranker or (_OfflineRerankerFallback() if not require_model else None),
        require_model=require_model,
        component_manifest_hashes=component_manifest_hashes,
    )
    if progress is not None:
        progress({
            "stage": "rerank",
            "status": reranked["rerank_status"],
            "message": "证据精排完成" if reranked["rerank_status"] == "complete" else "证据精排已降级",
            "candidate_count": reranked.get("candidate_count", 0),
            "result_count": len(reranked.get("results", [])),
            "provider": reranked.get("provider", ""),
            "latency_ms": reranked.get("latency_ms"),
            "degraded": bool(reranked.get("degraded", False)),
        })
    if query_scope["status"] == "unsupported":
        query_type_payload = {
            "requested_query_type": query_type,
            "resolved_query_type": "fact",
            "provider": "query_scope_policy",
            "model": "",
            "prompt_version": "query_scope_v1",
            "reason": query_scope["reason"],
            "degraded": False,
            "degraded_reason": None,
        }
    else:
        query_type_payload = resolve_query_type(query, query_type, client=query_type_client)
    context_started = time.perf_counter()
    structured_context = _build_structured_context(
        query,
        reranked["results"],
        query_type_payload["resolved_query_type"],
        token_budget,
        store=store,
        retrieval_data=active_data,
    )
    context_units = structured_context["context_units"]
    evidence = structured_context["evidence"]
    context_groups = structured_context["context_groups"]
    trim_events = structured_context["trim_events"]
    context_assembly_latency_ms = round((time.perf_counter() - context_started) * 1000, 3)
    citations = _citations_from_units(context_units) or retrieval_framework.citations_for(reranked["results"])
    payload = {
        **recall,
        "schema_version": "context_pack_v2",
        "results": reranked["results"],
        "citations": citations,
        "excluded_by_policy": active_data.excluded_by_policy(),
        "requested_query_type": query_type_payload["requested_query_type"],
        "resolved_query_type": query_type_payload["resolved_query_type"],
        "query_type_resolution": query_type_payload,
        "token_budget": token_budget,
        "context_units": context_units,
        "evidence": evidence,
        "context_groups": context_groups,
        "trim_events": trim_events,
        "provider": reranked.get("provider"),
        "model": reranked.get("model"),
        "revision": reranked.get("revision"),
        "degraded": bool(recall.get("degraded") or reranked.get("degraded") or query_type_payload.get("degraded")),
        "degraded_reason": reranked.get("degraded_reason") or query_type_payload.get("degraded_reason"),
        "rerank_status": reranked["rerank_status"],
        "reranked_chunk_count": len(reranked["results"]),
        "candidate_chunk_count": len(recall["results"]),
        "context_assembly_latency_ms": context_assembly_latency_ms,
        "deprecated_parameters": deprecated,
    }
    return payload
