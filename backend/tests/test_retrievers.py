import json
import os
import math
import sqlite3

import numpy as np
import pytest

from bgpkb.infrastructure.fast_vector_index import (
    FastVectorIndex,
    build_fast_vector_index,
    load_cached_fast_vector_index,
    verify_fast_vector_artifacts,
)
from bgpkb.retrieval.retrievers import (
    Bm25Retriever,
    DenseRetriever,
    RetrievalChannelResult,
    _fts_query,
)
from bgpkb.pipeline import build_sqlite_knowledge_base as sqlite_builder

from test_retrieval_document_v1_gold import _eligibility, _governance, _semantic_chunk


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


def test_fts_query_preserves_all_uppercase_and_mixed_case_domain_terms():
    query = _fts_query("How are ASPA, ROV, and BGPsec responsibilities separated?")

    assert '"ASPA"' in query
    assert '"ROV"' in query
    assert '"BGPsec"' in query


def test_current_bm25_candidates_propagate_retrieval_manifest_to_reranker(tmp_path):
    from bgpkb.indexing.retrieval_documents import (
        build_retrieval_input_manifest,
        derive_retrieval_document,
    )

    db_path = tmp_path / "retrieval.sqlite"
    chunk = _semantic_chunk(content="complete retrieval text with lexical_tail_marker")
    document = derive_retrieval_document(
        chunk, eligibility=_eligibility(), governance=_governance(chunk)
    )
    manifest = build_retrieval_input_manifest([document])
    with sqlite3.connect(db_path) as conn:
        conn.executescript(sqlite_builder.SCHEMA)
        assert sqlite_builder.create_fts_tables(conn)
        sqlite_builder.insert_retrieval_documents(conn, [document], manifest, True)
        conn.commit()

    result = Bm25Retriever(db_path).search("lexical_tail_marker", 5)

    assert result.error is None
    assert result.metadata["retrieval_input_manifest_hash"] == manifest["input_manifest_hash"]
    assert result.items[0]["retrieval_input_manifest_hash"] == manifest["input_manifest_hash"]
    assert result.items[0]["retrieval_text"] == document["retrieval_text"]


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


def test_fast_vector_freshness_uses_source_hash_and_builder_is_preallocated_mmap(tmp_path):
    index = tmp_path / "bge_m3_vector_index.jsonl"
    rows = [
        {
            "doc_id": "chunk:a",
            "kind": "chunk",
            "retrieval_input_manifest_hash": "sha256:" + "a" * 64,
            "metadata": {
                "chunk_id": "a",
                "eligibility": {"status": "eligible"},
            },
            "vector": [3.0, 4.0],
        },
        {
            "doc_id": "chunk:b",
            "kind": "chunk",
            "retrieval_input_manifest_hash": "sha256:" + "a" * 64,
            "metadata": {
                "chunk_id": "b",
                "eligibility": {"status": "eligible"},
            },
            "vector": [4.0, 3.0],
        },
    ]
    index.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")

    artifacts = build_fast_vector_index(index)
    manifest = json.loads(artifacts.manifest_path.read_text(encoding="utf-8"))
    loaded = FastVectorIndex.load(index)

    assert manifest["source_index_sha256"].startswith("sha256:")
    assert manifest["build_strategy"] == "two_pass_preallocated_memmap_v1"
    assert isinstance(loaded.matrix, np.memmap)
    verified = verify_fast_vector_artifacts(index, eligible_chunk_ids={"a", "b"})
    assert verified["eligible_chunk_ids_hash"] == manifest["eligible_chunk_ids_hash"]

    original_stat = index.stat()
    original = index.read_text(encoding="utf-8")
    changed = original.replace("[3.0, 4.0]", "[4.0, 3.0]", 1)
    assert len(changed.encode()) == len(original.encode())
    index.write_text(changed, encoding="utf-8")
    os.utime(index, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))

    assert FastVectorIndex.load(index) is None
    # 在线路径依赖激活前已验证的不可变 release，不重新扫描大型源 JSONL。
    assert load_cached_fast_vector_index(index) is not None


def test_fast_vector_gate_rejects_eligibility_set_mismatch(tmp_path):
    index = tmp_path / "bge_m3_vector_index.jsonl"
    index.write_text(
        json.dumps({
            "kind": "chunk",
            "metadata": {"chunk_id": "a", "eligibility": {"status": "eligible"}},
            "vector": [1.0, 0.0],
        }) + "\n",
        encoding="utf-8",
    )
    build_fast_vector_index(index)

    with pytest.raises(RuntimeError, match="eligibility"):
        verify_fast_vector_artifacts(index, eligible_chunk_ids={"a", "missing"})


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
    assert result.metadata["degraded"] is True
    assert result.metadata["degraded_reason"] == "fast_vector_index_unavailable"


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
