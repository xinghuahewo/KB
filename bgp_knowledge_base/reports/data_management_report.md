# 数据管理能力报告

## 范围

本报告基于 `config/data_management_capabilities.yaml` 生成，用于盘点 BGP KB 数据资产、治理能力、证据覆盖和下一步缺口。

该步骤不联网、不下载、不调用 LLM，不修改实体、关系、chunk 或发布包。

## 摘要

- 配置版本：`data_management_v1`
- 数据资产组数：14
- 能力模块数：10
- 证据缺失数：0

## 状态统计

| 状态 | 数量 |
| --- | ---: |
| 已完成 (`achieved`) | 18 |
| 部分完成 (`partial`) | 6 |
| 已规划 (`planned`) | 0 |
| 未开始 (`not_started`) | 0 |
| 暂缓 (`deferred`) | 0 |

## 数据资产清单

| 资产组 | 状态 | 说明 | 主要路径 | 证据缺失数 |
| --- | --- | --- | --- | ---: |
| 实体 (`entities`) | 已完成 | BGP 概念、异常类型、数据源、数据字段、证据模板、案例、论文方法和路由机制等结构化实体。 | `entities/*.jsonl`<br>`published/entity_catalog.jsonl` | 0 |
| 关系 (`relationships`) | 已完成 | 实体之间的有向关系边，包含关系类型、两端实体类型、置信度和来源引用。 | `relationships/relationships.jsonl`<br>`published/relationship_adjacency.json` | 0 |
| source (`sources`) | 已完成 | BGP 资料来源登记表，覆盖论文、标准、案例报告、数据文档和项目上下文。 | `inventory/sources.csv`<br>`published/source_catalog.jsonl` | 0 |
| chunk (`chunks`) | 已完成 | 从清洗文本和人工 seed 中生成的知识片段，是检索、证据摘录和发布索引的基础。 | `chunks/*.jsonl`<br>`published/chunk_catalog.jsonl` | 0 |
| 术语表 (`glossary`) | 已完成 | 从已有实体机械派生的术语表，服务查询、浏览和后续检索增强。 | `datasets/glossary.jsonl`<br>`datasets/glossary.csv` | 0 |
| 证据模板 (`evidence_templates`) | 已完成 | 面向异常类型判断的 required evidence、optional evidence 和 false positive checks。 | `entities/evidence_templates.jsonl`<br>`published/entity_catalog.jsonl` | 0 |
| 案例 (`cases`) | 部分完成 | BGP 历史案例和机械抽取的案例观察值，事件角色、影响范围和证据强度仍需语义复核。 | `entities/cases.jsonl`<br>`datasets/case_observations.jsonl`<br>`datasets/case_observations.csv` | 0 |
| 人工复核工作簿 (`human_review_workbook`) | 已完成 | 面向实体人工复核的工作簿、会话队列和字段核验入口。 | `datasets/human_review_workbook.jsonl`<br>`datasets/human_review_workbook.csv` | 0 |
| 行动队列 (`next_action_queue`) | 已完成 | 汇总实体复核、来源补充和语义跳过事项的下一步行动队列。 | `datasets/next_action_queue.jsonl`<br>`datasets/next_action_queue.csv` | 0 |
| 语义质量 findings (`semantic_quality`) | 已完成 | 语义一致性扫描输出的问题清单和报告，覆盖 blocker、warning、info 分级以及 RAG 默认可信集合影响。 | `datasets/semantic_quality_findings.jsonl`<br>`reports/semantic_quality_report.md` | 0 |
| 语义标识前置层 (`semantic_identity`) | 已完成 | 阶段三点五新增的 bgpkb 命名空间、URI 规则、JSON-LD context 和稳定 ID 映射。 | `config/semantic_identity.yaml`<br>`published/jsonld_context.json`<br>`published/semantic_id_map.jsonl`<br>`reports/semantic_identity_report.md` | 0 |
| RAG 检索框架 (`rag_retrieval_framework`) | 已完成 | 阶段四在当前设备不运行模型条件下建立的完整 RAG 框架，包含 provider 配置、候选增强、mock embedding、检索索引、context pack 和 API。 | `config/rag_retrieval.yaml`<br>`config/llm_candidate_enrichment.yaml`<br>`datasets/chunk_enrichment_candidates.jsonl`<br>`datasets/entity_link_candidates.jsonl`<br>`datasets/rag_query_eval.jsonl`<br>`published/embedding_manifest.json`<br>`published/rag_mock_vector_index.jsonl`<br>`published/rag_retrieval_index.json`<br>`reports/rag_readiness_report.md` | 0 |
| 发布包 (`published_package`) | 已完成 | 面向下游查询和集成的 JSONL、JSON、SQLite 和 manifest 发布目录。 | `published/`<br>`published/manifest.json`<br>`published/bgp_knowledge_base.sqlite` | 0 |
| 服务化 API (`service_api`) | 已完成 | 基于 FastAPI 的只读知识服务，提供 API、OpenAPI 和简单 HTML 浏览页。 | `service/`<br>`tests/test_service_api.py` | 0 |

