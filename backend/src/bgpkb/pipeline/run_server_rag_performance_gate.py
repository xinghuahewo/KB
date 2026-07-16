"""在目标服务器运行固定 RAG 并发性能门禁。"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import time
import urllib.request

from bgpkb import paths
from bgpkb.domain.rag_quality_gates import load_quality_gate_policy


DEFAULT_QUESTIONS_PATH = paths.METADATA_DIR / "evaluation" / "retrieval_gold_v1.jsonl"


def resolve_candidate_identity(
    data_dir: str | Path,
    *,
    candidate_release_id: str,
    candidate_manifest_hash: str,
) -> tuple[str, str]:
    manifest_path = Path(data_dir) / "published" / "publish_index_manifest_v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    derived_release_id = str(manifest.get("release_id", ""))
    derived_manifest_hash = "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    if candidate_release_id and candidate_release_id != derived_release_id:
        raise ValueError("性能门禁 candidate release id 与 publish manifest 不一致")
    if candidate_manifest_hash and candidate_manifest_hash != derived_manifest_hash:
        raise ValueError("性能门禁 candidate manifest hash 与实际文件不一致")
    if not derived_release_id:
        raise ValueError("publish manifest 缺少 release_id")
    return derived_release_id, derived_manifest_hash


def load_questions(path: str | Path = DEFAULT_QUESTIONS_PATH) -> list[dict]:
    rows = [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError("性能门禁问题集不能为空")
    versions = {row.get("dataset_version") for row in rows}
    if len(versions) != 1 or None in versions:
        raise ValueError("性能门禁问题集必须固定唯一 dataset_version")
    return rows


def _sse_events(body: str) -> list[dict]:
    events = []
    for line in body.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


def request_answer_stream(
    question: dict,
    *,
    target_url: str,
    timeout_seconds: float = 60,
) -> dict:
    endpoint = target_url.rstrip("/") + "/api/v1/rag/answer/stream"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps({"query": question["query"], "limit": 8}).encode("utf-8"),
        headers={"content-type": "application/json", "accept": "text/event-stream"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8")
    answer_latency_ms = round((time.perf_counter() - started) * 1000, 3)
    events = _sse_events(body)
    done = next((event for event in reversed(events) if event.get("type") == "done"), None)
    if done is None:
        error = next((event for event in reversed(events) if event.get("type") == "error"), {})
        raise RuntimeError(error.get("error") or "SSE 未返回 done 事件")
    payload = done.get("payload", {})
    context_pack = payload.get("context_pack", {})
    vector = context_pack.get("channel_metadata", {}).get("vector", {})
    retrieval_event = next(
        (
            event
            for event in events
            if event.get("type") == "stage"
            and event.get("stage") == "retrieval"
            and event.get("status") == "complete"
        ),
        {},
    )
    return {
        "ok": True,
        "dense_search_latency_ms": vector.get("latency_ms", retrieval_event.get("vector_latency_ms")),
        "retrieval_latency_ms": context_pack.get(
            "retrieval_latency_ms", retrieval_event.get("retrieval_latency_ms")
        ),
        "answer_latency_ms": answer_latency_ms,
        "index_mode": vector.get("index_mode", retrieval_event.get("vector_index_mode")),
        "degraded": bool(context_pack.get("degraded", retrieval_event.get("degraded", False))),
        "answer_status": payload.get("answer_status", ""),
    }


def run_workload(questions: list[dict], *, request_fn, concurrency: int) -> list[dict]:
    if concurrency < 1:
        raise ValueError("concurrency 必须大于等于 1")

    def execute(question: dict) -> dict:
        try:
            result = dict(request_fn(question))
        except Exception as exc:  # 网络边界必须转成可审计失败样本。
            result = {"ok": False, "error": str(exc)}
        return {
            "question_id": question["question_id"],
            "query_type": question.get("query_type", ""),
            **result,
        }

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        return list(executor.map(execute, questions))


def percentile(values: list[float], percentile_value: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    index = max(0, math.ceil(percentile_value * len(ordered)) - 1)
    return round(ordered[index], 3)


def _latencies(samples: list[dict], key: str) -> list[float]:
    return [
        float(sample[key])
        for sample in samples
        if sample.get("ok") is True
        and isinstance(sample.get(key), (int, float))
        and not isinstance(sample.get(key), bool)
    ]


def summarize_samples(samples: list[dict]) -> dict:
    metrics = {}
    for prefix, key in (
        ("dense_search_latency", "dense_search_latency_ms"),
        ("retrieval_latency", "retrieval_latency_ms"),
        ("answer_latency", "answer_latency_ms"),
    ):
        values = _latencies(samples, key)
        metrics[f"{prefix}_p50_ms"] = percentile(values, 0.50)
        metrics[f"{prefix}_p95_ms"] = percentile(values, 0.95)
    metrics["index_modes"] = sorted(
        {str(sample.get("index_mode")) for sample in samples if sample.get("index_mode")}
    )
    metrics["degraded"] = any(sample.get("degraded") is not False for sample in samples)
    metrics["request_failure_count"] = sum(sample.get("ok") is not True for sample in samples)
    return metrics


def evaluate_samples(samples: list[dict], *, retrieval_p95_max_ms: float) -> dict:
    metrics = summarize_samples(samples)
    failures = []
    if metrics["request_failure_count"]:
        failures.append({
            "rule_id": "performance.request_failure",
            "actual": metrics["request_failure_count"],
            "expected": 0,
        })
    p95 = metrics["retrieval_latency_p95_ms"]
    if p95 is None or p95 > retrieval_p95_max_ms:
        failures.append({
            "rule_id": "performance.retrieval_latency_p95_ms",
            "actual": p95,
            "expected": {"max": retrieval_p95_max_ms},
        })
    if metrics["index_modes"] != ["fast_numpy"]:
        failures.append({
            "rule_id": "performance.index_mode",
            "actual": metrics["index_modes"],
            "expected": "fast_numpy",
        })
    if metrics["degraded"] is not False:
        failures.append({
            "rule_id": "performance.degraded",
            "actual": metrics["degraded"],
            "expected": False,
        })
    return {
        "status": "failed" if failures else "passed",
        "exit_code": 1 if failures else 0,
        "hard_failure_count": len(failures),
        "failures": failures,
        "metrics": metrics,
    }


def validate_existing_report(
    report: dict,
    *,
    candidate_release_id: str,
    candidate_manifest_hash: str,
    questions: list[dict],
    concurrency: int,
    retrieval_p95_max_ms: float,
) -> dict:
    """复核同一候选的既有性能报告，不重新发送在线请求。"""

    failures: list[dict] = []
    expected_question_ids = [str(question["question_id"]) for question in questions]
    samples = report.get("samples")
    actual_question_ids = (
        [str(sample.get("question_id", "")) for sample in samples]
        if isinstance(samples, list)
        else []
    )
    expected_workload = {
        "question_set_version": questions[0]["dataset_version"],
        "question_count": len(questions),
        "concurrency": concurrency,
    }
    checks = (
        (
            "performance.report_schema",
            report.get("schema_version"),
            "rag_server_performance_report_v1",
        ),
        (
            "performance.report_candidate_release",
            report.get("candidate", {}).get("release_id"),
            candidate_release_id,
        ),
        (
            "performance.report_candidate_manifest",
            report.get("candidate", {}).get("manifest_hash"),
            candidate_manifest_hash,
        ),
        ("performance.report_workload", report.get("workload"), expected_workload),
        (
            "performance.report_sample_closure",
            sorted(actual_question_ids),
            sorted(expected_question_ids),
        ),
    )
    for rule_id, actual, expected in checks:
        if actual != expected:
            failures.append({"rule_id": rule_id, "actual": actual, "expected": expected})

    recomputed = evaluate_samples(
        samples if isinstance(samples, list) else [],
        retrieval_p95_max_ms=retrieval_p95_max_ms,
    )
    recorded_decision = {
        "status": report.get("status"),
        "hard_failure_count": report.get("hard_failure_count"),
        "failures": report.get("failures"),
        "metrics": report.get("metrics"),
    }
    expected_decision = {
        key: recomputed[key]
        for key in ("status", "hard_failure_count", "failures", "metrics")
    }
    if recorded_decision != expected_decision:
        failures.append({
            "rule_id": "performance.report_decision_integrity",
            "actual": recorded_decision,
            "expected": expected_decision,
        })
    failures.extend(recomputed["failures"])
    return {
        "status": "failed" if failures else "passed",
        "exit_code": 1 if failures else 0,
        "hard_failure_count": len(failures),
        "failures": failures,
        "metrics": recomputed["metrics"],
        "reused_existing_report": True,
    }


def build_report(
    *,
    samples: list[dict],
    decision: dict,
    target_url: str,
    candidate_release_id: str,
    candidate_manifest_hash: str,
    question_set_version: str,
    concurrency: int,
    started_at: str,
    completed_at: str,
) -> dict:
    return {
        "schema_version": "rag_server_performance_report_v1",
        "candidate": {
            "release_id": candidate_release_id,
            "manifest_hash": candidate_manifest_hash,
        },
        "target_url": target_url,
        "started_at": started_at,
        "completed_at": completed_at,
        "workload": {
            "question_set_version": question_set_version,
            "question_count": len(samples),
            "concurrency": concurrency,
        },
        "status": decision["status"],
        "hard_failure_count": decision["hard_failure_count"],
        "failures": decision["failures"],
        "metrics": decision["metrics"],
        "samples": samples,
    }


def write_report(path: str | Path, report: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=destination.parent, delete=False
    ) as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, destination)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    policy = load_quality_gate_policy()
    workload = policy["performance_workload"]
    parser = argparse.ArgumentParser(description="运行目标服务器 RAG 固定并发性能门禁。")
    parser.add_argument("--target-url", default=os.environ.get("BGPKB_VERIFY_TARGET_URL", ""))
    parser.add_argument("--data-dir", type=Path, default=paths.DATA_DIR)
    parser.add_argument("--candidate-release-id", default=os.environ.get("BGPKB_RELEASE_ID", ""))
    parser.add_argument("--candidate-manifest-hash", default="")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS_PATH)
    parser.add_argument("--concurrency", type=int, default=workload["concurrency"])
    parser.add_argument("--timeout-seconds", type=float, default=60)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--reuse-existing-report",
        action="store_true",
        help="仅复核同一候选的既有完整性能报告，不重新运行工作负载。",
    )
    args = parser.parse_args(argv)

    if not args.target_url and not args.reuse_existing_report:
        parser.error("缺少 --target-url 或 BGPKB_VERIFY_TARGET_URL")
    candidate_release_id, candidate_manifest_hash = resolve_candidate_identity(
        args.data_dir,
        candidate_release_id=args.candidate_release_id,
        candidate_manifest_hash=args.candidate_manifest_hash,
    )
    output = args.output or (
        args.data_dir / "published" / "rag_server_performance_report_v1.json"
    )

    questions = load_questions(args.questions)
    if args.reuse_existing_report:
        if not output.is_file():
            decision = {
                "status": "failed",
                "exit_code": 1,
                "hard_failure_count": 1,
                "failures": [{
                    "rule_id": "performance.report_missing",
                    "actual": str(output),
                    "expected": "existing report",
                }],
                "metrics": {},
                "reused_existing_report": True,
            }
        else:
            decision = validate_existing_report(
                json.loads(output.read_text(encoding="utf-8")),
                candidate_release_id=candidate_release_id,
                candidate_manifest_hash=candidate_manifest_hash,
                questions=questions,
                concurrency=args.concurrency,
                retrieval_p95_max_ms=policy["thresholds"]["performance"][
                    "retrieval_latency_p95_ms_max"
                ],
            )
        print(json.dumps({"output": str(output), **decision}, ensure_ascii=False, sort_keys=True))
        return decision["exit_code"]

    started_at = _utc_now()
    samples = run_workload(
        questions,
        request_fn=lambda question: request_answer_stream(
            question, target_url=args.target_url, timeout_seconds=args.timeout_seconds
        ),
        concurrency=args.concurrency,
    )
    completed_at = _utc_now()
    decision = evaluate_samples(
        samples,
        retrieval_p95_max_ms=policy["thresholds"]["performance"][
            "retrieval_latency_p95_ms_max"
        ],
    )
    report = build_report(
        samples=samples,
        decision=decision,
        target_url=args.target_url,
        candidate_release_id=candidate_release_id,
        candidate_manifest_hash=candidate_manifest_hash,
        question_set_version=questions[0]["dataset_version"],
        concurrency=args.concurrency,
        started_at=started_at,
        completed_at=completed_at,
    )
    write_report(output, report)
    print(json.dumps({"output": str(output), **decision}, ensure_ascii=False, sort_keys=True))
    return decision["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
