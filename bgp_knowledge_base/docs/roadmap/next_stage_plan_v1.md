---
title: "BGP KB 下一阶段建设计划文档 v1"
document_type: "规划与治理文档"
purpose: "说明BGP KB 下一阶段建设计划文档 v1的设计目标、治理边界和执行约束，供后续维护与阶段复核参考。"
scope: "知识库规划、治理与开发说明"
status: "现行参考"
last_reviewed: "2026-06-19"
---
# BGP KB 下一阶段建设计划文档 v1

## 1. 文档目的

本文档基于当前 BGP 知识库完成度和《BGP 知识库当前设计与工业界差距评估报告》的结论，定义下一阶段建设路线。

当前项目已经完成高质量 BGP 知识库数据底座，并新增了只读 FastAPI 服务和简单网页浏览入口。下一阶段重点不是推倒重来，也不是立刻做重型 RDF/OWL 迁移，而是把现有资产升级为具备数据管理、语义治理、RAG 就绪和轻量标准化能力的知识资产平台。

## 2. 当前基线

截至当前项目状态，已具备以下能力：

| 能力 | 当前状态 | 证据位置 |
| --- | --- | --- |
| 原始资料库 | 已完成 | `inventory/sources.csv`、`raw/` |
| 清洗文本库 | 已完成 | `cleaned/`、`reports/parse_report.md` |
| 知识片段库 | 已完成，2037 条 chunk | `chunks/`、`published/chunk_catalog.jsonl` |
| 实体库 | 已完成，112 条实体 | `entities/`、`published/entity_catalog.jsonl` |
| 关系表 | 已完成，106 条关系 | `relationships/relationships.jsonl` |
| 术语表 | 已完成，112 条术语 | `datasets/glossary.jsonl` |
| 质量检查 | 已完成结构质量检查 | `reports/quality_report.md` |
| 发布包 | 已完成 SQLite/JSONL/JSON 发布 | `published/` |
| 服务化访问 | 已完成 REST API 和简单网页 | `service/` |
| 人工复核 | 107 approved，5 pending | `reports/human_review_progress_report.md` |

当前仍然存在的主要差距：

- 语义质量检查不足，当前质量治理偏结构正确。
- 生命周期状态偏粗，主要依赖 `pending/approved`。
- RAG 就绪能力不足，尚无 embedding、向量索引和上下文包接口。
- 标准化出口不足，尚无 JSON-LD、SKOS、PROV-O 或 RDF 导出；阶段四前还需要先冻结轻量语义标识层，避免 RAG payload 后续返工。
- 知识覆盖还偏核心 MVP，BGP 社区生态、检测方法分类、运营实践、扩展协议和 IXP 路由仍需扩展。
- 持续维护机制不足，尚无 CI、知识 diff、版本化发布和自动过期提醒。

## 3. 总体目标

下一阶段总体目标：

> 把当前 BGP KB 从“高质量可查询知识库”升级为“具备数据管理体系、语义治理、RAG 就绪能力和标准化出口的 BGP 知识资产平台”。

目标能力包括：

- 数据资产可盘点。
- 数据模型可解释。
- 数据状态可治理。
- 语义问题可扫描。
- 检索结果可溯源。
- 服务接口可集成。
- 语义标识可稳定复用。
- 标准出口可演进。
- 后续 RAG/Agent 使用有可信基础。

## 4. 建设原则

1. 不推倒重来。
   当前目录、数据文件、报告和发布包已经形成稳定底座。下一阶段应新增治理层和服务层，而不是重排现有目录。

2. 先治理，再扩张。
   在扩展更多 BGP 子领域前，先补齐资产目录、生命周期和语义质量规则，避免知识规模扩大后治理失控。

3. 先轻量标准化，再重型本体化。
   优先 JSON-LD、SKOS 和 PROV-O 映射，不急于全量 RDF/OWL 存储迁移。

4. LLM 只做候选，不直接批准。
   后续可引入 LLM 辅助抽取 PaperMethod、案例角色、证据强度等语义字段，但必须进入人工复核和审计流程。