## 数据资产清单

- 状态：已完成
- 能力 ID：`data_asset_inventory`
- 说明：核心数据资产已在文件、发布包和报告中具备可盘点入口。

| 证据 | 状态 |
| --- | --- |
| `inventory/sources.csv` | 存在 |
| `reports/artifact_manifest_report.md` | 存在 |
| `published/manifest.json` | 存在 |

后续动作：
- 将新增资产统一登记到 data_management_capabilities.yaml。

## 数据模型标准覆盖

- 状态：部分完成
- 能力 ID：`data_model_standards`
- 说明：JSON Schema、实体类型、主题分类和阶段三点五语义标识层已存在，但跨类型关系约束和集中 required fields 说明仍待补充。

| 证据 | 状态 |
| --- | --- |
| `schemas/` | 存在 |
| `config/entity_types.yaml` | 存在 |
| `config/topic_taxonomy.yaml` | 存在 |
| `config/semantic_identity.yaml` | 存在 |

后续动作：
- 建立关系两端类型约束。
- 建立集中 required fields 说明。

## 元数据与溯源覆盖

- 状态：部分完成
- 能力 ID：`metadata_lineage`
- 说明：source、raw、parsed、cleaned、chunk、entity 的链路已经存在，统一 extracted_at、reviewed_by、approved_at 字段待阶段二补齐。

| 证据 | 状态 |
| --- | --- |
| `datasets/entity_source_evidence.jsonl` | 存在 |
| `reports/entity_source_evidence_report.md` | 存在 |
| `published/source_catalog.jsonl` | 存在 |

后续动作：
- 在生命周期阶段补齐统一审核和时间字段。

## 质量治理能力

- 状态：部分完成
- 能力 ID：`quality_governance`
- 说明：结构质量检查已较完整，语义质量扫描已建立，后续仍需扩展更多领域规则和有效期策略。

| 证据 | 状态 |
| --- | --- |
| `reports/quality_report.md` | 存在 |
| `reports/published_integrity_report.md` | 存在 |
| `reports/semantic_quality_report.md` | 存在 |

后续动作：
- 扩展更多跨实体语义规则。
- 新增更细的 validity period 来源时效策略。

## 生命周期现状

- 状态：已完成
- 能力 ID：`lifecycle`
- 说明：已建立 draft/candidate/reviewed/approved/deprecated/archived 生命周期视图，并生成实体级生命周期清单。

| 证据 | 状态 |
| --- | --- |
| `reports/lifecycle_report.md` | 存在 |
| `datasets/lifecycle_inventory.jsonl` | 存在 |
| `datasets/human_review_decision_audit.jsonl` | 存在 |

后续动作：
- 补齐 valid_from 和 valid_until 来源时效策略。
- 在后续阶段按需增加 deprecated 和 archived 显式覆盖。

## 语义质量治理能力

- 状态：已完成
- 能力 ID：`semantic_quality_governance`
- 说明：已建立确定性语义质量 findings，能分级展示跨实体语义问题、RAG 默认可信集合影响和人工复核建议。

| 证据 | 状态 |
| --- | --- |
| `config/semantic_quality_rules.yaml` | 存在 |
| `reports/semantic_quality_report.md` | 存在 |
| `datasets/semantic_quality_findings.jsonl` | 存在 |

后续动作：
- 将 blocker findings 转入人工修复或规则例外审查。
- 在 RAG 阶段默认引用无 blocker 的 approved 实体集合。

## 语义标识治理

- 状态：已完成
- 能力 ID：`semantic_identity_governance`
- 说明：已建立 bgpkb 命名空间、稳定 URI 规则、JSON-LD context 和字段映射草案，供 RAG 与标准化出口复用。

