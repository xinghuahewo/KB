#!/usr/bin/env python3
"""阶段 B chunking / retrieval 结构评测与可选答案基线对比。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from bgpkb import paths


RESULTS_PATH = paths.DATASETS_DIR / "chunking_eval_results.jsonl"
REPORT_PATH = paths.report_path("chunking_evaluation_report")


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 1.0


def evaluate_structure(chunks: list[dict[str, Any]], context_packs: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {chunk.get("chunk_id"): chunk for chunk in chunks if chunk.get("chunk_id")}
    resolved = [chunk for chunk in chunks if chunk.get("hierarchy_status") == "resolved"]
    traceable = [chunk for chunk in resolved if chunk.get("parent_section_id")]

    adjacent_checks = []
    for chunk in resolved:
        chunk_id = chunk.get("chunk_id")
        previous_id = chunk.get("previous_chunk_id")
        next_id = chunk.get("next_chunk_id")
        if previous_id:
            adjacent_checks.append(by_id.get(previous_id, {}).get("next_chunk_id") == chunk_id)
        if next_id:
            adjacent_checks.append(by_id.get(next_id, {}).get("previous_chunk_id") == chunk_id)

    citation_checks = []
    candidate_counts = []
    reranked_counts = []
    for pack in context_packs:
        if "candidate_chunk_count" in pack:
            candidate_counts.append(pack["candidate_chunk_count"])
        if "reranked_chunk_count" in pack:
            reranked_counts.append(pack["reranked_chunk_count"])
        for unit in pack.get("context_units", []):
            included = set(unit.get("included_chunk_ids", []))
            cited = {item.get("chunk_id") for item in unit.get("citations", [])}
            citation_checks.append(included <= cited)

    return {
        "total_chunks": len(chunks),
        "resolved_chunks": len(resolved),
        "resolved_coverage_rate": _rate(len(resolved), len(chunks)),
        "parent_traceability_rate": _rate(len(traceable), len(resolved)),
        "adjacent_context_correctness_rate": _rate(sum(1 for ok in adjacent_checks if ok), len(adjacent_checks)),
        "citation_completeness_rate": _rate(sum(1 for ok in citation_checks if ok), len(citation_checks)),
        "candidate_chunk_count_values": candidate_counts,
        "reranked_chunk_count_values": reranked_counts,
    }


def compare_answer_quality(current: list[dict[str, Any]], baseline: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if not baseline:
        return {
            "baseline_available": False,
            "structure_only_mode": True,
            "average_degradation_points": None,
            "critical_degradation_points": None,
            "passes_average_gate": True,
            "passes_critical_gate": True,
            "critical_question_ids": [],
        }
    baseline_by_id = {item["question_id"]: item for item in baseline}
    pairs = [
        (item, baseline_by_id[item["question_id"]])
        for item in current
        if item.get("question_id") in baseline_by_id
    ]
    degradations = [
        float(old.get("quality_score", 0.0)) - float(now.get("quality_score", 0.0))
        for now, old in pairs
    ]
    critical_pairs = [
        (now, old) for now, old in pairs
        if old.get("is_critical") is True or now.get("is_critical") is True
    ]
    critical_degradations = [
        float(old.get("quality_score", 0.0)) - float(now.get("quality_score", 0.0))
        for now, old in critical_pairs
    ]
    average = sum(degradations) / len(degradations) if degradations else 0.0
    critical = sum(critical_degradations) / len(critical_degradations) if critical_degradations else 0.0
    return {
        "baseline_available": True,
        "structure_only_mode": False,
        "average_degradation_points": average,
        "critical_degradation_points": critical,
        "passes_average_gate": average <= 0.03,
        "passes_critical_gate": critical <= 0.05,
        "critical_question_ids": [old["question_id"] for _now, old in critical_pairs],
    }


def render_report(structure: dict[str, Any], comparison: dict[str, Any]) -> str:
    lines = [
        "# 阶段 B Chunking / Retrieval 评测报告",
        "",
        "## 摘要",
        "",
        f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
        f"- resolved 覆盖率：{structure['resolved_coverage_rate']:.2%}",
        f"- 父 section 可追溯率：{structure['parent_traceability_rate']:.2%}",
        f"- 相邻上下文正确率：{structure['adjacent_context_correctness_rate']:.2%}",
        f"- 引用完整率：{structure['citation_completeness_rate']:.2%}",
        "",
        "## 答案质量基线",
        "",
    ]
    if comparison.get("structure_only_mode"):
        lines.append("- 无成熟答案基线；本轮 B 阶段只卡结构完整性。")
    else:
        lines.extend([
            f"- 平均答案质量退化：{comparison['average_degradation_points']:.2%}",
            f"- 关键问题答案质量退化：{comparison['critical_degradation_points']:.2%}",
            f"- 关键问题样本：{', '.join(comparison['critical_question_ids']) or '无'}",
        ])
    return "\n".join(lines).rstrip() + "\n"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_chunks() -> list[dict[str, Any]]:
    chunks = []
    for path in sorted((paths.CORPUS_DIR / "chunks_v2").glob("*.jsonl")):
        chunks.extend(_load_jsonl(path))
    if chunks:
        return chunks
    return _load_jsonl(paths.PUBLISHED_DIR / "chunk_catalog.jsonl")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def main():
    chunks = _load_chunks()
    context_packs = _load_jsonl(RESULTS_PATH)
    structure = evaluate_structure(chunks, context_packs)
    comparison = compare_answer_quality(context_packs, baseline=None)
    write_jsonl(RESULTS_PATH, [{"record_type": "summary", "structure": structure, "comparison": comparison}])
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_report(structure, comparison), encoding="utf-8")
    print(f"Wrote {RESULTS_PATH.relative_to(paths.PROJECT_ROOT)}")
    print(f"Wrote {REPORT_PATH.relative_to(paths.PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
