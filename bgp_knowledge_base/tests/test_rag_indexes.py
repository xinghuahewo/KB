import json
import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_rag_indexes.py"
MANIFEST = ROOT / "published" / "embedding_manifest.json"
VECTOR_INDEX = ROOT / "published" / "rag_mock_vector_index.jsonl"
RETRIEVAL_INDEX = ROOT / "published" / "rag_retrieval_index.json"
CHUNK_CATALOG = ROOT / "published" / "chunk_catalog.jsonl"


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_script(*args):
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(SCRIPT), *args]
        runpy.run_path(str(SCRIPT), run_name="__main__")
    finally:
        sys.argv = old_argv


def test_mock_embedding_index_is_offline_and_preserves_chunk_catalog():
    before = CHUNK_CATALOG.read_text(encoding="utf-8")
    run_script()
    after = CHUNK_CATALOG.read_text(encoding="utf-8")

    assert before == after
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    retrieval = json.loads(RETRIEVAL_INDEX.read_text(encoding="utf-8"))
    vectors = load_jsonl(VECTOR_INDEX)

    assert manifest["provider"] == "deterministic_mock"
    assert manifest["real_model_execution"] is False
    assert manifest["bge_m3_ready"] is True
    assert manifest["colbert_enabled"] is False
    assert manifest["input_count"] == len(vectors)
    assert retrieval["vector_store"]["provider"] == "mock_jsonl"
    assert retrieval["vector_store"]["real_milvus_execution"] is False
    assert retrieval["lexical_fallback"]["provider"] == "sqlite_fts5"
    assert vectors
    assert {"@id", "chunk_id", "source_ref", "review_status", "vector"} <= set(vectors[0])


def test_bge_provider_path_exists_but_is_disabled_by_default():
    namespace = runpy.run_path(str(SCRIPT))
    BgeM3EmbeddingProvider = namespace["BgeM3EmbeddingProvider"]
    provider = BgeM3EmbeddingProvider(enabled=False)

    assert provider.enabled is False
    try:
        provider.embed(["route leak"])
    except RuntimeError as exc:
        assert "disabled" in str(exc)
    else:
        raise AssertionError("disabled BGE-M3 provider must not embed")
