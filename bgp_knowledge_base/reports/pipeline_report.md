# 确定性流水线报告

## 摘要

- 运行时间：2026-06-20T16:57:41
- 工作目录：`/Users/botongwu/.config/superpowers/worktrees/DB/phase-4-5-bge-m3-hybrid/bgp_knowledge_base`
- 步骤数：49
- 总体状态：通过

## 步骤结果

| 步骤 | 脚本 | 状态 | 耗时秒 |
| --- | --- | --- | ---: |
| 解析原始文档 | `scripts/parse_documents.py` | 通过 | 30.80 |
| 构建知识片段 | `scripts/build_chunks.py` | 通过 | 0.18 |
| 抽取案例观察值 | `scripts/extract_case_observations.py` | 通过 | 0.03 |
| 构建来源处理状态 | `scripts/build_source_processing_status.py` | 通过 | 0.03 |
| 构建来源缺口队列 | `scripts/build_source_gap_queue.py` | 通过 | 0.02 |
| 构建实体复核队列 | `scripts/build_entity_review_queue.py` | 通过 | 0.02 |
| 构建实体来源证据索引 | `scripts/build_entity_source_evidence.py` | 通过 | 0.32 |
| 构建实体人工复核包 | `scripts/build_entity_review_packets.py` | 通过 | 0.02 |
| 构建权威来源补充需求 | `scripts/build_authoritative_source_requirements.py` | 通过 | 0.02 |
| 构建下一步行动队列 | `scripts/build_next_action_queue.py` | 通过 | 0.02 |
| 构建 LLM 跳过记录 | `scripts/build_llm_processing_skip_report.py` | 通过 | 0.02 |
| 构建案例观察值复核指南 | `scripts/build_case_observation_guides.py` | 通过 | 0.02 |
| 构建人工复核工作簿 | `scripts/build_human_review_workbook.py` | 通过 | 0.02 |
| 构建人工复核决策输入模板 | `scripts/build_human_review_decision_template.py` | 通过 | 0.02 |
| 校验人工复核决策输入 | `scripts/build_human_review_input_validation.py` | 通过 | 0.02 |
| 审计人工复核决策 | `scripts/build_human_review_decision_audit.py` | 通过 | 0.02 |
| 预览人工复核决策应用 | `scripts/apply_human_review_decisions.py` | 通过 | 0.03 |
| 构建人工复核进度 | `scripts/build_human_review_progress.py` | 通过 | 0.02 |
| 构建人工复核证据摘录 | `scripts/build_human_review_evidence_extracts.py` | 通过 | 0.10 |
| 构建人工复核会话队列 | `scripts/build_human_review_session_queue.py` | 通过 | 0.03 |
| 构建人工复核会话状态 | `scripts/build_human_review_session_status.py` | 通过 | 0.02 |
| 构建人工复核逐字段清单 | `scripts/build_human_review_field_checklist.py` | 通过 | 0.03 |
| 构建人工复核来源矩阵 | `scripts/build_human_review_source_matrix.py` | 通过 | 0.02 |
| 构建人工复核任务板 | `scripts/build_human_review_task_board.py` | 通过 | 0.02 |
| 构建人工复核交接清单 | `scripts/build_human_review_handoff.py` | 通过 | 0.02 |
| 构建人工复核会话决策模板 | `scripts/build_human_review_session_decision_templates.py` | 通过 | 0.02 |
| 构建人工复核会话指南 | `scripts/build_human_review_session_guides.py` | 通过 | 0.03 |
| 构建人工复核指南 | `scripts/build_human_review_guides.py` | 通过 | 0.02 |
| 构建术语表 | `scripts/build_glossary.py` | 通过 | 0.02 |
| 构建发布知识库 | `scripts/build_published_knowledge_base.py` | 通过 | 0.09 |
| 构建语义标识前置层 | `scripts/build_semantic_identity.py` | 通过 | 0.06 |
| 构建 LLM 候选增强框架 | `scripts/build_llm_candidate_enrichment.py` | 通过 | 0.04 |
| 构建 RAG 检索索引框架 | `scripts/build_rag_indexes.py` | 通过 | 0.12 |
| 构建 BGE-M3 远程向量索引 | `scripts/build_bge_m3_index.py` | 通过 | 0.06 |
| 构建 SQLite 知识库 | `scripts/build_sqlite_knowledge_base.py` | 通过 | 0.17 |
| 构建查询样例报告 | `scripts/build_query_examples.py` | 通过 | 0.75 |
| 校验发布完整性 | `scripts/build_published_integrity_report.py` | 通过 | 0.07 |
| 构建知识库就绪度报告 | `scripts/build_readiness_report.py` | 通过 | 0.02 |
| 构建数据字典 | `scripts/build_data_dictionary.py` | 通过 | 0.77 |
| 构建覆盖报告 | `scripts/build_coverage_report.py` | 通过 | 0.07 |
| 构建数据管理能力报告 | `scripts/build_data_management_report.py` | 通过 | 0.04 |
| 构建生命周期治理报告 | `scripts/build_lifecycle_report.py` | 通过 | 0.03 |
| 构建语义质量治理报告 | `scripts/build_semantic_quality_report.py` | 通过 | 0.04 |
| 构建 RAG 就绪框架报告 | `scripts/build_rag_readiness_report.py` | 通过 | 0.24 |
| 运行 RAG 答案质量评测 | `scripts/run_rag_answer_eval.py` | 通过 | 1.22 |
| 运行混合检索评测 | `scripts/run_hybrid_retrieval_eval.py` | 通过 | 1.18 |
| 构建 RAG 答案失败样本分析 | `scripts/build_rag_answer_failure_analysis.py` | 通过 | 0.02 |
| 构建制品清单 | `scripts/build_artifact_manifest.py` | 通过 | 4.81 |
| 运行质量检查 | `scripts/quality_check.py` | 通过 | 4.80 |

