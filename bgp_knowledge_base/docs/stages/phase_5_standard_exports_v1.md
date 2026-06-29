---
title: "阶段五：轻量标准化出口 v1"
document_type: "阶段设计文档"
purpose: "定义 BGP KB 从当前 JSON/JSONL/SQLite 出口渐进扩展到 JSON-LD、SKOS、PROV-O 和 RDF 的方案、简易版路径和验收边界。"
scope: "JSON-LD、SKOS、PROV-O、RDF、标准化报告和发布包兼容性"
status: "实施中"
last_reviewed: "2026-06-29"
---
# 阶段五：轻量标准化出口 v1

## 1. 阶段目标

阶段五目标是提升 BGP KB 的互操作能力，让现有实体、关系、source、chunk 和治理元数据可以被语义网、知识图谱和外部安全分析系统理解。

本阶段不做重型迁移，不把主存储改成 RDF，不要求引入 OWL 推理，也不替代当前 JSONL、CSV 和 SQLite 发布包。标准化出口应作为附加层存在，保持现有流水线和服务接口稳定。

## 2. 当前基线

当前已经具备：

| 能力 | 状态 |
| --- | --- |
| 稳定实体 ID | 已具备 |
| source ID 与 `source_refs` | 已具备 |
| chunk ID 和 source 到 chunk 链路 | 已具备 |
| relationship JSONL | 已具备 |
| 生命周期、复核、证据派生数据集 | 已具备 |
| JSONL、JSON、CSV、SQLite 发布包 | 已具备 |

阶段三点五已经进一步交付：

- JSON-LD `@context`。
- `bgpkb:` 命名空间和稳定 URI 规则。
- entity、source、chunk、relationship 和 evidence 的语义 ID 映射。
- 字段到 SKOS、PROV-O 和项目词汇的初步映射。

当前尚未具备：

- SKOS taxonomy 映射。
- PROV-O 溯源映射。
- RDF 导出。
- 标准化出口完整性报告。
- 模型辅助映射候选与人工审核闭环。

## 3. 较优解

较优解是在保持原有发布包不变的前提下，新增标准化出口层：

1. 定义 `bgpkb:` 命名空间和稳定 URI 规则。
2. 发布 JSON-LD `@context`。
3. 将概念类实体映射为 SKOS。
4. 将来源、生成脚本、复核审计和证据链映射为 PROV-O。
5. 生成 JSON-LD catalog 和 RDF 样例。
6. 生成标准化出口报告，记录覆盖率、缺口和不可映射字段。

较优解适合需要对接图数据库、RDF 工具链、知识图谱平台或外部数据治理评审的场景。

## 4. 简易版

简易版只做最小稳定语义层：

1. 冻结 ID 和 URI 命名规范。
2. 提供 `data/published/jsonld_context.json`。
3. 提供字段映射说明。
4. 为每类核心实体输出少量 JSON-LD 样例。
5. 不生成全量 RDF。
6. 不承诺完整 PROV-O 图，只记录可映射字段。

简易版适合阶段四 RAG 前后的过渡期。它能稳定字段语义，降低后续 API 和 context pack 改名风险。

## 5. 推荐路径

推荐分两步实施：

```text
阶段三点五：语义标识前置
  -> JSON-LD @context
  -> bgpkb: 命名空间
  -> URI/ID 规则

阶段五：标准化出口
  -> SKOS 映射
  -> PROV-O 映射
  -> JSON-LD catalog
  -> RDF 样例或全量导出
```

这样阶段四可以先稳定 RAG payload 和 context pack，不必等待完整 SKOS/PROV-O/RDF 完成。

## 6. 建议命名空间

| 前缀 | URI | 用途 |
| --- | --- | --- |
| `bgpkb:` | `https://example.org/bgpkb/id/` | BGP KB 自有实体、source、chunk、关系和证据 ID。 |
| `skos:` | `http://www.w3.org/2004/02/skos/core#` | 概念、标签、定义、概念关系和分类体系。 |
| `prov:` | `http://www.w3.org/ns/prov#` | 来源、生成活动、派生关系和审核活动。 |
| `dcterms:` | `http://purl.org/dc/terms/` | 标题、描述、日期、来源和语言等通用元数据。 |
| `schema:` | `https://schema.org/` | 组织、网页、文章、数据集等通用实体补充。 |

正式 URI 可在实施前替换为项目实际域名或内部命名空间。若没有公开域名，仍应保持 URI 形态稳定。

## 7. 核心字段映射

| 当前字段 | JSON-LD / 标准映射 | 说明 |
| --- | --- | --- |
| `id` / `entity_id` | `@id` | 使用 `bgpkb:` URI。 |
| `entity_type` | `@type` | 可映射到项目类型，概念类可附加 `skos:Concept`。 |
| `name` | `skos:prefLabel` | 默认语言可设为英文或按实体记录补充。 |
| `aliases` | `skos:altLabel` | 多值标签。 |
| `definition` | `skos:definition` | 概念定义。 |
| `category` | `skos:broader` 或 `bgpkb:category` | 简易版可先保留自定义字段。 |
| `related_terms` | `skos:related` | 需要把名称解析为实体 URI，不能解析时保留 literal。 |
| `source_refs` | `prov:wasDerivedFrom` | 指向 source URI。 |
| `review_status` | `bgpkb:reviewStatus` | 保留项目治理语义。 |
| `lifecycle_status` | `bgpkb:lifecycleStatus` | 来自生命周期派生视图。 |
| `generated_by` | `prov:wasGeneratedBy` | 指向脚本或活动 URI。 |
| `generated_at` | `prov:generatedAtTime` | 生成时间。 |
| `decision_reviewer` | `prov:wasAssociatedWith` | 审核人或审核主体。 |
| `decision_reviewed_at` | `prov:endedAtTime` | 审核活动结束时间。 |

## 8. 交付物

较优解交付物：

- `data/published/jsonld_context.json`
- `data/published/entity_catalog.jsonld`
- `data/published/source_catalog.jsonld`
- `data/published/provenance_map.jsonl`
- `data/published/standard_exports/`
- `data/generated/reports/publishing/standardization_report.md`
- `metadata/schemas/jsonld_context.schema.json`
- `tests/test_standard_exports.py`

简易版交付物：

- `data/published/jsonld_context.json`
- `docs/stages/phase_5_standard_exports_v1.md`
- `data/generated/reports/publishing/standardization_report.md`
- 5 到 10 条 JSON-LD 样例

## 9. 验收标准

较优解验收标准：

- 现有 JSONL、CSV、SQLite 发布包不被破坏。
- 每个发布实体都能生成稳定 `@id`。
- 每个发布 source 都能生成稳定 `@id`。
- `source_refs` 可被解析为 source URI。
- 至少 BGPConcept、AnomalyType、DataField、DataSource、EvidenceTemplate 有明确映射。
- source -> raw -> parsed -> cleaned -> chunk -> entity 的主要链路可表达为 provenance。
- 标准化报告能列出映射覆盖率和无法映射字段。

简易版验收标准：

- `@context` 可被 JSON-LD 工具解析。
- 样例实体包含 `@id`、`@type`、label、definition、source provenance。
- 样例不改变原始实体 JSONL 的字段。
- 文档清楚标明哪些字段暂不映射。

## 10. 非目标

本阶段不做：

- 不迁移主存储到 RDF。
- 不引入 OWL 本体推理。
- 不要求图数据库上线。
- 不把所有关系强行映射到标准词汇。
- 不自动批准 pending/candidate 实体。
- 不为 STIX/MISP 做完整安全事件建模，除非后续有明确对接需求。
