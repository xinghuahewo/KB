# SQLite 知识库报告

## 范围

`published/bgp_knowledge_base.sqlite` 从 `published/` 文件化入口确定性构建，用于本地 SQL 查询和程序化接入。

该步骤不联网、不下载、不调用 LLM、不做语义抽取，也不改变实体审批状态。

## 输出

- `published/bgp_knowledge_base.sqlite`
- `published/sqlite_schema.sql`

## 校验

- PRAGMA integrity_check：ok
- FTS5：enabled

## 表计数

- sources：54
- entities：112
- entity_sources：246
- chunks：2037
- chunk_topics：4332
- relationships：106
- lexical_terms：951
- lexical_entity_refs：685
- lexical_source_refs：524
- lexical_chunk_refs：8996
- entity_evidence：246
- review_packets：112
- next_actions：114
- case_observations：148
- glossary：112
- human_review_workbook：112
- human_review_decision_audit：112
- human_review_decision_apply_preview：110
- human_review_input_validation：8
- human_review_progress：14
- human_review_evidence_extracts：672
- human_review_session_queue：112
- human_review_session_status：12
- human_review_field_checklist：834
- human_review_source_matrix：31
- human_review_task_board：25
- human_review_handoff：25
- entity_fts：112
- chunk_fts：2037
