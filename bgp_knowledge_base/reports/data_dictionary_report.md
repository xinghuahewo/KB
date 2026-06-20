# 数据字典报告

## 范围

本报告描述当前 BGP 知识库发布包的数据入口、SQLite 表结构、JSONL 数据集字段和查询命令。

生成过程只读取现有文件和 SQLite PRAGMA，不联网、不下载、不调用 LLM、不做语义判断。

## 摘要

- Readiness：ready_deterministic
- 发布完整性：pass
- SQLite integrity_check：ok
- Published 文件数：17
- SQLite 表数：30
- JSONL 数据集数：31
- 查询命令数：23
- JSON 输出：`published/data_dictionary.json`

## Published 文件

| 文件 | 大小字节 | 说明 | JSONL 字段 |
| --- | ---: | --- | --- |
| `published/README.md` | 2601 | 发布入口说明。 |  |
| `published/bgp_knowledge_base.sqlite` | 12963840 | 本地 SQL 查询入口。 |  |
| `published/chunk_catalog.jsonl` | 1438186 | chunk 目录，包含 chunk 元数据、预览和所在文件。 | chunk_file, chunk_id, chunk_type, content_chars, content_preview, doc_id, language, review_status, section_path, source_ref, source_type, title, topics |
| `published/data_dictionary.json` | 99662 | 本数据字典的机器可读版本。 |  |
| `published/embedding_manifest.json` | 401 | 阶段四 RAG 框架的 embedding 覆盖、provider 和边界摘要。 |  |
| `published/entity_catalog.jsonl` | 121250 | 实体目录，包含实体 payload、来源、证据和复核桶。 | aliases, case_observation_count, category, chunk_count, entity_file, entity_id, entity_payload, entity_type, evidence_record_count, name, review_bucket, review_status, source_ref_count, source_refs |
| `published/integrity_summary.json` | 8950 | 发布完整性 gate 的机器可读摘要。 |  |
| `published/jsonld_context.json` | 842 | 阶段三点五语义标识前置层的 JSON-LD @context。 |  |
| `published/lexical_index.json` | 452779 | 机械词项索引，映射到实体、来源和 chunks。 |  |
| `published/manifest.json` | 2066 | 发布快照计数、输入输出和处理边界。 |  |
| `published/rag_mock_vector_index.jsonl` | 1359605 | 阶段四离线 mock 向量索引，用于当前设备不运行模型时的检索框架验收。 | @id, chunk_id, generated_by, review_status, source_ref, source_type, topics, vector |
| `published/rag_retrieval_index.json` | 622 | 阶段四检索索引摘要，登记 mock vector store、SQLite FTS5 兜底和可信集合规则。 |  |
| `published/readiness_summary.json` | 4792 | 知识库就绪度机器可读摘要。 |  |
| `published/relationship_adjacency.json` | 74288 | 实体关系邻接表。 |  |
| `published/semantic_id_map.jsonl` | 1263523 | 实体、来源、chunk、关系和证据的稳定 URI 映射。 | curie, generated_by, jsonld_type, label, local_id, resource_type, semantic_id, source_path, source_ref, uri |
| `published/source_catalog.jsonl` | 30259 | 来源目录，合并 inventory 和来源处理状态。 | authority, case_observation_count, chunk_count, cleaned_status, domain, language, organization, parsed_status, path, processing_status, publish_date, review_status, source_id, source_type, title, trust_level, url |
| `published/sqlite_schema.sql` | 16754 | SQLite 表结构。 |  |

## SQLite 表

