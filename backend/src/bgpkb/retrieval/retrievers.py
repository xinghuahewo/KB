"""v2 混合召回的 SQLite BM25 与 BGE-M3 dense adapter。"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import re
import sqlite3
import time
from typing import Any, Protocol

from bgpkb import paths
from bgpkb.infrastructure.fast_vector_index import FastVectorIndexError, load_cached_fast_vector_index
from bgpkb.retrieval.retrieval_data import PublishedArtifactRetrievalData, RetrievalData
from bgpkb.infrastructure.retrieval_model_client import EmbeddingProviderChain


MAX_CHANNEL_TOP_K = 50


@dataclass
class RetrievalChannelResult:
    channel: str
    items: list[dict[str, Any]] = field(default_factory=list)
    error: dict[str, str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Retriever(Protocol):
    def search(self, query: str, top_k: int) -> RetrievalChannelResult: ...


def _top_k_error(channel: str, top_k: int) -> RetrievalChannelResult | None:
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= MAX_CHANNEL_TOP_K:
        return RetrievalChannelResult(
            channel=channel,
            error={"code": "invalid_top_k", "message": "top_k 必须是 1 到 50 的整数"},
            metadata={"requested_top_k": top_k, "max_top_k": MAX_CHANNEL_TOP_K},
        )
    return None


def _fts_query(query: str) -> str:
    # 把用户输入降为字面量 token，避免引号、通配符和 FTS 操作符改变语义。
    tokens = [
        token for token in re.findall(r"[\w./]+", query, flags=re.UNICODE)
        if token.upper() not in {"AND", "OR", "NOT", "NEAR"}
    ]
    named_tokens = [
        token for token in tokens
        if re.search(r"[a-z][A-Z]", token) or re.match(r"[A-Z]{2,}[A-Z][a-z]", token)
    ]
    if named_tokens:
        tokens = named_tokens
    return " OR ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens)


class Bm25Retriever:
    def __init__(self, db_path: Path | None = None, retrieval_data: RetrievalData | None = None):
        if db_path is not None:
            self.db_path = Path(db_path)
        else:
            active_data = retrieval_data or PublishedArtifactRetrievalData.from_environment()
            self.db_path = active_data.database_path()

    def search(self, query: str, top_k: int) -> RetrievalChannelResult:
        invalid = _top_k_error("lexical", top_k)
        if invalid:
            return invalid
        fts_query = _fts_query(query)
        if not fts_query:
            return RetrievalChannelResult("lexical", metadata={"query_empty": True})
        try:
            uri = f"file:{self.db_path.resolve().as_posix()}?mode=ro&immutable=1"
            with sqlite3.connect(uri, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT c.chunk_id, c.doc_id, c.title, c.source_type, c.chunk_type,
                           c.source_ref, c.language, c.review_status, c.content_chars,
                           c.content_preview, c.chunk_file, c.payload_json,
                           bm25(chunk_fts) AS raw_score
                    FROM chunk_fts
                    JOIN chunks c ON c.chunk_id = chunk_fts.chunk_id
                    WHERE chunk_fts MATCH ?
                    ORDER BY raw_score ASC, c.chunk_id ASC
                    LIMIT ?
                    """,
                    (fts_query, top_k),
                ).fetchall()
        except (sqlite3.Error, OSError) as exc:
            return RetrievalChannelResult(
                "lexical",
                error={"code": "bm25_unavailable", "message": f"SQLite BM25 查询失败：{exc}"},
                metadata={"fts_query": fts_query},
            )
        best = float(rows[0]["raw_score"]) if rows else 0.0
        items = []
        for rank, row in enumerate(rows, start=1):
            item = dict(row)
            raw_score = float(item["raw_score"])
            item.update({
                "raw_score": raw_score,
                "raw_rank": rank,
                "score": 1.0 / (1.0 + max(0.0, raw_score - best)),
                "channel": "lexical",
            })
            items.append(item)
        return RetrievalChannelResult(
            "lexical", items=items,
            metadata={"engine": "sqlite_fts5", "score_direction": "raw_lower_is_better", "fts_query": fts_query},
        )


def _cosine(left: list[float], right: list[float]) -> float:
    denominator = math.sqrt(sum(value * value for value in left)) * math.sqrt(sum(value * value for value in right))
    if denominator == 0:
        raise ValueError("向量范数不能为零")
    return sum(a * b for a, b in zip(left, right)) / denominator


