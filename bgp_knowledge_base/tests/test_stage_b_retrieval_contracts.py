import json

import pytest
import yaml
from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, Resource

from bgpkb import paths


CONFIG_PATH = paths.CONFIG_DIR / "rag_retrieval.yaml"
SCHEMA_DIR = paths.SCHEMAS_DIR
SCHEMA_BASE_URI = f"{SCHEMA_DIR.as_uri()}/"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def test_stage_b_config_pins_retrieval_model_and_budget_contracts():
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

    assert cfg["version"] == "rag_retrieval_v2"
    assert {
        key: cfg["hybrid_retrieval"][key]
        for key in ("lexical_top_k", "vector_top_k", "rrf_k", "fused_top_k")
    } == {
        "lexical_top_k": 50,
        "vector_top_k": 50,
        "rrf_k": 60,
        "fused_top_k": 20,
    }
    assert cfg["reranker"]["top_n_default"] == 5
    assert cfg["reranker"]["top_n_min"] == 5
    assert cfg["reranker"]["top_n_max"] == 8
    assert cfg["reranker"]["local_endpoint"] == "http://10.99.8.28:8012/v1/rerank"
    assert cfg["reranker"]["api_fallback"] == {
        "endpoint_env": "RERANK_API_ENDPOINT",
        "api_key_env": "RERANK_API_KEY",
        "model_env": "RERANK_API_MODEL",
    }
    assert cfg["embedding"]["local_endpoint"] == "http://10.99.8.28:8011/v1/embeddings"
    assert {"siliconflow_bge_m3", "aliyun_eas_bge_m3"} <= set(cfg["embedding"]["providers"])
    assert cfg["embedding"]["default_provider"] == "private_bge_m3_service"
    assert cfg["embedding"]["provider_chain"] == [
        "private_bge_m3_service",
        "siliconflow_bge_m3",
        "aliyun_eas_bge_m3",
    ]
    private_embedding = cfg["embedding"]["providers"]["private_bge_m3_service"]
    assert private_embedding["endpoint"] == "http://10.99.8.28:8011/v1/embeddings"
    assert private_embedding["model"] == "BAAI/bge-m3"
    assert private_embedding["requires_network"] is True
    assert private_embedding["runs_on_current_device"] is False
    assert cfg["embedding"]["offline_fallback_provider"] == "deterministic_mock"
    assert "deterministic_mock" not in cfg["embedding"]["provider_chain"]

    query_type = cfg["query_type"]
    assert query_type["allowed_values"] == ["fact", "procedure", "policy", "global", "auto"]
    assert query_type["resolved_values"] == ["fact", "procedure", "policy", "global"]
    assert query_type["default"] == "auto"
    assert query_type["resolution"]["audit_enabled"] is True
    assert query_type["resolution"]["final_fallback"] == "fact"
    assert query_type["deepseek"]["classification_prompt_version"]
    assert query_type["deepseek"]["summary_prompt_version"]

    context = cfg["context_pack"]
    assert context["default_tokens"] == 6000
    assert context["hard_max_tokens"] == 8000
    assert context["sibling_windows"] == {
        "fact": 1,
        "procedure": 2,
        "policy": 2,
        "global": 1,
    }
    assert context["full_section_eligible_query_types"] == ["policy", "global"]
    assert context["global_summary"]["max_tokens"] == 400
    assert context["parent_budget"] == {
        "normal_span": {
            "formula": "min(1200, context_pack_budget * 0.30)",
            "max_tokens": 1200,
            "budget_fraction": 0.30,
        },
        "policy_full_section": {
            "formula": "min(3000, context_pack_budget * 0.50)",
            "max_tokens": 3000,
            "budget_fraction": 0.50,
            "max_full_parent_sections": 1,
        },
        "global_full_section": {
            "per_parent_formula": "min(2000, context_pack_budget * 0.35)",
            "total_formula": "context_pack_budget * 0.60",
            "max_tokens": 2000,
            "budget_fraction": 0.35,
            "max_full_parent_sections": 2,
            "max_total_budget_fraction": 0.60,
        },
    }
    assert cfg["degradation_metadata"]["required_fields"] == [
        "provider",
        "model",
        "degraded_reason",
    ]


