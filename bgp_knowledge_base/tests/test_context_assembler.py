from bgpkb.service.context_assembler import ContextAssembler


class FakeStore:
    def __init__(self, chunks, sections):
        self.chunks = {item["chunk_id"]: item for item in chunks}
        self.sections = {item["section_id"]: item for item in sections}

    def get_chunk(self, chunk_id):
        return dict(self.chunks[chunk_id])

    def get_section(self, section_id):
        return dict(self.sections[section_id])

    def get_section_direct_chunks(self, section_id):
        section = self.sections[section_id]
        return sorted(
            [self.get_chunk(chunk_id) for chunk_id in section["child_chunk_ids"]],
            key=lambda item: item["chunk_order"],
        )

    def get_section_subtree_chunks(self, section_id):
        section = self.sections[section_id]
        rows = self.get_section_direct_chunks(section_id)
        for child_id in section.get("child_section_ids", []):
            rows.extend(self.get_section_subtree_chunks(child_id))
        return sorted(rows, key=lambda item: (item["section_path"], item["chunk_order"]))


class WordCounter:
    def count(self, text):
        from bgpkb.service.token_budget import TokenCount
        return TokenCount(tokens=max(1, len(text.split())), estimated=True, method="word_test")


class FakeSummarizer:
    def __init__(self):
        self.calls = []

    def summarize_context(self, query, context, max_tokens, prompt_version):
        self.calls.append((query, context, max_tokens, prompt_version))
        return {"ok": True, "provider": "deepseek", "model": "deepseek-chat", "summary": "压缩摘要"}


def _chunk(chunk_id, section="s1", order=0, content=None, blocks=None, doc="doc-a"):
    return {
        "chunk_id": chunk_id,
        "doc_id": doc,
        "parent_section_id": section,
        "section_path": ["Root", section],
        "title": f"Heading {section}",
        "chunk_order": order,
        "content": content or f"content {chunk_id}",
        "source_ref": f"{doc}#{chunk_id}",
        "source_block_ids": blocks or [f"block-{chunk_id}"],
    }


def _section(section_id, chunk_ids, children=None, doc="doc-a"):
    return {
        "section_id": section_id,
        "doc_id": doc,
        "heading": f"Heading {section_id}",
        "section_path": ["Root", section_id],
        "child_chunk_ids": chunk_ids,
        "child_section_ids": children or [],
        "estimated_tokens": 10,
    }


def _hit(chunk_id, score=0.9, section="s1", doc="doc-a"):
    return {
        "chunk_id": chunk_id,
        "doc_id": doc,
        "parent_section_id": section,
        "rerank_score": score,
        "rerank_rank": 1,
    }


def test_fact_uses_hit_chunk_with_one_sibling_window_and_exact_citations():
    chunks = [_chunk("c0", order=0), _chunk("c1", order=1), _chunk("c2", order=2)]
    store = FakeStore(chunks, [_section("s1", ["c0", "c1", "c2"])])

    pack = ContextAssembler(store, token_counter=WordCounter()).build(
        query="什么是 route leak",
        reranked_chunks=[_hit("c1")],
        query_type="fact",
        token_budget=6000,
    )

    unit = pack["context_units"][0]
    assert unit["mode"] == "matched_chunk"
    assert unit["parent_section_heading"] == "Heading s1"
    assert unit["included_chunk_ids"] == ["c0", "c1", "c2"]
    assert unit["citations"] == [
        {"chunk_id": "c0", "source_ref": "doc-a#c0"},
        {"chunk_id": "c1", "source_ref": "doc-a#c1"},
        {"chunk_id": "c2", "source_ref": "doc-a#c2"},
    ]


def test_procedure_promotes_same_parent_hits_to_parent_span_and_fills_small_gap():
    chunks = [_chunk(f"c{i}", order=i) for i in range(5)]
    store = FakeStore(chunks, [_section("s1", [f"c{i}" for i in range(5)])])

    pack = ContextAssembler(store, token_counter=WordCounter()).build(
        query="如何排查",
        reranked_chunks=[_hit("c1", 0.9), _hit("c3", 0.8)],
        query_type="procedure",
        token_budget=6000,
    )

    unit = pack["context_units"][0]
    assert unit["mode"] == "parent_span"
    assert unit["included_chunk_ids"] == ["c0", "c1", "c2", "c3", "c4"]
    assert unit["max_rerank_score"] == 0.9


def test_policy_small_section_can_use_full_section_subtree():
    chunks = [
        _chunk("p0", section="policy", order=0, content="must not leak"),
        _chunk("child0", section="child", order=0, content="child rule"),
    ]
    sections = [
        _section("policy", ["p0"], children=["child"]),
        _section("child", ["child0"]),
    ]
    store = FakeStore(chunks, sections)

    pack = ContextAssembler(store, token_counter=WordCounter()).build(
        query="RFC 约束",
        reranked_chunks=[_hit("p0", section="policy")],
        query_type="policy",
        token_budget=6000,
    )

    unit = pack["context_units"][0]
    assert unit["mode"] == "full_section"
    assert unit["included_chunk_ids"] == ["child0", "p0"]


def test_global_summarizes_only_when_original_units_exceed_budget():
    chunks = [
        _chunk("g0", section="g", order=0, content="alpha beta gamma delta epsilon"),
        _chunk("g1", section="g", order=1, content="zeta eta theta iota kappa"),
    ]
    store = FakeStore(chunks, [_section("g", ["g0", "g1"])])
    summarizer = FakeSummarizer()

    pack = ContextAssembler(store, token_counter=WordCounter(), summarizer=summarizer).build(
        query="总结",
        reranked_chunks=[_hit("g0", 0.9, "g"), _hit("g1", 0.8, "g")],
        query_type="global",
        token_budget=3,
    )

    unit = pack["context_units"][0]
    assert unit["mode"] == "summary"
    assert unit["content"] == "压缩摘要"
    assert unit["included_chunk_ids"] == ["g0", "g1"]
    assert summarizer.calls and summarizer.calls[0][2] == 400


def test_context_assembler_deduplicates_equal_block_sets_before_budget_trimming():
    chunks = [
        _chunk("dup-low", order=0, blocks=["same"], content="low"),
        _chunk("dup-high", order=1, blocks=["same"], content="high"),
        _chunk("other", order=2, blocks=["other"], content="other"),
    ]
    store = FakeStore(chunks, [_section("s1", ["dup-low", "dup-high", "other"])])

    pack = ContextAssembler(store, token_counter=WordCounter()).build(
        query="q",
        reranked_chunks=[_hit("dup-low", 0.1), _hit("dup-high", 0.9), _hit("other", 0.8)],
        query_type="fact",
        token_budget=6000,
    )

    assert pack["trim_events"][0]["event"] == "dedupe_by_block_set"
    included = pack["context_units"][0]["included_chunk_ids"]
    assert "dup-high" in included
    assert "dup-low" not in included


def test_context_id_is_deterministic_from_section_and_included_chunks():
    chunks = [_chunk("c0", order=0), _chunk("c1", order=1)]
    store = FakeStore(chunks, [_section("s1", ["c0", "c1"])])
    assembler = ContextAssembler(store, token_counter=WordCounter())

    first = assembler.build("q", [_hit("c0")], "fact", 6000)["context_units"][0]["context_id"]
    second = assembler.build("q", [_hit("c0")], "fact", 6000)["context_units"][0]["context_id"]

    assert first == second
    assert first.startswith("context_unit_")
    assert len(first.split("_")[-1]) == 16
