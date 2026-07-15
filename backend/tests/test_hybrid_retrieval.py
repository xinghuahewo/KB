import json
import hashlib
import os
from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgpkb import paths  # noqa: E402
from bgpkb.retrieval import hybrid_retrieval  # noqa: E402
from bgpkb.retrieval import retrieval_framework  # noqa: E402
from bgpkb.retrieval.retrievers import RetrievalChannelResult  # noqa: E402


QUERY_SCRIPT = ROOT / "src" / "bgpkb" / "pipeline" / "query_hybrid_rag.py"


def result(doc_id, chunk_id, source_type, score):
    return {
        "doc_id": doc_id,
        "chunk_id": chunk_id,
        "title": chunk_id,
        "source_ref": doc_id,
        "source_type": source_type,
        "review_status": "approved",
        "lifecycle_status": "approved",
        "content_preview": f"content for {chunk_id}",
        "score": score,
    }


def test_rrf_fuses_lexical_and_vector_results_and_deduplicates_chunks():
    lexical = [
        result("rfc7908", "chunk_a", "standard", 8.0),
        result("case_001", "chunk_b", "case_report", 7.0),
    ]
    vector = [
        result("rfc7908", "chunk_a", "standard", 0.95),
        result("paper_001", "chunk_c", "paper", 0.90),
    ]

    fused = hybrid_retrieval.rrf_fuse(
        query="route leak",
        lexical_results=lexical,
        vector_results=vector,
        limit=10,
        rrf_k=60,
    )

    assert [item["chunk_id"] for item in fused].count("chunk_a") == 1
    assert fused[0]["chunk_id"] == "chunk_a"
    assert fused[0]["lexical_score"] == 8.0
    assert fused[0]["vector_score"] == 0.95
    assert fused[0]["retrieval_method"] == "hybrid_rrf"
    assert {"lexical", "vector"} <= set(fused[0]["match_reasons"])
    assert fused[0]["fusion_score"] > 0


def test_reranker_uses_current_retrieval_text_and_blocks_component_manifest_drift():
    manifest_hash = "sha256:" + "a" * 64
    candidate = result("rfc7908", "chunk-current", "standard", 1.0)
    retrieval_text = "title: Route Leak\ncontent: complete body tail-marker"
    candidate.update({
        "retrieval_text": retrieval_text,
        "retrieval_text_hash": "sha256:" + hashlib.sha256(retrieval_text.encode()).hexdigest(),
        "retrieval_text_version": "retrieval_text_v1",
        "retrieval_input_manifest_hash": manifest_hash,
    })

    class CapturingReranker:
        def __init__(self):
            self.documents = None

        def rerank(self, query, documents, top_n, require_model=False):
            self.documents = documents
            return {
                "ok": True,
                "provider": "fake",
                "model": "BAAI/bge-reranker-v2-m3",
                "revision": "rev-test",
                "results": [{"index": 0, "relevance_score": 0.9}],
            }

    reranker = CapturingReranker()
    payload = hybrid_retrieval.rerank_candidates(
        "route leak",
        [candidate],
        reranker=reranker,
        component_manifest_hashes={
            "fts": manifest_hash,
            "embedding": manifest_hash,
            "reranker": manifest_hash,
        },
    )
    assert reranker.documents == [candidate["retrieval_text"]]
    assert payload["reranker_input_manifest_hash"] == manifest_hash

    with __import__("pytest").raises(ValueError, match="embedding"):
        hybrid_retrieval.rerank_candidates(
            "route leak",
            [candidate],
            reranker=reranker,
            component_manifest_hashes={
                "fts": manifest_hash,
                "embedding": "sha256:" + "c" * 64,
                "reranker": manifest_hash,
            },
        )


def test_vector_search_filters_results_below_similarity_threshold():
    records = [
        {
            "doc_id": "chunk:strong",
            "kind": "chunk",
            "trusted": True,
            "review_status": "approved",
            "vector": [1.0, 0.0],
            "metadata": {"chunk_id": "strong", "doc_id": "rfc7908"},
        },
        {
            "doc_id": "chunk:weak",
            "kind": "chunk",
            "trusted": True,
            "review_status": "approved",
            "vector": [0.4, 0.916515],
            "metadata": {"chunk_id": "weak", "doc_id": "other"},
        },
    ]

    results = hybrid_retrieval.vector_search(
        [1.0, 0.0],
        records,
        limit=5,
        min_similarity=0.5,
    )

    assert [item["chunk_id"] for item in results] == ["strong"]


