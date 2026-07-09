"""远程 BGE-M3 embedding 客户端。"""

import json
import os
import time
import urllib.error
import urllib.request


SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1/embeddings"
DEFAULT_MODEL = "BAAI/bge-m3"


class BgeM3RemoteClient:
    def __init__(
        self,
        provider="siliconflow_bge_m3",
        api_key="",
        base_url="",
        model=DEFAULT_MODEL,
        timeout=30,
    ):
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url or (SILICONFLOW_BASE_URL if provider == "siliconflow_bge_m3" else "")
        self.model = model
        self.timeout = timeout

    def __repr__(self):
        return (
            f"BgeM3RemoteClient(provider={self.provider!r}, model={self.model!r}, "
            f"base_url={self.base_url!r}, api_key='<redacted>')"
        )

    @classmethod
    def from_env(cls, provider="siliconflow_bge_m3"):
        if provider == "generic":
            return cls(
                provider=provider,
                api_key=os.environ.get("EMBEDDING_API_KEY", ""),
                base_url=os.environ.get("EMBEDDING_API_ENDPOINT", ""),
                model=os.environ.get("EMBEDDING_API_MODEL", DEFAULT_MODEL),
                timeout=int(os.environ.get("EMBEDDING_API_TIMEOUT_SECONDS", "30")),
            )
        if provider == "aliyun_eas_bge_m3":
            return cls(
                provider=provider,
                api_key=os.environ.get("ALIYUN_BGE_M3_API_KEY", ""),
                base_url=os.environ.get("ALIYUN_BGE_M3_ENDPOINT", ""),
                model=os.environ.get("ALIYUN_BGE_M3_MODEL", DEFAULT_MODEL),
                timeout=int(os.environ.get("ALIYUN_BGE_M3_TIMEOUT_SECONDS", "30")),
            )
        return cls(
            provider=provider,
            api_key=os.environ.get("SILICONFLOW_API_KEY", ""),
            base_url=os.environ.get("SILICONFLOW_BASE_URL", SILICONFLOW_BASE_URL),
            model=os.environ.get("SILICONFLOW_EMBEDDING_MODEL", DEFAULT_MODEL),
            timeout=int(os.environ.get("SILICONFLOW_TIMEOUT_SECONDS", "30")),
        )

    def build_payload(self, texts):
        if self.provider == "aliyun_eas_bge_m3":
            return {"input": texts, "embedding_type": "dense"}
        return {
            "model": self.model,
            "input": texts,
            "encoding_format": "float",
        }

    def _parse_vectors(self, payload):
        data = payload.get("data", [])
        if data and isinstance(data[0], dict):
            ordered = sorted(data, key=lambda item: item.get("index", 0))
            return [item.get("embedding", []) for item in ordered]
        embeddings = payload.get("embeddings", [])
        if embeddings and isinstance(embeddings[0], dict):
            return [item.get("embedding", item.get("vector", [])) for item in embeddings]
        return embeddings

    def embed_texts(self, texts):
        if not self.api_key:
            return self._error("missing_api_key", "BGE-M3 API key is not configured.")
        if not self.base_url:
            return self._error("missing_endpoint", "BGE-M3 endpoint is not configured.")

        request = urllib.request.Request(
            self.base_url,
            data=json.dumps(self.build_payload(texts), ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return self._error("http_error", f"BGE-M3 API returned HTTP {exc.code}.")
        except Exception:
            return self._error("request_failed", "BGE-M3 API request failed.")

        vectors = self._parse_vectors(payload)
        if len(vectors) != len(texts) or any(not vector for vector in vectors):
            return self._error("invalid_response", "BGE-M3 API returned invalid embeddings.")
        return {
            "ok": True,
            "provider": self.provider,
            "model": self.model,
            "revision": payload.get("revision", ""),
            "latency_ms": round((time.monotonic() - started) * 1000, 3),
            "vectors": vectors,
            "dimension": len(vectors[0]),
            "input_count": len(texts),
        }

    def _error(self, code, message):
        return {
            "ok": False,
            "provider": self.provider,
            "model": self.model,
            "error_code": code,
            "error": message,
        }
