# 覆盖报告

## MVP 覆盖快照

| 范围 | 目标 | 当前 | 状态 |
| --- | ---: | ---: | --- |
| BGPConcept | 30 | 31 | 已达到 |
| RoutingMechanism | 10 | 12 | 已达到 |
| AnomalyType | 8 | 8 | 已达到 |
| DataSource | 8 | 9 | 已达到 |
| DataField | 30 | 32 | 已达到 |
| EvidenceTemplate | 8 | 8 | 已达到 |
| PaperMethod | 5 | 3 | 部分覆盖 |
| Case | 5 | 5 | 已达到 |
| Relationship | 约 100 | 106 | 已达到 |

## 文本内化进度

| 层级 | 当前结果 |
| --- | ---: |
| parsed/standards | 11 个 JSON |
| parsed/data_docs | 16 个 JSON |
| parsed/papers | 13 个 JSON |
| parsed/cases | 13 个 JSON |
| cleaned/standards | 11 个 Markdown |
| cleaned/data_docs | 16 个 Markdown |
| cleaned/papers | 13 个 Markdown |
| cleaned/cases | 13 个 Markdown |
| cleaned/notes | 1 个 Markdown |

## Chunk 覆盖

| 文件 | Chunk 数 |
| --- | ---: |
| bgp_chunks.jsonl | 890 |
| case_chunks.jsonl | 89 |
| paper_chunks.jsonl | 504 |
| standard_chunks.jsonl | 554 |
| 合计 | 2037 |

## 规则化数据集覆盖

| 文件 | 记录数 | 说明 |
| --- | ---: | --- |
| datasets/case_observations.jsonl | 148 | 从 cleaned/cases 用正则抽取的案例观察值 |
| datasets/case_observations.csv | 148 | 同一观察值数据的 CSV 版本 |
| datasets/source_processing_status.jsonl | 54 | 按 inventory/source_id 汇总的确定性处理状态 |
| datasets/source_processing_status.csv | 54 | 同一来源处理状态数据的 CSV 版本 |
| datasets/source_gap_queue.jsonl | 0 | 未完成来源的缺口队列，记录建议后续动作 |
| datasets/source_gap_queue.csv | 0 | 同一来源缺口队列的 CSV 版本 |
| datasets/entity_review_queue.jsonl | 5 | 待人工复核实体队列，包含来源处理状态和建议动作 |
| datasets/entity_review_queue.csv | 5 | 同一实体复核队列的 CSV 版本 |
| datasets/entity_source_evidence.jsonl | 246 | 实体到来源的机械证据索引，列出路径和 chunk 样例 |
| datasets/entity_source_evidence.csv | 246 | 同一实体来源证据索引的 CSV 版本 |
| datasets/entity_review_packets.jsonl | 112 | 实体人工复核包，汇总实体字段、证据路径、chunk 样例和检查清单 |
| datasets/entity_review_packets.csv | 112 | 同一实体人工复核包的 CSV 版本 |
| datasets/authoritative_source_requirements.jsonl | 0 | 仅含 context/manual note 实体的权威来源补充需求队列 |
| datasets/authoritative_source_requirements.csv | 0 | 同一权威来源补充需求队列的 CSV 版本 |
| datasets/next_action_queue.jsonl | 114 | 统一下一步行动队列，合并补源、人工复核和按规则跳过事项 |
| datasets/next_action_queue.csv | 114 | 同一下一步行动队列的 CSV 版本 |
| datasets/human_review_workbook.jsonl | 112 | 面向人工审核的一行一实体复核工作簿，默认 unreviewed，不自动批准 |
| datasets/human_review_workbook.csv | 112 | 同一人工复核工作簿的 CSV 版本 |
| datasets/human_review_decision_audit.jsonl | 112 | 人工复核决策审计结果，识别可显式应用的 approved/rejected 决策 |
| datasets/human_review_decision_audit.csv | 112 | 同一人工复核决策审计结果的 CSV 版本 |
| datasets/human_review_decision_apply_preview.jsonl | 110 | 人工复核决策应用预览，记录 dry-run/write 模式、可应用决策、跳过状态和更新候选 |
| datasets/human_review_decision_apply_preview.csv | 110 | 同一人工复核决策应用预览的 CSV 版本 |
| datasets/human_review_input_validation.jsonl | 8 | 人工复核输入校验结果，检查主决策 CSV 的结构、枚举、重复项、未知实体和语义边界 |
| datasets/human_review_input_validation.csv | 8 | 同一人工复核输入校验结果的 CSV 版本 |
| datasets/human_review_progress.jsonl | 14 | 人工复核进度仪表盘，按整体、实体类型、复核批次和复核桶汇总 |
| datasets/human_review_progress.csv | 14 | 同一人工复核进度仪表盘的 CSV 版本 |
| datasets/human_review_evidence_extracts.jsonl | 672 | 人工复核证据摘录，按实体展开 chunk 样例、词项匹配和短摘录 |
| datasets/human_review_evidence_extracts.csv | 672 | 同一人工复核证据摘录的 CSV 版本 |
| datasets/human_review_session_queue.jsonl | 112 | 人工复核会话队列，将待复核实体切分为小批次并引用 top 摘录 |
| datasets/human_review_session_queue.csv | 112 | 同一人工复核会话队列的 CSV 版本 |
| datasets/human_review_session_status.jsonl | 12 | 人工复核会话状态汇总，按 session 汇总完成率、状态计数和下一条待处理实体 |
| datasets/human_review_session_status.csv | 12 | 同一人工复核会话状态汇总的 CSV 版本 |
| datasets/human_review_field_checklist.jsonl | 834 | 人工复核逐字段清单，把 pending 实体的结构化字段展开为字段级核验项 |
| datasets/human_review_field_checklist.csv | 834 | 同一人工复核逐字段清单的 CSV 版本 |
| datasets/human_review_source_matrix.jsonl | 31 | 人工复核来源矩阵，按来源聚合待复核实体、字段核验项、session 和证据路径 |
| datasets/human_review_source_matrix.csv | 31 | 同一人工复核来源矩阵的 CSV 版本 |
| datasets/human_review_task_board.jsonl | 25 | 人工复核任务板，整理 session、来源、输入校验、审计和应用入口的下一步执行队列 |
| datasets/human_review_task_board.csv | 25 | 同一人工复核任务板的 CSV 版本 |
| datasets/human_review_handoff.jsonl | 25 | 人工复核交接清单，逐项列出输入、人工输出目标、命令边界和验证入口 |
| datasets/human_review_handoff.csv | 25 | 同一人工复核交接清单的 CSV 版本 |
| datasets/glossary.jsonl | 112 | 从 entities 机械派生的 BGP 术语表 |
| datasets/glossary.csv | 112 | 同一术语表数据的 CSV 版本 |
| datasets/artifact_manifest.jsonl | 440 | 文件级制品清单，包含大小、行数和 SHA-256 |
| datasets/artifact_manifest.csv | 440 | 同一制品清单数据的 CSV 版本 |