def test_metadata_boost_prefers_standards_cases_and_papers_by_query_intent():
    standard = result("rfc7908", "standard_chunk", "standard", 1.0)
    case = result("route_leak_case", "case_chunk", "case_report", 1.0)
    paper = result("detection_paper", "paper_chunk", "paper", 1.0)
    data_doc = result("routeviews_api_doc", "data_chunk", "data_doc", 1.0)
    tool_doc = result("bgpstream_docs", "tool_chunk", "tool_doc", 1.0)

    definition = hybrid_retrieval.rrf_fuse("RFC route leak definition", [case, standard], [], limit=2)
    incident = hybrid_retrieval.rrf_fuse("route leak incident case", [standard, case], [], limit=2)
    method = hybrid_retrieval.rrf_fuse("route leak detection method", [standard, paper], [], limit=2)
    named_method = hybrid_retrieval.rrf_fuse("What is BEAR for BGP analysis?", [standard, paper], [], limit=2)
    data_query = hybrid_retrieval.rrf_fuse("What does RouteViews provide?", [standard, data_doc], [], limit=2)
    data_analysis_query = hybrid_retrieval.rrf_fuse(
        "How is BGPStream used in BGP event analysis?",
        [paper, tool_doc],
        [],
        limit=2,
    )

    assert definition[0]["source_type"] == "standard"
    assert incident[0]["source_type"] == "case_report"
    assert method[0]["source_type"] == "paper"
    assert named_method[0]["source_type"] == "paper"
    assert data_query[0]["source_type"] == "data_doc"
    assert data_analysis_query[0]["source_type"] == "tool_doc"
    assert definition[0]["metadata_boost"] > 0


def test_chinese_route_leak_query_expands_and_returns_trusted_results():
    payload = hybrid_retrieval.search("路由泄露", limit=5, vector_enabled=False)

    assert "route leak" in payload["normalized_query"].lower()
    assert payload["results"]
    assert all(item["trusted"] is True for item in payload["results"])
    assert any(
        "route leak" in (item["title"] + " " + item["content_preview"]).lower().replace("-", " ")
        for item in payload["results"]
    )
    assert payload["vector_status"] == "disabled"


def test_processed_source_is_retrieval_eligible_without_changing_review_status():
    payload = hybrid_retrieval.search("RouteViews API", limit=5, vector_enabled=False)

    assert payload["results"]
    routeviews = next(item for item in payload["results"] if "routeviews" in item["source_ref"].lower())
    assert routeviews["trusted"] is True
    assert routeviews["trust_basis"] in {
        "approved_entity_evidence",
        "processed_source_with_traceability",
        "approved_record",
    }
    manifest = json.loads((paths.PUBLISHED_DIR / "manifest.json").read_text(encoding="utf-8"))
    expected_status = "approved" if manifest["corpus_version"] == "v2" else "pending"
    assert routeviews["review_status"] == expected_status


def test_named_tool_query_surfaces_matching_documentation():
    payload = hybrid_retrieval.search(
        "How is BGPStream used in BGP event analysis?",
        limit=8,
        vector_enabled=False,
    )

    assert any("bgpstream" in item["source_ref"].lower() for item in payload["results"])


def test_hybrid_query_cli_outputs_json(capsys):
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(QUERY_SCRIPT), "search", "路由泄露", "--top-k", "2", "--no-vector"]
        runpy.run_path(str(QUERY_SCRIPT), run_name="__main__")
    finally:
        sys.argv = old_argv

    payload = json.loads(capsys.readouterr().out)
    assert payload["query"] == "路由泄露"
    assert len(payload["results"]) <= 2
    assert payload["vector_status"] == "disabled"


class FakeRetriever:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def search(self, query, top_k):
        self.calls.append((query, top_k))
        return self.result


