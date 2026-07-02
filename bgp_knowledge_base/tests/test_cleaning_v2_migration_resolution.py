import copy
import json

from bgpkb.cleaning_v2 import migration_resolution
from bgpkb.pipeline import resolve_cleaning_v2_migration


def test_legacy_markdown_import_preserves_structure_and_marks_reviewed_fallback():
    markdown = "# Document Title\n\n## Section\n\nBody text.\n\n- Item one\n"
    source = {
        "doc_id": "doc-a",
        "source_path": "data/sources/raw/doc-a.html",
        "source_sha256": "a" * 64,
    }
    snapshot = copy.deepcopy(source)

    document, decisions = migration_resolution.build_legacy_preservation_document(
        doc_id="doc-a",
        markdown=markdown,
        source_meta=source,
        runtime_meta={"pipeline_revision": "test"},
        reviewer="botongwu",
        reviewed_at="2026-07-02T00:00:00+08:00",
    )

    assert source == snapshot
    assert document["parser_mode"] == "fallback"
    assert document["fallback_review_status"] == "approved"
    assert document["document_status"] == "approved"
    assert [block["block_type"] for block in document["blocks"]] == [
        "title",
        "heading",
        "paragraph",
        "list_item",
    ]
    assert [block["heading_level"] for block in document["blocks"][:2]] == [1, 2]
    assert all(block["review_status"] == "approved" for block in document["blocks"])
    assert all(block["quality"]["fallback_reviewed"] is True for block in document["blocks"])
    assert len(decisions) == 4
    assert all(decision["decision"] == "approved" for decision in decisions)


def test_migration_difference_decision_is_stable_and_has_required_evidence():
    first = migration_resolution.build_migration_decision(
        doc_id="doc-a",
        strategy="docling",
        reason_code="reviewed_layout_difference",
        v1_digest="sha256:" + "a" * 64,
        v2_digest="sha256:" + "b" * 64,
        reviewer="botongwu",
        reviewed_at="2026-07-02T00:00:00+08:00",
    )
    second = migration_resolution.build_migration_decision(**{
        "doc_id": "doc-a",
        "strategy": "docling",
        "reason_code": "reviewed_layout_difference",
        "v1_digest": "sha256:" + "a" * 64,
        "v2_digest": "sha256:" + "b" * 64,
        "reviewer": "botongwu",
        "reviewed_at": "2026-07-02T00:00:00+08:00",
    })

    assert first == second
    assert first["decision_id"].startswith("migration_decision_v2_")
    assert first["evidence"] == {
        "v1_digest": "sha256:" + "a" * 64,
        "v2_digest": "sha256:" + "b" * 64,
    }


def test_resolver_imports_low_coverage_html_and_writes_resolved_run(tmp_path):
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    (raw_root / "doc-a.html").write_text("<h1>Title</h1><p>Body</p>", encoding="utf-8")
    v1_root = tmp_path / "cleaned"
    v1_root.mkdir()
    (v1_root / "doc-a.md").write_text("# Title\n\nBody\n", encoding="utf-8")
    authority = tmp_path / "authority" / "doc-a"
    authority.mkdir(parents=True)
    original = {
        "doc_id": "doc-a",
        "parser_mode": "docling",
        "blocks": [],
        "runtime": {"pipeline_revision": "test"},
    }
    (authority / "cleaned_document.json").write_text(json.dumps(original), encoding="utf-8")
    original_run = tmp_path / "original-run"
    original_run.mkdir()
    (original_run / "document_status.jsonl").write_text(
        json.dumps({"doc_id": "doc-a", "state": "approved", "output_summary": {}}) + "\n",
        encoding="utf-8",
    )
    diff_path = tmp_path / "diff.jsonl"
    diff_path.write_text(
        json.dumps(
            {
                "doc_id": "doc-a",
                "state": "approved",
                "diff": {"body": {"coverage_ratio": 0.1}},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = resolve_cleaning_v2_migration.resolve_migration(
        authority_root=tmp_path / "authority",
        original_run_dir=original_run,
        resolved_run_dir=tmp_path / "resolved-run",
        v1_markdown_root=v1_root,
        raw_root=raw_root,
        diff_path=diff_path,
        decisions_path=tmp_path / "decisions.jsonl",
        reviewer="botongwu",
        reviewed_at="2026-07-02T00:00:00+08:00",
    )

    resolved = json.loads((authority / "cleaned_document.json").read_text(encoding="utf-8"))
    statuses = [
        json.loads(line)
        for line in (tmp_path / "resolved-run" / "document_status.jsonl").read_text().splitlines()
    ]
    assert result["fallback_document_count"] == 1
    assert resolved["fallback_review_status"] == "approved"
    assert "Body" in [block["cleaned_text"] for block in resolved["blocks"]]
    assert statuses[0]["state"] == "approved"
    assert statuses[0]["output_summary"]["fallback_used"] is True
    authority_status = json.loads((authority / "document_status.json").read_text(encoding="utf-8"))
    assert authority_status == statuses[0]

    diff_path.write_text(
        json.dumps(
            {
                "doc_id": "doc-a",
                "state": "approved",
                "diff": {"body": {"coverage_ratio": 1.0}},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    repeated = resolve_cleaning_v2_migration.resolve_migration(
        authority_root=tmp_path / "authority",
        original_run_dir=original_run,
        resolved_run_dir=tmp_path / "resolved-run",
        v1_markdown_root=v1_root,
        raw_root=raw_root,
        diff_path=diff_path,
        decisions_path=tmp_path / "decisions.jsonl",
        reviewer="botongwu",
        reviewed_at="2026-07-02T00:00:00+08:00",
    )
    assert repeated == result


def test_resolver_uses_historical_context_summary_alias(tmp_path):
    cleaned = tmp_path / "cleaned" / "notes"
    cleaned.mkdir(parents=True)
    expected = cleaned / "context_summary.md"
    expected.write_text("context", encoding="utf-8")

    assert resolve_cleaning_v2_migration.find_v1_markdown(
        tmp_path / "cleaned", "context_2026"
    ) == expected
