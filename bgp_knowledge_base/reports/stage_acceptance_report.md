# 阶段验收报告

## 结论

- 阶段：RAG 就绪框架 v1 (`phase_4_rag_framework_v1`)
- 结论：pass
- 验收模式：`deterministic_with_effect_review`
- 生成时间：2026-06-19T21:21:07

当前 KB 已具备不运行模型也可验收的 RAG 框架，真实 DeepSeek、Qwen/vLLM、BGE-M3 和 Milvus 路径保留为显式启用项。

## 交付物验收

| 文件 | 状态 |
| --- | --- |
| `docs/stages/phase_4_rag_framework_v1.md` | 通过 |
| `config/rag_retrieval.yaml` | 通过 |
| `config/llm_candidate_enrichment.yaml` | 通过 |
| `schemas/retrieval_result.schema.json` | 通过 |
| `schemas/context_pack.schema.json` | 通过 |
| `scripts/build_llm_candidate_enrichment.py` | 通过 |
| `scripts/build_rag_indexes.py` | 通过 |
| `scripts/query_rag.py` | 通过 |
| `scripts/build_rag_readiness_report.py` | 通过 |
| `published/embedding_manifest.json` | 通过 |
| `published/rag_mock_vector_index.jsonl` | 通过 |
| `published/rag_retrieval_index.json` | 通过 |
| `datasets/chunk_enrichment_candidates.jsonl` | 通过 |
| `datasets/entity_link_candidates.jsonl` | 通过 |
| `datasets/rag_query_eval.jsonl` | 通过 |
| `reports/rag_readiness_report.md` | 通过 |
| `tests/test_rag_framework_config.py` | 通过 |
| `tests/test_llm_candidate_enrichment.py` | 通过 |
| `tests/test_rag_indexes.py` | 通过 |
| `tests/test_rag_retrieval.py` | 通过 |

## 效果验收

### 新增能力

- 建立了 RAG provider 配置与运行边界，默认离线 mock，真实 provider 默认禁用。
- 建立了 LLM 候选增强、mock embedding、检索索引、context pack 和 CLI/API 入口。
- 建立了 route leak 和中文路由泄露等查询验收记录。
- 将 RAG 框架纳入确定性流水线、数据管理和阶段验收。

### 使用者现在能做什么

- 在当前设备不下载模型、不调用 API 的前提下运行 RAG 框架测试。
- 通过 retrieval API 获取可追溯 search、evidence 和 context pack。
- 后续在模型设备上用配置显式启用 DeepSeek、Qwen/vLLM、BGE-M3 或 Milvus。

### 后续阶段能依赖什么

- 阶段四真实模型评估可以复用同一 provider 与 context pack 契约。
- 阶段五标准出口可以复用 RAG 返回的稳定 @id 和 citation 结构。
- 后续问答系统可以基于 context pack 接入答案生成，但阶段四不直接生成答案。

## 证据验收

### 命令结果

| 命令 | 状态 | 摘要 |
| --- | --- | --- |
| `python3 scripts/build_llm_candidate_enrichment.py` | 通过 | Provider: mock; candidates require human review; primary entities unchanged |
| `python3 scripts/build_rag_indexes.py` | 通过 | Wrote published/rag_retrieval_index.json |
| `python3 scripts/build_rag_readiness_report.py` | 通过 | Wrote datasets/rag_query_eval.jsonl |
| `python3 -m pytest tests/test_rag_framework_config.py tests/test_llm_candidate_enrichment.py tests/test_rag_indexes.py tests/test_rag_retrieval.py tests/test_rag_readiness_report.py -v` | 通过 | ============================== 10 passed in 0.60s ============================== |
| `python3 -m pytest tests/test_service_api.py::test_retrieval_api_returns_traceable_search_evidence_and_context_pack -v` | 通过 | ============================== 1 passed in 0.25s =============================== |

### 报告检查

| 报告 | 状态 | 缺失项 |
| --- | --- | --- |
| `reports/rag_readiness_report.md` | 通过 | 无 |
| `reports/pipeline_report.md` | 通过 | 无 |
| `reports/quality_report.md` | 通过 | 无 |

## 风险与剩余人工事项

- 当前阶段只验收框架，不验收 BGE-M3/Milvus/DeepSeek 的真实召回效果。
- LLM 候选仍需人工复核后才能进入主实体或关系。

## 建议

- 可进入下一阶段；保留人工事项不阻塞阶段通过。
