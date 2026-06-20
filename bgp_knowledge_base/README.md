---
title: "BGP 知识库数据准备"
document_type: "目录入口说明"
purpose: "说明 BGP 知识库数据准备目录的目标、范围、结构和统一运行入口，帮助快速理解仓库内容。"
scope: "知识库根目录"
status: "现行入口"
last_reviewed: "2026-06-19"
---
# BGP 知识库数据准备

这个目录用于把 BGP 领域资料整理成可追溯、可维护、可扩展的数据底座。当前阶段不实现 RAG、Agent 工作流或业务系统集成。

## 文档入口

当前 Markdown 已按用途归并到以下入口：

| 入口 | 用途 |
| --- | --- |
| [docs/README.md](docs/README.md) | 规划、治理、项目上下文和目录导航的归并索引。 |
| [docs/rules/document_crud_rules_v1.md](docs/rules/document_crud_rules_v1.md) | Markdown 文档 CRUD 与自动校验规则。 |
| [reports/README.md](reports/README.md) | 阶段报告、质量报告、发布报告和人工复核报告的归并索引。 |
| [cleaned/README.md](cleaned/README.md) | 清洗后的标准、数据源、论文、案例语料归并索引。 |
| [published/README.md](published/README.md) | 可交付发布包、SQLite、JSONL 和查询入口。 |

## 目标

构建一条可复跑的数据准备链路：

