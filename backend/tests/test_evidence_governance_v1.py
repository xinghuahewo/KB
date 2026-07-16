import copy
import json

import jsonschema
import pytest

from bgpkb import paths
from bgpkb.domain.evidence_governance import (
    ContentQualityStatus,
    GovernanceUpdateError,
    ParseStatus,
    RetrievalEligibilityStatus,
    SemanticReviewStatus,
    SourceTrustStatus,
    apply_governance_update,
    derive_retrieval_eligibility,
    load_eligibility_policy,
    migrate_legacy_governance,
)


SNAPSHOT_ID = "snapshot_" + "a" * 64


def _governance(**overrides):
    value = {
        "schema_version": "evidence_governance_state_v1",
        "object_id": "semantic_chunk_v3_" + "1" * 64,
        "object_type": "semantic_chunk",
        "parse_status": "parsed",
        "content_quality_status": "approved",
        "source_trust_status": "trusted",
        "semantic_review_status": "approved",
        "retrieval_eligibility": None,
        "status_provenance": {
            "parse_status": "canonical.parse_status",
            "content_quality_status": "canonical.content_quality_status",
            "source_trust_status": "source_review.review_status+trust_level",
            "semantic_review_status": "entity_review.review_status",
        },
        "migration_audit": [],
    }
    value.update(overrides)
    return value


def _derive(governance=None, **overrides):
    inputs = {
        "governance": governance or _governance(),
        "source_ref": "raw/standards/rfc4271.txt#section-5",
        "source_snapshot_id": SNAPSHOT_ID,
        "purpose": "answer_evidence",
        "source_type": "standard",
        "isolation_signals": [],
    }
    inputs.update(overrides)
    return derive_retrieval_eligibility(**inputs)


def _eligibility_record():
    return {
        "status": "eligible",
        "policy_version": "retrieval_eligibility_v1",
        "rule_id": "retrieval.reviewed_trusted_evidence",
        "reason": "来源与语义审核均通过",
        "audit": {
            "actor": "system:retrieval_eligibility_policy",
            "decision_method": "deterministic_policy",
            "input_fingerprint": "sha256:" + "b" * 64,
            "policy_fingerprint": "sha256:" + "c" * 64,
        },
    }


