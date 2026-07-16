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


def test_existing_performance_report_can_be_reused_without_running_workload(
    tmp_path, monkeypatch
):
    from bgpkb.pipeline import run_server_rag_performance_gate as gate

    data_dir = tmp_path / "candidate-a" / "data"
    published = data_dir / "published"
    published.mkdir(parents=True)
    manifest = published / "publish_index_manifest_v1.json"
    manifest.write_text(json.dumps({"release_id": "candidate-a"}) + "\n", encoding="utf-8")
    manifest_hash = "sha256:" + hashlib.sha256(manifest.read_bytes()).hexdigest()
    questions = tmp_path / "questions.jsonl"
    questions.write_text(
        json.dumps(
            {
                "question_id": "q-1",
                "query": "什么是 BGP？",
                "query_type": "fact",
                "dataset_version": "retrieval_gold_test_v1",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    report = gate.build_report(
        samples=[
            {
                "question_id": "q-1",
                "query_type": "fact",
                "ok": True,
                "dense_search_latency_ms": 4,
                "retrieval_latency_ms": 80,
                "answer_latency_ms": 7000,
                "index_mode": "fast_numpy",
                "degraded": False,
                "answer_status": "answered",
            }
        ],
        decision=gate.evaluate_samples([], retrieval_p95_max_ms=500)
        | {
            "status": "passed",
            "exit_code": 0,
            "hard_failure_count": 0,
            "failures": [],
            "metrics": gate.summarize_samples(
                [
                    {
                        "question_id": "q-1",
                        "ok": True,
                        "dense_search_latency_ms": 4,
                        "retrieval_latency_ms": 80,
                        "answer_latency_ms": 7000,
                        "index_mode": "fast_numpy",
                        "degraded": False,
                    }
                ]
            ),
        },
        target_url="http://127.0.0.1:39282",
        candidate_release_id="candidate-a",
        candidate_manifest_hash=manifest_hash,
        question_set_version="retrieval_gold_test_v1",
        concurrency=4,
        started_at="2026-07-15T08:00:00Z",
        completed_at="2026-07-15T08:01:00Z",
    )
    output = published / "rag_server_performance_report_v1.json"
    gate.write_report(output, report)

    monkeypatch.setattr(
        gate,
        "run_workload",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("复用已有报告时不得运行网络工作负载")
        ),
    )

    exit_code = gate.main(
        [
            "--target-url",
            "http://127.0.0.1:39282",
            "--data-dir",
            str(data_dir),
            "--questions",
            str(questions),
            "--output",
            str(output),
            "--reuse-existing-report",
        ]
    )

    assert exit_code == 0


def test_existing_performance_report_reuse_fails_closed_on_sample_mismatch(tmp_path):
    from bgpkb.pipeline.run_server_rag_performance_gate import (
        validate_existing_report,
    )

    report = {
        "schema_version": "rag_server_performance_report_v1",
        "candidate": {
            "release_id": "candidate-a",
            "manifest_hash": "sha256:" + "a" * 64,
        },
        "workload": {
            "question_set_version": "retrieval_gold_test_v1",
            "question_count": 1,
            "concurrency": 4,
        },
        "status": "passed",
        "hard_failure_count": 0,
        "failures": [],
        "metrics": {},
        "samples": [],
    }

    decision = validate_existing_report(
        report,
        candidate_release_id="candidate-a",
        candidate_manifest_hash="sha256:" + "a" * 64,
        questions=[
            {
                "question_id": "q-1",
                "dataset_version": "retrieval_gold_test_v1",
            }
        ],
        concurrency=4,
        retrieval_p95_max_ms=500,
    )

    assert decision["status"] == "failed"
    assert "performance.report_sample_closure" in {
        item["rule_id"] for item in decision["failures"]
    }
