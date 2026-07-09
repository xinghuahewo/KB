---
title: "BGP KB 数据管理体系 v1"
document_type: "规划与治理文档"
purpose: "说明BGP KB 数据管理体系 v1的设计目标、治理边界和执行约束，供后续维护与阶段复核参考。"
scope: "知识库规划、治理与开发说明"
status: "现行参考"
last_reviewed: "2026-06-19"
---
# BGP KB 数据管理体系 v1

## 1. 设计目标

BGP KB 数据管理体系 v1 用于把当前知识库从“文件和脚本集合”整理为可盘点、可审计、可演进的数据资产体系。它借鉴 DAMA-DMBOK 的数据管理思想，但不照搬企业级组织流程；本项目优先解决知识库工程中最关键的七件事：

- 数据资产在哪里。
- 数据模型如何约束。
- 元数据和溯源是否完整。
- 质量检查覆盖到哪一层。
- 数据生命周期目前处于什么阶段。
- 服务化访问能力有哪些。
- 标准化出口如何逐步演进。

本体系是现有流水线之上的治理层，不替代 `src/bgpkb/pipeline/run_pipeline.py`，不重排现有目录，也不改变 `data/knowledge/entities/`、`data/corpus/chunks/`、`data/knowledge/relationships/`、`data/published/` 的当前数据格式。

## 2. 数据资产清单

当前 BGP KB 的核心数据资产包括：

| 资产 | 当前位置 | 发布出口 | 当前状态 |
| --- | --- | --- | --- |
| 实体 | `data/knowledge/entities/*.jsonl` | `data/published/entity_catalog.jsonl`、SQLite `entities` | 已建立 |
| 关系 | `data/knowledge/relationships/relationships.jsonl` | `data/published/relationship_adjacency.json`、SQLite `relationships` | 已建立 |
| source | `data/sources/inventory/sources.csv` | `data/published/source_catalog.jsonl`、SQLite `sources` | 已建立 |
| chunk | `data/corpus/chunks/*.jsonl` | `data/published/chunk_catalog.jsonl`、SQLite `chunks` | 已建立 |
| 术语表 | `data/derived/datasets/glossary.*` | SQLite `glossary` | 已建立 |
| 证据模板 | `data/knowledge/entities/evidence_templates.jsonl` | `data/published/entity_catalog.jsonl`、SQLite `entities` | 已建立 |
| 案例 | `data/knowledge/entities/cases.jsonl`、`data/derived/datasets/case_observations.*` | SQLite `entities`、`case_observations` | 已建立，语义字段仍需复核 |
| 人工复核工作簿 | `data/derived/datasets/human_review_workbook.*` | SQLite `human_review_workbook` | 已建立 |
| 行动队列 | `data/derived/datasets/next_action_queue.*` | SQLite `next_actions` | 已建立 |
| 发布包 | `data/published/` | JSONL/JSON/SQLite | 已建立 |
| 服务化 API | `src/bgpkb/service/` | FastAPI/OpenAPI | 已建立 |

资产清单的机器可读版本维护在 `metadata/config/data_management_capabilities.yaml`，自动盘点报告由 `src/bgpkb/pipeline/build_data_management_report.py` 生成。

## 3. 数据模型标准

当前项目已经具备以下模型标准：

- `metadata/schemas/` 中维护实体、来源、关系、chunk、复核队列、治理数据集等 JSON Schema。
- `metadata/config/entity_types.yaml` 定义实体类型。
- `metadata/config/topic_taxonomy.yaml` 定义主题分类。
- `metadata/config/source_types.yaml` 定义来源类型。
- `metadata/config/storage_formats.yaml` 定义各层存储格式。

当前不足：

- 命名规范仍分散在数据和脚本中，尚未形成集中规则。
- 跨实体类型关系约束尚未机器化。
- 必填字段规则主要依赖 schema 和质量脚本，尚未形成统一的人读说明。

下一阶段应补充命名规范、字段规范和关系约束规则，但阶段一只做盘点，不改变模型。

## 4. 元数据与溯源

当前项目已经保留较完整的溯源链：

```text
source
  -> raw file
  -> parsed document
  -> cleaned markdown
  -> chunk
  -> entity / relationship / evidence
```

