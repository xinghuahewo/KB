"""本地优先的 embedding 与 reranker provider chain。"""

import json
import os
import time
import urllib.error
import urllib.request


def _failure(provider, operation, args):
    if provider is None:
        return None, "未配置"
    try:
        result = getattr(provider, operation)(*args)
    except Exception as exc:
        return None, str(exc) or type(exc).__name__
    if not result.get("ok"):
        return None, result.get("error", result.get("error_code", "provider 失败"))
    return result, None


def _real_result(result, require_model):
    return not require_model or not result.get("is_mock", result.get("provider") == "mock")


class EmbeddingProviderChain:
    def __init__(self, local=None, api=None):
        self.local = local
        self.api = api

    def embed_texts(self, texts, require_model=False):
        local_result, local_error = _failure(self.local, "embed_texts", (texts,))
        if local_result and _real_result(local_result, require_model):
            return local_result
        if local_result:
            local_error = "本地 provider 返回 mock 结果"
        api_result, api_error = _failure(self.api, "embed_texts", (texts,))
        if api_result and _real_result(api_result, require_model):
            api_result["degraded_reason"] = local_error
            return api_result
        if api_result:
            api_error = "API provider 返回 mock 结果"
        return {"ok": False, "error": f"本地失败: {local_error}; API 失败: {api_error}"}


class RerankerProviderChain:
    def __init__(self, local=None, api=None):
        self.local = local
        self.api = api

    def rerank(self, query, documents, top_n, require_model=False):
        args = (query, documents, top_n)
        local_result, local_error = _failure(self.local, "rerank", args)
        if local_result and _real_result(local_result, require_model):
            return local_result
        if local_result:
            local_error = "本地 provider 返回 mock 结果"
        api_result, api_error = _failure(self.api, "rerank", args)
        if api_result and _real_result(api_result, require_model):
            api_result["degraded_reason"] = local_error
            return api_result
        if api_result:
            api_error = "API provider 返回 mock 结果"
        return {"ok": False, "error": f"本地失败: {local_error}; API 失败: {api_error}"}


class RerankerApiClient:
    def __init__(self, endpoint, api_key="", model="BAAI/bge-reranker-v2-m3", timeout=30):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @classmethod
    def from_env(cls):
        return cls(
            os.environ.get("RERANK_API_ENDPOINT", ""),
            os.environ.get("RERANK_API_KEY", ""),
            os.environ.get("RERANK_API_MODEL", "BAAI/bge-reranker-v2-m3"),
            int(os.environ.get("RERANK_API_TIMEOUT_SECONDS", "30")),
        )

    def rerank(self, query, documents, top_n):
        if not self.endpoint:
            return {"ok": False, "error": "未配置 RERANK_API_ENDPOINT"}
        payload = {"model": self.model, "query": query, "documents": documents, "top_n": top_n}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode(),
            headers=headers,
            method="POST",
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as exc:
            return {"ok": False, "error": f"rerank API 请求失败: {exc}"}
        return {
            "ok": True,
            "provider": "api",
            "model": body.get("model", self.model),
            "revision": body.get("revision", ""),
            "results": body.get("results", []),
            "latency_ms": round((time.monotonic() - started) * 1000, 3),
        }
