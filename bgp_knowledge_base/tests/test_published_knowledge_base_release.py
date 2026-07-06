import json

import pytest

from bgpkb.pipeline import build_published_knowledge_base as published
from bgpkb.pipeline import build_sqlite_knowledge_base as sqlite_builder


def _resolved_chunk(chunk_id="chunk-v2-a", **overrides):
    row = {
        "schema_version": "chunk_v2_hierarchical", "chunk_id": chunk_id, "doc_id": "doc-a",
        "source_type": "standard", "chunk_type": "document", "topics": [],
        "content": "approved v2 content", "review_status": "approved", "source_ref": "raw.pdf#p1",
        "source_block_ids": ["block-a"], "section_path": ["A"], "parent_section_id": "section-a",
        "chunk_order": 0, "previous_chunk_id": None, "next_chunk_id": None, "hierarchy_status": "resolved",
    }
    row.update(overrides)
    return row


def _section(**overrides):
    row = {
        "schema_version": "section_catalog_v1", "section_id": "section-a",
        "content_hash": "sha256:x", "doc_id": "doc-a", "heading": "A",
        "section_path": ["A"], "section_order": 0, "parent_section_id": None,
        "child_section_ids": [], "previous_section_id": None, "next_section_id": None,
        "source_ref": "raw.pdf#p1", "child_chunk_ids": ["chunk-v2-a"],
        "block_ids": ["block-a"], "content_chars": 10, "estimated_tokens": 3,
    }
    row.update(overrides)
    return row


def test_published_chunk_catalog_resolves_active_release(tmp_path):
    chunks = tmp_path / "data/corpus/chunks_v2"
    chunks.mkdir(parents=True)
    (chunks / "doc-a.jsonl").write_text(
        json.dumps(
            _resolved_chunk()
        )
        + "\n",
        encoding="utf-8",
    )
    pointer = tmp_path / "metadata/config/corpus_release_pointer.json"
    pointer.parent.mkdir(parents=True)
    pointer.write_text(
        json.dumps(
            {
                "active": {
                    "version": "v2",
                    "authority": "data/corpus/cleaned_blocks_v2",
                    "markdown": "data/corpus/markdown_v2",
                    "chunks": "data/corpus/chunks_v2",
                    "input_snapshot": "sha256:v2-snapshot",
                }
            }
        ),
        encoding="utf-8",
    )

    active = published.resolve_active_release(pointer, project_root=tmp_path)
    catalog = published.build_chunk_catalog(
        active["chunks_path"],
        corpus_version="v2",
        section_records=[_section()],
        project_root=tmp_path,
        sources_by_doc={
            "doc-a": {
                "source_type": "standard",
                "title": "RFC fixture",
                "language": "en",
            }
        },
    )

    assert active["manifest"]["version"] == "v2"
    assert active["manifest"]["input_snapshot"] == "sha256:v2-snapshot"
    assert [row["chunk_id"] for row in catalog] == ["chunk-v2-a"]
    assert catalog[0]["chunk_file"] == "data/corpus/chunks_v2/doc-a.jsonl"
    assert catalog[0]["source_type"] == "standard"
    assert catalog[0]["title"] == "RFC fixture"
    assert catalog[0]["parent_section_id"] == "section-a"


def test_v2_catalog_isolates_unresolved_chunks_and_reports_diagnostics(tmp_path):
    chunks = tmp_path / "chunks"
    chunks.mkdir()
    unresolved = _resolved_chunk("chunk-unresolved", hierarchy_status="unresolved", parent_section_id=None)
    (chunks / "doc-a.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in [_resolved_chunk(), unresolved]), encoding="utf-8"
    )
    diagnostics = {}

    catalog = published.build_chunk_catalog(
        chunks, project_root=tmp_path, corpus_version="v2", section_records=[_section()], diagnostics=diagnostics,
    )

    assert [row["chunk_id"] for row in catalog] == ["chunk-v2-a"]
    assert diagnostics == {
        "published_resolved_count": 1,
        "isolated_unresolved_count": 1,
        "isolated_reasons": {"hierarchy_status_unresolved": 1},
        "hierarchy_integrity": "pass",
    }