## 发布知识库入口

| 文件 | 状态 |
| --- | --- |
| published/README.md | 已生成 |
| published/manifest.json | 已生成 |
| published/source_catalog.jsonl | 已生成 |
| published/entity_catalog.jsonl | 已生成 |
| published/chunk_catalog.jsonl | 已生成 |
| published/relationship_adjacency.json | 已生成 |
| published/lexical_index.json | 已生成 |
| published/bgp_knowledge_base.sqlite | 已生成 |
| published/sqlite_schema.sql | 已生成 |
| published/integrity_summary.json | 已生成 |
| published/readiness_summary.json | 已生成 |
| published/data_dictionary.json | 已生成 |

| 发布项 | 数量 |
| --- | ---: |
| chunks | 2037 |
| entities | 112 |
| human_review_decision_apply_preview | 110 |
| human_review_decision_audit | 112 |
| human_review_field_checklist | 834 |
| human_review_handoff | 25 |
| human_review_input_validation | 8 |
| human_review_progress | 14 |
| human_review_source_matrix | 31 |
| human_review_task_board | 25 |
| lexical_terms | 951 |
| pending_entities | 5 |
| relationships | 106 |
| semantic_skipped_actions | 2 |
| source_gap_items | 0 |
| sources | 54 |

## 来源处理状态

| 状态 | 来源数 |
| --- | ---: |
| complete_deterministic | 53 |
| manual_note | 1 |

## 来源缺口

- 当前缺口总数：0
- 无

## Schema 覆盖

