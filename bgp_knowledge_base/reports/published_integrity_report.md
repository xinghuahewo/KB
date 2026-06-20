# 发布完整性校验报告

## 范围

本报告校验 `published/` 文件化入口、发布 manifest、SQLite 数据库、治理数据集和固定查询样例之间的一致性。

该步骤不联网、不下载、不调用 LLM、不做语义判断，也不改变实体审批状态。

## 摘要

- 总体状态：通过
- 检查项数：53
- 失败项数：0
- SQLite integrity_check：ok
- 查询样例失败数：0
- JSON 输出：`published/integrity_summary.json`

## 关键计数

| 项 | published | sqlite/dataset |
| --- | ---: | ---: |
| sources | 54 | 54 |
| entities | 112 | 112 |
| chunks | 2037 | 2037 |
| relationships | 106 | 106 |
| lexical_terms | 951 | 951 |
| pending_entities | 5 |  |
| semantic_skipped_actions | 2 |  |
| source_gap_items | 0 |  |
| human_review_decision_audit | 112 | 112 |
| human_review_decision_apply_preview | 110 | 110 |
| human_review_input_validation | 8 | 8 |
| human_review_progress | 14 | 14 |
| human_review_field_checklist | 834 | 834 |
| human_review_source_matrix | 31 | 31 |
| human_review_task_board | 25 | 25 |
| human_review_handoff | 25 | 25 |
| entity_evidence | 246 | 246 |
| review_packets | 112 | 112 |
| next_actions | 114 | 114 |
| case_observations | 148 | 148 |
| glossary | 112 | 112 |
| human_review_workbook | 112 | 112 |
| human_review_evidence_extracts | 672 | 672 |
| human_review_session_queue | 112 | 112 |
| human_review_session_status | 12 | 12 |

## 检查项

| 名称 | 状态 | 详情 |
| --- | --- | --- |
| published_file:README.md | 通过 | present |
| published_file:manifest.json | 通过 | present |
| published_file:source_catalog.jsonl | 通过 | present |
| published_file:entity_catalog.jsonl | 通过 | present |
| published_file:chunk_catalog.jsonl | 通过 | present |
| published_file:relationship_adjacency.json | 通过 | present |
| published_file:lexical_index.json | 通过 | present |
| published_file:bgp_knowledge_base.sqlite | 通过 | present |
| published_file:sqlite_schema.sql | 通过 | present |
| manifest_count:sources | 通过 | manifest=54, actual=54 |
| manifest_count:entities | 通过 | manifest=112, actual=112 |
| manifest_count:chunks | 通过 | manifest=2037, actual=2037 |
| manifest_count:relationships | 通过 | manifest=106, actual=106 |
| manifest_count:lexical_terms | 通过 | manifest=951, actual=951 |
| manifest_count:pending_entities | 通过 | manifest=5, actual=5 |
| manifest_count:semantic_skipped_actions | 通过 | manifest=2, actual=2 |
| manifest_count:source_gap_items | 通过 | manifest=0, actual=0 |
| manifest_count:human_review_decision_audit | 通过 | manifest=112, actual=112 |
| manifest_count:human_review_decision_apply_preview | 通过 | manifest=110, actual=110 |
| manifest_count:human_review_input_validation | 通过 | manifest=8, actual=8 |
| manifest_count:human_review_progress | 通过 | manifest=14, actual=14 |
| manifest_count:human_review_field_checklist | 通过 | manifest=834, actual=834 |
| manifest_count:human_review_source_matrix | 通过 | manifest=31, actual=31 |
| manifest_count:human_review_task_board | 通过 | manifest=25, actual=25 |
| manifest_count:human_review_handoff | 通过 | manifest=25, actual=25 |
| sqlite_count:sources | 通过 | sqlite=54, published=54 |
| sqlite_count:entities | 通过 | sqlite=112, published=112 |
| sqlite_count:chunks | 通过 | sqlite=2037, published=2037 |
| sqlite_count:relationships | 通过 | sqlite=106, published=106 |
| sqlite_count:lexical_terms | 通过 | sqlite=951, published=951 |
| sqlite_dataset_count:entity_evidence | 通过 | sqlite=246, dataset=246 |
| sqlite_dataset_count:review_packets | 通过 | sqlite=112, dataset=112 |
| sqlite_dataset_count:next_actions | 通过 | sqlite=114, dataset=114 |
| sqlite_dataset_count:case_observations | 通过 | sqlite=148, dataset=148 |
| sqlite_dataset_count:glossary | 通过 | sqlite=112, dataset=112 |
| sqlite_dataset_count:human_review_workbook | 通过 | sqlite=112, dataset=112 |
| sqlite_dataset_count:human_review_decision_audit | 通过 | sqlite=112, dataset=112 |
| sqlite_dataset_count:human_review_decision_apply_preview | 通过 | sqlite=110, dataset=110 |
| sqlite_dataset_count:human_review_input_validation | 通过 | sqlite=8, dataset=8 |
| sqlite_dataset_count:human_review_progress | 通过 | sqlite=14, dataset=14 |
| sqlite_dataset_count:human_review_evidence_extracts | 通过 | sqlite=672, dataset=672 |
| sqlite_dataset_count:human_review_session_queue | 通过 | sqlite=112, dataset=112 |
| sqlite_dataset_count:human_review_session_status | 通过 | sqlite=12, dataset=12 |
| sqlite_dataset_count:human_review_field_checklist | 通过 | sqlite=834, dataset=834 |
| sqlite_dataset_count:human_review_source_matrix | 通过 | sqlite=31, dataset=31 |
| sqlite_dataset_count:human_review_task_board | 通过 | sqlite=25, dataset=25 |
| sqlite_dataset_count:human_review_handoff | 通过 | sqlite=25, dataset=25 |
| sqlite_integrity | 通过 | ok |
| query_examples | 通过 | {"failed": 0, "passed": 24, "total": 24} |
| boundary:uses_llm | 通过 | manifest=False, expected=False |
| boundary:downloads_sources | 通过 | manifest=False, expected=False |
| boundary:approves_pending_entities | 通过 | manifest=False, expected=False |
| boundary:semantic_extraction | 通过 | manifest=False, expected=False |