## 输出详情

### 解析原始文档

- 脚本：`scripts/parse_documents.py`
- 返回码：0

标准输出：

```text
Parsed 53; skipped 0
Wrote reports/parse_report.md
```

标准错误：

无

### 构建知识片段

- 脚本：`scripts/build_chunks.py`
- 返回码：0

标准输出：

```text
bgp_chunks.jsonl: 890 chunks
case_chunks.jsonl: 89 chunks
paper_chunks.jsonl: 504 chunks
standard_chunks.jsonl: 554 chunks
```

标准错误：

无

### 抽取案例观察值

- 脚本：`scripts/extract_case_observations.py`
- 返回码：0

标准输出：

```text
Wrote datasets/case_observations.jsonl
Wrote datasets/case_observations.csv
Wrote reports/case_observation_report.md
```

标准错误：

无

### 构建来源处理状态

- 脚本：`scripts/build_source_processing_status.py`
- 返回码：0

标准输出：

```text
Wrote datasets/source_processing_status.jsonl
Wrote datasets/source_processing_status.csv
Wrote reports/source_processing_status_report.md
```

标准错误：

无

### 构建来源缺口队列

- 脚本：`scripts/build_source_gap_queue.py`
- 返回码：0

标准输出：

```text
Wrote datasets/source_gap_queue.jsonl
Wrote datasets/source_gap_queue.csv
Wrote reports/source_gap_queue_report.md
```

标准错误：

无

### 构建实体复核队列

- 脚本：`scripts/build_entity_review_queue.py`
- 返回码：0

标准输出：

```text
Wrote datasets/entity_review_queue.jsonl
Wrote datasets/entity_review_queue.csv
Wrote reports/entity_review_queue_report.md
```

标准错误：

无

### 构建实体来源证据索引

- 脚本：`scripts/build_entity_source_evidence.py`
- 返回码：0

标准输出：

```text
Wrote datasets/entity_source_evidence.jsonl
Wrote datasets/entity_source_evidence.csv
Wrote reports/entity_source_evidence_report.md
```

标准错误：

无

### 构建实体人工复核包

- 脚本：`scripts/build_entity_review_packets.py`
- 返回码：0

标准输出：

```text
Wrote datasets/entity_review_packets.jsonl
Wrote datasets/entity_review_packets.csv
Wrote reports/entity_review_packet_report.md
```

标准错误：

无

### 构建权威来源补充需求

- 脚本：`scripts/build_authoritative_source_requirements.py`
- 返回码：0

标准输出：

```text
Wrote datasets/authoritative_source_requirements.jsonl
Wrote datasets/authoritative_source_requirements.csv
Wrote reports/authoritative_source_requirements_report.md
```

标准错误：

无

### 构建下一步行动队列

- 脚本：`scripts/build_next_action_queue.py`
- 返回码：0

标准输出：

