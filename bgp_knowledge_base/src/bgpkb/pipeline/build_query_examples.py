#!/usr/bin/env python3
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
REPORT = paths.report_path("query_examples_report")
QUERY_MODULE = paths.pipeline_module("query_knowledge_base.py")
DB_PATH = paths.PUBLISHED_DIR / "bgp_knowledge_base.sqlite"


EXAMPLES = [
    ("stats", ["stats"]),
    ("term_route", ["term", "route", "--limit", "5"]),
    ("entity_route_leak", ["entity", "anomaly_route_leak"]),
    ("neighbors_as_path", ["neighbors", "concept_as_path"]),
    ("source_rfc4271", ["source", "rfc4271"]),
    ("evidence_route_leak", ["evidence", "anomaly_route_leak"]),
    ("review_packets_ready", ["review-packets", "--bucket", "ready_without_manual_note", "--limit", "5"]),
    ("workbook_first_batch", ["workbook", "--batch", "01_ready_without_manual_note", "--limit", "5"]),
    ("extracts_route_leak", ["extracts", "anomaly_route_leak", "--limit", "3"]),
    ("sessions_first", ["sessions", "--session-id", "review_session_001", "--limit", "5"]),
    ("actions_open", ["actions", "--status", "open", "--limit", "5"]),
    ("actions_llm_skipped", ["actions", "--needs-llm", "true", "--limit", "5"]),
    ("observations_asn", ["observations", "--type", "asn", "--limit", "5"]),
    ("glossary_route", ["glossary", "route", "--limit", "5"]),
    ("decision_audit_ready_to_apply", ["decision-audit", "--status", "ready_to_apply", "--limit", "5"]),
    ("apply_preview_summary", ["apply-preview", "--record-type", "summary", "--limit", "5"]),
    ("input_validation_pass", ["input-validation", "--status", "pass", "--limit", "5"]),
    ("progress_overall", ["progress", "--scope-type", "overall", "--limit", "5"]),
    ("field_checks_first", ["field-checks", "--session-id", "review_session_001", "--limit", "5"]),
    ("source_matrix_rfc4271", ["source-matrix", "--source-id", "rfc4271", "--limit", "5"]),
    ("task_board_sessions", ["task-board", "--type", "review_session", "--limit", "5"]),
    ("handoff_sessions", ["handoff", "--type", "review_session", "--limit", "5"]),
    ("search_entities_rpki", ["search-entities", "RPKI", "--limit", "5"]),
    ("search_chunks_route_leak", ["search-chunks", '"route leak"', "--limit", "5"]),
]