def _channel_item(chunk_id, raw_rank, raw_score=1.0):
    return {
        "chunk_id": chunk_id,
        "doc_id": f"doc-{chunk_id}",
        "title": chunk_id,
        "content_preview": chunk_id,
        "raw_rank": raw_rank,
        "raw_score": raw_score,
        "score": raw_score,
    }


def test_v2_search_uses_fixed_channel_limits_and_rrf_contract():
    lexical = FakeRetriever(RetrievalChannelResult("lexical", items=[
        _channel_item("shared", 2, 8.0),
        _channel_item("shared", 1, 9.0),
        _channel_item("lexical-only", 2, 7.0),
    ]))
    vector = FakeRetriever(RetrievalChannelResult("vector", items=[
        _channel_item("shared", 1, 0.9),
        _channel_item("vector-only", 2, 0.8),
    ], metadata={"provider": "local_http"}))

    payload = hybrid_retrieval.search(
        "route leak",
        lexical_retriever=lexical,
        dense_retriever=vector,
        trusted_chunk_ids=set(),
        eligible_doc_ids=set(),
    )

    assert lexical.calls == [(payload["normalized_query"], 50)]
    assert vector.calls == [(payload["normalized_query"], 50)]
    assert len(payload["results"]) == 3
    shared = payload["results"][0]
    assert shared["chunk_id"] == "shared"
    assert shared["rrf_score"] == 2 / 61
    assert shared["lexical_raw_rank"] == 1
    assert shared["lexical_raw_score"] == 9.0
    assert shared["vector_raw_rank"] == 1
    assert shared["vector_raw_score"] == 0.9
    assert shared["match_channels"] == ["lexical", "vector"]
    assert payload["degraded"] is False


def test_search_reports_jsonl_vector_fallback_as_degraded():
    lexical = FakeRetriever(RetrievalChannelResult("lexical", items=[]))
    vector = FakeRetriever(RetrievalChannelResult(
        "vector",
        items=[_channel_item("vector-only", 1, 0.8)],
        metadata={
            "index_mode": "jsonl_scan",
            "degraded": True,
            "degraded_reason": "fast_vector_index_unavailable",
        },
    ))

    payload = hybrid_retrieval.search(
        "route leak",
        lexical_retriever=lexical,
        dense_retriever=vector,
        trusted_chunk_ids=set(),
        eligible_doc_ids=set(),
    )

    assert payload["degraded"] is True


def test_context_pack_accepts_empty_candidates_with_matching_channel_manifests(monkeypatch):
    manifest_hash = "sha256:" + "a" * 64

    class EmptyRetrievalData:
        @staticmethod
        def excluded_by_policy():
            return []

    monkeypatch.setattr(hybrid_retrieval, "search", lambda *args, **kwargs: {
        "results": [],
        "channel_metadata": {
            "lexical": {"retrieval_input_manifest_hash": manifest_hash},
            "vector": {"retrieval_input_manifest_hash": manifest_hash},
        },
        "degraded": False,
        "lexical_count": 0,
        "vector_count": 0,
        "vector_status": "empty",
    })

    payload = hybrid_retrieval.context_pack(
        "明天北京逐小时天气",
        top_n=5,
        query_type="fact",
        require_model=True,
        retrieval_data=EmptyRetrievalData(),
    )

    assert payload["results"] == []
    assert payload["rerank_status"] == "empty"
    assert payload["degraded"] is False


def test_rrf_is_capped_at_twenty_and_ties_are_stable():
    lexical = FakeRetriever(RetrievalChannelResult("lexical", items=[
        _channel_item(f"chunk-{index:02}", 1, 1.0) for index in range(25, -1, -1)
    ]))
    vector = FakeRetriever(RetrievalChannelResult("vector", items=[]))

    payload = hybrid_retrieval.search(
        "BGP",
        lexical_retriever=lexical,
        dense_retriever=vector,
        trusted_chunk_ids=set(),
        eligible_doc_ids=set(),
    )

    assert len(payload["results"]) == 20
    assert [item["chunk_id"] for item in payload["results"]] == [f"chunk-{index:02}" for index in range(20)]
    assert payload["channel_status"]["vector"] == "empty"


