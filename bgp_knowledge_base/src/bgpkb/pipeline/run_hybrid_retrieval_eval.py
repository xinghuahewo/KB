#!/usr/bin/env python3
import json
from datetime import datetime

from bgpkb import paths
from bgpkb.service import hybrid_retrieval


QUESTIONS_PATH = paths.DATASETS_DIR / "hybrid_retrieval_eval_questions.jsonl"
RESULTS_PATH = paths.DATASETS_DIR / "hybrid_retrieval_eval_results.jsonl"
REPORT_PATH = paths.GENERATED_REPORTS_DIR / "rag" / "hybrid_retrieval_eval_report.md"


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _matched_refs(expected_refs, results, limit):
    matched = []
    for expected in expected_refs:
        if any(expected in item.get("source_ref", "") for item in results[:limit]):
            matched.append(expected)
    return matched


def _reciprocal_rank(expected_refs, results):
    for rank, item in enumerate(results, start=1):
        if any(expected in item.get("source_ref", "") for expected in expected_refs):
            return 1.0 / rank
    return 0.0


def evaluate(questions=None, search_fn=None):
    selected = questions if questions is not None else load_jsonl(QUESTIONS_PATH)
    active_search = search_fn or hybrid_retrieval.search
    rows = []
    for question in selected:
        payload = active_search(question["query"], limit=8)
        results = payload.get("results", [])
        expected_refs = question.get("expected_source_refs", [])
        matched_5 = _matched_refs(expected_refs, results, 5)
        matched_8 = _matched_refs(expected_refs, results, 8)
        expected_status = question["expected_status"]
        if expected_status == "no_evidence":
            passed = not results
        else:
            passed = bool(matched_8)
        rows.append({
            "question_id": question["question_id"],
            "query": question["query"],
            "expected_status": expected_status,
            "decision": "pass" if passed else "fail",
            "result_count": len(results),
            "recall_at_5": len(matched_5) / len(expected_refs) if expected_refs else 1.0,
            "recall_at_8": len(matched_8) / len(expected_refs) if expected_refs else 1.0,
            "reciprocal_rank": _reciprocal_rank(expected_refs, results),
            "expected_source_refs": expected_refs,
            "matched_source_refs_at_5": matched_5,
            "matched_source_refs_at_8": matched_8,
            "returned_source_refs": [item.get("source_ref", "") for item in results],
            "returned_source_types": sorted({item.get("source_type", "") for item in results if item.get("source_type")}),
            "returned_chunk_ids": [item.get("chunk_id", "") for item in results],
            "vector_status": payload.get("vector_status", ""),
            "normalized_query": payload.get("normalized_query", question["query"]),
            "notes": question.get("notes", ""),
        })
    return rows


def summarize(results):
    evidence = [item for item in results if item["expected_status"] == "evidence"]
    no_evidence = [item for item in results if item["expected_status"] == "no_evidence"]
    source_types = sorted({source_type for item in results for source_type in item["returned_source_types"]})
    return {
        "total": len(results),
        "passed": sum(item["decision"] == "pass" for item in results),
        "failed": sum(item["decision"] == "fail" for item in results),
        "recall_at_5": sum(item["recall_at_5"] for item in evidence) / len(evidence) if evidence else 1.0,
        "recall_at_8": sum(item["recall_at_8"] for item in evidence) / len(evidence) if evidence else 1.0,
        "mrr": sum(item["reciprocal_rank"] for item in evidence) / len(evidence) if evidence else 1.0,
        "no_evidence_rejection_rate": (
            sum(item["decision"] == "pass" for item in no_evidence) / len(no_evidence)
            if no_evidence else 1.0
        ),
        "source_coverage": source_types,
    }


def render_report(results):
    summary = summarize(results)
    lines = [
        "# 阶段 4.5 混合检索评测报告",
        "",
        "## 摘要",
        "",
        f"- 生成时间：{datetime.now().replace(microsecond=0).isoformat()}",
        f"- 问题数：{summary['total']}",
        f"- 通过数：{summary['passed']}",
        f"- 失败数：{summary['failed']}",
        f"- Recall@5：{summary['recall_at_5']:.2%}",
        f"- Recall@8：{summary['recall_at_8']:.2%}",
        f"- MRR：{summary['mrr']:.4f}",
        f"- 无证据拒答率：{summary['no_evidence_rejection_rate']:.2%}",
        f"- 来源类型覆盖：{', '.join(summary['source_coverage'])}",
        "- 当前设备未运行本地模型。",
        "- 评测不写回实体、关系、chunk 或复核状态。",
        "",
        "## 逐题结果",
        "",
        "| ID | 查询 | 预期 | 结论 | Recall@5 | Recall@8 | RR | 向量状态 |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for item in results:
        lines.append(
            f"| {item['question_id']} | {item['query']} | {item['expected_status']} | {item['decision']} | "
            f"{item['recall_at_5']:.2f} | {item['recall_at_8']:.2f} | {item['reciprocal_rank']:.4f} | "
            f"{item['vector_status']} |"
        )
    lines.extend(["", "## 失败与人工复核", ""])
    failures = [item for item in results if item["decision"] == "fail"]
    if failures:
        for item in failures:
            lines.append(
                f"- `{item['question_id']}`：预期来源 {item['expected_source_refs']}，"
                f"实际前 8 来源 {item['returned_source_refs']}。"
            )
    else:
        lines.append("- 无。")
    return "\n".join(lines).rstrip() + "\n"


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main():
    results = evaluate()
    write_jsonl(RESULTS_PATH, results)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_report(results), encoding="utf-8")
    print(json.dumps(summarize(results), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
