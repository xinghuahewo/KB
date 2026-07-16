"""RAG 发布门禁的确定性失败契约。

本模块只判断评测证据是否允许进入发布；真实检索、回答和性能评测仍由各自
评测器产生报告，后续由 verify-release 编排器接入本契约。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from bgpkb import paths


REQUIRED_MODEL_BINDINGS = ("embedding", "reranker", "llm")
DEFAULT_POLICY_PATH = paths.CONFIG_DIR / "rag_quality_gates_v1.yaml"


@dataclass(frozen=True)
class ReleaseGateDecision:
    status: str
    exit_code: int
    failure_codes: tuple[str, ...]


def load_quality_gate_policy(path: str | Path = DEFAULT_POLICY_PATH) -> dict:
    import yaml

    policy = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(policy, dict) or policy.get("schema_version") != "rag_quality_gates_v1":
        raise ValueError("RAG 质量门禁配置必须使用 rag_quality_gates_v1")
    if not policy.get("policy_version"):
        raise ValueError("RAG 质量门禁配置缺少 policy_version")
    return policy


def _metric(metrics: Mapping[str, Any], section: str, name: str) -> object:
    payload = metrics.get(section, {})
    return payload.get(name) if isinstance(payload, Mapping) else None


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def evaluate_quality_metrics(
    metrics: Mapping[str, Any],
    *,
    policy: Mapping[str, Any] | None = None,
    policy_path: str | Path = DEFAULT_POLICY_PATH,
) -> dict:
    """按版本化阈值确定性评估发布指标；缺失指标按硬失败处理。"""

    active_policy = dict(policy) if policy is not None else load_quality_gate_policy(policy_path)
    thresholds = active_policy["thresholds"]
    failures: list[dict[str, Any]] = []

    def numeric_rule(section: str, metric: str, rule_id: str, operator: str, expected: float) -> None:
        actual = _metric(metrics, section, metric)
        if not _is_number(actual):
            failures.append({
                "rule_id": rule_id,
                "reason": "missing_metric" if actual is None else "invalid_metric",
                "expected": {operator: expected},
                "actual": actual,
            })
            return
        passed = actual >= expected if operator == "min" else actual <= expected
        if not passed:
            failures.append({
                "rule_id": rule_id,
                "reason": "threshold_violation",
                "expected": {operator: expected},
                "actual": actual,
            })

    data = thresholds["data"]
    numeric_rule("data", "schema_traceability_rate", "data.schema_traceability_rate", "min", data["schema_traceability_rate_min"])
    numeric_rule("data", "citation_id_validity_rate", "data.citation_id_validity_rate", "min", data["citation_id_validity_rate_min"])
    numeric_rule("data", "empty_retrieval_text_count", "data.empty_retrieval_text_count", "max", data["empty_retrieval_text_count_max"])
    numeric_rule("data", "short_eligible_chunk_count", "data.short_eligible_chunk_count", "max", data["short_eligible_chunk_count_max"])
    numeric_rule("data", "exact_duplicate_rate", "data.exact_duplicate_rate", "max", data["exact_duplicate_rate_max"])

    retrieval = thresholds["retrieval"]
    numeric_rule("retrieval", "recall_at_8", "retrieval.recall_at_8_min", "min", retrieval["recall_at_8_min"])
    numeric_rule("retrieval", "mrr", "retrieval.mrr", "min", retrieval["mrr_min"])
    recall = _metric(metrics, "retrieval", "recall_at_8")
    baseline_recall = active_policy["frozen_baseline"]["retrieval"]["recall_at_8"]
    minimum_from_baseline = baseline_recall - retrieval["recall_at_8_max_regression"]
    if _is_number(recall) and recall < minimum_from_baseline:
        failures.append({
            "rule_id": "retrieval.recall_at_8_regression",
            "reason": "baseline_regression",
            "expected": {
                "min": minimum_from_baseline,
                "baseline": baseline_recall,
                "max_regression": retrieval["recall_at_8_max_regression"],
            },
            "actual": recall,
        })

    answer = thresholds["answer"]
    numeric_rule("answer", "claim_citation_coverage", "answer.claim_citation_coverage", "min", answer["claim_citation_coverage_min"])
    numeric_rule("answer", "citation_precision", "answer.citation_precision", "min", answer["citation_precision_min"])
    numeric_rule("answer", "hard_negative_rejection_rate", "answer.hard_negative_rejection_rate", "min", answer["hard_negative_rejection_rate_min"])
    numeric_rule("answer", "injection_protection_rate", "answer.injection_protection_rate", "min", answer["injection_protection_rate_min"])

    performance = thresholds["performance"]
    numeric_rule("performance", "retrieval_latency_p95_ms", "performance.retrieval_latency_p95_ms", "max", performance["retrieval_latency_p95_ms_max"])
    for metric, expected, rule_id in (
        ("index_mode", performance["required_index_mode"], "performance.index_mode"),
        ("degraded", performance["degraded_required"], "performance.degraded"),
    ):
        actual = _metric(metrics, "performance", metric)
        if actual != expected:
            failures.append({
                "rule_id": rule_id,
                "reason": "missing_metric" if actual is None else "required_value_mismatch",
                "expected": expected,
                "actual": actual,
            })

    return {
        "schema_version": "rag_quality_gate_decision_v1",
        "policy_version": active_policy["policy_version"],
        "status": "failed" if failures else "passed",
        "hard_failure_count": len(failures),
        "failures": failures,
    }


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo is not None else None
    except ValueError:
        return None


def build_evaluation_envelope(
    *,
    release_id: str,
    manifest_hash: str,
    manifest_generated_at: str,
    code_commit: str,
    models: Mapping[str, Mapping[str, str]],
    prompt_version: str,
    started_at: str,
    completed_at: str,
    evaluations: Mapping[str, Any],
) -> dict:
    missing = sorted(set(REQUIRED_MODEL_BINDINGS) - set(models))
    if missing:
        raise ValueError(f"评测 evidence 缺少模型绑定：{', '.join(missing)}")
    for component in REQUIRED_MODEL_BINDINGS:
        binding = models[component]
        if not binding.get("model") or not binding.get("revision"):
            raise ValueError(f"评测 evidence 的 {component} 必须固定 model 和 revision")
    if _parse_time(manifest_generated_at) is None:
        raise ValueError("候选 manifest_generated_at 必须是带时区时间")
    started = _parse_time(started_at)
    completed = _parse_time(completed_at)
    if started is None or completed is None or completed < started:
        raise ValueError("评测开始/结束时间必须带时区且顺序有效")
    return {
        "schema_version": "rag_release_gate_evidence_v1",
        "candidate": {
            "release_id": release_id,
            "manifest_hash": manifest_hash,
            "manifest_generated_at": manifest_generated_at,
            "code_commit": code_commit,
        },
        "report": {"started_at": started_at, "completed_at": completed_at},
        "models": {
            component: {
                "model": str(models[component]["model"]),
                "revision": str(models[component]["revision"]),
            }
            for component in REQUIRED_MODEL_BINDINGS
        },
        "prompt_version": prompt_version,
        "evaluations": dict(evaluations),
    }


def evaluate_release_gate(
    report: Mapping[str, Any],
    *,
    expected_release_id: str,
    expected_manifest_hash: str,
    expected_code_commit: str,
    expected_models: Mapping[str, Mapping[str, str]],
    expected_prompt_version: str,
) -> ReleaseGateDecision:
    """把硬失败和阻断性跳过统一转换为非零发布决定。"""

    failures: list[str] = []
    candidate = report.get("candidate", {})
    report_meta = report.get("report", {})
    evaluations = report.get("evaluations", {})

    if candidate.get("release_id") != expected_release_id:
        failures.append("stale_report:release_id_mismatch")
    if candidate.get("manifest_hash") != expected_manifest_hash:
        failures.append("stale_report:manifest_hash_mismatch")
    if candidate.get("code_commit") != expected_code_commit:
        failures.append("stale_report:code_commit_mismatch")

    models = report.get("models", {})
    for component in REQUIRED_MODEL_BINDINGS:
        if models.get(component) != expected_models.get(component):
            failures.append(f"stale_report:model_binding_mismatch:{component}")
    if report.get("prompt_version") != expected_prompt_version:
        failures.append("stale_report:prompt_version_mismatch")

    manifest_time = _parse_time(candidate.get("manifest_generated_at"))
    report_start = _parse_time(report_meta.get("started_at"))
    report_completed = _parse_time(report_meta.get("completed_at"))
    if manifest_time is None or report_start is None or report_start < manifest_time:
        failures.append("stale_report:report_predates_manifest")
    if report_start is None or report_completed is None or report_completed < report_start:
        failures.append("stale_report:invalid_time_range")

    for name in sorted(evaluations):
        evaluation = evaluations[name]
        status = evaluation.get("status")
        if status == "skipped_blocking":
            failures.append(f"blocking_skip:{name}")
        elif status == "failed" or int(evaluation.get("hard_failure_count", 0)) > 0:
            failures.append(f"evaluation_hard_failure:{name}")

    performance = evaluations.get("performance", {})
    if performance.get("index_mode") != "fast_numpy":
        failures.append("jsonl_scan_degradation:index_mode")
    if performance.get("degraded") is not False:
        failures.append("jsonl_scan_degradation:degraded")

    unique_failures = tuple(dict.fromkeys(failures))
    return ReleaseGateDecision(
        status="failed" if unique_failures else "passed",
        exit_code=1 if unique_failures else 0,
        failure_codes=unique_failures,
    )