@pytest.mark.parametrize(
    ("chunk", "message"),
    [
        (_resolved_chunk(source_block_ids=None), "source_block_ids"),
        (_resolved_chunk(hierarchy_status="unknown"), "hierarchy_status"),
    ],
)
def test_v2_catalog_rejects_invalid_chunks_instead_of_isolating_them(tmp_path, chunk, message):
    chunks = tmp_path / "chunks"
    chunks.mkdir()
    (chunks / "doc-a.jsonl").write_text(json.dumps(chunk) + "\n", encoding="utf-8")
    diagnostics = {}

    with pytest.raises(ValueError, match=message):
        published.build_chunk_catalog(
            chunks,
            project_root=tmp_path,
            corpus_version="v2",
            section_records=[_section()],
            diagnostics=diagnostics,
        )

    assert diagnostics.get("hierarchy_integrity") != "pass"


def test_unresolved_chunk_reusing_resolved_id_is_not_reintroduced(tmp_path):
    chunks = tmp_path / "chunks"
    chunks.mkdir()
    unresolved = _resolved_chunk(hierarchy_status="unresolved", parent_section_id=None)
    (chunks / "doc-a.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in [_resolved_chunk(), unresolved]), encoding="utf-8"
    )

    catalog = published.build_chunk_catalog(
        chunks, project_root=tmp_path, corpus_version="v2", section_records=[_section()],
    )

    assert [row["chunk_id"] for row in catalog] == ["chunk-v2-a"]


