import json

import pytest
from jsonschema import Draft202012Validator

from bgpkb import paths
from bgpkb.domain.knowledge_candidates import normalize_model_suggestion
from bgpkb.workflows.extract_knowledge_candidates import run_candidate_extraction


def _evidence(content_hash="a" * 64):
    return {
        "evidence_id": "evidence-rfc6811-1",
        "content_hash": content_hash,
        "source_ref": "rfc6811",
        "content": "RPKI origin validation compares a route origin with validated ROA payloads.",
    }


def _suggestion(candidate_type="entity", **overrides):
    payloads = {
        "entity": {
            "type": "entity",
            "entity_kind": "protocol",
            "canonical_name": "RPKI",
        },
        "relation": {
            "type": "relation",
            "subject_ref": "entity:router",
            "predicate": "validates_with",
            "object_ref": "entity:rpki",
        },
        "fact": {
            "type": "fact",
            "claim": "RPKI can support route-origin validation.",
        },
    }
    suggestion = {
        "candidate_type": candidate_type,
        "payload": payloads[candidate_type],
        "evidence_ids": ["evidence-rfc6811-1"],
        "confidence": 0.91,
        "reason": "证据直接描述了该知识项。",
    }
    suggestion.update(overrides)
    return suggestion


def _extraction_config():
    return {
        "version": "knowledge_candidate_extraction_v1",
        "default_provider": "disabled",
        "providers": {
            "deterministic": {
                "model_revision": "knowledge-term-rules-v1",
                "prompt_version": "knowledge_candidate_deterministic_v1",
                "terms": [
                    {
                        "term": "RPKI",
                        "entity_kind": "protocol",
                        "aliases": ["Resource Public Key Infrastructure"],
                    }
                ],
            },
            "deepseek": {
                "api_key_env": "DEEPSEEK_API_KEY",
                "model_revision": "deepseek-chat@2026-07-14",
                "prompt_version": "knowledge_candidate_v1",
            },
        },
        "inputs": {"evidence": "data/candidate/evidence.jsonl"},
        "outputs": {
            "candidates": "data/governance/knowledge_candidates.jsonl",
            "candidate_errors": "data/governance/knowledge_candidate_errors.jsonl",
            "report": "data/governance/knowledge_candidate_report.json",
        },
    }


def _write_evidence(root, evidence=None):
    path = root / "data/candidate/evidence.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(evidence or _evidence()) + "\n", encoding="utf-8")
    return path


@pytest.mark.parametrize("candidate_type", ["entity", "relation", "fact"])
def test_entity_relation_and_fact_candidates_without_evidence_are_invalid(candidate_type):
    candidate, errors = normalize_model_suggestion(
        _suggestion(candidate_type, evidence_ids=[]),
        evidence_by_id={"evidence-rfc6811-1": _evidence()},
        provider="deepseek",
        model_revision="deepseek-chat@2026-07-14",
        prompt_version="knowledge_candidate_v1",
    )

    assert candidate is None
    assert "evidence_ids" in errors


@pytest.mark.parametrize("field", ["status", "source_trust_status", "retrieval_eligibility"])
def test_model_cannot_return_approval_trust_or_eligibility_fields(field):
    candidate, errors = normalize_model_suggestion(
        _suggestion(**{field: "approved"}),
        evidence_by_id={"evidence-rfc6811-1": _evidence()},
        provider="deepseek",
        model_revision="deepseek-chat@2026-07-14",
        prompt_version="knowledge_candidate_v1",
    )

    assert candidate is None
    assert "forbidden_governance_field" in errors


def test_evidence_content_change_changes_input_fingerprint_and_candidate_id():
    first, first_errors = normalize_model_suggestion(
        _suggestion(),
        evidence_by_id={"evidence-rfc6811-1": _evidence("a" * 64)},
        provider="deepseek",
        model_revision="deepseek-chat@2026-07-14",
        prompt_version="knowledge_candidate_v1",
    )
    second, second_errors = normalize_model_suggestion(
        _suggestion(),
        evidence_by_id={"evidence-rfc6811-1": _evidence("b" * 64)},
        provider="deepseek",
        model_revision="deepseek-chat@2026-07-14",
        prompt_version="knowledge_candidate_v1",
    )

    assert first_errors == second_errors == []
    assert first["input_fingerprint"] != second["input_fingerprint"]
    assert first["candidate_id"] != second["candidate_id"]


