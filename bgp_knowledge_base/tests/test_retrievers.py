import json
import math
import sqlite3

import pytest

from bgpkb.service.fast_vector_index import FastVectorIndex, build_fast_vector_index
from bgpkb.service.retrievers import Bm25Retriever, DenseRetriever, RetrievalChannelResult


def _fts_database(path):
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE chunks (
          chunk_id TEXT PRIMARY KEY, doc_id TEXT, title TEXT, source_type TEXT,
          chunk_type TEXT, source_ref TEXT, language TEXT, review_status TEXT,
          content_chars INTEGER, content_preview TEXT, chunk_file TEXT, payload_json TEXT
        );
        CREATE VIRTUAL TABLE chunk_fts USING fts5(
          chunk_id UNINDEXED, title, source_type, chunk_type, content_preview
        );
    """)
    rows = [
        ("b", "doc-b", "Route leak leak", "standard", "section", "b.txt", "en", "approved", 20, "route leak leak", "b.md", "{}"),
        ("a", "doc-a", "Route leak", "paper", "section", "a.txt", "en", "approved", 10, "route leak", "a.md", "{}"),
    ]
    conn.executemany("INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    conn.executemany(
        "INSERT INTO chunk_fts VALUES (?, ?, ?, ?, ?)",
        [(r[0], r[2], r[3], r[4], r[9]) for r in rows],
    )
    conn.commit()
    conn.close()


def test_bm25_retriever_uses_fts5_and_preserves_raw_rank(tmp_path):
    db_path = tmp_path / "kb.sqlite"
    _fts_database(db_path)

    result = Bm25Retriever(db_path).search('route leak" OR *', 50)

    assert isinstance(result, RetrievalChannelResult)
    assert result.channel == "lexical"
    assert result.error is None
    assert [item["raw_rank"] for item in result.items] == [1, 2]
    assert all(item["score"] > 0 and item["raw_score"] < 0 for item in result.items)
    assert result.items[0]["score"] >= result.items[1]["score"]
    assert {"doc_id", "source_ref", "content_preview", "review_status"} <= result.items[0].keys()


def test_bm25_failure_and_empty_result_are_distinguishable(tmp_path):
    missing = Bm25Retriever(tmp_path / "missing.sqlite").search("BGP", 50)
    db_path = tmp_path / "kb.sqlite"
    _fts_database(db_path)
    empty = Bm25Retriever(db_path).search("unfindable", 50)

    assert missing.error and missing.items == []
    assert empty.error is None and empty.items == []


class FakeProvider:
    def embed_texts(self, texts, require_model=False):
        return {
            "ok": True,
            "provider": "local_http",
            "model": "BAAI/bge-m3",
            "revision": "rev-1",
            "vectors": [[1.0, 0.0]],
            "dimension": 2,
            "degraded": False,
        }


def test_fast_vector_index_builder_normalizes_chunk_vectors(tmp_path):
    index = tmp_path / "bge_m3_vector_index.jsonl"
    records = [
        {
            "doc_id": "chunk:a",
            "kind": "chunk",
            "metadata": {"chunk_id": "a", "doc_id": "doc-a", "title": "A"},
            "vector": [3.0, 4.0],
        },
        {
            "doc_id": "entity:not-a-chunk",
            "kind": "entity",
            "metadata": {"chunk_id": "ignored"},
            "vector": [1.0, 0.0],
        },
    ]
    index.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")

    artifacts = build_fast_vector_index(index)
    loaded = FastVectorIndex.load(index)

    assert artifacts.matrix_path.exists()
    assert artifacts.metadata_path.exists()
    assert artifacts.manifest_path.exists()
    assert loaded is not None
    assert loaded.record_count == 1
    assert loaded.dimension == 2
    results = loaded.search([0.6, 0.8], top_k=5, min_similarity=0.0)
    assert [item["chunk_id"] for item in results] == ["a"]
    assert results[0]["raw_score"] == pytest.approx(1.0)
    assert "vector" not in results[0]


def test_dense_retriever_prefers_fast_vector_index_without_reading_jsonl(tmp_path):
    index = tmp_path / "bge_m3_vector_index.jsonl"
    records = [
        {"doc_id": "chunk:a", "kind": "chunk", "metadata": {"chunk_id": "a"}, "vector": [1.0, 0.0]},
        {"doc_id": "chunk:b", "kind": "chunk", "metadata": {"chunk_id": "b"}, "vector": [0.0, 1.0]},
        {"doc_id": "chunk:c", "kind": "chunk", "metadata": {"chunk_id": "c"}, "vector": [1.0, 1.0]},
    ]
    index.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
    build_fast_vector_index(index)
    index.unlink()

    result = DenseRetriever(index, FakeProvider(), min_similarity=0.1).search("route leak", 2)

    assert result.error is None
    assert [item["chunk_id"] for item in result.items] == ["a", "c"]
    assert [item["raw_rank"] for item in result.items] == [1, 2]
    assert result.metadata["index_mode"] == "fast_numpy"
    assert result.metadata["vector_count"] == 3


def test_dense_retriever_computes_cosine_and_keeps_provider_metadata(tmp_path):
    index = tmp_path / "index.jsonl"
    records = [
        {"doc_id": "chunk:z", "kind": "chunk", "metadata": {"chunk_id": "z", "doc_id": "doc-z"}, "vector": [1.0, 0.0]},
        {"doc_id": "chunk:y", "kind": "chunk", "metadata": {"chunk_id": "y", "doc_id": "doc-y"}, "vector": [1.0, 1.0]},
        {"doc_id": "entity:not-a-chunk", "kind": "entity", "vector": [1.0, 0.0]},
    ]
    index.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")

    result = DenseRetriever(index, FakeProvider()).search("route leak", 50)

    assert result.error is None
    assert [item["chunk_id"] for item in result.items] == ["z", "y"]
    assert result.items[0]["raw_score"] == 1.0
    assert result.items[1]["raw_score"] == 1 / math.sqrt(2)
    assert [item["raw_rank"] for item in result.items] == [1, 2]
    assert result.metadata["provider"] == "local_http"
    assert result.metadata["revision"] == "rev-1"
    assert result.metadata["index_mode"] == "jsonl_scan"


def test_dense_invalid_dimension_and_provider_failure_are_structured(tmp_path):
    index = tmp_path / "index.jsonl"
    index.write_text(json.dumps({"doc_id": "chunk:a", "vector": [1.0, 0.0, 0.0]}) + "\n")
    bad_index = DenseRetriever(index, FakeProvider()).search("BGP", 50)

    class FailedProvider:
        def embed_texts(self, texts, require_model=False):
            return {"ok": False, "error": "both unavailable", "degraded": True}

    failed = DenseRetriever(index, FailedProvider()).search("BGP", 50)

    assert bad_index.error["code"] == "dimension_mismatch"
    assert bad_index.items == []
    assert failed.error["code"] == "embedding_unavailable"
    assert failed.items == []


def test_retrievers_reject_top_k_outside_contract(tmp_path):
    db_path = tmp_path / "kb.sqlite"
    _fts_database(db_path)
    for top_k in (0, 51):
        result = Bm25Retriever(db_path).search("BGP", top_k)
        assert result.error["code"] == "invalid_top_k"