| 证据 | 状态 |
| --- | --- |
| `docs/governance/semantic_identity_v1.md` | 存在 |
| `config/semantic_identity.yaml` | 存在 |
| `reports/semantic_identity_report.md` | 存在 |
| `published/jsonld_context.json` | 存在 |
| `published/semantic_id_map.jsonl` | 存在 |

后续动作：
- 在阶段四 RAG context pack 中引用 semantic_id_map 的 @id。
- 在阶段五继续扩展 SKOS、PROV-O 和 RDF 导出。

## RAG 检索框架

- 状态：已完成
- 能力 ID：`rag_retrieval`
- 说明：已建立离线可验收的 RAG 框架，默认使用 mock provider、SQLite FTS5 和稳定 @id；DeepSeek、Qwen/vLLM、BGE-M3 和 Milvus 真实路径保留但默认禁用。

| 证据 | 状态 |
| --- | --- |
| `config/rag_retrieval.yaml` | 存在 |
| `config/llm_candidate_enrichment.yaml` | 存在 |
| `reports/rag_readiness_report.md` | 存在 |
| `published/rag_retrieval_index.json` | 存在 |

后续动作：
- 在有模型设备后显式启用 BGE-M3 与 Milvus，不运行模型的默认 mock 流水线必须保持通过。
- 在具备 API key 后显式启用 DeepSeek 候选增强，并保持候选 pending_review 边界。
- 后续用 Qwen/vLLM OpenAI-compatible endpoint 替换 DeepSeek provider。

## 服务化访问现状

- 状态：部分完成
- 能力 ID：`service_access`
- 说明：SQLite、FTS、CLI、REST API、HTML 浏览页和 RAG retrieval API 已具备；真实向量库和模型运行留待具备部署环境后启用。

| 证据 | 状态 |
| --- | --- |
| `published/bgp_knowledge_base.sqlite` | 存在 |
| `scripts/query_knowledge_base.py` | 存在 |
| `service/app.py` | 存在 |
| `scripts/query_rag.py` | 存在 |

后续动作：
- 在模型设备上启用 BGE-M3 和 Milvus。
- 对比真实 hybrid retrieval 与当前 mock/FTS baseline。

## 标准化出口现状

- 状态：部分完成
- 能力 ID：`standard_exports`
- 说明：JSONL、JSON、CSV、SQLite 和轻量 JSON-LD context 已具备，RDF、完整 SKOS/PROV-O、STIX/MISP 尚未建设。

| 证据 | 状态 |
| --- | --- |
| `published/` | 存在 |
| `datasets/` | 存在 |
| `published/jsonld_context.json` | 存在 |

后续动作：
- 在阶段五补充实体级 JSON-LD 样例出口。
- 再扩展完整 SKOS 和 PROV-O 映射。

## 缺口与下一步建议

- 案例：部分完成。BGP 历史案例和机械抽取的案例观察值，事件角色、影响范围和证据强度仍需语义复核。
- 数据模型标准：部分完成。JSON Schema、实体类型、主题分类和阶段三点五语义标识层已存在，但跨类型关系约束和集中 required fields 说明仍待补充。
  - 下一步：建立关系两端类型约束。
  - 下一步：建立集中 required fields 说明。
- 元数据与溯源：部分完成。source、raw、parsed、cleaned、chunk、entity 的链路已经存在，统一 extracted_at、reviewed_by、approved_at 字段待阶段二补齐。
  - 下一步：在生命周期阶段补齐统一审核和时间字段。
- 质量治理：部分完成。结构质量检查已较完整，语义质量扫描已建立，后续仍需扩展更多领域规则和有效期策略。
  - 下一步：扩展更多跨实体语义规则。
  - 下一步：新增更细的 validity period 来源时效策略。
- 服务化访问：部分完成。SQLite、FTS、CLI、REST API、HTML 浏览页和 RAG retrieval API 已具备；真实向量库和模型运行留待具备部署环境后启用。
  - 下一步：在模型设备上启用 BGE-M3 和 Milvus。
  - 下一步：对比真实 hybrid retrieval 与当前 mock/FTS baseline。
- 标准化出口：部分完成。JSONL、JSON、CSV、SQLite 和轻量 JSON-LD context 已具备，RDF、完整 SKOS/PROV-O、STIX/MISP 尚未建设。
  - 下一步：在阶段五补充实体级 JSON-LD 样例出口。
  - 下一步：再扩展完整 SKOS 和 PROV-O 映射。
