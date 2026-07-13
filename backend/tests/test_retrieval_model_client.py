from bgpkb.infrastructure.retrieval_model_client import (
    EmbeddingHttpProvider,
    EmbeddingProviderChain,
    RerankerHttpProvider,
    RerankerProviderChain,
)
import json


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
    assert "超时" in result["degraded_reason"]
    assert result["degraded"] is True


def test_embedding_double_failure_is_aggregated():
    local = Provider({"ok": False, "error": "local unavailable"})
    api = Provider(error=RuntimeError("api down"))

    result = EmbeddingProviderChain(local=local, api=api).embed_texts(["BGP"])

    assert result["ok"] is False
    assert "local unavailable" in result["error"]
    assert "provider 调用失败" in result["error"]
    assert [attempt["provider"] for attempt in result["attempts"]] == ["local", "api"]


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
    assert "超时" in result["degraded_reason"]
    assert result["degraded"] is True


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def test_local_http_providers_call_service_without_required_auth(monkeypatch):
    requests = []

    def urlopen(request, timeout):
        requests.append(request)
        if request.full_url.endswith("embeddings"):
            return FakeResponse({
                "model": "BAAI/bge-m3", "revision": "er",
                "data": [{"index": 0, "embedding": [1.0, 2.0]}],
            })
        return FakeResponse({
            "model": "BAAI/bge-reranker-v2-m3", "revision": "rr",
            "results": [{"index": index, "relevance_score": 0.8 - index / 10} for index in range(5)],
        })

    monkeypatch.setattr("bgpkb.infrastructure.retrieval_model_client.urllib.request.urlopen", urlopen)
    embedding = EmbeddingHttpProvider("http://10.99.8.28:8011/v1/embeddings")
    reranker = RerankerHttpProvider("http://10.99.8.28:8012/v1/rerank")

    embedded = embedding.embed_texts(["BGP"])
    reranked = reranker.rerank("q", ["d"] * 5, 5)

    assert embedded["vectors"] == [[1.0, 2.0]] and embedded["revision"] == "er"
    assert reranked["results"][0]["relevance_score"] == 0.8 and reranked["revision"] == "rr"
    assert all("Authorization" not in request.headers for request in requests)


def test_default_chains_from_env_use_local_then_external_api(monkeypatch):
    monkeypatch.delenv("LOCAL_RETRIEVAL_API_KEY", raising=False)
    monkeypatch.setenv("LOCAL_EMBEDDING_ENDPOINT", "http://10.99.8.28:8011/v1/embeddings")
    monkeypatch.setenv("LOCAL_RERANK_ENDPOINT", "http://10.99.8.28:8012/v1/rerank")
    monkeypatch.setenv("EMBEDDING_API_ENDPOINT", "https://external.invalid/embeddings")
    monkeypatch.setenv("EMBEDDING_API_KEY", "external-key")
    monkeypatch.setenv("RERANK_API_ENDPOINT", "https://external.invalid/rerank")
    monkeypatch.setenv("RERANK_API_KEY", "external-key")

    embedding = EmbeddingProviderChain.from_env()
    reranker = RerankerProviderChain.from_env()

    assert embedding.local.endpoint.startswith("http://10.99.8.28:8011")
    assert embedding.local.api_key == ""
    assert embedding.api.base_url == "https://external.invalid/embeddings"
    assert reranker.local.endpoint.startswith("http://10.99.8.28:8012")
    assert reranker.api.endpoint == "https://external.invalid/rerank"


def test_malformed_local_embedding_200_falls_back_to_api(monkeypatch):
    responses = iter([
        {"model": "BAAI/bge-m3", "revision": "bad", "data": [
            {"index": 0, "embedding": [1.0, float("nan")]},
        ]},
        {"model": "BAAI/bge-m3", "revision": "good", "data": [
            {"index": 0, "embedding": [1.0, 0.0]},
        ]},
    ])
    monkeypatch.setattr(
        "bgpkb.infrastructure.retrieval_model_client.urllib.request.urlopen",
        lambda request, timeout: FakeResponse(next(responses)),
    )
    chain = EmbeddingProviderChain(
        EmbeddingHttpProvider("http://local/embeddings"),
        EmbeddingHttpProvider("https://api/embeddings", provider="api"),
    )

    result = chain.embed_texts(["BGP"])

    assert result["ok"] is True and result["provider"] == "api"
    assert result["degraded"] is True
    assert "finite" in result["degraded_reason"]


def test_both_malformed_rerank_200_responses_are_aggregated(monkeypatch):
    responses = iter([
        {"model": "BAAI/bge-reranker-v2-m3", "results": [
            {"index": 99, "relevance_score": 0.8},
        ] * 5},
        {"model": "BAAI/bge-reranker-v2-m3", "results": [
            {"index": 0, "relevance_score": True},
        ] * 5},
    ])
    monkeypatch.setattr(
        "bgpkb.infrastructure.retrieval_model_client.urllib.request.urlopen",
        lambda request, timeout: FakeResponse(next(responses)),
    )
    chain = RerankerProviderChain(
        RerankerHttpProvider("http://local/rerank"),
        RerankerHttpProvider("https://api/rerank", provider="api"),
    )

    result = chain.rerank("q", ["d"] * 5, 5)

    assert result["ok"] is False
    assert len(result["attempts"]) == 2
    assert all(attempt.get("error_code") == "invalid_response" for attempt in result["attempts"])


def test_provider_errors_redact_credentials_and_endpoint_query(monkeypatch):
    secret = "super-secret-token"
    endpoint = f"https://user:{secret}@example.invalid/embed?api_key={secret}"
    monkeypatch.setattr(
        "bgpkb.infrastructure.retrieval_model_client.urllib.request.urlopen",
        lambda request, timeout: (_ for _ in ()).throw(RuntimeError(f"failed {request.full_url} {secret}")),
    )
    chain = EmbeddingProviderChain(
        EmbeddingHttpProvider(endpoint, api_key=secret),
        EmbeddingHttpProvider(endpoint, api_key=secret, provider="api"),
    )

    result = chain.embed_texts(["BGP"])
    serialized = json.dumps(result)

    assert secret not in serialized
    assert "api_key" not in serialized
    assert result["attempts"][0]["error_code"] == "request_failed"
    assert result["attempts"][0]["endpoint"] == "https://example.invalid"