```text
raw sources -> parsed text -> cleaned text -> knowledge chunks -> structured entities -> relationships -> quality reports
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
config/          分类体系、实体类型、来源类型、质量规则
raw/             不可变原始资料
parsed/          从 TXT/HTML/YAML/PDF 等原始资料解析出的结构化文本
cleaned/         清洗后的 Markdown 文本
chunks/          JSONL 知识片段与人工 seed chunks
entities/        JSONL 结构化领域实体
relationships/   JSONL 实体关系图
published/       可交付知识库入口、目录、索引、SQLite 数据库和发布 manifest
schemas/         JSON Schema
inventory/       来源登记表
datasets/        规则化派生数据集
review_inputs/   人工填写的复核决策输入与可再生成模板
reports/         摄取、解析、覆盖、质量和跳过记录
scripts/         本地解析、切分、抽取和校验脚本
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

机器可读版本维护在 `config/storage_formats.yaml`。

## 确定性流水线

推荐统一运行：

```bash
python3 scripts/run_pipeline.py
```

该命令会按顺序执行：

1. `scripts/parse_documents.py`
2. `scripts/build_chunks.py`
3. `scripts/extract_case_observations.py`
4. `scripts/build_source_processing_status.py`
5. `scripts/build_source_gap_queue.py`
6. `scripts/build_entity_review_queue.py`
7. `scripts/build_entity_source_evidence.py`
8. `scripts/build_entity_review_packets.py`
9. `scripts/build_authoritative_source_requirements.py`
10. `scripts/build_next_action_queue.py`
11. `scripts/build_llm_processing_skip_report.py`
12. `scripts/build_case_observation_guides.py`
13. `scripts/build_human_review_workbook.py`
14. `scripts/build_human_review_decision_template.py`
15. `scripts/build_human_review_input_validation.py`
16. `scripts/build_human_review_decision_audit.py`
17. `scripts/apply_human_review_decisions.py`
18. `scripts/build_human_review_progress.py`
19. `scripts/build_human_review_evidence_extracts.py`
20. `scripts/build_human_review_session_queue.py`
21. `scripts/build_human_review_session_status.py`
22. `scripts/build_human_review_field_checklist.py`
23. `scripts/build_human_review_source_matrix.py`
24. `scripts/build_human_review_task_board.py`
25. `scripts/build_human_review_handoff.py`
26. `scripts/build_human_review_session_decision_templates.py`
27. `scripts/build_human_review_session_guides.py`
28. `scripts/build_human_review_guides.py`
29. `scripts/build_glossary.py`
30. `scripts/build_published_knowledge_base.py`
31. `scripts/build_sqlite_knowledge_base.py`
32. `scripts/build_query_examples.py`
33. `scripts/build_published_integrity_report.py`
34. `scripts/build_readiness_report.py`
35. `scripts/build_data_dictionary.py`
36. `scripts/build_coverage_report.py`
37. `scripts/build_data_management_report.py`
38. `scripts/build_lifecycle_report.py`
39. `scripts/build_semantic_quality_report.py`
40. `scripts/build_artifact_manifest.py`
41. `scripts/quality_check.py`

运行结果写入 `reports/pipeline_report.md`。

## 人工复核决策流程

流水线会生成 `review_inputs/human_review_decisions_template.csv` 作为可参考模板，并只在 `review_inputs/human_review_decisions.csv` 不存在时初始化表头。人工填写文件不会被流水线覆盖。

人工复核 pending 实体时：

1. 参考 `reports/human_review_task_board_report.md` 查看下一步任务板；需要交接清单时看 `reports/human_review_handoff_report.md` 和 `datasets/human_review_handoff.csv`，需要 session 细节时看 `reports/human_review_session_guides/`，需要 session 完成率和下一条实体时看 `reports/human_review_session_status_report.md`，需要逐字段核验项时看 `reports/human_review_field_checklist_report.md` 和 `datasets/human_review_field_checklist.csv`，需要按来源批量核验时看 `reports/human_review_source_matrix_report.md` 和 `datasets/human_review_source_matrix.csv`，需要逐 session 填写参考时看 `review_inputs/human_review_session_decision_templates/`，需要表格视图时看 `datasets/human_review_session_queue.csv`。
2. 在 `review_inputs/human_review_decisions.csv` 填写 `entity_id`、`review_decision`、`reviewer`、`reviewed_at` 和 `decision_note`。
3. 只使用 `approved`、`rejected`、`needs_source`、`needs_semantic_review`；留空或 `unreviewed` 表示不应用。
4. 如果先填写了逐 session 模板，可先运行 `python3 scripts/import_human_review_session_decisions.py --session-id review_session_001` 做 dry-run；确认无误后显式加 `--write` 合并到主决策文件。
5. 运行 `python3 scripts/build_human_review_input_validation.py` 校验主决策输入结构，检查 `reports/human_review_input_validation_report.md`。
6. 运行 `python3 scripts/build_human_review_decision_audit.py` 审计输入，检查 `reports/human_review_decision_audit_report.md`。
7. 运行 `python3 scripts/build_human_review_progress.py` 查看 `reports/human_review_progress_report.md` 中的分组进度。
8. 运行 `python3 scripts/build_human_review_evidence_extracts.py` 查看 `datasets/human_review_evidence_extracts.*` 中的 chunk 摘录；摘录只用于定位，不代表自动批准依据。
9. 运行 `python3 scripts/build_human_review_session_queue.py`、`python3 scripts/build_human_review_session_status.py`、`python3 scripts/build_human_review_field_checklist.py`、`python3 scripts/build_human_review_source_matrix.py`、`python3 scripts/build_human_review_task_board.py`、`python3 scripts/build_human_review_handoff.py`、`python3 scripts/build_human_review_session_decision_templates.py` 和 `python3 scripts/build_human_review_session_guides.py` 更新小批次队列、会话状态、逐字段清单、来源矩阵、任务板、交接清单、会话模板与分会话指南，继续从下一个 session 处理。
10. 确认无误后，先运行 `python3 scripts/apply_human_review_decisions.py` 查看 dry-run 应用报告；确认后显式运行 `python3 scripts/apply_human_review_decisions.py --write` 应用已审计通过且不需要 LLM 的 `approved/rejected` 决策。
11. 重新运行 `python3 scripts/run_pipeline.py` 生成一致的发布包和报告。

`needs_semantic_review` 需要语义流程或 LLM，当前按规则跳过并记录，不会被应用脚本写入实体。

## 本地查询入口

发布后的 SQLite 数据库位于 `published/bgp_knowledge_base.sqlite`。可使用查询脚本查看统计、实体、来源、关系邻居、词项索引和 chunk 检索结果：

```bash
python3 scripts/query_knowledge_base.py stats
python3 scripts/query_knowledge_base.py term route --limit 5
python3 scripts/query_knowledge_base.py entity anomaly_route_leak
python3 scripts/query_knowledge_base.py source rfc4271
python3 scripts/query_knowledge_base.py neighbors concept_as_path
python3 scripts/query_knowledge_base.py evidence anomaly_route_leak
python3 scripts/query_knowledge_base.py review-packets --bucket ready_without_manual_note --limit 5
python3 scripts/query_knowledge_base.py workbook --batch 01_ready_without_manual_note --limit 5
python3 scripts/query_knowledge_base.py extracts anomaly_route_leak --limit 3
python3 scripts/query_knowledge_base.py sessions --session-id review_session_001 --limit 5
python3 scripts/query_knowledge_base.py actions --needs-llm true --limit 5
python3 scripts/query_knowledge_base.py observations --type asn --limit 5
python3 scripts/query_knowledge_base.py glossary route --limit 5
python3 scripts/query_knowledge_base.py decision-audit --status no_op --limit 5
python3 scripts/query_knowledge_base.py apply-preview --record-type summary --limit 5
python3 scripts/query_knowledge_base.py input-validation --status pass --limit 5
python3 scripts/query_knowledge_base.py progress --scope-type overall --limit 5
python3 scripts/query_knowledge_base.py field-checks --session-id review_session_001 --limit 5
python3 scripts/query_knowledge_base.py source-matrix --source-id rfc4271 --limit 5
python3 scripts/query_knowledge_base.py task-board --type review_session --limit 5
python3 scripts/query_knowledge_base.py handoff --type review_session --limit 5
python3 scripts/query_knowledge_base.py search-entities RPKI --limit 5
python3 scripts/query_knowledge_base.py search-chunks '"route leak"' --limit 5
```

固定查询验收结果写入 `reports/query_examples_report.md`，覆盖统计、词项、实体、来源、关系、证据索引、复核包、人工复核工作簿、人工复核证据摘录、人工复核会话队列、行动队列、案例观察值、术语表、决策审计、应用预览、输入校验、复核进度、逐字段清单、来源矩阵、任务板、交接清单和全文检索入口。

## 知识服务化入口

`service/` 提供一个只读 FastAPI 服务，直接读取已发布的 `published/bgp_knowledge_base.sqlite`。该服务只做查询和浏览，不生成、不修复、不覆盖流水线产物。

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
curl "http://127.0.0.1:8000/api/v1/hybrid/search?q=route%20leak&limit=5"
curl "http://127.0.0.1:8000/api/v1/hybrid/context-pack?q=%E8%B7%AF%E7%94%B1%E6%B3%84%E9%9C%B2&limit=5"
curl -X POST http://127.0.0.1:8000/api/v1/rag/answer \
  -H "Content-Type: application/json" \
  -d '{"query":"route leak","limit":3}'
```

