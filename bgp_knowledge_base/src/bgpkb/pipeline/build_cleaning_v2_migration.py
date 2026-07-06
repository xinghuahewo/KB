#!/usr/bin/env python3
"""派生清洗 v2 语料并生成全量迁移差异报告。"""

import argparse
import json
import os
from pathlib import Path
import tempfile

import jsonschema

from bgpkb import paths
from bgpkb.cleaning_v2.contracts import atomic_write_json
from bgpkb.cleaning_v2.derivation import (
    build_derivatives,
    compare_v1_v2,
    evaluate_migration_gates,
    publish_derivatives,
)


DEFAULT_AUTHORITY = paths.CORPUS_DIR / "cleaned_blocks_v2"
DEFAULT_RUN = paths.DATASETS_DIR / "cleaning_runs_v2" / "full-54-v2-resolved"
DEFAULT_PARSED = paths.CORPUS_DIR / "parsed_v2"
DEFAULT_MARKDOWN = paths.CORPUS_DIR / "markdown_v2"
DEFAULT_ASSETS = paths.CORPUS_DIR / "assets_v2"
DEFAULT_CHUNKS = paths.CORPUS_DIR / "chunks_v2"
DEFAULT_DATASET = paths.DATASETS_DIR / "cleaning_v2_migration_diff.jsonl"
DEFAULT_REPORT = paths.GENERATED_REPORTS_DIR / "corpus" / "cleaning_v2_migration_report.md"
DEFAULT_DECISIONS = paths.REVIEW_INPUTS_DIR / "cleaning_v2_migration_decisions.jsonl"
DEFAULT_SECTION_CATALOG = paths.DATASETS_DIR / "section_catalog.jsonl"


def _atomic_text(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def _load_jsonl(path):
    if not Path(path).is_file():
        return []
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _chunks_by_doc(root):
    result = {}
    root = Path(root)
    if not root.exists():
        return result
    for path in sorted(root.rglob("*.jsonl")):
        for row in _load_jsonl(path):
            result.setdefault(row.get("doc_id", ""), []).append(row)
    return result


def _v1_markdown_path(root, doc_id):
    root = Path(root)
    if doc_id == "context_2026":
        override = root / "notes" / "context_summary.md"
        if override.is_file():
            return override
    matches = sorted(root.rglob(f"{doc_id}.md")) if root.exists() else []
    return matches[0] if matches else None


def _write_jsonl(path, rows):
    content = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )
    _atomic_text(path, content)


def _validate_hierarchy(sections, chunks):
    schema = json.loads((paths.SCHEMAS_DIR / "section_catalog.schema.json").read_text(encoding="utf-8"))
    chunk_by_id = {}
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        if chunk_id in chunk_by_id:
            raise ValueError(f"重复 chunk_id: {chunk_id}")
        chunk_by_id[chunk_id] = chunk
    by_doc = {}
    section_by_id = {}
    for section in sections:
        jsonschema.validate(section, schema)
        section_id = section["section_id"]
        if section_id in section_by_id:
            raise ValueError(f"重复 section_id: {section_id}")
        section_by_id[section_id] = section
        by_doc.setdefault(section["doc_id"], []).append(section)
    for chunk_id, chunk in chunk_by_id.items():
        parent_id = chunk.get("parent_section_id")
        if not parent_id:
            raise ValueError(f"chunk 缺少 parent_section_id: {chunk_id}")
        parent = section_by_id.get(parent_id)
        if parent is None:
            raise ValueError(f"chunk parent section 不存在: {chunk_id} -> {parent_id}")
        if parent["doc_id"] != chunk.get("doc_id"):
            raise ValueError(f"chunk 与 parent section 跨文档: {chunk_id} -> {parent_id}")
        if chunk_id not in parent["child_chunk_ids"]:
            raise ValueError(f"parent section 未收录 chunk: {parent_id} -> {chunk_id}")
    for doc_id, doc_sections in by_doc.items():
        ordered = sorted(doc_sections, key=lambda row: (row["section_order"], row["section_id"]))
        ids = {row["section_id"] for row in ordered}
        for index, section in enumerate(ordered):
            expected_previous = ordered[index - 1]["section_id"] if index else None
            expected_next = ordered[index + 1]["section_id"] if index + 1 < len(ordered) else None
            if section["previous_section_id"] != expected_previous or section["next_section_id"] != expected_next:
                raise ValueError(f"section 邻接不连续: {section['section_id']}")
            if any(child not in ids for child in section["child_section_ids"]):
                raise ValueError(f"section 子级引用不存在: {section['section_id']}")
            for chunk_id in section["child_chunk_ids"]:
                chunk = chunk_by_id.get(chunk_id)
                if not chunk or chunk.get("doc_id") != doc_id or chunk.get("parent_section_id") != section["section_id"]:
                    raise ValueError(f"section/chunk 引用不一致: {section['section_id']} -> {chunk_id}")


