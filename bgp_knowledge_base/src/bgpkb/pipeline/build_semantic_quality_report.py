#!/usr/bin/env python3
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from bgpkb import paths
import json
import re

import yaml


ROOT = paths.PROJECT_ROOT
CONFIG = paths.CONFIG_DIR / "semantic_quality_rules.yaml"
ENTITY_DIR = paths.ENTITIES_DIR
RELATIONSHIP_FILE = paths.RELATIONSHIPS_DIR / "relationships.jsonl"
LIFECYCLE_FILE = paths.DATASETS_DIR / "lifecycle_inventory.jsonl"
ACTION_FILE = paths.DATASETS_DIR / "next_action_queue.jsonl"


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
        for row in load_jsonl(path):
            yield row


def load_entities():
    by_id = {}
    by_type = defaultdict(list)
    for row in iter_entities():
        entity_id = row.get("id")
        if not entity_id:
            continue
        by_id[entity_id] = row
        by_type[row.get("entity_type", "")].append(row)
    return by_id, by_type


def index_by(rows, key):
    result = defaultdict(list)
    for row in rows:
        value = row.get(key)
        if value:
            result[value].append(row)
    return result


def first_by(rows, key):
    result = {}
    for row in rows:
        value = row.get(key)
        if value and value not in result:
            result[value] = row
    return result


def rule_severity(config, rule_id):
    for rule in config["rules"]:
        if rule["id"] == rule_id:
            return rule["severity"]
    raise ValueError(f"Unknown semantic quality rule: {rule_id}")


def sanitize(value):
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).lower()).strip("_")
    return cleaned or "unknown"


def make_finding(config, rule_id, subject_type, subject_id, field, message, suggested_action, lifecycle_status="unknown"):
    severity = rule_severity(config, rule_id)
    return {
        "finding_id": "finding_"
        + "_".join([sanitize(rule_id), sanitize(subject_type), sanitize(subject_id), sanitize(field)]),
        "rule_id": rule_id,
        "severity": severity,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "field": field,
        "message": message,
        "suggested_action": suggested_action,
        "lifecycle_status": lifecycle_status,
        "generated_by": "src/bgpkb/pipeline/build_semantic_quality_report.py",
    }


def lifecycle_status_for(entity_id, lifecycle):
    return lifecycle.get(entity_id, {}).get("lifecycle_status", "unknown")


def terms(value):
    return {item for item in re.split(r"[^a-z0-9]+", str(value).lower()) if item}


def semantic_terms(value, config):
    ignored = set(config.get("field_mapping_ignored_terms", []))
    return {item for item in terms(value) if item not in ignored}


def build_term_index(rows, config):
    index = []
    for row in rows:
        values = [row.get("id", ""), row.get("name", "")]
        token_set = set()
        for value in values:
            token_set.update(semantic_terms(value, config))
        if token_set:
            index.append((row, token_set))
    return index


def maps_to_known_term(value, term_index, config):
    value_terms = semantic_terms(value, config)
    if not value_terms:
        return False
    for _, candidate_terms in term_index:
        if candidate_terms and candidate_terms <= value_terms:
            return True
        if value_terms and candidate_terms and value_terms <= candidate_terms:
            return True
        if len(value_terms & candidate_terms) >= 2:
            return True
    return False


def check_anomaly_required_evidence_template_coverage(by_type, lifecycle, config):
    findings = []
    templates_by_anomaly = defaultdict(list)
    for template in by_type.get("EvidenceTemplate", []):
        templates_by_anomaly[template.get("applies_to")].append(template)

    for anomaly in by_type.get("AnomalyType", []):
        entity_id = anomaly["id"]
        templates = templates_by_anomaly.get(entity_id, [])
        lifecycle_status = lifecycle_status_for(entity_id, lifecycle)
        if not templates:
            findings.append(make_finding(
                config,
                "anomaly_required_evidence_template_coverage",
                anomaly.get("entity_type", "AnomalyType"),
                entity_id,
                "required_evidence",
                "异常类型没有对应的 EvidenceTemplate。",
                "为该异常类型新增或关联 EvidenceTemplate。",
                lifecycle_status,
            ))
            continue

        template_required = set()
        for template in templates:
            template_required.update(template.get("required_evidence", []))
            template_required.update(template.get("optional_evidence", []))
        missing = sorted(set(anomaly.get("required_evidence", [])) - template_required)
        if missing:
            findings.append(make_finding(
                config,
                "anomaly_required_evidence_template_coverage",
                anomaly.get("entity_type", "AnomalyType"),
                entity_id,
                "required_evidence",
                "异常类型的 required_evidence 未被 EvidenceTemplate 完整覆盖：" + ", ".join(missing),
                "补齐 EvidenceTemplate 的 required_evidence，或在规则配置中登记解释性例外。",
                lifecycle_status,
            ))
    return findings


