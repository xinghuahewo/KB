"""Context Pack 证据对象与结构化回答的纯领域契约。"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

from bgpkb import paths


EVIDENCE_SCHEMA_VERSION = "evidence_v1"
CONTEXT_GROUP_SCHEMA_VERSION = "context_group_v1"
GROUNDED_CLAIM_SCHEMA_VERSION = "grounded_claim_v1"
GROUNDED_ANSWER_SCHEMA_VERSION = "grounded_answer_v1"


class GroundingValidationError(ValueError):
    """结构化回答未满足 evidence 闭包时的稳定错误。"""

    def __init__(self, code: str, message: str, details: Sequence[str] | None = None):
        self.code = code
        self.details = list(details or [])
        super().__init__(f"{code}: {message}")


def _sha256_text(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_evidence(
    *,
    chunk_id: str,
    doc_id: str,
    source_ref: str,
    title: str,
    section_path: Sequence[str],
    content: str,
    governance: Mapping[str, Any],
    retrieval_scores: Mapping[str, Any],
    context_group_id: str,
    member_index: int,
    start_char: int,
    end_char: int,
) -> dict[str, Any]:
    """以 chunk、来源和内容 hash 生成稳定 Evidence 身份。"""
    content_hash = _sha256_text(content)
    evidence_id = (
        f"{EVIDENCE_SCHEMA_VERSION}_"
        f"{_fingerprint({'chunk_id': chunk_id, 'source_ref': source_ref, 'content_hash': content_hash})}"
    )
    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "evidence_id": evidence_id,
        "chunk_id": chunk_id,
        "doc_id": doc_id,
        "source_ref": source_ref,
        "title": title,
        "section_path": list(section_path),
        "content": content,
        "content_hash": content_hash,
        "member_boundary": {
            "context_group_id": context_group_id,
            "member_index": member_index,
            "start_char": start_char,
            "end_char": end_char,
        },
        "governance": dict(governance),
        "retrieval_scores": {
            "score": retrieval_scores.get("score"),
            "fusion_score": retrieval_scores.get("fusion_score"),
            "rerank_score": retrieval_scores.get("rerank_score"),
        },
    }


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((paths.SCHEMAS_DIR / name).read_text(encoding="utf-8"))


def _schema_errors(schema_name: str, payload: Any) -> list[str]:
    validator = Draft202012Validator(_load_schema(schema_name))
    errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path))
    return [
        f"{'.'.join(str(part) for part in error.absolute_path) or '$'}: {error.message}"
        for error in errors
    ]


def parse_grounded_answer(payload: Any) -> dict[str, Any]:
    """只接受 JSON 对象，不从自由文本或 Markdown 中猜测结构。"""
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise GroundingValidationError(
                "invalid_json", "回答不是合法 JSON 对象", [str(exc)]
            ) from exc
    if not isinstance(payload, dict):
        raise GroundingValidationError("schema_invalid", "回答根节点必须是 JSON 对象")
    return dict(payload)


def validate_grounded_answer(payload: Any, evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """校验回答 Schema、证据闭包、事实 claim 引用和顶层证据并集。"""
    parsed = parse_grounded_answer(payload)

    claims = parsed.get("claims")
    if isinstance(claims, list):
        for index, claim in enumerate(claims):
            if (
                isinstance(claim, dict)
                and claim.get("claim_type") == "factual"
                and not claim.get("evidence_ids")
            ):
                raise GroundingValidationError(
                    "claim_without_evidence",
                    f"事实 claim[{index}] 没有 evidence_id",
                )

    schema_errors = _schema_errors("grounded_answer_v1.schema.json", parsed)
    if schema_errors:
        raise GroundingValidationError(
            "schema_invalid", "GroundedAnswer Schema 校验失败", schema_errors
        )

    available_ids: set[str] = set()
    for index, item in enumerate(evidence):
        item_errors = _schema_errors("evidence_v1.schema.json", item)
        if item_errors:
            raise GroundingValidationError(
                "invalid_context_evidence",
                f"Context Pack evidence[{index}] 非法",
                item_errors,
            )
        evidence_id = str(item["evidence_id"])
        if evidence_id in available_ids:
            raise GroundingValidationError(
                "duplicate_context_evidence_id", f"Context Pack evidence_id 重复：{evidence_id}"
            )
        available_ids.add(evidence_id)

    claim_evidence_ids: list[str] = []
    for claim in parsed["claims"]:
        for evidence_id in claim["evidence_ids"]:
            if evidence_id not in available_ids:
                raise GroundingValidationError(
                    "unknown_evidence_id", f"claim 引用了本次 Context Pack 之外的 ID：{evidence_id}"
                )
            if evidence_id not in claim_evidence_ids:
                claim_evidence_ids.append(evidence_id)

    top_level_ids = parsed["evidence_ids"]
    unknown_top_level = [item for item in top_level_ids if item not in available_ids]
    if unknown_top_level:
        raise GroundingValidationError(
            "unknown_evidence_id",
            f"回答顶层引用了本次 Context Pack 之外的 ID：{', '.join(unknown_top_level)}",
        )
    if set(top_level_ids) != set(claim_evidence_ids):
        raise GroundingValidationError(
            "evidence_set_mismatch", "顶层 evidence_ids 必须等于全部 claim evidence_ids 的并集"
        )
    return parsed
