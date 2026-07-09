import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgpkb.service import llm_client, rag_answer  # noqa: E402


REPORT_PATH = paths.report_path("rag_answer_smoke_test_report")
DATASET_PATH = paths.DATASETS_DIR / "rag_answer_smoke_test_results.jsonl"
DEFAULT_QUERIES = [
    "route leak",
    "路由泄露",
    "zzzzqqqxxxx",
]


def compact_payload(payload):
    return {
        "query": payload.get("query", ""),
        "answer_status": payload.get("answer_status", ""),
        "generated": payload.get("generated", False),
        "model_provider": payload.get("model_provider", ""),
        "model": payload.get("model", ""),
        "citation_count": len(payload.get("citations", [])),
        "result_count": len(payload.get("context_pack", {}).get("results", [])),
        "error_code": payload.get("error_code", ""),
        "guardrails": payload.get("guardrails", {}),
        "answer_preview": payload.get("answer", "")[:240],
        "citations": payload.get("citations", []),
    }


def run_smoke_tests(client=None, queries=None, limit=3):
    active_client = client or llm_client.DeepSeekClient.from_env()
    results = []
    for query in queries or DEFAULT_QUERIES:
        payload = rag_answer.answer_question(query, limit=limit, client=active_client)
        results.append(compact_payload(payload))
    return results


def render_report(results, api_key_configured):
    status_counts = {}
    for result in results:
        status_counts[result["answer_status"]] = status_counts.get(result["answer_status"], 0) + 1
    lines = [
        "# 阶段 4.2 DeepSeek 冒烟测试报告",
        "",
        "## 摘要",
        "",
        f"- 生成时间：{datetime.now().replace(microsecond=0).isoformat()}",
        f"- DeepSeek API key 配置：{'是' if api_key_configured else '否'}",
        "- 密钥记录：未写入报告、数据集或仓库。",
        f"- 查询数：{len(results)}",
        f"- 状态分布：{json.dumps(status_counts, ensure_ascii=False, sort_keys=True)}",
        "",
        "## 约束确认",
        "",
        "- 当前设备不运行本地模型。",
        "- 只读调用已发布知识库与 RAG Answer 编排。",
        "- 无引用证据时拒绝生成答案。",
        "- LLM 不可用时保留检索证据，不编造答案。",
        "- `DEEPSEEK_API_KEY` 只从环境变量读取。",
        "",
        "## 查询结果",
        "",
        "| 查询 | 状态 | generated | 引用数 | 命中数 | 错误码 |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for result in results:
        lines.append(
            "| {query} | {answer_status} | {generated} | {citation_count} | {result_count} | {error_code} |".format(
                query=result["query"],
                answer_status=result["answer_status"],
                generated="是" if result["generated"] else "否",
                citation_count=result["citation_count"],
                result_count=result["result_count"],
                error_code=result["error_code"] or "",
            )
        )
    lines.extend(["", "## 答案预览", ""])
    for result in results:
        lines.extend([
            f"### {result['query']}",
            "",
            f"- 状态：{result['answer_status']}",
            f"- 模型：{result['model_provider']} / {result['model']}",
            f"- 引用数：{result['citation_count']}",
            "",
            result["answer_preview"] or "无生成答案。",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run real DeepSeek smoke tests for RAG Answer API.")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--query", action="append", dest="queries")
    args = parser.parse_args()

    api_key_configured = bool(os.environ.get("DEEPSEEK_API_KEY"))
    results = run_smoke_tests(queries=args.queries, limit=args.limit)
    write_jsonl(DATASET_PATH, results)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_report(results, api_key_configured), encoding="utf-8")
    print(f"Wrote {DATASET_PATH.relative_to(ROOT)}")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
