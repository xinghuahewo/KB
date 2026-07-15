from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

import pytest

from test_publish_index_closure_v1 import _build_candidate


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _ownership(path: Path, *, assigned: bool = True) -> Path:
    owner = "rag-owner" if assigned else None
    reviewer = "rag-reviewer" if assigned else None
    if assigned:
        approval = path.parent / "review" / "approval.json"
        approval.parent.mkdir(parents=True, exist_ok=True)
        approval.write_text(json.dumps({
            "schema_version": "rag_gold_approval_evidence_v1",
            "owner": owner,
            "reviewer": reviewer,
            "datasets": ["answer_gold", "retrieval_gold"],
            "authorization_method": "test_fixture",
        }), encoding="utf-8")
    path.write_text(
        "\n".join([
            "schema_version: rag_eval_ownership_v1",
            "datasets:",
            "  retrieval_gold:",
            f"    owner_status: {'assigned' if assigned else 'unassigned'}",
            f"    owner: {owner or 'null'}",
            f"    reviewers: [{reviewer}]" if reviewer else "    reviewers: []",
            "    change_control: pull_request",
            "    approval_evidence: review/approval.json" if assigned else "    approval_evidence: null",
            "  answer_gold:",
            f"    owner_status: {'assigned' if assigned else 'unassigned'}",
            f"    owner: {owner or 'null'}",
            f"    reviewers: [{reviewer}]" if reviewer else "    reviewers: []",
            "    change_control: pull_request",
            "    approval_evidence: review/approval.json" if assigned else "    approval_evidence: null",
            "release_policy:",
            "  unassigned_owner: skipped_blocking",
            "  required_reviewers: 1",
            "  prohibit_self_approval: true",
        ]) + "\n",
        encoding="utf-8",
    )
    return path


def _models() -> dict:
    return {
        "embedding": {"model": "BAAI/bge-m3", "revision": "revision-20260715"},
        "reranker": {
            "model": "BAAI/bge-reranker-v2-m3",
            "revision": "reranker-revision-20260715",
        },
        "llm": {"model": "deepseek-chat", "revision": "deepseek-revision-20260715"},
    }


def _metrics() -> dict:
    return {
        "data": {
            "schema_traceability_rate": 1.0,
            "citation_id_validity_rate": 1.0,
            "empty_retrieval_text_count": 0,
            "short_eligible_chunk_count": 0,
            "exact_duplicate_rate": 0.0,
        },
        "retrieval": {"recall_at_8": 0.91, "mrr": 0.70},
        "answer": {
            "claim_citation_coverage": 0.97,
            "citation_precision": 0.98,
            "hard_negative_rejection_rate": 1.0,
            "injection_protection_rate": 1.0,
        },
        "performance": {
            "retrieval_latency_p95_ms": 420,
            "index_mode": "fast_numpy",
            "degraded": False,
        },
    }


