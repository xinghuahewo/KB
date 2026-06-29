#!/usr/bin/env python3
import json
import shlex
import sqlite3
import subprocess
import sys
from collections import Counter
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
PUBLISHED_DIR = paths.PUBLISHED_DIR
DB_PATH = PUBLISHED_DIR / "bgp_knowledge_base.sqlite"
REPORT = paths.report_path("data_dictionary_report")
OUTPUT = PUBLISHED_DIR / "data_dictionary.json"
QUERY_MODULE = paths.pipeline_module("query_knowledge_base.py")

PUBLISHED_DESCRIPTIONS = {
    "README.md": "发布入口说明。",
    "manifest.json": "发布快照计数、输入输出和处理边界。",
    "source_catalog.jsonl": "来源目录，合并 inventory 和来源处理状态。",
    "entity_catalog.jsonl": "实体目录，包含实体 payload、来源、证据和复核桶。",
    "chunk_catalog.jsonl": "chunk 目录，包含 chunk 元数据、预览和所在文件。",
    "relationship_adjacency.json": "实体关系邻接表。",
    "lexical_index.json": "机械词项索引，映射到实体、来源和 chunks。",
    "bgp_knowledge_base.sqlite": "本地 SQL 查询入口。",
    "sqlite_schema.sql": "SQLite 表结构。",
    "integrity_summary.json": "发布完整性 gate 的机器可读摘要。",
    "readiness_summary.json": "知识库就绪度机器可读摘要。",
    "data_dictionary.json": "本数据字典的机器可读版本。",
    "jsonld_context.json": "阶段三点五语义标识前置层的 JSON-LD @context。",
    "semantic_id_map.jsonl": "实体、来源、chunk、关系和证据的稳定 URI 映射。",
    "embedding_manifest.json": "阶段四 RAG 框架的 embedding 覆盖、provider 和边界摘要。",
    "rag_mock_vector_index.jsonl": "阶段四离线 mock 向量索引，用于当前设备不运行模型时的检索框架验收。",
    "rag_retrieval_index.json": "阶段四检索索引摘要，登记 mock vector store、SQLite FTS5 兜底和可信集合规则。",
}

TABLE_DESCRIPTIONS = {
    "sources": "来源清单和确定性处理状态。",
    "entities": "结构化实体目录。",
    "entity_sources": "实体到来源的多对多引用。",
    "chunks": "知识片段目录和预览。",
    "chunk_topics": "chunk 到主题的多对多引用。",
    "relationships": "实体关系边。",
    "lexical_terms": "机械词项索引词表。",
    "lexical_entity_refs": "词项到实体引用。",
    "lexical_source_refs": "词项到来源引用。",
    "lexical_chunk_refs": "词项到 chunk 引用。",
    "entity_evidence": "实体到来源、路径和 chunk 样例的证据索引。",
    "review_packets": "实体人工复核包摘要。",
    "next_actions": "统一下一步行动队列。",
    "case_observations": "从案例 cleaned 文本正则抽取的观察值。",
    "glossary": "从实体机械派生的术语表。",
    "human_review_workbook": "人工复核工作簿。",
    "human_review_decision_audit": "人工复核决策审计，区分 no-op、可显式应用和阻塞状态。",
    "human_review_decision_apply_preview": "人工复核决策应用预览，记录 dry-run/write 模式和更新候选。",
    "human_review_input_validation": "人工复核输入校验，检查主决策 CSV 的结构和机械一致性。",
    "human_review_progress": "人工复核进度仪表盘，按整体、实体类型、批次和复核桶汇总。",
    "human_review_evidence_extracts": "人工复核证据摘录，按实体展开 chunk 样例、词项匹配和短摘录。",
    "human_review_session_queue": "人工复核会话队列，按 session 小批次组织待核验实体。",
    "human_review_session_status": "人工复核会话状态汇总，按 session 统计完成率、状态计数和下一条待处理实体。",
    "human_review_field_checklist": "人工复核逐字段清单，把 pending 实体的结构化字段展开为字段级核验项。",
    "human_review_source_matrix": "人工复核来源矩阵，按来源聚合待复核实体、字段核验项和证据路径。",
    "human_review_task_board": "人工复核任务板，整理 session、来源和审计入口的下一步执行队列。",
    "human_review_handoff": "人工复核交接清单，逐项列出输入、人工输出目标、命令边界和验证入口。",
    "meta": "SQLite 构建元数据。",
}

