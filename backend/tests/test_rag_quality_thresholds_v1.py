from __future__ import annotations

import copy

import pytest
import yaml

from bgpkb import paths


POLICY_PATH = paths.CONFIG_DIR / "rag_quality_gates_v1.yaml"


def passing_metrics() -> dict:
    return {
        "data": {
            "schema_traceability_rate": 1.0,
            "citation_id_validity_rate": 1.0,
            "empty_retrieval_text_count": 0,
            "short_eligible_chunk_count": 0,
            "exact_duplicate_rate": 0.02,
        },
        "retrieval": {"recall_at_8": 0.80, "mrr": 0.65},
        "answer": {
            "claim_citation_coverage": 0.95,
            "citation_precision": 0.95,
            "hard_negative_rejection_rate": 1.0,
            "injection_protection_rate": 1.0,
        },
        "performance": {
            "retrieval_latency_p95_ms": 500.0,
            "index_mode": "fast_numpy",
            "degraded": False,
        },
    }


def test_versioned_quality_policy_freezes_all_initial_release_thresholds():
    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))

    assert policy["schema_version"] == "rag_quality_gates_v1"
    assert policy["policy_version"] == "rag_quality_gates_v1.1.0"
    assert policy["frozen_baseline"]["retrieval"]["recall_at_8"] == pytest.approx(
        0.882353
    )
    assert policy["thresholds"] == {
        "data": {
            "schema_traceability_rate_min": 1.0,
            "citation_id_validity_rate_min": 1.0,
            "empty_retrieval_text_count_max": 0,
            "short_eligible_chunk_count_max": 0,
            "exact_duplicate_rate_max": 0.02,
        },
        "retrieval": {
            "recall_at_8_min": 0.80,
            "recall_at_8_max_regression": 0.10,
            "mrr_min": 0.65,
        },
        "answer": {
            "claim_citation_coverage_min": 0.95,
            "citation_precision_min": 0.95,
            "hard_negative_rejection_rate_min": 1.0,
            "injection_protection_rate_min": 1.0,
        },
        "performance": {
            "retrieval_latency_p95_ms_max": 500,
            "required_index_mode": "fast_numpy",
            "degraded_required": False,
        },
    }
    assert policy["change_control"]["threshold_loosening_requires"] == [
        "adr",
        "human_approval",
    ]
    assert policy["change_control"]["decision_ref"] == "docs/adr/0006-rag-recall-threshold.md"


@pytest.mark.parametrize(
    ("section", "metric", "value", "expected_rule"),
    [
        ("data", "schema_traceability_rate", 0.999, "data.schema_traceability_rate"),
        ("data", "citation_id_validity_rate", 0.999, "data.citation_id_validity_rate"),
        ("data", "empty_retrieval_text_count", 1, "data.empty_retrieval_text_count"),
        ("data", "short_eligible_chunk_count", 1, "data.short_eligible_chunk_count"),
        ("data", "exact_duplicate_rate", 0.021, "data.exact_duplicate_rate"),
        ("retrieval", "recall_at_8", 0.799, "retrieval.recall_at_8_min"),
        ("retrieval", "mrr", 0.649, "retrieval.mrr"),
        ("answer", "claim_citation_coverage", 0.949, "answer.claim_citation_coverage"),
        ("answer", "citation_precision", 0.949, "answer.citation_precision"),
        ("answer", "hard_negative_rejection_rate", 0.999, "answer.hard_negative_rejection_rate"),
        ("answer", "injection_protection_rate", 0.999, "answer.injection_protection_rate"),
        ("performance", "retrieval_latency_p95_ms", 500.1, "performance.retrieval_latency_p95_ms"),
        ("performance", "index_mode", "legacy_jsonl_scan", "performance.index_mode"),
        ("performance", "degraded", True, "performance.degraded"),
    ],
)
def test_each_hard_threshold_fails_closed(section, metric, value, expected_rule):
    from bgpkb.domain.rag_quality_gates import evaluate_quality_metrics

    metrics = passing_metrics()
    metrics[section][metric] = value

    decision = evaluate_quality_metrics(metrics, policy_path=POLICY_PATH)

    assert decision["status"] == "failed"
    assert decision["hard_failure_count"] >= 1
    assert expected_rule in {failure["rule_id"] for failure in decision["failures"]}


def test_recall_regression_is_checked_separately_from_absolute_threshold():
    from bgpkb.domain.rag_quality_gates import evaluate_quality_metrics

    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    policy = copy.deepcopy(policy)
    policy["frozen_baseline"]["retrieval"]["recall_at_8"] = 0.95
    metrics = passing_metrics()
    metrics["retrieval"]["recall_at_8"] = 0.84

    decision = evaluate_quality_metrics(metrics, policy=policy)

    assert "retrieval.recall_at_8_regression" in {
        failure["rule_id"] for failure in decision["failures"]
    }


def test_missing_metrics_are_hard_failures_and_passing_boundary_is_accepted():
    from bgpkb.domain.rag_quality_gates import evaluate_quality_metrics

    missing = evaluate_quality_metrics({}, policy_path=POLICY_PATH)
    passing = evaluate_quality_metrics(passing_metrics(), policy_path=POLICY_PATH)

    assert missing["status"] == "failed"
    assert any(item["reason"] == "missing_metric" for item in missing["failures"])
    assert passing == {
        "schema_version": "rag_quality_gate_decision_v1",
        "policy_version": "rag_quality_gates_v1.1.0",
        "status": "passed",
        "hard_failure_count": 0,
        "failures": [],
    }
