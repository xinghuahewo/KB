---
title: "阶段四：RAG 就绪框架 v1"
document_type: "阶段说明"
purpose: "记录当前设备不运行模型条件下交付的 RAG 框架、运行边界和验收标准。"
scope: "LLM 候选增强框架、离线 embedding/index 框架、retrieval API、context pack 和阶段验收"
status: "已交付"
last_reviewed: "2026-06-19"
---
# 阶段四：RAG 就绪框架 v1

## 1. 目标

本阶段先交付完整 RAG 框架，而不是在当前设备运行模型。默认流水线不下载 BGE-M3、不调用 DeepSeek、不启动 Milvus、不部署 Qwen/vLLM。

## 2. 交付物

- `config/rag_retrieval.yaml`
- `config/llm_candidate_enrichment.yaml`
- `scripts/build_llm_candidate_enrichment.py`
- `scripts/build_rag_indexes.py`
- `scripts/query_rag.py`
- `scripts/build_rag_readiness_report.py`
- `service/retrieval_framework.py`
- `reports/rag_readiness_report.md`
- `/api/v1/retrieval/search`
- `/api/v1/retrieval/evidence`
- `/api/v1/retrieval/context-pack`

## 3. 边界

- LLM 只生成 pending_review 候选，不修改主实体、关系、chunk 或 SQLite。
- DeepSeek、Qwen/vLLM、BGE-M3、Milvus 均为显式启用路径，默认禁用。
- 当前验收只证明框架、契约和离线 baseline 可用，不证明真实模型召回效果。
- 阶段四不生成自然语言答案，只生成可追溯 context pack。

## 4. 后续

在具备模型设备或远端服务后，可按同一 provider 契约启用：

1. DeepSeek API 候选增强。
2. BGE-M3 dense+sparse embedding。
3. Milvus Lite 或 Milvus Standalone hybrid search。
4. Qwen/vLLM OpenAI-compatible endpoint。
