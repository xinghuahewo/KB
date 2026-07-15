import hashlib

import pytest

from bgpkb.retrieval import hybrid_retrieval


def _candidate(chunk_id, score=1.0, content=None):
    return {
        "chunk_id": chunk_id,
        "doc_id": f"doc-{chunk_id}",
        "title": f"title-{chunk_id}",
        "content_preview": content or f"content for {chunk_id}",
        "rrf_score": score,
        "fusion_score": score,
        "score": score,
    }


class FakeReranker:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def rerank(self, query, documents, top_n, require_model=False):
        self.calls.append({
            "query": query,
            "documents": documents,
            "top_n": top_n,
            "require_model": require_model,
        })
        return {
            "ok": True,
            "provider": "local_http",
            "model": "BAAI/bge-reranker-v2-m3",
            "revision": "rev-reranker",
            "results": self.results,
            "latency_ms": 12.5,
        }


def test_validate_top_n_defaults_and_rejects_illegal_values():
    assert hybrid_retrieval.validate_top_n(None) == 5
    assert hybrid_retrieval.validate_top_n(5) == 5
    assert hybrid_retrieval.validate_top_n(8) == 8

    for value in (4, 9, "5", True):
        with pytest.raises(ValueError, match="top_n"):
            hybrid_retrieval.validate_top_n(value)


def test_rerank_candidates_limits_to_twenty_and_sorts_with_rrf_tie_break():
    candidates = [_candidate(f"chunk-{index:02}", score=1.0 / (index + 1)) for index in range(25)]
    reranker = FakeReranker([
        {"index": 4, "relevance_score": 0.8},
        {"index": 1, "relevance_score": 0.9},
        {"index": 0, "relevance_score": 0.9},
        {"index": 2, "relevance_score": 0.7},
        {"index": 3, "relevance_score": 0.6},
    ])

    payload = hybrid_retrieval.rerank_candidates(
        "route leak", candidates, top_n=5, reranker=reranker, require_model=True,
    )

    assert len(reranker.calls[0]["documents"]) == 20
    assert reranker.calls[0]["top_n"] == 5
    assert reranker.calls[0]["require_model"] is True
    assert [item["chunk_id"] for item in payload["results"]] == [
        "chunk-00", "chunk-01", "chunk-04", "chunk-02", "chunk-03",
    ]
    assert [item["rerank_rank"] for item in payload["results"]] == [1, 2, 3, 4, 5]
    assert payload["results"][0]["rerank_score"] == 0.9
    assert payload["rerank_status"] == "complete"
    assert payload["provider"] == "local_http"
    assert payload["model"] == "BAAI/bge-reranker-v2-m3"


def test_rerank_candidates_caps_model_top_n_to_available_candidates():
    candidates = [
        _candidate(f"chunk-{index:02}", score=1.0 / (index + 1))
        for index in range(6)
    ]
    reranker = FakeReranker([
        {"index": index, "relevance_score": 1.0 - index / 10}
        for index in range(6)
    ])

    payload = hybrid_retrieval.rerank_candidates(
        "route leak", candidates, top_n=8, reranker=reranker, require_model=True,
    )

    assert reranker.calls[0]["top_n"] == 6
    assert len(payload["results"]) == 6


def test_rerank_failure_degrades_to_rrf_unless_model_required():
    candidates = [_candidate("a", 0.9), _candidate("b", 0.8)]

    class FailedReranker:
        def rerank(self, query, documents, top_n, require_model=False):
            return {
                "ok": False,
                "provider": "provider_chain",
                "model": "BAAI/bge-reranker-v2-m3",
                "error": "local and api unavailable",
                "degraded_reason": "local_http: timeout; api: missing key",
            }

    degraded = hybrid_retrieval.rerank_candidates(
        "BGP", candidates, top_n=5, reranker=FailedReranker(), require_model=False,
    )

    assert degraded["rerank_status"] == "degraded_to_rrf"
    assert degraded["degraded"] is True
    assert degraded["degraded_reason"] == "local_http: timeout; api: missing key"
    assert [item["chunk_id"] for item in degraded["results"]] == ["a", "b"]
    assert all(item["rerank_score"] is None and item["rerank_rank"] is None for item in degraded["results"])

    with pytest.raises(hybrid_retrieval.RerankUnavailable):
        hybrid_retrieval.rerank_candidates(
            "BGP", candidates, top_n=5, reranker=FailedReranker(), require_model=True,
        )


def test_exact_duplicate_and_per_document_cap_are_diagnostic_while_cross_source_survives():
    def enriched(chunk_id, doc_id, source_ref, text, score):
        item = _candidate(chunk_id, score=score, content="display only")
        item.update({
            "doc_id": doc_id,
            "source_ref": source_ref,
            "retrieval_text": text,
            "retrieval_text_hash": "sha256:" + hashlib.sha256(text.encode()).hexdigest(),
            "retrieval_text_version": "retrieval_text_v1",
        })
        return item

    repeated = "title: repeated\ncontent: exact evidence"
    candidates = [
        enriched("a1", "doc-a", "source-a#1", repeated, 1.0),
        enriched("a2", "doc-a", "source-a#2", repeated, 0.9),
        enriched("a3", "doc-a", "source-a#3", "title: unique a3", 0.8),
        enriched("a4", "doc-a", "source-a#4", "title: unique a4", 0.7),
        enriched("b1", "doc-b", "source-b#1", repeated, 0.6),
        enriched("c1", "doc-c", "source-c#1", "title: unique c1", 0.5),
    ]

    class PassthroughReranker:
        def rerank(self, query, documents, top_n, require_model=False):
            return {
                "ok": True,
                "provider": "fake",
                "model": "BAAI/bge-reranker-v2-m3",
                "revision": "rev",
                "results": [
                    {"index": index, "relevance_score": 1.0 - index / 100}
                    for index in range(top_n)
                ],
            }

    payload = hybrid_retrieval.rerank_candidates(
        "route leak",
        candidates,
        top_n=5,
        reranker=PassthroughReranker(),
    )

    result_ids = [item["chunk_id"] for item in payload["results"]]
    assert "a1" in result_ids and "a2" not in result_ids
    assert "b1" in result_ids  # 相同文本但独立来源必须保留
    assert len([item for item in payload["results"] if item["doc_id"] == "doc-a"]) == 2
    assert {item["rule_id"] for item in payload["suppression_diagnostics"]} == {
        "exact_duplicate_same_source_v1",
        "per_document_candidate_cap_v1",
    }


def test_per_document_cap_is_applied_after_reranker_ordering():
    candidates = [
        {**_candidate("a1", 1.0), "doc_id": "doc-a"},
        {**_candidate("a2", 0.9), "doc_id": "doc-a"},
        {**_candidate("a3", 0.8), "doc_id": "doc-a"},
        {**_candidate("b1", 0.7), "doc_id": "doc-b"},
    ]

    reranker = FakeReranker([
        {"index": 2, "relevance_score": 0.99},
        {"index": 1, "relevance_score": 0.98},
        {"index": 3, "relevance_score": 0.97},
        {"index": 0, "relevance_score": 0.10},
    ])
    payload = hybrid_retrieval.rerank_candidates(
        "route leak", candidates, top_n=5, reranker=reranker,
    )

    assert [item["chunk_id"] for item in payload["results"]] == ["a3", "a2", "b1"]
    assert payload["suppression_diagnostics"] == [{
        "chunk_id": "a1",
        "kept_chunk_id": "",
        "doc_id": "doc-a",
        "rule_id": "per_document_candidate_cap_v1",
        "limit": 2,
    }]