def test_evidence_bound_candidate_schema_is_closed_pending_and_auditable():
    candidate, errors = normalize_model_suggestion(
        _suggestion(),
        evidence_by_id={"evidence-rfc6811-1": _evidence()},
        provider="deepseek",
        model_revision="deepseek-chat@2026-07-14",
        prompt_version="knowledge_candidate_v1",
    )
    schema = json.loads(
        (paths.SCHEMAS_DIR / "evidence_bound_knowledge_candidate_v1.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert errors == []
    Draft202012Validator(schema).validate(candidate)
    assert candidate["schema_version"] == "evidence_bound_knowledge_candidate_v1"
    assert candidate["evidence_ids"] == ["evidence-rfc6811-1"]
    assert candidate["source_refs"] == ["rfc6811"]
    assert candidate["governance"] == {"review_status": "pending_review"}
    assert candidate["provider"] == "deepseek"
    assert candidate["model_revision"] == "deepseek-chat@2026-07-14"
    assert candidate["prompt_version"] == "knowledge_candidate_v1"


@pytest.mark.parametrize(
    ("field", "first_value", "second_value"),
    [
        ("provider", "deepseek", "deterministic"),
        ("model_revision", "deepseek-chat@v1", "deepseek-chat@v2"),
        ("prompt_version", "knowledge_candidate_v1", "knowledge_candidate_v2"),
    ],
)
def test_provider_model_or_prompt_change_invalidates_candidate_identity(
    field, first_value, second_value
):
    kwargs = {
        "provider": "deepseek",
        "model_revision": "deepseek-chat@v1",
        "prompt_version": "knowledge_candidate_v1",
    }
    first_kwargs = dict(kwargs, **{field: first_value})
    second_kwargs = dict(kwargs, **{field: second_value})

    first, first_errors = normalize_model_suggestion(
        _suggestion(), evidence_by_id={"evidence-rfc6811-1": _evidence()}, **first_kwargs
    )
    second, second_errors = normalize_model_suggestion(
        _suggestion(), evidence_by_id={"evidence-rfc6811-1": _evidence()}, **second_kwargs
    )

    assert first_errors == second_errors == []
    assert first["input_fingerprint"] != second["input_fingerprint"]
    assert first["candidate_id"] != second["candidate_id"]


def test_missing_llm_key_is_skipped_without_overwriting_existing_candidates(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    evidence_path = tmp_path / "data/candidate/evidence.jsonl"
    candidate_path = tmp_path / "data/governance/knowledge_candidates.jsonl"
    error_path = tmp_path / "data/governance/knowledge_candidate_errors.jsonl"
    report_path = tmp_path / "data/governance/knowledge_candidate_report.json"
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_text(json.dumps(_evidence()) + "\n", encoding="utf-8")
    candidate_path.parent.mkdir(parents=True)
    candidate_path.write_text("canary\n", encoding="utf-8")
    error_path.write_text("error-canary\n", encoding="utf-8")
    report_path.write_text("report-canary\n", encoding="utf-8")
    config = _extraction_config()

    result = run_candidate_extraction(tmp_path, config, provider="deepseek")

    assert result == {
        "status": "skipped",
        "provider": "deepseek",
        "reason": "missing_api_key",
    }
    assert candidate_path.read_text(encoding="utf-8") == "canary\n"
    assert error_path.read_text(encoding="utf-8") == "error-canary\n"
    assert report_path.read_text(encoding="utf-8") == "report-canary\n"


def test_default_disabled_provider_makes_no_request_and_writes_no_outputs(tmp_path):
    _write_evidence(tmp_path)

    class UnexpectedClient:
        def generate_knowledge_candidates(self, evidence, prompt_version):
            raise AssertionError("默认禁用时不得调用模型")

    result = run_candidate_extraction(
        tmp_path, _extraction_config(), client=UnexpectedClient()
    )

    assert result == {
        "status": "skipped",
        "provider": "disabled",
        "reason": "provider_not_enabled",
    }
    assert not (tmp_path / "data/governance").exists()


def test_explicit_deterministic_provider_generates_pending_evidence_bound_candidates(tmp_path):
    _write_evidence(tmp_path)

    result = run_candidate_extraction(
        tmp_path, _extraction_config(), provider="deterministic"
    )
    candidates = [
        json.loads(line)
        for line in (tmp_path / "data/governance/knowledge_candidates.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    ]

    assert result["status"] == "generated"
    assert result["candidate_count"] == 1
    assert result["error_count"] == 0
    assert candidates[0]["payload"]["canonical_name"] == "RPKI"
    assert candidates[0]["governance"] == {"review_status": "pending_review"}
    assert candidates[0]["evidence_ids"] == ["evidence-rfc6811-1"]
    assert candidates[0]["provider"] == "deterministic"


def test_llm_overreach_is_quarantined_as_error_without_approved_candidate(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    _write_evidence(tmp_path)

    class OverreachingClient:
        def generate_knowledge_candidates(self, evidence, prompt_version):
            return {
                "ok": True,
                "model": "deepseek-chat@2026-07-14",
                "content": json.dumps(
                    {"candidates": [_suggestion(status="approved")]},
                    ensure_ascii=False,
                ),
            }

    result = run_candidate_extraction(
        tmp_path,
        _extraction_config(),
        provider="deepseek",
        client=OverreachingClient(),
    )
    candidate_text = (
        tmp_path / "data/governance/knowledge_candidates.jsonl"
    ).read_text(encoding="utf-8")
    errors = [
        json.loads(line)
        for line in (tmp_path / "data/governance/knowledge_candidate_errors.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    ]

    assert result["candidate_count"] == 0
    assert result["error_count"] == 1
    assert candidate_text == ""
    assert errors[0]["error_code"] == "invalid_candidate"
    assert "forbidden_governance_field" in errors[0]["validation_errors"]


def test_model_unavailable_is_skipped_without_overwriting_existing_results(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    _write_evidence(tmp_path)
    candidate_path = tmp_path / "data/governance/knowledge_candidates.jsonl"
    candidate_path.parent.mkdir(parents=True)
    candidate_path.write_text("canary\n", encoding="utf-8")

    class UnavailableClient:
        def generate_knowledge_candidates(self, evidence, prompt_version):
            return {"ok": False, "error_code": "model_unavailable"}

    result = run_candidate_extraction(
        tmp_path,
        _extraction_config(),
        provider="deepseek",
        client=UnavailableClient(),
    )

    assert result == {
        "status": "skipped",
        "provider": "deepseek",
        "reason": "model_unavailable",
    }
    assert candidate_path.read_text(encoding="utf-8") == "canary\n"
