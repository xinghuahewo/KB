import copy
import json

import pytest

from bgpkb.cleaning_v2.derivation import build_derivatives
from bgpkb.pipeline import build_cleaning_v2_migration as migration


def _document(doc_id="doc-a"):
    block = {
        "block_id": "block-a", "doc_id": doc_id, "block_type": "paragraph",
        "heading_level": None, "reading_order": 0, "cleaned_text": "Stable body",
        "language": "en", "review_status": "approved", "asset_refs": [],
        "quality": {"confidence": 1.0, "ocr_used": False, "issues": []},
        "provenance": {"source_path": f"data/sources/raw/{doc_id}.txt", "source_anchor": "#/texts/0"},
    }
    return {
        "schema_version": "canonical_document_v2", "doc_id": doc_id,
        "source": {"source_path": f"data/sources/raw/{doc_id}.txt"},
        "parser_mode": "docling", "document_status": "approved",
        "blocks": [block], "assets": [], "transformations": [],
    }


def test_migration_builds_derivatives_diffs_terminal_records_and_chinese_report(tmp_path):
    authority = tmp_path / "authority" / "doc-a"
    authority.mkdir(parents=True)
    document = _document()
    (authority / "cleaned_document.json").write_text(json.dumps(document), encoding="utf-8")
    (authority / "parsed_document.json").write_text(json.dumps(document), encoding="utf-8")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    statuses = [
        {"doc_id": "doc-a", "state": "approved", "errors": [], "output_summary": {"fallback_used": False}},
        {"doc_id": "doc-b", "state": "quarantined", "errors": [{"error_type": "invalid_content"}], "output_summary": {"fallback_used": True}},
    ]
    (run_dir / "document_status.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in statuses), encoding="utf-8"
    )
    quarantine = run_dir / "work" / "doc-b"
    quarantine.mkdir(parents=True)
    (quarantine / "parsed_document.json").write_text(json.dumps(_document("doc-b")), encoding="utf-8")
    v1 = tmp_path / "v1"
    v1.mkdir()
    (v1 / "doc-a.md").write_text("Stable body\n", encoding="utf-8")

    result = migration.build_migration(
        authority_root=tmp_path / "authority", run_dir=run_dir, v1_markdown_root=v1,
        v1_chunks_root=tmp_path / "empty-chunks", parsed_root=tmp_path / "parsed_v2",
        markdown_root=tmp_path / "markdown_v2", assets_root=tmp_path / "assets_v2",
        chunks_root=tmp_path / "chunks_v2", dataset_path=tmp_path / "diffs.jsonl",
        report_path=tmp_path / "report.md", section_catalog_path=tmp_path / "sections.jsonl",
        expected_document_count=2,
    )

    assert result["terminal_count"] == 2
    assert (tmp_path / "parsed_v2" / "doc-a.json").is_file()
    assert (tmp_path / "parsed_v2" / "doc-b.json").is_file()
    assert (tmp_path / "markdown_v2" / "doc-a.md").is_file()
    records = [json.loads(line) for line in (tmp_path / "diffs.jsonl").read_text().splitlines()]
    assert {row["doc_id"] for row in records} == {"doc-a", "doc-b"}
    assert next(row for row in records if row["doc_id"] == "doc-b")["blocking_issues"] == ["quarantined_document"]
    assert "# Docling 清洗 v2 全量迁移报告" in (tmp_path / "report.md").read_text(encoding="utf-8")
    assert result["section_count"] == 1
    assert result["resolved_chunk_count"] == 1
    assert result["unresolved_chunk_count"] == 0
    assert result["hierarchy_resolution_rate"] == 1.0