def test_governance_schema_keeps_five_statuses_orthogonal():
    schema = json.loads(
        (paths.SCHEMAS_DIR / "evidence_governance_state_v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    record = _governance()
    record["retrieval_eligibility"] = _eligibility_record()

    jsonschema.Draft202012Validator(schema).validate(record)
    assert schema["additionalProperties"] is False

    invalid = copy.deepcopy(record)
    invalid["source_trust_status"] = "approved"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(invalid)

    invalid = copy.deepcopy(record)
    invalid["approved"] = True
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(schema).validate(invalid)


def test_policy_configuration_is_versioned_and_declares_rule_order():
    policy = load_eligibility_policy()

    assert policy["schema_version"] == "retrieval_eligibility_policy_config_v1"
    assert policy["policy_version"] == "retrieval_eligibility_v1"
    assert policy["policy_fingerprint"].startswith("sha256:")
    assert policy["rule_order"][0] == "retrieval.missing_source_trace"
    assert len(policy["rule_order"]) == len(set(policy["rule_order"]))
    assert {item.value for item in ParseStatus} == {"parsed", "failed", "quarantined", "unknown"}
    assert {item.value for item in ContentQualityStatus} == {
        "approved", "pending_review", "rejected", "quarantined", "unknown"
    }
    assert {item.value for item in SourceTrustStatus} == {
        "trusted", "trusted_with_caution", "untrusted", "pending", "unknown"
    }
    assert {item.value for item in SemanticReviewStatus} == {
        "approved", "pending", "rejected", "unknown"
    }
    assert {item.value for item in RetrievalEligibilityStatus} == {
        "eligible", "eligible_with_caution", "ineligible"
    }


def test_legacy_approved_only_promotes_content_quality_when_other_reviews_are_missing():
    migrated = migrate_legacy_governance(
        {
            "chunk_id": "legacy-chunk-1",
            "review_status": "approved",
            "parsed_status": "parsed",
        },
        source_record=None,
        semantic_review_record=None,
    )

    assert migrated["parse_status"] == "parsed"
    assert migrated["content_quality_status"] == "approved"
    assert migrated["source_trust_status"] == "unknown"
    assert migrated["semantic_review_status"] == "unknown"
    assert migrated["retrieval_eligibility"] is None
    assert migrated["status_provenance"]["content_quality_status"] == "legacy.review_status"
    assert migrated["status_provenance"]["source_trust_status"] == "migration.missing_source_review"


def test_source_and_semantic_reviews_migrate_only_from_their_own_records():
    migrated = migrate_legacy_governance(
        {"chunk_id": "legacy-chunk-2", "review_status": "approved"},
        source_record={"source_id": "rfc4271", "trust_level": "medium", "review_status": "approved"},
        semantic_review_record={"id": "bgp-concept", "review_status": "pending"},
    )

    assert migrated["content_quality_status"] == "approved"
    assert migrated["source_trust_status"] == "trusted_with_caution"
    assert migrated["semantic_review_status"] == "pending"
    assert {event["dimension"] for event in migrated["migration_audit"]} == {
        "parse_status",
        "content_quality_status",
        "source_trust_status",
        "semantic_review_status",
    }


def test_missing_statuses_remain_unknown_or_pending_instead_of_becoming_approved():
    migrated = migrate_legacy_governance(
        {"chunk_id": "legacy-chunk-3"},
        source_record={"source_id": "draft-source", "trust_level": "high", "review_status": "pending"},
        semantic_review_record={},
    )

    assert migrated["parse_status"] == "unknown"
    assert migrated["content_quality_status"] == "unknown"
    assert migrated["source_trust_status"] == "pending"
    assert migrated["semantic_review_status"] == "unknown"


def test_eligibility_policy_is_deterministic_and_fully_audited():
    first = _derive()
    second = _derive()

    assert first == second
    assert first["status"] == "eligible"
    assert first["policy_version"] == "retrieval_eligibility_v1"
    assert first["rule_id"] == "retrieval.reviewed_trusted_evidence"
    assert first["reason"]
    assert first["audit"]["actor"] == "system:retrieval_eligibility_policy"
    assert first["audit"]["decision_method"] == "deterministic_policy"
    assert first["audit"]["input_fingerprint"].startswith("sha256:")
    assert first["audit"]["policy_fingerprint"].startswith("sha256:")


def test_pending_source_is_only_eligible_with_caution():
    governance = _governance(
        source_trust_status="pending",
        semantic_review_status="unknown",
    )

    decision = _derive(governance)

    assert decision["status"] == "eligible_with_caution"
    assert decision["rule_id"] == "retrieval.pending_governance_caution"


def test_missing_source_trace_is_deterministically_ineligible():
    decision = _derive(source_ref="", source_snapshot_id="")

    assert decision["status"] == "ineligible"
    assert decision["rule_id"] == "retrieval.missing_source_trace"
    assert "来源" in decision["reason"]


@pytest.mark.parametrize(
    ("governance", "overrides", "rule_id"),
    [
        (_governance(parse_status="failed"), {}, "retrieval.parse_not_approved"),
        (
            _governance(content_quality_status="pending_review"),
            {},
            "retrieval.content_quality_not_approved",
        ),
        (_governance(source_trust_status="untrusted"), {}, "retrieval.source_untrusted"),
        (_governance(semantic_review_status="rejected"), {}, "retrieval.semantic_rejected"),
        (
            _governance(semantic_review_status="pending"),
            {"purpose": "knowledge_fact"},
            "retrieval.knowledge_fact_requires_semantic_review",
        ),
        (
            _governance(source_trust_status="unknown"),
            {"source_type": "internal"},
            "retrieval.internal_source_requires_review",
        ),
        (
            _governance(),
            {"isolation_signals": ["semantic.short_content"]},
            "retrieval.isolated_content",
        ),
    ],
)
def test_policy_hard_gates_are_conservative(governance, overrides, rule_id):
    decision = _derive(governance, **overrides)

    assert decision["status"] == "ineligible"
    assert decision["rule_id"] == rule_id


@pytest.mark.parametrize("actor_kind", ["llm", "embedding", "reranker"])
def test_model_components_cannot_write_governance_or_eligibility(actor_kind):
    current = _governance()
    before = copy.deepcopy(current)

    with pytest.raises(GovernanceUpdateError, match="无权"):
        apply_governance_update(
            current,
            {
                "source_trust_status": "trusted",
                "semantic_review_status": "approved",
                "retrieval_eligibility": {
                    "status": "eligible",
                    "policy_version": "forged",
                    "rule_id": "forged",
                    "reason": "模型自行批准",
                    "audit": {},
                },
            },
            actor={"kind": actor_kind, "id": f"model:{actor_kind}"},
        )

    assert current == before