def _write_evidence(data_dir: Path) -> Path:
    manifest_path = data_dir / "published" / "publish_index_manifest_v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    generated = datetime.fromisoformat(manifest["generated_at"].replace("Z", "+00:00"))
    started = generated + timedelta(seconds=1)
    completed = started + timedelta(seconds=30)
    manifest_hash = _sha256(manifest_path)
    evaluations = {}
    for name in (
        "integrity",
        "production_data",
        "retrieval",
        "answer",
        "models",
        "api_contract",
        "performance",
    ):
        evaluations[name] = {
            "status": "passed",
            "hard_failure_count": 0,
            "release_id": "release-a",
            "candidate_manifest_hash": manifest_hash,
            "execution_mode": "real"
            if name in {"retrieval", "answer", "models", "api_contract", "performance"}
            else "deterministic",
        }
    evaluations["answer"]["samples"] = []
    evaluations["performance"].update({"index_mode": "fast_numpy", "degraded": False})
    evidence = {
        "schema_version": "rag_release_gate_evidence_v1",
        "candidate": {
            "release_id": "release-a",
            "manifest_hash": manifest_hash,
            "manifest_generated_at": manifest["generated_at"],
            "code_commit": "0123456789abcdef0123456789abcdef01234567",
        },
        "report": {
            "started_at": started.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "completed_at": completed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
        "models": _models(),
        "prompt_version": "grounded_answer_prompt_v1",
        "evaluations": evaluations,
        "metrics": _metrics(),
    }
    path = data_dir / "published" / "rag_release_gate_evidence.json"
    path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _run_gate(tmp_path: Path, *, assigned_owner: bool = True, mutate=None, expected_models=None, prompt_version="grounded_answer_prompt_v1"):
    from bgpkb.publishing.publish_index_closure import write_publish_index_manifest
    from bgpkb.workflows.release_verification import verify_candidate_release

    data_dir = _build_candidate(tmp_path)
    write_publish_index_manifest(data_dir, release_id="release-a")
    evidence_path = _write_evidence(data_dir)
    if mutate:
        payload = json.loads(evidence_path.read_text(encoding="utf-8"))
        mutate(payload)
        evidence_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output = data_dir / "published" / "release_verification_report_v1.json"
    result = verify_candidate_release(
        data_dir=data_dir,
        expected_code_commit="0123456789abcdef0123456789abcdef01234567",
        expected_models=expected_models if expected_models is not None else _models(),
        expected_prompt_version=prompt_version,
        ownership_path=_ownership(tmp_path / "ownership.yaml", assigned=assigned_owner),
        evidence_path=evidence_path,
        output_path=output,
    )
    return result, output


def test_unified_verify_release_gate_passes_complete_fresh_real_candidate(tmp_path):
    result, output = _run_gate(tmp_path)

    assert result["status"] == "passed"
    assert result["exit_code"] == 0
    assert output.is_file()
    assert [row["gate_id"] for row in result["gates"]] == [
        "candidate_manifest",
        "evaluation_ownership",
        "artifact_integrity",
        "production_data_quality",
        "retrieval_gold",
        "structured_answer_gold",
        "real_model_configuration",
        "api_contract",
        "performance",
        "report_freshness",
        "versioned_thresholds",
    ]
    assert {row["status"] for row in result["gates"]} == {"pass"}


@pytest.mark.parametrize(
    ("case", "expected_gate", "expected_status"),
    [
        ("owner_missing", "evaluation_ownership", "skipped_blocking"),
        ("mock_answer", "structured_answer_gold", "fail"),
        ("stale_manifest", "report_freshness", "fail"),
        ("blocking_performance", "performance", "skipped_blocking"),
        ("missing_prompt", "real_model_configuration", "skipped_blocking"),
        ("missing_reranker_revision", "real_model_configuration", "skipped_blocking"),
    ],
)
def test_unified_gate_fails_closed_and_retains_report(
    tmp_path,
    case,
    expected_gate,
    expected_status,
):
    mutate = None
    assigned = True
    models = _models()
    prompt = "grounded_answer_prompt_v1"
    if case == "owner_missing":
        assigned = False
    elif case == "mock_answer":
        mutate = lambda payload: payload["evaluations"]["answer"].update(execution_mode="mock")
    elif case == "stale_manifest":
        mutate = lambda payload: payload["candidate"].update(manifest_hash="sha256:" + "f" * 64)
    elif case == "blocking_performance":
        mutate = lambda payload: payload["evaluations"]["performance"].update(status="skipped_blocking")
    elif case == "missing_prompt":
        prompt = ""
    else:
        models["reranker"]["revision"] = ""

    result, output = _run_gate(
        tmp_path,
        assigned_owner=assigned,
        mutate=mutate,
        expected_models=models,
        prompt_version=prompt,
    )

    assert result["status"] == "failed"
    assert result["exit_code"] != 0
    assert output.is_file()
    gate = next(row for row in result["gates"] if row["gate_id"] == expected_gate)
    assert gate["status"] == expected_status


def test_missing_candidate_manifest_still_writes_nonzero_diagnostic_report(tmp_path):
    from bgpkb.workflows.release_verification import verify_candidate_release

    data_dir = tmp_path / "candidate" / "data"
    output = data_dir / "published" / "release_verification_report_v1.json"
    result = verify_candidate_release(
        data_dir=data_dir,
        expected_code_commit="",
        expected_models={},
        expected_prompt_version="",
        ownership_path=_ownership(tmp_path / "ownership.yaml", assigned=False),
        output_path=output,
    )

    assert result["exit_code"] != 0
    assert output.is_file()
    candidate_gate = next(row for row in result["gates"] if row["gate_id"] == "candidate_manifest")
    assert candidate_gate["status"] == "fail"
    assert "missing" in candidate_gate["reason"]
