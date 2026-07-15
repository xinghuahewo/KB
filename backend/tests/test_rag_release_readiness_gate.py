from bgpkb.workflows import check_release_readiness


def test_release_checker_propagates_owner_and_real_eval_blocking_status():
    checks = check_release_readiness.release_quality_checks(
        ownership_status={
            "status": "skipped_blocking",
            "reason": "evaluation_owner_unassigned",
            "datasets": ["answer_gold", "retrieval_gold"],
        },
        evaluation_evidence={},
    )

    assert [item["status"] for item in checks] == [
        "skipped_blocking",
        "skipped_blocking",
        "skipped_blocking",
    ]
    assert any(item["name"] == "rag_gold_ownership" for item in checks)
    assert any(item["name"] == "real_rag_evaluation" for item in checks)
    assert "skipped_blocking" in check_release_readiness.render_report(checks)


def test_release_checker_recomputes_versioned_quality_thresholds():
    passing_metrics = {
        "data": {
            "schema_traceability_rate": 1.0,
            "citation_id_validity_rate": 1.0,
            "empty_retrieval_text_count": 0,
            "short_eligible_chunk_count": 0,
            "exact_duplicate_rate": 0.0,
        },
        "retrieval": {"recall_at_8": 0.80, "mrr": 0.65},
        "answer": {
            "claim_citation_coverage": 0.95,
            "citation_precision": 0.95,
            "hard_negative_rejection_rate": 1.0,
            "injection_protection_rate": 1.0,
        },
        "performance": {
            "retrieval_latency_p95_ms": 500,
            "index_mode": "fast_numpy",
            "degraded": False,
        },
    }
    checks = check_release_readiness.release_quality_checks(
        ownership_status={"status": "ready"},
        evaluation_evidence={"status": "passed", "metrics": passing_metrics},
    )

    quality = next(item for item in checks if item["name"] == "rag_quality_thresholds")
    assert quality["status"] == "pass"
    assert "rag_quality_gates_v1.1.0" in quality["detail"]

    passing_metrics["retrieval"]["recall_at_8"] = 0.79
    failed = check_release_readiness.release_quality_checks(
        ownership_status={"status": "ready"},
        evaluation_evidence={"status": "passed", "metrics": passing_metrics},
    )
    quality = next(item for item in failed if item["name"] == "rag_quality_thresholds")
    assert quality["status"] == "fail"
    assert "retrieval.recall_at_8_min" in quality["detail"]
