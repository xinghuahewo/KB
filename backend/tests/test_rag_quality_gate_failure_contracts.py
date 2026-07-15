from __future__ import annotations

import copy


def _passing_report() -> dict:
    return {
        "schema_version": "rag_release_gate_evidence_v1",
        "candidate": {
            "release_id": "candidate-2026-07-14",
            "manifest_hash": "sha256:" + "a" * 64,
            "manifest_generated_at": "2026-07-14T08:00:00Z",
            "code_commit": "0123456789abcdef0123456789abcdef01234567",
        },
        "report": {
            "started_at": "2026-07-14T08:01:00Z",
            "completed_at": "2026-07-14T08:02:00Z",
        },
        "evaluations": {
            "retrieval": {"status": "passed", "hard_failure_count": 0},
            "answer": {"status": "passed", "hard_failure_count": 0, "samples": []},
            "performance": {
                "status": "passed",
                "hard_failure_count": 0,
                "index_mode": "fast_numpy",
                "degraded": False,
            },
        },
        "models": {
            "embedding": {"model": "BAAI/bge-m3", "revision": "bge-m3@rev-a"},
            "reranker": {
                "model": "BAAI/bge-reranker-v2-m3",
                "revision": "bge-reranker-v2-m3@rev-a",
            },
            "llm": {"model": "deepseek-chat", "revision": "deepseek-chat@rev-a"},
        },
        "prompt_version": "grounded_answer_prompt_v1",
    }


def _evaluate(report: dict):
    from bgpkb.domain.rag_quality_gates import evaluate_release_gate

    return evaluate_release_gate(
        report,
        expected_release_id="candidate-2026-07-14",
        expected_manifest_hash="sha256:" + "a" * 64,
        expected_code_commit="0123456789abcdef0123456789abcdef01234567",
        expected_models={
            "embedding": {"model": "BAAI/bge-m3", "revision": "bge-m3@rev-a"},
            "reranker": {
                "model": "BAAI/bge-reranker-v2-m3",
                "revision": "bge-reranker-v2-m3@rev-a",
            },
            "llm": {"model": "deepseek-chat", "revision": "deepseek-chat@rev-a"},
        },
        expected_prompt_version="grounded_answer_prompt_v1",
    )


def test_hard_evaluation_failure_propagates_nonzero_exit_code():
    report = _passing_report()
    report["evaluations"]["retrieval"] = {
        "status": "failed",
        "hard_failure_count": 1,
    }

    decision = _evaluate(report)

    assert decision.status == "failed"
    assert decision.exit_code != 0
    assert decision.failure_codes == ("evaluation_hard_failure:retrieval",)


def test_blocking_skip_is_a_release_failure_not_a_successful_skip():
    report = _passing_report()
    report["evaluations"]["answer"] = {
        "status": "skipped_blocking",
        "hard_failure_count": 0,
        "reason": "required_deepseek_revision_unavailable",
        "samples": [],
    }

    decision = _evaluate(report)

    assert decision.exit_code != 0
    assert decision.failure_codes == ("blocking_skip:answer",)


def test_stale_report_is_rejected_by_manifest_binding_and_time_order():
    report = _passing_report()
    report["candidate"]["manifest_hash"] = "sha256:" + "b" * 64
    report["report"]["started_at"] = "2026-07-14T07:59:59Z"

    decision = _evaluate(report)

    assert decision.exit_code != 0
    assert "stale_report:manifest_hash_mismatch" in decision.failure_codes
    assert "stale_report:report_predates_manifest" in decision.failure_codes


def test_context_valid_but_semantically_wrong_citation_fails_support_check():
    report = _passing_report()
    report["evaluations"]["answer"]["samples"] = [
        {
            "question_id": "answer-route-leak-definition",
            "context_evidence_ids": ["ev-rfc7908", "ev-rfc6811"],
            "expected_claims": [
                {
                    "claim_id": "claim-route-leak-definition",
                    "acceptable_evidence_sets": [["ev-rfc7908"]],
                }
            ],
            "actual_claims": [
                {
                    "claim_id": "claim-route-leak-definition",
                    "evidence_ids": ["ev-rfc7908", "ev-rfc6811"],
                }
            ],
        }
    ]

    decision = _evaluate(report)

    assert decision.exit_code != 0
    assert decision.failure_codes == (
        "citation_support_mismatch:answer-route-leak-definition:claim-route-leak-definition",
    )


def test_jsonl_scan_fallback_is_a_performance_release_failure():
    report = copy.deepcopy(_passing_report())
    report["evaluations"]["performance"].update(
        {"index_mode": "legacy_jsonl_scan", "degraded": True}
    )

    decision = _evaluate(report)

    assert decision.exit_code != 0
    assert "jsonl_scan_degradation:index_mode" in decision.failure_codes
    assert "jsonl_scan_degradation:degraded" in decision.failure_codes


def test_report_freshness_binds_code_models_prompt_and_complete_time_range():
    report = _passing_report()
    report["candidate"]["code_commit"] = "f" * 40
    report["models"]["embedding"]["revision"] = "bge-m3@stale"
    report["models"]["reranker"]["model"] = "wrong-reranker"
    report["models"]["llm"]["revision"] = "deepseek-chat@stale"
    report["prompt_version"] = "grounded_answer_prompt_stale"
    report["report"]["completed_at"] = "2026-07-14T08:00:30Z"

    decision = _evaluate(report)

    assert decision.exit_code == 1
    assert "stale_report:code_commit_mismatch" in decision.failure_codes
    assert "stale_report:model_binding_mismatch:embedding" in decision.failure_codes
    assert "stale_report:model_binding_mismatch:reranker" in decision.failure_codes
    assert "stale_report:model_binding_mismatch:llm" in decision.failure_codes
    assert "stale_report:prompt_version_mismatch" in decision.failure_codes
    assert "stale_report:invalid_time_range" in decision.failure_codes


def test_evaluation_envelope_records_all_release_freshness_inputs():
    from bgpkb.domain.rag_quality_gates import build_evaluation_envelope

    envelope = build_evaluation_envelope(
        release_id="candidate-2026-07-14",
        manifest_hash="sha256:" + "a" * 64,
        manifest_generated_at="2026-07-14T08:00:00Z",
        code_commit="0123456789abcdef0123456789abcdef01234567",
        models=_passing_report()["models"],
        prompt_version="grounded_answer_prompt_v1",
        started_at="2026-07-14T08:01:00Z",
        completed_at="2026-07-14T08:02:00Z",
        evaluations=_passing_report()["evaluations"],
    )

    assert envelope["schema_version"] == "rag_release_gate_evidence_v1"
    assert envelope["candidate"]["code_commit"].startswith("012345")
    assert set(envelope["models"]) == {"embedding", "reranker", "llm"}
    assert envelope["prompt_version"] == "grounded_answer_prompt_v1"
    assert envelope["report"] == {
        "started_at": "2026-07-14T08:01:00Z",
        "completed_at": "2026-07-14T08:02:00Z",
    }
