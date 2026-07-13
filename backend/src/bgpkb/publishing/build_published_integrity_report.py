#!/usr/bin/env python3
import json
import re
import sqlite3
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
PUBLISHED_DIR = paths.PUBLISHED_DIR
REPORT = paths.report_path("published_integrity_report")
SUMMARY = PUBLISHED_DIR / "integrity_summary.json"
DB_PATH = PUBLISHED_DIR / "bgp_knowledge_base.sqlite"

EXPECTED_PUBLISHED_FILES = [
    "README.md",
    "manifest.json",
    "source_catalog.jsonl",
    "entity_catalog.jsonl",
    "chunk_catalog.jsonl",
    "relationship_adjacency.json",
    "lexical_index.json",
    "bgp_knowledge_base.sqlite",
    "sqlite_schema.sql",
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


def count_jsonl(path):
    return len(load_jsonl(path))


def sqlite_count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def add_check(checks, name, ok, detail):
    checks.append({"name": name, "status": "pass" if ok else "fail", "detail": detail})


def query_report_counts():
    path = paths.report_path("query_examples_report")
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    total = passed = failed = None
    for key, label in (("total", "查询样例数"), ("passed", "通过数"), ("failed", "失败数")):
        match = re.search(rf"- {label}：([0-9]+)", text)
        if match:
            value = int(match.group(1))
            if key == "total":
                total = value
            elif key == "passed":
                passed = value
            else:
                failed = value
    return {"total": total, "passed": passed, "failed": failed}


def build_summary():
    manifest = load_json(PUBLISHED_DIR / "manifest.json")
    relationship_adjacency = load_json(PUBLISHED_DIR / "relationship_adjacency.json")
    lexical_index = load_json(PUBLISHED_DIR / "lexical_index.json")
    query_counts = query_report_counts()

    file_presence = {
        filename: (PUBLISHED_DIR / filename).exists()
        for filename in EXPECTED_PUBLISHED_FILES
    }

    published_counts = {
        "sources": count_jsonl(PUBLISHED_DIR / "source_catalog.jsonl"),
        "entities": count_jsonl(PUBLISHED_DIR / "entity_catalog.jsonl"),
        "chunks": count_jsonl(PUBLISHED_DIR / "chunk_catalog.jsonl"),
        "relationships": relationship_adjacency.get("relationship_count", 0),
        "lexical_terms": len(lexical_index),
        "pending_entities": sum(
            1 for record in load_jsonl(PUBLISHED_DIR / "entity_catalog.jsonl")
            if record.get("review_status") == "pending"
        ),
        "semantic_skipped_actions": sum(
            1 for record in load_jsonl(paths.DATASETS_DIR / "next_action_queue.jsonl")
            if record.get("needs_llm")
        ),
        "source_gap_items": count_jsonl(paths.DATASETS_DIR / "source_gap_queue.jsonl"),
        "human_review_decision_audit": count_jsonl(paths.DATASETS_DIR / "human_review_decision_audit.jsonl"),
        "human_review_decision_apply_preview": count_jsonl(paths.DATASETS_DIR / "human_review_decision_apply_preview.jsonl"),
        "human_review_input_validation": count_jsonl(paths.DATASETS_DIR / "human_review_input_validation.jsonl"),
        "human_review_progress": count_jsonl(paths.DATASETS_DIR / "human_review_progress.jsonl"),
        "human_review_field_checklist": count_jsonl(paths.DATASETS_DIR / "human_review_field_checklist.jsonl"),
        "human_review_source_matrix": count_jsonl(paths.DATASETS_DIR / "human_review_source_matrix.jsonl"),
        "human_review_task_board": count_jsonl(paths.DATASETS_DIR / "human_review_task_board.jsonl"),
        "human_review_handoff": count_jsonl(paths.DATASETS_DIR / "human_review_handoff.jsonl"),
    }

    dataset_counts = {
        "entity_evidence": count_jsonl(paths.DATASETS_DIR / "entity_source_evidence.jsonl"),
        "review_packets": count_jsonl(paths.DATASETS_DIR / "entity_review_packets.jsonl"),
        "next_actions": count_jsonl(paths.DATASETS_DIR / "next_action_queue.jsonl"),
        "case_observations": count_jsonl(paths.DATASETS_DIR / "case_observations.jsonl"),
        "glossary": count_jsonl(paths.DATASETS_DIR / "glossary.jsonl"),
        "human_review_workbook": count_jsonl(paths.DATASETS_DIR / "human_review_workbook.jsonl"),
        "human_review_decision_audit": count_jsonl(paths.DATASETS_DIR / "human_review_decision_audit.jsonl"),
        "human_review_decision_apply_preview": count_jsonl(paths.DATASETS_DIR / "human_review_decision_apply_preview.jsonl"),
        "human_review_input_validation": count_jsonl(paths.DATASETS_DIR / "human_review_input_validation.jsonl"),
        "human_review_progress": count_jsonl(paths.DATASETS_DIR / "human_review_progress.jsonl"),
        "human_review_evidence_extracts": count_jsonl(paths.DATASETS_DIR / "human_review_evidence_extracts.jsonl"),
        "human_review_session_queue": count_jsonl(paths.DATASETS_DIR / "human_review_session_queue.jsonl"),
        "human_review_session_status": count_jsonl(paths.DATASETS_DIR / "human_review_session_status.jsonl"),
        "human_review_field_checklist": count_jsonl(paths.DATASETS_DIR / "human_review_field_checklist.jsonl"),
        "human_review_source_matrix": count_jsonl(paths.DATASETS_DIR / "human_review_source_matrix.jsonl"),
        "human_review_task_board": count_jsonl(paths.DATASETS_DIR / "human_review_task_board.jsonl"),
        "human_review_handoff": count_jsonl(paths.DATASETS_DIR / "human_review_handoff.jsonl"),
    }

    sqlite_counts = {}
    sqlite_integrity = "missing"
    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        try:
            sqlite_integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            for table in [
                "sources",
                "entities",
                "chunks",
                "relationships",
                "lexical_terms",
                "entity_evidence",
                "review_packets",
                "next_actions",
                "case_observations",
                "glossary",
                "human_review_workbook",
                "human_review_decision_audit",
                "human_review_decision_apply_preview",
                "human_review_input_validation",
                "human_review_progress",
                "human_review_evidence_extracts",
                "human_review_session_queue",
                "human_review_session_status",
                "human_review_field_checklist",
                "human_review_source_matrix",
                "human_review_task_board",
                "human_review_handoff",
            ]:
                sqlite_counts[table] = sqlite_count(conn, table)
        finally:
            conn.close()

    checks = []
    for filename, exists in file_presence.items():
        add_check(checks, f"published_file:{filename}", exists, "present" if exists else "missing")

    for key, actual in published_counts.items():
        expected = manifest.get("counts", {}).get(key)
        add_check(
            checks,
            f"manifest_count:{key}",
            expected == actual,
            f"manifest={expected}, actual={actual}",
        )

    for key in ["sources", "entities", "chunks", "relationships", "lexical_terms"]:
        add_check(
            checks,
            f"sqlite_count:{key}",
            sqlite_counts.get(key) == published_counts.get(key),
            f"sqlite={sqlite_counts.get(key)}, published={published_counts.get(key)}",
        )

    for key, expected in dataset_counts.items():
        add_check(
            checks,
            f"sqlite_dataset_count:{key}",
            sqlite_counts.get(key) == expected,
            f"sqlite={sqlite_counts.get(key)}, dataset={expected}",
        )

    add_check(checks, "sqlite_integrity", sqlite_integrity == "ok", sqlite_integrity)
    add_check(
        checks,
        "query_examples",
        query_counts.get("failed") == 0 and query_counts.get("total") == query_counts.get("passed"),
        json.dumps(query_counts, ensure_ascii=False, sort_keys=True),
    )

    boundary = manifest.get("boundary", {})
    boundary_expectations = {
        "uses_llm": False,
        "downloads_sources": False,
        "approves_pending_entities": False,
        "semantic_extraction": False,
    }
    for key, expected in boundary_expectations.items():
        add_check(
            checks,
            f"boundary:{key}",
            boundary.get(key) is expected,
            f"manifest={boundary.get(key)}, expected={expected}",
        )

    summary = {
        "generated_by": "src/bgpkb/pipeline/build_published_integrity_report.py",
        "status": "pass" if all(check["status"] == "pass" for check in checks) else "fail",
        "published_counts": published_counts,
        "dataset_counts": dataset_counts,
        "sqlite_counts": sqlite_counts,
        "sqlite_integrity": sqlite_integrity,
        "query_examples": query_counts,
        "checks": checks,
    }
    return summary


def write_outputs(summary):
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# 发布完整性校验报告",
        "",
        "## 范围",
        "",
        "本报告校验 `data/published/` 文件化入口、发布 manifest、SQLite 数据库、治理数据集和固定查询样例之间的一致性。",
        "",
        "该步骤不联网、不下载、不调用 LLM、不做语义判断，也不改变实体审批状态。",
        "",
        "## 摘要",
        "",
        f"- 总体状态：{'通过' if summary['status'] == 'pass' else '失败'}",
        f"- 检查项数：{len(summary['checks'])}",
        f"- 失败项数：{sum(1 for check in summary['checks'] if check['status'] != 'pass')}",
        f"- SQLite integrity_check：{summary['sqlite_integrity']}",
        f"- 查询样例失败数：{summary['query_examples'].get('failed')}",
        "- JSON 输出：`data/published/integrity_summary.json`",
        "",
        "## 关键计数",
        "",
        "| 项 | published | sqlite/dataset |",
        "| --- | ---: | ---: |",
    ]
    for key, value in summary["published_counts"].items():
        comparison = summary["sqlite_counts"].get(key, summary["dataset_counts"].get(key, ""))
        lines.append(f"| {key} | {value} | {comparison} |")
    for key, value in summary["dataset_counts"].items():
        if key in summary["published_counts"]:
            continue
        lines.append(f"| {key} | {value} | {summary['sqlite_counts'].get(key, '')} |")

    lines.extend(["", "## 检查项", "", "| 名称 | 状态 | 详情 |", "| --- | --- | --- |"])
    for check in summary["checks"]:
        status = "通过" if check["status"] == "pass" else "失败"
        lines.append(f"| {check['name']} | {status} | {check['detail']} |")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    summary = build_summary()
    write_outputs(summary)
    print(f"Wrote {SUMMARY.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    if summary["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
