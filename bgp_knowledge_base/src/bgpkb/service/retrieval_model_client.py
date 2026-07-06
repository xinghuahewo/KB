"""可直接用于生产的本地优先 embedding 与 reranker provider chain。"""

import json
import os
import time
import urllib.error
import urllib.request

from bgpkb.service.bge_m3_remote_client import BgeM3RemoteClient


def _provider_name(provider, default):
    return getattr(provider, "provider", default)


def _attempt(provider, operation, args, default_name):
    name = _provider_name(provider, default_name)
    if provider is None:
        return None, {"provider": name, "ok": False, "error": "未配置", "latency_ms": 0}
    started = time.monotonic()
    try:
        result = getattr(provider, operation)(*args)
    except Exception as exc:
        return None, {
            "provider": name, "ok": False, "error": str(exc) or type(exc).__name__,
            "latency_ms": round((time.monotonic() - started) * 1000, 3),
        }
    attempt = {
        "provider": result.get("provider", name),
        "ok": bool(result.get("ok")),
        "model": result.get("model", getattr(provider, "model", "")),
        "revision": result.get("revision", ""),
        "latency_ms": result.get("latency_ms", round((time.monotonic() - started) * 1000, 3)),
    }
    if not result.get("ok"):
        attempt["error"] = result.get("error", result.get("error_code", "provider 失败"))
        return None, attempt
    return result, attempt


def _real_result(result, require_model):
    return not require_model or not result.get("is_mock", result.get("provider") == "mock")


def _failed_chain(attempts):
    reason = "; ".join(f"{item['provider']}: {item.get('error', 'mock 结果被拒绝')}" for item in attempts)
    return {
        "ok": False,
        "provider": "provider_chain",
        "model": next((item.get("model") for item in reversed(attempts) if item.get("model")), ""),
        "revision": "",
        "latency_ms": sum(item.get("latency_ms", 0) for item in attempts),
        "degraded": True,
        "degraded_reason": reason,
        "error": reason,
        "attempts": attempts,
    }


class EmbeddingProviderChain:
    def __init__(self, local=None, api=None):
        self.local = local
        self.api = api

    @classmethod
    def from_env(cls):
        return cls(EmbeddingHttpProvider.from_env(), BgeM3RemoteClient.from_env("generic"))

    def embed_texts(self, texts, require_model=False):
        local_result, local_attempt = _attempt(self.local, "embed_texts", (texts,), "local")
        if local_result and _real_result(local_result, require_model):
            local_result.setdefault("degraded", False)
            local_result.setdefault("degraded_reason", None)
            return local_result
        if local_result:
            local_attempt.update({"ok": False, "error": "本地 provider 返回 mock 结果"})
        api_result, api_attempt = _attempt(self.api, "embed_texts", (texts,), "api")
        if api_result and _real_result(api_result, require_model):
            api_result.update({
                "degraded": True,
                "degraded_reason": local_attempt.get("error", "本地 provider 不可用"),
                "attempts": [local_attempt, api_attempt],
            })
            return api_result
        if api_result:
            api_attempt.update({"ok": False, "error": "API provider 返回 mock 结果"})
        return _failed_chain([local_attempt, api_attempt])


class RerankerProviderChain:
    def __init__(self, local=None, api=None):
        self.local = local
        self.api = api

    @classmethod
    def from_env(cls):
        return cls(RerankerHttpProvider.from_env(), RerankerApiClient.from_env())

    def rerank(self, query, documents, top_n, require_model=False):
        args = (query, documents, top_n)
        local_result, local_attempt = _attempt(self.local, "rerank", args, "local")
        if local_result and _real_result(local_result, require_model):
            local_result.setdefault("degraded", False)
            local_result.setdefault("degraded_reason", None)
            return local_result
        if local_result:
            local_attempt.update({"ok": False, "error": "本地 provider 返回 mock 结果"})
        api_result, api_attempt = _attempt(self.api, "rerank", args, "api")
        if api_result and _real_result(api_result, require_model):
            api_result.update({
                "degraded": True,
                "degraded_reason": local_attempt.get("error", "本地 provider 不可用"),
                "attempts": [local_attempt, api_attempt],
            })
            return api_result
        if api_result:
            api_attempt.update({"ok": False, "error": "API provider 返回 mock 结果"})
        return _failed_chain([local_attempt, api_attempt])