阶段 4.2 可用真实 DeepSeek API 做冒烟验证。该脚本只从环境变量读取密钥，不把密钥写入报告或数据集：

```bash
export DEEPSEEK_API_KEY="你的 DeepSeek API key"
python3 scripts/run_rag_answer_smoke_test.py
```

输出：

- `datasets/rag_answer_smoke_test_results.jsonl`
- `reports/rag_answer_smoke_test_report.md`

阶段 4.3 提供可复跑的 RAG 答案质量评测。无 `DEEPSEEK_API_KEY` 时脚本使用离线结构检查客户端，不调用外部 API；设置密钥后可复用同一评测集做真实答案评测：

```bash
python3 scripts/run_rag_answer_eval.py
```

输出：

- `datasets/rag_answer_eval_questions.jsonl`
- `datasets/rag_answer_eval_results.jsonl`
- `reports/rag_answer_eval_report.md`

阶段 4.4 可用真实 DeepSeek API 跑同一评测集，并对失败样本做中文分析。真实评测脚本要求显式设置 `DEEPSEEK_API_KEY`；失败分析脚本不读取密钥，可在 CI 或本地离线复跑：

```bash
export DEEPSEEK_API_KEY="你的 DeepSeek API key"
python3 scripts/run_deepseek_rag_answer_eval.py
python3 scripts/build_rag_answer_failure_analysis.py
```

输出：

