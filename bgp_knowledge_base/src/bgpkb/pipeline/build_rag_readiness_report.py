#!/usr/bin/env python3
import json
import sys
from collections import Counter
from pathlib import Path

from bgpkb import paths

import yaml


ROOT = paths.PROJECT_ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgpkb.service import retrieval_framework


RAG_CONFIG = paths.CONFIG_DIR / "rag_retrieval.yaml"
LLM_CONFIG = paths.CONFIG_DIR / "llm_candidate_enrichment.yaml"
REPORT = paths.report_path("rag_readiness_report")
EVAL = paths.DATASETS_DIR / "rag_query_eval.jsonl"


QUERIES = ["route leak", "路由泄露", "prefix hijack", "RPKI invalid", "AS_PATH", "MOAS"]


def load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def build_eval_records():
    records = []
    for query in QUERIES:
        results = retrieval_framework.search(query, limit=5)
        records.append({
            "query": query,
            "normalized_query": retrieval_framework.normalize_query(query),
            "result_count": len(results),
            "top_chunk_ids": [item["chunk_id"] for item in results[:5]],
            "has_traceable_result": all(item.get("@id") and item.get("source_ref") for item in results),
            "generated_by": "src/bgpkb/pipeline/build_rag_readiness_report.py",
        })
    return records


def main():
    rag = load_yaml(RAG_CONFIG)
    llm = load_yaml(LLM_CONFIG)
    eval_records = build_eval_records()
    write_jsonl(EVAL, eval_records)

    manifest = retrieval_framework.load_json(paths.PUBLISHED_DIR / "embedding_manifest.json", default={})
    retrieval_index = retrieval_framework.load_json(paths.PUBLISHED_DIR / "rag_retrieval_index.json", default={})
    vector_store = retrieval_index.get("vector_store", {})
    counts = Counter("pass" if row["result_count"] > 0 and row["has_traceable_result"] else "fail" for row in eval_records)

    lines = [
        "# RAG 就绪框架报告",
        "",
        "## 范围",
        "",
        "本报告验收阶段四在当前设备不运行模型条件下的完整 RAG 框架。默认路径不下载 BGE-M3、不调用 DeepSeek、不启动 Milvus、不部署 Qwen/vLLM。",
        "",
        "## Provider 与运行边界",
        "",
        f"- 当前模式：`{rag['default_mode']}`",
        f"- LLM 默认 provider：`{llm['default_provider']}`",
        f"- DeepSeek：已预留 OpenAI-compatible provider，默认启用：{llm['providers']['deepseek']['enabled']}。",
        f"- Qwen/vLLM：已预留 OpenAI-compatible provider，默认启用：{llm['providers']['qwen_vllm']['enabled']}。",
        f"- Embedding 默认 provider：`{rag['embedding']['default_provider']}`。",
        f"- BGE-M3：模型 `{rag['embedding']['providers']['bge_m3']['model']}`，默认启用：{rag['embedding']['providers']['bge_m3']['enabled']}。",
        f"- BGE-M3 ColBERT/multi-vector 默认启用：{rag['embedding']['providers']['bge_m3']['outputs']['colbert']}。",
        f"- Vector store 默认 provider：`{rag['vector_store']['default_provider']}`。",
        f"- Milvus Lite 默认启用：{rag['vector_store']['providers']['milvus_lite']['enabled']}。",
        "",
        "## RAG 索引覆盖",
        "",
        f"- Embedding manifest：`data/published/embedding_manifest.json`",
        f"- Embedding 输入数：{manifest.get('input_count', 0)}",
        f"- 真实模型执行：{manifest.get('real_model_execution', False)}",
        f"- Vector store：{vector_store.get('provider', '未生成')}",
        f"- SQLite FTS5 兜底：{rag['lexical_fallback']['enabled']}",
        "",
        "## 默认可信集合",
        "",
        f"- 允许 lifecycle_status：{', '.join(rag['trusted_collection']['lifecycle_status'])}",
        f"- 排除 lifecycle_status：{', '.join(rag['trusted_collection']['exclude_lifecycle_status'])}",
        f"- 排除 semantic blocker：{rag['trusted_collection']['exclude_semantic_blocker']}",
        "",
        "## 查询验收",
        "",
        f"- 查询数：{len(eval_records)}",
        f"- 通过数：{counts.get('pass', 0)}",
        f"- 失败数：{counts.get('fail', 0)}",
        "",
        "| 查询 | 规范化查询 | 结果数 | Top chunks |",
        "| --- | --- | ---: | --- |",
    ]
    for record in eval_records:
        lines.append(
            f"| `{record['query']}` | `{record['normalized_query']}` | {record['result_count']} | {', '.join(record['top_chunk_ids'][:3])} |"
        )

    lines.extend([
        "",
        "## Context Pack",
        "",
        "- 输出固定为 JSON context pack，不生成自然语言最终答案。",
        "- 每条结果必须带 `@id`、`chunk_id`、`source_ref`、`review_status` 和 `retrieval_method`。",
        "- 策略排除实体进入 `excluded_by_policy`。",
        "",
        "## LLM 候选边界",
        "",
        "- 候选只写入 `data/derived/datasets/*_candidates.jsonl`。",
        "- 默认状态为 `pending_review`。",
        "- 不改写主实体、关系、chunk 或 SQLite 主库。",
        "",
        "## 安全与成本边界",
        "",
        "- 不在日志、报告或 published 产物中写入 API key。",
        "- 当前设备不运行模型，不执行真实 DeepSeek/BGE-M3/Milvus/Qwen 路径。",
        "- 真实 provider 只在显式配置启用并满足依赖时执行。",
        "",
        "## API 入口",
        "",
        "- `/api/v1/retrieval/search`",
        "- `/api/v1/retrieval/evidence`",
        "- `/api/v1/retrieval/context-pack`",
        "",
    ])
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Wrote {EVAL.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
