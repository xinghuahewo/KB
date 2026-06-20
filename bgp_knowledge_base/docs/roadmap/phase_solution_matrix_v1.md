---
title: "BGP KB 阶段方案矩阵 v1"
document_type: "阶段方案矩阵"
purpose: "为每个建设阶段同时给出较优解和简易版，帮助在质量、成本、时间和后续扩展之间做取舍。"
scope: "BGP KB 下一阶段路线、治理、RAG、标准化出口和覆盖扩展"
status: "现行参考"
last_reviewed: "2026-06-19"
---
# BGP KB 阶段方案矩阵 v1

## 1. 使用方式

本文档是阶段路线的决策入口。每个阶段都给出两个版本：

- 较优解：更适合长期维护、自动化复跑、质量治理和外部集成。
- 简易版：更适合资源有限、需要先跑通闭环或验证价值的场景。

默认策略不是永远选择较优解，而是先判断阶段是否会影响后续接口、数据格式或治理边界。会影响下游稳定性的部分优先做较优解；只影响局部体验或扩展深度的部分可以先做简易版。

## 2. 总览矩阵

| 阶段 | 较优解 | 简易版 | 推荐采用 |
| --- | --- | --- | --- |
| 阶段一：数据管理体系 | 完整资产登记、机器可读配置、自动报告和测试。 | 手工维护资产清单和文档索引。 | 已完成较优解。 |
| 阶段二：生命周期与元数据治理 | 派生生命周期清单、状态规则、质量规则和报告。 | 继续只使用 `review_status`，在报告里人工说明状态。 | 已完成较优解。 |
| 阶段三：语义质量治理 | 规则化 blocker/warning/info 扫描，输出 findings 和报告。 | 人工抽查实体、关系和证据模板的语义问题。 | 已完成较优解。 |
| 阶段三点五：语义标识前置 | JSON-LD `@context`、`bgpkb:` 命名空间、URI/ID 规则和字段映射草案。 | 只冻结实体 ID、source ID、chunk ID 和关系 ID 命名规范。 | 已完成小步较优解。 |
| 阶段四：RAG 就绪与混合检索 | LLM 候选增强、embedding、向量索引、混合检索、rerank 和 context pack。 | SQLite FTS、关键词扩展、人工 context pack 和少量查询验收。 | 先简易版 PoC，再推进较优解。 |
| 阶段五：轻量标准化出口 | JSON-LD、SKOS、PROV-O、RDF 导出和标准化报告。 | JSON-LD context、JSONL 映射说明和少量样例导出。 | 先简易版，后补完整映射。 |
| 阶段六：知识覆盖扩展 | 系统扩展来源、实体类型、案例、论文方法和运营实践。 | 按缺口队列补充少量高价值主题。 | 先简易版，避免覆盖扩张压过治理。 |

## 3. 阶段一：数据管理体系

### 较优解

建立完整的数据资产登记和能力配置，把实体、关系、source、chunk、术语表、复核工作簿、行动队列、发布包和服务接口纳入统一治理视图。配置由 `config/data_management_capabilities.yaml` 承载，报告由脚本生成，测试保证字段、路径和状态不漂移。

### 简易版

只维护一份人工资产清单，记录每类文件的位置、用途和生成方式，不引入机器可读配置和测试。

### 推荐

当前项目已经完成较优解，应继续把新增数据资产挂入配置和报告，而不是退回手工清单。

## 4. 阶段二：生命周期与元数据治理

### 较优解

保留原始 `review_status`，新增派生的 `lifecycle_status` 视图，并用确定性规则把实体划入 `draft`、`candidate`、`reviewed`、`approved`、`deprecated`、`archived`。生命周期报告必须能解释状态来源、证据记录、复核包、行动队列和有效期。

### 简易版

继续只使用 `pending`、`approved`、`rejected`，在 README 或报告中人工解释哪些实体可进入高可信集合。

### 推荐

当前项目已经完成较优解。后续只需要补齐有效期策略和显式废弃/归档覆盖，不需要重新设计状态模型。

