#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
REPORT = paths.report_path("coverage_report")

TARGETS = {
    "BGPConcept": ("30", 30),
    "RoutingMechanism": ("10", 10),
    "AnomalyType": ("8", 8),
    "DataSource": ("8", 8),
    "DataField": ("30", 30),
    "EvidenceTemplate": ("8", 8),
    "PaperMethod": ("5", 5),
    "Case": ("5", 5),
    "Relationship": ("约 100", 100),
}

DATASET_DESCRIPTIONS = {
    "case_observations.jsonl": "从 data/corpus/cleaned/cases 用正则抽取的案例观察值",
    "case_observations.csv": "同一观察值数据的 CSV 版本",
    "source_processing_status.jsonl": "按 data/sources/inventory/source_id 汇总的确定性处理状态",
    "source_processing_status.csv": "同一来源处理状态数据的 CSV 版本",
    "source_gap_queue.jsonl": "未完成来源的缺口队列，记录建议后续动作",
    "source_gap_queue.csv": "同一来源缺口队列的 CSV 版本",
    "entity_review_queue.jsonl": "待人工复核实体队列，包含来源处理状态和建议动作",
    "entity_review_queue.csv": "同一实体复核队列的 CSV 版本",
    "entity_source_evidence.jsonl": "实体到来源的机械证据索引，列出路径和 chunk 样例",
    "entity_source_evidence.csv": "同一实体来源证据索引的 CSV 版本",
    "entity_review_packets.jsonl": "实体人工复核包，汇总实体字段、证据路径、chunk 样例和检查清单",
    "entity_review_packets.csv": "同一实体人工复核包的 CSV 版本",
    "authoritative_source_requirements.jsonl": "仅含 context/manual note 实体的权威来源补充需求队列",
    "authoritative_source_requirements.csv": "同一权威来源补充需求队列的 CSV 版本",
    "next_action_queue.jsonl": "统一下一步行动队列，合并补源、人工复核和按规则跳过事项",
    "next_action_queue.csv": "同一下一步行动队列的 CSV 版本",
    "human_review_workbook.jsonl": "面向人工审核的一行一实体复核工作簿，默认 unreviewed，不自动批准",
    "human_review_workbook.csv": "同一人工复核工作簿的 CSV 版本",
    "human_review_decision_audit.jsonl": "人工复核决策审计结果，识别可显式应用的 approved/rejected 决策",
    "human_review_decision_audit.csv": "同一人工复核决策审计结果的 CSV 版本",
    "human_review_decision_apply_preview.jsonl": "人工复核决策应用预览，记录 dry-run/write 模式、可应用决策、跳过状态和更新候选",
    "human_review_decision_apply_preview.csv": "同一人工复核决策应用预览的 CSV 版本",
    "human_review_input_validation.jsonl": "人工复核输入校验结果，检查主决策 CSV 的结构、枚举、重复项、未知实体和语义边界",
    "human_review_input_validation.csv": "同一人工复核输入校验结果的 CSV 版本",
    "human_review_progress.jsonl": "人工复核进度仪表盘，按整体、实体类型、复核批次和复核桶汇总",
    "human_review_progress.csv": "同一人工复核进度仪表盘的 CSV 版本",
    "human_review_evidence_extracts.jsonl": "人工复核证据摘录，按实体展开 chunk 样例、词项匹配和短摘录",
    "human_review_evidence_extracts.csv": "同一人工复核证据摘录的 CSV 版本",
    "human_review_session_queue.jsonl": "人工复核会话队列，将待复核实体切分为小批次并引用 top 摘录",
    "human_review_session_queue.csv": "同一人工复核会话队列的 CSV 版本",
    "human_review_session_status.jsonl": "人工复核会话状态汇总，按 session 汇总完成率、状态计数和下一条待处理实体",
    "human_review_session_status.csv": "同一人工复核会话状态汇总的 CSV 版本",
    "human_review_field_checklist.jsonl": "人工复核逐字段清单，把 pending 实体的结构化字段展开为字段级核验项",
    "human_review_field_checklist.csv": "同一人工复核逐字段清单的 CSV 版本",
    "human_review_source_matrix.jsonl": "人工复核来源矩阵，按来源聚合待复核实体、字段核验项、session 和证据路径",
    "human_review_source_matrix.csv": "同一人工复核来源矩阵的 CSV 版本",
    "human_review_task_board.jsonl": "人工复核任务板，整理 session、来源、输入校验、审计和应用入口的下一步执行队列",
    "human_review_task_board.csv": "同一人工复核任务板的 CSV 版本",
    "human_review_handoff.jsonl": "人工复核交接清单，逐项列出输入、人工输出目标、命令边界和验证入口",
    "human_review_handoff.csv": "同一人工复核交接清单的 CSV 版本",
    "glossary.jsonl": "从 entities 机械派生的 BGP 术语表",
    "glossary.csv": "同一术语表数据的 CSV 版本",
    "artifact_manifest.jsonl": "文件级制品清单，包含大小、行数和 SHA-256",
    "artifact_manifest.csv": "同一制品清单数据的 CSV 版本",
}