```text
Wrote datasets/next_action_queue.jsonl
Wrote datasets/next_action_queue.csv
Wrote reports/next_action_queue_report.md
```

标准错误：

无

### 构建 LLM 跳过记录

- 脚本：`scripts/build_llm_processing_skip_report.py`
- 返回码：0

标准输出：

```text
Wrote reports/llm_processing_skip_report.md
```

标准错误：

无

### 构建案例观察值复核指南

- 脚本：`scripts/build_case_observation_guides.py`
- 返回码：0

标准输出：

```text
Wrote reports/case_observation_guides/README.md
Wrote reports/case_observation_guides/aws_route53_crypto_hijack_2018.md
Wrote reports/case_observation_guides/cert_eu_china_telecom_route_leak_2019.md
Wrote reports/case_observation_guides/china_telecom_europe_route_leak_2019.md
Wrote reports/case_observation_guides/cloudflare_outage_2026.md
Wrote reports/case_observation_guides/cloudflare_verizon_route_leak_2019.md
Wrote reports/case_observation_guides/facebook_outage_cloudflare_2021.md
Wrote reports/case_observation_guides/facebook_outage_meta_2021.md
Wrote reports/case_observation_guides/fastly_rpki_hijack_2024.md
Wrote reports/case_observation_guides/indosat_route_leak_2014.md
Wrote reports/case_observation_guides/mainone_google_cloudflare_route_leak_2018.md
Wrote reports/case_observation_guides/manrs_bgp_2020_review.md
Wrote reports/case_observation_guides/manrs_regional_bgp_incidents_2020.md
Wrote reports/case_observation_guides/youtube_hijack_google_2008.md
```

标准错误：

无

### 构建人工复核工作簿

- 脚本：`scripts/build_human_review_workbook.py`
- 返回码：0

标准输出：

```text
Wrote datasets/human_review_workbook.jsonl
Wrote datasets/human_review_workbook.csv
Wrote reports/human_review_workbook_report.md
```

标准错误：

无

### 构建人工复核决策输入模板

- 脚本：`scripts/build_human_review_decision_template.py`
- 返回码：0

标准输出：

```text
Wrote review_inputs/human_review_decisions_template.csv
Checked review_inputs/human_review_decisions.csv
Wrote reports/human_review_decision_template_report.md
```

标准错误：

无

### 校验人工复核决策输入

- 脚本：`scripts/build_human_review_input_validation.py`
- 返回码：0

标准输出：

```text
Wrote datasets/human_review_input_validation.jsonl
Wrote datasets/human_review_input_validation.csv
Wrote reports/human_review_input_validation_report.md
```

标准错误：

无

### 审计人工复核决策

- 脚本：`scripts/build_human_review_decision_audit.py`
- 返回码：0

标准输出：

```text
Wrote datasets/human_review_decision_audit.jsonl
Wrote datasets/human_review_decision_audit.csv
Wrote reports/human_review_decision_audit_report.md
```

标准错误：

无

### 预览人工复核决策应用

- 脚本：`scripts/apply_human_review_decisions.py`
- 返回码：0

标准输出：

```text
Wrote reports/human_review_decision_apply_report.md
Wrote datasets/human_review_decision_apply_preview.jsonl
Wrote datasets/human_review_decision_apply_preview.csv
Dry-run update candidates: 0
```

标准错误：

无

### 构建人工复核进度

- 脚本：`scripts/build_human_review_progress.py`
- 返回码：0

标准输出：

```text
Wrote datasets/human_review_progress.jsonl
Wrote datasets/human_review_progress.csv
Wrote reports/human_review_progress_report.md
```

标准错误：

无

### 构建人工复核证据摘录

- 脚本：`scripts/build_human_review_evidence_extracts.py`
- 返回码：0

标准输出：

```text
Wrote datasets/human_review_evidence_extracts.jsonl
Wrote datasets/human_review_evidence_extracts.csv
Wrote reports/human_review_evidence_extracts_report.md
```

标准错误：

无

### 构建人工复核会话队列

- 脚本：`scripts/build_human_review_session_queue.py`
- 返回码：0

标准输出：

```text
Wrote datasets/human_review_session_queue.jsonl
Wrote datasets/human_review_session_queue.csv
Wrote reports/human_review_session_queue_report.md
```

标准错误：

无

### 构建人工复核会话状态

- 脚本：`scripts/build_human_review_session_status.py`
- 返回码：0

标准输出：

