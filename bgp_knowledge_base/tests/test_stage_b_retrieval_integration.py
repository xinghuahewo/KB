from bgpkb.service import hybrid_retrieval
from bgpkb.service.retrievers import RetrievalChannelResult


class FakeRetriever:
    def __init__(self, channel, items):
        self.result = RetrievalChannelResult(channel, items=items)

    def search(self, query, top_k):
        return self.result


class FakeReranker:
    def rerank(self, query, documents, top_n, require_model=False):
        return {
            "ok": True,
            "provider": "fake_reranker",
            "model": "BAAI/bge-reranker-v2-m3",
            "results": [
                {"index": 1, "relevance_score": 0.95},
                {"index": 0, "relevance_score": 0.9},
            ][:top_n],
        }


class FakeQueryTypeClient:
    def classify_query_type(self, query, prompt_version):
        return {
            "ok": True,
            "provider": "deepseek",
            "model": "deepseek-chat",
            "query_type": "procedure",
            "reason": "流程问题",
        }


class FakeStore:
    def __init__(self):
        self.chunks = {
            "c1": {
                "chunk_id": "c1", "doc_id": "doc", "parent_section_id": "s",
                "section_path": ["Root", "Procedure"], "title": "Procedure",
                "chunk_order": 0, "content": "step one", "source_ref": "doc#1",
                "source_block_ids": ["b1"],
            },
            "c2": {
                "chunk_id": "c2", "doc_id": "doc", "parent_section_id": "s",
                "section_path": ["Root", "Procedure"], "title": "Procedure",
                "chunk_order": 1, "content": "step two", "source_ref": "doc#2",
                "source_block_ids": ["b2"],
            },
        }
        self.section = {
            "section_id": "s", "doc_id": "doc", "heading": "Procedure",
            "section_path": ["Root", "Procedure"], "child_chunk_ids": ["c1", "c2"],
            "child_section_ids": [],
        }

    def get_chunk(self, chunk_id):
        return dict(self.chunks[chunk_id])

    def get_section(self, section_id):
        return dict(self.section)

    def get_section_direct_chunks(self, section_id):
        return [self.get_chunk("c1"), self.get_chunk("c2")]

    def get_section_subtree_chunks(self, section_id):
        return self.get_section_direct_chunks(section_id)


def _item(chunk_id, rank, score):
    return {
        "chunk_id": chunk_id,
        "doc_id": "doc",
        "raw_rank": rank,
        "raw_score": score,
        "score": score,
        "content_preview": chunk_id,
        "source_ref": f"doc#{chunk_id}",
    }


def test_stage_b_fake_provider_context_pack_chain_is_not_patched_apart():
    pack = hybrid_retrieval.context_pack(
        "如何执行流程",
        top_n=5,
        query_type="auto",
        token_budget=6000,
        lexical_retriever=FakeRetriever("lexical", [_item("c1", 1, 4.0)]),
        dense_retriever=FakeRetriever("vector", [_item("c2", 1, 0.9)]),
        reranker=FakeReranker(),
        query_type_client=FakeQueryTypeClient(),
        store=FakeStore(),
    )

    assert pack["candidate_chunk_count"] == 2
    assert pack["reranked_chunk_count"] == 2
    assert pack["resolved_query_type"] == "procedure"
    assert pack["provider"] == "fake_reranker"
    assert pack["context_units"][0]["mode"] == "parent_span"
    assert pack["context_units"][0]["included_chunk_ids"] == ["c1", "c2"]
    assert pack["citations"] == [
        {"chunk_id": "c1", "source_ref": "doc#1"},
        {"chunk_id": "c2", "source_ref": "doc#2"},
    ]
