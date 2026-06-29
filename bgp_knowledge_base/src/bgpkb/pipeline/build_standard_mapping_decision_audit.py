#!/usr/bin/env python3
"""审计阶段五标准语义映射的人工决策，不修改任何主数据。"""

import csv
from collections import Counter, defaultdict
from datetime import datetime
import json
from pathlib import Path

import yaml

from bgpkb import paths


ALLOWED_DECISIONS = {"unreviewed", "approved", "rejected", "needs_evidence"}
CONFIG_PATH = paths.CONFIG_DIR / "standard_exports.yaml"


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def load_decision_rows(path):
    if not path.exists():
        return []
    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row_number, row in enumerate(csv.DictReader(handle), start=2):
            if not any((value or "").strip() for value in row.values()):
                continue
            rows.append({
                "candidate_id": (row.get("candidate_id") or "").strip(),
                "input_fingerprint": (row.get("input_fingerprint") or "").strip(),
                "decision": (row.get("decision") or "unreviewed").strip(),
                "reviewer": (row.get("reviewer") or "").strip(),
                "reviewed_at": (row.get("reviewed_at") or "").strip(),
                "decision_note": (row.get("decision_note") or "").strip(),
                "row_number": row_number,
            })
    return rows


def valid_reviewed_at(value):
    if not value or "T" not in value:
        return False
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _audit_record(row, candidate, status, eligible, reason):
    record = {
        "candidate_id": row.get("candidate_id", ""),
        "submitted_input_fingerprint": row.get("input_fingerprint", ""),
        "decision": row.get("decision", "unreviewed"),
        "reviewer": row.get("reviewer", ""),
        "reviewed_at": row.get("reviewed_at", ""),
        "decision_note": row.get("decision_note", ""),
        "audit_status": status,
        "write_eligible": eligible,
        "reason": reason,
    }
    if candidate:
        record["current_input_fingerprint"] = candidate.get("input_fingerprint", "")
    return record


def audit_mapping_decisions(candidates, decisions):
    candidate_by_id = {row.get("candidate_id"): row for row in candidates if row.get("candidate_id")}
    counts = Counter(row.get("candidate_id", "") for row in decisions)
    records = []
    errors = []

    for row in decisions:
        candidate_id = row.get("candidate_id", "")
        candidate = candidate_by_id.get(candidate_id)
        decision = row.get("decision", "unreviewed")
        if not candidate_id or counts[candidate_id] > 1:
            record = _audit_record(row, candidate, "blocked_invalid_input", False, "candidate_id 缺失或人工决策重复。")
        elif candidate is None:
            record = _audit_record(row, None, "blocked_invalid_candidate", False, "人工决策引用的候选不存在。")
        elif decision not in ALLOWED_DECISIONS:
            record = _audit_record(row, candidate, "blocked_invalid_input", False, "decision 不在允许范围内。")
        elif decision == "unreviewed":
            record = _audit_record(row, candidate, "no_op", False, "尚未人工审核。")
        elif decision == "rejected":
            record = _audit_record(row, candidate, "rejected", False, "人工已拒绝该映射候选。")
        elif decision == "needs_evidence":
            record = _audit_record(row, candidate, "needs_evidence", False, "需要补充映射证据。")
        elif (
            row.get("input_fingerprint") != candidate.get("input_fingerprint")
            or not row.get("reviewer")
            or not valid_reviewed_at(row.get("reviewed_at", ""))
        ):
            record = _audit_record(row, candidate, "blocked_invalid_input", False, "批准记录的指纹、审核人或审核时间无效。")
        else:
            record = _audit_record(row, candidate, "ready_to_apply", True, "人工批准且审计通过。")
        records.append(record)

    ready_groups = defaultdict(list)
    for index, record in enumerate(records):
        if record["audit_status"] != "ready_to_apply":
            continue
        candidate = candidate_by_id[record["candidate_id"]]
        ready_groups[(candidate.get("candidate_type"), candidate.get("local_value"))].append(index)
    for indexes in ready_groups.values():
        mappings = {candidate_by_id[records[index]["candidate_id"]].get("suggested_mapping") for index in indexes}
        if len(mappings) > 1:
            for index in indexes:
                records[index]["audit_status"] = "blocked_conflict"
                records[index]["write_eligible"] = False
                records[index]["reason"] = "同一本地项存在多个冲突的批准映射。"

    records.sort(key=lambda row: (row["candidate_id"], row["decision"], row.get("submitted_input_fingerprint", "")))
    blockers = [row for row in records if row["audit_status"].startswith("blocked_")]
    errors.extend(row["reason"] for row in blockers)
    return {"records": records, "errors": errors, "has_blockers": bool(blockers)}


def build_report(result):
    counts = Counter(row["audit_status"] for row in result["records"])
    lines = [
        "# 标准映射人工决策审计报告", "",
        "本报告只审计人工输入，不修改实体、关系、候选或正式标准出口。", "",
        "## 摘要", "",
        f"- 人工决策记录：{len(result['records'])} 条",
        f"- 可显式应用：{counts['ready_to_apply']} 条",
        f"- 阻塞记录：{sum(count for status, count in counts.items() if status.startswith('blocked_'))} 条",
        f"- 总体状态：{'阻塞' if result['has_blockers'] else '通过'}", "",
        "## 状态统计", "",
    ]
    for status, count in sorted(counts.items()):
        lines.append(f"- `{status}`：{count} 条")
    return "\n".join(lines).rstrip() + "\n"


def run_audit(root, config):
    root = Path(root)
    outputs = config["outputs"]
    candidates = read_jsonl(root / outputs["candidates"])
    decisions = load_decision_rows(root / outputs["decisions"])
    result = audit_mapping_decisions(candidates, decisions)
    write_jsonl(root / outputs["decision_audit"], result["records"])
    report_path = root / outputs["decision_audit_report"]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_report(result), encoding="utf-8")
    return result


def main():
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    result = run_audit(paths.PROJECT_ROOT, config)
    print(f"审计 {len(result['records'])} 条标准映射人工决策。")
    return 1 if result["has_blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
