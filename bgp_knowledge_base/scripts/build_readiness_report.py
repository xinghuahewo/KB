#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "readiness_report.md"
SUMMARY = ROOT / "published" / "readiness_summary.json"


def load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path):
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def count_files(pattern):
    return len(list(ROOT.glob(pattern)))


def file_exists(rel):
    return (ROOT / rel).exists()


def status(ok, blocked=False):
    if ok:
        return "achieved"
    if blocked:
        return "requires_human_or_semantic"
    return "incomplete"


def build_deliverables():
    manifest = load_json(ROOT / "published" / "manifest.json")
    integrity = load_json(ROOT / "published" / "integrity_summary.json")
    counts = manifest.get("counts", {})
    entity_counts = manifest.get("entity_type_counts", {})
    source_gaps = load_jsonl(ROOT / "datasets" / "source_gap_queue.jsonl")
    next_actions = load_jsonl(ROOT / "datasets" / "next_action_queue.jsonl")
    semantic_skips = [item for item in next_actions if item.get("needs_llm")]
    open_actions = [item for item in next_actions if item.get("status") == "open"]

    deliverables = [
        {
            "id": "raw_source_library",
            "name": "BGP 原始资料库",
            "status": status(counts.get("sources", 0) > 0 and len(source_gaps) == 0),
            "evidence": ["inventory/sources.csv", "raw/", "datasets/source_processing_status.jsonl"],
            "count": counts.get("sources", 0),
            "note": "来源层无缺口；不做全量下载。",
        },
        {
            "id": "cleaned_text_library",
            "name": "BGP 清洗文本库",
            "status": status(count_files("cleaned/*/*.md") > 0),
            "evidence": ["cleaned/", "reports/parse_report.md"],
            "count": count_files("cleaned/*/*.md"),
            "note": "TXT/HTML/YAML/PDF 可抽取文本已进入 cleaned 层。",
        },
        {
            "id": "chunk_library",
            "name": "BGP 知识片段库",
            "status": status(counts.get("chunks", 0) > 0),
            "evidence": ["chunks/", "published/chunk_catalog.jsonl"],
            "count": counts.get("chunks", 0),
            "note": "chunk 目录和发布 catalog 已生成。",
        },
        {
            "id": "concept_entity_library",
            "name": "BGP 概念实体库",
            "status": status(entity_counts.get("BGPConcept", 0) >= 30),
            "evidence": ["entities/bgp_concepts.jsonl", "published/entity_catalog.jsonl"],
            "count": entity_counts.get("BGPConcept", 0),
            "note": "实体保持 pending，等待人工来源复核。",
        },
        {
            "id": "anomaly_type_library",
            "name": "BGP 异常类型库",
            "status": status(entity_counts.get("AnomalyType", 0) >= 8),
            "evidence": ["entities/anomaly_types.jsonl", "entities/evidence_templates.jsonl"],
            "count": entity_counts.get("AnomalyType", 0),
            "note": "异常类型与证据模板已建立。",
        },
        {
            "id": "data_source_library",
            "name": "BGP 数据源说明库",
            "status": status(entity_counts.get("DataSource", 0) >= 8),
            "evidence": ["entities/data_sources.jsonl", "published/source_catalog.jsonl"],
            "count": entity_counts.get("DataSource", 0),
            "note": "覆盖 RouteViews、RIPE RIS、BGPStream、CAIDA、RIPEstat、PeeringDB 等来源。",
        },
        {
            "id": "evidence_field_library",
            "name": "BGP 证据字段库",
            "status": status(entity_counts.get("DataField", 0) >= 30 and entity_counts.get("EvidenceTemplate", 0) >= 8),
            "evidence": ["entities/data_fields.jsonl", "entities/evidence_templates.jsonl"],
            "count": entity_counts.get("DataField", 0),
            "note": "字段和证据模板已结构化，仍需人工批准。",
        },
        {
            "id": "case_library",
            "name": "BGP 案例库",
            "status": status(entity_counts.get("Case", 0) >= 5),
            "evidence": ["entities/cases.jsonl", "datasets/case_observations.jsonl", "reports/case_observation_guides/"],
            "count": entity_counts.get("Case", 0),
            "note": "案例观察值已机械抽取；角色、影响范围、证据强度仍需人工或语义流程。",
        },
        {
            "id": "glossary",
            "name": "BGP 术语表",
            "status": status(count_files("datasets/glossary.jsonl") == 1 and counts.get("entities", 0) > 0),
            "evidence": ["datasets/glossary.jsonl", "published/bgp_knowledge_base.sqlite"],
            "count": len(load_jsonl(ROOT / "datasets" / "glossary.jsonl")),
            "note": "术语表从实体机械派生，不自动润色或补同义词。",
        },
        {
            "id": "relationship_table",
            "name": "BGP 关系表",
            "status": status(counts.get("relationships", 0) >= 100),
            "evidence": ["relationships/relationships.jsonl", "published/relationship_adjacency.json"],
            "count": counts.get("relationships", 0),
            "note": "关系表已达 MVP 目标；不从正文自动推断新语义关系。",
        },
        {
            "id": "quality_report",
            "name": "质量检查报告",
            "status": status(file_exists("reports/quality_report.md") and integrity.get("status") == "pass"),
            "evidence": ["reports/quality_report.md", "reports/published_integrity_report.md"],
            "count": len(integrity.get("checks", [])),
            "note": "发布完整性 gate 通过，质量问题计数由 quality_report 记录。",
        },
        {
            "id": "published_queryable_package",
            "name": "可查询发布包",
            "status": status(
                file_exists("published/bgp_knowledge_base.sqlite")
                and file_exists("scripts/query_knowledge_base.py")
                and integrity.get("status") == "pass"
            ),
            "evidence": ["published/", "published/bgp_knowledge_base.sqlite", "scripts/query_knowledge_base.py"],
            "count": counts.get("entities", 0),
            "note": "发布包含 JSONL/JSON/SQLite/查询 CLI/完整性摘要。",
        },
        {
            "id": "semantic_review_boundary",
            "name": "语义/LLM 跳过边界",
            "status": status(len(semantic_skips) >= 2, blocked=True),
            "evidence": ["reports/llm_processing_skip_report.md", "datasets/next_action_queue.jsonl"],
            "count": len(semantic_skips),
            "note": "按用户要求，PaperMethod 扩展和案例语义核验跳过并记录。",
        },
        {
            "id": "human_review_boundary",
            "name": "人工复核边界",
            "status": status(len(open_actions) == 0, blocked=True),
            "evidence": ["datasets/human_review_workbook.jsonl", "reports/human_review_guides/"],
            "count": len(open_actions),
            "note": "pending 实体需要人工来源核验；当前不自动批准。",
        },
    ]
    return deliverables