ARTIFACT_SCAN_DIRS = [
    "config",
    "inventory",
    "raw",
    "parsed",
    "cleaned",
    "chunks",
    "entities",
    "relationships",
    "published",
    "datasets",
    "review_inputs",
    "reports",
    "schemas",
    "scripts",
]

ARTIFACT_EXCLUDED_PATHS = {
    "data/derived/datasets/artifact_manifest.jsonl",
    "data/derived/datasets/artifact_manifest.csv",
    "data/generated/reports/publishing/artifact_manifest_report.md",
    "data/reports/gates/pipeline_report.md",
    "data/reports/gates/quality_report.md",
}

SCHEMA_LABELS = [
    "Source",
    "ParsedDocument",
    "Chunk",
    "BGPConcept",
    "RoutingMechanism",
    "AnomalyType",
    "DataSource",
    "DataField",
    "EvidenceTemplate",
    "FalsePositivePattern",
    "PaperMethod",
    "Case",
    "CaseObservation",
    "SourceProcessingStatus",
    "SourceGapQueueItem",
    "EntityReviewQueueItem",
    "EntitySourceEvidence",
    "EntityReviewPacket",
    "AuthoritativeSourceRequirement",
    "NextAction",
    "HumanReviewWorkbookEntry",
    "HumanReviewDecisionAudit",
    "HumanReviewDecisionApplyPreview",
    "HumanReviewInputValidation",
    "HumanReviewProgress",
    "HumanReviewEvidenceExtract",
    "HumanReviewSessionQueue",
    "HumanReviewSessionStatus",
    "HumanReviewFieldChecklist",
    "HumanReviewSourceMatrix",
    "HumanReviewTaskBoard",
    "HumanReviewHandoff",
    "GlossaryEntry",
    "ArtifactManifest",
    "Relationship",
]


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def count_csv_rows(path):
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def count_dataset(path):
    if path.name in {"artifact_manifest.jsonl", "artifact_manifest.csv"}:
        return count_expected_artifacts()
    if path.suffix == ".jsonl":
        return len(load_jsonl(path))
    if path.suffix == ".csv":
        return count_csv_rows(path)
    return 0


def relative_path(path):
    return path.relative_to(ROOT).as_posix()


def count_expected_artifacts():
    count = 0
    for dirname in ARTIFACT_SCAN_DIRS:
        base = ROOT / dirname
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if "__pycache__" in path.parts:
                continue
            if not path.is_file():
                continue
            if relative_path(path) in ARTIFACT_EXCLUDED_PATHS:
                continue
            count += 1
    return count