def test_rrf_candidate_pool_caps_each_logical_source_before_global_limit():
    lexical_items = []
    for index in range(25):
        item = _channel_item(f"dominant-{index:02}", index + 1, 1.0)
        item.update({
            "doc_id": "dominant-source",
            "source_ref": "https://example.test/dominant-source#part",
        })
        if index < 3:
            item["source_id"] = "dominant-source"
        lexical_items.append(item)
    tail = _channel_item("independent", 26, 0.1)
    tail.update({"doc_id": "independent-source", "source_ref": "independent-source#part"})
    lexical_items.append(tail)

    fused = hybrid_retrieval._rrf_channel_results(
        RetrievalChannelResult("lexical", items=lexical_items),
        RetrievalChannelResult("vector", items=[]),
        limit=20,
    )

    assert [item["doc_id"] for item in fused].count("dominant-source") == 2
    assert any(item["doc_id"] == "independent-source" for item in fused)


def test_context_pack_rejects_unsupported_intent_but_preserves_channel_evidence():
    manifest_hash = "sha256:" + "a" * 64
    lexical_item = _channel_item("stock-route", 1, 1.0)
    lexical_item.update({
        "doc_id": "rfc4271",
        "source_ref": "rfc4271#part",
        "retrieval_input_manifest_hash": manifest_hash,
    })
    lexical = FakeRetriever(RetrievalChannelResult(
        "lexical",
        items=[lexical_item],
        metadata={"retrieval_input_manifest_hash": manifest_hash},
    ))
    vector = FakeRetriever(RetrievalChannelResult(
        "vector",
        items=[],
        metadata={
            "retrieval_input_manifest_hash": manifest_hash,
            "index_mode": "fast_numpy",
        },
    ))

    class RetrievalData:
        @staticmethod
        def excluded_by_policy():
            return []

    class ForbiddenReranker:
        def rerank(self, *args, **kwargs):
            raise AssertionError("不支持的查询不得进入 reranker")

    payload = hybrid_retrieval.context_pack(
        "How can today's best stock purchase be selected from a BGP routing table?",
        top_n=8,
        query_type="fact",
        require_model=True,
        reranker=ForbiddenReranker(),
        lexical_retriever=lexical,
        dense_retriever=vector,
        trusted_chunk_ids=set(),
        eligible_doc_ids=set(),
        retrieval_data=RetrievalData(),
    )

    assert payload["results"] == []
    assert payload["rerank_status"] == "empty"
    assert payload["channel_metadata"]["vector"]["index_mode"] == "fast_numpy"
    assert payload["query_scope"] == {
        "policy_version": "query_scope_v1",
        "status": "unsupported",
        "rule_id": "unsupported_financial_recommendation",
        "reason": "知识库不支持由 BGP 数据推导投资建议",
    }


def test_context_pack_uses_the_same_normalized_query_for_recall_and_rerank(monkeypatch):
    candidate = _channel_item("rfc6811-state", 1, 1.0)
    candidate.update({"doc_id": "rfc6811", "source_ref": "rfc6811#state"})
    monkeypatch.setattr(hybrid_retrieval, "search", lambda *args, **kwargs: {
        "query": "ROV 会把路由起源有效性分成哪些状态？",
        "normalized_query": "ROV 会把路由起源有效性分成哪些状态？ route origin validation RFC6811",
        "results": [candidate],
        "channel_metadata": {},
        "lexical_count": 1,
        "vector_count": 1,
        "vector_status": "complete",
        "degraded": False,
    })
    monkeypatch.setattr(hybrid_retrieval, "_build_structured_context", lambda *args, **kwargs: {
        "context_units": [],
        "evidence": [],
        "context_groups": [],
        "trim_events": [],
    })

    class RetrievalData:
        @staticmethod
        def excluded_by_policy():
            return []

    class CapturingReranker:
        query = None

        def rerank(self, query, documents, top_n, require_model=False):
            self.query = query
            return {
                "ok": True,
                "provider": "fake",
                "model": "BAAI/bge-reranker-v2-m3",
                "revision": "rev",
                "results": [{"index": 0, "relevance_score": 0.9}],
            }

    reranker = CapturingReranker()
    hybrid_retrieval.context_pack(
        "ROV 会把路由起源有效性分成哪些状态？",
        top_n=8,
        query_type="fact",
        require_model=True,
        reranker=reranker,
        retrieval_data=RetrievalData(),
    )

    assert reranker.query.endswith("route origin validation RFC6811")


