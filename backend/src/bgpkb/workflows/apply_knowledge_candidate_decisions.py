#!/usr/bin/env python3
"""预览或显式应用经人工审计的知识候选。"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
from typing import Any

import yaml

from bgpkb import paths


CONFIG_PATH = paths.CONFIG_DIR / "knowledge_candidate_extraction_v1.yaml"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def atomic_write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        for record in records
    )
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def select_ready_candidates(
    audits: list[dict[str, Any]], candidates: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidate_by_id = {
        candidate.get("candidate_id"): candidate
        for candidate in candidates
        if candidate.get("candidate_id")
    }
    approved = []
    skipped = []
    for audit in audits:
        candidate = candidate_by_id.get(audit.get("candidate_id"))
        fingerprints_match = bool(candidate) and (
            audit.get("submitted_input_fingerprint")
            == audit.get("current_input_fingerprint")
            == candidate.get("input_fingerprint")
        )
        if not (
            candidate
            and candidate.get("governance") == {"review_status": "pending_review"}
            and audit.get("decision") == "approved"
            and audit.get("audit_status") == "ready_to_apply"
            and audit.get("write_eligible") is True
            and fingerprints_match
        ):
            skipped.append(
                {
                    "candidate_id": audit.get("candidate_id", ""),
                    "action": "skip",
                    "reason": "审核状态或当前候选指纹不满足显式应用条件。",
                }
            )
            continue
        approved.append(
            {
                "schema_version": "applied_knowledge_candidate_v1",
                "candidate_id": candidate["candidate_id"],
                "candidate_type": candidate["candidate_type"],
                "payload": candidate["payload"],
                "evidence_ids": candidate["evidence_ids"],
                "source_refs": candidate["source_refs"],
                "input_fingerprint": candidate["input_fingerprint"],
                "provider": candidate["provider"],
                "model_revision": candidate["model_revision"],
                "prompt_version": candidate["prompt_version"],
                "application_status": "approved_for_next_release",
                "reviewer": audit.get("reviewer", ""),
                "reviewed_at": audit.get("reviewed_at", ""),
                "decision_note": audit.get("decision_note", ""),
            }
        )
    approved.sort(key=lambda record: record["candidate_id"])
    skipped.sort(key=lambda record: record["candidate_id"])
    return approved, skipped


def validate_serving_knowledge_inputs(records: list[dict[str, Any]]) -> None:
    """阻止 pending candidate 被误当作下一 release 的正式知识输入。"""
    invalid_ids = [
        record.get("candidate_id", "")
        for record in records
        if record.get("schema_version") != "applied_knowledge_candidate_v1"
        or record.get("application_status") != "approved_for_next_release"
        or record.get("governance", {}).get("review_status") == "pending_review"
    ]
    if invalid_ids:
        raise ValueError(
            "serving 知识输入必须经过 approved_for_next_release 显式应用："
            + ", ".join(invalid_ids)
        )


def apply_knowledge_candidate_decisions(
    root: Path, config: dict[str, Any], *, write: bool = False
) -> dict[str, Any]:
    root = Path(root)
    outputs = config["outputs"]
    candidates = _read_jsonl(root / outputs["candidates"])
    audits = _read_jsonl(root / outputs["decision_audit"])
    approved, skipped = select_ready_candidates(audits, candidates)
    validate_serving_knowledge_inputs(approved)
    preview = [dict(record, action="apply") for record in approved] + skipped
    preview.sort(key=lambda record: (record.get("candidate_id", ""), record["action"]))
    atomic_write_jsonl(root / outputs["apply_preview"], preview)
    if write:
        atomic_write_jsonl(root / outputs["approved_candidates"], approved)
    report = {
        "mode": "explicit_write" if write else "dry_run",
        "ready_count": len(approved),
        "skipped_count": len(skipped),
        "approved_collection_modified": write,
        "message": "仅应用经人工审计记录；不会直接修改 serving release。",
    }
    report_path = root / outputs["decision_apply_report"]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "ready_count": len(approved),
        "skipped_count": len(skipped),
        "written": write,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="预览或显式应用知识候选人工决策")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--root", type=Path, default=paths.PROJECT_ROOT)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args(argv)
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    result = apply_knowledge_candidate_decisions(
        args.root, config, write=args.write
    )
    print(
        f"可应用 {result['ready_count']} 条；"
        f"跳过 {result['skipped_count']} 条；写入模式：{result['written']}。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
