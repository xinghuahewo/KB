"""在候选临时目录重放现有来源与实体审核状态。"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable

from bgpkb.domain.evidence_governance import (
    derive_retrieval_eligibility,
    load_eligibility_policy,
    migrate_legacy_governance,
)


MIGRATION_RECORDS_NAME = "evidence_governance_migration_v1.jsonl"
DIFF_REPORT_NAME = "evidence_governance_migration_diff_v1.json"
HUMAN_REPORT_NAME = "evidence_governance_migration_report_v1.md"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _semantic_review_by_chunk(
    records: Iterable[dict[str, Any]],
) -> tuple[dict[str, dict[str, str]], dict[str, list[str]]]:
    statuses: dict[str, list[str]] = defaultdict(list)
    entities: dict[str, list[str]] = defaultdict(list)
    for record in records:
        status = str(record.get("entity_review_status") or record.get("review_status") or "")
        entity_id = str(record.get("entity_id") or record.get("id") or "")
        for chunk_id in record.get("chunk_sample_ids", []):
            if status:
                statuses[str(chunk_id)].append(status)
            if entity_id:
                entities[str(chunk_id)].append(entity_id)
    resolved = {}
    for chunk_id, values in statuses.items():
        unique = set(values)
        if "rejected" in unique:
            status = "rejected"
        elif unique == {"approved"}:
            status = "approved"
        else:
            status = "pending"
        resolved[chunk_id] = {"review_status": status}
    return resolved, {key: sorted(set(value)) for key, value in entities.items()}


def _status_counts(records: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(row["governance"][field] for row in records).items()))


def _render_markdown(report: dict[str, Any]) -> str:
    statistics = report["statistics"]
    lines = [
        "# 证据治理状态迁移重放报告",
        "",
        "## 范围",
        "",
        "本报告只重放来源与实体审核数据到候选治理状态，不构建或发布 Retrieval Document、SQLite、embedding 或快索引，也不修改任何 release 指针。",
        "",
        "## 统计",
        "",
        f"- 记录数：{statistics['record_count']}",
        f"- 输入指纹：`{report['input_fingerprint']}`",
        f"- Policy：`{report['policy_version']}`",
    ]
    for status, count in statistics["retrieval_eligibility"].items():
        lines.append(f"- retrieval_eligibility={status}：{count}")
    lines.extend([
        "",
        "## 复核清单",
        "",
        f"- 独立审核状态提升：{len(report['status_promotions'])}",
        f"- 相对旧 approved 的检索降级：{len(report['retrieval_downgrades'])}",
        f"- ineligible：{len(report['ineligible_records'])}",
        f"- 阻断类别：{len(report['blockers'])}",
        "",
        "所有明细均保存在同目录的差异 JSON 中；缺失来源或审核信息保持 pending/unknown，不做推断提升。",
        "",
    ])
    return "\n".join(lines)


def replay_governance_migration(
    chunks: Iterable[dict[str, Any]],
    *,
    source_records: Iterable[dict[str, Any]],
    entity_evidence_records: Iterable[dict[str, Any]],
    output_root: Path,
) -> dict[str, Any]:
    chunks = sorted((dict(row) for row in chunks), key=lambda row: row.get("chunk_id", ""))
    sources = sorted(
        (dict(row) for row in source_records), key=lambda row: row.get("source_id", "")
    )
    entity_evidence = sorted(
        (dict(row) for row in entity_evidence_records),
        key=lambda row: (row.get("entity_id", ""), _canonical_json(row)),
    )
    sources_by_id = {str(row.get("source_id")): row for row in sources if row.get("source_id")}
    semantic_by_chunk, semantic_entities = _semantic_review_by_chunk(entity_evidence)
    policy = load_eligibility_policy()
    records = []
    status_promotions = []
    retrieval_downgrades = []
    ineligible_records = []
    missing_source_records = []
    missing_source_trace = []

    for chunk in chunks:
        chunk_id = str(chunk.get("chunk_id") or "")
        if not chunk_id:
            raise ValueError("治理迁移输入缺少 chunk_id")
        source_id = str(chunk.get("source_id") or chunk.get("doc_id") or "")
        source_record = sources_by_id.get(source_id)
        semantic_record = semantic_by_chunk.get(chunk_id)
        legacy_record = {
            **chunk,
            "parse_status": chunk.get("parse_status") or "parsed",
            "content_quality_status": (
                chunk.get("content_quality_status")
                or ("approved" if chunk.get("schema_version") == "semantic_chunk_v3" else None)
            ),
        }
        governance = migrate_legacy_governance(
            legacy_record,
            source_record=source_record,
            semantic_review_record=semantic_record,
        )
        source_refs = [str(item) for item in chunk.get("source_refs", []) if item]
        if not source_refs and chunk.get("source_ref"):
            source_refs = [str(chunk["source_ref"])]
        eligibility = derive_retrieval_eligibility(
            governance=governance,
            source_ref=source_refs[0] if source_refs else "",
            source_snapshot_id=str(chunk.get("source_snapshot_id") or ""),
            purpose="answer_evidence",
            source_type=str((source_record or {}).get("source_type") or chunk.get("document_profile") or ""),
            isolation_signals=[str(item) for item in chunk.get("isolation_signals", []) if item],
            policy=policy,
        )
        governance["retrieval_eligibility"] = eligibility
        row = {
            "schema_version": "evidence_governance_migration_record_v1",
            "chunk_id": chunk_id,
            "source_id": source_id,
            "legacy_review_status": chunk.get("review_status"),
            "semantic_review_entity_ids": semantic_entities.get(chunk_id, []),
            "governance": governance,
        }
        records.append(row)

        if source_record and governance["source_trust_status"] in {
            "trusted", "trusted_with_caution"
        }:
            status_promotions.append({
                "chunk_id": chunk_id,
                "dimension": "source_trust_status",
                "old_value": "unknown",
                "new_value": governance["source_trust_status"],
                "basis": governance["status_provenance"]["source_trust_status"],
            })
        if semantic_record and governance["semantic_review_status"] == "approved":
            status_promotions.append({
                "chunk_id": chunk_id,
                "dimension": "semantic_review_status",
                "old_value": "unknown",
                "new_value": "approved",
                "basis": governance["status_provenance"]["semantic_review_status"],
            })
        old_content_approved = (
            chunk.get("review_status") == "approved"
            or governance["content_quality_status"] == "approved"
        )
        if old_content_approved and eligibility["status"] != "eligible":
            retrieval_downgrades.append({
                "chunk_id": chunk_id,
                "from": "legacy_approved_content",
                "to": eligibility["status"],
                "rule_id": eligibility["rule_id"],
                "reason": eligibility["reason"],
            })
        if eligibility["status"] == "ineligible":
            ineligible_records.append({
                "chunk_id": chunk_id,
                "source_id": source_id,
                "rule_id": eligibility["rule_id"],
                "reason": eligibility["reason"],
            })
        if source_record is None:
            missing_source_records.append(chunk_id)
        if eligibility["rule_id"] == "retrieval.missing_source_trace":
            missing_source_trace.append(chunk_id)

    blockers = []
    for code, chunk_ids in (
        ("missing_source_record", missing_source_records),
        ("missing_source_trace", missing_source_trace),
    ):
        if chunk_ids:
            blockers.append({
                "code": code,
                "count": len(chunk_ids),
                "chunk_ids": sorted(chunk_ids),
            })
    report = {
        "schema_version": "evidence_governance_migration_diff_v1",
        "policy_version": policy["policy_version"],
        "policy_fingerprint": policy["policy_fingerprint"],
        "input_fingerprint": _fingerprint({
            "chunks": chunks,
            "source_records": sources,
            "entity_evidence_records": entity_evidence,
        }),
        "statistics": {
            "record_count": len(records),
            "parse_status": _status_counts(records, "parse_status"),
            "content_quality_status": _status_counts(records, "content_quality_status"),
            "source_trust_status": _status_counts(records, "source_trust_status"),
            "semantic_review_status": _status_counts(records, "semantic_review_status"),
            "retrieval_eligibility": dict(sorted(Counter(
                row["governance"]["retrieval_eligibility"]["status"] for row in records
            ).items())),
        },
        "status_promotions": sorted(
            status_promotions, key=lambda row: (row["chunk_id"], row["dimension"])
        ),
        "retrieval_downgrades": sorted(
            retrieval_downgrades, key=lambda row: row["chunk_id"]
        ),
        "ineligible_records": sorted(ineligible_records, key=lambda row: row["chunk_id"]),
        "blockers": blockers,
    }
    output_root = Path(output_root)
    _atomic_text(
        output_root / MIGRATION_RECORDS_NAME,
        "".join(_canonical_json(row) + "\n" for row in records),
    )
    _atomic_text(
        output_root / DIFF_REPORT_NAME,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_text(output_root / HUMAN_REPORT_NAME, _render_markdown(report))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="在临时候选目录重放证据治理状态迁移")
    parser.add_argument("--semantic-chunks", type=Path, required=True)
    parser.add_argument("--source-catalog", type=Path, required=True)
    parser.add_argument("--entity-evidence", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    report = replay_governance_migration(
        _load_jsonl(args.semantic_chunks),
        source_records=_load_jsonl(args.source_catalog),
        entity_evidence_records=_load_jsonl(args.entity_evidence),
        output_root=args.output_root,
    )
    print(json.dumps({
        "status": "complete",
        "statistics": report["statistics"],
        "blocker_count": len(report["blockers"]),
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