def test_stage_b_schemas_are_json_schema_2020_12():
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        if path.name in {
            "section_catalog.schema.json",
            "context_unit.schema.json",
            "chunk.schema.json",
            "retrieval_result.schema.json",
            "context_pack.schema.json",
        }:
            schema = json.loads(path.read_text(encoding="utf-8"))
            assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
            Draft202012Validator.check_schema(schema)


def test_section_catalog_and_context_unit_accept_minimum_records():
    section = {
        "schema_version": "section_catalog_v1",
        "section_id": "section:doc-1:intro",
        "content_hash": "sha256:abc",
        "doc_id": "doc-1",
        "heading": "引言",
        "section_path": ["引言"],
        "section_order": 0,
        "parent_section_id": None,
        "child_section_ids": [],
        "previous_section_id": None,
        "next_section_id": None,
        "source_ref": "docs/doc-1.md#intro",
        "child_chunk_ids": ["chunk-1"],
        "block_ids": ["block-1"],
        "content_chars": 80,
        "estimated_tokens": 40,
    }
    Draft202012Validator(load_schema("section_catalog.schema.json")).validate(section)

    context_unit = {
        "schema_version": "context_unit_v1",
        "context_id": "context-1",
        "mode": "parent_span",
        "doc_id": "doc-1",
        "section_path": ["引言"],
        "parent_section_id": "section:doc-1:intro",
        "parent_section_heading": "引言",
        "included_chunk_ids": ["chunk-1"],
        "included_block_ids": ["block-1"],
        "content": "示例上下文",
        "estimated_tokens": 10,
        "actual_tokens": None,
        "max_rerank_score": 0.91,
        "trim_events": [],
        "citations": [{"chunk_id": "chunk-1", "source_ref": "docs/doc-1.md#intro"}],
    }
    context_validator = Draft202012Validator(load_schema("context_unit.schema.json"))
    context_validator.validate(context_unit)
    context_validator.validate(context_unit | {"max_rerank_score": None})
    with pytest.raises(ValidationError):
        context_validator.validate(context_unit | {"citations": []})


def test_chunk_schema_keeps_v1_compatible_and_gates_v2_hierarchy_fields():
    schema = Draft202012Validator(load_schema("chunk.schema.json"))
    legacy_chunk = {
        "chunk_id": "legacy-1",
        "doc_id": "doc-1",
        "source_type": "rfc",
        "chunk_type": "text",
        "topics": [],
        "content": "legacy",
        "source_ref": "rfc/1",
        "review_status": "approved",
    }
    schema.validate(legacy_chunk)
    current_chunks_v2_path = paths.PROJECT_ROOT / "data/corpus/chunks_v2/rfc4271.jsonl"
    current_chunks_v2_record = json.loads(
        current_chunks_v2_path.read_text(encoding="utf-8").splitlines()[0]
    )
    assert "schema_version" not in current_chunks_v2_record
    assert current_chunks_v2_record["source_block_ids"]
    schema.validate(current_chunks_v2_record)

    v2_chunk = legacy_chunk | {
        "schema_version": "chunk_v2_hierarchical",
        "parent_section_id": "section-1",
        "chunk_order": 0,
        "previous_chunk_id": None,
        "next_chunk_id": None,
        "hierarchy_status": "resolved",
        "source_block_ids": ["block-1"],
    }
    schema.validate(v2_chunk)
    schema.validate(v2_chunk | {"hierarchy_status": "unresolved", "parent_section_id": None})

    with pytest.raises(ValidationError):
        schema.validate(v2_chunk | {"parent_section_id": None})
    with pytest.raises(ValidationError):
        incomplete = dict(v2_chunk)
        incomplete.pop("source_block_ids")
        schema.validate(incomplete)

    v2_fields = {
        "parent_section_id": "section-1",
        "chunk_order": 0,
        "previous_chunk_id": None,
        "next_chunk_id": None,
        "hierarchy_status": "resolved",
    }
    for field, value in v2_fields.items():
        with pytest.raises(ValidationError):
            schema.validate(legacy_chunk | {field: value})
        with pytest.raises(ValidationError):
            schema.validate(legacy_chunk | {"schema_version": "chunk_v1", field: value})


