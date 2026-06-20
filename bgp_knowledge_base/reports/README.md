---
title: "报告文档归并索引"
document_type: "归并索引"
purpose: "归并 reports 目录下的阶段报告、质量报告、发布报告和人工复核指南，降低报告查找成本。"
scope: "reports 目录 Markdown 报告与指南"
status: "现行索引"
last_reviewed: "2026-06-19"
---
# 报告文档归并索引

## 先看这些

| 场景 | 入口 |
| --- | --- |
| 判断当前阶段是否可验收 | [stage_acceptance_report.md](stage_acceptance_report.md) |
| 判断知识库是否就绪 | [readiness_report.md](readiness_report.md) |
| 查看流水线执行结果 | [pipeline_report.md](pipeline_report.md) |
| 查看质量门禁 | [quality_report.md](quality_report.md) |
| 查看覆盖情况 | [coverage_report.md](coverage_report.md) |
| 查看发布包完整性 | [published_integrity_report.md](published_integrity_report.md) |
| 查看数据入口、字段和 SQLite 表 | [data_dictionary_report.md](data_dictionary_report.md) |
| 查看语义标识和 JSON-LD context | [semantic_identity_report.md](semantic_identity_report.md) |
| 查看 RAG 框架与运行边界 | [rag_readiness_report.md](rag_readiness_report.md) |
| 查看下一步任务 | [next_action_queue_report.md](next_action_queue_report.md) |

## 报告归并分组

### 流水线与阶段状态

- [pipeline_report.md](pipeline_report.md)：确定性流水线执行摘要。
- [stage_acceptance_report.md](stage_acceptance_report.md)：阶段验收结果与证据检查。
- [readiness_report.md](readiness_report.md)：知识库就绪度判断。
- [quality_report.md](quality_report.md)：质量检查结果。
- [coverage_report.md](coverage_report.md)：来源、chunk、实体、关系和发布覆盖情况。
- [lifecycle_report.md](lifecycle_report.md)：生命周期治理结果。
- [data_management_report.md](data_management_report.md)：数据管理能力盘点。
- [semantic_identity_report.md](semantic_identity_report.md)：阶段三点五语义标识、URI 规则和 JSON-LD context 结果。
- [rag_readiness_report.md](rag_readiness_report.md)：阶段四 RAG 框架、provider 边界、查询验收和 API 入口。

### 来源、解析与语料

- [raw_collection_summary.md](raw_collection_summary.md)：原始资料采集摘要。
- [ingestion_report.md](ingestion_report.md)：摄取结果。
- [parse_report.md](parse_report.md)：解析结果。
- [source_processing_status_report.md](source_processing_status_report.md)：来源处理状态。
- [source_gap_queue_report.md](source_gap_queue_report.md)：来源缺口队列。
- [authoritative_source_requirements_report.md](authoritative_source_requirements_report.md)：权威来源补充需求。
- [llm_processing_skip_report.md](llm_processing_skip_report.md)：LLM 跳过边界与记录。
- [low_risk_internalization_report.md](low_risk_internalization_report.md)：低风险内化结果。

### 实体、关系与证据

- [entity_review_queue_report.md](entity_review_queue_report.md)：实体复核队列。
- [entity_review_packet_report.md](entity_review_packet_report.md)：实体人工复核包。
- [entity_source_evidence_report.md](entity_source_evidence_report.md)：实体来源证据索引。
- [case_observation_report.md](case_observation_report.md)：案例观察值抽取结果。
- [glossary_report.md](glossary_report.md)：术语表结果。
- [artifact_manifest_report.md](artifact_manifest_report.md)：制品清单。

### 人工复核

- [human_review_task_board_report.md](human_review_task_board_report.md)：人工复核任务板。
- [human_review_handoff_report.md](human_review_handoff_report.md)：人工复核交接清单。
- [human_review_workbook_report.md](human_review_workbook_report.md)：人工复核工作簿。
- [human_review_progress_report.md](human_review_progress_report.md)：人工复核进度。
- [human_review_input_validation_report.md](human_review_input_validation_report.md)：人工复核输入校验。
- [human_review_decision_audit_report.md](human_review_decision_audit_report.md)：人工复核决策审计。
- [human_review_decision_apply_report.md](human_review_decision_apply_report.md)：人工复核决策应用结果。
- [human_review_decision_template_report.md](human_review_decision_template_report.md)：主决策模板报告。
- [human_review_session_decision_templates_report.md](human_review_session_decision_templates_report.md)：分会话决策模板报告。
- [human_review_session_queue_report.md](human_review_session_queue_report.md)：复核会话队列。
- [human_review_session_status_report.md](human_review_session_status_report.md)：复核会话状态。
- [human_review_field_checklist_report.md](human_review_field_checklist_report.md)：逐字段复核清单。
- [human_review_source_matrix_report.md](human_review_source_matrix_report.md)：按来源组织的复核矩阵。
- [human_review_evidence_extracts_report.md](human_review_evidence_extracts_report.md)：人工复核证据摘录。

### 发布与查询

- [published_knowledge_base_report.md](published_knowledge_base_report.md)：发布知识库报告。
- [published_integrity_report.md](published_integrity_report.md)：发布完整性校验。
- [sqlite_knowledge_base_report.md](sqlite_knowledge_base_report.md)：SQLite 知识库构建结果。
- [data_dictionary_report.md](data_dictionary_report.md)：数据字典。
- [query_examples_report.md](query_examples_report.md)：查询样例。
- [semantic_identity_report.md](semantic_identity_report.md)：语义标识前置层报告。
- [rag_readiness_report.md](rag_readiness_report.md)：RAG 就绪框架报告。

## 指南目录

| 目录 | 作用 |
| --- | --- |
| [case_observation_guides/](case_observation_guides/) | 按案例展开观察值核验材料。 |
| [human_review_guides/](human_review_guides/) | 按人工复核分组展开清单。 |
| [human_review_session_guides/](human_review_session_guides/) | 按 session 展开实体复核材料。 |

## 维护边界

- 本文件只归并报告入口，不替代单个报告中的统计数据和证据。
- 若报告由脚本生成，应优先重跑对应脚本更新原报告，再同步调整本索引。
- 若只是新增报告，应先补 Frontmatter，再加入本索引的相应分组。
