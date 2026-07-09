#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
DATASET_DIR = paths.DATASETS_DIR
REPORT = paths.report_path("authoritative_source_requirements_report")
JSONL_OUTPUT = DATASET_DIR / "authoritative_source_requirements.jsonl"
CSV_OUTPUT = DATASET_DIR / "authoritative_source_requirements.csv"


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def source_plan_for(packet):
    entity_id = packet["entity_id"]
    entity_type = packet["entity_type"]
    display_name = packet["display_name"]
    if entity_id == "field_review_status":
        return {
            "requirement_type": "internal_governance_source_needed",
            "required_source_categories": ["internal_schema_or_project_design"],
            "candidate_source_hints": [
                "如果该字段只是知识库治理字段，应由 schema 或 README 明确说明。",
                "如果该字段不是 BGP 领域字段，应考虑从 DataField 实体中移出或保持 pending。",
            ],
            "search_query": "",
            "suggested_action": "补充内部 schema/README 依据，或人工决定是否从领域 DataField 中移除。",
        }
    if entity_id == "concept_whois_rdap":
        return {
            "requirement_type": "external_authoritative_source_needed",
            "required_source_categories": ["rfc", "rir_official_documentation"],
            "candidate_source_hints": [
                "RDAP 相关 RFC",
                "ARIN/RIPE/APNIC 等 RIR 的 WHOIS/RDAP 官方说明",
            ],
            "search_query": "WHOIS RDAP RFC RIR official documentation BGP prefix ownership",
            "suggested_action": "补充 RFC 或 RIR 官方文档后，再核验 WHOIS/RDAP 概念定义和适用边界。",
        }
    if entity_id == "concept_irr":
        return {
            "requirement_type": "external_authoritative_source_needed",
            "required_source_categories": ["rir_official_documentation", "irr_operator_documentation"],
            "candidate_source_hints": [
                "RIPE Database、ARIN IRR、APNIC IRR 或 RADb 官方说明",
                "RIR 关于 route/route6/route-set 对象的文档",
            ],
            "search_query": "Internet Routing Registry IRR route object official documentation",
            "suggested_action": "补充 RIR 或 IRR 运营方官方文档后，再核验 IRR 概念定义和证据边界。",
        }
    if entity_type == "Case":
        return {
            "requirement_type": "external_authoritative_source_needed",
            "required_source_categories": ["incident_report", "operator_postmortem", "research_or_measurement_report"],
            "candidate_source_hints": [
                f"{display_name} 的运营商公告、事件复盘或测量报告",
                "MANRS、Cloudflare、APNIC、RIPE Labs、Dyn/Oracle Internet Intelligence 等事件分析",
            ],
            "search_query": f"{display_name} BGP incident report route leak hijack outage",
            "suggested_action": "只登记少量权威事件报告；不要全量下载，先确认来源可支撑事件时间、AS、prefix 和影响字段。",
        }
    return {
        "requirement_type": "external_authoritative_source_needed",
        "required_source_categories": ["official_documentation", "standard", "research_report"],
        "candidate_source_hints": [f"{display_name} 的官方文档、标准或可信研究报告"],
        "search_query": f"{display_name} BGP official documentation",
        "suggested_action": "补充可直接支撑实体字段的权威来源后再复核。",
    }


def build_records():
    packets = load_jsonl(DATASET_DIR / "entity_review_packets.jsonl")
    records = []
    for packet in packets:
        if packet.get("review_bucket") != "context_only_needs_authoritative_source":
            continue
        plan = source_plan_for(packet)
        entity_id = packet["entity_id"]
        records.append({
            "requirement_id": f"authsrc_{entity_id}",
            "entity_id": entity_id,
            "entity_type": packet["entity_type"],
            "display_name": packet["display_name"],
            "review_bucket": packet["review_bucket"],
            "current_source_refs": packet.get("source_refs", []),
            "current_source_ref_count": packet.get("source_ref_count", 0),
            "requirement_type": plan["requirement_type"],
            "required_source_categories": plan["required_source_categories"],
            "candidate_source_hints": plan["candidate_source_hints"],
            "search_query": plan["search_query"],
            "suggested_action": plan["suggested_action"],
            "llm_skip_note": "未使用 LLM 判断来源相关性；本记录只给出机械补源需求和人工检索提示。",
            "download_scope_note": "不要全量下载；人工确认候选来源后再单条登记和归档。",
            "generated_by": "src/bgpkb/pipeline/build_authoritative_source_requirements.py",
        })
    records.sort(key=lambda item: (item["entity_type"], item["display_name"].lower(), item["entity_id"]))
    return records


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "requirement_id",
        "entity_id",
        "entity_type",
        "display_name",
        "review_bucket",
        "current_source_refs",
        "current_source_ref_count",
        "requirement_type",
        "required_source_categories",
        "candidate_source_hints",
        "search_query",
        "suggested_action",
        "llm_skip_note",
        "download_scope_note",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = dict(record)
            for field in ("current_source_refs", "required_source_categories", "candidate_source_hints"):
                row[field] = "|".join(row[field])
            writer.writerow(row)


def write_report(records):
    by_type = Counter(record["entity_type"] for record in records)
    by_requirement_type = Counter(record["requirement_type"] for record in records)
    lines = [
        "# 权威来源补充需求报告",
        "",
        "## 范围",
        "",
        "本报告从实体人工复核包中机械筛出 `context_only_needs_authoritative_source` 记录，生成补充权威来源的需求队列。该步骤不联网、不下载资料、不判断候选来源是否足以批准实体。",
        "",
        "## 摘要",
        "",
        f"- 需求记录数：{len(records)}",
        f"- JSONL 输出：`data/derived/datasets/authoritative_source_requirements.jsonl`",
        f"- CSV 输出：`data/derived/datasets/authoritative_source_requirements.csv`",
        "- 下载范围：不要全量下载；确认单条候选来源后再登记归档。",
        "",
        "## 按需求类型统计",
        "",
    ]
    for requirement_type, count in sorted(by_requirement_type.items()):
        lines.append(f"- {requirement_type}：{count}")
    lines.extend(["", "## 按实体类型统计", ""])
    for entity_type, count in sorted(by_type.items()):
        lines.append(f"- {entity_type}：{count}")
    lines.extend([
        "",
        "## 需求明细",
        "",
        "| 实体 ID | 类型 | 名称 | 推荐来源类别 | 检索提示 |",
        "| --- | --- | --- | --- | --- |",
    ])
    for record in records:
        categories = "<br>".join(record["required_source_categories"])
        query = record["search_query"] or "内部 schema/README 决策"
        lines.append(
            f"| `{record['entity_id']}` | {record['entity_type']} | {record['display_name']} | {categories} | {query} |"
        )
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未使用 LLM 判断候选来源相关性。",
        "- 未从网页、论文或案例正文中抽取新实体。",
        "- 未批量下载资料；下一步应只对人工确认的少量来源做单条归档。",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    records = build_records()
    write_jsonl(records)
    write_csv(records)
    write_report(records)
    print(f"Wrote {JSONL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {CSV_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
