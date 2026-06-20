import json
import os
import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_llm_candidate_enrichment.py"
CHUNK_CANDIDATES = ROOT / "datasets" / "chunk_enrichment_candidates.jsonl"
ENTITY_LINK_CANDIDATES = ROOT / "datasets" / "entity_link_candidates.jsonl"
ENTITY_FILE = ROOT / "entities" / "anomaly_types.jsonl"


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_script(*args):
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(SCRIPT), *args]
        runpy.run_path(str(SCRIPT), run_name="__main__")
    finally:
        sys.argv = old_argv


def test_mock_candidate_generation_is_offline_traceable_and_does_not_edit_entities():
    before = ENTITY_FILE.read_text(encoding="utf-8")
    run_script()
    after = ENTITY_FILE.read_text(encoding="utf-8")

    assert before == after
    chunks = load_jsonl(CHUNK_CANDIDATES)
    links = load_jsonl(ENTITY_LINK_CANDIDATES)
    assert chunks
    assert links
    assert all(record["review_status"] == "pending_review" for record in chunks)
    assert all(record["provider"] == "mock" for record in chunks)
    assert all(record["chunk_id"] and record["source_ref"] for record in chunks)
    assert all(record["generated_by"] == "scripts/build_llm_candidate_enrichment.py" for record in chunks)
    assert any("route" in " ".join(record["keywords"]).lower() for record in chunks)
    assert all(record["review_status"] == "pending_review" for record in links)
    assert all(record["chunk_id"] and record["entity_id"] and record["source_ref"] for record in links)


def test_deepseek_provider_requires_explicit_api_key_without_fallback(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(SCRIPT), "--provider", "deepseek"]
        try:
            runpy.run_path(str(SCRIPT), run_name="__main__")
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError("deepseek provider must fail without DEEPSEEK_API_KEY")
    finally:
        sys.argv = old_argv
        os.environ.pop("DEEPSEEK_API_KEY", None)
