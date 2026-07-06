from bgpkb.service.retrieval_model_client import (
    EmbeddingProviderChain,
    RerankerProviderChain,
)


class Provider:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def embed_texts(self, texts):
        self.calls.append(texts)
        if self.error:
            raise self.error
        return dict(self.result)

    def rerank(self, query, documents, top_n):
        self.calls.append((query, documents, top_n))
        if self.error:
            raise self.error
        return dict(self.result)


def test_embedding_local_success_never_calls_api_and_keeps_metadata():
    local = Provider({
        "ok": True,
        "provider": "local",
        "model": "BAAI/bge-m3",
        "revision": "rev",
        "vectors": [[1.0]],
        "latency_ms": 3,
    })
    api = Provider(error=AssertionError("不应调用 API"))

    result = EmbeddingProviderChain(local=local, api=api).embed_texts(["BGP"])

    assert result["ok"] is True
    assert result["provider"] == "local"
    assert result["revision"] == "rev"
    assert result["latency_ms"] == 3
    assert api.calls == []


def test_embedding_timeout_falls_back_to_api_and_records_degradation():
    local = Provider(error=TimeoutError("local timeout"))
    api = Provider({
        "ok": True,
        "provider": "api",
        "model": "BAAI/bge-m3",
        "revision": "rev-api",
        "vectors": [[1.0]],
        "latency_ms": 8,
    })

    result = EmbeddingProviderChain(local=local, api=api).embed_texts(["BGP"])

    assert result["ok"] is True
    assert result["provider"] == "api"
    assert "local timeout" in result["degraded_reason"]


def test_embedding_double_failure_is_aggregated():
    local = Provider({"ok": False, "error": "local unavailable"})
    api = Provider(error=RuntimeError("api down"))

    result = EmbeddingProviderChain(local=local, api=api).embed_texts(["BGP"])

    assert result["ok"] is False
    assert "local unavailable" in result["error"]
    assert "api down" in result["error"]


def test_require_model_rejects_mock_but_accepts_real_api():
    mock = Provider({"ok": True, "provider": "mock", "is_mock": True, "vectors": [[0.0]]})
    real_api = Provider({"ok": True, "provider": "api", "model": "BAAI/bge-m3", "revision": "r", "vectors": [[1.0]]})

    result = EmbeddingProviderChain(local=mock, api=real_api).embed_texts(["BGP"], require_model=True)

    assert result["ok"] is True
    assert result["provider"] == "api"


def test_reranker_local_success_fallback_and_require_model_contract():
    local = Provider(error=TimeoutError("reranker timeout"))
    api = Provider({
        "ok": True,
        "provider": "api",
        "model": "BAAI/bge-reranker-v2-m3",
        "revision": "r",
        "results": [{"index": 0, "relevance_score": 0.9}],
        "latency_ms": 4,
    })

    result = RerankerProviderChain(local=local, api=api).rerank("q", ["d"] * 5, 5, require_model=True)

    assert result["ok"] is True
    assert result["provider"] == "api"
    assert result["model"] == "BAAI/bge-reranker-v2-m3"
    assert "reranker timeout" in result["degraded_reason"]