| 表 | 行数 | 说明 | 字段 |
| --- | ---: | --- | --- |
| `case_observations` | 148 | 从案例 cleaned 文本正则抽取的观察值。 | observation_id TEXT, source_id TEXT, title TEXT, observation_type TEXT, value TEXT, source_ref TEXT, review_status TEXT, context TEXT, payload_json TEXT |
| `chunk_fts` | 2037 |  | chunk_id, title, source_type, chunk_type, content_preview |
| `chunk_topics` | 4332 | chunk 到主题的多对多引用。 | chunk_id TEXT, topic TEXT |
| `chunks` | 2037 | 知识片段目录和预览。 | chunk_id TEXT, doc_id TEXT, title TEXT, source_type TEXT, chunk_type TEXT, source_ref TEXT, language TEXT, review_status TEXT, content_chars INTEGER, content_preview TEXT, chunk_file TEXT, payload_json TEXT |
| `entities` | 112 | 结构化实体目录。 | entity_id TEXT, entity_type TEXT, name TEXT, category TEXT, review_status TEXT, source_ref_count INTEGER, evidence_record_count INTEGER, chunk_count INTEGER, case_observation_count INTEGER, review_bucket TEXT, entity_file TEXT, payload_json TEXT |
| `entity_evidence` | 246 | 实体到来源、路径和 chunk 样例的证据索引。 | evidence_id TEXT, entity_id TEXT, entity_type TEXT, entity_review_status TEXT, source_id TEXT, source_type TEXT, source_status TEXT, source_path TEXT, parsed_path TEXT, cleaned_path TEXT, chunk_count INTEGER, case_observation_count INTEGER, chunk_sample_ids_json TEXT, payload_json TEXT |
| `entity_fts` | 112 |  | entity_id, name, entity_type, category, payload_json |
| `entity_sources` | 246 | 实体到来源的多对多引用。 | entity_id TEXT, source_id TEXT |
| `glossary` | 112 | 从实体机械派生的术语表。 | term_id TEXT, entity_id TEXT, entity_type TEXT, term TEXT, category TEXT, definition TEXT, aliases_json TEXT, source_refs_json TEXT, review_status TEXT, payload_json TEXT |
| `human_review_decision_apply_preview` | 110 | 人工复核决策应用预览，记录 dry-run/write 模式和更新候选。 | preview_id TEXT, record_type TEXT, run_mode TEXT, entity_id TEXT, entity_file TEXT, from_status TEXT, to_status TEXT, application_status TEXT, can_apply INTEGER, needs_llm INTEGER, count INTEGER, message TEXT, payload_json TEXT |
| `human_review_decision_audit` | 112 | 人工复核决策审计，区分 no-op、可显式应用和阻塞状态。 | audit_id TEXT, workbook_id TEXT, entity_id TEXT, entity_type TEXT, display_name TEXT, entity_file TEXT, current_review_status TEXT, review_decision TEXT, target_review_status TEXT, application_status TEXT, can_apply INTEGER, blocking_reason TEXT, needs_llm INTEGER, decision_source TEXT, decision_reviewer TEXT, decision_reviewed_at TEXT, decision_note TEXT, payload_json TEXT |
| `human_review_evidence_extracts` | 672 | 人工复核证据摘录，按实体展开 chunk 样例、词项匹配和短摘录。 | extract_id TEXT, entity_id TEXT, entity_type TEXT, display_name TEXT, review_order INTEGER, review_batch TEXT, review_bucket TEXT, chunk_rank INTEGER, chunk_id TEXT, chunk_file TEXT, doc_id TEXT, source_ref TEXT, chunk_type TEXT, section_path_json TEXT, matched_terms_json TEXT, match_score INTEGER, excerpt TEXT, excerpt_char_count INTEGER, needs_llm INTEGER, llm_skip_reason TEXT, payload_json TEXT |
| `human_review_field_checklist` | 834 | 人工复核逐字段清单，把 pending 实体的结构化字段展开为字段级核验项。 | field_check_id TEXT, session_id TEXT, session_order INTEGER, within_session_order INTEGER, global_review_order INTEGER, field_order INTEGER, entity_id TEXT, entity_type TEXT, display_name TEXT, entity_file TEXT, field_name TEXT, field_value_preview TEXT, verification_prompt TEXT, decision_input_path TEXT, review_decision TEXT, needs_llm INTEGER, payload_json TEXT |
| `human_review_handoff` | 25 | 人工复核交接清单，逐项列出输入、人工输出目标、命令边界和验证入口。 | handoff_id TEXT, task_id TEXT, task_order INTEGER, task_type TEXT, handoff_status TEXT, title TEXT, primary_input TEXT, primary_input_exists INTEGER, secondary_input TEXT, secondary_input_exists INTEGER, expected_manual_output TEXT, dry_run_command TEXT, write_command TEXT, verification_command TEXT, can_write INTEGER, requires_human_decision INTEGER, needs_llm INTEGER, payload_json TEXT |
| `human_review_input_validation` | 8 | 人工复核输入校验，检查主决策 CSV 的结构和机械一致性。 | validation_id TEXT, check_order INTEGER, input_path TEXT, check_type TEXT, status TEXT, severity TEXT, checked_count INTEGER, issue_count INTEGER, affected_entity_ids_json TEXT, affected_rows_json TEXT, message TEXT, suggested_action TEXT, needs_llm INTEGER, payload_json TEXT |
| `human_review_progress` | 14 | 人工复核进度仪表盘，按整体、实体类型、批次和复核桶汇总。 | progress_id TEXT, scope_type TEXT, scope_value TEXT, entity_count INTEGER, pending_count INTEGER, approved_count INTEGER, rejected_count INTEGER, unreviewed_decision_count INTEGER, approved_decision_count INTEGER, rejected_decision_count INTEGER, needs_source_decision_count INTEGER, needs_semantic_review_decision_count INTEGER, ready_to_apply_count INTEGER, manual_followup_count INTEGER, blocked_by_llm_count INTEGER, no_op_count INTEGER, completion_percent REAL, needs_llm_count INTEGER, next_step TEXT, payload_json TEXT |
| `human_review_session_queue` | 112 | 人工复核会话队列，按 session 小批次组织待核验实体。 | session_item_id TEXT, session_id TEXT, session_order INTEGER, within_session_order INTEGER, global_review_order INTEGER, entity_id TEXT, entity_type TEXT, display_name TEXT, review_batch TEXT, review_bucket TEXT, review_status TEXT, review_decision TEXT, application_status TEXT, queue_status TEXT, source_refs_json TEXT, cleaned_paths_json TEXT, parsed_paths_json TEXT, top_extract_ids_json TEXT, top_chunk_ids_json TEXT, top_match_scores_json TEXT, decision_input_path TEXT, next_step TEXT, needs_llm INTEGER, payload_json TEXT |
| `human_review_session_status` | 12 | 人工复核会话状态汇总，按 session 统计完成率、状态计数和下一条待处理实体。 | session_status_id TEXT, session_id TEXT, session_order INTEGER, item_count INTEGER, awaiting_human_review_count INTEGER, ready_to_apply_count INTEGER, manual_followup_count INTEGER, blocked_by_llm_count INTEGER, unreviewed_decision_count INTEGER, approved_decision_count INTEGER, rejected_decision_count INTEGER, needs_source_decision_count INTEGER, needs_semantic_review_decision_count INTEGER, completion_percent REAL, next_entity_id TEXT, next_display_name TEXT, decision_input_path TEXT, needs_llm_count INTEGER, payload_json TEXT |
| `human_review_source_matrix` | 31 | 人工复核来源矩阵，按来源聚合待复核实体、字段核验项和证据路径。 | source_matrix_id TEXT, source_id TEXT, source_title TEXT, source_type TEXT, processing_status TEXT, source_chunk_count INTEGER, evidence_record_count INTEGER, entity_count INTEGER, field_check_count INTEGER, session_ids_json TEXT, entity_types_json TEXT, sample_entity_ids_json TEXT, cleaned_paths_json TEXT, parsed_paths_json TEXT, chunk_sample_ids_json TEXT, decision_input_path TEXT, payload_json TEXT |
| `human_review_task_board` | 25 | 人工复核任务板，整理 session、来源和审计入口的下一步执行队列。 | task_id TEXT, task_order INTEGER, task_type TEXT, task_status TEXT, title TEXT, session_id TEXT, source_id TEXT, entity_id TEXT, item_count INTEGER, field_check_count INTEGER, primary_input TEXT, secondary_input TEXT, suggested_command TEXT, write_command TEXT, needs_llm INTEGER, payload_json TEXT |
| `human_review_workbook` | 112 | 人工复核工作簿。 | workbook_id TEXT, review_order INTEGER, review_batch TEXT, priority INTEGER, entity_id TEXT, entity_type TEXT, display_name TEXT, review_status TEXT, review_bucket TEXT, review_decision TEXT, needs_llm INTEGER, related_packet_id TEXT, related_action_id TEXT, decision_instructions TEXT, payload_json TEXT |
| `lexical_chunk_refs` | 8996 | 词项到 chunk 引用。 | term TEXT, chunk_id TEXT |
| `lexical_entity_refs` | 685 | 词项到实体引用。 | term TEXT, entity_id TEXT |
| `lexical_source_refs` | 524 | 词项到来源引用。 | term TEXT, source_id TEXT |
| `lexical_terms` | 951 | 机械词项索引词表。 | term TEXT |
| `meta` | 5 | SQLite 构建元数据。 | key TEXT, value TEXT |
| `next_actions` | 114 | 统一下一步行动队列。 | action_id TEXT, action_order INTEGER, priority INTEGER, action_type TEXT, status TEXT, scope_id TEXT, entity_id TEXT, entity_type TEXT, display_name TEXT, review_bucket TEXT, related_dataset TEXT, needs_llm INTEGER, blocking_reason TEXT, suggested_action TEXT, skip_reason TEXT, payload_json TEXT |
| `relationships` | 106 | 实体关系边。 | relationship_id TEXT, src_id TEXT, src_type TEXT, relation TEXT, dst_id TEXT, dst_type TEXT, confidence REAL, source_refs_json TEXT |
| `review_packets` | 112 | 实体人工复核包摘要。 | packet_id TEXT, review_order INTEGER, entity_id TEXT, entity_type TEXT, display_name TEXT, review_status TEXT, review_bucket TEXT, source_ref_count INTEGER, evidence_record_count INTEGER, total_chunk_count INTEGER, case_observation_count INTEGER, suggested_action TEXT, payload_json TEXT |
| `sources` | 54 | 来源清单和确定性处理状态。 | source_id TEXT, title TEXT, source_type TEXT, domain TEXT, authority TEXT, organization TEXT, publish_date TEXT, language TEXT, path TEXT, url TEXT, trust_level TEXT, review_status TEXT, processing_status TEXT, parsed_status TEXT, cleaned_status TEXT, chunk_count INTEGER, case_observation_count INTEGER, payload_json TEXT |

