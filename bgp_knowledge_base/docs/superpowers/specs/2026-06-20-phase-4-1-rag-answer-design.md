---
title: "阶段 4.1 RAG Answer API 设计"
document_type: "阶段设计说明"
purpose: "定义在不运行本地模型的前提下，接入远程 LLM API、保留检索证据、输出可追溯答案的最小闭环。"
scope: "阶段 4.1"
status: "已批准"
last_reviewed: "2026-06-20"
---
# 阶段 4.1 RAG Answer API 设计

## 目标

阶段 4.1 把阶段四的离线检索框架推进到可调用的 RAG MVP：服务接收问题，先执行已发布知识库检索，再构造 context pack，最后在允许时调用 DeepSeek API 生成答案，并返回答案、引用、边界声明和生成元数据。

## 架构

新增能力保持只读服务边界：

1. `retrieval_framework` 继续负责检索、证据和 context pack。
2. `embedding_provider` 只提供 provider 抽象和配置校验；默认仍使用确定性 mock，不下载、不加载、不运行本地模型。
3. `llm_client` 只负责远程 DeepSeek 兼容接口调用、请求构造和错误归一化。
4. `rag_answer` 负责把检索结果、LLM 调用和失败兜底编排为 API 响应。
5. `service/app.py` 暴露 `POST /api/v1/rag/answer`，不提供写入接口。

## 数据流

```text
query -> retrieval_search -> context_pack -> citations
      -> guardrail check
      -> DeepSeek API 或 fallback
      -> answer payload
```

无论 LLM 是否可用，API 都必须返回检索证据。没有引用时不调用 LLM，直接返回 `answer_status=no_answer`。

## 约束与边界

- 当前设备不运行任何本地模型。
- 默认 embedding provider 为 `deterministic_mock`，只用于测试和索引占位。
- DeepSeek API key 只能从环境变量读取，不能写入仓库。
- LLM 输出不能覆盖 `entities/`、`relationships/`、`chunks/`、`published/` 或人工复核输入。
- 没有 citation 的回答必须拒绝生成。
- LLM 调用失败时返回检索证据和失败原因，不编造答案。
- 所有生成答案必须标记 `generated=true`，并保留 `model_provider`、`model`、`answer_status` 和 `guardrails`。
- 预留 Qwen 本地部署字段，但默认 `local_model_enabled=false`。

## 测试策略

- 使用 monkeypatch 替换 LLM 客户端，验证成功生成、无 key 兜底、无证据拒答。
- 验证 embedding provider 默认不运行本地模型。
- 验证 API 响应包含 answer、citations、context_pack、generated、guardrails。
- 验证 `.env.example` 和 README 记录运行边界。