- `datasets/deepseek_rag_answer_eval_results.jsonl`
- `reports/deepseek_rag_answer_eval_report.md`
- `reports/rag_answer_failure_analysis_report.md`

阶段 4.5 使用远程 BGE-M3、关键词和元数据做 RRF 混合检索。默认远程 provider 是 SiliconFlow `BAAI/bge-m3`；当前设备不运行或下载模型。无 key 时 embedding 构建会生成结构化 `skipped` manifest，CLI、API、离线 mock 向量和检索评测仍可运行：

```bash
# 无 key：验证框架、边界和离线检索基线
python3 scripts/build_bge_m3_index.py
python3 scripts/query_hybrid_rag.py search "路由泄露" --top-k 5
python3 scripts/query_hybrid_rag.py context-pack "route leak" --top-k 8
python3 scripts/run_hybrid_retrieval_eval.py

# 有 SiliconFlow key：构建真实 BGE-M3 文件化向量索引
set -a
source .env
set +a
python3 scripts/build_bge_m3_index.py --provider siliconflow_bge_m3

# 阿里云 PAI/EAS 兼容路径
export ALIYUN_BGE_M3_ENDPOINT="你的 EAS endpoint"
export ALIYUN_BGE_M3_API_KEY="你的 EAS token"
python3 scripts/build_bge_m3_index.py --provider aliyun_eas_bge_m3
```

本地 `.env` 已被根目录 `.gitignore` 排除。运行 pipeline、阶段验收或服务前都可以先执行 `set -a; source .env; set +a`，让子进程继承远程 API 配置。

阶段 4.5 输入数据限定为：`published/chunk_catalog.jsonl`、`published/entity_catalog.jsonl`、`datasets/glossary.jsonl` 和 `entities/evidence_templates.jsonl`。不直接 embedding `raw/` 或整份 `cleaned/` 文件。

输出：

- `published/bge_m3_embedding_manifest.json`
- 配置真实 key 后生成 `published/bge_m3_vector_index.jsonl`
- `reports/bge_m3_embedding_report.md`
- `datasets/hybrid_retrieval_eval_results.jsonl`
- `reports/hybrid_retrieval_eval_report.md`

自动化测试：

```bash
pytest tests -v
```

当前服务边界：

- 只读访问 SQLite，缺失数据库时通过 `/health` 和 API 错误返回清晰状态。
- 阶段 4.1 提供 `POST /api/v1/rag/answer`，只做检索、context pack 和可追溯答案编排。
- 阶段 4.5 提供 `/api/v1/hybrid/search` 和 `/api/v1/hybrid/context-pack`，RAG Answer 复用同一混合检索 context pack。
- DeepSeek API 只从环境变量 `DEEPSEEK_API_KEY` 读取密钥；仓库只提供 `.env.example`，不保存真实密钥。
- 当前设备不运行本地模型；`config/rag_retrieval.yaml` 中 `embedding.local_model_enabled=false`，BGE-M3 只调用远程 provider，Qwen embedding 只预留后续部署字段。
- LLM 不可用或没有证据时不会编造答案，会返回检索证据、引用和失败状态。
- 不提供编辑、审批、写入、导出、权限系统或知识库自动改写能力。
- API 返回结构尽量贴近 `scripts/query_knowledge_base.py` 的 JSON 输出，方便后续迁移和集成。

阶段 4.1 RAG Answer API 最小响应字段：

- `answer_status`：`answered`、`llm_unavailable` 或 `no_evidence`。
- `generated`：是否由 LLM 生成最终答案。
- `citations`：生成或兜底响应所依据的来源引用。
- `context_pack`：检索命中的 chunk、引用和策略排除项。
- `guardrails`：只读、引用必需、本地模型禁用和禁止写回等边界。

## 数据管理体系

阶段一数据管理体系文档位于 `docs/governance/data_management_v1.md`，用于说明 BGP KB 的数据资产清单、数据模型标准、元数据与溯源、质量治理、生命周期、服务化访问和标准化出口。

机器可读能力清单位于 `config/data_management_capabilities.yaml`。可运行以下命令生成当前数据管理能力盘点报告：

```bash
python3 scripts/build_data_management_report.py
```

