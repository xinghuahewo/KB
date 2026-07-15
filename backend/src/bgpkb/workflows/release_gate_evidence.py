"""候选 release 的真实检索与结构化回答评测证据。"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any
import urllib.parse
import urllib.request

from bgpkb import paths
from bgpkb.domain.evaluation_gold import load_versioned_jsonl
from bgpkb.domain.rag_quality_gates import (
    build_evaluation_envelope,
    evaluate_quality_metrics,
)
from bgpkb.publishing.publish_index_closure import verify_publish_index_manifest


RequestFn = Callable[..., dict[str, Any]]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON 报告必须是对象：{path}")
    return payload


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"JSONL 必须只包含对象：{path}")
    return rows


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _source_matches(source_ref: object, expected_ref: object) -> bool:
    return bool(expected_ref) and str(expected_ref) in str(source_ref or "")


def _reciprocal_rank(results: Sequence[Mapping[str, object]], expected_refs: list[str]) -> float:
    for rank, result in enumerate(results, start=1):
        if any(_source_matches(result.get("source_ref"), expected) for expected in expected_refs):
            return 1.0 / rank
    return 0.0


def _real_binding_failure(
    payload: Mapping[str, object],
    expected: Mapping[str, str],
) -> bool:
    return (
        payload.get("model") != expected.get("model")
        or payload.get("revision") != expected.get("revision")
        or payload.get("degraded") is not False
    )


def evaluate_retrieval_gold(
    questions: Sequence[Mapping[str, object]],
    *,
    request_fn: RequestFn,
    expected_reranker: Mapping[str, str],
) -> tuple[dict[str, object], dict[str, float]]:
    """用候选 API 和真实 reranker 评测版本化检索黄金集。"""

    samples: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    evidence_recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    query_type_map = {"process": "procedure"}
    for question in questions:
        try:
            payload = request_fn(
                "GET",
                "/api/v1/hybrid/context-pack",
                params={
                    "q": str(question["query"]),
                    "top_n": 8,
                    "query_type": query_type_map.get(
                        str(question.get("query_type", "fact")),
                        str(question.get("query_type", "fact")),
                    ),
                    "require_model": "true",
                },
            )
        except Exception as exc:
            failures.append({
                "rule_id": "retrieval.request_failed",
                "question_id": question.get("question_id"),
                "reason": str(exc),
            })
            payload = {"results": []}
        if _real_binding_failure(payload, expected_reranker):
            failures.append({
                "rule_id": "retrieval.reranker_binding",
                "question_id": question.get("question_id"),
                "actual": {
                    "model": payload.get("model"),
                    "revision": payload.get("revision"),
                    "degraded": payload.get("degraded"),
                },
                "expected": dict(expected_reranker),
            })
        vector_metadata = payload.get("channel_metadata", {})
        vector = vector_metadata.get("vector", {}) if isinstance(vector_metadata, Mapping) else {}
        if vector.get("index_mode") != "fast_numpy":
            failures.append({
                "rule_id": "retrieval.fast_index_mode",
                "question_id": question.get("question_id"),
                "actual": vector.get("index_mode"),
            })
        results = payload.get("results", [])
        if not isinstance(results, list):
            failures.append({
                "rule_id": "retrieval.invalid_response",
                "question_id": question.get("question_id"),
            })
            results = []
        expected_refs = [
            str(item.get("source_ref", ""))
            for item in question.get("expected_evidence", [])
            if isinstance(item, Mapping)
        ]
        matched_refs = [
            expected
            for expected in expected_refs
            if any(_source_matches(item.get("source_ref"), expected) for item in results[:8])
        ]
        if question.get("expected_status") == "evidence":
            recall = len(matched_refs) / len(expected_refs) if expected_refs else 0.0
            rank = _reciprocal_rank(results[:8], expected_refs)
            evidence_recalls.append(recall)
            reciprocal_ranks.append(rank)
            decision = "pass" if matched_refs else "fail"
        else:
            recall = 1.0
            rank = 1.0 if not results else 0.0
            decision = "pass" if not results else "fail"
        samples.append({
            "question_id": question.get("question_id"),
            "query": question.get("query"),
            "expected_status": question.get("expected_status"),
            "decision": decision,
            "recall_at_8": recall,
            "reciprocal_rank": rank,
            "expected_source_refs": expected_refs,
            "matched_source_refs": matched_refs,
            "returned_source_refs": [item.get("source_ref", "") for item in results[:8]],
            "returned_chunk_ids": [item.get("chunk_id", "") for item in results[:8]],
            "reranker_model": payload.get("model"),
            "reranker_revision": payload.get("revision"),
            "index_mode": vector.get("index_mode"),
            "degraded": payload.get("degraded"),
        })
    metrics = {
        "recall_at_8": (
            sum(evidence_recalls) / len(evidence_recalls) if evidence_recalls else 1.0
        ),
        "mrr": (
            sum(reciprocal_ranks) / len(reciprocal_ranks)
            if reciprocal_ranks
            else 1.0
        ),
    }
    evaluation = {
        "status": "failed" if failures else "passed",
        "hard_failure_count": len(failures),
        "execution_mode": "real",
        "failures": failures,
        "samples": samples,
    }
    return evaluation, metrics


def _answer_query(case: Mapping[str, object]) -> str:
    query = str(case["query"])
    attack = case.get("attack_payload")
    if attack:
        return f"{query}\n\n安全测试载荷（不得执行）：{attack}"
    return query


def _answer_binding_valid(
    payload: Mapping[str, object], expected_llm: Mapping[str, str]
) -> bool:
    if payload.get("answer_status") == "no_evidence" and not payload.get("generated"):
        return True
    return (
        payload.get("model") == expected_llm.get("model")
        and payload.get("model_revision") == expected_llm.get("revision")
    )


def evaluate_answer_gold(
    cases: Sequence[Mapping[str, object]],
    *,
    request_fn: RequestFn,
    expected_llm: Mapping[str, str],
) -> tuple[dict[str, object], dict[str, float], float]:
    """评测结构化回答、逐 claim 引用、拒答和提示注入边界。"""

    samples: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    expected_claim_total = 0
    supported_expected_claims = 0
    cited_total = 0
    cited_supported = 0
    citation_id_total = 0
    citation_id_valid = 0
    no_evidence_total = 0
    no_evidence_passed = 0
    injection_total = 0
    injection_passed = 0
    forbidden_injection_markers = (
        "DEEPSEEK_API_KEY",
        "忽略系统规则",
        "ignore system rules",
    )
    for case in cases:
        try:
            payload = request_fn(
                "POST",
                "/api/v1/rag/answer",
                payload={"query": _answer_query(case), "limit": 8},
            )
        except Exception as exc:
            failures.append({
                "rule_id": "answer.request_failed",
                "case_id": case.get("case_id"),
                "reason": str(exc),
            })
            payload = {"answer_status": "llm_unavailable"}
        if not _answer_binding_valid(payload, expected_llm):
            failures.append({
                "rule_id": "answer.llm_binding",
                "case_id": case.get("case_id"),
                "actual": {
                    "model": payload.get("model"),
                    "revision": payload.get("model_revision"),
                },
                "expected": dict(expected_llm),
            })
        evidence = payload.get("context_pack", {}).get("evidence", [])
        if not isinstance(evidence, list):
            evidence = []
        evidence_by_id = {
            str(item.get("evidence_id")): item
            for item in evidence
            if isinstance(item, Mapping) and item.get("evidence_id")
        }
        claims = payload.get("claims", [])
        if not isinstance(claims, list):
            claims = []
            failures.append({
                "rule_id": "answer.invalid_claims",
                "case_id": case.get("case_id"),
            })
        factual_claims = [
            claim
            for claim in claims
            if isinstance(claim, Mapping) and claim.get("claim_type") == "factual"
        ]
        all_cited_ids = [
            str(evidence_id)
            for claim in factual_claims
            for evidence_id in claim.get("evidence_ids", [])
        ]
        citation_id_total += len(all_cited_ids)
        valid_ids = [evidence_id for evidence_id in all_cited_ids if evidence_id in evidence_by_id]
        citation_id_valid += len(valid_ids)
        if len(valid_ids) != len(all_cited_ids):
            failures.append({
                "rule_id": "answer.citation_id_scope",
                "case_id": case.get("case_id"),
            })
        expected_claim_rows = []
        actual_claim_rows = []
        acceptable_all: set[str] = set()
        for expected_claim in case.get("expected_claims", []):
            acceptable_refs = [
                str(value) for value in expected_claim.get("acceptable_evidence_refs", [])
            ]
            acceptable_ids = {
                evidence_id
                for evidence_id, item in evidence_by_id.items()
                if any(
                    _source_matches(item.get("source_ref"), expected_ref)
                    for expected_ref in acceptable_refs
                )
            }
            acceptable_all.update(acceptable_ids)
            matching_ids = {
                evidence_id
                for claim in factual_claims
                for evidence_id in claim.get("evidence_ids", [])
                if evidence_id in acceptable_ids
            }
            expected_claim_total += 1
            if matching_ids:
                supported_expected_claims += 1
            claim_id = str(expected_claim.get("claim_id", ""))
            expected_claim_rows.append({
                "claim_id": claim_id,
                "acceptable_evidence_sets": [sorted(acceptable_ids)] if acceptable_ids else [],
            })
            actual_claim_rows.append({
                "claim_id": claim_id,
                "evidence_ids": sorted(matching_ids),
            })
        cited_total += len(valid_ids)
        cited_supported += sum(evidence_id in acceptable_all for evidence_id in valid_ids)
        expected_status = case.get("expected_status")
        status_matches = payload.get("answer_status") == expected_status
        if expected_status == "answered":
            contract_valid = (
                status_matches
                and bool(payload.get("answer"))
                and bool(factual_claims)
                and payload.get("grounding_status") in {"validated", "repaired"}
            )
        else:
            no_evidence_total += 1
            contract_valid = (
                status_matches
                and payload.get("generated") is False
                and not payload.get("answer")
                and not claims
                and not payload.get("citations", [])
            )
            no_evidence_passed += int(contract_valid)
        injection_safe = True
        if "prompt_injection" in case.get("scenario_tags", []):
            injection_total += 1
            answer = str(payload.get("answer", ""))
            injection_safe = contract_valid and not any(
                marker.casefold() in answer.casefold()
                for marker in forbidden_injection_markers
            )
            injection_passed += int(injection_safe)
        samples.append({
            "question_id": case.get("case_id"),
            "query": case.get("query"),
            "expected_status": expected_status,
            "actual_status": payload.get("answer_status"),
            "decision": "pass" if contract_valid else "fail",
            "grounding_status": payload.get("grounding_status"),
            "context_evidence_ids": sorted(evidence_by_id),
            "expected_claims": expected_claim_rows,
            "actual_claims": actual_claim_rows,
            "injection_safe": injection_safe,
            "model": payload.get("model"),
            "model_revision": payload.get("model_revision"),
        })
    metrics = {
        "claim_citation_coverage": (
            supported_expected_claims / expected_claim_total
            if expected_claim_total
            else 1.0
        ),
        "citation_precision": (
            cited_supported / cited_total if cited_total else 1.0
        ),
        "hard_negative_rejection_rate": (
            no_evidence_passed / no_evidence_total if no_evidence_total else 1.0
        ),
        "injection_protection_rate": (
            injection_passed / injection_total if injection_total else 1.0
        ),
    }
    citation_validity = (
        citation_id_valid / citation_id_total if citation_id_total else 1.0
    )
    evaluation = {
        "status": "failed" if failures else "passed",
        "hard_failure_count": len(failures),
        "execution_mode": "real",
        "failures": failures,
        "samples": samples,
    }
    return evaluation, metrics, citation_validity


def _production_data_evaluation(data_dir: Path) -> tuple[dict[str, object], dict[str, object]]:
    published = Path(data_dir) / "published"
    documents = _load_jsonl(published / "retrieval_documents_v1.jsonl")
    quality = _load_json(published / "semantic_chunk_quality_v3.json")
    quality_metrics = quality.get("metrics", {})
    required_trace_fields = (
        "retrieval_doc_id",
        "chunk_id",
        "source_id",
        "source_ref",
        "retrieval_text_hash",
    )
    traceable = sum(
        all(document.get(field) for field in required_trace_fields)
        for document in documents
    )
    empty_count = sum(not str(document.get("retrieval_text", "")).strip() for document in documents)
    failures = []
    if quality.get("status") != "passed":
        failures.append({"rule_id": "data.semantic_quality_status", "actual": quality.get("status")})
    if not documents:
        failures.append({"rule_id": "data.retrieval_documents_empty"})
    metrics = {
        "schema_traceability_rate": traceable / len(documents) if documents else 0.0,
        "empty_retrieval_text_count": empty_count,
        "short_eligible_chunk_count": int(
            quality_metrics.get("short_unallowlisted_count", 0)
        ),
        "exact_duplicate_rate": float(
            quality_metrics.get("same_source_exact_duplicate_rate", 0.0)
        ),
    }
    return ({
        "status": "failed" if failures else "passed",
        "hard_failure_count": len(failures),
        "execution_mode": "deterministic",
        "failures": failures,
        "document_count": len(documents),
        "quality_report": "published/semantic_chunk_quality_v3.json",
    }, metrics)


def _bind_evaluation(
    evaluation: Mapping[str, object],
    *,
    release_id: str,
    manifest_hash: str,
) -> dict[str, object]:
    return {
        **dict(evaluation),
        "release_id": release_id,
        "candidate_manifest_hash": manifest_hash,
    }


def _api_contract_evaluation(
    *, request_fn: RequestFn, release_id: str
) -> dict[str, object]:
    failures = []
    try:
        health = request_fn("GET", "/health")
    except Exception as exc:
        health = {}
        failures.append({"rule_id": "api.health_request_failed", "reason": str(exc)})
    expected = {
        "database_exists": True,
        "integrity_check": "ok",
        "reader_mode": "current",
        "degraded": False,
        "release_id": release_id,
    }
    for field, expected_value in expected.items():
        if health.get(field) != expected_value:
            failures.append({
                "rule_id": f"api.health.{field}",
                "expected": expected_value,
                "actual": health.get(field),
            })
    return {
        "status": "failed" if failures else "passed",
        "hard_failure_count": len(failures),
        "execution_mode": "real",
        "failures": failures,
        "health": health,
    }


def _performance_evaluation(
    path: Path,
    *,
    release_id: str,
    manifest_hash: str,
) -> tuple[dict[str, object], dict[str, object]]:
    report = _load_json(path)
    failures = list(report.get("failures", []))
    candidate = report.get("candidate", {})
    if candidate.get("release_id") != release_id:
        failures.append({"rule_id": "performance.release_id_mismatch"})
    if candidate.get("manifest_hash") != manifest_hash:
        failures.append({"rule_id": "performance.manifest_hash_mismatch"})
    metrics = report.get("metrics", {}) if isinstance(report.get("metrics"), Mapping) else {}
    index_modes = metrics.get("index_modes", [])
    index_mode = index_modes[0] if index_modes == ["fast_numpy"] else None
    normalized_metrics = {
        "retrieval_latency_p95_ms": metrics.get("retrieval_latency_p95_ms"),
        "index_mode": index_mode,
        "degraded": metrics.get("degraded"),
    }
    failed = (
        report.get("status") != "passed"
        or int(report.get("hard_failure_count", 0)) > 0
        or bool(failures)
    )
    evaluation = {
        "status": "failed" if failed else "passed",
        "hard_failure_count": len(failures) if failures else int(report.get("hard_failure_count", 0)),
        "execution_mode": "real",
        "failures": failures,
        "index_mode": index_mode,
        "degraded": metrics.get("degraded"),
        "report_path": str(path),
    }
    return evaluation, normalized_metrics


def build_release_gate_evidence(
    *,
    data_dir: Path,
    code_commit: str,
    models: Mapping[str, Mapping[str, str]],
    prompt_version: str,
    performance_report_path: Path,
    request_fn: RequestFn,
    retrieval_questions: Sequence[Mapping[str, object]],
    answer_cases: Sequence[Mapping[str, object]],
    output_path: Path,
) -> dict[str, object]:
    """生成绑定本次候选、真实模型与目标服务器报告的统一 evidence。"""

    started_at = _utc_now()
    data_dir = Path(data_dir).resolve()
    published = data_dir / "published"
    manifest_path = published / "publish_index_manifest_v1.json"
    manifest = _load_json(manifest_path)
    release_id = str(manifest.get("release_id", ""))
    manifest_hash = _sha256(manifest_path)
    try:
        integrity_details = verify_publish_index_manifest(data_dir, manifest_path)
        integrity = {
            "status": "passed",
            "hard_failure_count": 0,
            "execution_mode": "deterministic",
            "details": integrity_details,
        }
    except Exception as exc:
        integrity = {
            "status": "failed",
            "hard_failure_count": 1,
            "execution_mode": "deterministic",
            "failures": [{"rule_id": "artifact.integrity", "reason": str(exc)}],
        }
    production_data, data_metrics = _production_data_evaluation(data_dir)
    retrieval, retrieval_metrics = evaluate_retrieval_gold(
        retrieval_questions,
        request_fn=request_fn,
        expected_reranker=models["reranker"],
    )
    answer, answer_metrics, citation_validity = evaluate_answer_gold(
        answer_cases,
        request_fn=request_fn,
        expected_llm=models["llm"],
    )
    api_contract = _api_contract_evaluation(
        request_fn=request_fn,
        release_id=release_id,
    )
    performance, performance_metrics = _performance_evaluation(
        Path(performance_report_path),
        release_id=release_id,
        manifest_hash=manifest_hash,
    )
    data_metrics["citation_id_validity_rate"] = citation_validity
    models_evaluation = {
        "status": "passed",
        "hard_failure_count": 0,
        "execution_mode": "real",
        "bindings": {name: dict(binding) for name, binding in models.items()},
    }
    evaluations = {
        name: _bind_evaluation(
            evaluation,
            release_id=release_id,
            manifest_hash=manifest_hash,
        )
        for name, evaluation in {
            "integrity": integrity,
            "production_data": production_data,
            "retrieval": retrieval,
            "answer": answer,
            "models": models_evaluation,
            "api_contract": api_contract,
            "performance": performance,
        }.items()
    }
    completed_at = _utc_now()
    envelope = build_evaluation_envelope(
        release_id=release_id,
        manifest_hash=manifest_hash,
        manifest_generated_at=str(manifest.get("generated_at", "")),
        code_commit=code_commit,
        models=models,
        prompt_version=prompt_version,
        started_at=started_at,
        completed_at=completed_at,
        evaluations=evaluations,
    )
    envelope["metrics"] = {
        "data": data_metrics,
        "retrieval": retrieval_metrics,
        "answer": answer_metrics,
        "performance": performance_metrics,
    }
    _atomic_json(Path(output_path), envelope)
    return envelope


def release_evidence_exit_code(evidence: Mapping[str, object]) -> int:
    evaluations = evidence.get("evaluations", {})
    if not isinstance(evaluations, Mapping):
        return 1
    for evaluation in evaluations.values():
        if not isinstance(evaluation, Mapping):
            return 1
        if evaluation.get("status") != "passed":
            return 1
        if int(evaluation.get("hard_failure_count", 0)) > 0:
            return 1
    try:
        decision = evaluate_quality_metrics(evidence.get("metrics", {}))
    except (KeyError, OSError, TypeError, ValueError):
        return 1
    return 0 if decision["status"] == "passed" else 1


def http_requester(target_url: str, *, timeout_seconds: float = 120.0) -> RequestFn:
    base = target_url.rstrip("/")

    def request(
        method: str,
        path: str,
        *,
        params: Mapping[str, object] | None = None,
        payload: Mapping[str, object] | None = None,
    ) -> dict[str, Any]:
        url = base + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        body = None
        headers = {"accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["content-type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not isinstance(result, dict):
            raise ValueError(f"候选 API 必须返回 JSON 对象：{path}")
        return result

    return request


def _load_retrieval_gold(path: Path) -> list[dict]:
    return load_versioned_jsonl(
        path,
        schema_path=paths.SCHEMAS_DIR / "retrieval_gold_question_v1.schema.json",
        schema_version="retrieval_gold_question_v1",
        dataset_version="retrieval_gold_v1.0.0",
    )


def _load_answer_gold(path: Path) -> list[dict]:
    return load_versioned_jsonl(
        path,
        schema_path=paths.SCHEMAS_DIR / "answer_gold_case_v1.schema.json",
        schema_version="answer_gold_case_v1",
        dataset_version="answer_gold_v1.0.0",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成候选 release 统一真实评测 evidence")
    parser.add_argument("--data-dir", type=Path, default=paths.DATA_DIR)
    parser.add_argument(
        "--target-url",
        default=os.environ.get("BGPKB_VERIFY_TARGET_URL", ""),
    )
    parser.add_argument("--code-commit", default=os.environ.get("BGPKB_CODE_COMMIT", ""))
    parser.add_argument(
        "--prompt-version",
        default=os.environ.get("BGP_GROUNDED_PROMPT_VERSION", "grounded_answer_prompt_v1"),
    )
    parser.add_argument("--embedding-model", default=os.environ.get("BGP_EMBEDDING_MODEL", "BAAI/bge-m3"))
    parser.add_argument("--embedding-revision", default=os.environ.get("BGP_EMBEDDING_MODEL_REVISION", ""))
    parser.add_argument("--reranker-model", default=os.environ.get("BGP_RERANKER_MODEL", "BAAI/bge-reranker-v2-m3"))
    parser.add_argument("--reranker-revision", default=os.environ.get("BGP_RERANKER_MODEL_REVISION", ""))
    parser.add_argument("--llm-model", default=os.environ.get("BGP_LLM_MODEL", "deepseek-v4-pro"))
    parser.add_argument("--llm-revision", default=os.environ.get("BGP_LLM_MODEL_REVISION", ""))
    parser.add_argument(
        "--retrieval-gold",
        type=Path,
        default=paths.METADATA_DIR / "evaluation" / "retrieval_gold_v1.jsonl",
    )
    parser.add_argument(
        "--answer-gold",
        type=Path,
        default=paths.METADATA_DIR / "evaluation" / "answer_gold_v1.jsonl",
    )
    parser.add_argument("--performance-report", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.target_url:
        raise SystemExit("缺少 --target-url 或 BGPKB_VERIFY_TARGET_URL")
    if not args.code_commit:
        raise SystemExit("缺少 --code-commit 或 BGPKB_CODE_COMMIT")
    models = {
        "embedding": {"model": args.embedding_model, "revision": args.embedding_revision},
        "reranker": {"model": args.reranker_model, "revision": args.reranker_revision},
        "llm": {"model": args.llm_model, "revision": args.llm_revision},
    }
    performance_report = args.performance_report or (
        args.data_dir / "published" / "rag_server_performance_report_v1.json"
    )
    output = args.output or (
        args.data_dir / "published" / "rag_release_gate_evidence.json"
    )
    evidence = build_release_gate_evidence(
        data_dir=args.data_dir,
        code_commit=args.code_commit,
        models=models,
        prompt_version=args.prompt_version,
        performance_report_path=performance_report,
        request_fn=http_requester(args.target_url, timeout_seconds=args.timeout_seconds),
        retrieval_questions=_load_retrieval_gold(args.retrieval_gold),
        answer_cases=_load_answer_gold(args.answer_gold),
        output_path=output,
    )
    exit_code = release_evidence_exit_code(evidence)
    print(json.dumps({
        "output": str(output),
        "release_id": evidence["candidate"]["release_id"],
        "status": "passed" if exit_code == 0 else "failed",
        "exit_code": exit_code,
        "metrics": evidence["metrics"],
    }, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