class _HttpProvider:
    def __init__(self, endpoint, api_key, model, timeout, provider):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.provider = provider

    def _post(self, payload):
        if not self.endpoint:
            raise RuntimeError(f"未配置 {self.provider} endpoint")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


class EmbeddingHttpProvider(_HttpProvider):
    def __init__(self, endpoint, api_key="", model="BAAI/bge-m3", timeout=30, provider="local_http"):
        super().__init__(endpoint, api_key, model, timeout, provider)

    @classmethod
    def from_env(cls):
        return cls(
            os.environ.get("LOCAL_EMBEDDING_ENDPOINT", "http://10.99.8.28:8011/v1/embeddings"),
            os.environ.get("LOCAL_RETRIEVAL_API_KEY", ""),
            os.environ.get("LOCAL_EMBEDDING_MODEL", "BAAI/bge-m3"),
            int(os.environ.get("LOCAL_RETRIEVAL_TIMEOUT_SECONDS", "30")),
        )

    def embed_texts(self, texts):
        started = time.monotonic()
        try:
            body = self._post({"model": self.model, "input": texts})
            ordered = sorted(body.get("data", []), key=lambda item: item.get("index", 0))
            vectors = [item["embedding"] for item in ordered]
            if len(vectors) != len(texts):
                raise ValueError("embedding 响应数量不匹配")
        except Exception as exc:
            return self._error(exc, started)
        return {
            "ok": True, "provider": self.provider, "model": body.get("model", self.model),
            "revision": body.get("revision", ""), "vectors": vectors,
            "dimension": len(vectors[0]) if vectors else 0, "input_count": len(texts),
            "latency_ms": round((time.monotonic() - started) * 1000, 3),
        }

    def _error(self, exc, started):
        return {
            "ok": False, "provider": self.provider, "model": self.model, "revision": "",
            "latency_ms": round((time.monotonic() - started) * 1000, 3), "error": str(exc),
        }


class RerankerHttpProvider(_HttpProvider):
    def __init__(self, endpoint, api_key="", model="BAAI/bge-reranker-v2-m3", timeout=30, provider="local_http"):
        super().__init__(endpoint, api_key, model, timeout, provider)

    @classmethod
    def from_env(cls):
        return cls(
            os.environ.get("LOCAL_RERANK_ENDPOINT", "http://10.99.8.28:8012/v1/rerank"),
            os.environ.get("LOCAL_RETRIEVAL_API_KEY", ""),
            os.environ.get("LOCAL_RERANK_MODEL", "BAAI/bge-reranker-v2-m3"),
            int(os.environ.get("LOCAL_RETRIEVAL_TIMEOUT_SECONDS", "30")),
        )

    def rerank(self, query, documents, top_n):
        started = time.monotonic()
        try:
            body = self._post({"model": self.model, "query": query, "documents": documents, "top_n": top_n})
            results = body.get("results", [])
        except Exception as exc:
            return self._error(exc, started)
        return {
            "ok": True, "provider": self.provider, "model": body.get("model", self.model),
            "revision": body.get("revision", ""), "results": results,
            "latency_ms": round((time.monotonic() - started) * 1000, 3),
        }

    def _error(self, exc, started):
        return {
            "ok": False, "provider": self.provider, "model": self.model, "revision": "",
            "latency_ms": round((time.monotonic() - started) * 1000, 3), "error": str(exc),
        }


class RerankerApiClient(RerankerHttpProvider):
    def __init__(self, endpoint, api_key="", model="BAAI/bge-reranker-v2-m3", timeout=30):
        super().__init__(endpoint, api_key, model, timeout, provider="api")

    @classmethod
    def from_env(cls):
        return cls(
            os.environ.get("RERANK_API_ENDPOINT", ""),
            os.environ.get("RERANK_API_KEY", ""),
            os.environ.get("RERANK_API_MODEL", "BAAI/bge-reranker-v2-m3"),
            int(os.environ.get("RERANK_API_TIMEOUT_SECONDS", "30")),
        )