@pytest.mark.parametrize(
    ("chunks", "sections", "message"),
    [
        ([_resolved_chunk(), _resolved_chunk("duplicate", chunk_order=0, previous_chunk_id="chunk-v2-a")], [_section(child_chunk_ids=["chunk-v2-a", "duplicate"])], "chunk_order"),
        ([_resolved_chunk(previous_chunk_id="other")], [_section()], "邻接"),
        ([_resolved_chunk()], [_section(doc_id="doc-b")], "跨文档"),
        ([_resolved_chunk()], [_section(child_chunk_ids=[])], "child_chunk_ids"),
        ([_resolved_chunk(), _resolved_chunk()], [_section()], "重复 chunk_id"),
    ],
)
def test_v2_catalog_rejects_broken_resolved_hierarchy(tmp_path, chunks, sections, message):
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir()
    (chunk_dir / "chunks.jsonl").write_text("".join(json.dumps(row) + "\n" for row in chunks), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        published.build_chunk_catalog(
            chunk_dir, project_root=tmp_path, corpus_version="v2", section_records=sections,
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"section_path": "A"}, "section_path"),
        ({"source_block_ids": "block-a"}, "source_block_ids"),
        ({"chunk_order": False}, "chunk_order"),
    ],
)
def test_v2_catalog_validates_chunk_schema_types(tmp_path, overrides, message):
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir()
    chunk = _resolved_chunk(**overrides)
    (chunk_dir / "doc-a.jsonl").write_text(json.dumps(chunk) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        published.build_chunk_catalog(
            chunk_dir, project_root=tmp_path, corpus_version="v2", section_records=[_section()],
        )


def test_v2_catalog_validates_section_schema_types(tmp_path):
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir()
    (chunk_dir / "doc-a.jsonl").write_text(json.dumps(_resolved_chunk()) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="section_path"):
        published.build_chunk_catalog(
            chunk_dir,
            project_root=tmp_path,
            corpus_version="v2",
            section_records=[_section(section_path="A")],
        )


def test_v2_catalog_validates_unresolved_chunk_schema_before_isolation(tmp_path):
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir()
    chunk = _resolved_chunk(
        hierarchy_status="unresolved", parent_section_id=None, source_block_ids="block-a",
    )
    (chunk_dir / "doc-a.jsonl").write_text(json.dumps(chunk) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="source_block_ids"):
        published.build_chunk_catalog(
            chunk_dir, project_root=tmp_path, corpus_version="v2", section_records=[_section()],
        )


@pytest.mark.parametrize("cross_document", [False, True])
def test_v2_catalog_rejects_broken_section_parent_child_tree(tmp_path, cross_document):
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir()
    (chunk_dir / "doc-a.jsonl").write_text(json.dumps(_resolved_chunk()) + "\n", encoding="utf-8")
    root = _section(child_section_ids=["section-b"], next_section_id="section-b")
    child = _section(
        section_id="section-b",
        doc_id="doc-b" if cross_document else "doc-a",
        section_order=1,
        parent_section_id="section-a" if cross_document else None,
        previous_section_id="section-a",
        child_chunk_ids=[],
        block_ids=["block-b"],
    )

    with pytest.raises(ValueError, match="跨文档" if cross_document else "互反"):
        published.build_chunk_catalog(
            chunk_dir,
            project_root=tmp_path,
            corpus_version="v2",
            section_records=[root, child],
        )


def test_v1_catalog_keeps_legacy_chunks_without_hierarchy(tmp_path):
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir()
    (chunk_dir / "legacy.jsonl").write_text(json.dumps({"chunk_id": "legacy", "doc_id": "doc-a", "content": "old"}) + "\n")

    catalog = published.build_chunk_catalog(chunk_dir, project_root=tmp_path, corpus_version="v1")

    assert [row["chunk_id"] for row in catalog] == ["legacy"]
    assert "parent_section_id" not in catalog[0]


def test_chunk_catalog_rejects_unknown_corpus_version(tmp_path):
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir()

    with pytest.raises(ValueError, match="corpus_version"):
        published.build_chunk_catalog(chunk_dir, project_root=tmp_path, corpus_version="v3")


def test_resolved_v2_chunk_with_wrong_schema_version_is_broken(tmp_path):
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir()
    chunk = _resolved_chunk(schema_version="chunk_v1")
    (chunk_dir / "doc-a.jsonl").write_text(json.dumps(chunk) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="schema_version"):
        published.build_chunk_catalog(
            chunk_dir, project_root=tmp_path, corpus_version="v2", section_records=[_section()],
        )


@pytest.mark.parametrize(
    ("corpus_version", "contains_section_catalog"),
    [("v2", True), ("v1", False)],
)
def test_manifest_inputs_register_section_catalog_only_for_v2(
    corpus_version, contains_section_catalog,
):
    inputs = published.build_manifest_inputs({
        "version": corpus_version,
        "chunks": f"data/corpus/chunks_{corpus_version}",
    })

    assert ("data/derived/datasets/section_catalog.jsonl" in inputs) is contains_section_catalog


def test_publish_report_records_hierarchy_integrity_and_isolation(monkeypatch, tmp_path):
    report = tmp_path / "report.md"
    monkeypatch.setattr(published, "REPORT", report)
    published.write_report({
        "corpus_version": "v2", "corpus_input_snapshot": "sha256:x", "outputs": [],
        "counts": {"published_resolved_chunks": 3, "isolated_unresolved_chunks": 1},
        "hierarchy_integrity": "pass",
        "hierarchy_isolation_reasons": {"hierarchy_status_unresolved": 1},
    })

    text = report.read_text(encoding="utf-8")
    assert "层级完整性：pass" in text
    assert "hierarchy_status_unresolved：1" in text


def test_published_jsonl_writer_replaces_output_atomically(monkeypatch, tmp_path):
    output = tmp_path / "catalog.jsonl"
    replacements = []
    original_replace = published.os.replace
    monkeypatch.setattr(
        published.os, "replace",
        lambda source, target: (replacements.append((source, target)), original_replace(source, target))[1],
    )

    published.write_jsonl(output, [{"id": "a"}])

    assert output.read_text(encoding="utf-8") == '{"id": "a"}\n'
    assert len(replacements) == 1
    assert replacements[0][1] == output


def test_historical_review_evidence_is_segregated_from_active_chunks():
    rows = sqlite_builder.build_historical_evidence_chunks(
        [
            {
                "chunk_id": "legacy-chunk-a",
                "chunk_file": "data/corpus/chunks/paper_chunks.jsonl",
                "doc_id": "doc-a",
                "source_ref": "data/sources/raw/doc-a.pdf#page-1",
                "chunk_type": "paper_method_source",
            },
            {
                "chunk_id": "legacy-chunk-a",
                "chunk_file": "data/corpus/chunks/paper_chunks.jsonl",
                "doc_id": "doc-a",
                "source_ref": "data/sources/raw/doc-a.pdf#page-1",
                "chunk_type": "paper_method_source",
            },
        ],
        corpus_version="v1",
    )

    assert rows == [
        {
            "chunk_id": "legacy-chunk-a",
            "chunk_file": "data/corpus/chunks/paper_chunks.jsonl",
            "doc_id": "doc-a",
            "source_ref": "data/sources/raw/doc-a.pdf#page-1",
            "chunk_type": "paper_method_source",
            "corpus_version": "v1",
        }
    ]
