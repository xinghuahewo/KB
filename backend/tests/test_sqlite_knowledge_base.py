import json
import sqlite3

from bgpkb.pipeline import build_sqlite_knowledge_base as builder


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


def test_v1_chunks_get_compatible_hierarchy_defaults_and_fts_remains_queryable():
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
        assert conn.execute("SELECT chunk_id FROM chunk_fts WHERE chunk_fts MATCH 'hierarchy'").fetchone() == ("chunk-a",)