```text
Wrote datasets/human_review_session_status.jsonl
Wrote datasets/human_review_session_status.csv
Wrote reports/human_review_session_status_report.md
```

标准错误：

无

### 构建人工复核逐字段清单

- 脚本：`scripts/build_human_review_field_checklist.py`
- 返回码：0

标准输出：

```text
Wrote datasets/human_review_field_checklist.jsonl
Wrote datasets/human_review_field_checklist.csv
Wrote reports/human_review_field_checklist_report.md
```

标准错误：

无

### 构建人工复核来源矩阵

- 脚本：`scripts/build_human_review_source_matrix.py`
- 返回码：0

标准输出：

```text
Wrote datasets/human_review_source_matrix.jsonl
Wrote datasets/human_review_source_matrix.csv
Wrote reports/human_review_source_matrix_report.md
```

标准错误：

无

### 构建人工复核任务板

- 脚本：`scripts/build_human_review_task_board.py`
- 返回码：0

标准输出：

```text
Wrote datasets/human_review_task_board.jsonl
Wrote datasets/human_review_task_board.csv
Wrote reports/human_review_task_board_report.md
```

标准错误：

无

### 构建人工复核交接清单

- 脚本：`scripts/build_human_review_handoff.py`
- 返回码：0

标准输出：

```text
Wrote datasets/human_review_handoff.jsonl
Wrote datasets/human_review_handoff.csv
Wrote reports/human_review_handoff_report.md
```

标准错误：

无

### 构建人工复核会话决策模板

- 脚本：`scripts/build_human_review_session_decision_templates.py`
- 返回码：0

标准输出：

```text
Wrote 12 templates in review_inputs/human_review_session_decision_templates
Wrote review_inputs/human_review_session_decision_templates/README.md
Wrote reports/human_review_session_decision_templates_report.md
```

标准错误：

无

### 构建人工复核会话指南

- 脚本：`scripts/build_human_review_session_guides.py`
- 返回码：0

标准输出：

```text
Wrote reports/human_review_session_guides/README.md
Wrote 12 session guides in reports/human_review_session_guides
```

标准错误：

无

### 构建人工复核指南

- 脚本：`scripts/build_human_review_guides.py`
- 返回码：0

标准输出：

```text
Wrote reports/human_review_guides/README.md
Wrote reports/human_review_guides/01_ready_without_manual_note.md
Wrote reports/human_review_guides/02_ready_with_manual_note.md
```

标准错误：

无

### 构建术语表

- 脚本：`scripts/build_glossary.py`
- 返回码：0

标准输出：

```text
Wrote datasets/glossary.jsonl
Wrote datasets/glossary.csv
Wrote reports/glossary_report.md
```

标准错误：

无

### 构建发布知识库

- 脚本：`scripts/build_published_knowledge_base.py`
- 返回码：0

标准输出：

```text
Wrote published/README.md
Wrote published/manifest.json
Wrote published/source_catalog.jsonl
Wrote published/entity_catalog.jsonl
Wrote published/chunk_catalog.jsonl
Wrote published/relationship_adjacency.json
Wrote published/lexical_index.json
Wrote reports/published_knowledge_base_report.md
```

标准错误：

无

### 构建语义标识前置层

- 脚本：`scripts/build_semantic_identity.py`
- 返回码：0

标准输出：

```text
Wrote published/jsonld_context.json
Wrote published/semantic_id_map.jsonl
Wrote reports/semantic_identity_report.md
```

标准错误：

无

### 构建 LLM 候选增强框架

- 脚本：`scripts/build_llm_candidate_enrichment.py`
- 返回码：0

标准输出：

```text
Wrote datasets/chunk_enrichment_candidates.jsonl
Wrote datasets/entity_link_candidates.jsonl
Provider: mock; candidates require human review; primary entities unchanged
```

标准错误：

无

### 构建 RAG 检索索引框架

- 脚本：`scripts/build_rag_indexes.py`
- 返回码：0

标准输出：

```text
Wrote published/rag_mock_vector_index.jsonl
Wrote published/embedding_manifest.json
Wrote published/rag_retrieval_index.json
```

标准错误：

无

### 构建 BGE-M3 远程向量索引

- 脚本：`scripts/build_bge_m3_index.py`
- 返回码：0

标准输出：