def build_summary():
    deliverables = build_deliverables()
    counts = {
        "achieved": sum(1 for item in deliverables if item["status"] == "achieved"),
        "requires_human_or_semantic": sum(1 for item in deliverables if item["status"] == "requires_human_or_semantic"),
        "incomplete": sum(1 for item in deliverables if item["status"] == "incomplete"),
    }
    return {
        "generated_by": "scripts/build_readiness_report.py",
        "status": "ready_deterministic" if counts["incomplete"] == 0 else "incomplete",
        "counts": counts,
        "deliverables": deliverables,
    }


def write_outputs(summary):
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# 知识库就绪度报告",
        "",
        "## 范围",
        "",
        "本报告把 `context.md` 中的目标产物映射到当前确定性证据。它不做语义判断、不调用 LLM、不自动批准实体。",
        "",
        "## 摘要",
        "",
        f"- 总体状态：{summary['status']}",
        f"- 已达到：{summary['counts']['achieved']}",
        f"- 需人工或语义流程：{summary['counts']['requires_human_or_semantic']}",
        f"- 未完成：{summary['counts']['incomplete']}",
        "- JSON 输出：`published/readiness_summary.json`",
        "",
        "## 目标产物映射",
        "",
        "| 目标产物 | 状态 | 数量 | 证据 | 说明 |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for item in summary["deliverables"]:
        evidence = "<br>".join(f"`{path}`" for path in item["evidence"])
        lines.append(f"| {item['name']} | {item['status']} | {item['count']} | {evidence} | {item['note']} |")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    summary = build_summary()
    write_outputs(summary)
    print(f"Wrote {SUMMARY.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    if summary["status"] == "incomplete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