def test_migration_applies_evidenced_approved_difference_decision(tmp_path):
    authority = tmp_path / "authority" / "doc-a"
    authority.mkdir(parents=True)
    document = _document()
    (authority / "cleaned_document.json").write_text(json.dumps(document), encoding="utf-8")
    (authority / "parsed_document.json").write_text(json.dumps(document), encoding="utf-8")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "document_status.jsonl").write_text(
        json.dumps({"doc_id": "doc-a", "state": "approved", "output_summary": {}}) + "\n",
        encoding="utf-8",
    )
    v1 = tmp_path / "v1"
    v1.mkdir()
    (v1 / "doc-a.md").write_text("Stable body removed legacy text\n", encoding="utf-8")
    decisions = tmp_path / "decisions.jsonl"
    decisions.write_text(
        json.dumps(
            {
                "doc_id": "doc-a",
                "decision": "approved",
                "reason_code": "reviewed_layout_difference",
                "evidence": {"v1_digest": "sha256:a", "v2_digest": "sha256:b"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = migration.build_migration(
        authority_root=tmp_path / "authority",
        run_dir=run_dir,
        v1_markdown_root=v1,
        v1_chunks_root=tmp_path / "empty-chunks",
        parsed_root=tmp_path / "parsed_v2",
        markdown_root=tmp_path / "markdown_v2",
        assets_root=tmp_path / "assets_v2",
        chunks_root=tmp_path / "chunks_v2",
        dataset_path=tmp_path / "diffs.jsonl",
        report_path=tmp_path / "report.md",
        section_catalog_path=tmp_path / "sections.jsonl",
        decisions_path=decisions,
        expected_document_count=1,
    )

    assert result["gate_pass_count"] == 1


def test_migration_writes_stable_cross_document_section_catalog(tmp_path):
    authority_root = tmp_path / "authority"
    statuses = []
    for doc_id in ("doc-b", "doc-a"):
        authority = authority_root / doc_id
        authority.mkdir(parents=True)
        document = _document(doc_id)
        document["blocks"] = [
            {**document["blocks"][0], "block_id": f"{doc_id}-h", "block_type": "heading", "heading_level": 1, "reading_order": 0, "cleaned_text": "章节"},
            {**document["blocks"][0], "block_id": f"{doc_id}-p", "reading_order": 1},
        ]
        (authority / "cleaned_document.json").write_text(json.dumps(document), encoding="utf-8")
        (authority / "parsed_document.json").write_text(json.dumps(document), encoding="utf-8")
        statuses.append({"doc_id": doc_id, "state": "approved", "output_summary": {}})
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "document_status.jsonl").write_text("".join(json.dumps(row) + "\n" for row in statuses), encoding="utf-8")

    kwargs = dict(
        authority_root=authority_root, run_dir=run_dir, v1_markdown_root=tmp_path / "v1",
        v1_chunks_root=tmp_path / "v1-chunks", parsed_root=tmp_path / "parsed",
        markdown_root=tmp_path / "markdown", assets_root=tmp_path / "assets",
        chunks_root=tmp_path / "chunks", dataset_path=tmp_path / "diff.jsonl",
        report_path=tmp_path / "report.md", section_catalog_path=tmp_path / "sections.jsonl",
        expected_document_count=2,
    )
    first = migration.build_migration(**kwargs)
    first_bytes = (tmp_path / "sections.jsonl").read_bytes()
    second = migration.build_migration(**kwargs)

    sections = [json.loads(line) for line in first_bytes.decode().splitlines()]
    assert [(row["doc_id"], row["section_order"]) for row in sections] == sorted(
        (row["doc_id"], row["section_order"]) for row in sections
    )
    assert (tmp_path / "sections.jsonl").read_bytes() == first_bytes
    assert first["section_count"] == second["section_count"] == 4
    chunk_ids = {
        row["chunk_id"]: row
        for path in (tmp_path / "chunks").glob("*.jsonl")
        for row in [json.loads(line) for line in path.read_text().splitlines()]
    }
    for section in sections:
        for chunk_id in section["child_chunk_ids"]:
            assert chunk_ids[chunk_id]["parent_section_id"] == section["section_id"]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda sections, chunk: sections[0]["child_chunk_ids"].clear(), "未收录"),
        (lambda sections, chunk: chunk.update(parent_section_id=None), "parent_section_id"),
        (lambda sections, chunk: chunk.update(doc_id="other-doc"), "跨文档"),
        (lambda sections, chunk: chunk.update(parent_section_id="missing-section"), "不存在"),
    ],
)
def test_migration_rejects_chunks_not_bidirectionally_linked_to_sections(mutation, message):
    derivatives = build_derivatives(_document())
    sections = derivatives["sections"]
    chunks = derivatives["chunks"]
    mutation(sections, chunks[0])

    with pytest.raises(ValueError, match=message):
        migration._validate_hierarchy(sections, chunks)


def test_migration_accepts_unresolved_chunk_without_parent_section():
    derivatives = build_derivatives(_document())
    sections = derivatives["sections"]
    chunks = derivatives["chunks"]
    chunk = chunks[0]
    chunk["hierarchy_status"] = "unresolved"
    chunk["parent_section_id"] = None
    sections[0]["child_chunk_ids"].remove(chunk["chunk_id"])

    migration._validate_hierarchy(sections, chunks)


def test_migration_rejects_unknown_chunk_hierarchy_status():
    derivatives = build_derivatives(_document())
    derivatives["chunks"][0]["hierarchy_status"] = "resovled"

    with pytest.raises(ValueError, match="hierarchy_status"):
        migration._validate_hierarchy(derivatives["sections"], derivatives["chunks"])


@pytest.mark.parametrize("cross_document", [False, True])
def test_migration_rejects_broken_section_parent_child_tree(cross_document):
    derivatives = build_derivatives(_document())
    root = derivatives["sections"][0]
    child = copy.deepcopy(root)
    child["section_id"] = "section-child"
    child["doc_id"] = "doc-b" if cross_document else "doc-a"
    child["section_order"] = 1
    child["parent_section_id"] = root["section_id"] if cross_document else None
    child["child_section_ids"] = []
    child["child_chunk_ids"] = []
    child["block_ids"] = []
    root["child_section_ids"] = [child["section_id"]]
    if cross_document:
        root["next_section_id"] = None
        child["previous_section_id"] = None
    else:
        root["next_section_id"] = child["section_id"]
        child["previous_section_id"] = root["section_id"]

    with pytest.raises(ValueError, match="跨文档" if cross_document else "互反"):
        migration._validate_hierarchy([root, child], derivatives["chunks"])
