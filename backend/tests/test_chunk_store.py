import json

import pytest

from bgpkb.retrieval.chunk_store import ChunkStore, ChunkStoreError


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def test_chunk_store_lazily_loads_chunk_files_and_caches_them(tmp_path):
    chunk_file = tmp_path / "data" / "corpus" / "chunks_v2" / "doc.jsonl"
    _write_jsonl(chunk_file, [
        {"chunk_id": "c1", "content": "alpha", "chunk_order": 1},
        {"chunk_id": "c2", "content": "beta", "chunk_order": 2},
    ])
    catalog = tmp_path / "data" / "published" / "chunk_catalog.jsonl"
    _write_jsonl(catalog, [
        {"chunk_id": "c1", "chunk_file": "data/corpus/chunks_v2/doc.jsonl", "doc_id": "doc"},
        {"chunk_id": "c2", "chunk_file": "data/corpus/chunks_v2/doc.jsonl", "doc_id": "doc"},
    ])
    sections = tmp_path / "data" / "derived" / "datasets" / "section_catalog.jsonl"
    _write_jsonl(sections, [])

    store = ChunkStore(tmp_path, catalog, sections)

    assert store.get_chunk("c1")["content"] == "alpha"
    assert store.get_chunk("c2")["content"] == "beta"
    assert store.cache_stats()["loaded_chunk_files"] == 1


def test_chunk_store_rejects_path_escape_and_reports_missing_chunk(tmp_path):
    outside = tmp_path.parent / "outside.jsonl"
    outside.write_text('{"chunk_id":"evil","content":"no"}\n', encoding="utf-8")
    catalog = tmp_path / "chunk_catalog.jsonl"
    _write_jsonl(catalog, [{"chunk_id": "evil", "chunk_file": "../outside.jsonl"}])
    sections = tmp_path / "section_catalog.jsonl"
    _write_jsonl(sections, [])
    store = ChunkStore(tmp_path, catalog, sections)

    with pytest.raises(ChunkStoreError) as escaped:
        store.get_chunk("evil")
    with pytest.raises(ChunkStoreError) as missing:
        store.get_chunk("missing")

    assert escaped.value.code == "path_escape"
    assert missing.value.code == "chunk_not_found"


def test_chunk_store_reads_direct_chunks_and_section_subtree_in_order(tmp_path):
    chunk_file = tmp_path / "chunks.jsonl"
    _write_jsonl(chunk_file, [
        {"chunk_id": "root-c", "content": "root", "chunk_order": 0},
        {"chunk_id": "child-c2", "content": "child2", "chunk_order": 2},
        {"chunk_id": "child-c1", "content": "child1", "chunk_order": 1},
    ])
    catalog = tmp_path / "chunk_catalog.jsonl"
    _write_jsonl(catalog, [
        {"chunk_id": "root-c", "chunk_file": "chunks.jsonl", "doc_id": "doc"},
        {"chunk_id": "child-c1", "chunk_file": "chunks.jsonl", "doc_id": "doc"},
        {"chunk_id": "child-c2", "chunk_file": "chunks.jsonl", "doc_id": "doc"},
    ])
    sections = tmp_path / "section_catalog.jsonl"
    _write_jsonl(sections, [
        {
            "section_id": "root",
            "child_section_ids": ["child"],
            "child_chunk_ids": ["root-c"],
            "section_order": 0,
        },
        {
            "section_id": "child",
            "child_section_ids": [],
            "child_chunk_ids": ["child-c2", "child-c1"],
            "section_order": 1,
        },
    ])
    store = ChunkStore(tmp_path, catalog, sections)

    assert [item["chunk_id"] for item in store.get_section_direct_chunks("root")] == ["root-c"]
    assert [item["chunk_id"] for item in store.get_section_subtree_chunks("root")] == [
        "root-c", "child-c1", "child-c2",
    ]


def test_chunk_store_reports_missing_section(tmp_path):
    catalog = tmp_path / "chunk_catalog.jsonl"
    sections = tmp_path / "section_catalog.jsonl"
    _write_jsonl(catalog, [])
    _write_jsonl(sections, [])

    with pytest.raises(ChunkStoreError) as error:
        ChunkStore(tmp_path, catalog, sections).get_section_direct_chunks("missing")

    assert error.value.code == "section_not_found"
