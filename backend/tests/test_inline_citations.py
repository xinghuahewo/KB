from bgpkb.retrieval.inline_citations import (
    IncrementalCitationParser,
    complete_sentence,
    enrich_citations,
    parse_answer,
)


class FakeStore:
    def get_chunk(self, chunk_id):
        return {
            "chunk_id": chunk_id,
            "doc_id": "rfc6811",
            "title": "RFC 6811",
            "parent_section_id": "section-1",
            "parent_section_heading": "Introduction",
            "content": (
                "The Resource Public Key Infrastructure is a trusted repository for certificates "
                "that bind IP prefixes to owning ASes, called Route Origin Authorizations (ROAs). "
                "Routers can validate announcements against these records."
            ),
        }


def test_enriched_citation_uses_stable_id_release_and_complete_roa_sentence(monkeypatch):
    monkeypatch.setenv("BGPKB_RELEASE_ID", "release-2026-07")
    pack = {
        "results": [{"chunk_id": "chunk-rpki", "title": "RPKI", "content_preview": "called Rou…"}],
        "context_units": [],
        "citations": [{"chunk_id": "chunk-rpki", "source_ref": "rfc6811#section-1"}],
    }

    citations = enrich_citations(pack, store=FakeStore())

    assert citations[0]["citation_id"] == "ev_1"
    assert citations[0]["source_id"] == "rfc6811"
    assert citations[0]["section_id"] == "section-1"
    assert citations[0]["release_id"] == "release-2026-07"
    assert "Route Origin Authorizations (ROAs)" in citations[0]["content_preview"]
    assert not citations[0]["content_preview"].endswith("…")


def test_incremental_parser_handles_unicode_and_marker_split_across_chunks():
    parser = IncrementalCitationParser({"ev_1"})

    tokens = []
    for delta in ["RPKI 可验", "证路由[[ci", "te:ev_", "1]]。"]:
        tokens.extend(parser.feed(delta))
    tokens.extend(parser.finish())

    assert tokens == [
        {"type": "text", "text": "RPKI 可验"},
        {"type": "text", "text": "证路由"},
        {"type": "citation", "citation_ids": ["ev_1"]},
        {"type": "text", "text": "。"},
    ]
    assert parser.status == "complete"


def test_unknown_and_unclosed_markers_never_leak_as_clickable_or_raw_control_text():
    answer, parts, status = parse_answer(
        "合法说明[[cite:ev_404]]尾部[[cite:ev_1",
        [{"citation_id": "ev_1"}],
    )

    assert answer == "合法说明尾部"
    assert all(part["type"] != "citation" for part in parts)
    assert "[[cite:" not in answer
    assert status == "incomplete"


def test_parse_answer_returns_compatible_text_and_structured_parts():
    answer, parts, status = parse_answer(
        "ROA 绑定前缀与起源 AS[[cite:ev_1]]。",
        [{"citation_id": "ev_1"}],
    )

    assert answer == "ROA 绑定前缀与起源 AS[1]。"
    assert parts[1] == {"type": "citation", "citation_ids": ["ev_1"], "label": "1"}
    assert status == "complete"


def test_complete_sentence_does_not_cut_at_fixed_preview_boundary():
    full = "First sentence. The mechanism is called Route Origin Authorization (ROA). Last sentence."
    assert complete_sentence(full, "The mechanism is called Rou…") == (
        "The mechanism is called Route Origin Authorization (ROA)."
    )
