import json

import pytest

from bgpkb.domain.knowledge_candidates import normalize_model_suggestion
from bgpkb.publishing.build_knowledge_candidate_decision_audit import (
    audit_knowledge_candidate_decisions,
)
from bgpkb.workflows.apply_knowledge_candidate_decisions import (
    apply_knowledge_candidate_decisions,
    validate_serving_knowledge_inputs,
)


def _evidence():
    return {
        "evidence_id": "evidence-rfc6811-1",
        "content_hash": "a" * 64,
        "source_ref": "rfc6811",
    }


def _candidate(
    candidate_type="entity",
    *,
    canonical_name="RPKI",
    object_ref="entity:rpki",
):
    payloads = {
        "entity": {
            "type": "entity",
            "entity_kind": "protocol",
            "canonical_name": canonical_name,
        },
        "relation": {
            "type": "relation",
            "subject_ref": "entity:router",
            "predicate": "validates_with",
            "object_ref": object_ref,
        },
        "fact": {"type": "fact", "claim": "RPKI supports origin validation."},
    }
    candidate, errors = normalize_model_suggestion(
        {
            "candidate_type": candidate_type,
            "payload": payloads[candidate_type],
            "evidence_ids": ["evidence-rfc6811-1"],
            "confidence": 0.9,
            "reason": "证据充分。",
        },
        evidence_by_id={"evidence-rfc6811-1": _evidence()},
        provider="deterministic",
        model_revision="knowledge-term-rules-v1",
        prompt_version="knowledge_candidate_deterministic_v1",
    )
    assert errors == []
    return candidate


def _decision(candidate, value="approved", fingerprint=None, **overrides):
    record = {
        "candidate_id": candidate["candidate_id"],
        "input_fingerprint": fingerprint or candidate["input_fingerprint"],
        "decision": value,
        "reviewer": "reviewer@example.com",
        "reviewed_at": "2026-07-14T18:00:00+08:00",
        "decision_note": "已核对原始证据。",
    }
    record.update(overrides)
    return record


def _config():
    return {
        "outputs": {
            "candidates": "data/governance/knowledge_candidates.jsonl",
            "decision_audit": "data/governance/knowledge_candidate_decision_audit.jsonl",
            "apply_preview": "data/governance/knowledge_candidate_apply_preview.jsonl",
            "approved_candidates": "data/governance/approved_knowledge_candidates.jsonl",
            "decision_apply_report": "data/governance/knowledge_candidate_apply_report.json",
        }
    }


def _write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def test_stale_fingerprint_and_missing_reviewer_cannot_be_applied():
    candidate = _candidate()
    decisions = [
        _decision(candidate, fingerprint="b" * 64),
        _decision(candidate, reviewer="", candidate_id=candidate["candidate_id"] + "-copy"),
    ]
    copied_candidate = dict(candidate, candidate_id=candidate["candidate_id"] + "-copy")

    result = audit_knowledge_candidate_decisions(
        [candidate, copied_candidate], decisions
    )

    assert {record["audit_status"] for record in result["records"]} == {
        "blocked_invalid_input"
    }
    assert all(record["write_eligible"] is False for record in result["records"])


def test_conflicting_approved_relations_are_blocked_as_one_group():
    first = _candidate("relation", object_ref="entity:rpki")
    second = _candidate("relation", object_ref="entity:manual_filter")

    result = audit_knowledge_candidate_decisions(
        [first, second], [_decision(first), _decision(second)]
    )

    assert {record["audit_status"] for record in result["records"]} == {
        "blocked_conflict"
    }
    assert all(record["write_eligible"] is False for record in result["records"])
    assert result["has_blockers"] is True


def test_dry_run_writes_preview_without_touching_approved_collection(tmp_path):
    candidate = _candidate()
    audit = {
        **_decision(candidate),
        "submitted_input_fingerprint": candidate["input_fingerprint"],
        "current_input_fingerprint": candidate["input_fingerprint"],
        "audit_status": "ready_to_apply",
        "write_eligible": True,
        "reason": "人工批准且审计通过。",
    }
    config = _config()
    outputs = config["outputs"]
    _write_jsonl(tmp_path / outputs["candidates"], [candidate])
    _write_jsonl(tmp_path / outputs["decision_audit"], [audit])
    approved_path = tmp_path / outputs["approved_candidates"]
    approved_path.parent.mkdir(parents=True, exist_ok=True)
    approved_path.write_text("canary\n", encoding="utf-8")

    result = apply_knowledge_candidate_decisions(tmp_path, config, write=False)

    assert result == {"ready_count": 1, "skipped_count": 0, "written": False}
    assert approved_path.read_text(encoding="utf-8") == "canary\n"
    preview = (tmp_path / outputs["apply_preview"]).read_text(encoding="utf-8")
    assert '"action": "apply"' in preview


def test_explicit_apply_only_writes_current_audited_candidates(tmp_path):
    ready = _candidate("entity", canonical_name="RPKI")
    stale = _candidate("entity", canonical_name="ROA")
    config = _config()
    outputs = config["outputs"]
    _write_jsonl(tmp_path / outputs["candidates"], [ready, stale])
    _write_jsonl(
        tmp_path / outputs["decision_audit"],
        [
            {
                **_decision(ready),
                "submitted_input_fingerprint": ready["input_fingerprint"],
                "current_input_fingerprint": ready["input_fingerprint"],
                "audit_status": "ready_to_apply",
                "write_eligible": True,
                "reason": "人工批准且审计通过。",
            },
            {
                **_decision(stale),
                "submitted_input_fingerprint": "b" * 64,
                "current_input_fingerprint": stale["input_fingerprint"],
                "audit_status": "blocked_invalid_input",
                "write_eligible": False,
                "reason": "输入指纹已变化。",
            },
        ],
    )

    result = apply_knowledge_candidate_decisions(tmp_path, config, write=True)
    approved = [
        json.loads(line)
        for line in (tmp_path / outputs["approved_candidates"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    ]

    assert result == {"ready_count": 1, "skipped_count": 1, "written": True}
    assert [record["candidate_id"] for record in approved] == [ready["candidate_id"]]
    assert approved[0]["application_status"] == "approved_for_next_release"
    validate_serving_knowledge_inputs(approved)


def test_pending_candidates_are_rejected_from_serving_inputs():
    with pytest.raises(ValueError, match="approved_for_next_release"):
        validate_serving_knowledge_inputs([_candidate()])