def check_evidence_template_field_mapping(by_type, lifecycle, config):
    findings = []
    term_index = build_term_index(
        [*by_type.get("DataField", []), *by_type.get("BGPConcept", [])],
        config,
    )
    for template in by_type.get("EvidenceTemplate", []):
        entity_id = template["id"]
        lifecycle_status = lifecycle_status_for(entity_id, lifecycle)
        fields = sorted(set(template.get("required_evidence", []) + template.get("optional_evidence", [])))
        unmapped = [field for field in fields if not maps_to_known_term(field, term_index, config)]
        if unmapped:
            findings.append(make_finding(
                config,
                "evidence_template_field_mapping",
                "EvidenceTemplate",
                entity_id,
                "required_evidence",
                "证据字段尚未能确定性映射到 DataField 或 BGPConcept：" + ", ".join(unmapped[:12]),
                "补充 DataField、Concept 或语义映射规则；无法自动判断时进入人工复核。",
                lifecycle_status,
            ))
    return findings


def allowed_pair_map(config):
    result = {}
    for relation, pairs in config.get("relationship_type_constraints", {}).items():
        result[relation] = {tuple(pair) for pair in pairs}
    return result


def check_relationship_type_constraints(relationships, entity_index, lifecycle, config):
    findings = []
    allowed = allowed_pair_map(config)
    for index, relationship in enumerate(relationships, start=1):
        relation = relationship.get("relation", "")
        src_id = relationship.get("src_id", "")
        dst_id = relationship.get("dst_id", "")
        src_type = relationship.get("src_type", "")
        dst_type = relationship.get("dst_type", "")
        subject_id = f"{src_id}->{relation}->{dst_id}"
        lifecycle_status = lifecycle_status_for(src_id, lifecycle)

        if src_id not in entity_index or dst_id not in entity_index:
            findings.append(make_finding(
                config,
                "relationship_type_constraint",
                "Relationship",
                subject_id,
                "endpoint",
                "关系引用了不存在的实体端点。",
                "修复关系端点 ID，或先补齐对应实体。",
                lifecycle_status,
            ))
            continue

        actual_src_type = entity_index[src_id].get("entity_type")
        actual_dst_type = entity_index[dst_id].get("entity_type")
        if actual_src_type != src_type or actual_dst_type != dst_type:
            findings.append(make_finding(
                config,
                "relationship_type_constraint",
                "Relationship",
                subject_id,
                "entity_type",
                f"关系声明类型与实体实际类型不一致：声明 {src_type}->{dst_type}，实际 {actual_src_type}->{actual_dst_type}。",
                "按实体目录修正关系 src_type/dst_type。",
                lifecycle_status,
            ))
            continue

        if (src_type, dst_type) not in allowed.get(relation, set()):
            findings.append(make_finding(
                config,
                "relationship_type_constraint",
                "Relationship",
                subject_id,
                "relation",
                f"关系类型 `{relation}` 不允许连接 {src_type}->{dst_type}。",
                "在关系类型约束中登记该组合，或调整关系类型。",
                lifecycle_status,
            ))
    return findings


def check_case_anomaly_type_mapping(by_type, lifecycle, config):
    findings = []
    anomaly_terms = []
    for anomaly in by_type.get("AnomalyType", []):
        combined = f"{anomaly.get('id', '')} {anomaly.get('name', '')} {anomaly.get('category', '')}"
        anomaly_terms.append((anomaly, semantic_terms(combined, config)))

    for case in by_type.get("Case", []):
        entity_id = case["id"]
        event_type = case.get("event_type", "")
        lifecycle_status = lifecycle_status_for(entity_id, lifecycle)
        event_terms = semantic_terms(event_type, config)
        matched = any(event_terms and event_terms <= tokens for _, tokens in anomaly_terms)
        if not matched:
            matched = any(len(event_terms & tokens) >= 2 for _, tokens in anomaly_terms)
        if not matched:
            findings.append(make_finding(
                config,
                "case_anomaly_type_mapping",
                "Case",
                entity_id,
                "event_type",
                f"案例 event_type `{event_type}` 尚未能映射到已知 AnomalyType。",
                "补充 Case 到 AnomalyType 的 instance_of 关系，或规范 event_type 命名。",
                lifecycle_status,
            ))
    return findings