## 5. 阶段三：语义质量治理

### 较优解

建立可复跑的语义质量规则，把证据模板覆盖、关系类型约束、案例事件类型、DataSource 字段链路、生命周期影响和过期行动项转成 findings。findings 必须有等级、主体、字段、解释和建议动作。

### 简易版

由人工抽查核心实体和关系，手工记录语义问题，不形成机器可读 findings。

### 推荐

当前项目已经完成较优解。后续重点是处理 blocker 和高价值 warning，而不是扩大规则数量本身。

## 6. 阶段三点五：语义标识前置

### 较优解

在 RAG 和标准出口前先冻结标识层：

- 定义 `bgpkb:` 命名空间。
- 定义实体、source、chunk、relationship、evidence 的 URI 规则。
- 提供 JSON-LD `@context`。
- 明确现有字段到 JSON-LD、SKOS、PROV-O 的初步映射。
- 不改变现有 JSONL 主格式，只增加轻量出口和说明。

### 简易版

只冻结命名规范，不输出 JSON-LD。要求新实体和新关系继续使用稳定 ID，并禁止在 RAG payload 中引入临时字段名。

### 推荐

当前项目已经完成小步较优解：已交付 `@context`、`bgpkb:` 命名空间、URI 规则和字段映射草案。阶段四的 RAG API 和 context pack 应直接引用该语义标识层，避免在阶段五标准化时大规模改名。

## 7. 阶段四：RAG 就绪与混合检索

### 较优解

先用 LLM 生成候选增强数据，再进入人工复核和审计；随后建立 embedding、向量索引、SQLite FTS 混合检索、rerank、过滤器和 RAG context pack。默认可信集合只包含 `lifecycle_status=approved` 且无 blocker 的实体。

### 简易版

先不引入向量库和 LLM 候选数据，只使用 SQLite FTS、术语表、别名扩展和固定模板生成 context pack。用少量中文/英文查询验证召回和溯源字段。

### 推荐

先做简易版 PoC，证明查询、过滤、证据返回和 context pack 结构可用；再进入较优解的 embedding 和 LLM 候选增强。这样能避免向量库提前放大 chunk 质量问题。

## 8. 阶段五：轻量标准化出口

### 较优解

在不迁移主存储的前提下，提供 JSON-LD、SKOS、PROV-O 和 RDF 导出：

- `BGPConcept`、`AnomalyType`、`DataField` 等映射为 `skos:Concept` 或项目自定义类型。
- `source_refs`、`generated_by`、`generated_at`、review audit 映射为 PROV-O。
- 输出 JSON-LD catalog、provenance map、RDF 样例和标准化报告。

### 简易版

只提供 JSON-LD `@context`、字段映射说明和 5 到 10 条样例导出，不承诺全量 RDF 或完整 PROV-O 图。

### 推荐

先做简易版，确保命名空间、URI 和字段语义稳定；等 RAG payload 和治理字段稳定后，再做全量 SKOS/PROV-O/RDF 导出。

## 9. 阶段六：知识覆盖扩展

### 较优解

系统性扩展 BGP Community、检测方法、RPKI/ROV 生态、运营实践、扩展协议、IXP 路由和更多案例。每个扩展主题都要新增来源、实体、关系、chunk、质量规则和复核材料。

### 简易版

按 `source_gap_queue`、语义 findings 和用户高频查询补充少量主题，只扩充最能提升检索和问答质量的实体。

### 推荐

先做简易版。覆盖扩展会快速增加治理负担，应在阶段四和阶段五的接口形态稳定后再系统扩张。

## 10. 当前推荐路线

短期推荐路线：

```text
阶段四简易版 RAG PoC
-> 阶段四较优解的 embedding 与混合检索
-> 阶段五简易版标准出口
-> 阶段六按缺口扩展
```

如果资源很有限，最小可执行路线是：

```text
冻结 ID/URI 规则
-> SQLite FTS context pack
-> JSON-LD context 和样例导出
```

这条路线牺牲自动化深度，但不会破坏后续升级路径。
