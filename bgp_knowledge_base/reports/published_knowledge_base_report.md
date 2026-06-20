# 发布知识库报告

## 范围

`published/` 是当前 BGP 知识库的确定性发布入口，只汇总已有事实、路径和引用，不做语义抽取、归纳或审批。

## 输出

- `published/README.md`
- `published/manifest.json`
- `published/source_catalog.jsonl`
- `published/entity_catalog.jsonl`
- `published/chunk_catalog.jsonl`
- `published/relationship_adjacency.json`
- `published/lexical_index.json`

## 计数

- sources：54
- entities：112
- chunks：2037
- relationships：106
- lexical_terms：951
- pending_entities：5
- semantic_skipped_actions：2
- source_gap_items：0
- human_review_decision_audit：112
- human_review_decision_apply_preview：110
- human_review_input_validation：8
- human_review_progress：14
- human_review_field_checklist：834
- human_review_source_matrix：31
- human_review_task_board：25
- human_review_handoff：25

## 边界

- 不联网、不下载资料。
- 不使用 LLM。
- 不把 pending 实体升级为 approved。
- 不根据文本内容自动扩展 PaperMethod、Case 或语义关系。