## JSONL 数据集

| 数据集 | 记录数 | 字段 |
| --- | ---: | --- |
| `datasets/artifact_manifest.jsonl` | 444 | artifact_group, artifact_path, extension, generated_by, is_binary, line_count, sha256, size_bytes |
| `datasets/authoritative_source_requirements.jsonl` | 0 |  |
| `datasets/case_observations.jsonl` | 148 | context, observation_type, review_status, source_id, source_ref, title, value |
| `datasets/chunk_enrichment_candidates.jsonl` | 25 | candidate_id, chunk_id, evidence_type, generated_by, keywords, provider, review_status, semantic_title, source_ref, summary |
| `datasets/entity_link_candidates.jsonl` | 25 | candidate_id, chunk_id, confidence, entity_id, generated_by, provider, review_status, source_ref |
| `datasets/entity_review_packets.jsonl` | 112 | case_observation_count, chunk_sample_ids, cleaned_paths, display_name, entity_id, entity_payload, entity_type, evidence_record_count, generated_by, manual_note_source_count, non_manual_source_count, packet_id, parsed_paths, review_bucket, review_checklist, review_order, review_status, source_paths, source_ref_count, source_refs, suggested_action, total_chunk_count |
| `datasets/entity_review_queue.jsonl` | 5 | blocked_source_refs, entity_id, entity_type, generated_by, name, queue_id, review_status, source_processing_statuses, source_ref_count, source_refs, suggested_action |
| `datasets/entity_source_evidence.jsonl` | 246 | case_observation_count, chunk_count, chunk_sample_ids, cleaned_path, entity_id, entity_review_status, entity_type, evidence_id, generated_by, parsed_path, source_id, source_path, source_status, source_type |
| `datasets/glossary.jsonl` | 112 | aliases, category, definition, entity_id, entity_type, generated_by, review_status, source_refs, term, term_id |
| `datasets/human_review_decision_apply_preview.jsonl` | 110 | application_status, can_apply, count, entity_file, entity_id, from_status, generated_by, message, needs_llm, preview_id, record_type, run_mode, to_status |
| `datasets/human_review_decision_audit.jsonl` | 112 | application_status, audit_id, blocking_reason, can_apply, current_review_status, decision_note, decision_reviewed_at, decision_reviewer, decision_source, display_name, entity_file, entity_id, entity_type, generated_by, needs_llm, review_decision, target_review_status, workbook_id |
| `datasets/human_review_evidence_extracts.jsonl` | 672 | chunk_file, chunk_id, chunk_rank, chunk_type, display_name, doc_id, entity_id, entity_type, excerpt, excerpt_char_count, extract_id, generated_by, llm_skip_reason, match_score, matched_terms, needs_llm, review_batch, review_bucket, review_order, section_path, source_ref |
| `datasets/human_review_field_checklist.jsonl` | 834 | decision_input_path, display_name, entity_file, entity_id, entity_type, field_check_id, field_name, field_order, field_value_json, field_value_preview, generated_by, global_review_order, needs_llm, review_decision, session_id, session_order, verification_prompt, within_session_order |
| `datasets/human_review_handoff.jsonl` | 25 | can_write, dry_run_command, expected_manual_output, generated_by, handoff_id, handoff_status, needs_llm, primary_input, primary_input_exists, requires_human_decision, secondary_input, secondary_input_exists, skip_note, task_id, task_order, task_type, title, verification_command, write_command |
| `datasets/human_review_input_validation.jsonl` | 8 | affected_entity_ids, affected_rows, check_order, check_type, checked_count, generated_by, input_path, issue_count, message, needs_llm, severity, status, suggested_action, validation_id |
| `datasets/human_review_progress.jsonl` | 14 | approved_count, approved_decision_count, blocked_by_llm_count, completion_percent, entity_count, generated_by, manual_followup_count, needs_llm_count, needs_semantic_review_decision_count, needs_source_decision_count, next_step, no_op_count, pending_count, progress_id, ready_to_apply_count, rejected_count, rejected_decision_count, scope_type, scope_value, unreviewed_decision_count |
| `datasets/human_review_session_queue.jsonl` | 112 | application_status, cleaned_paths, decision_input_path, display_name, entity_id, entity_type, generated_by, global_review_order, needs_llm, next_step, parsed_paths, queue_status, review_batch, review_bucket, review_decision, review_status, session_id, session_item_id, session_order, source_refs, top_chunk_ids, top_extract_ids, top_match_scores, within_session_order |
| `datasets/human_review_session_status.jsonl` | 12 | approved_decision_count, awaiting_human_review_count, blocked_by_llm_count, completion_percent, decision_input_path, generated_by, item_count, manual_followup_count, needs_llm_count, needs_semantic_review_decision_count, needs_source_decision_count, next_display_name, next_entity_id, ready_to_apply_count, rejected_decision_count, session_id, session_order, session_status_id, unreviewed_decision_count |
| `datasets/human_review_source_matrix.jsonl` | 31 | chunk_sample_ids, cleaned_paths, cleaned_status, decision_input_path, entity_count, entity_types, evidence_record_count, field_check_count, generated_by, inventory_review_status, parsed_paths, parsed_status, processing_status, raw_status, sample_entity_ids, session_ids, source_chunk_count, source_id, source_matrix_id, source_path, source_title, source_type, trust_level |
| `datasets/human_review_task_board.jsonl` | 25 | entity_id, field_check_count, generated_by, item_count, needs_llm, primary_input, priority_reason, secondary_input, session_id, source_id, suggested_command, task_id, task_order, task_status, task_type, title, write_command |
| `datasets/human_review_workbook.jsonl` | 112 | chunk_sample_ids, cleaned_paths, decision_instructions, display_name, entity_id, entity_type, generated_by, llm_skip_reason, needs_llm, parsed_paths, priority, related_action_id, related_packet_id, review_batch, review_bucket, review_decision, review_order, review_status, source_paths, source_refs, workbook_id |
| `datasets/lifecycle_inventory.jsonl` | 112 | approved_at, display_name, entity_file, entity_id, entity_type, evidence_index, evidence_record_count, generated_by, lifecycle_id, lifecycle_reason, lifecycle_status, next_action_ids, open_action_count, review_bucket, review_packet_id, review_status, reviewed_by, source_ref_count, source_refs, valid_from, valid_until |
| `datasets/next_action_queue.jsonl` | 114 | action_id, action_order, action_type, blocking_reason, display_name, entity_id, entity_type, generated_by, needs_llm, priority, related_dataset, review_bucket, scope_id, skip_reason, source_refs, status, suggested_action |
| `datasets/rag_answer_eval_questions.jsonl` | 20 | expected_source_refs, expected_status, forbidden_terms, must_have_terms, notes, query, question_id |
| `datasets/rag_answer_eval_results.jsonl` | 20 | answer_preview, answer_status, citation_count, citations_from_context_pack, decision, expected_source_refs, expected_status, failed_checks, forbidden_terms_hit, generated, guardrails, matched_expected_source_refs, model, model_provider, must_have_terms_missing, query, question_id |
| `datasets/rag_answer_smoke_test_results.jsonl` | 3 | answer_preview, answer_status, citation_count, citations, error_code, generated, guardrails, model, model_provider, query, result_count |
| `datasets/rag_query_eval.jsonl` | 6 | generated_by, has_traceable_result, normalized_query, query, result_count, top_chunk_ids |
| `datasets/semantic_quality_findings.jsonl` | 16 | field, finding_id, generated_by, lifecycle_status, message, rule_id, severity, subject_id, subject_type, suggested_action |
| `datasets/source_gap_queue.jsonl` | 0 |  |
| `datasets/source_processing_status.jsonl` | 54 | case_observation_count, chunk_count, cleaned_status, notes, parseable, parsed_status, path, processing_status, raw_status, source_id, source_type |
| `datasets/stage_acceptance_results.jsonl` | 32 | commands_passed, commands_total, decision, effect_summary, file_checks_passed, file_checks_total, generated_at, human_items_count, reasons, report_checks_passed, report_checks_total, stage_id, stage_name |