def check_datasource_field_lineage(by_type, relationships, lifecycle, config):
    findings = []
    datasource_to_fields = defaultdict(set)
    datafield_ids = {field["id"] for field in by_type.get("DataField", [])}
    for relationship in relationships:
        src_id = relationship.get("src_id")
        dst_id = relationship.get("dst_id")
        if relationship.get("src_type") == "DataSource" and dst_id in datafield_ids:
            datasource_to_fields[src_id].add(dst_id)
        if relationship.get("dst_type") == "DataSource" and src_id in datafield_ids:
            datasource_to_fields[dst_id].add(src_id)

    for datasource in by_type.get("DataSource", []):
        entity_id = datasource["id"]
        if not datasource_to_fields.get(entity_id):
            findings.append(make_finding(
                config,
                "datasource_field_lineage",
                "DataSource",
                entity_id,
                "relationships",
                "数据源尚未通过关系连接到任何 DataField。",
                "补充 DataSource provides/supports DataField 的关系，或在来源证据中说明字段链路。",
                lifecycle_status_for(entity_id, lifecycle),
            ))
    return findings


def check_candidate_excluded_from_trusted_rag(lifecycle, config):
    findings = []
    for entity_id, row in lifecycle.items():
        if row.get("lifecycle_status") == "candidate":
            findings.append(make_finding(
                config,
                "candidate_excluded_from_trusted_rag",
                row.get("entity_type", "Entity"),
                entity_id,
                "lifecycle_status",
                "candidate 实体不能进入高可信默认集合。",
                "完成人工复核与证据补齐后，再进入 approved 生命周期。",
                "candidate",
            ))
    return findings


def check_expired_validity_requires_action(lifecycle, open_actions_by_entity, config):
    findings = []
    today = date.today().isoformat()
    for entity_id, row in lifecycle.items():
        valid_until = row.get("valid_until")
        if not valid_until or valid_until >= today:
            continue
        if row.get("lifecycle_status") in {"deprecated", "archived"}:
            continue
        if open_actions_by_entity.get(entity_id):
            continue
        findings.append(make_finding(
            config,
            "expired_validity_requires_action",
            row.get("entity_type", "Entity"),
            entity_id,
            "valid_until",
            f"实体 valid_until={valid_until} 已过期，但没有打开的行动项。",
            "补充复核行动项，或将实体降级为 deprecated/archived。",
            row.get("lifecycle_status", "unknown"),
        ))
    return findings


def finalize_findings(findings):
    rows = sorted(findings, key=lambda row: (row["severity"], row["rule_id"], row["subject_type"], row["subject_id"], row["field"]))
    seen = Counter()
    for row in rows:
        base = row["finding_id"]
        seen[base] += 1
        if seen[base] > 1:
            row["finding_id"] = f"{base}_{seen[base]}"
    return rows


def build_findings(config):
    entity_index, by_type = load_entities()
    relationships = load_jsonl(RELATIONSHIP_FILE)
    lifecycle = first_by(load_jsonl(LIFECYCLE_FILE), "entity_id")
    open_actions_by_entity = index_by([row for row in load_jsonl(ACTION_FILE) if row.get("status") == "open"], "entity_id")

    findings = []
    findings.extend(check_anomaly_required_evidence_template_coverage(by_type, lifecycle, config))
    findings.extend(check_evidence_template_field_mapping(by_type, lifecycle, config))
    findings.extend(check_relationship_type_constraints(relationships, entity_index, lifecycle, config))
    findings.extend(check_case_anomaly_type_mapping(by_type, lifecycle, config))
    findings.extend(check_datasource_field_lineage(by_type, relationships, lifecycle, config))
    findings.extend(check_candidate_excluded_from_trusted_rag(lifecycle, config))
    findings.extend(check_expired_validity_requires_action(lifecycle, open_actions_by_entity, config))

    allowed = set(config["allowed_severities"])
    bad = sorted({row["severity"] for row in findings} - allowed)
    if bad:
        raise ValueError(f"Unknown semantic severity values: {bad}")
    return finalize_findings(findings)