| 范围 | 状态 |
| --- | --- |
| Source | 已校验 |
| ParsedDocument | 已校验 |
| Chunk | 已校验 |
| BGPConcept | 已校验 |
| RoutingMechanism | 已校验 |
| AnomalyType | 已校验 |
| DataSource | 已校验 |
| DataField | 已校验 |
| EvidenceTemplate | 已校验 |
| FalsePositivePattern | 已校验 |
| PaperMethod | 已校验 |
| Case | 已校验 |
| CaseObservation | 已校验 |
| SourceProcessingStatus | 已校验 |
| SourceGapQueueItem | 已校验 |
| EntityReviewQueueItem | 已校验 |
| EntitySourceEvidence | 已校验 |
| EntityReviewPacket | 已校验 |
| AuthoritativeSourceRequirement | 已校验 |
| NextAction | 已校验 |
| HumanReviewWorkbookEntry | 已校验 |
| HumanReviewDecisionAudit | 已校验 |
| HumanReviewDecisionApplyPreview | 已校验 |
| HumanReviewInputValidation | 已校验 |
| HumanReviewProgress | 已校验 |
| HumanReviewEvidenceExtract | 已校验 |
| HumanReviewSessionQueue | 已校验 |
| HumanReviewSessionStatus | 已校验 |
| HumanReviewFieldChecklist | 已校验 |
| HumanReviewSourceMatrix | 已校验 |
| HumanReviewTaskBoard | 已校验 |
| HumanReviewHandoff | 已校验 |
| GlossaryEntry | 已校验 |
| ArtifactManifest | 已校验 |
| Relationship | 已校验 |

## 已覆盖主题

- BGP 基础：BGP、AS、ASN、Prefix、BGP Speaker、BGP Session、eBGP、iBGP。
- BGP 消息与数据：RIB、FIB、Update、Announcement、Withdrawal、MRT、Collector、Peer、Vantage Point。
- 路径与属性：AS_PATH、Origin AS、NEXT_HOP、LOCAL_PREF、MED、OTC 等。
- 路由策略：AS Relationship、Customer Cone、Valley-free、BGP Roles。
- 路由安全：RPKI、ROA、ROV、BGPsec、RPKI-to-Router、ASPA、IRR、WHOIS/RDAP。
- 异常类型：Prefix Hijack、Subprefix Hijack、Path Hijack、Route Leak、MOAS、Origin Change、Path Manipulation、Prefix Outage。
- 数据源：RouteViews、RIPE RIS、BGPStream、CAIDA AS Relationship、CAIDA ASRank、RIPEstat、PeeringDB、MANRS、ASPA 文档。
- 论文和案例来源文本已覆盖 HTML 与可抽取文本的 PDF；PeeringDB OpenAPI YAML 已进入文本层；结构化 PaperMethod 和 Case 扩展仍遵守“需要 LLM 介入则跳过”的边界。

## 当前新增能力

