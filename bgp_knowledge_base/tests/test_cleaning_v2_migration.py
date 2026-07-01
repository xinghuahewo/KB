import json

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
        report_path=tmp_path / "report.md", expected_document_count=2,
    )

    assert result["terminal_count"] == 2
    assert (tmp_path / "parsed_v2" / "doc-a.json").is_file()
    assert (tmp_path / "parsed_v2" / "doc-b.json").is_file()
    assert (tmp_path / "markdown_v2" / "doc-a.md").is_file()
    records = [json.loads(line) for line in (tmp_path / "diffs.jsonl").read_text().splitlines()]
    assert {row["doc_id"] for row in records} == {"doc-a", "doc-b"}
    assert next(row for row in records if row["doc_id"] == "doc-b")["blocking_issues"] == ["quarantined_document"]
    assert "# Docling 清洗 v2 全量迁移报告" in (tmp_path / "report.md").read_text(encoding="utf-8")
