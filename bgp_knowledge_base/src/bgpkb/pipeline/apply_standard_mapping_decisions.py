#!/usr/bin/env python3
"""预览或显式写入经审计批准的标准语义映射。"""

import argparse
import json
import os
from pathlib import Path
import tempfile

import yaml

from bgpkb import paths
from bgpkb.pipeline.build_standard_mapping_decision_audit import read_jsonl


CONFIG_PATH = paths.CONFIG_DIR / "standard_exports.yaml"


def atomic_write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def select_ready_mappings(audits, candidates):
    candidate_by_id = {row.get("candidate_id"): row for row in candidates if row.get("candidate_id")}
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
            and audit.get("decision") == "approved"
            and audit.get("audit_status") == "ready_to_apply"
            and audit.get("write_eligible") is True
            and fingerprints_match
        ):
            skipped.append({
                "candidate_id": audit.get("candidate_id", ""),
                "action": "skip",
                "reason": "审核状态或当前候选指纹不满足写入条件。",
            })
            continue
        approved.append({
            "candidate_id": candidate["candidate_id"],
            "candidate_type": candidate["candidate_type"],
            "local_value": candidate["local_value"],
            "suggested_mapping": candidate["suggested_mapping"],
            "input_fingerprint": candidate["input_fingerprint"],
            "source_refs": candidate.get("source_refs", []),
            "reviewer": audit.get("reviewer", ""),
            "reviewed_at": audit.get("reviewed_at", ""),
            "decision_note": audit.get("decision_note", ""),
        })
    approved.sort(key=lambda row: (
        row["candidate_type"], row["local_value"], row["suggested_mapping"], row["candidate_id"]
    ))
    skipped.sort(key=lambda row: row["candidate_id"])
    return approved, skipped


def build_report(approved, skipped, write):
    return "\n".join([
        "# 标准映射人工决策应用报告", "",
        "本报告记录经审计映射的应用预览；该流程不修改主实体或主关系。", "",
        "## 摘要", "",
        f"- 可应用映射：{len(approved)} 条",
        f"- 跳过记录：{len(skipped)} 条",
        f"- 写入模式：{'显式写入' if write else 'dry-run'}",
        f"- 已修改批准映射集合：{'是' if write else '否'}", "",
    ])


def apply_standard_mapping_decisions(root, config, write=False):
    root = Path(root)
    outputs = config["outputs"]
    candidates = read_jsonl(root / outputs["candidates"])
    audits = read_jsonl(root / outputs["decision_audit"])
    approved, skipped = select_ready_mappings(audits, candidates)
    preview = [dict(row, action="apply") for row in approved] + skipped
    preview.sort(key=lambda row: (row.get("candidate_id", ""), row["action"]))
    atomic_write_jsonl(root / outputs["apply_preview"], preview)
    if write:
        atomic_write_jsonl(root / outputs["approved_mappings"], approved)
    report_path = root / outputs["decision_apply_report"]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_report(approved, skipped, write), encoding="utf-8")
    return {"ready_count": len(approved), "skipped_count": len(skipped), "written": write}


def main(argv=None):
    parser = argparse.ArgumentParser(description="预览或显式应用标准映射人工决策")
    parser.add_argument("--write", action="store_true", help="显式写入批准映射集合")
    args = parser.parse_args(argv)
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    result = apply_standard_mapping_decisions(paths.PROJECT_ROOT, config, write=args.write)
    print(f"可应用 {result['ready_count']} 条；写入模式：{result['written']}。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