def trusted_rag_entities(lifecycle, findings, config):
    blocker_subjects = {row["subject_id"] for row in findings if row["severity"] == "blocker"}
    trusted_status = config["generated_policy"]["trusted_rag_default_lifecycle_status"]
    trusted = [
        row
        for entity_id, row in lifecycle.items()
        if row.get("lifecycle_status") == trusted_status and entity_id not in blocker_subjects
    ]
    return sorted(trusted, key=lambda row: (row.get("entity_type", ""), row.get("entity_id", "")))


def write_jsonl(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def render_report(config, findings):
    severity_counts = Counter(row["severity"] for row in findings)
    rule_counts = Counter(row["rule_id"] for row in findings)
    lifecycle = first_by(load_jsonl(LIFECYCLE_FILE), "entity_id")
    trusted = trusted_rag_entities(lifecycle, findings, config)
    candidate_findings = [row for row in findings if row["rule_id"] == "candidate_excluded_from_trusted_rag"]
    blocker_findings = [row for row in findings if row["severity"] == "blocker"]
    human_review_findings = [
        row for row in findings if row["severity"] in {"blocker", "warning"}
    ]

    lines = [
        "# 语义质量治理报告",
        "",
        "## 范围",
        "",
        "本报告基于 `metadata/config/semantic_quality_rules.yaml` 生成，读取实体、关系、生命周期清单、行动队列和来源证据索引，输出确定性语义质量 findings。",
        "",
        "该步骤不联网、不调用 LLM，不自动修改实体、关系、chunk、来源或发布包。",
        "",
        "## 语义问题总览",
        "",
        f"- 配置版本：`{config['version']}`",
        f"- finding 总数：{len(findings)}",
        f"- blocker 数：{severity_counts.get('blocker', 0)}",
        f"- warning 数：{severity_counts.get('warning', 0)}",
        f"- info 数：{severity_counts.get('info', 0)}",
        f"- 高可信默认集合实体数：{len(trusted)}",
        "",
        "## 等级统计",
        "",
        "| 等级 | 数量 |",
        "| --- | ---: |",
    ]
    for severity in config["allowed_severities"]:
        lines.append(f"| `{severity}` | {severity_counts.get(severity, 0)} |")

    lines.extend(["", "## 规则统计", "", "| 规则 | 数量 |", "| --- | ---: |"])
    for rule in config["rules"]:
        lines.append(f"| `{rule['id']}` | {rule_counts.get(rule['id'], 0)} |")

    lines.extend(["", "## RAG 默认可信集合影响", ""])
    if blocker_findings:
        lines.append("- 存在 blocker，相关主体必须从默认高可信 RAG 集合排除。")
    else:
        lines.append("- 当前没有 blocker 级语义问题；默认高可信集合主要由 approved 生命周期控制。")
    lines.append(f"- candidate 排除提示数：{len(candidate_findings)}")
    if candidate_findings:
        lines.append("- candidate 样例：" + ", ".join(f"`{row['subject_id']}`" for row in candidate_findings[:10]))

    lines.extend(["", "## 人工复核建议", ""])
    if human_review_findings:
        lines.append("- 优先处理 blocker；warning 进入人工复核或语义映射补充。")
        lines.append("- 每条 finding 的 `suggested_action` 可作为下一步行动队列候选来源。")
    else:
        lines.append("- 当前没有 blocker 或 warning。")

    lines.extend(["", "## 后续 RAG 可依赖集合", ""])
    lines.append("- 默认策略：`lifecycle_status=approved` 且主体无 blocker。")
    lines.append(f"- 当前可依赖实体数：{len(trusted)}")
    if trusted:
        sample = ", ".join(f"`{row['entity_id']}`" for row in trusted[:20])
        lines.append(f"- 样例：{sample}")

    lines.extend(["", "## Finding 样例", "", "| 等级 | 规则 | 主体 | 字段 | 建议 |", "| --- | --- | --- | --- | --- |"])
    for row in findings[:30]:
        lines.append(
            f"| `{row['severity']}` | `{row['rule_id']}` | `{row['subject_id']}` | "
            f"`{row['field']}` | {row['suggested_action']} |"
        )

    return "\n".join(lines).rstrip() + "\n"


def main():
    config = load_config()
    findings = build_findings(config)
    findings_path = paths.resolve_logical_path(config["generated_policy"]["findings_path"])
    report_path = paths.resolve_logical_path(config["generated_policy"]["report_path"])
    write_jsonl(findings, findings_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(config, findings), encoding="utf-8")
    print(f"Wrote {paths.rel(findings_path)}")
    print(f"Wrote {paths.rel(report_path)}")


if __name__ == "__main__":
    main()