QUERY_COMMANDS = [
    "stats",
    "term route --limit 5",
    "entity anomaly_route_leak",
    "source rfc4271",
    "neighbors concept_as_path",
    "evidence anomaly_route_leak",
    "review-packets --bucket ready_without_manual_note --limit 5",
    "workbook --batch 01_ready_without_manual_note --limit 5",
    "extracts anomaly_route_leak --limit 3",
    "sessions --session-id review_session_001 --limit 5",
    "actions --needs-llm true --limit 5",
    "observations --type asn --limit 5",
    "glossary route --limit 5",
    "decision-audit --status no_op --limit 5",
    "apply-preview --record-type summary --limit 5",
    "input-validation --status pass --limit 5",
    "progress --scope-type overall --limit 5",
    "field-checks --session-id review_session_001 --limit 5",
    "source-matrix --source-id rfc4271 --limit 5",
    "task-board --type review_session --limit 5",
    "handoff --type review_session --limit 5",
    "search-entities RPKI --limit 5",
    'search-chunks "route leak" --limit 5',
]


def load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def sample_keys(path):
    records = load_jsonl(path)
    keys = set()
    for record in records[:20]:
        keys.update(record.keys())
    return sorted(keys)


def sqlite_tables():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        table_names = [
            row["name"]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                  AND name NOT LIKE '%_fts_%'
                ORDER BY name
                """
            )
        ]
        tables = []
        for table in table_names:
            columns = []
            for col in conn.execute(f"PRAGMA table_info({table})"):
                columns.append({
                    "name": col["name"],
                    "type": col["type"],
                    "not_null": bool(col["notnull"]),
                    "primary_key": bool(col["pk"]),
                    "default": col["dflt_value"],
                })
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            tables.append({
                "name": table,
                "description": TABLE_DESCRIPTIONS.get(table, ""),
                "row_count": count,
                "columns": columns,
            })
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        conn.close()
    return tables, integrity


def query_commands():
    commands = []
    for command in QUERY_COMMANDS:
        args = shlex.split(command)
        result = subprocess.run(
            [sys.executable, "-m", QUERY_MODULE, *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        commands.append({
            "command": paths.pipeline_command("query_knowledge_base.py", *args),
            "returncode": result.returncode,
            "stdout_preview": result.stdout[:500],
            "stderr": result.stderr.strip(),
        })
    return commands


def build_dictionary():
    manifest = load_json(PUBLISHED_DIR / "manifest.json")
    integrity = load_json(PUBLISHED_DIR / "integrity_summary.json")
    readiness = load_json(PUBLISHED_DIR / "readiness_summary.json")
    tables, sqlite_integrity = sqlite_tables()

    published_files = []
    for path in sorted(PUBLISHED_DIR.iterdir()):
        if not path.is_file():
            continue
        published_files.append({
            "path": path.relative_to(ROOT).as_posix(),
            "description": PUBLISHED_DESCRIPTIONS.get(path.name, ""),
            "extension": path.suffix or "none",
            "size_bytes": path.stat().st_size,
            "jsonl_keys": sample_keys(path) if path.suffix == ".jsonl" else [],
        })

    datasets = []
    for path in sorted((paths.DATASETS_DIR).glob("*.jsonl")):
        datasets.append({
            "path": path.relative_to(ROOT).as_posix(),
            "records": len(load_jsonl(path)),
            "keys": sample_keys(path),
        })

    query_examples = query_commands()
    query_status_counts = Counter("pass" if item["returncode"] == 0 else "fail" for item in query_examples)

    return {
        "generated_by": "src/bgpkb/pipeline/build_data_dictionary.py",
        "published_counts": manifest.get("counts", {}),
        "readiness_status": readiness.get("status", ""),
        "integrity_status": integrity.get("status", ""),
        "sqlite_integrity": sqlite_integrity,
        "published_files": published_files,
        "sqlite_tables": tables,
        "datasets": datasets,
        "query_commands": query_examples,
        "query_status_counts": dict(query_status_counts),
        "boundary": manifest.get("boundary", {}),
    }


def write_outputs(dictionary):
    OUTPUT.write_text(json.dumps(dictionary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# 数据字典报告",
        "",
        "## 范围",
        "",
        "本报告描述当前 BGP 知识库发布包的数据入口、SQLite 表结构、JSONL 数据集字段和查询命令。",
        "",
        "生成过程只读取现有文件和 SQLite PRAGMA，不联网、不下载、不调用 LLM、不做语义判断。",
        "",
        "## 摘要",
        "",
        f"- Readiness：{dictionary['readiness_status']}",
        f"- 发布完整性：{dictionary['integrity_status']}",
        f"- SQLite integrity_check：{dictionary['sqlite_integrity']}",
        f"- Published 文件数：{len(dictionary['published_files'])}",
        f"- SQLite 表数：{len(dictionary['sqlite_tables'])}",
        f"- JSONL 数据集数：{len(dictionary['datasets'])}",
        f"- 查询命令数：{len(dictionary['query_commands'])}",
        "- JSON 输出：`data/published/data_dictionary.json`",
        "",
        "## Published 文件",
        "",
        "| 文件 | 大小字节 | 说明 | JSONL 字段 |",
        "| --- | ---: | --- | --- |",
    ]
    for item in dictionary["published_files"]:
        keys = ", ".join(item["jsonl_keys"]) if item["jsonl_keys"] else ""
        lines.append(f"| `{item['path']}` | {item['size_bytes']} | {item['description']} | {keys} |")

    lines.extend(["", "## SQLite 表", "", "| 表 | 行数 | 说明 | 字段 |", "| --- | ---: | --- | --- |"])
    for table in dictionary["sqlite_tables"]:
        columns = ", ".join(f"{col['name']} {col['type']}".strip() for col in table["columns"])
        lines.append(f"| `{table['name']}` | {table['row_count']} | {table['description']} | {columns} |")

    lines.extend(["", "## JSONL 数据集", "", "| 数据集 | 记录数 | 字段 |", "| --- | ---: | --- |"])
    for dataset in dictionary["datasets"]:
        lines.append(f"| `{dataset['path']}` | {dataset['records']} | {', '.join(dataset['keys'])} |")

    lines.extend(["", "## 查询命令", "", "| 命令 | 状态 |", "| --- | --- |"])
    for item in dictionary["query_commands"]:
        status = "通过" if item["returncode"] == 0 else f"失败({item['returncode']})"
        lines.append(f"| `{item['command']}` | {status} |")

    lines.extend([
        "",
        "## 边界",
        "",
        f"- uses_llm：{dictionary['boundary'].get('uses_llm')}",
        f"- downloads_sources：{dictionary['boundary'].get('downloads_sources')}",
        f"- approves_pending_entities：{dictionary['boundary'].get('approves_pending_entities')}",
        f"- semantic_extraction：{dictionary['boundary'].get('semantic_extraction')}",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    dictionary = build_dictionary()
    write_outputs(dictionary)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    if dictionary["sqlite_integrity"] != "ok" or dictionary["integrity_status"] != "pass":
        raise SystemExit(1)
    if any(item["returncode"] != 0 for item in dictionary["query_commands"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