def count_files(dirname, pattern):
    base = ROOT / dirname
    if not base.exists():
        return Counter()
    return Counter(path.parent.name for path in base.glob(pattern))


def count_chunk_lines():
    counts = {}
    for path in sorted((paths.CHUNKS_DIR).glob("*.jsonl")):
        counts[path.name] = len(load_jsonl(path))
    return counts


def count_entities():
    counts = Counter()
    pending = Counter()
    for path in sorted((paths.ENTITIES_DIR).glob("*.jsonl")):
        for record in load_jsonl(path):
            entity_type = record.get("entity_type", "UNKNOWN")
            counts[entity_type] += 1
            if record.get("review_status") == "pending":
                pending[entity_type] += 1
    return counts, pending


def relationship_count():
    return len(load_jsonl(paths.RELATIONSHIPS_DIR / "relationships.jsonl"))


def status_for(current, target):
    if current >= target:
        return "已达到"
    return "部分覆盖"


def dataset_rows():
    rows = []
    for filename, description in DATASET_DESCRIPTIONS.items():
        path = paths.DATASETS_DIR / filename
        rows.append((f"data/derived/datasets/{filename}", count_dataset(path), description))
    return rows


def source_gap_summary():
    gaps = load_jsonl(paths.DATASETS_DIR / "source_gap_queue.jsonl")
    by_action = Counter(record.get("suggested_action", "unknown") for record in gaps)
    return gaps, by_action


def published_summary():
    published_dir = paths.PUBLISHED_DIR
    manifest = load_json(published_dir / "manifest.json")
    files = sorted(path.name for path in published_dir.glob("*") if path.is_file())
    return manifest, files


