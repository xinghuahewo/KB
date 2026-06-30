---
title: "BGP 知识库数据准备"
document_type: "目录入口说明"
purpose: "说明 BGP 知识库数据准备目录的目标、范围、结构和统一运行入口，帮助快速理解仓库内容。"
scope: "知识库根目录"
status: "现行入口"
last_reviewed: "2026-06-19"
---
# BGP 知识库数据准备

这个目录用于把 BGP 领域资料整理成可追溯、可维护、可扩展的数据底座，并提供确定性流水线、本地查询入口和只读服务。

## 文档入口

当前 Markdown 已按用途归并到以下入口：

| 入口 | 用途 |
| --- | --- |
| [docs/README.md](docs/README.md) | 规划、治理、项目上下文和目录导航的归并索引。 |
| [docs/rules/document_crud_rules_v1.md](docs/rules/document_crud_rules_v1.md) | Markdown 文档 CRUD 与自动校验规则。 |
| [data/reports/README.md](data/reports/README.md) | 阶段报告、质量报告、发布报告和人工复核报告的归并索引。 |
| [data/corpus/cleaned/README.md](data/corpus/cleaned/README.md) | 清洗后的标准、数据源、论文、案例语料归并索引。 |
| [data/published/README.md](data/published/README.md) | 可交付发布包、SQLite、JSONL 和查询入口。 |

## 目标

构建一条可复跑的数据准备链路：

```text
data/sources/raw -> data/corpus/parsed -> data/corpus/cleaned -> data/corpus/chunks
  -> data/knowledge/entities + data/knowledge/relationships
  -> data/derived/datasets + data/published + data/reports
```

## 范围

第一版只覆盖 BGP 领域知识：

- BGP 概念。
- 路由机制。
- 数据源与字段。
- 异常类型。
- 检测证据模板。
- 误报与边界条件。
- 论文方法。
- 历史案例。
- 上述对象之间的关系。

## 目录结构

```text
data/
  sources/        原始资料和来源登记表
  corpus/         parsed、cleaned、chunks 语料链路
  knowledge/      实体和关系核心知识资产
  derived/        规则化派生数据集
  review_inputs/  人工填写的复核决策输入与可再生成模板
  published/      可交付知识库入口、索引、SQLite 数据库和发布 manifest
  reports/        门禁、参考和行动入口报告
  generated/      可再生成报告、指南和快照
metadata/
  config/         分类体系、实体类型、来源类型、质量规则
  schemas/        JSON Schema
src/bgpkb/
  pipeline/       本地解析、切分、抽取和校验模块
  service/        只读 FastAPI 服务
tests/            自动化测试
docs/             规划、治理、阶段和规则文档
```

## 存储格式

| 层级 | 格式 |
| --- | --- |
| 原始资料层 | PDF / DOCX / HTML / Markdown / TXT / YAML |
| 清洗文本层 | Markdown |
| 知识片段层 | JSONL |
| 结构化实体层 | JSONL / PostgreSQL |
| 关系图谱层 | JSONL / SQLite / PostgreSQL / Neo4j |
| 大规模结构化数据层 | CSV / Parquet |
| 配置层 | YAML |
| Schema 层 | JSON Schema |

机器可读版本维护在 `metadata/config/storage_formats.yaml`。

## 确定性流水线

推荐统一运行：

```bash
export PYTHONPATH=src
python3 -m bgpkb.pipeline.run_pipeline
```

该命令会按顺序执行：

