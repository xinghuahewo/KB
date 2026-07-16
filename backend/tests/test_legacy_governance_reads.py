import json

from bgpkb.ingestion import extract_case_observations
from bgpkb.publishing import build_entity_source_evidence
from bgpkb.publishing import build_human_review_evidence_extracts


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_case_observation_marks_cleaned_v1_as_deprecated_read_only(tmp_path, monkeypatch):
    cleaned = tmp_path / "case.md"
    cleaned.write_text("On 2024-01-02 AS64500 announced 192.0.2.0/24.", encoding="utf-8")
    monkeypatch.setattr(extract_case_observations, "cleaned_case_path", lambda _source_id: cleaned)

    records, status = extract_case_observations.extract_observations(
        {"source_id": "case-1", "title": "Case One"}
    )

    assert status["input_mode"] == "legacy_read_only"
    assert status["diagnostic_code"] == "deprecated_legacy_canonical_input"
    assert records
    assert {row["input_mode"] for row in records} == {"legacy_read_only"}


def test_human_review_evidence_reads_v1_chunks_through_explicit_adapter(tmp_path, monkeypatch):
    chunk_root = tmp_path / "chunks"
    _write_jsonl(chunk_root / "old.jsonl", [{"chunk_id": "old-1", "doc_id": "doc-1", "content": "BGP"}])
    monkeypatch.setattr(build_human_review_evidence_extracts, "CHUNK_DIR", chunk_root)
    monkeypatch.setattr(build_human_review_evidence_extracts, "ROOT", tmp_path)

    chunks = build_human_review_evidence_extracts.load_chunks_by_id()

    assert chunks["old-1"]["input_mode"] == "legacy_read_only"
    assert chunks["old-1"]["legacy_diagnostic_code"] == "deprecated_legacy_canonical_input"


def test_entity_evidence_reads_v1_chunks_through_explicit_adapter(tmp_path, monkeypatch):
    chunk_root = tmp_path / "chunks"
    _write_jsonl(chunk_root / "old.jsonl", [{"chunk_id": "old-1", "doc_id": "doc-1", "content": "BGP"}])
    monkeypatch.setattr(build_entity_source_evidence.paths, "CHUNKS_DIR", chunk_root)

    chunks = build_entity_source_evidence.load_chunks_by_doc()

    assert chunks["doc-1"][0]["input_mode"] == "legacy_read_only"
    assert chunks["doc-1"][0]["legacy_diagnostic_code"] == "deprecated_legacy_canonical_input"