5. 所有服务输出必须保留溯源。
   API、RAG 和标准化出口都必须保留 `source_ref`、`chunk_id`、`review_status` 等可信边界信息。

## 5. 阶段路线图

### 阶段一：数据管理体系 v1

目标：把 DAMA-DMBOK 风格的数据管理目录落成项目内治理框架。

交付物：

- `docs/governance/data_management_v1.md`
- `config/data_management_capabilities.yaml`
- `scripts/build_data_management_report.py`
- `reports/data_management_report.md`

核心能力：

- 数据资产清单。
- 数据模型标准说明。
- 元数据与溯源覆盖说明。
- 质量治理能力矩阵。
- 生命周期现状说明。
- 服务化访问能力说明。
- 标准化出口现状说明。

验收标准：

- 能一页看清 BGP KB 有哪些数据资产。
- 每类资产都能追踪到 schema、数据文件、生成脚本、报告和发布出口。
- 后续新增资产必须能挂到这套目录下。

阶段一详细开发文档见 `docs/stages/phase_1_data_management_v1_development.md`。

### 阶段二：生命周期与元数据治理

目标：补齐知识资产从候选到废弃的状态流转。

建议新增生命周期状态：

```text
draft -> candidate -> reviewed -> approved -> deprecated -> archived
```

实现策略：

- 保留现有 `review_status`。
- 新增 `lifecycle_status`，避免破坏当前流水线。
- 增加统一治理字段：
  - `created_at`
  - `updated_at`
  - `extracted_at`
  - `reviewed_by`
  - `reviewed_at`
  - `approved_at`
  - `change_reason`
  - `valid_from`
  - `valid_until`

交付物：

- 生命周期 schema 扩展。
- 生命周期状态报告。
- 生命周期一致性检查。

验收标准：

- 每个实体都有生命周期状态。
- approved 实体必须有审核信息。
- deprecated/archived 实体不能被 active 关系无提示引用。

### 阶段三：语义质量治理

目标：从“结构正确”升级到“语义一致”。

新增检查规则：

- AnomalyType 的 required evidence 必须能映射到 EvidenceTemplate。
- EvidenceTemplate 引用的数据字段必须存在于 DataField。
- Relationship 的 src/dst 类型必须符合允许规则。
- Case 引用的 anomaly type 必须存在。
- DataSource 的字段说明必须能对应 source_type。
- pending 实体不能进入高可信 RAG 结果默认集合。
- valid_until 过期实体必须进入复核队列。

交付物：

- `scripts/build_semantic_quality_report.py`
- `reports/semantic_quality_report.md`
- `datasets/semantic_quality_findings.jsonl`

验收标准：

- 语义问题可机器扫描。
- 每条问题包含 entity_id、字段、严重度、建议修复动作。
- 报告能区分 blocker、warning、info。

### 阶段三点五：轻量语义标识前置

目标：在 RAG 和标准化出口之前，先稳定字段语义、命名空间和 URI 规则。

建设内容：

- 定义 `bgpkb:` 命名空间。
- 定义实体、source、chunk、relationship、evidence 的 URI/ID 规则。
- 建立 JSON-LD `@context`。
- 给出当前字段到 JSON-LD、SKOS、PROV-O 的初步映射。
- 保持现有 JSONL、CSV、SQLite 主格式不变。

验收标准：

- 每个实体、source、chunk 都能生成稳定 URI。
- RAG context pack 可以引用稳定 `@id`，而不是临时字段名。
- 阶段五标准化出口可以在该语义标识层上继续扩展。

较优解与简易版取舍见 `docs/roadmap/phase_solution_matrix_v1.md`。

### 阶段四：RAG 就绪与混合检索

目标：让知识库可被问答系统、Agent 和分析系统稳定调用。

建设内容：

