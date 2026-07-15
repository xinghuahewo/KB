"""证据绑定知识候选的纯领域契约。"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping


SCHEMA_VERSION = "evidence_bound_knowledge_candidate_v1"
ALLOWED_CANDIDATE_TYPES = {"entity", "relation", "fact"}
MODEL_FIELDS = {"candidate_type", "payload", "evidence_ids", "confidence", "reason"}
FORBIDDEN_GOVERNANCE_FIELDS = {
    "status",
    "governance",
    "review_status",
    "parse_status",
    "content_quality_status",
    "source_trust_status",
    "semantic_review_status",
    "retrieval_eligibility",
}
HEX_64 = re.compile(r"^[a-f0-9]{64}$")
PAYLOAD_FIELDS = {
    "entity": ({"type", "entity_kind", "canonical_name", "aliases"}, {"type", "entity_kind", "canonical_name"}),
    "relation": ({"type", "subject_ref", "predicate", "object_ref"}, {"type", "subject_ref", "predicate", "object_ref"}),
    "fact": ({"type", "claim"}, {"type", "claim"}),
}


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _valid_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_payload(candidate_type: Any, payload: Any) -> list[str]:
    if candidate_type not in ALLOWED_CANDIDATE_TYPES:
        return ["candidate_type"]
    if not isinstance(payload, dict):
        return ["payload"]
    allowed, required = PAYLOAD_FIELDS[candidate_type]
    errors = []
    if set(payload) - allowed or required - set(payload):
        errors.append("payload")
    if payload.get("type") != candidate_type:
        errors.append("payload_type")
    for field in required - {"type"}:
        if not _valid_non_empty_string(payload.get(field)):
            errors.append("payload")
    aliases = payload.get("aliases", [])
    if candidate_type == "entity" and (
        not isinstance(aliases, list)
        or len(aliases) != len(set(aliases))
        or any(not _valid_non_empty_string(alias) for alias in aliases)
    ):
        errors.append("payload")
    return list(dict.fromkeys(errors))


def build_input_fingerprint(
    *,
    candidate_type: str,
    payload: Mapping[str, Any],
    evidence_ids: list[str],
    evidence_by_id: Mapping[str, Mapping[str, Any]],
    provider: str,
    model_revision: str,
    prompt_version: str,
) -> str:
    """绑定完整证据内容身份和生成配置，而不是只绑定候选名称。"""
    evidence_inputs = [
        {
            "evidence_id": evidence_id,
            "content_hash": evidence_by_id[evidence_id]["content_hash"],
            "source_ref": evidence_by_id[evidence_id]["source_ref"],
        }
        for evidence_id in sorted(evidence_ids)
    ]
    return _fingerprint(
        {
            "candidate_type": candidate_type,
            "payload": payload,
            "evidence": evidence_inputs,
            "provider": provider,
            "model_revision": model_revision,
            "prompt_version": prompt_version,
        }
    )


def build_candidate_id(
    candidate_type: str, payload: Mapping[str, Any], input_fingerprint: str
) -> str:
    payload_fingerprint = _fingerprint(payload)[:16]
    return (
        f"knowledge_candidate__{candidate_type}__{payload_fingerprint}__"
        f"{input_fingerprint}"
    )


def normalize_model_suggestion(
    suggestion: Any,
    *,
    evidence_by_id: Mapping[str, Mapping[str, Any]],
    provider: str,
    model_revision: str,
    prompt_version: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    """校验模型语义建议，并由系统生成全部治理与身份字段。"""
    if not isinstance(suggestion, dict):
        return None, ["candidate"]

    errors: list[str] = []
    fields = set(suggestion)
    if fields & FORBIDDEN_GOVERNANCE_FIELDS:
        errors.append("forbidden_governance_field")
    if fields - MODEL_FIELDS - FORBIDDEN_GOVERNANCE_FIELDS:
        errors.append("additional_property")
    for field in sorted(MODEL_FIELDS - fields):
        errors.append(f"missing_{field}")

    candidate_type = suggestion.get("candidate_type")
    payload = suggestion.get("payload")
    errors.extend(_validate_payload(candidate_type, payload))

    evidence_ids = suggestion.get("evidence_ids")
    if (
        not isinstance(evidence_ids, list)
        or not evidence_ids
        or len(evidence_ids) != len(set(evidence_ids))
        or any(not _valid_non_empty_string(value) for value in evidence_ids)
    ):
        errors.append("evidence_ids")
        evidence_ids = []
    else:
        for evidence_id in evidence_ids:
            evidence = evidence_by_id.get(evidence_id)
            if evidence is None:
                errors.append("unknown_evidence_id")
                continue
            if not HEX_64.fullmatch(str(evidence.get("content_hash", ""))):
                errors.append("evidence_content_hash")
            if not _valid_non_empty_string(evidence.get("source_ref")):
                errors.append("source_ref")

    confidence = suggestion.get("confidence")
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0 <= confidence <= 1
    ):
        errors.append("confidence")
    if not _valid_non_empty_string(suggestion.get("reason")):
        errors.append("reason")
    for field, value in (
        ("provider", provider),
        ("model_revision", model_revision),
        ("prompt_version", prompt_version),
    ):
        if not _valid_non_empty_string(value):
            errors.append(field)

    errors = list(dict.fromkeys(errors))
    if errors:
        return None, errors

    ordered_evidence_ids = sorted(evidence_ids)
    input_fingerprint = build_input_fingerprint(
        candidate_type=candidate_type,
        payload=payload,
        evidence_ids=ordered_evidence_ids,
        evidence_by_id=evidence_by_id,
        provider=provider,
        model_revision=model_revision,
        prompt_version=prompt_version,
    )
    source_refs = sorted(
        {evidence_by_id[evidence_id]["source_ref"] for evidence_id in ordered_evidence_ids}
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_id": build_candidate_id(candidate_type, payload, input_fingerprint),
        "candidate_type": candidate_type,
        "payload": payload,
        "evidence_ids": ordered_evidence_ids,
        "source_refs": source_refs,
        "input_fingerprint": input_fingerprint,
        "confidence": confidence,
        "reason": suggestion["reason"],
        "provider": provider,
        "model_revision": model_revision,
        "prompt_version": prompt_version,
        "governance": {"review_status": "pending_review"},
    }, []
