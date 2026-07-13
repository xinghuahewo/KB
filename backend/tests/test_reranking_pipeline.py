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
