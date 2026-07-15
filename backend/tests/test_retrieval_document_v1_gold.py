import copy
import json

import jsonschema
import pytest

from bgpkb import paths


def _semantic_chunk(*, content: str | None = None) -> dict:
    body = content or (
        "A route leak is the propagation of routing announcements beyond their intended scope. "
        "The receiving network can select and further propagate an invalid path, affecting reachability. "
        "Operators should validate export policy, inspect AS paths, and compare the announcement with "
        "the expected customer-provider relationship before classifying the event. "
        "This final sentence must remain available to every retrieval model and must not be truncated."
    )
    return {
        "schema_version": "semantic_chunk_v3",
        "chunk_id": "semantic_chunk_v3_" + "1" * 64,
        "doc_id": "rfc7908",
        "source_id": "rfc7908",
        "source_snapshot_id": "snapshot_" + "2" * 64,
        "source_object_digest": "sha256:" + "3" * 64,
        "document_profile": "rfc",
        "chunker": {
            "name": "rfc_semantic",
            "version": "3.0.0",
            "config_version": "semantic_chunking_v3.0.0",
            "config_fingerprint": "sha256:" + "4" * 64,
        },
        "title": "RFC 7908 Route Leak",
        "section_path": ["2. Route Leak Definition", "2.1 Operational Consequences"],
        "semantic_unit": "paragraph",
        "content": body,
        "content_hash": "sha256:" + "5" * 64,
        "exact_content_hash": "sha256:" + "6" * 64,
        "source_block_ids": ["block_v2_" + "7" * 64],
        "source_block_hashes": ["sha256:" + "8" * 64],
        "source_refs": ["raw/standards/rfc7908.txt#section-2.1"],
        "page_numbers": [],
        "language": "en",
        "estimated_tokens": 110,
        "short_content_rule_id": None,
    }


def _eligibility() -> dict:
    return {
        "status": "eligible",
        "rule_id": "retrieval_eligibility_v1:eligible_reviewed_source",
        "policy_version": "retrieval_eligibility_v1",
        "reason": "来源和内容满足检索前置条件",
        "audit": {
            "actor": "system:retrieval_eligibility_policy",
            "decision_method": "deterministic_policy",
            "input_fingerprint": "sha256:" + "9" * 64,
            "policy_fingerprint": "sha256:" + "a" * 64,
        },
    }


def _governance(chunk: dict, eligibility: dict | None = None) -> dict:
    return {
        "schema_version": "evidence_governance_state_v1",
        "object_id": chunk["chunk_id"],
        "object_type": "semantic_chunk",
        "parse_status": "parsed",
        "content_quality_status": "approved",
        "source_trust_status": "trusted",
        "semantic_review_status": "approved",
        "retrieval_eligibility": eligibility or _eligibility(),
        "status_provenance": {
            "parse_status": "canonical.parse_status",
            "content_quality_status": "canonical.content_quality_status",
            "source_trust_status": "source_review.review_status+trust_level",
            "semantic_review_status": "entity_review.review_status",
        },
        "migration_audit": [],
    }


def test_retrieval_document_schema_and_long_body_are_complete():
    from bgpkb.indexing.retrieval_documents import derive_retrieval_document

    schema = json.loads(
        (paths.SCHEMAS_DIR / "retrieval_document_v1.schema.json").read_text(encoding="utf-8")
    )
    chunk = _semantic_chunk()
    document = derive_retrieval_document(
        chunk, eligibility=_eligibility(), governance=_governance(chunk)
    )

    jsonschema.Draft202012Validator(schema).validate(document)
    assert schema["additionalProperties"] is False
    assert len(chunk["content"]) > 240
    assert chunk["content"] in document["retrieval_text"]
    assert document["retrieval_text"].endswith(chunk["content"])
    assert document["content_preview"] == chunk["content"][:240]
    assert len(document["content_preview"]) <= 240
    assert document["retrieval_text_hash"].startswith("sha256:")
    assert document["retrieval_text_version"] == "retrieval_text_v1"