def test_retrieval_and_context_pack_schemas_add_v2_fields_without_breaking_v1_required_sets():
    retrieval = load_schema("retrieval_result.schema.json")
    context_pack = load_schema("context_pack.schema.json")
    context_unit_schema = load_schema("context_unit.schema.json")

    assert {"@id", "chunk_id", "source_ref", "review_status", "retrieval_method", "score"} <= set(
        retrieval["required"]
    )
    assert {
        "lexical_score",
        "lexical_rank",
        "vector_score",
        "vector_rank",
        "fusion_score",
        "fusion_rank",
        "rerank_score",
        "rerank_rank",
        "match_channels",
        "parent_section_id",
        "parent_section_heading",
        "provider",
        "model",
        "degraded",
        "degraded_reason",
    } <= set(retrieval["properties"])
    assert retrieval["properties"]["fusion_rank"] == {"type": "integer", "minimum": 1}
    assert {"query", "results", "citations", "excluded_by_policy"} <= set(context_pack["required"])
    assert {
        "requested_query_type",
        "resolved_query_type",
        "token_budget",
        "context_units",
        "provider",
        "model",
        "degraded",
        "degraded_reason",
        "trim_events",
    } <= set(context_pack["properties"])

    legacy_result = {
        "@id": "result-1",
        "chunk_id": "chunk-1",
        "source_ref": "rfc/1",
        "review_status": "approved",
        "retrieval_method": "hybrid",
        "score": 0.8,
    }
    retrieval_validator = Draft202012Validator(retrieval)
    retrieval_validator.validate(legacy_result)
    retrieval_validator.validate(legacy_result | {"schema_version": "retrieval_result_v1"})

    v2_result_fields = {
        "lexical_score": 0.2,
        "lexical_rank": 1,
        "vector_score": None,
        "vector_rank": None,
        "fusion_score": 0.1,
        "fusion_rank": 1,
        "rerank_score": None,
        "rerank_rank": None,
        "match_channels": ["lexical"],
        "section_path": ["引言"],
        "parent_section_id": "section-1",
        "parent_section_heading": "引言",
        "provider": "rrf",
        "model": "none",
        "degraded": True,
        "degraded_reason": "reranker_unavailable",
    }
    v2_result = (
        legacy_result
        | {"schema_version": "retrieval_result_v2", "doc_id": "doc-1"}
        | v2_result_fields
    )
    retrieval_validator.validate(v2_result)
    vector_only_result = v2_result | {
        "lexical_score": None,
        "lexical_rank": None,
        "vector_score": 0.3,
        "vector_rank": 1,
        "match_channels": ["vector"],
    }
    retrieval_validator.validate(vector_only_result)

    v2_required_fields = {
        "doc_id",
        "lexical_score",
        "lexical_rank",
        "vector_score",
        "vector_rank",
        "fusion_score",
        "fusion_rank",
        "rerank_score",
        "rerank_rank",
        "match_channels",
        "section_path",
        "parent_section_id",
        "parent_section_heading",
        "provider",
        "model",
        "degraded",
    }
    for field in v2_required_fields:
        incomplete = dict(v2_result)
        incomplete.pop(field)
        with pytest.raises(ValidationError):
            retrieval_validator.validate(incomplete)

    for field in ("doc_id", "parent_section_id", "parent_section_heading"):
        with pytest.raises(ValidationError):
            retrieval_validator.validate(v2_result | {field: ""})
    with pytest.raises(ValidationError):
        retrieval_validator.validate(v2_result | {"match_channels": []})
    with pytest.raises(ValidationError):
        retrieval_validator.validate(v2_result | {"fusion_score": None})

    for field in ("lexical_score", "lexical_rank"):
        with pytest.raises(ValidationError):
            retrieval_validator.validate(v2_result | {field: None})
    for field in ("vector_score", "vector_rank"):
        with pytest.raises(ValidationError):
            retrieval_validator.validate(vector_only_result | {field: None})

    with pytest.raises(ValidationError):
        retrieval_validator.validate(v2_result | {"vector_score": 0.3, "vector_rank": 1})
    with pytest.raises(ValidationError):
        retrieval_validator.validate(
            vector_only_result | {"lexical_score": 0.2, "lexical_rank": 1}
        )

    with pytest.raises(ValidationError):
        retrieval_validator.validate(v2_result | {"rerank_score": 0.8, "rerank_rank": None})
    with pytest.raises(ValidationError):
        retrieval_validator.validate(v2_result | {"rerank_score": None, "rerank_rank": 1})

    with pytest.raises(ValidationError):
        retrieval_validator.validate(legacy_result | {"schema_version": "retrieval_result_v2"})
    for field, value in v2_result_fields.items():
        isolation_value = False if field == "degraded" else value
        with pytest.raises(ValidationError):
            retrieval_validator.validate(legacy_result | {field: isolation_value})
        with pytest.raises(ValidationError):
            retrieval_validator.validate(
                legacy_result | {"schema_version": "retrieval_result_v1", field: isolation_value}
            )

    with pytest.raises(ValidationError):
        retrieval_validator.validate(v2_result | {"fusion_rank": 0})
    with pytest.raises(ValidationError):
        retrieval_validator.validate(v2_result | {"degraded_reason": ""})

    legacy_pack = {
        "query": "BGP",
        "results": [],
        "citations": [],
        "excluded_by_policy": [],
    }
    registry = Registry().with_resources(
        [
            (
                f"{SCHEMA_BASE_URI}retrieval_result.schema.json",
                Resource.from_contents(retrieval),
            ),
            (
                f"{SCHEMA_BASE_URI}context_unit.schema.json",
                Resource.from_contents(context_unit_schema),
            ),
        ]
    )
    context_pack = context_pack | {"$id": f"{SCHEMA_BASE_URI}context_pack.schema.json"}
    context_validator = Draft202012Validator(context_pack, registry=registry)
    context_validator.validate(legacy_pack)
    context_validator.validate(legacy_pack | {"schema_version": "context_pack_v1"})

    context_unit = {
        "schema_version": "context_unit_v1",
        "context_id": "context-1",
        "mode": "parent_span",
        "doc_id": "doc-1",
        "section_path": ["引言"],
        "parent_section_id": "section-1",
        "parent_section_heading": "引言",
        "included_chunk_ids": ["chunk-1"],
        "included_block_ids": ["block-1"],
        "content": "上下文",
        "estimated_tokens": 10,
        "actual_tokens": None,
        "max_rerank_score": None,
        "trim_events": [],
        "citations": [{"chunk_id": "chunk-1", "source_ref": "rfc/1"}],
    }

    v2_pack_fields = {
        "requested_query_type": "auto",
        "resolved_query_type": "fact",
        "token_budget": 6000,
        "context_units": [context_unit],
        "provider": "private_bge_m3_service",
        "model": "BAAI/bge-m3",
        "degraded": True,
        "degraded_reason": "query_type_classifier_unavailable",
        "trim_events": [],
    }
    v2_pack = (
        legacy_pack
        | {"schema_version": "context_pack_v2", "results": [v2_result]}
        | v2_pack_fields
    )
    context_validator.validate(v2_pack)

    with pytest.raises(ValidationError):
        context_validator.validate(v2_pack | {"results": [v2_result | {"fusion_rank": 0}]})
    with pytest.raises(ValidationError):
        context_validator.validate(
            v2_pack | {"context_units": [context_unit | {"citations": []}]}
        )

    with pytest.raises(ValidationError):
        context_validator.validate(legacy_pack | {"schema_version": "context_pack_v2"})
    for field, value in v2_pack_fields.items():
        isolation_value = False if field == "degraded" else value
        with pytest.raises(ValidationError):
            context_validator.validate(legacy_pack | {field: isolation_value})
        with pytest.raises(ValidationError):
            context_validator.validate(
                legacy_pack | {"schema_version": "context_pack_v1", field: isolation_value}
            )
