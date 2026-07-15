"""候选 release 的统一、失败关闭验证矩阵。"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Mapping
import uuid

from bgpkb import paths
from bgpkb.domain.evaluation_ownership import load_ownership, release_ownership_status
from bgpkb.domain.rag_quality_gates import (
    REQUIRED_MODEL_BINDINGS,
    evaluate_quality_metrics,
    evaluate_release_gate,
)
from bgpkb.publishing.publish_index_closure import (
    PUBLISH_INDEX_MANIFEST_FILENAME,
    PublishIndexClosureError,
    verify_publish_index_manifest,
)


DEFAULT_OWNERSHIP_PATH = paths.CONFIG_DIR / "rag_eval_ownership.yaml"
DEFAULT_EVIDENCE_FILENAME = "rag_release_gate_evidence.json"
DEFAULT_REPORT_FILENAME = "release_verification_report_v1.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _gate(gate_id: str, status: str, reason: str, evidence: list[str]) -> dict:
    return {
        "gate_id": gate_id,
        "status": status,
        "reason": reason,
        "evidence": evidence,
    }


def _model_configuration_errors(
    expected_models: Mapping[str, Mapping[str, str]],
    expected_prompt_version: str,
) -> list[str]:
    errors = []
    if not expected_prompt_version:
        errors.append("missing_prompt_version")
    for component in REQUIRED_MODEL_BINDINGS:
        binding = expected_models.get(component, {})
        if not binding.get("model"):
            errors.append(f"missing_model:{component}")
        if not binding.get("revision"):
            errors.append(f"missing_model_revision:{component}")
    return errors


def _evaluation_gate(
    *,
    gate_id: str,
    evaluation_name: str,
    evaluations: Mapping[str, object],
    release_id: str,
    manifest_hash: str,
    require_real: bool,
) -> dict:
    payload = evaluations.get(evaluation_name)
    if not isinstance(payload, Mapping):
        return _gate(gate_id, "skipped_blocking", "missing_evaluation_report", [])
    status = payload.get("status")
    evidence = [f"evaluations.{evaluation_name}"]
    if status == "skipped_blocking":
        return _gate(gate_id, "skipped_blocking", str(payload.get("reason", status)), evidence)
    if status != "passed" or int(payload.get("hard_failure_count", 0)) > 0:
        return _gate(gate_id, "fail", "evaluation_hard_failure", evidence)
    if payload.get("release_id") != release_id:
        return _gate(gate_id, "fail", "evaluation_release_id_mismatch", evidence)
    if payload.get("candidate_manifest_hash") != manifest_hash:
        return _gate(gate_id, "fail", "evaluation_candidate_manifest_mismatch", evidence)
    if require_real and payload.get("execution_mode") != "real":
        return _gate(gate_id, "fail", "real_evaluation_required", evidence)
    return _gate(gate_id, "pass", "verified", evidence)


def _atomic_report(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    try:
        candidate.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with candidate.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(candidate, path)
    finally:
        candidate.unlink(missing_ok=True)


def verify_candidate_release(
    *,
    data_dir: Path,
    expected_code_commit: str,
    expected_models: Mapping[str, Mapping[str, str]],
    expected_prompt_version: str,
    ownership_path: Path = DEFAULT_OWNERSHIP_PATH,
    evidence_path: Path | None = None,
    output_path: Path | None = None,
) -> dict:
    """验证候选并始终保留统一报告；仅全部 pass 时返回零。"""

    data_dir = Path(data_dir).resolve()
    published_dir = data_dir / "published"
    manifest_path = published_dir / PUBLISH_INDEX_MANIFEST_FILENAME
    evidence_path = Path(evidence_path or published_dir / DEFAULT_EVIDENCE_FILENAME)
    output_path = Path(output_path or published_dir / DEFAULT_REPORT_FILENAME)
    gates = []

    manifest = _load_json(manifest_path)
    release_id = str(manifest.get("release_id", ""))
    manifest_hash = _sha256(manifest_path) if manifest_path.is_file() else ""
    try:
        closure = verify_publish_index_manifest(data_dir, manifest_path)
        gates.append(_gate(
            "candidate_manifest",
            "pass",
            "verified",
            [str(manifest_path)],
        ))
    except (PublishIndexClosureError, OSError) as exc:
        closure = {}
        reason = "missing_candidate_manifest" if not manifest_path.is_file() else str(exc)
        gates.append(_gate("candidate_manifest", "fail", reason, [str(manifest_path)]))

    try:
        resolved_ownership_path = Path(ownership_path).resolve()
        project_root = (
            paths.PROJECT_ROOT
            if resolved_ownership_path.is_relative_to(paths.PROJECT_ROOT.resolve())
            else resolved_ownership_path.parent
        )
        ownership = release_ownership_status(
            load_ownership(resolved_ownership_path),
            project_root=project_root,
        )
    except (OSError, ValueError) as exc:
        ownership = {"status": "skipped_blocking", "reason": str(exc)}
    owner_ready = ownership.get("status") == "ready"
    gates.append(_gate(
        "evaluation_ownership",
        "pass" if owner_ready else "skipped_blocking",
        "verified" if owner_ready else str(ownership.get("reason", "evaluation_owner_unassigned")),
        [str(ownership_path)],
    ))

    evidence = _load_json(evidence_path)
    evaluations = evidence.get("evaluations", {})
    if not isinstance(evaluations, Mapping):
        evaluations = {}
    evaluation_specs = (
        ("artifact_integrity", "integrity", False),
        ("production_data_quality", "production_data", False),
        ("retrieval_gold", "retrieval", True),
        ("structured_answer_gold", "answer", True),
    )
    for gate_id, evaluation_name, require_real in evaluation_specs:
        gates.append(_evaluation_gate(
            gate_id=gate_id,
            evaluation_name=evaluation_name,
            evaluations=evaluations,
            release_id=release_id,
            manifest_hash=manifest_hash,
            require_real=require_real,
        ))

    model_errors = _model_configuration_errors(
        expected_models, expected_prompt_version
    )
    if not expected_code_commit:
        model_errors.append("missing_code_commit")
    model_gate = _evaluation_gate(
        gate_id="real_model_configuration",
        evaluation_name="models",
        evaluations=evaluations,
        release_id=release_id,
        manifest_hash=manifest_hash,
        require_real=True,
    )
    embedded_revision = (
        manifest.get("model_revisions", {}).get("embedding")
        if isinstance(manifest.get("model_revisions"), Mapping)
        else None
    )
    if model_errors:
        model_gate = _gate(
            "real_model_configuration",
            "skipped_blocking",
            ",".join(model_errors),
            ["expected_model_bindings", str(evidence_path)],
        )
    elif evidence.get("models") != expected_models:
        model_gate = _gate(
            "real_model_configuration",
            "fail",
            "evaluation_model_bindings_mismatch",
            [str(evidence_path)],
        )
    elif embedded_revision != expected_models["embedding"]["revision"]:
        model_gate = _gate(
            "real_model_configuration",
            "fail",
            "publish_embedding_revision_mismatch",
            [str(manifest_path), str(evidence_path)],
        )
    gates.append(model_gate)

    gates.append(_evaluation_gate(
        gate_id="api_contract",
        evaluation_name="api_contract",
        evaluations=evaluations,
        release_id=release_id,
        manifest_hash=manifest_hash,
        require_real=True,
    ))

    gates.append(_evaluation_gate(
        gate_id="performance",
        evaluation_name="performance",
        evaluations=evaluations,
        release_id=release_id,
        manifest_hash=manifest_hash,
        require_real=True,
    ))

    if evidence and not model_errors and manifest_hash:
        freshness = evaluate_release_gate(
            evidence,
            expected_release_id=release_id,
            expected_manifest_hash=manifest_hash,
            expected_code_commit=expected_code_commit,
            expected_models=expected_models,
            expected_prompt_version=expected_prompt_version,
        )
        freshness_status = "pass" if freshness.exit_code == 0 else "fail"
        freshness_reason = (
            "verified" if not freshness.failure_codes else ",".join(freshness.failure_codes)
        )
    else:
        freshness_status = "fail"
        freshness_reason = "missing_or_incomplete_freshness_binding"
    gates.append(_gate(
        "report_freshness",
        freshness_status,
        freshness_reason,
        [str(manifest_path), str(evidence_path)],
    ))

    try:
        threshold_decision = evaluate_quality_metrics(evidence.get("metrics", {}))
        threshold_status = "pass" if threshold_decision["status"] == "passed" else "fail"
        threshold_reason = (
            f"policy={threshold_decision['policy_version']};"
            f"failures={[item['rule_id'] for item in threshold_decision['failures']]}"
        )
    except (OSError, ValueError, KeyError) as exc:
        threshold_status = "fail"
        threshold_reason = str(exc)
    gates.append(_gate(
        "versioned_thresholds",
        threshold_status,
        threshold_reason,
        [str(paths.CONFIG_DIR / "rag_quality_gates_v1.yaml"), str(evidence_path)],
    ))

    passed = all(row["status"] == "pass" for row in gates)
    report = {
        "schema_version": "release_verification_report_v1",
        "status": "passed" if passed else "failed",
        "exit_code": 0 if passed else 1,
        "generated_at": _utc_now(),
        "candidate": {
            "release_id": release_id or None,
            "publish_index_manifest": str(manifest_path),
            "publish_index_manifest_hash": manifest_hash or None,
            "closure": closure,
        },
        "policy_version": threshold_decision.get("policy_version") if 'threshold_decision' in locals() else None,
        "gates": gates,
        "failure_count": sum(row["status"] != "pass" for row in gates),
    }
    _atomic_report(output_path, report)
    return report
