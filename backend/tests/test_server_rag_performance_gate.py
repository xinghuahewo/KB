from __future__ import annotations

import json
import hashlib

from bgpkb import paths


QUESTIONS_PATH = paths.METADATA_DIR / "evaluation" / "retrieval_gold_v1.jsonl"


def test_performance_gate_uses_fixed_versioned_question_set():
    from bgpkb.pipeline.run_server_rag_performance_gate import load_questions

    questions = load_questions(QUESTIONS_PATH)

    assert len(questions) == 104
    assert {item["dataset_version"] for item in questions} == {
        "retrieval_gold_v1.0.0"
    }
    assert {item["query_type"] for item in questions} == {
        "fact",
        "process",
        "policy",
        "global",
    }


def test_concurrent_gate_records_dense_retrieval_answer_and_runtime_mode():
    from bgpkb.pipeline.run_server_rag_performance_gate import run_workload

    questions = [
        {"question_id": f"q-{index}", "query": f"query-{index}", "query_type": "fact"}
        for index in range(4)
    ]

    def fake_request(question):
        index = int(question["question_id"].split("-")[-1])
        return {
            "ok": True,
            "dense_search_latency_ms": 4.0 + index,
            "retrieval_latency_ms": 80.0 + index,
            "answer_latency_ms": 7000.0 + index,
            "index_mode": "fast_numpy",
            "degraded": False,
            "answer_status": "answered",
        }

    samples = run_workload(questions, request_fn=fake_request, concurrency=2)

    assert [item["question_id"] for item in samples] == ["q-0", "q-1", "q-2", "q-3"]
    assert all(item["index_mode"] == "fast_numpy" for item in samples)
    assert all(item["degraded"] is False for item in samples)
    assert samples[0]["dense_search_latency_ms"] == 4.0
    assert samples[0]["retrieval_latency_ms"] == 80.0
    assert samples[0]["answer_latency_ms"] == 7000.0


def test_performance_gate_fails_on_p95_index_fallback_degradation_or_request_error():
    from bgpkb.pipeline.run_server_rag_performance_gate import evaluate_samples

    samples = [
        {
            "question_id": "slow",
            "ok": True,
            "dense_search_latency_ms": 10,
            "retrieval_latency_ms": 501,
            "answer_latency_ms": 7000,
            "index_mode": "fast_numpy",
            "degraded": False,
        },
        {
            "question_id": "fallback",
            "ok": True,
            "dense_search_latency_ms": 12,
            "retrieval_latency_ms": 90,
            "answer_latency_ms": 7100,
            "index_mode": "legacy_jsonl_scan",
            "degraded": True,
        },
        {
            "question_id": "error",
            "ok": False,
            "error": "timeout",
        },
    ]

    decision = evaluate_samples(samples, retrieval_p95_max_ms=500)

    assert decision["status"] == "failed"
    assert decision["exit_code"] == 1
    assert {
        "performance.request_failure",
        "performance.retrieval_latency_p95_ms",
        "performance.index_mode",
        "performance.degraded",
    } <= {item["rule_id"] for item in decision["failures"]}


def test_performance_report_is_bound_to_candidate_and_preserved_on_failure(tmp_path):
    from bgpkb.pipeline.run_server_rag_performance_gate import (
        build_report,
        evaluate_samples,
        write_report,
    )

    samples = [
        {
            "question_id": "q-1",
            "ok": True,
            "dense_search_latency_ms": 4,
            "retrieval_latency_ms": 501,
            "answer_latency_ms": 7000,
            "index_mode": "fast_numpy",
            "degraded": False,
            "answer_status": "answered",
        }
    ]
    decision = evaluate_samples(samples, retrieval_p95_max_ms=500)
    report = build_report(
        samples=samples,
        decision=decision,
        target_url="http://127.0.0.1:39281",
        candidate_release_id="candidate-2026-07-14",
        candidate_manifest_hash="sha256:" + "a" * 64,
        question_set_version="retrieval_gold_v1.0.0",
        concurrency=4,
        started_at="2026-07-14T08:00:00Z",
        completed_at="2026-07-14T08:01:00Z",
    )
    output = tmp_path / "performance.json"

    write_report(output, report)
    written = json.loads(output.read_text(encoding="utf-8"))

    assert written["schema_version"] == "rag_server_performance_report_v1"
    assert written["candidate"]["release_id"] == "candidate-2026-07-14"
    assert written["candidate"]["manifest_hash"].startswith("sha256:")
    assert written["workload"] == {
        "question_set_version": "retrieval_gold_v1.0.0",
        "question_count": 1,
        "concurrency": 4,
    }
    assert written["metrics"]["retrieval_latency_p95_ms"] == 501
    assert written["metrics"]["dense_search_latency_p95_ms"] == 4
    assert written["metrics"]["answer_latency_p95_ms"] == 7000
    assert written["status"] == "failed"


def test_performance_cli_derives_candidate_identity_from_publish_manifest(tmp_path):
    from bgpkb.pipeline.run_server_rag_performance_gate import resolve_candidate_identity

    data_dir = tmp_path / "candidate-a" / "data"
    manifest = data_dir / "published" / "publish_index_manifest_v1.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"release_id": "candidate-a"}) + "\n", encoding="utf-8")

    release_id, manifest_hash = resolve_candidate_identity(
        data_dir,
        candidate_release_id="",
        candidate_manifest_hash="",
    )

    assert release_id == "candidate-a"
    assert manifest_hash == "sha256:" + hashlib.sha256(manifest.read_bytes()).hexdigest()
