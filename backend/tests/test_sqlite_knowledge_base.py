import json
import sqlite3

from bgpkb.pipeline import build_sqlite_knowledge_base as builder

from test_retrieval_document_v1_gold import _eligibility, _governance, _semantic_chunk


def test_candidate_release_id_prefers_pipeline_release_environment(monkeypatch):
    monkeypatch.setenv("BGPKB_RELEASE_ID", "candidate-release-v2")

    assert builder._candidate_release_id(
        {"release_id": "stale-inner-release"}
    ) == "candidate-release-v2"


def _catalog_chunk(**overrides):
    row = {
        "chunk_id": "chunk-a", "doc_id": "doc-a", "title": "BGP hierarchy",
        "source_type": "standard", "chunk_type": "paragraph", "topics": ["BGP"],
        "section_path": ["A", "B"], "source_ref": "raw.pdf#p1", "language": "en",
        "review_status": "approved", "content_chars": 12, "content_preview": "route hierarchy",
        "chunk_file": "data/corpus/chunks_v2/doc-a.jsonl", "schema_version": "chunk_v2_hierarchical",
        "parent_section_id": "section-a", "chunk_order": 0, "previous_chunk_id": None,
        "next_chunk_id": None, "hierarchy_status": "resolved", "source_block_ids": ["block-a"],
    }
    row.update(overrides)
    return row


def _database():
    conn = sqlite3.connect(":memory:")
    conn.executescript(builder.SCHEMA)
    return conn


def test_chunks_schema_and_v2_hierarchy_values_are_persisted():
    conn = _database()
    builder.insert_chunks(conn, [_catalog_chunk()], False)

    columns = {row[1] for row in conn.execute("PRAGMA table_info(chunks)")}
    assert {
        "schema_version", "section_path_json", "parent_section_id", "chunk_order",
        "previous_chunk_id", "next_chunk_id", "hierarchy_status", "source_block_ids_json",
    } <= columns
    row = conn.execute(
        "SELECT schema_version, section_path_json, parent_section_id, chunk_order, "
        "previous_chunk_id, next_chunk_id, hierarchy_status, source_block_ids_json FROM chunks"
    ).fetchone()
    assert row == (
        "chunk_v2_hierarchical", json.dumps(["A", "B"], ensure_ascii=False, sort_keys=True),
        "section-a", 0, None, None, "resolved",
        json.dumps(["block-a"], ensure_ascii=False, sort_keys=True),
    )


def test_v1_chunks_get_compatible_hierarchy_defaults_but_preview_is_not_indexed():
    conn = _database()
    fts_enabled = builder.create_fts_tables(conn)
    legacy = _catalog_chunk()
    for field in (
        "schema_version", "section_path", "parent_section_id", "chunk_order",
        "previous_chunk_id", "next_chunk_id", "hierarchy_status", "source_block_ids",
    ):
        legacy.pop(field, None)
    builder.insert_chunks(conn, [legacy], fts_enabled)

    assert conn.execute(
        "SELECT schema_version, section_path_json, parent_section_id, chunk_order, "
        "previous_chunk_id, next_chunk_id, hierarchy_status, source_block_ids_json FROM chunks"
    ).fetchone() == ("", "[]", None, None, None, None, "", "[]")
    if fts_enabled:
        assert conn.execute("SELECT chunk_id FROM chunk_fts WHERE chunk_fts MATCH 'hierarchy'").fetchone() is None


def test_fts5_indexes_only_complete_current_retrieval_text_and_records_manifest():
    from bgpkb.indexing.retrieval_documents import (
        build_retrieval_input_manifest,
        derive_retrieval_document,
    )

    chunk = _semantic_chunk(content="开头展示内容。" + "中间内容。" * 80 + "尾部唯一检索词 bgp_tail_signal")
    document = derive_retrieval_document(
        chunk, eligibility=_eligibility(), governance=_governance(chunk)
    )
    manifest = build_retrieval_input_manifest([document])
    conn = _database()
    fts_enabled = builder.create_fts_tables(conn)
    if not fts_enabled:
        return

    builder.insert_retrieval_documents(conn, [document], manifest, fts_enabled=True)

    fts_columns = [row[1] for row in conn.execute("PRAGMA table_info(chunk_fts)")]
    assert fts_columns == ["retrieval_doc_id", "chunk_id", "retrieval_text"]
    assert conn.execute(
        "SELECT chunk_id FROM chunk_fts WHERE chunk_fts MATCH 'bgp_tail_signal'"
    ).fetchone() == (chunk["chunk_id"],)
    assert conn.execute(
        "SELECT value FROM meta WHERE key = 'fts_input_manifest_hash'"
    ).fetchone() == (manifest["input_manifest_hash"],)
