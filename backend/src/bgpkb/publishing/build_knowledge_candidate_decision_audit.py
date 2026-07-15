#!/usr/bin/env python3
"""复用现有人工审核语义，审计证据绑定知识候选决策。"""

from __future__ import annotations

from collections import Counter, defaultdict
import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from bgpkb import paths
from bgpkb.publishing.build_standard_mapping_decision_audit import (
    load_decision_rows,
    valid_reviewed_at,
)


CONFIG_PATH = paths.CONFIG_DIR / "knowledge_candidate_extraction_v1.yaml"
ALLOWED_DECISIONS = {"unreviewed", "approved", "rejected", "needs_evidence"}


def _audit_record(
    decision: dict[str, Any],
    candidate: dict[str, Any] | None,
    status: str,
    eligible: bool,
    reason: str,
) -> dict[str, Any]:
    record = {
        "candidate_id": decision.get("candidate_id", ""),
        "submitted_input_fingerprint": decision.get("input_fingerprint", ""),
        "decision": decision.get("decision", "unreviewed"),
        "reviewer": decision.get("reviewer", ""),
        "reviewed_at": decision.get("reviewed_at", ""),
        "decision_note": decision.get("decision_note", ""),
        "audit_status": status,
        "write_eligible": eligible,
        "reason": reason,
    }
    if candidate is not None:
        record["current_input_fingerprint"] = candidate.get("input_fingerprint", "")
    return record


def audit_knowledge_candidate_decisions(
    candidates: list[dict[str, Any]], decisions: list[dict[str, Any]]
) -> dict[str, Any]:
    """只审计人工输入，不修改候选、正式知识或 serving 数据。"""
    candidate_by_id = {
        candidate.get("candidate_id"): candidate
        for candidate in candidates
        if candidate.get("candidate_id")
    }
    decision_counts = Counter(
        decision.get("candidate_id", "") for decision in decisions
    )
    records = []
    for decision in decisions:
        candidate_id = decision.get("candidate_id", "")
        candidate = candidate_by_id.get(candidate_id)
        value = decision.get("decision", "unreviewed")
        candidate_is_pending = bool(candidate) and candidate.get("governance") == {
            "review_status": "pending_review"
        }
        if not candidate_id or decision_counts[candidate_id] > 1:
            record = _audit_record(
                decision,
                candidate,
                "blocked_invalid_input",
                False,
                "candidate_id 缺失或人工决策重复。",
            )
        elif candidate is None or not candidate_is_pending:
            record = _audit_record(
                decision,
                candidate,
                "blocked_invalid_candidate",
                False,
                "候选不存在或已越过 pending_review 边界。",
            )
        elif value not in ALLOWED_DECISIONS:
            record = _audit_record(
                decision,
                candidate,
                "blocked_invalid_input",
                False,
                "decision 不在允许范围内。",
            )
        elif value == "unreviewed":
            record = _audit_record(
                decision, candidate, "no_op", False, "尚未人工审核。"
            )
        elif value == "rejected":
            record = _audit_record(
                decision, candidate, "rejected", False, "人工已拒绝该知识候选。"
            )
        elif value == "needs_evidence":
            record = _audit_record(
                decision,
                candidate,
                "needs_evidence",
                False,
                "需要补充知识候选证据。",
            )
        elif (
            decision.get("input_fingerprint") != candidate.get("input_fingerprint")
            or not decision.get("reviewer")
            or not valid_reviewed_at(decision.get("reviewed_at", ""))
        ):
            record = _audit_record(
                decision,
                candidate,
                "blocked_invalid_input",
                False,
                "批准记录的输入指纹、审核人或带时区审核时间无效。",
            )
        else:
            record = _audit_record(
                decision,
                candidate,
                "ready_to_apply",
                True,
                "人工批准且审计通过。",
            )
        records.append(record)

    relation_groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    for index, record in enumerate(records):
        if record["audit_status"] != "ready_to_apply":
            continue
        candidate = candidate_by_id[record["candidate_id"]]
        if candidate.get("candidate_type") != "relation":
            continue
        payload = candidate.get("payload", {})
        relation_groups[(payload.get("subject_ref", ""), payload.get("predicate", ""))].append(index)
    for indexes in relation_groups.values():
        objects = {
            candidate_by_id[records[index]["candidate_id"]]
            .get("payload", {})
            .get("object_ref", "")
            for index in indexes
        }
        if len(objects) > 1:
            for index in indexes:
                records[index]["audit_status"] = "blocked_conflict"
                records[index]["write_eligible"] = False
                records[index]["reason"] = (
                    "同一 subject+predicate 存在多个互斥的批准 relation 候选。"
                )

    records.sort(
        key=lambda record: (
            record["candidate_id"],
            record["decision"],
            record["submitted_input_fingerprint"],
        )
    )
    blockers = [
        record for record in records if record["audit_status"].startswith("blocked_")
    ]
    return {
        "records": records,
        "has_blockers": bool(blockers),
        "blocker_count": len(blockers),
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )


def run_audit(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    root = Path(root)
    outputs = config["outputs"]
    result = audit_knowledge_candidate_decisions(
        _read_jsonl(root / outputs["candidates"]),
        load_decision_rows(root / outputs["decisions"]),
    )
    _write_jsonl(root / outputs["decision_audit"], result["records"])
    report = {
        "status": "blocked" if result["has_blockers"] else "passed",
        "decision_count": len(result["records"]),
        "blocker_count": result["blocker_count"],
        "message": "本报告只审计人工输入，不修改候选或正式知识。",
    }
    report_path = root / outputs["decision_audit_report"]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="审计证据绑定知识候选的人工决策")
    parser.add_argument("--root", type=Path, default=paths.PROJECT_ROOT)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args(argv)
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    result = run_audit(args.root, config)
    print(
        f"审计 {len(result['records'])} 条知识候选决策；"
        f"阻断 {result['blocker_count']} 条。"
    )
    return 1 if result["has_blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