1. `src/bgpkb/pipeline/parse_documents.py`
2. `src/bgpkb/pipeline/build_chunks.py`
3. `src/bgpkb/pipeline/extract_case_observations.py`
4. `src/bgpkb/pipeline/build_source_processing_status.py`
5. `src/bgpkb/pipeline/build_source_gap_queue.py`
6. `src/bgpkb/pipeline/build_entity_review_queue.py`
7. `src/bgpkb/pipeline/build_entity_source_evidence.py`
8. `src/bgpkb/pipeline/build_entity_review_packets.py`
9. `src/bgpkb/pipeline/build_authoritative_source_requirements.py`
10. `src/bgpkb/pipeline/build_next_action_queue.py`
11. `src/bgpkb/pipeline/build_llm_processing_skip_report.py`
12. `src/bgpkb/pipeline/build_case_observation_guides.py`
13. `src/bgpkb/pipeline/build_human_review_workbook.py`
14. `src/bgpkb/pipeline/build_human_review_decision_template.py`
15. `src/bgpkb/pipeline/build_human_review_input_validation.py`
16. `src/bgpkb/pipeline/build_human_review_decision_audit.py`
17. `src/bgpkb/pipeline/apply_human_review_decisions.py`
18. `src/bgpkb/pipeline/build_human_review_progress.py`
19. `src/bgpkb/pipeline/build_human_review_evidence_extracts.py`
20. `src/bgpkb/pipeline/build_human_review_session_queue.py`
21. `src/bgpkb/pipeline/build_human_review_session_status.py`
22. `src/bgpkb/pipeline/build_human_review_field_checklist.py`
23. `src/bgpkb/pipeline/build_human_review_source_matrix.py`
24. `src/bgpkb/pipeline/build_human_review_task_board.py`
25. `src/bgpkb/pipeline/build_human_review_handoff.py`
26. `src/bgpkb/pipeline/build_human_review_session_decision_templates.py`
27. `src/bgpkb/pipeline/build_human_review_session_guides.py`
28. `src/bgpkb/pipeline/build_human_review_guides.py`
29. `src/bgpkb/pipeline/build_glossary.py`
30. `src/bgpkb/pipeline/build_published_knowledge_base.py`
31. `src/bgpkb/pipeline/build_sqlite_knowledge_base.py`
32. `src/bgpkb/pipeline/build_query_examples.py`
33. `src/bgpkb/pipeline/build_published_integrity_report.py`
34. `src/bgpkb/pipeline/build_readiness_report.py`
35. `src/bgpkb/pipeline/build_data_dictionary.py`
36. `src/bgpkb/pipeline/build_coverage_report.py`
37. `src/bgpkb/pipeline/build_data_management_report.py`
38. `src/bgpkb/pipeline/build_lifecycle_report.py`
39. `src/bgpkb/pipeline/build_semantic_quality_report.py`
40. `src/bgpkb/pipeline/build_artifact_manifest.py`
41. `src/bgpkb/pipeline/quality_check.py`

运行结果写入 `data/reports/gates/pipeline_report.md`。

## 人工复核决策流程

流水线会生成 `data/review_inputs/human_review_decisions_template.csv` 作为可参考模板，并只在 `data/review_inputs/human_review_decisions.csv` 不存在时初始化表头。人工填写文件不会被流水线覆盖。

人工复核 pending 实体时：

1. 参考 `data/reports/actions/human_review_task_board_report.md` 查看下一步任务板；需要交接清单时看 `data/generated/reports/review/human_review_handoff_report.md` 和 `data/derived/datasets/human_review_handoff.csv`，需要 session 细节时看 `data/generated/reports/review/human_review_session_guides/`，需要 session 完成率和下一条实体时看 `data/generated/reports/review/human_review_session_status_report.md`，需要逐字段核验项时看 `data/generated/reports/review/human_review_field_checklist_report.md` 和 `data/derived/datasets/human_review_field_checklist.csv`，需要按来源批量核验时看 `data/generated/reports/review/human_review_source_matrix_report.md` 和 `data/derived/datasets/human_review_source_matrix.csv`，需要逐 session 填写参考时看 `data/review_inputs/human_review_session_decision_templates/`，需要表格视图时看 `data/derived/datasets/human_review_session_queue.csv`。
2. 在 `data/review_inputs/human_review_decisions.csv` 填写 `entity_id`、`review_decision`、`reviewer`、`reviewed_at` 和 `decision_note`。
3. 只使用 `approved`、`rejected`、`needs_source`、`needs_semantic_review`；留空或 `unreviewed` 表示不应用。
4. 如果先填写了逐 session 模板，可先运行 `python3 -m bgpkb.pipeline.import_human_review_session_decisions --session-id review_session_001` 做 dry-run；确认无误后显式加 `--write` 合并到主决策文件。
5. 运行 `python3 -m bgpkb.pipeline.build_human_review_input_validation` 校验主决策输入结构，检查 `data/generated/reports/review/human_review_input_validation_report.md`。
6. 运行 `python3 -m bgpkb.pipeline.build_human_review_decision_audit` 审计输入，检查 `data/generated/reports/review/human_review_decision_audit_report.md`。
7. 运行 `python3 -m bgpkb.pipeline.build_human_review_progress` 查看 `data/reports/actions/human_review_progress_report.md` 中的分组进度。
8. 运行 `python3 -m bgpkb.pipeline.build_human_review_evidence_extracts` 查看 `data/derived/datasets/human_review_evidence_extracts.*` 中的 chunk 摘录；摘录只用于定位，不代表自动批准依据。
9. 运行 `python3 -m bgpkb.pipeline.build_human_review_session_queue`、`python3 -m bgpkb.pipeline.build_human_review_session_status`、`python3 -m bgpkb.pipeline.build_human_review_field_checklist`、`python3 -m bgpkb.pipeline.build_human_review_source_matrix`、`python3 -m bgpkb.pipeline.build_human_review_task_board`、`python3 -m bgpkb.pipeline.build_human_review_handoff`、`python3 -m bgpkb.pipeline.build_human_review_session_decision_templates` 和 `python3 -m bgpkb.pipeline.build_human_review_session_guides` 更新小批次队列、会话状态、逐字段清单、来源矩阵、任务板、交接清单、会话模板与分会话指南，继续从下一个 session 处理。
10. 确认无误后，先运行 `python3 -m bgpkb.pipeline.apply_human_review_decisions` 查看 dry-run 应用报告；确认后显式运行 `python3 -m bgpkb.pipeline.apply_human_review_decisions --write` 应用已审计通过且不需要 LLM 的 `approved/rejected` 决策。
11. 重新运行 `python3 -m bgpkb.pipeline.run_pipeline` 生成一致的发布包和报告。

