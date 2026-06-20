#!/usr/bin/env python3
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
import json

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "lifecycle_policy.yaml"
ENTITY_DIR = ROOT / "entities"
RELATIONSHIP_FILE = ROOT / "relationships" / "relationships.jsonl"
EVIDENCE_FILE = ROOT / "datasets" / "entity_source_evidence.jsonl"
PACKET_FILE = ROOT / "datasets" / "entity_review_packets.jsonl"
ACTION_FILE = ROOT / "datasets" / "next_action_queue.jsonl"
DECISION_AUDIT_FILE = ROOT / "datasets" / "human_review_decision_audit.jsonl"


def load_jsonl(path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_config():
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def iter_entities():
    for path in sorted(ENTITY_DIR.glob("*.jsonl")):
        for record in load_jsonl(path):
            yield record, path.relative_to(ROOT).as_posix()


def index_by_entity(rows):
    grouped = defaultdict(list)
    for row in rows:
        entity_id = row.get("entity_id")
        if entity_id:
            grouped[entity_id].append(row)
    return grouped


def first_by_entity(rows):
    result = {}
    for row in rows:
        entity_id = row.get("entity_id")
        if entity_id and entity_id not in result:
            result[entity_id] = row
    return result


def load_relationship_references():
    references = defaultdict(list)
    for row in load_jsonl(RELATIONSHIP_FILE):
        source = row.get("source")
        target = row.get("target")
        relation = row.get("relation")
        if source and target:
            references[source].append({"direction": "outgoing", "neighbor": target, "relation": relation})
            references[target].append({"direction": "incoming", "neighbor": source, "relation": relation})
    return references


def override_index(config, key):
    return {item["entity_id"]: item for item in config.get(key, []) if item.get("entity_id")}


def approved_decisions_by_entity(rows):
    result = {}
    for row in rows:
        if row.get("application_status") == "ready_to_apply" and row.get("review_decision") == "approved":
            result[row["entity_id"]] = row
    return result


def derive_lifecycle(entity, packet, evidence_rows, action_rows, config, status_override):
    allowed = {state["id"] for state in config["states"]}
    entity_id = entity["id"]
    review_status = entity.get("review_status", "pending")
    source_refs = entity.get("source_refs", [])

    if status_override:
        status = status_override["lifecycle_status"]
        if status not in allowed:
            raise ValueError(f"Unknown lifecycle_status override for {entity_id}: {status}")
        return status, f"策略显式覆盖为 {status}。"

    if review_status == "approved":
        if evidence_rows:
            return "approved", "实体 review_status=approved，且存在来源证据索引记录。"
        return "reviewed", "实体已标记 approved，但缺少来源证据索引，先进入 reviewed。"

    if review_status in {"rejected", "deprecated"}:
        return "deprecated", f"实体 review_status={review_status}，默认不进入活跃 approved 视图。"

    if source_refs and (packet or action_rows or evidence_rows):
        return "candidate", "实体仍待复核，但已有来源、复核包、证据或行动项。"

    return "draft", "实体缺少足够来源或复核上下文。"


def build_inventory(config):
    evidence_by_entity = index_by_entity(load_jsonl(EVIDENCE_FILE))
    actions_by_entity = index_by_entity([row for row in load_jsonl(ACTION_FILE) if row.get("status") == "open"])
    packets_by_entity = first_by_entity(load_jsonl(PACKET_FILE))
    decisions_by_entity = approved_decisions_by_entity(load_jsonl(DECISION_AUDIT_FILE))
    status_overrides = override_index(config, "status_overrides")
    validity_overrides = override_index(config, "validity_overrides")

    rows = []
    for entity, entity_file in iter_entities():
        entity_id = entity["id"]
        packet = packets_by_entity.get(entity_id, {})
        evidence_rows = evidence_by_entity.get(entity_id, [])
        action_rows = actions_by_entity.get(entity_id, [])
        decision = decisions_by_entity.get(entity_id, {})
        validity = validity_overrides.get(entity_id, {})
        status, reason = derive_lifecycle(
            entity,
            packet,
            evidence_rows,
            action_rows,
            config,
            status_overrides.get(entity_id),
        )
        source_refs = entity.get("source_refs", [])
        rows.append({
            "lifecycle_id": f"lifecycle_{entity_id}",
            "entity_id": entity_id,
            "entity_type": entity.get("entity_type", ""),
            "display_name": entity.get("name") or entity.get("paper") or entity.get("id", ""),
            "entity_file": entity_file,
            "review_status": entity.get("review_status", "pending"),
            "lifecycle_status": status,
            "lifecycle_reason": reason,
            "source_refs": source_refs,
            "source_ref_count": len(source_refs),
            "evidence_index": [row["evidence_id"] for row in evidence_rows if row.get("evidence_id")],
            "evidence_record_count": len(evidence_rows),
            "review_packet_id": packet.get("packet_id", ""),
            "review_bucket": packet.get("review_bucket", ""),
            "open_action_count": len(action_rows),
            "next_action_ids": [row["action_id"] for row in action_rows if row.get("action_id")],
            "reviewed_by": decision.get("decision_reviewer", ""),
            "approved_at": decision.get("decision_reviewed_at", "") if status == "approved" else "",
            "valid_from": validity.get("valid_from", ""),
            "valid_until": validity.get("valid_until", ""),
            "generated_by": "scripts/build_lifecycle_report.py",
        })
    return sorted(rows, key=lambda row: (row["entity_type"], row["entity_id"]))


def check_quality_rules(rows, config):
    row_by_id = {row["entity_id"]: row for row in rows}
    references = load_relationship_references()
    today = date.today().isoformat()
    checks = []

    missing_status = [row["entity_id"] for row in rows if not row.get("lifecycle_status")]
    checks.append({
        "rule_id": "lifecycle_status_required",
        "status": "pass" if not missing_status else "fail",
        "count": len(missing_status),
        "items": missing_status,
    })

    approved_without_evidence = [
        row["entity_id"]
        for row in rows
        if row["lifecycle_status"] == "approved" and row["evidence_record_count"] < 1
    ]
    checks.append({
        "rule_id": "approved_requires_review_evidence",
        "status": "pass" if not approved_without_evidence else "fail",
        "count": len(approved_without_evidence),
        "items": approved_without_evidence,
    })

    inactive_referenced = []
    for row in rows:
        if row["lifecycle_status"] in {"deprecated", "archived"} and references.get(row["entity_id"]):
            inactive_referenced.append(row["entity_id"])
    checks.append({
        "rule_id": "deprecated_or_archived_reference_warning",
        "status": "pass" if not inactive_referenced else "warning",
        "count": len(inactive_referenced),
        "items": inactive_referenced,
    })

    expired_without_action = [
        row["entity_id"]
        for row in rows
        if row.get("valid_until")
        and row["valid_until"] < today
        and row["open_action_count"] == 0
        and row["lifecycle_status"] not in {"deprecated", "archived"}
    ]
    checks.append({
        "rule_id": "expired_validity_requires_action",
        "status": "pass" if not expired_without_action else "warning",
        "count": len(expired_without_action),
        "items": expired_without_action,
    })

    inconsistent = []
    for row in rows:
        review_status = row["review_status"]
        lifecycle_status = row["lifecycle_status"]
        if review_status == "pending" and lifecycle_status == "approved":
            inconsistent.append(row["entity_id"])
        if review_status == "approved" and lifecycle_status in {"draft", "candidate"}:
            inconsistent.append(row["entity_id"])
    checks.append({
        "rule_id": "review_lifecycle_consistency",
        "status": "pass" if not inconsistent else "fail",
        "count": len(inconsistent),
        "items": sorted(set(inconsistent)),
    })

    known_rule_ids = {rule["id"] for rule in config["quality_rules"]}
    unknown_checks = sorted(set(check["rule_id"] for check in checks) - known_rule_ids)
    if unknown_checks:
        raise ValueError(f"Quality checks not registered in policy: {unknown_checks}")
    return checks


def write_inventory(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def status_label(status):
    return {
        "draft": "草稿",
        "candidate": "候选",
        "reviewed": "已复核",
        "approved": "已批准",
        "deprecated": "已弃用",
        "archived": "已归档",
        "pass": "通过",
        "fail": "失败",
        "warning": "提示",
    }.get(status, status)


def render_report(config, rows, checks):
    state_order = [state["id"] for state in config["states"]]
    status_counts = Counter(row["lifecycle_status"] for row in rows)
    review_counts = Counter(row["review_status"] for row in rows)
    type_counts = Counter(row["entity_type"] for row in rows)
    metadata_fields = config["metadata_fields"]

    field_coverage = []
    for field in metadata_fields:
        if field == "review_packet":
            present = sum(1 for row in rows if row.get("review_packet_id"))
        elif field == "next_action":
            present = sum(1 for row in rows if row.get("next_action_ids"))
        else:
            present = sum(1 for row in rows if field in row and row.get(field) not in ("", [], None))
        field_coverage.append((field, present, len(rows) - present))

    lines = [
        "# 生命周期治理报告",
        "",
        "## 范围",
        "",
        "本报告基于 `config/lifecycle_policy.yaml` 生成，读取现有实体、证据索引、复核包、行动队列和人工决策审计，输出实体级生命周期治理视图。",
        "",
        "该步骤不联网、不调用 LLM，不修改实体、关系、chunk 或发布包。",
        "",
        "## 摘要",
        "",
        f"- 配置版本：`{config['version']}`",
        f"- 实体总数：{len(rows)}",
        f"- 生命周期状态数：{len(state_order)}",
        f"- 质量规则数：{len(checks)}",
        "",
        "## 生命周期状态统计",
        "",
        "| 生命周期状态 | 实体数 |",
        "| --- | ---: |",
    ]
    for status in state_order:
        lines.append(f"| {status_label(status)} (`{status}`) | {status_counts.get(status, 0)} |")

    lines.extend(["", "## review_status 对照", "", "| review_status | 实体数 |", "| --- | ---: |"])
    for status, count in sorted(review_counts.items()):
        lines.append(f"| `{status}` | {count} |")

    lines.extend(["", "## 实体类型覆盖", "", "| 实体类型 | 实体数 |", "| --- | ---: |"])
    for entity_type, count in sorted(type_counts.items()):
        lines.append(f"| `{entity_type}` | {count} |")

    lines.extend(["", "## 元数据覆盖", "", "| 字段 | 有值记录数 | 缺失或空值记录数 |", "| --- | ---: | ---: |"])
    for field, present, missing in field_coverage:
        lines.append(f"| `{field}` | {present} | {missing} |")

    lines.extend(["", "## 质量规则结果", "", "| 规则 | 状态 | 命中数 | 样例 |", "| --- | --- | ---: | --- |"])
    for check in checks:
        sample = "<br>".join(check["items"][:10]) if check["items"] else "无"
        lines.append(f"| `{check['rule_id']}` | {status_label(check['status'])} | {check['count']} | {sample} |")

    lines.extend(["", "## 下一步行动", ""])
    pending_rows = [row for row in rows if row["lifecycle_status"] in {"draft", "candidate", "reviewed"}]
    if pending_rows:
        lines.append("- 优先处理 `candidate` 实体的人工复核与来源补充，使其进入 `approved`。")
        lines.append("- 对 `reviewed` 但缺少证据索引的实体补齐证据记录或降低生命周期状态。")
        lines.append("- 仅在明确替代或失效时，通过策略显式标记 `deprecated` 或 `archived`。")
    else:
        lines.append("- 当前实体均已达到 approved 或更明确的非活跃状态。")

    lines.extend(["", "## 候选与待处理实体样例", "", "| 实体 | 类型 | 生命周期 | 行动项数 | 原因 |", "| --- | --- | --- | ---: | --- |"])
    for row in pending_rows[:20]:
        lines.append(
            f"| `{row['entity_id']}` | `{row['entity_type']}` | `{row['lifecycle_status']}` | "
            f"{row['open_action_count']} | {row['lifecycle_reason']} |"
        )

    return "\n".join(lines).rstrip() + "\n"


def main():
    config = load_config()
    inventory_path = ROOT / config["generated_policy"]["inventory_path"]
    report_path = ROOT / config["generated_policy"]["report_path"]

    rows = build_inventory(config)
    checks = check_quality_rules(rows, config)

    write_inventory(rows, inventory_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(config, rows, checks), encoding="utf-8")

    print(f"Wrote {inventory_path.relative_to(ROOT)}")
    print(f"Wrote {report_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