def test_single_failure_degrades_and_double_failure_raises():
    failed_lexical = FakeRetriever(RetrievalChannelResult(
        "lexical", error={"code": "bm25_unavailable", "message": "broken"},
    ))
    vector = FakeRetriever(RetrievalChannelResult("vector", items=[_channel_item("a", 1, 0.8)]))

    payload = hybrid_retrieval.search(
        "BGP",
        lexical_retriever=failed_lexical,
        dense_retriever=vector,
        trusted_chunk_ids=set(),
        eligible_doc_ids=set(),
    )

    assert payload["degraded"] is True
    assert payload["channel_errors"]["lexical"]["code"] == "bm25_unavailable"
    assert payload["results"][0]["chunk_id"] == "a"

    failed_vector = FakeRetriever(RetrievalChannelResult(
        "vector", error={"code": "embedding_unavailable", "message": "broken"},
    ))
    with __import__("pytest").raises(hybrid_retrieval.RetrievalUnavailable):
        hybrid_retrieval.search(
            "BGP",
            lexical_retriever=failed_lexical,
            dense_retriever=failed_vector,
            trusted_chunk_ids=set(),
            eligible_doc_ids=set(),
        )


def test_default_context_store_is_reused_until_catalog_changes(tmp_path, monkeypatch):
    data_dir = tmp_path / "release" / "data"
    chunk_catalog = data_dir / "published" / "chunk_catalog.jsonl"
    section_catalog = tmp_path / "section_catalog.jsonl"
    chunk_catalog.parent.mkdir(parents=True)
    chunk_catalog.write_text('{"chunk_id":"c1"}\n', encoding="utf-8")
    section_catalog.write_text('{"section_id":"s"}\n', encoding="utf-8")

    class CountingChunkStore:
        calls = []

        def __init__(self, project_root, chunk_catalog_path, section_catalog_path):
            self.calls.append((Path(project_root), Path(chunk_catalog_path), Path(section_catalog_path)))

        def get_chunk(self, chunk_id):
            return {
                "chunk_id": chunk_id,
                "doc_id": "doc",
                "parent_section_id": "s",
                "section_path": ["Root"],
                "chunk_order": 0,
                "content": "alpha",
                "source_ref": "doc#1",
                "source_block_ids": ["b1"],
            }

        def get_section(self, section_id):
            return {
                "section_id": section_id,
                "doc_id": "doc",
                "heading": "Root",
                "section_path": ["Root"],
            }

        def get_section_direct_chunks(self, section_id):
            return [self.get_chunk("c1")]

        def get_section_subtree_chunks(self, section_id):
            return self.get_section_direct_chunks(section_id)

    monkeypatch.setenv("BGPKB_DATA_DIR", str(data_dir))
    monkeypatch.setattr(hybrid_retrieval, "_default_section_catalog_path", lambda retrieval_data: section_catalog)
    monkeypatch.setattr(hybrid_retrieval, "ChunkStore", CountingChunkStore)
    hybrid_retrieval.clear_context_store_cache()

    results = [{"chunk_id": "c1", "rerank_score": 0.9}]
    first_units, first_trim = hybrid_retrieval._build_context_units("q", results, "fact", 6000)
    second_units, second_trim = hybrid_retrieval._build_context_units("q", results, "fact", 6000)

    assert [unit["included_chunk_ids"] for unit in first_units] == [["c1"]]
    assert [unit["included_chunk_ids"] for unit in second_units] == [["c1"]]
    assert first_trim == []
    assert second_trim == []
    assert len(CountingChunkStore.calls) == 1

    chunk_catalog.write_text('{"chunk_id":"c1"}\n{"chunk_id":"c2"}\n', encoding="utf-8")
    os.utime(chunk_catalog, None)
    hybrid_retrieval._build_context_units("q", results, "fact", 6000)

    assert len(CountingChunkStore.calls) == 2


def test_v1_retrieval_framework_search_remains_available():
    payload = retrieval_framework.search("route leak", limit=1)
    assert isinstance(payload, list)
    assert payload and payload[0]["retrieval_method"] in {"sqlite_fts5", "mock_hybrid"}