```text
{"dimension": 0, "error_code": "missing_api_key", "generated_at": "2026-06-20T08:57:27+00:00", "generated_by": "scripts/build_bge_m3_index.py", "input_count": 2269, "input_hash": "ab0c6754081e7fd042d9cc2349fdb06fe4612a085056edb973b50b06b9891c6d", "local_model_enabled": false, "model": "BAAI/bge-m3", "provider": "siliconflow_bge_m3", "real_model_execution": false, "source_counts": {"chunk": 2037, "entity": 112, "evidence_template": 8, "glossary": 112}, "status": "skipped"}
```

标准错误：

无

### 构建 SQLite 知识库

- 脚本：`scripts/build_sqlite_knowledge_base.py`
- 返回码：0

标准输出：

```text
Wrote published/bgp_knowledge_base.sqlite
Wrote published/sqlite_schema.sql
Wrote reports/sqlite_knowledge_base_report.md
```

标准错误：

无

### 构建查询样例报告

- 脚本：`scripts/build_query_examples.py`
- 返回码：0

标准输出：

```text
Wrote reports/query_examples_report.md
```

标准错误：

无

### 校验发布完整性

- 脚本：`scripts/build_published_integrity_report.py`
- 返回码：0

标准输出：

```text
Wrote published/integrity_summary.json
Wrote reports/published_integrity_report.md
```

标准错误：

无

### 构建知识库就绪度报告

- 脚本：`scripts/build_readiness_report.py`
- 返回码：0

标准输出：

```text
Wrote published/readiness_summary.json
Wrote reports/readiness_report.md
```

标准错误：

无

### 构建数据字典

- 脚本：`scripts/build_data_dictionary.py`
- 返回码：0

标准输出：

```text
Wrote published/data_dictionary.json
Wrote reports/data_dictionary_report.md
```

标准错误：

无

### 构建覆盖报告

- 脚本：`scripts/build_coverage_report.py`
- 返回码：0

标准输出：

```text
Wrote reports/coverage_report.md
```

标准错误：

无

### 构建数据管理能力报告

- 脚本：`scripts/build_data_management_report.py`
- 返回码：0

标准输出：

```text
Wrote reports/data_management_report.md
```

标准错误：

无

### 构建生命周期治理报告

- 脚本：`scripts/build_lifecycle_report.py`
- 返回码：0

标准输出：

```text
Wrote datasets/lifecycle_inventory.jsonl
Wrote reports/lifecycle_report.md
```

标准错误：

无

### 构建语义质量治理报告

- 脚本：`scripts/build_semantic_quality_report.py`
- 返回码：0

标准输出：

```text
Wrote datasets/semantic_quality_findings.jsonl
Wrote reports/semantic_quality_report.md
```

标准错误：

无

### 构建 RAG 就绪框架报告

- 脚本：`scripts/build_rag_readiness_report.py`
- 返回码：0

标准输出：

```text
Wrote reports/rag_readiness_report.md
Wrote datasets/rag_query_eval.jsonl
```

标准错误：

无

### 运行 RAG 答案质量评测

- 脚本：`scripts/run_rag_answer_eval.py`
- 返回码：0

标准输出：

```text
Wrote datasets/rag_answer_eval_results.jsonl
Wrote reports/rag_answer_eval_report.md
```

标准错误：

无

### 运行混合检索评测

- 脚本：`scripts/run_hybrid_retrieval_eval.py`
- 返回码：0

标准输出：

```text
{"failed": 0, "mrr": 0.6882352941176471, "no_evidence_rejection_rate": 1.0, "passed": 20, "recall_at_5": 0.8431372549019607, "recall_at_8": 0.872549019607843, "source_coverage": ["case_report", "data_doc", "paper", "standard", "tool_doc"], "total": 20}
```

标准错误：

无

### 构建 RAG 答案失败样本分析

- 脚本：`scripts/build_rag_answer_failure_analysis.py`
- 返回码：0

标准输出：

```text
Wrote reports/rag_answer_failure_analysis_report.md
```

标准错误：

无

### 构建制品清单

- 脚本：`scripts/build_artifact_manifest.py`
- 返回码：0

标准输出：

```text
Wrote datasets/artifact_manifest.jsonl
Wrote datasets/artifact_manifest.csv
Wrote reports/artifact_manifest_report.md
```

标准错误：

无

### 运行质量检查

- 脚本：`scripts/quality_check.py`
- 返回码：0

标准输出：

```text
Wrote reports/quality_report.md
```

标准错误：

无