`needs_semantic_review` 需要语义流程或 LLM，当前按规则跳过并记录，不会被应用脚本写入实体。

## 本地查询入口

发布后的 SQLite 数据库位于 `data/published/bgp_knowledge_base.sqlite`。可使用查询脚本查看统计、实体、来源、关系邻居、词项索引和 chunk 检索结果：

```bash
python3 -m bgpkb.pipeline.query_knowledge_base stats
python3 -m bgpkb.pipeline.query_knowledge_base term route --limit 5
python3 -m bgpkb.pipeline.query_knowledge_base entity anomaly_route_leak
python3 -m bgpkb.pipeline.query_knowledge_base source rfc4271
python3 -m bgpkb.pipeline.query_knowledge_base neighbors concept_as_path
python3 -m bgpkb.pipeline.query_knowledge_base evidence anomaly_route_leak
python3 -m bgpkb.pipeline.query_knowledge_base review-packets --bucket ready_without_manual_note --limit 5
python3 -m bgpkb.pipeline.query_knowledge_base workbook --batch 01_ready_without_manual_note --limit 5
python3 -m bgpkb.pipeline.query_knowledge_base extracts anomaly_route_leak --limit 3
python3 -m bgpkb.pipeline.query_knowledge_base sessions --session-id review_session_001 --limit 5
python3 -m bgpkb.pipeline.query_knowledge_base actions --needs-llm true --limit 5
python3 -m bgpkb.pipeline.query_knowledge_base observations --type asn --limit 5
python3 -m bgpkb.pipeline.query_knowledge_base glossary route --limit 5
python3 -m bgpkb.pipeline.query_knowledge_base decision-audit --status no_op --limit 5
python3 -m bgpkb.pipeline.query_knowledge_base apply-preview --record-type summary --limit 5
python3 -m bgpkb.pipeline.query_knowledge_base input-validation --status pass --limit 5
python3 -m bgpkb.pipeline.query_knowledge_base progress --scope-type overall --limit 5
python3 -m bgpkb.pipeline.query_knowledge_base field-checks --session-id review_session_001 --limit 5
python3 -m bgpkb.pipeline.query_knowledge_base source-matrix --source-id rfc4271 --limit 5
python3 -m bgpkb.pipeline.query_knowledge_base task-board --type review_session --limit 5
python3 -m bgpkb.pipeline.query_knowledge_base handoff --type review_session --limit 5
python3 -m bgpkb.pipeline.query_knowledge_base search-entities RPKI --limit 5
python3 -m bgpkb.pipeline.query_knowledge_base search-chunks '"route leak"' --limit 5
```

固定查询验收结果写入 `data/reports/reference/query_examples_report.md`，覆盖统计、词项、实体、来源、关系、证据索引、复核包、人工复核工作簿、人工复核证据摘录、人工复核会话队列、行动队列、案例观察值、术语表、决策审计、应用预览、输入校验、复核进度、逐字段清单、来源矩阵、任务板、交接清单和全文检索入口。

## 知识服务化入口

`src/bgpkb/service/` 提供一个只读 FastAPI 服务，直接读取已发布的 `data/published/bgp_knowledge_base.sqlite`。该服务只做查询和浏览，不生成、不修复、不覆盖流水线产物。

安装依赖：

