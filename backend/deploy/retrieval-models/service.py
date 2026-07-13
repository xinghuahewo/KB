"""离线检索模型 HTTP 服务。"""

import os
from pathlib import Path
import threading
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator


EMBEDDING_MODEL = "BAAI/bge-m3"
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
REVISIONS = {
    EMBEDDING_MODEL: "5617a9f61b028005a4858fdac845db406aefb181",
    RERANKER_MODEL: "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e",
}
MAX_EMBEDDING_BATCH = 64
MAX_TEXT_CHARS = 4096
MAX_EMBEDDING_TOTAL_CHARS = 65536
MAX_QUERY_CHARS = 4096
MAX_DOCUMENTS = 20
MAX_DOCUMENT_CHARS = 8192
MAX_RERANK_TOTAL_CHARS = 131072


class EmbeddingRequest(BaseModel):
    model: Literal[EMBEDDING_MODEL]
    input: list[str] = Field(min_length=1, max_length=MAX_EMBEDDING_BATCH)

    @model_validator(mode="after")
    def validate_text_limits(self):
        if any(not text or len(text) > MAX_TEXT_CHARS for text in self.input):
            raise ValueError("每个 embedding 文本长度必须为 1..4096")
        if sum(map(len, self.input)) > MAX_EMBEDDING_TOTAL_CHARS:
            raise ValueError("embedding 总字符数超过限制")
        return self


class RerankRequest(BaseModel):
    model: Literal[RERANKER_MODEL]
    query: str = Field(min_length=1, max_length=MAX_QUERY_CHARS)
    documents: list[str] = Field(min_length=1, max_length=MAX_DOCUMENTS)
    top_n: int = Field(ge=5, le=8)

    @model_validator(mode="after")
    def validate_top_n(self):
        if self.top_n > len(self.documents):
            raise ValueError("top_n 不能超过 documents 数量")
        if any(not document or len(document) > MAX_DOCUMENT_CHARS for document in self.documents):
            raise ValueError("每个 rerank 文档长度必须为 1..8192")
        if len(self.query) + sum(map(len, self.documents)) > MAX_RERANK_TOTAL_CHARS:
            raise ValueError("rerank 总字符数超过限制")
        return self


class LazyModel:
    def __init__(self, role: str, model_root: str, device: str, loader=None):
        self.role = role
        self.model_root = Path(model_root)
        self.device = device
        self._model = None
        self._lock = threading.Lock()
        self._loader = loader

    @property
    def loaded(self):
        return self._model is not None

    def get(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    if self._loader:
                        self._model = self._loader()
                    else:
                        from FlagEmbedding import BGEM3FlagModel, FlagReranker

                        if self.role == "embedding":
                            self._model = BGEM3FlagModel(str(self.model_root / EMBEDDING_MODEL), use_fp16=True)
                        else:
                            self._model = FlagReranker(str(self.model_root / RERANKER_MODEL), use_fp16=True)
        return self._model


def create_app(
    role: str | None = None,
    model: Any | None = None,
    revision: str | None = None,
    device: str | None = None,
    model_root: str | None = None,
    max_concurrency: int | None = None,
) -> FastAPI:
    role = role or os.environ.get("SERVICE_ROLE", "")
    if role not in {"embedding", "reranker"}:
        raise ValueError("SERVICE_ROLE 必须为 embedding 或 reranker")
    model_name = EMBEDDING_MODEL if role == "embedding" else RERANKER_MODEL
    revision = revision or REVISIONS[model_name]
    device = device or os.environ.get("MODEL_DEVICE", "cuda:0")
    holder = model or LazyModel(role, model_root or os.environ.get("MODEL_ROOT", "/models"), device)
    configured_concurrency = max_concurrency or int(os.environ.get("MAX_CONCURRENT_INFERENCE", "1"))
    inference_slots = threading.BoundedSemaphore(max(1, min(configured_concurrency, 8)))
    readiness_lock = threading.Lock()
    ready = False
    app = FastAPI()

    def loaded_model():
        return holder.get() if isinstance(holder, LazyModel) else holder

    def warmup():
        nonlocal ready
        if ready:
            return
        with readiness_lock:
            if ready:
                return
            with inference_slots:
                current = loaded_model()
                if role == "embedding":
                    current.encode(["healthcheck"])
                else:
                    current.compute_score([["healthcheck", "healthcheck"]], normalize=True)
            ready = True

    @app.get("/health")
    def health():
        try:
            warmup()
        except Exception:
            raise HTTPException(status_code=503, detail="模型未就绪")
        return {
            "role": role,
            "model": model_name,
            "revision": revision,
            "device": device,
            "loaded": ready,
        }

    @app.post("/v1/embeddings")
    def embeddings(request: EmbeddingRequest):
        if role != "embedding":
            raise HTTPException(status_code=409, detail="当前服务角色不是 embedding")
        try:
            warmup()
        except Exception:
            raise HTTPException(status_code=503, detail="模型未就绪")
        with inference_slots:
            encoded = loaded_model().encode(request.input)
        vectors = encoded.get("dense_vecs", encoded) if isinstance(encoded, dict) else encoded
        if hasattr(vectors, "tolist"):
            vectors = vectors.tolist()
        return {
            "model": model_name,
            "revision": revision,
            "data": [
                {"index": index, "embedding": list(vector)}
                for index, vector in enumerate(vectors)
            ],
        }

    @app.post("/v1/rerank")
    def rerank(request: RerankRequest):
        if role != "reranker":
            raise HTTPException(status_code=409, detail="当前服务角色不是 reranker")
        pairs = [[request.query, document] for document in request.documents]
        try:
            warmup()
        except Exception:
            raise HTTPException(status_code=503, detail="模型未就绪")
        with inference_slots:
            scores = loaded_model().compute_score(pairs, normalize=True)
        if not isinstance(scores, (list, tuple)):
            scores = [scores]
        ranked = sorted(
            (
                {"index": index, "relevance_score": float(score), "document": request.documents[index]}
                for index, score in enumerate(scores)
            ),
            key=lambda item: (-item["relevance_score"], item["index"]),
        )
        return {"model": model_name, "revision": revision, "results": ranked[: request.top_n]}

    return app


app = create_app() if os.environ.get("SERVICE_ROLE") else FastAPI()
