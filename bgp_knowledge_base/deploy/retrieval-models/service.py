"""离线检索模型 HTTP 服务。"""

import os
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator


EMBEDDING_MODEL = "BAAI/bge-m3"
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
REVISIONS = {
    EMBEDDING_MODEL: "5617a9f61b028005a4858fdac845db406aefb181",
    RERANKER_MODEL: "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e",
}


class EmbeddingRequest(BaseModel):
    model: Literal[EMBEDDING_MODEL]
    input: list[str] = Field(min_length=1)


class RerankRequest(BaseModel):
    model: Literal[RERANKER_MODEL]
    query: str = Field(min_length=1)
    documents: list[str] = Field(min_length=1)
    top_n: int = Field(ge=5, le=8)

    @model_validator(mode="after")
    def validate_top_n(self):
        if self.top_n > len(self.documents):
            raise ValueError("top_n 不能超过 documents 数量")
        return self


class LazyModel:
    def __init__(self, role: str, model_root: str, device: str):
        self.role = role
        self.model_root = Path(model_root)
        self.device = device
        self._model = None

    @property
    def loaded(self):
        return self._model is not None

    def get(self):
        if self._model is None:
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
) -> FastAPI:
    role = role or os.environ.get("SERVICE_ROLE", "")
    if role not in {"embedding", "reranker"}:
        raise ValueError("SERVICE_ROLE 必须为 embedding 或 reranker")
    model_name = EMBEDDING_MODEL if role == "embedding" else RERANKER_MODEL
    revision = revision or REVISIONS[model_name]
    device = device or os.environ.get("MODEL_DEVICE", "cuda:0")
    holder = model or LazyModel(role, model_root or os.environ.get("MODEL_ROOT", "/models"), device)
    app = FastAPI()

    def loaded_model():
        return holder.get() if isinstance(holder, LazyModel) else holder

    @app.get("/health")
    def health():
        return {
            "role": role,
            "model": model_name,
            "revision": revision,
            "device": device,
            "loaded": holder.loaded if isinstance(holder, LazyModel) else True,
        }

    @app.post("/v1/embeddings")
    def embeddings(request: EmbeddingRequest):
        if role != "embedding":
            raise HTTPException(status_code=409, detail="当前服务角色不是 embedding")
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