def build_migration(
    *, authority_root, run_dir, v1_markdown_root, v1_chunks_root,
    parsed_root, markdown_root, assets_root, chunks_root, dataset_path,
    report_path, section_catalog_path=DEFAULT_SECTION_CATALOG,
    expected_document_count=54, decisions_path=None,
):
    authority_root = Path(authority_root)
    run_dir = Path(run_dir)
    statuses = _load_jsonl(run_dir / "document_status.jsonl")
    v1_chunks = _chunks_by_doc(v1_chunks_root)
    decisions = {
        row["doc_id"]: row for row in _load_jsonl(decisions_path)
    } if decisions_path else {}
    records = []
    sections = []
    chunks = []

    for status in sorted(statuses, key=lambda row: row["doc_id"]):
        doc_id = status["doc_id"]
        authority_dir = authority_root / doc_id
        evidence_dir = authority_dir if status["state"] == "approved" else run_dir / "work" / doc_id
        parsed_path = evidence_dir / "parsed_document.json"
        if parsed_path.is_file():
            atomic_write_json(Path(parsed_root) / f"{doc_id}.json", json.loads(parsed_path.read_text(encoding="utf-8")))
        if status["state"] != "approved":
            records.append(
                {
                    "doc_id": doc_id, "state": status["state"], "parser_mode": "fallback" if status.get("output_summary", {}).get("fallback_used") else "unknown",
                    "content_digest": None, "stable": None, "diff": None,
                    "gate_passed": False, "blocking_issues": ["quarantined_document"],
                    "review_item_count": 0,
                }
            )
            continue

        document = json.loads((authority_dir / "cleaned_document.json").read_text(encoding="utf-8"))
        first = build_derivatives(document)
        repeated = build_derivatives(document)
        published = publish_derivatives(
            document, markdown_root=markdown_root, assets_root=assets_root,
            chunks_root=chunks_root, asset_source_root=authority_dir,
        )
        sections.extend(published["sections"])
        chunks.extend(published["chunks"])
        v1_path = _v1_markdown_path(v1_markdown_root, doc_id)
        v1_markdown = v1_path.read_text(encoding="utf-8") if v1_path else ""
        diff = compare_v1_v2(
            v1_markdown, document, v1_chunks.get(doc_id, []), published["chunks"],
            document.get("transformations", []),
        )
        gate = evaluate_migration_gates(
            document, diff, current_digest=first["content_digest"],
            repeated_digest=repeated["content_digest"], minimum_coverage=0.995,
            migration_decision=decisions.get(doc_id),
        )
        records.append(
            {
                "doc_id": doc_id, "state": status["state"],
                "parser_mode": document.get("parser_mode", "unknown"),
                "content_digest": published["content_digest"],
                "stable": first["content_digest"] == repeated["content_digest"],
                "diff": diff, "gate_passed": gate["passed"],
                "blocking_issues": gate["blocking_issues"],
                "review_item_count": len(document.get("review_items", [])) + len(json.loads((authority_dir / "review_queue.json").read_text(encoding="utf-8"))) if (authority_dir / "review_queue.json").is_file() else 0,
                "migration_decision_id": decisions.get(doc_id, {}).get("decision_id"),
            }
        )

    sections.sort(key=lambda row: (row["doc_id"], row["section_order"], row["section_id"]))
    _validate_hierarchy(sections, chunks)
    _write_jsonl(section_catalog_path, sections)
    _write_jsonl(dataset_path, records)
    terminal_count = sum(row["state"] in {"approved", "quarantined"} for row in statuses)
    approved_count = sum(row["state"] == "approved" for row in statuses)
    quarantined_count = sum(row["state"] == "quarantined" for row in statuses)
    gate_pass_count = sum(row["gate_passed"] for row in records)
    resolved_chunk_count = sum(row.get("hierarchy_status") == "resolved" for row in chunks)
    unresolved_chunk_count = len(chunks) - resolved_chunk_count
    hierarchy_resolution_rate = resolved_chunk_count / len(chunks) if chunks else 1.0
    issue_counts = {}
    for row in records:
        for issue in row["blocking_issues"]:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
    report_lines = [
        "# Docling 清洗 v2 全量迁移报告", "", "## 批次结论", "",
        f"- 目标文档数：{expected_document_count}", f"- 终态文档数：{terminal_count}",
        f"- approved：{approved_count}", f"- quarantined：{quarantined_count}",
        f"- 逐文档迁移门禁通过：{gate_pass_count}/{len(records)}", "",
        "## 层级派生摘要", "",
        f"- section 数：{len(sections)}",
        f"- 已解析 chunk：{resolved_chunk_count}",
        f"- 未解析且排除检索 chunk：{unresolved_chunk_count}",
        f"- 层级解析率：{hierarchy_resolution_rate:.2%}", "",
        "## 阻断项汇总", "",
    ]
    if issue_counts:
        report_lines.extend(f"- `{key}`：{value} 篇" for key, value in sorted(issue_counts.items()))
    else:
        report_lines.append("- 无")
    report_lines.extend(["", "## 逐文档状态", ""])
    for row in records:
        issues = "、".join(row["blocking_issues"]) or "无"
        report_lines.append(f"- `{row['doc_id']}`：{row['state']}；门禁={'通过' if row['gate_passed'] else '阻断'}；问题={issues}")
    report_lines.append("")
    _atomic_text(report_path, "\n".join(report_lines))
    return {
        "expected_document_count": expected_document_count,
        "terminal_count": terminal_count,
        "approved_count": approved_count,
        "quarantined_count": quarantined_count,
        "gate_pass_count": gate_pass_count,
        "section_count": len(sections),
        "resolved_chunk_count": resolved_chunk_count,
        "unresolved_chunk_count": unresolved_chunk_count,
        "hierarchy_resolution_rate": hierarchy_resolution_rate,
        "records": records,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="生成清洗 v2 派生产物、差异数据集和中文迁移报告")
    parser.add_argument("--authority-root", type=Path, default=DEFAULT_AUTHORITY)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--v1-markdown-root", type=Path, default=paths.CLEANED_DIR)
    parser.add_argument("--v1-chunks-root", type=Path, default=paths.CHUNKS_DIR)
    parser.add_argument("--parsed-root", type=Path, default=DEFAULT_PARSED)
    parser.add_argument("--markdown-root", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--assets-root", type=Path, default=DEFAULT_ASSETS)
    parser.add_argument("--chunks-root", type=Path, default=DEFAULT_CHUNKS)
    parser.add_argument("--dataset-path", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--section-catalog-path", type=Path, default=DEFAULT_SECTION_CATALOG)
    parser.add_argument("--decisions-path", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--expected-document-count", type=int, default=54)
    args = parser.parse_args(argv)
    result = build_migration(**vars(args))
    print(json.dumps({key: value for key, value in result.items() if key != "records"}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