class DenseRetriever:
    def __init__(
        self,
        index_path: Path | None = None,
        provider: Any | None = None,
        min_similarity: float = 0.5,
        retrieval_data: RetrievalData | None = None,
    ):
        if index_path is not None:
            self.index_path = Path(index_path)
        else:
            active_data = retrieval_data or PublishedArtifactRetrievalData.from_environment()
            self.index_path = active_data.vector_index_path()
        self.provider = provider or EmbeddingProviderChain.from_env()
        self.min_similarity = float(min_similarity)

    def _failure(self, code: str, message: str, metadata: dict[str, Any] | None = None):
        return RetrievalChannelResult("vector", error={"code": code, "message": message}, metadata=metadata or {})

    def search(self, query: str, top_k: int) -> RetrievalChannelResult:
        started = time.perf_counter()
        invalid = _top_k_error("vector", top_k)
        if invalid:
            return invalid
        try:
            response = self.provider.embed_texts([query], require_model=True)
        except Exception as exc:
            return self._failure("embedding_unavailable", f"Embedding provider 调用失败：{exc}")
        provider_metadata = {
            key: response.get(key) for key in
            ("provider", "model", "revision", "degraded", "degraded_reason", "attempts")
            if key in response
        }
        if not response.get("ok"):
            return self._failure(
                "embedding_unavailable",
                response.get("error", "Embedding provider 不可用"),
                provider_metadata,
            )
        vectors = response.get("vectors")
        if not isinstance(vectors, list) or len(vectors) != 1:
            return self._failure("invalid_embedding", "Embedding 响应必须包含一个查询向量", provider_metadata)
        query_vector = vectors[0]
        if (
            not isinstance(query_vector, list) or not query_vector
            or any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in query_vector)
        ):
            return self._failure("invalid_embedding", "查询向量必须是非空 finite 数值数组", provider_metadata)
        query_vector = [float(value) for value in query_vector]
        if math.sqrt(sum(value * value for value in query_vector)) == 0:
            return self._failure("invalid_embedding", "查询向量范数不能为零", provider_metadata)

        index_started = time.perf_counter()
        try:
            fast_index = load_cached_fast_vector_index(self.index_path)
            if fast_index is not None:
                items = fast_index.search(query_vector, top_k=top_k, min_similarity=self.min_similarity)
                provider_metadata.update({
                    "index_path": str(self.index_path),
                    "index_mode": "fast_numpy",
                    "score": "cosine",
                    "vector_count": fast_index.record_count,
                    "dimension": fast_index.dimension,
                    "index_search_ms": round((time.perf_counter() - index_started) * 1000, 3),
                    "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                })
                return RetrievalChannelResult("vector", items=items, metadata=provider_metadata)
        except ValueError as exc:
            return self._failure("dimension_mismatch", f"快向量索引查询失败：{exc}", provider_metadata)
        except FastVectorIndexError as exc:
            return self._failure("index_unavailable", f"快向量索引不可用：{exc}", provider_metadata)

        try:
            records = []
            scanned_count = 0
            with self.index_path.open(encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    if record.get("kind", "chunk") != "chunk":
                        continue
                    vector = record.get("vector")
                    if (
                        not isinstance(vector, list) or len(vector) != len(query_vector)
                        or any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in vector)
                    ):
                        return self._failure("dimension_mismatch", f"索引第 {line_number} 行向量维度或数值无效", provider_metadata)
                    scanned_count += 1
                    score = _cosine(query_vector, [float(value) for value in vector])
                    if score < self.min_similarity:
                        continue
                    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
                    chunk_id = metadata.get("chunk_id") or record.get("chunk_id")
                    if not chunk_id and str(record.get("doc_id", "")).startswith("chunk:"):
                        chunk_id = str(record["doc_id"]).split(":", 1)[1]
                    if not chunk_id:
                        return self._failure("index_corrupt", f"索引第 {line_number} 行缺少 chunk_id", provider_metadata)
                    item = {**record, **metadata, "chunk_id": chunk_id, "raw_score": score, "score": score, "channel": "vector"}
                    item.pop("vector", None)
                    records.append(item)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            return self._failure("index_unavailable", f"Dense 索引不可用：{exc}", provider_metadata)
        records.sort(key=lambda item: (-item["raw_score"], item["chunk_id"]))
        items = records[:top_k]
        for rank, item in enumerate(items, start=1):
            item["raw_rank"] = rank
        provider_metadata.update({
            "index_path": str(self.index_path),
            "score": "cosine",
            "index_mode": "jsonl_scan",
            "degraded": True,
            "degraded_reason": "fast_vector_index_unavailable",
            "vector_count": scanned_count,
            "index_search_ms": round((time.perf_counter() - index_started) * 1000, 3),
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
        })
        return RetrievalChannelResult("vector", items=items, metadata=provider_metadata)
