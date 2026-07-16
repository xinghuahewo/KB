"""证据治理的正交状态、保守迁移与确定性检索资格。"""

from __future__ import annotations

import copy
from enum import StrEnum
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import yaml

from bgpkb import paths


SCHEMA_VERSION = "evidence_governance_state_v1"
POLICY_PATH = paths.CONFIG_DIR / "retrieval_eligibility_policy_v1.yaml"


class ParseStatus(StrEnum):
    PARSED = "parsed"
    FAILED = "failed"
    QUARANTINED = "quarantined"
    UNKNOWN = "unknown"


class ContentQualityStatus(StrEnum):
    APPROVED = "approved"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"
    UNKNOWN = "unknown"


class SourceTrustStatus(StrEnum):
    TRUSTED = "trusted"
    TRUSTED_WITH_CAUTION = "trusted_with_caution"
    UNTRUSTED = "untrusted"
    PENDING = "pending"
    UNKNOWN = "unknown"


class SemanticReviewStatus(StrEnum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


class RetrievalEligibilityStatus(StrEnum):
    ELIGIBLE = "eligible"
    ELIGIBLE_WITH_CAUTION = "eligible_with_caution"
    INELIGIBLE = "ineligible"


class GovernanceUpdateError(ValueError):
    """治理状态更新越权或非法。"""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def load_eligibility_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    policy = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if policy.get("schema_version") != "retrieval_eligibility_policy_config_v1":
        raise ValueError("retrieval eligibility policy schema_version 非法")
    if policy.get("policy_version") != "retrieval_eligibility_v1":
        raise ValueError("retrieval eligibility policy_version 与当前实现不一致")
    rule_order = policy.get("rule_order")
    rules = policy.get("rules")
    if not isinstance(rule_order, list) or len(rule_order) != len(set(rule_order)):
        raise ValueError("retrieval eligibility rule_order 必须非空且无重复")
    if not isinstance(rules, dict) or set(rule_order) != set(rules):
        raise ValueError("retrieval eligibility rule_order 与 rules 不闭合")
    policy["policy_fingerprint"] = _fingerprint(policy)
    return policy


def migrate_legacy_governance(
    legacy_record: dict[str, Any],
    *,
    source_record: dict[str, Any] | None,
    semantic_review_record: dict[str, Any] | None,
) -> dict[str, Any]:
    legacy_record = dict(legacy_record or {})
    source_record = dict(source_record or {})
    semantic_review_record = dict(semantic_review_record or {})
    input_fingerprint = _fingerprint({
        "legacy_record": legacy_record,
        "source_record": source_record,
        "semantic_review_record": semantic_review_record,
    })

    parse_raw = legacy_record.get("parse_status", legacy_record.get("parsed_status"))
    parse_status = (
        str(parse_raw)
        if parse_raw in {item.value for item in ParseStatus if item is not ParseStatus.UNKNOWN}
        else ParseStatus.UNKNOWN.value
    )
    parse_provenance = (
        "legacy.parse_status" if "parse_status" in legacy_record
        else "legacy.parsed_status" if "parsed_status" in legacy_record
        else "migration.missing_parse_status"
    )

    content_raw = legacy_record.get("content_quality_status", legacy_record.get("review_status"))
    content_mapping = {
        "approved": ContentQualityStatus.APPROVED.value,
        "pending": ContentQualityStatus.PENDING_REVIEW.value,
        "pending_review": ContentQualityStatus.PENDING_REVIEW.value,
        "unreviewed": ContentQualityStatus.PENDING_REVIEW.value,
        "rejected": ContentQualityStatus.REJECTED.value,
        "quarantined": ContentQualityStatus.QUARANTINED.value,
    }
    content_quality_status = content_mapping.get(
        str(content_raw or ""), ContentQualityStatus.UNKNOWN.value
    )
    content_provenance = (
        "legacy.content_quality_status" if "content_quality_status" in legacy_record
        else "legacy.review_status" if "review_status" in legacy_record
        else "migration.missing_content_quality_review"
    )

    source_review = str(source_record.get("review_status") or "")
    trust_level = str(source_record.get("trust_level") or "")
    if not source_record:
        source_trust_status = SourceTrustStatus.UNKNOWN.value
        source_provenance = "migration.missing_source_review"
    elif source_review in {"pending", "unreviewed", "needs_source", "pending_review"}:
        source_trust_status = SourceTrustStatus.PENDING.value
        source_provenance = "source_review.review_status"
    elif source_review == "rejected" or (source_review == "approved" and trust_level == "low"):
        source_trust_status = SourceTrustStatus.UNTRUSTED.value
        source_provenance = "source_review.review_status+trust_level"
    elif source_review == "approved" and trust_level in {"high", "internal"}:
        source_trust_status = SourceTrustStatus.TRUSTED.value
        source_provenance = "source_review.review_status+trust_level"
    elif source_review == "approved" and trust_level == "medium":
        source_trust_status = SourceTrustStatus.TRUSTED_WITH_CAUTION.value
        source_provenance = "source_review.review_status+trust_level"
    else:
        source_trust_status = SourceTrustStatus.UNKNOWN.value
        source_provenance = "migration.incomplete_source_review"

    semantic_raw = str(semantic_review_record.get("review_status") or "")
    semantic_mapping = {
        "approved": SemanticReviewStatus.APPROVED.value,
        "pending": SemanticReviewStatus.PENDING.value,
        "pending_review": SemanticReviewStatus.PENDING.value,
        "unreviewed": SemanticReviewStatus.PENDING.value,
        "needs_semantic_review": SemanticReviewStatus.PENDING.value,
        "rejected": SemanticReviewStatus.REJECTED.value,
    }
    semantic_review_status = semantic_mapping.get(
        semantic_raw, SemanticReviewStatus.UNKNOWN.value
    )
    semantic_provenance = (
        "entity_review.review_status"
        if semantic_raw
        else "migration.missing_semantic_review"
    )

    dimensions = [
        (
            "parse_status", parse_raw, parse_status, "migration.parse_status_v1",
            "只迁移显式解析状态；缺失值保持 unknown",
        ),
        (
            "content_quality_status", content_raw, content_quality_status,
            "migration.content_quality_v1",
            "旧 approved 仅作为内容质量审核结果迁移",
        ),
        (
            "source_trust_status",
            {"review_status": source_review or None, "trust_level": trust_level or None}
            if source_record else None,
            source_trust_status,
            "migration.source_trust_v1",
            "来源可信只从独立来源审核状态和 trust_level 保守迁移",
        ),
        (
            "semantic_review_status", semantic_raw or None, semantic_review_status,
            "migration.semantic_review_v1",
            "语义状态只从独立实体/语义审核记录迁移",
        ),
    ]
    audit = [
        {
            "dimension": dimension,
            "old_value": _canonical_json(old_value) if isinstance(old_value, dict) else old_value,
            "new_value": new_value,
            "rule_id": rule_id,
            "reason": reason,
            "input_fingerprint": input_fingerprint,
        }
        for dimension, old_value, new_value, rule_id, reason in dimensions
    ]
    object_id = next(
        (
            str(legacy_record[key])
            for key in ("chunk_id", "doc_id", "source_id", "id", "entity_id")
            if legacy_record.get(key)
        ),
        "unknown-object",
    )
    object_type = (
        "semantic_chunk" if legacy_record.get("chunk_id")
        else "document" if legacy_record.get("doc_id")
        else "source" if legacy_record.get("source_id")
        else "entity"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "object_id": object_id,
        "object_type": object_type,
        "parse_status": parse_status,
        "content_quality_status": content_quality_status,
        "source_trust_status": source_trust_status,
        "semantic_review_status": semantic_review_status,
        "retrieval_eligibility": None,
        "status_provenance": {
            "parse_status": parse_provenance,
            "content_quality_status": content_provenance,
            "source_trust_status": source_provenance,
            "semantic_review_status": semantic_provenance,
        },
        "migration_audit": audit,
    }


def derive_retrieval_eligibility(
    *,
    governance: dict[str, Any],
    source_ref: str,
    source_snapshot_id: str,
    purpose: str,
    source_type: str,
    isolation_signals: list[str],
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_policy = policy or load_eligibility_policy()
    if purpose not in resolved_policy.get("supported_purposes", []):
        raise ValueError(f"未知 retrieval purpose：{purpose}")

    states = {
        "parse_status": governance.get("parse_status"),
        "content_quality_status": governance.get("content_quality_status"),
        "source_trust_status": governance.get("source_trust_status"),
        "semantic_review_status": governance.get("semantic_review_status"),
    }
    input_payload = {
        "states": states,
        "source_ref": str(source_ref or ""),
        "source_snapshot_id": str(source_snapshot_id or ""),
        "purpose": purpose,
        "source_type": str(source_type or ""),
        "isolation_signals": sorted({str(item) for item in isolation_signals if item}),
    }
    has_source_trace = bool(input_payload["source_ref"]) and bool(
        re.fullmatch(r"snapshot_[0-9a-f]{64}", input_payload["source_snapshot_id"])
    )
    if not has_source_trace:
        rule_id = "retrieval.missing_source_trace"
    elif input_payload["isolation_signals"]:
        rule_id = "retrieval.isolated_content"
    elif states["parse_status"] != ParseStatus.PARSED.value:
        rule_id = "retrieval.parse_not_approved"
    elif states["content_quality_status"] != ContentQualityStatus.APPROVED.value:
        rule_id = "retrieval.content_quality_not_approved"
    elif states["source_trust_status"] == SourceTrustStatus.UNTRUSTED.value:
        rule_id = "retrieval.source_untrusted"
    elif states["semantic_review_status"] == SemanticReviewStatus.REJECTED.value:
        rule_id = "retrieval.semantic_rejected"
    elif (
        purpose == "knowledge_fact"
        and states["semantic_review_status"] != SemanticReviewStatus.APPROVED.value
    ):
        rule_id = "retrieval.knowledge_fact_requires_semantic_review"
    elif (
        source_type == "internal"
        and states["source_trust_status"]
        in {SourceTrustStatus.PENDING.value, SourceTrustStatus.UNKNOWN.value}
    ):
        rule_id = "retrieval.internal_source_requires_review"
    elif (
        states["source_trust_status"] == SourceTrustStatus.TRUSTED.value
        and states["semantic_review_status"] == SemanticReviewStatus.APPROVED.value
    ):
        rule_id = "retrieval.reviewed_trusted_evidence"
    elif (
        states["source_trust_status"]
        in {
            SourceTrustStatus.TRUSTED.value,
            SourceTrustStatus.TRUSTED_WITH_CAUTION.value,
            SourceTrustStatus.PENDING.value,
            SourceTrustStatus.UNKNOWN.value,
        }
        and states["semantic_review_status"]
        in {
            SemanticReviewStatus.APPROVED.value,
            SemanticReviewStatus.PENDING.value,
            SemanticReviewStatus.UNKNOWN.value,
        }
    ):
        rule_id = "retrieval.pending_governance_caution"
    else:
        rule_id = "retrieval.no_matching_rule"

    if rule_id not in resolved_policy["rule_order"]:
        raise ValueError(f"资格规则未登记在 rule_order：{rule_id}")
    rule = resolved_policy["rules"][rule_id]
    return {
        "status": rule["status"],
        "policy_version": resolved_policy["policy_version"],
        "rule_id": rule_id,
        "reason": rule["reason"],
        "audit": {
            "actor": resolved_policy["policy_actor"],
            "decision_method": "deterministic_policy",
            "input_fingerprint": _fingerprint(input_payload),
            "policy_fingerprint": resolved_policy["policy_fingerprint"],
        },
    }


def apply_governance_update(
    current: dict[str, Any],
    patch: dict[str, Any],
    *,
    actor: dict[str, str],
) -> dict[str, Any]:
    protected_fields = {
        "parse_status",
        "content_quality_status",
        "source_trust_status",
        "semantic_review_status",
        "retrieval_eligibility",
    }
    changed_protected = sorted(protected_fields & set(patch))
    actor_kind = str(actor.get("kind") or "")
    actor_id = str(actor.get("id") or "")
    policy = load_eligibility_policy()
    if actor_kind in set(policy["forbidden_direct_actor_kinds"]) and changed_protected:
        raise GovernanceUpdateError(
            f"{actor_kind} 无权修改治理状态：{', '.join(changed_protected)}"
        )
    if "retrieval_eligibility" in patch and not (
        actor_kind == "policy" and actor_id == policy["policy_actor"]
    ):
        raise GovernanceUpdateError("检索资格只能由版本化确定性 policy 写入，当前 actor 无权修改")
    unknown = sorted(set(patch) - set(current))
    if unknown:
        raise GovernanceUpdateError(f"治理更新包含未知字段：{', '.join(unknown)}")
    updated = copy.deepcopy(current)
    updated.update(copy.deepcopy(patch))
    return updated