def test_ineligible_chunk_cannot_produce_a_retrieval_document():
    from bgpkb.indexing.retrieval_documents import derive_retrieval_document

    eligibility = {**_eligibility(), "status": "ineligible"}
    with pytest.raises(ValueError, match="eligible"):
        chunk = _semantic_chunk()
        derive_retrieval_document(
            chunk, eligibility=eligibility, governance=_governance(chunk, eligibility)
        )


def test_fts_embedding_and_reranker_receive_the_identical_versioned_text():
    from bgpkb.indexing.retrieval_documents import (
        build_retrieval_input_manifest,
        retrieval_input_for,
    )

    document = __import__(
        "bgpkb.indexing.retrieval_documents", fromlist=["derive_retrieval_document"]
    ).derive_retrieval_document(
        (chunk := _semantic_chunk()), eligibility=_eligibility(), governance=_governance(chunk)
    )
    manifest = build_retrieval_input_manifest([document])
    inputs = {
        component: retrieval_input_for(document, component, manifest=manifest)
        for component in ("fts", "embedding", "reranker")
    }

    assert {item["text"] for item in inputs.values()} == {document["retrieval_text"]}
    assert {item["retrieval_text_hash"] for item in inputs.values()} == {
        document["retrieval_text_hash"]
    }
    assert {item["retrieval_text_version"] for item in inputs.values()} == {
        "retrieval_text_v1"
    }
    assert {item["input_manifest_hash"] for item in inputs.values()} == {
        manifest["input_manifest_hash"]
    }
    assert document["content_preview"] not in {
        item["text"] for item in inputs.values() if item["text"] != document["retrieval_text"]
    }


def test_embedding_cache_key_invalidates_every_authoritative_input():
    from bgpkb.indexing.retrieval_documents import embedding_cache_key

    document = __import__(
        "bgpkb.indexing.retrieval_documents", fromlist=["derive_retrieval_document"]
    ).derive_retrieval_document(
        (chunk := _semantic_chunk()), eligibility=_eligibility(), governance=_governance(chunk)
    )
    kwargs = {
        "document": document,
        "model": "BAAI/bge-m3",
        "model_revision": "rev-a",
        "normalization": "l2_v1",
        "provider_contract": "local_http_v1",
    }
    baseline = embedding_cache_key(**kwargs)

    variants = []
    changed_document = copy.deepcopy(document)
    changed_document["retrieval_text_hash"] = "sha256:" + "9" * 64
    variants.append({**kwargs, "document": changed_document})
    variants.append({**kwargs, "model": "BAAI/bge-m3-new"})
    variants.append({**kwargs, "model_revision": "rev-b"})
    variants.append({**kwargs, "normalization": "none"})
    variants.append({**kwargs, "provider_contract": "local_http_v2"})

    assert all(embedding_cache_key(**variant) != baseline for variant in variants)


def test_component_manifest_mismatch_names_the_divergent_component():
    from bgpkb.indexing.retrieval_documents import verify_component_input_manifests

    current = "sha256:" + "a" * 64
    with pytest.raises(ValueError, match="reranker"):
        verify_component_input_manifests({
            "fts": current,
            "embedding": current,
            "reranker": "sha256:" + "b" * 64,
        })


@pytest.mark.parametrize("missing_name", ["matrix", "metadata", "manifest"])
def test_publish_gate_rejects_each_missing_fast_index_artifact(tmp_path, missing_name):
    from bgpkb.infrastructure.fast_vector_index import verify_fast_vector_artifacts

    vector_index = tmp_path / "bge_m3_vector_index.jsonl"
    vector_index.write_text(
        json.dumps({
            "kind": "chunk",
            "metadata": {"chunk_id": "chunk-1", "retrieval_eligibility": "eligible"},
            "vector": [1.0, 0.0],
        }) + "\n",
        encoding="utf-8",
    )
    artifacts = __import__(
        "bgpkb.infrastructure.fast_vector_index", fromlist=["build_fast_vector_index"]
    ).build_fast_vector_index(vector_index)
    getattr(artifacts, f"{missing_name}_path").unlink()

    with pytest.raises(RuntimeError, match=missing_name):
        verify_fast_vector_artifacts(vector_index, eligible_chunk_ids={"chunk-1"})