## 查询命令

| 命令 | 状态 |
| --- | --- |
| `python3 scripts/query_knowledge_base.py stats` | 通过 |
| `python3 scripts/query_knowledge_base.py term route --limit 5` | 通过 |
| `python3 scripts/query_knowledge_base.py entity anomaly_route_leak` | 通过 |
| `python3 scripts/query_knowledge_base.py source rfc4271` | 通过 |
| `python3 scripts/query_knowledge_base.py neighbors concept_as_path` | 通过 |
| `python3 scripts/query_knowledge_base.py evidence anomaly_route_leak` | 通过 |
| `python3 scripts/query_knowledge_base.py review-packets --bucket ready_without_manual_note --limit 5` | 通过 |
| `python3 scripts/query_knowledge_base.py workbook --batch 01_ready_without_manual_note --limit 5` | 通过 |
| `python3 scripts/query_knowledge_base.py extracts anomaly_route_leak --limit 3` | 通过 |
| `python3 scripts/query_knowledge_base.py sessions --session-id review_session_001 --limit 5` | 通过 |
| `python3 scripts/query_knowledge_base.py actions --needs-llm true --limit 5` | 通过 |
| `python3 scripts/query_knowledge_base.py observations --type asn --limit 5` | 通过 |
| `python3 scripts/query_knowledge_base.py glossary route --limit 5` | 通过 |
| `python3 scripts/query_knowledge_base.py decision-audit --status no_op --limit 5` | 通过 |
| `python3 scripts/query_knowledge_base.py apply-preview --record-type summary --limit 5` | 通过 |
| `python3 scripts/query_knowledge_base.py input-validation --status pass --limit 5` | 通过 |
| `python3 scripts/query_knowledge_base.py progress --scope-type overall --limit 5` | 通过 |
| `python3 scripts/query_knowledge_base.py field-checks --session-id review_session_001 --limit 5` | 通过 |
| `python3 scripts/query_knowledge_base.py source-matrix --source-id rfc4271 --limit 5` | 通过 |
| `python3 scripts/query_knowledge_base.py task-board --type review_session --limit 5` | 通过 |
| `python3 scripts/query_knowledge_base.py handoff --type review_session --limit 5` | 通过 |
| `python3 scripts/query_knowledge_base.py search-entities RPKI --limit 5` | 通过 |
| `python3 scripts/query_knowledge_base.py search-chunks "route leak" --limit 5` | 通过 |

## 边界

- uses_llm：False
- downloads_sources：False
- approves_pending_entities：False
- semantic_extraction：False
