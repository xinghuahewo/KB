# 阶段 4.1 RAG Answer API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个不运行本地模型、可接入 DeepSeek API、失败时保留检索证据的 RAG Answer API。

**Architecture:** 维持现有 FastAPI 只读服务结构。检索仍由 `retrieval_framework` 负责，新增 `llm_client`、`embedding_provider`、`rag_answer` 三个小模块；API 层只做参数接收和响应返回。

**Tech Stack:** Python 3、FastAPI、标准库 `urllib.request`、pytest、GitHub Actions。

---

### Task 1: 配置与 provider 边界

**Files:**
- Modify: `bgp_knowledge_base/config/rag_retrieval.yaml`
- Create: `bgp_knowledge_base/service/embedding_provider.py`
- Test: `bgp_knowledge_base/tests/test_embedding_provider.py`

- [ ] 写失败测试：默认 provider 不运行本地模型，Qwen 预留但禁用。
- [ ] 运行单测确认失败。
- [ ] 实现 provider 配置读取和边界校验。
- [ ] 运行单测确认通过。

### Task 2: DeepSeek LLM 客户端

**Files:**
- Create: `bgp_knowledge_base/service/llm_client.py`
- Test: `bgp_knowledge_base/tests/test_llm_client.py`

- [ ] 写失败测试：无 API key 返回不可用；有 API key 时生成 OpenAI-compatible 请求。
- [ ] 运行单测确认失败。
- [ ] 实现 DeepSeek 客户端、请求 payload 构造和错误归一化。
- [ ] 运行单测确认通过。

### Task 3: RAG Answer 编排

**Files:**
- Create: `bgp_knowledge_base/service/rag_answer.py`
- Modify: `bgp_knowledge_base/service/repository.py`
- Test: `bgp_knowledge_base/tests/test_rag_answer.py`

- [ ] 写失败测试：成功答案带 citation；无证据拒答；LLM 不可用时返回 fallback。
- [ ] 运行单测确认失败。
- [ ] 实现 answer 编排和 guardrails。
- [ ] 运行单测确认通过。

### Task 4: FastAPI 入口与文档

**Files:**
- Modify: `bgp_knowledge_base/service/app.py`
- Modify: `bgp_knowledge_base/README.md`
- Create: `bgp_knowledge_base/.env.example`
- Test: `bgp_knowledge_base/tests/test_service_api.py`

- [ ] 写失败测试：`POST /api/v1/rag/answer` 返回可追溯响应。
- [ ] 运行单测确认失败。
- [ ] 实现 API endpoint，补 README 和 `.env.example`。
- [ ] 运行单测确认通过。

### Task 5: CI 与总验证

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] 新增 GitHub Actions，运行 pytest、pipeline、阶段验收和质量检查。
- [ ] 运行 `python3 -m pytest -v`。
- [ ] 运行 `python3 scripts/run_stage_acceptance.py --stage phase_4_rag_framework_v1`。
- [ ] 运行 `python3 scripts/build_artifact_manifest.py && python3 scripts/quality_check.py`。