- 为 entities、chunks、glossary、evidence_templates 生成 embedding。
- 建立向量索引，优先 Chroma 或 Qdrant。
- 建立混合检索：SQLite FTS + 向量检索 + 实体类型过滤 + 来源过滤 + 复核状态过滤。
- 新增 RAG 接口：
  - `/api/v1/retrieval/search`
  - `/api/v1/retrieval/evidence`
  - `/api/v1/retrieval/context-pack`

验收标准：

- `route leak` 能召回异常类型、证据模板和相关 chunk。
- 中文“路由泄露”能召回英文 route leak 相关内容。
- 返回结果必须包含 `source_ref`、`chunk_id`、`review_status`。
- RAG context pack 默认不包含 archived 或策略排除实体。

### 阶段五：轻量标准化出口

目标：提升互操作能力，但不做重型迁移。

优先顺序：

1. JSON-LD `@context`
2. `bgpkb:` 命名空间
3. SKOS taxonomy 映射
4. PROV-O 溯源映射
5. RDF 导出
6. STIX/MISP，仅在需要对接安全平台时做

交付物：

- `published/jsonld_context.json`
- `published/entity_catalog.jsonld`
- `published/provenance_map.jsonl`
- `reports/standardization_report.md`
- `docs/stages/phase_5_standard_exports_v1.md`

验收标准：

- 现有 JSONL 不被破坏。
- 每个实体可生成稳定 URI。
- source -> raw -> parsed -> cleaned -> chunk -> entity 的链路可表达为 provenance。

### 阶段六：知识覆盖扩展

目标：扩展 BGP 子领域覆盖，但保持质量纪律。

优先扩展方向：

1. BGP Community 生态。
2. 检测方法分类。
3. RPKI/ROV 生态测量。
4. BGP 运营实践。
5. BGP 扩展协议。
6. IXP 路由场景。

建议目标：

- 实体从 112 扩展到 250-400。
- 关系从 106 扩展到 300+。
- 案例从 5 扩展到 15-20。
- PaperMethod 从 3 扩展到 10+。

## 6. 推荐执行顺序

建议优先执行：

```text
阶段一：数据管理体系 v1
阶段二：生命周期与元数据治理
阶段三：语义质量治理
阶段三点五：轻量语义标识前置（已交付小步较优解）
阶段四：RAG 就绪与混合检索
阶段五：轻量标准化出口
阶段六：知识覆盖扩展
```

第一批最小闭环状态：

```text
data_management_v1
+ lifecycle_status
+ semantic_quality_report
+ jsonld_context 与 bgpkb 命名空间（已交付）
```

前三项已经形成治理底座；`jsonld_context` 与 `bgpkb` 命名空间已经作为阶段四前的小步前置项交付，后续 RAG context pack 和标准出口应复用该标识层。

阶段较优解与简易版的详细取舍见 `docs/roadmap/phase_solution_matrix_v1.md`。

## 7. 风险与边界

### 不应立即做的事情

- 不应直接重排现有目录结构。
- 不应马上全量迁移到 RDF/OWL。
- 不应让 LLM 直接改写 approved 实体。
- 不应在 RAG 中默认使用 pending、deprecated 或 archived 实体。
- 不应让服务层写入实体或发布产物。

### 主要风险

- 扩展知识覆盖过快，导致人工复核压力上升。
- 语义规则过早复杂化，造成维护成本过高。
- 标准化映射过早锁死模型。
- RAG 检索在缺少状态过滤时混入未复核内容。

### 缓解策略

- 每阶段只增加少量、可验证的能力。
- 所有新增能力必须有报告或测试。
- 保留现有 JSONL/SQLite 作为稳定主线。
- 标准化出口作为派生产物，不反向驱动核心模型。

## 8. 总结

当前 BGP KB 已经完成从资料到结构化知识资产的第一阶段建设，并已具备本地查询和服务化访问能力。

下一阶段的核心不是继续堆数据，而是建立数据管理体系、生命周期、语义质量和 RAG 就绪能力。

一句话目标：

> 把当前 BGP KB 从“高质量知识库工程”升级为“具备数据管理体系的数据资产平台”。
