import json
from pathlib import Path

from bgpkb import paths

import yaml


ROOT = paths.PROJECT_ROOT
RAG_CONFIG = paths.CONFIG_DIR / "rag_retrieval.yaml"
LLM_CONFIG = paths.CONFIG_DIR / "llm_candidate_enrichment.yaml"
RETRIEVAL_SCHEMA = paths.SCHEMAS_DIR / "retrieval_result.schema.json"
CONTEXT_SCHEMA = paths.SCHEMAS_DIR / "context_pack.schema.json"


def test_rag_and_llm_configs_lock_offline_defaults_and_real_provider_boundaries():
    rag = yaml.safe_load(RAG_CONFIG.read_text(encoding="utf-8"))
    llm = yaml.safe_load(LLM_CONFIG.read_text(encoding="utf-8"))

    assert rag["version"] == "rag_retrieval_v1"
    assert rag["default_mode"] == "offline_framework"
    assert rag["trusted_collection"]["lifecycle_status"] == ["approved"]
    assert rag["trusted_collection"]["exclude_lifecycle_status"] == ["deprecated", "archived"]
    assert rag["embedding"]["default_provider"] == "siliconflow_bge_m3"
    assert rag["embedding"]["offline_fallback_provider"] == "deterministic_mock"
    assert rag["embedding"]["providers"]["siliconflow_bge_m3"]["api_key_env"] == "SILICONFLOW_API_KEY"
    assert rag["embedding"]["providers"]["siliconflow_bge_m3"]["model"] == "BAAI/bge-m3"
    assert rag["embedding"]["providers"]["aliyun_eas_bge_m3"]["endpoint_env"] == "ALIYUN_BGE_M3_ENDPOINT"
    assert rag["embedding"]["providers"]["local_bge_m3"]["enabled"] is False
    assert rag["embedding"]["providers"]["local_bge_m3"]["outputs"] == {
        "dense": True,
        "sparse": True,
        "colbert": False,
    }
    assert rag["vector_store"]["default_provider"] == "mock_jsonl"
    assert rag["hybrid_retrieval"]["min_vector_similarity"] == 0.5
    assert rag["vector_store"]["providers"]["milvus_lite"]["enabled"] is False
    assert rag["lexical_fallback"]["provider"] == "sqlite_fts5"
    assert rag["context_pack"]["generates_final_answer"] is False

    assert llm["version"] == "llm_candidate_enrichment_v1"
    assert llm["default_provider"] == "mock"
    assert llm["providers"]["deepseek"]["enabled"] is False
    assert llm["providers"]["deepseek"]["api_key_env"] == "DEEPSEEK_API_KEY"
    assert llm["providers"]["qwen_vllm"]["enabled"] is False
    assert llm["providers"]["qwen_vllm"]["client_protocol"] == "openai_compatible"
    assert llm["safety"]["writes_primary_entities"] is False
    assert llm["safety"]["approves_entities"] is False
    assert llm["safety"]["generates_final_answers"] is False


def test_retrieval_and_context_pack_schemas_require_traceability_fields():
    retrieval_schema = json.loads(RETRIEVAL_SCHEMA.read_text(encoding="utf-8"))
    context_schema = json.loads(CONTEXT_SCHEMA.read_text(encoding="utf-8"))

    assert {
        "@id",
        "chunk_id",
        "source_ref",
        "review_status",
        "retrieval_method",
        "score",
    } <= set(retrieval_schema["required"])
    assert {"query", "results", "citations", "excluded_by_policy"} <= set(context_schema["required"])
    result_ref = context_schema["properties"]["results"]["items"]
    assert result_ref["$ref"] == "retrieval_result.schema.json"
