import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
DEEPSEEK_RESULTS = paths.DATASETS_DIR / "deepseek_rag_answer_eval_results.jsonl"
FALLBACK_RESULTS = paths.DATASETS_DIR / "rag_answer_eval_results.jsonl"
REPORT_PATH = paths.report_path("rag_answer_failure_analysis_report")


def load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def select_source_path():
    return DEEPSEEK_RESULTS if DEEPSEEK_RESULTS.exists() else FALLBACK_RESULTS


def summarize_failures(rows):
    failed = [row for row in rows if row.get("decision") != "pass"]
    failed_check_counts = Counter()
    status_pairs = Counter()
    for row in rows:
        status_pairs[(row.get("expected_status", ""), row.get("answer_status", ""))] += 1
    for row in failed:
        failed_check_counts.update(row.get("failed_checks", []))
    return {
        "total": len(rows),
        "passed": len(rows) - len(failed),
        "failed": len(failed),
        "failed_check_counts": dict(sorted(failed_check_counts.items())),
        "status_pairs": {f"{expected}->{actual}": count for (expected, actual), count in sorted(status_pairs.items())},
    }


def render_report(rows, summary, source_path):
    lines = [
        "# 阶段 4.4 RAG 答案失败样本分析报告",
        "",
        "## 摘要",
        "",
        f"- 生成时间：{datetime.now().replace(microsecond=0).isoformat()}",
        f"- 输入文件：`{source_path}`",
        f"- 问题数：{summary['total']}",
        f"- 通过数：{summary['passed']}",
        f"- 失败数：{summary['failed']}",
        "- 密钥记录：未读取、未写入、未报告。",
        "",
        "## 失败检查分布",
        "",
    ]
    if summary["failed_check_counts"]:
        for key, count in summary["failed_check_counts"].items():
            lines.append(f"- {key}：{count}")
    else:
        lines.append("- 无失败检查。")
    lines.extend(["", "## 状态迁移分布", ""])
    for pair, count in summary["status_pairs"].items():
        lines.append(f"- {pair}：{count}")
    lines.extend(["", "## 失败样本", ""])
    failed = [row for row in rows if row.get("decision") != "pass"]
    if failed:
        for row in failed:
            lines.extend([
                f"### {row.get('question_id', '')}",
                "",
                f"- 查询：{row.get('query', '')}",
                f"- 预期状态：{row.get('expected_status', '')}",
                f"- 实际状态：{row.get('answer_status', '')}",
                f"- 失败检查：{', '.join(row.get('failed_checks', []))}",
                f"- 引用数：{row.get('citation_count', 0)}",
                "",
            ])
    else:
        lines.append("- 无失败样本。")
    lines.extend([
        "",
        "## 建议",
        "",
        "- 如果失败集中在 `must_have_terms_missing`，优先检查提示词和答案约束。",
        "- 如果失败集中在 `missing_citations`，优先检查检索召回和 context pack。",
        "- 如果失败集中在 `answer_status_mismatch`，优先检查无证据查询和检索阈值。",
    ])
    return "\n".join(lines).rstrip() + "\n"


def main():
    source_path = select_source_path()
    rows = load_jsonl(source_path)
    summary = summarize_failures(rows)
    REPORT_PATH.write_text(
        render_report(rows, summary, source_path.relative_to(ROOT).as_posix()),
        encoding="utf-8",
    )
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