```bash
cd bgp_knowledge_base
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-service.txt
```

启动服务：

```bash
uvicorn service.app:app --reload --host 127.0.0.1 --port 8000
```

浏览入口：

- 首页：`http://127.0.0.1:8000/`
- OpenAPI 文档：`http://127.0.0.1:8000/docs`
- 实体页示例：`http://127.0.0.1:8000/entities/anomaly_route_leak`
- 来源页示例：`http://127.0.0.1:8000/sources/rfc4271`

API 示例：

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/v1/stats
curl http://127.0.0.1:8000/api/v1/entities/anomaly_route_leak
curl "http://127.0.0.1:8000/api/v1/search/entities?q=RPKI&limit=5"
curl "http://127.0.0.1:8000/api/v1/search/chunks?q=route%20leak&limit=5"
curl "http://127.0.0.1:8000/api/v1/actions?needs_llm=true&limit=5"
curl -X POST http://127.0.0.1:8000/api/v1/rag/answer \
  -H "Content-Type: application/json" \
  -d '{"query":"route leak","limit":3}'
```

阶段 4.2 可用真实 DeepSeek API 做冒烟验证。该脚本只从环境变量读取密钥，不把密钥写入报告或数据集：

```bash
export DEEPSEEK_API_KEY="你的 DeepSeek API key"
python3 -m bgpkb.pipeline.run_rag_answer_smoke_test
```

输出：

- `data/derived/datasets/rag_answer_smoke_test_results.jsonl`
- `data/generated/reports/rag/rag_answer_smoke_test_report.md`

阶段 4.3 提供可复跑的 RAG 答案质量评测。无 `DEEPSEEK_API_KEY` 时脚本使用离线结构检查客户端，不调用外部 API；设置密钥后可复用同一评测集做真实答案评测：

```bash
python3 -m bgpkb.pipeline.run_rag_answer_eval
```

输出：

- `data/derived/datasets/rag_answer_eval_questions.jsonl`
- `data/derived/datasets/rag_answer_eval_results.jsonl`
- `data/generated/reports/rag/rag_answer_eval_report.md`

阶段 4.4 可用真实 DeepSeek API 跑同一评测集，并对失败样本做中文分析。真实评测脚本要求显式设置 `DEEPSEEK_API_KEY`；失败分析脚本不读取密钥，可在 CI 或本地离线复跑：

```bash
export DEEPSEEK_API_KEY="你的 DeepSeek API key"
python3 -m bgpkb.pipeline.run_deepseek_rag_answer_eval
python3 -m bgpkb.pipeline.build_rag_answer_failure_analysis
```

输出：

- `data/derived/datasets/deepseek_rag_answer_eval_results.jsonl`
- `data/generated/reports/rag/deepseek_rag_answer_eval_report.md`
- `data/generated/reports/rag/rag_answer_failure_analysis_report.md`

阶段 4.5 使用远程 BGE-M3、关键词和元数据做 RRF 混合检索。默认使用 SiliconFlow `BAAI/bge-m3`；当前设备不下载或运行本地模型。无密钥时可验证离线检索边界和评测框架：

```bash
python3 -m bgpkb.pipeline.build_bge_m3_index
python3 -m bgpkb.pipeline.query_hybrid_rag search "路由泄露" --top-k 5 --no-vector
python3 -m bgpkb.pipeline.run_hybrid_retrieval_eval
```

配置 `SILICONFLOW_API_KEY` 后，可运行真实远程向量索引构建。产物位于：

- `data/published/bge_m3_embedding_manifest.json`
- `data/published/bge_m3_vector_index.jsonl`
- `data/derived/datasets/hybrid_retrieval_eval_results.jsonl`
- `data/generated/reports/rag/bge_m3_embedding_report.md`
- `data/generated/reports/rag/hybrid_retrieval_eval_report.md`

自动化测试：

```bash
pytest tests -v
```

当前服务边界：

- 只读访问 SQLite，缺失数据库时通过 `/health` 和 API 错误返回清晰状态。
- 阶段 4.1 提供 `POST /api/v1/rag/answer`，只做检索、context pack 和可追溯答案编排。
- 阶段 4.5 提供 `/api/v1/hybrid/search` 和 `/api/v1/hybrid/context-pack`，RAG Answer 复用同一混合检索 context pack。
- DeepSeek API 只从环境变量 `DEEPSEEK_API_KEY` 读取密钥；仓库只提供 `.env.example`，不保存真实密钥。
- 当前设备不运行本地模型；`metadata/config/rag_retrieval.yaml` 中 `embedding.local_model_enabled=false`，Qwen embedding 只预留后续部署字段。
- LLM 不可用或没有证据时不会编造答案，会返回检索证据、引用和失败状态。
- 不提供编辑、审批、写入、导出、权限系统或知识库自动改写能力。
- API 返回结构尽量贴近 `src/bgpkb/pipeline/query_knowledge_base.py` 的 JSON 输出，方便后续迁移和集成。

阶段 4.1 RAG Answer API 最小响应字段：

- `answer_status`：`answered`、`llm_unavailable` 或 `no_evidence`。
- `generated`：是否由 LLM 生成最终答案。
- `citations`：生成或兜底响应所依据的来源引用。
- `context_pack`：检索命中的 chunk、引用和策略排除项。
- `guardrails`：只读、引用必需、本地模型禁用和禁止写回等边界。

## 数据管理体系

阶段一数据管理体系文档位于 `docs/governance/data_management_v1.md`，用于说明 BGP KB 的数据资产清单、数据模型标准、元数据与溯源、质量治理、生命周期、服务化访问和标准化出口。

机器可读能力清单位于 `metadata/config/data_management_capabilities.yaml`。可运行以下命令生成当前数据管理能力盘点报告：

```bash
python3 -m bgpkb.pipeline.build_data_management_report
```

报告输出到 `data/generated/reports/knowledge/data_management_report.md`，用于查看各类资产和治理能力的状态、证据覆盖和下一步缺口。

## 生命周期与元数据治理

阶段二生命周期治理文档位于 `docs/governance/lifecycle_metadata_v1.md`，用于把实体从单一 `review_status` 扩展为 `draft -> candidate -> reviewed -> approved -> deprecated -> archived` 的治理视图。

机器可读策略位于 `metadata/config/lifecycle_policy.yaml`。可运行以下命令生成实体级生命周期清单和治理报告：

```bash
python3 -m bgpkb.pipeline.build_lifecycle_report
```

输出：

- `data/derived/datasets/lifecycle_inventory.jsonl`
- `data/generated/reports/knowledge/lifecycle_report.md`

该步骤只读取现有实体、来源证据、复核包、行动队列和人工决策审计，不修改实体、关系、chunk 或发布包。

## 语义质量治理

阶段三语义质量治理文档位于 `docs/governance/semantic_quality_v1.md`，用于把结构质量检查扩展为跨实体语义一致性扫描。

机器可读规则位于 `metadata/config/semantic_quality_rules.yaml`。可运行以下命令生成语义质量 findings 和报告：

```bash
python3 -m bgpkb.pipeline.build_semantic_quality_report
```

输出：

- `data/derived/datasets/semantic_quality_findings.jsonl`
- `data/generated/reports/knowledge/semantic_quality_report.md`

该步骤只做 blocker、warning、info 分级扫描，不自动修改实体、关系、chunk、来源或发布包。后续 RAG 默认可信集合应优先使用 `lifecycle_status=approved` 且无 blocker 的实体。

## 阶段五标准化出口

阶段五在现有 JSONL、CSV 和 SQLite 发布包之外生成 JSON-LD、SKOS、PROV-O 与 Turtle 派生出口。正式出口保持确定性；模型只生成 `pending_review` 映射候选，未经人工审计和显式应用不会影响发布结果。

```bash
python3 -m bgpkb.pipeline.build_standard_mapping_candidates --provider mock
python3 -m bgpkb.pipeline.build_standard_mapping_decision_audit
python3 -m bgpkb.pipeline.apply_standard_mapping_decisions
python3 -m bgpkb.pipeline.build_standard_exports
```

显式应用已批准映射时才使用：

```bash
python3 -m bgpkb.pipeline.apply_standard_mapping_decisions --write
```

主要输出：

- `data/published/entity_catalog.jsonld`
- `data/published/source_catalog.jsonld`
- `data/published/provenance_map.jsonl`
- `data/published/standard_exports/bgp_knowledge_sample.ttl`
- `data/derived/datasets/standard_mapping_candidates.jsonl`
- `data/generated/reports/publishing/standardization_report.md`

## 阶段验收 Agent

`src/bgpkb/pipeline/run_stage_acceptance.py` 提供效果导向的阶段验收 Agent。它不会只输出“测试通过”，还会给出本阶段实际新增能力、使用者现在能做什么、后续阶段能依赖什么，以及仍需人工处理的语义事项。

阶段验收配置位于 `metadata/config/stage_acceptance_gates.yaml`。运行阶段一验收：

```bash
python3 -m bgpkb.pipeline.run_stage_acceptance --stage phase_1_data_management_v1
```

运行阶段二验收：

```bash
python3 -m bgpkb.pipeline.run_stage_acceptance --stage phase_2_lifecycle_metadata_v1
```

运行阶段三验收：

```bash
python3 -m bgpkb.pipeline.run_stage_acceptance --stage phase_3_semantic_quality_v1
```

运行阶段五验收：

```bash
python3 -m bgpkb.pipeline.run_stage_acceptance --stage phase_5_standard_exports_v1
```

输出：

- `data/reports/gates/stage_acceptance_report.md`
- `data/derived/datasets/stage_acceptance_results.jsonl`

验收结论分为：

- `pass`：确定性证据足够，阶段通过。
- `fail`：文件、命令、报告或质量门禁失败。
- `needs_human`：存在阻塞性人工判断事项。

阶段验收报告必须包含“效果验收”章节，用于回答：

1. 这个阶段新增了什么能力？
2. 使用者现在能做什么？
3. 后续阶段能依赖什么？

发布完整性校验结果写入 `data/reports/gates/published_integrity_report.md` 和 `data/published/integrity_summary.json`。该校验会比较发布 manifest、SQLite 表计数、治理数据集、查询样例和边界标记。

知识库就绪度报告写入 `data/reports/gates/readiness_report.md` 和 `data/published/readiness_summary.json`，用于把 `context.md` 中的目标产物映射到当前可验证证据。

数据字典写入 `data/reports/reference/data_dictionary_report.md` 和 `data/published/data_dictionary.json`，用于说明 published 文件、SQLite 表结构、JSONL 字段和查询命令。

质量检查会覆盖：

- 来源清单、raw、parsed、cleaned 的一致性。
- Parsed 文档 JSON 的顶层字段、章节字段、来源路径和 `doc_id` 一致性。
- Cleaned Markdown 的标题、正文、parsed 对应关系、manual note 例外和替换字符检查。
- JSONL 语法、实体 ID、chunk ID、关系引用。
- Source、ParsedDocument、Chunk、实体、关系和案例观察值的 JSON Schema 子集校验。
- 来源处理状态与制品清单的 JSON Schema 子集校验。
- 来源缺口队列的未完成来源覆盖、source_id、处理状态和 gap_id 校验。
- 实体复核队列的 pending 覆盖、来源状态、entity_id、entity_type 和建议动作校验。
- 人工复核工作簿、输入校验、会话队列、状态、逐字段清单、来源矩阵、任务板、交接清单和决策模板的一致性校验。
- 术语表的实体覆盖、term_id、entity_id、entity_type 和来源引用校验。
- 关系重复边、关系来源引用和 confidence 范围。
- 案例观察值数据集的字段、来源引用和重复键。
- 制品清单的路径覆盖、文件大小、行数和 SHA-256 一致性。

## 当前处理边界

- PDF 只做确定性文本抽取和按页切分，不做论文方法、案例角色、证据强度或影响范围等语义判断。
- YAML/OpenAPI schema 只按顶层键做机械分段，不做 API 语义归纳。
- 来源缺口队列只把未完成来源转成待办动作，不自动联网归档。
- 需要 LLM 介入的语义抽取、归纳、审批和关系推断全部跳过，并记录在 `data/generated/reports/knowledge/llm_processing_skip_report.md`。
- `data/knowledge/entities/*.jsonl` 中的 `pending` 不会被脚本自动升级为 `approved`。
- 实体复核队列只用于整理待审实体和来源状态，不替代人工审批。
- `data/review_inputs/human_review_decisions.csv` 是稳定人工输入；流水线只审计它，不覆盖它，也不自动应用其中的状态变更。
- 案例观察值只作为规则化数据集保存到 `data/derived/datasets/case_observations.*`，不会自动写入 `data/knowledge/entities/cases.jsonl`。
- 术语表只从已有实体字段机械派生，不自动推断新别名、不重写定义。
- `data/published/` 只汇总已有来源、chunk、实体、关系和复核索引，并生成本地 SQLite 查询入口；不做语义补全、不调用 LLM、不改变实体审批状态。

## MVP 目标

- 30 个 BGP 概念。
- 10 个路由机制。
- 8 个异常类型。
- 8 个数据源。
- 30 个数据字段。
- 8 个证据模板。
- 5 个论文方法。
- 5 个案例。
- 约 100 条关系。