报告输出到 `reports/data_management_report.md`，用于查看各类资产和治理能力的状态、证据覆盖和下一步缺口。

## 生命周期与元数据治理

阶段二生命周期治理文档位于 `docs/governance/lifecycle_metadata_v1.md`，用于把实体从单一 `review_status` 扩展为 `draft -> candidate -> reviewed -> approved -> deprecated -> archived` 的治理视图。

机器可读策略位于 `config/lifecycle_policy.yaml`。可运行以下命令生成实体级生命周期清单和治理报告：

```bash
python3 scripts/build_lifecycle_report.py
```

输出：

- `datasets/lifecycle_inventory.jsonl`
- `reports/lifecycle_report.md`

该步骤只读取现有实体、来源证据、复核包、行动队列和人工决策审计，不修改实体、关系、chunk 或发布包。

## 语义质量治理

阶段三语义质量治理文档位于 `docs/governance/semantic_quality_v1.md`，用于把结构质量检查扩展为跨实体语义一致性扫描。

机器可读规则位于 `config/semantic_quality_rules.yaml`。可运行以下命令生成语义质量 findings 和报告：

```bash
python3 scripts/build_semantic_quality_report.py
```

输出：

- `datasets/semantic_quality_findings.jsonl`
- `reports/semantic_quality_report.md`

该步骤只做 blocker、warning、info 分级扫描，不自动修改实体、关系、chunk、来源或发布包。后续 RAG 默认可信集合应优先使用 `lifecycle_status=approved` 且无 blocker 的实体。

## 阶段验收 Agent

`scripts/run_stage_acceptance.py` 提供效果导向的阶段验收 Agent。它不会只输出“测试通过”，还会给出本阶段实际新增能力、使用者现在能做什么、后续阶段能依赖什么，以及仍需人工处理的语义事项。

阶段验收配置位于 `config/stage_acceptance_gates.yaml`。运行阶段一验收：

```bash
python3 scripts/run_stage_acceptance.py --stage phase_1_data_management_v1
```

运行阶段二验收：

```bash
python3 scripts/run_stage_acceptance.py --stage phase_2_lifecycle_metadata_v1
```

运行阶段三验收：

```bash
python3 scripts/run_stage_acceptance.py --stage phase_3_semantic_quality_v1
```

输出：

- `reports/stage_acceptance_report.md`
- `datasets/stage_acceptance_results.jsonl`

验收结论分为：

- `pass`：确定性证据足够，阶段通过。
- `fail`：文件、命令、报告或质量门禁失败。
- `needs_human`：存在阻塞性人工判断事项。

阶段验收报告必须包含“效果验收”章节，用于回答：

1. 这个阶段新增了什么能力？
2. 使用者现在能做什么？
3. 后续阶段能依赖什么？

发布完整性校验结果写入 `reports/published_integrity_report.md` 和 `published/integrity_summary.json`。该校验会比较发布 manifest、SQLite 表计数、治理数据集、查询样例和边界标记。

知识库就绪度报告写入 `reports/readiness_report.md` 和 `published/readiness_summary.json`，用于把 `context.md` 中的目标产物映射到当前可验证证据。

数据字典写入 `reports/data_dictionary_report.md` 和 `published/data_dictionary.json`，用于说明 published 文件、SQLite 表结构、JSONL 字段和查询命令。

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
- 需要 LLM 介入的语义抽取、归纳、审批和关系推断全部跳过，并记录在 `reports/llm_processing_skip_report.md`。
- `entities/*.jsonl` 中的 `pending` 不会被脚本自动升级为 `approved`。
- 实体复核队列只用于整理待审实体和来源状态，不替代人工审批。
- `review_inputs/human_review_decisions.csv` 是稳定人工输入；流水线只审计它，不覆盖它，也不自动应用其中的状态变更。
- 案例观察值只作为规则化数据集保存到 `datasets/case_observations.*`，不会自动写入 `entities/cases.jsonl`。
- 术语表只从已有实体字段机械派生，不自动推断新别名、不重写定义。
- `published/` 只汇总已有来源、chunk、实体、关系和复核索引，并生成本地 SQLite 查询入口；不做语义补全、不调用 LLM、不改变实体审批状态。

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