已有关键字段包括：

- `source_ref`
- `source_id`
- `chunk_id`
- `raw path`
- `parsed_path`
- `cleaned_path`
- `source_refs`
- `review_status`

当前不足：

- `extracted_at` 未在所有资产中统一。
- `reviewed_by`、`reviewed_at`、`approved_at` 尚未成为实体统一字段。
- `valid_from`、`valid_until` 等时间有效性字段尚未进入通用模型。

这些缺口应在阶段二“生命周期与元数据治理”中处理。

## 5. 质量治理

当前质量治理已覆盖结构完整性，主要包括：

- JSON 语法检查。
- JSON Schema 子集检查。
- 重复 ID 检查。
- orphan reference 检查。
- source、raw、parsed、cleaned、chunk 一致性检查。
- 关系引用检查。
- 制品清单校验。
- 发布完整性校验。

主要证据：

- `data/reports/gates/quality_report.md`
- `data/reports/gates/published_integrity_report.md`
- `data/published/integrity_summary.json`

当前不足：

- 语义一致性检查仍不足。
- validity period check 尚未建立。
- assertion-level confidence 尚未进入通用模型。

阶段三应新增 `semantic_quality_report`，把质量治理从“结构正确”扩展到“语义一致”。

## 6. 生命周期

当前项目主要使用 `review_status` 表达审核状态，典型值包括：

- `pending`
- `approved`

人工复核体系已经具备工作簿、证据摘录、会话队列、任务板、交接清单和决策审计，但生命周期模型仍偏粗。

建议后续扩展为：

```text
draft -> candidate -> reviewed -> approved -> deprecated -> archived
```

阶段一只记录该缺口，不新增生命周期字段。

## 7. 服务化访问

当前已具备以下访问方式：

- 文件化访问：JSONL、JSON、CSV。
- SQLite 查询：`data/published/bgp_knowledge_base.sqlite`。
- FTS 查询：实体和 chunk 全文检索。
- CLI 查询：`src/bgpkb/pipeline/query_knowledge_base.py`。
- REST API：`src/bgpkb/service/app.py`。
- 简单 HTML 浏览页：`src/bgpkb/service/templates/`。

当前不足：

- 尚无 vector index。
- 尚无 RAG context-pack 接口。
- 尚无稳定 SDK。

服务化访问的下一步应是混合检索和 RAG 就绪。

## 8. 标准化出口

当前已具备：

- JSONL。
- JSON。
- CSV。
- SQLite。
- JSON-LD `@context`、实体目录和来源目录。
- SKOS 概念映射。
- PROV-O 加工与来源主链。
- RDF/Turtle 样例。

按实际对接需求后置：

- 全量 RDF 发布包。
- STIX/MISP 安全事件映射。

建议顺序：

1. JSON-LD `@context`。
2. `bgpkb:` 命名空间。
3. SKOS 分类映射。
4. PROV-O 溯源映射。
5. RDF 导出。
6. STIX/MISP，仅在需要对接安全平台时建设。

## 9. 当前成熟度

| 模块 | 成熟度 | 说明 |
| --- | --- | --- |
| 数据资产清单 | achieved | 核心资产已经存在，阶段一补集中登记 |
| 数据模型标准 | partial | schema 和 taxonomy 已有，命名规范和跨类型约束待补 |
| 元数据与溯源 | partial | 溯源链完整，统一审核和时间字段待补 |
| 质量治理 | partial | 结构质量强，语义质量待建设 |
| 生命周期 | planned | 当前仅有 review_status，生命周期状态待建设 |
| 服务化访问 | partial | REST API 已有，向量和 RAG 接口待建设 |
| 标准化出口 | achieved | JSON/CSV/SQLite、JSON-LD、SKOS、PROV-O 与 Turtle 样例已具备 |

## 10. 后续演进

阶段一完成后，应按以下顺序推进：

1. 生命周期与元数据治理。
2. 语义质量治理。
3. RAG 就绪与混合检索。
4. 轻量标准化出口。
5. 知识覆盖扩展。

数据管理体系 v1 的价值不在于改变现有知识库形态，而在于提供一个稳定的治理地图，让后续每次新增资产、字段、报告或服务接口都能被纳入同一套管理视角。