- `scripts/parse_documents.py` 已支持 RFC TXT、HTML、YAML/OpenAPI schema 和可由 `pypdf` 确定性抽取文本的 PDF。
- PDF 来源已进入 parsed、cleaned 和 chunks 层；PDF 解析只做文本抽取和按页切分，不做语义归纳。
- YAML/OpenAPI schema 已进入 parsed、cleaned 和 chunks 层；YAML 解析只按顶层键机械分段。
- `scripts/build_case_observation_guides.py` 已生成中文逐案例观察值核验指南，只展开正则观察值，不判断角色、证据强度或影响范围。
- `scripts/build_source_gap_queue.py` 将未完成来源转换为待办队列；当前来源层缺口为 0。
- `scripts/build_entity_source_evidence.py` 已生成实体到来源的机械证据索引，为人工复核提供 parsed、cleaned 和 chunk 入口。
- `scripts/build_entity_review_packets.py` 已生成实体人工复核包，把实体字段、证据路径、chunk 样例和检查清单合并为人工审核入口。
- `scripts/build_authoritative_source_requirements.py` 已将仅含 context/manual note 的实体转成权威来源补充需求队列，且明确不做全量下载。
- `scripts/build_next_action_queue.py` 已将补源、人工复核和按规则跳过的语义任务合并成统一行动队列。
- `scripts/build_human_review_workbook.py` 已生成一行一实体的人工复核工作簿，默认 `unreviewed`，只供人工决策，不自动批准实体。
- `scripts/build_human_review_decision_template.py` 已生成 `review_inputs/human_review_decisions_template.csv`，并只在缺失时初始化 `review_inputs/human_review_decisions.csv`，避免覆盖人工填写结果。
- `scripts/build_human_review_input_validation.py` 已生成主人工决策输入校验，检查 CSV 结构、枚举、重复项、未知实体和语义边界，不判断实体内容。
- `scripts/build_human_review_decision_audit.py` 已生成工作簿决策审计，区分 no-op、可显式应用和需要语义流程阻塞的决策。
- `scripts/build_human_review_progress.py` 已生成人工复核进度仪表盘，按整体、实体类型、复核批次和复核桶汇总 pending、可应用决策与 LLM 阻塞计数。
- `scripts/build_human_review_evidence_extracts.py` 已生成人工复核证据摘录，按实体展开 chunk 样例、词项匹配和短摘录，只辅助人工定位，不判断证据充分性。
- `scripts/build_human_review_session_queue.py` 已生成人工复核会话队列，把 pending 实体按固定大小切成可执行小批次，并引用 top 摘录入口。
- `scripts/build_human_review_session_status.py` 已生成人工复核会话状态汇总，按 session 统计完成率、状态计数和下一条待处理实体。
- `scripts/build_human_review_field_checklist.py` 已生成人工复核逐字段清单，把实体 payload 展开为字段级核验项，方便逐字段确认来源支撑。
- `scripts/build_human_review_source_matrix.py` 已生成人工复核来源矩阵，按来源聚合受影响实体、字段核验项、session 和证据路径。
- `scripts/build_human_review_task_board.py` 已生成人工复核任务板，把 session、来源、输入校验、决策审计和显式应用入口整理为下一步执行队列。
- `scripts/build_human_review_handoff.py` 已生成人工复核交接清单，把任务板逐项转成输入、人工输出目标、命令边界和验证入口。
- `scripts/build_human_review_session_decision_templates.py` 已生成按 session 切分的人工决策模板，方便小批次填写主决策文件。
- `scripts/import_human_review_session_decisions.py` 提供逐 session 模板到主决策文件的显式导入入口；默认 dry-run，只有传入 `--write` 才会写入人工决策 CSV。
- `scripts/build_human_review_session_guides.py` 已生成中文分会话人工复核指南，把每个 session 的实体、来源路径和 top 摘录展开为可执行操作入口。
- `scripts/apply_human_review_decisions.py` 提供显式应用入口；默认 dry-run 并生成机器可读应用预览，只有传入 `--write` 且审计通过的 `approved/rejected` 人工决策才会改写实体状态。
- `scripts/build_human_review_guides.py` 已生成中文分批人工复核指南，展开证据路径、chunk 样例和按规则跳过的语义事项。
- `rfc2622`、`rfc3912`、`rfc9082`、`rfc9083` 已作为少量权威标准来源补充归档，用于 IRR 与 WHOIS/RDAP 概念复核。
- `scripts/build_published_knowledge_base.py` 已生成 `published/` 发布入口，包含来源目录、实体目录、chunk 目录、关系邻接表、词项索引和发布 manifest。
- `scripts/build_sqlite_knowledge_base.py` 已生成 `published/bgp_knowledge_base.sqlite` 和 `published/sqlite_schema.sql`，用于本地 SQL 查询和程序化接入；数据库包含来源、实体、chunk、关系、词项、证据索引、复核包、行动队列、案例观察值、术语表、人工复核工作簿、决策审计、输入校验、复核进度、证据摘录、会话队列、会话状态、逐字段清单、来源矩阵、任务板和交接清单。
- `scripts/query_knowledge_base.py` 已提供本地查询 CLI；`scripts/build_query_examples.py` 已生成固定查询样例报告，验证 stats、term、entity、source、neighbors、evidence、review-packets、workbook、extracts、sessions、actions、observations、glossary、decision-audit、input-validation、progress、field-checks、source-matrix、task-board、handoff 和全文检索入口。
- `scripts/build_published_integrity_report.py` 已生成发布完整性 gate，校验 published 文件、manifest 计数、SQLite 表计数、治理数据集、查询样例和边界标记之间的一致性。
- `scripts/build_readiness_report.py` 已生成知识库就绪度报告，把 `context.md` 的目标产物映射到当前证据，并区分确定性已达成项与需人工/语义流程项。
- `scripts/build_data_dictionary.py` 已生成数据字典，描述 published 文件、SQLite 表结构、JSONL 数据集字段和查询命令。
- `scripts/build_coverage_report.py` 从当前制品自动生成本报告，避免覆盖数字与流水线产物漂移。

## 仍然存在的缺口

- 实体记录仍有 5 条 `pending`，需要人工来源核验后才能改为 `approved`。
- PaperMethod 当前 3 条，目标 5 条；从论文正文扩展结构化方法需要语义判断，已按规则跳过。
- 案例观察值已有 148 条，但事件角色、证据强度和影响范围仍需人工或明确允许的语义流程。

## 下一步优先级

1. 基于 `reports/human_review_guides/`、`datasets/human_review_workbook.*` 与 `review_inputs/human_review_decisions.csv` 对 pending 实体做人工来源核验，人工确认并审计后再显式应用 `approved/rejected`。
2. 基于 `reports/case_observation_guides/` 与 `datasets/case_observations.*` 做人工核验，人工确认后再决定是否写入 `entities/cases.jsonl`。
3. 明确允许语义流程后，再扩展 PaperMethod 和 Case 结构化字段。