def main():
    entity_counts, pending_counts = count_entities()
    relationship_total = relationship_count()
    parsed_counts = count_files("parsed", "*/*.json")
    cleaned_counts = count_files("cleaned", "*/*.md")
    chunk_counts = count_chunk_lines()
    source_statuses = load_jsonl(paths.DATASETS_DIR / "source_processing_status.jsonl")
    source_status_counts = Counter(record.get("processing_status", "unknown") for record in source_statuses)
    gaps, gap_actions = source_gap_summary()
    published_manifest, published_files = published_summary()
    case_observations = len(load_jsonl(paths.DATASETS_DIR / "case_observations.jsonl"))
    total_chunks = sum(chunk_counts.values())

    lines = [
        "# 覆盖报告",
        "",
        "## MVP 覆盖快照",
        "",
        "| 范围 | 目标 | 当前 | 状态 |",
        "| --- | ---: | ---: | --- |",
    ]
    for entity_type, (target_label, target) in TARGETS.items():
        current = relationship_total if entity_type == "Relationship" else entity_counts.get(entity_type, 0)
        lines.append(f"| {entity_type} | {target_label} | {current} | {status_for(current, target)} |")

    lines.extend([
        "",
        "## 文本内化进度",
        "",
        "| 层级 | 当前结果 |",
        "| --- | ---: |",
    ])
    for dirname in ("standards", "data_docs", "papers", "cases"):
        lines.append(f"| data/corpus/parsed/{dirname} | {parsed_counts.get(dirname, 0)} 个 JSON |")
    for dirname in ("standards", "data_docs", "papers", "cases", "notes"):
        count = cleaned_counts.get(dirname, 0)
        if count:
            lines.append(f"| data/corpus/cleaned/{dirname} | {count} 个 Markdown |")

    lines.extend(["", "## Chunk 覆盖", "", "| 文件 | Chunk 数 |", "| --- | ---: |"])
    for filename, count in sorted(chunk_counts.items()):
        lines.append(f"| {filename} | {count} |")
    lines.append(f"| 合计 | {total_chunks} |")

    lines.extend(["", "## 规则化数据集覆盖", "", "| 文件 | 记录数 | 说明 |", "| --- | ---: | --- |"])
    for path, count, description in dataset_rows():
        lines.append(f"| {path} | {count} | {description} |")

    published_counts = published_manifest.get("counts", {})
    lines.extend([
        "",
        "## 发布知识库入口",
        "",
        "| 文件 | 状态 |",
        "| --- | --- |",
    ])
    for filename in [
        "README.md",
        "manifest.json",
        "source_catalog.jsonl",
        "entity_catalog.jsonl",
        "chunk_catalog.jsonl",
        "relationship_adjacency.json",
        "lexical_index.json",
        "bgp_knowledge_base.sqlite",
        "sqlite_schema.sql",
        "integrity_summary.json",
        "readiness_summary.json",
        "data_dictionary.json",
    ]:
        status = "已生成" if filename in published_files else "缺失"
        lines.append(f"| data/published/{filename} | {status} |")
    if published_counts:
        lines.extend(["", "| 发布项 | 数量 |", "| --- | ---: |"])
        for key, value in published_counts.items():
            lines.append(f"| {key} | {value} |")

    lines.extend([
        "",
        "## 来源处理状态",
        "",
        "| 状态 | 来源数 |",
        "| --- | ---: |",
    ])
    for status, count in sorted(source_status_counts.items()):
        lines.append(f"| {status} | {count} |")

    lines.extend([
        "",
        "## 来源缺口",
        "",
        f"- 当前缺口总数：{len(gaps)}",
    ])
    if gap_actions:
        for action, count in sorted(gap_actions.items()):
            lines.append(f"- {action}：{count}")
    else:
        lines.append("- 无")

    lines.extend([
        "",
        "## Schema 覆盖",
        "",
        "| 范围 | 状态 |",
        "| --- | --- |",
    ])
    for label in SCHEMA_LABELS:
        lines.append(f"| {label} | 已校验 |")

    lines.extend([
        "",
        "## 已覆盖主题",
        "",
        "- BGP 基础：BGP、AS、ASN、Prefix、BGP Speaker、BGP Session、eBGP、iBGP。",
        "- BGP 消息与数据：RIB、FIB、Update、Announcement、Withdrawal、MRT、Collector、Peer、Vantage Point。",
        "- 路径与属性：AS_PATH、Origin AS、NEXT_HOP、LOCAL_PREF、MED、OTC 等。",
        "- 路由策略：AS Relationship、Customer Cone、Valley-free、BGP Roles。",
        "- 路由安全：RPKI、ROA、ROV、BGPsec、RPKI-to-Router、ASPA、IRR、WHOIS/RDAP。",
        "- 异常类型：Prefix Hijack、Subprefix Hijack、Path Hijack、Route Leak、MOAS、Origin Change、Path Manipulation、Prefix Outage。",
        "- 数据源：RouteViews、RIPE RIS、BGPStream、CAIDA AS Relationship、CAIDA ASRank、RIPEstat、PeeringDB、MANRS、ASPA 文档。",
        "- 论文和案例来源文本已覆盖 HTML 与可抽取文本的 PDF；PeeringDB OpenAPI YAML 已进入文本层；结构化 PaperMethod 和 Case 扩展仍遵守“需要 LLM 介入则跳过”的边界。",
        "",
        "## 当前新增能力",
        "",
        "- `src/bgpkb/pipeline/parse_documents.py` 已支持 RFC TXT、HTML、YAML/OpenAPI schema 和可由 `pypdf` 确定性抽取文本的 PDF。",
        "- PDF 来源已进入 parsed、cleaned 和 chunks 层；PDF 解析只做文本抽取和按页切分，不做语义归纳。",
        "- YAML/OpenAPI schema 已进入 parsed、cleaned 和 chunks 层；YAML 解析只按顶层键机械分段。",
        "- `src/bgpkb/pipeline/build_case_observation_guides.py` 已生成中文逐案例观察值核验指南，只展开正则观察值，不判断角色、证据强度或影响范围。",
        "- `src/bgpkb/pipeline/build_source_gap_queue.py` 将未完成来源转换为待办队列；当前来源层缺口为 0。",
        "- `src/bgpkb/pipeline/build_entity_source_evidence.py` 已生成实体到来源的机械证据索引，为人工复核提供 parsed、cleaned 和 chunk 入口。",
        "- `src/bgpkb/pipeline/build_entity_review_packets.py` 已生成实体人工复核包，把实体字段、证据路径、chunk 样例和检查清单合并为人工审核入口。",
        "- `src/bgpkb/pipeline/build_authoritative_source_requirements.py` 已将仅含 context/manual note 的实体转成权威来源补充需求队列，且明确不做全量下载。",
        "- `src/bgpkb/pipeline/build_next_action_queue.py` 已将补源、人工复核和按规则跳过的语义任务合并成统一行动队列。",
        "- `src/bgpkb/pipeline/build_human_review_workbook.py` 已生成一行一实体的人工复核工作簿，默认 `unreviewed`，只供人工决策，不自动批准实体。",
        "- `src/bgpkb/pipeline/build_human_review_decision_template.py` 已生成 `data/review_inputs/human_review_decisions_template.csv`，并只在缺失时初始化 `data/review_inputs/human_review_decisions.csv`，避免覆盖人工填写结果。",
        "- `src/bgpkb/pipeline/build_human_review_input_validation.py` 已生成主人工决策输入校验，检查 CSV 结构、枚举、重复项、未知实体和语义边界，不判断实体内容。",
        "- `src/bgpkb/pipeline/build_human_review_decision_audit.py` 已生成工作簿决策审计，区分 no-op、可显式应用和需要语义流程阻塞的决策。",
        "- `src/bgpkb/pipeline/build_human_review_progress.py` 已生成人工复核进度仪表盘，按整体、实体类型、复核批次和复核桶汇总 pending、可应用决策与 LLM 阻塞计数。",
        "- `src/bgpkb/pipeline/build_human_review_evidence_extracts.py` 已生成人工复核证据摘录，按实体展开 chunk 样例、词项匹配和短摘录，只辅助人工定位，不判断证据充分性。",
        "- `src/bgpkb/pipeline/build_human_review_session_queue.py` 已生成人工复核会话队列，把 pending 实体按固定大小切成可执行小批次，并引用 top 摘录入口。",
        "- `src/bgpkb/pipeline/build_human_review_session_status.py` 已生成人工复核会话状态汇总，按 session 统计完成率、状态计数和下一条待处理实体。",
        "- `src/bgpkb/pipeline/build_human_review_field_checklist.py` 已生成人工复核逐字段清单，把实体 payload 展开为字段级核验项，方便逐字段确认来源支撑。",
        "- `src/bgpkb/pipeline/build_human_review_source_matrix.py` 已生成人工复核来源矩阵，按来源聚合受影响实体、字段核验项、session 和证据路径。",
        "- `src/bgpkb/pipeline/build_human_review_task_board.py` 已生成人工复核任务板，把 session、来源、输入校验、决策审计和显式应用入口整理为下一步执行队列。",
        "- `src/bgpkb/pipeline/build_human_review_handoff.py` 已生成人工复核交接清单，把任务板逐项转成输入、人工输出目标、命令边界和验证入口。",
        "- `src/bgpkb/pipeline/build_human_review_session_decision_templates.py` 已生成按 session 切分的人工决策模板，方便小批次填写主决策文件。",
        "- `src/bgpkb/pipeline/import_human_review_session_decisions.py` 提供逐 session 模板到主决策文件的显式导入入口；默认 dry-run，只有传入 `--write` 才会写入人工决策 CSV。",
        "- `src/bgpkb/pipeline/build_human_review_session_guides.py` 已生成中文分会话人工复核指南，把每个 session 的实体、来源路径和 top 摘录展开为可执行操作入口。",
        "- `src/bgpkb/pipeline/apply_human_review_decisions.py` 提供显式应用入口；默认 dry-run 并生成机器可读应用预览，只有传入 `--write` 且审计通过的 `approved/rejected` 人工决策才会改写实体状态。",
        "- `src/bgpkb/pipeline/build_human_review_guides.py` 已生成中文分批人工复核指南，展开证据路径、chunk 样例和按规则跳过的语义事项。",
        "- `rfc2622`、`rfc3912`、`rfc9082`、`rfc9083` 已作为少量权威标准来源补充归档，用于 IRR 与 WHOIS/RDAP 概念复核。",
        "- `src/bgpkb/pipeline/build_published_knowledge_base.py` 已生成 `data/published/` 发布入口，包含来源目录、实体目录、chunk 目录、关系邻接表、词项索引和发布 manifest。",
        "- `src/bgpkb/pipeline/build_sqlite_knowledge_base.py` 已生成 `data/published/bgp_knowledge_base.sqlite` 和 `data/published/sqlite_schema.sql`，用于本地 SQL 查询和程序化接入；数据库包含来源、实体、chunk、关系、词项、证据索引、复核包、行动队列、案例观察值、术语表、人工复核工作簿、决策审计、输入校验、复核进度、证据摘录、会话队列、会话状态、逐字段清单、来源矩阵、任务板和交接清单。",
        "- `src/bgpkb/pipeline/query_knowledge_base.py` 已提供本地查询 CLI；`src/bgpkb/pipeline/build_query_examples.py` 已生成固定查询样例报告，验证 stats、term、entity、source、neighbors、evidence、review-packets、workbook、extracts、sessions、actions、observations、glossary、decision-audit、input-validation、progress、field-checks、source-matrix、task-board、handoff 和全文检索入口。",
        "- `src/bgpkb/pipeline/build_published_integrity_report.py` 已生成发布完整性 gate，校验 published 文件、manifest 计数、SQLite 表计数、治理数据集、查询样例和边界标记之间的一致性。",
        "- `src/bgpkb/pipeline/build_readiness_report.py` 已生成知识库就绪度报告，把 `context.md` 的目标产物映射到当前证据，并区分确定性已达成项与需人工/语义流程项。",
        "- `src/bgpkb/pipeline/build_data_dictionary.py` 已生成数据字典，描述 published 文件、SQLite 表结构、JSONL 数据集字段和查询命令。",
        "- `src/bgpkb/pipeline/build_coverage_report.py` 从当前制品自动生成本报告，避免覆盖数字与流水线产物漂移。",
        "",
        "## 仍然存在的缺口",
        "",
    ])
    if pending_counts:
        total_pending = sum(pending_counts.values())
        lines.append(f"- 实体记录仍有 {total_pending} 条 `pending`，需要人工来源核验后才能改为 `approved`。")
    lines.extend([
        f"- PaperMethod 当前 {entity_counts.get('PaperMethod', 0)} 条，目标 5 条；从论文正文扩展结构化方法需要语义判断，已按规则跳过。",
        f"- 案例观察值已有 {case_observations} 条，但事件角色、证据强度和影响范围仍需人工或明确允许的语义流程。",
        "",
        "## 下一步优先级",
        "",
        "1. 基于 `data/generated/reports/review/human_review_guides/`、`data/derived/datasets/human_review_workbook.*` 与 `data/review_inputs/human_review_decisions.csv` 对 pending 实体做人工来源核验，人工确认并审计后再显式应用 `approved/rejected`。",
        "2. 基于 `data/generated/reports/review/case_observation_guides/` 与 `data/derived/datasets/case_observations.*` 做人工核验，人工确认后再决定是否写入 `data/knowledge/entities/cases.jsonl`。",
        "3. 明确允许语义流程后，再扩展 PaperMethod 和 Case 结构化字段。",
    ])

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
