---
title: "语义质量治理 v1"
document_type: "规划与治理文档"
purpose: "说明语义质量治理 v1 的检查范围、分级标准、可信默认集合和阶段边界。"
scope: "BGP KB 实体、关系、证据模板、生命周期状态和后续 RAG/标准出口可信集合"
status: "现行参考"
last_reviewed: "2026-06-19"
---
# 语义质量治理 v1

## 阶段目标

阶段三把 BGP KB 从“结构质量可检查”推进到“语义一致性可扫描、可分级、可验收”。

本阶段只新增确定性语义质量检查层，不自动修改实体、关系、chunk、来源或发布包。检查结果用于暴露知识之间的语义断点，并为后续 RAG、向量索引、JSON-LD/RDF 出口提供可信默认集合。

## 检查范围

语义质量治理 v1 覆盖以下对象：

- AnomalyType 与 EvidenceTemplate 的 required evidence 覆盖关系。
- EvidenceTemplate 中证据字段到 DataField 或 BGPConcept 的可解释映射。
- Relationship 的关系类型、起点实体类型和终点实体类型约束。
- Case 的 `event_type` 到已知 AnomalyType 的映射。
- DataSource 与 DataField 的来源链路。
- Lifecycle 中 `candidate` 实体对高可信默认集合的影响。
- `valid_until` 过期实体的行动队列覆盖。

## 分级标准

语义问题等级固定为 blocker、warning、info：

| 等级 | 含义 |
| --- | --- |
| `blocker` | 会破坏实体引用、关系约束或核心语义链路，后续 RAG 默认可信集合必须排除相关主体。 |
| `warning` | 表示语义证据不足、需要人工复核或需要后续补充映射，但不代表现有结构不可用。 |
| `info` | 表示可改进的解释性或覆盖性提示，不阻塞服务化查询。 |

## 高可信默认集合

阶段三默认只把同时满足以下条件的实体视为后续高可信默认集合：

1. `lifecycle_status=approved`。
2. 主体本身没有 `blocker` 级语义问题。
3. 不属于策略明确排除范围。

`candidate` 实体会被记录为不能进入高可信默认集合，但本阶段不改变实体审批状态。

## 交付物

- `config/semantic_quality_rules.yaml`：语义质量规则、等级、关系类型约束和输出路径。
- `scripts/build_semantic_quality_report.py`：确定性生成 findings 与报告。
- `datasets/semantic_quality_findings.jsonl`：逐条语义质量问题清单。
- `reports/semantic_quality_report.md`：语义问题总览、等级统计、RAG 影响和人工复核建议。
- `tests/test_semantic_quality.py`：阶段三测试。

## 非目标

本阶段不引入 LLM、embedding、向量库、RAG 接口、JSON-LD/RDF 出口，也不自动修复任何实体、关系、chunk、来源或发布包。

发现的 blocker 不要求在本阶段全部修复，但必须被记录、分级并给出建议动作。