def run_example(args):
    result = subprocess.run(
        [sys.executable, "-m", QUERY_MODULE, *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    parsed = None
    if result.stdout.strip():
        parsed = json.loads(result.stdout)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "parsed": parsed,
    }


def list_len(value, key):
    if isinstance(value, dict) and isinstance(value.get(key), list):
        return len(value[key])
    return 0


def validate_result(name, parsed):
    if name == "stats":
        return (
            isinstance(parsed, dict)
            and parsed.get("integrity_check") == "ok"
            and parsed.get("entities", 0) > 0
            and parsed.get("chunks", 0) > 0
        )
    if name == "term_route":
        return (
            isinstance(parsed, dict)
            and parsed.get("term") == "route"
            and list_len(parsed, "entities") > 0
            and list_len(parsed, "chunks") > 0
        )
    if name == "entity_route_leak":
        return isinstance(parsed, dict) and parsed.get("entity_id") == "anomaly_route_leak"
    if name == "neighbors_as_path":
        return isinstance(parsed, dict) and (
            list_len(parsed, "incoming") > 0 or list_len(parsed, "outgoing") > 0
        )
    if name == "source_rfc4271":
        return (
            isinstance(parsed, dict)
            and parsed.get("source_id") == "rfc4271"
            and list_len(parsed, "entities") > 0
            and list_len(parsed, "chunks") > 0
        )
    if name == "evidence_route_leak":
        return isinstance(parsed, dict) and parsed.get("entity_id") == "anomaly_route_leak" and list_len(parsed, "records") > 0
    if name == "review_packets_ready":
        return (
            isinstance(parsed, list)
            and len(parsed) > 0
            and all(item.get("review_bucket") == "ready_without_manual_note" for item in parsed)
        )
    if name == "workbook_first_batch":
        return (
            isinstance(parsed, list)
            and len(parsed) > 0
            and all(item.get("review_batch") == "01_ready_without_manual_note" for item in parsed)
        )
    if name == "extracts_route_leak":
        return isinstance(parsed, dict) and parsed.get("entity_id") == "anomaly_route_leak" and list_len(parsed, "records") > 0
    if name == "sessions_first":
        return (
            isinstance(parsed, list)
            and len(parsed) > 0
            and all(item.get("session_id") == "review_session_001" for item in parsed)
        )
    if name == "actions_open":
        return isinstance(parsed, list) and len(parsed) > 0 and all(item.get("status") == "open" for item in parsed)
    if name == "actions_llm_skipped":
        return isinstance(parsed, list) and len(parsed) > 0 and all(item.get("needs_llm") == 1 for item in parsed)
    if name == "observations_asn":
        return isinstance(parsed, list) and len(parsed) > 0 and all(item.get("observation_type") == "asn" for item in parsed)
    if name == "glossary_route":
        return isinstance(parsed, list) and len(parsed) > 0
    if name == "decision_audit_ready_to_apply":
        return isinstance(parsed, list) and len(parsed) > 0 and all(item.get("application_status") == "ready_to_apply" for item in parsed)
    if name == "apply_preview_summary":
        return (
            isinstance(parsed, list)
            and len(parsed) == 1
            and parsed[0].get("record_type") == "summary"
            and parsed[0].get("run_mode") == "dry_run"
        )
    if name == "input_validation_pass":
        return isinstance(parsed, list) and len(parsed) > 0 and all(item.get("status") == "pass" for item in parsed)
    if name == "progress_overall":
        return (
            isinstance(parsed, list)
            and len(parsed) == 1
            and parsed[0].get("scope_type") == "overall"
            and parsed[0].get("scope_value") == "all"
        )
    if name == "field_checks_first":
        return (
            isinstance(parsed, list)
            and len(parsed) > 0
            and all(item.get("session_id") == "review_session_001" for item in parsed)
        )
    if name == "source_matrix_rfc4271":
        return (
            isinstance(parsed, list)
            and len(parsed) == 1
            and parsed[0].get("source_id") == "rfc4271"
        )
    if name == "task_board_sessions":
        return isinstance(parsed, list) and len(parsed) > 0 and all(item.get("task_type") == "review_session" for item in parsed)
    if name == "handoff_sessions":
        return isinstance(parsed, list) and len(parsed) > 0 and all(item.get("task_type") == "review_session" for item in parsed)
    if name == "search_entities_rpki":
        return isinstance(parsed, list) and len(parsed) > 0
    if name == "search_chunks_route_leak":
        return isinstance(parsed, list) and len(parsed) > 0
    return False


def summarize_payload(parsed):
    if isinstance(parsed, list):
        return f"{len(parsed)} records"
    if not isinstance(parsed, dict):
        return "no structured payload"
    keys = []
    for key in ("entity_id", "source_id", "term"):
        if key in parsed:
            keys.append(f"{key}={parsed[key]}")
    for key in ("entities", "sources", "chunks", "incoming", "outgoing"):
        if isinstance(parsed.get(key), list):
            keys.append(f"{key}={len(parsed[key])}")
    for key in ("records",):
        if isinstance(parsed.get(key), list):
            keys.append(f"{key}={len(parsed[key])}")
    if "integrity_check" in parsed:
        keys.append(f"integrity_check={parsed['integrity_check']}")
    return ", ".join(keys) if keys else f"{len(parsed)} keys"


def database_integrity():
    conn = sqlite3.connect(DB_PATH)
    try:
        return conn.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        conn.close()


def main():
    rows = []
    failures = []
    for name, args in EXAMPLES:
        result = run_example(args)
        ok = result["returncode"] == 0 and validate_result(name, result["parsed"])
        if not ok:
            failures.append(name)
        rows.append((name, args, ok, result))

    integrity = database_integrity()
    if integrity != "ok":
        failures.append("sqlite_integrity")

    lines = [
        "# 查询样例报告",
        "",
        "## 范围",
        "",
        "本报告运行 `python3 -m bgpkb.pipeline.query_knowledge_base` 的固定查询样例，验证 `data/published/bgp_knowledge_base.sqlite` 可被程序化查询。",
        "",
        "该步骤不联网、不下载、不调用 LLM、不做语义判断。",
        "",
        "## 摘要",
        "",
        f"- 查询样例数：{len(rows)}",
        f"- 通过数：{sum(1 for _, _, ok, _ in rows if ok)}",
        f"- 失败数：{len(failures)}",
        f"- SQLite integrity_check：{integrity}",
        "",
        "## 样例结果",
        "",
        "| 名称 | 命令 | 状态 | 摘要 |",
        "| --- | --- | --- | --- |",
    ]
    for name, args, ok, result in rows:
        command = paths.pipeline_command("query_knowledge_base.py", *args)
        status = "通过" if ok else f"失败({result['returncode']})"
        lines.append(f"| {name} | `{command}` | {status} | {summarize_payload(result['parsed'])} |")

    lines.extend(["", "## 输出节选", ""])
    for name, args, ok, result in rows:
        lines.extend([
            f"### {name}",
            "",
            "```json",
            result["stdout"][:2000],
            "```",
            "",
        ])
        if result["stderr"]:
            lines.extend(["标准错误：", "", "```text", result["stderr"], "```", ""])

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {paths.rel(REPORT)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
