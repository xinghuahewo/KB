# 阶段验收报告

## 结论

- 阶段：BGE-M3 混合检索 v1 (`phase_4_5_bge_m3_hybrid_retrieval_v1`)
- 结论：pass
- 验收模式：`deterministic_with_effect_review`
- 生成时间：2026-06-20T16:58:04

当前 KB 已具备可替换远程 BGE-M3 provider、可解释融合排序、可信来源边界和固定检索评测体系。

## 交付物验收

| 文件 | 状态 |
| --- | --- |
| `docs/stages/phase_4_5_bge_m3_hybrid_retrieval_v1.md` | 通过 |
| `config/rag_retrieval.yaml` | 通过 |
| `service/bge_m3_remote_client.py` | 通过 |
| `service/hybrid_retrieval.py` | 通过 |
| `scripts/build_bge_m3_index.py` | 通过 |
| `scripts/query_hybrid_rag.py` | 通过 |
| `scripts/run_hybrid_retrieval_eval.py` | 通过 |
| `published/bge_m3_embedding_manifest.json` | 通过 |
| `datasets/hybrid_retrieval_eval_questions.jsonl` | 通过 |
| `datasets/hybrid_retrieval_eval_results.jsonl` | 通过 |
| `reports/bge_m3_embedding_report.md` | 通过 |
| `reports/hybrid_retrieval_eval_report.md` | 通过 |
| `tests/test_bge_m3_remote_client.py` | 通过 |
| `tests/test_build_bge_m3_index.py` | 通过 |
| `tests/test_hybrid_retrieval.py` | 通过 |
| `tests/test_hybrid_retrieval_eval.py` | 通过 |

## 效果验收

### 新增能力

- 建立了 SiliconFlow 优先、阿里云 PAI/EAS 兼容的远程 BGE-M3 客户端。
- 建立了 chunk、entity、glossary、evidence template 四类数据的 embedding 文档和 manifest。
- 建立了关键词、向量、元数据意图和 RRF 的可解释混合检索。
- 建立了 20 题检索评测，覆盖 Recall@5、Recall@8、MRR、来源类型和无证据拒答。

### 使用者现在能做什么

- 无 API key 时离线验证完整框架和排序边界。
- 配置 SiliconFlow key 后构建真实 BGE-M3 文件化向量索引。
- 通过 CLI、API 和 RAG Answer 使用同一 hybrid context pack。

### 后续阶段能依赖什么

- 后续可在不改检索契约的情况下切换阿里云 PAI/EAS 或其它 OpenAI-compatible embedding 服务。
- 数据规模扩大后可把文件化向量索引替换为 Milvus 或 Qdrant。
- 阶段五可复用当前 source_ref、chunk_id、review_status 和排序解释做标准化出口。

## 证据验收

### 命令结果

| 命令 | 状态 | 摘要 |
| --- | --- | --- |
| `python3 scripts/build_bge_m3_index.py` | 通过 | {"dimension": 0, "error_code": "missing_api_key", "generated_at": "2026-06-20T08:58:02+00:00", "generated_by": "scripts/build_bge_m3_index.py", "input_count": 2269, "input_hash": "ab0c6754081e7fd042d9cc2349fdb06fe4612a085056edb973b50b06b9891c6d", "local_model_enabled": false, "model": "BAAI/bge-m3", "provider": "siliconflow_bge_m3", "real_model_execution": false, "source_counts": {"chunk": 2037, "entity": 112, "evidence_template": 8, "glossary": 112}, "status": "skipped"} |
| `python3 scripts/run_hybrid_retrieval_eval.py` | 通过 | {"failed": 0, "mrr": 0.6882352941176471, "no_evidence_rejection_rate": 1.0, "passed": 20, "recall_at_5": 0.8431372549019607, "recall_at_8": 0.872549019607843, "source_coverage": ["case_report", "data_doc", "paper", "standard", "tool_doc"], "total": 20} |
| `python3 -m pytest tests/test_embedding_provider.py tests/test_bge_m3_remote_client.py tests/test_build_bge_m3_index.py tests/test_hybrid_retrieval.py tests/test_hybrid_retrieval_eval.py tests/test_service_api.py -v` | 通过 | ============================== 29 passed in 0.73s ============================== |

### 报告检查

| 报告 | 状态 | 缺失项 |
| --- | --- | --- |
| `reports/bge_m3_embedding_report.md` | 通过 | 无 |
| `reports/hybrid_retrieval_eval_report.md` | 通过 | 无 |
| `reports/pipeline_report.md` | 通过 | 无 |
| `reports/quality_report.md` | 通过 | 无 |

## 风险与剩余人工事项

- 当前未配置 SiliconFlow key，真实 BGE-M3 向量效果仍待远程调用验证。
- pending chunk 只在已批准实体 evidence 或已确定性处理来源的可追溯边界内进入检索，不会被改写为 approved。

## 建议

- 可进入下一阶段；保留人工事项不阻塞阶段通过。
