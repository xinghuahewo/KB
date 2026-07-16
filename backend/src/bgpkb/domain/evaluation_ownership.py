"""检索与回答黄金集的发布责任边界。"""

import json
from pathlib import Path

import yaml


REQUIRED_DATASETS = ("answer_gold", "retrieval_gold")


def load_ownership(path: Path) -> dict:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "rag_eval_ownership_v1":
        raise ValueError("评测 owner 配置版本无效")
    datasets = payload.get("datasets")
    if not isinstance(datasets, dict):
        raise ValueError("评测 owner 配置缺少 datasets")
    missing = sorted(set(REQUIRED_DATASETS) - set(datasets))
    if missing:
        raise ValueError(f"评测 owner 配置缺少数据集：{', '.join(missing)}")
    return datasets


def _approval_evidence_valid(
    dataset: str,
    record: dict,
    *,
    project_root: Path | None,
) -> bool:
    reference = record.get("approval_evidence")
    if project_root is None:
        return reference is None or bool(reference)
    if not isinstance(reference, str) or not reference:
        return False
    logical = Path(reference)
    if logical.is_absolute() or ".." in logical.parts:
        return False
    evidence_path = (Path(project_root) / logical).resolve()
    try:
        evidence_path.relative_to(Path(project_root).resolve())
        payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    return (
        payload.get("schema_version") == "rag_gold_approval_evidence_v1"
        and payload.get("owner") == record.get("owner")
        and payload.get("reviewer") in record.get("reviewers", [])
        and dataset in payload.get("datasets", [])
        and bool(payload.get("authorization_method"))
    )


def release_ownership_status(
    ownership: dict,
    *,
    project_root: Path | None = None,
) -> dict:
    blocking = []
    for dataset in REQUIRED_DATASETS:
        record = ownership.get(dataset, {})
        assigned = (
            record.get("owner_status") == "assigned"
            and bool(record.get("owner"))
            and bool(record.get("reviewers"))
            and record.get("change_control") == "pull_request"
        )
        if not assigned:
            blocking.append(dataset)
    if blocking:
        return {
            "status": "skipped_blocking",
            "reason": "evaluation_owner_unassigned",
            "datasets": blocking,
        }
    self_approved = [
        dataset
        for dataset in REQUIRED_DATASETS
        if ownership[dataset]["owner"] in ownership[dataset]["reviewers"]
    ]
    if self_approved:
        return {
            "status": "skipped_blocking",
            "reason": "evaluation_owner_self_approval",
            "datasets": self_approved,
        }
    invalid_evidence = [
        dataset
        for dataset in REQUIRED_DATASETS
        if not _approval_evidence_valid(
            dataset,
            ownership[dataset],
            project_root=project_root,
        )
    ]
    if invalid_evidence:
        return {
            "status": "skipped_blocking",
            "reason": "evaluation_approval_evidence_invalid",
            "datasets": invalid_evidence,
        }
    return {"status": "ready", "datasets": []}
