---
title: "生命周期与元数据治理 v1"
document_type: "规划与治理文档"
purpose: "说明生命周期与元数据治理 v1的设计目标、治理边界和执行约束，供后续维护与阶段复核参考。"
scope: "知识库规划、治理与开发说明"
status: "现行参考"
last_reviewed: "2026-06-19"
---
# 生命周期与元数据治理 v1

## 阶段目标

本阶段把当前 BGP KB 的粗粒度 `review_status` 扩展为可盘点、可审计、可持续演进的生命周期治理视图。

生命周期状态模型：

```text
draft -> candidate -> reviewed -> approved -> deprecated -> archived
```

本阶段不修改实体、关系、chunk 或发布包，不修复流水线外的历史问题，不做写入审批系统。所有状态均由现有实体、来源证据、人工复核包、下一步行动队列和生命周期策略配置确定性推导。

## 状态定义

| 状态 | 含义 | 当前推导入口 |
| --- | --- | --- |
| `draft` | 缺少来源、证据或复核包，尚不能进入正式复核。 | 实体缺少 `source_refs`，或无法找到证据索引与复核包。 |
| `candidate` | 已有来源和证据线索，等待人工复核或补充。 | `review_status=pending`，且存在复核包或打开的行动项。 |
| `reviewed` | 已经过一定复核或结构审查，但尚未满足批准条件。 | `review_status=approved` 但证据索引不足，或后续策略显式覆盖。 |
| `approved` | 已批准进入知识库主视图，可被服务化、检索和下游出口依赖。 | `review_status=approved`，且存在来源证据记录。 |
| `deprecated` | 仍保留用于兼容或历史解释，但不建议新流程继续依赖。 | 由 `config/lifecycle_policy.yaml` 显式覆盖。 |
| `archived` | 历史归档，不进入默认活跃视图。 | 由 `config/lifecycle_policy.yaml` 显式覆盖。 |

## 生命周期状态推导规则

1. 若策略配置中存在实体级 `status_overrides`，优先使用显式生命周期状态。
2. 若实体 `review_status=approved` 且证据索引记录数大于 0，推导为 `approved`。
3. 若实体 `review_status=approved` 但缺少证据索引，推导为 `reviewed`，并在质量规则中提示。
4. 若实体仍为 `pending` 且存在复核包、来源引用或打开行动项，推导为 `candidate`。
5. 若实体缺少来源引用或缺少可复核证据，推导为 `draft`。
6. `deprecated` 与 `archived` 当前只通过策略显式声明，不由脚本自动猜测。

## 元数据字段

生命周期清单 `datasets/lifecycle_inventory.jsonl` 至少登记以下字段：

- `entity_id`
- `entity_type`
- `display_name`
- `review_status`
- `lifecycle_status`
- `lifecycle_reason`
- `source_refs`
- `source_ref_count`
- `evidence_index`
- `evidence_record_count`
- `review_packet_id`
- `review_bucket`
- `open_action_count`
- `next_action_ids`
- `reviewed_by`
- `approved_at`
- `valid_from`
- `valid_until`

这些字段不是替代原始实体，而是给治理、验收、服务化和后续标准出口使用的派生元数据视图。

## 质量规则

本阶段登记并执行以下确定性规则：

- `lifecycle_status_required`：每个实体必须能推导出生命周期状态。
- `approved_requires_review_evidence`：`approved` 生命周期实体必须具备可追踪证据。
- `deprecated_or_archived_reference_warning`：被标记为 `deprecated` 或 `archived` 的实体若仍被活跃关系引用，需要报告提示。
- `expired_validity_requires_action`：若实体设置了 `valid_until` 且已过期，必须存在后续行动项或降级状态。
- `review_lifecycle_consistency`：`review_status` 与 `lifecycle_status` 不应互相冲突。

## 交付物

- `config/lifecycle_policy.yaml`：生命周期状态、元数据字段、推导规则和质量规则配置。
- `scripts/build_lifecycle_report.py`：生成生命周期清单与治理报告。
- `datasets/lifecycle_inventory.jsonl`：实体级生命周期清单。
- `reports/lifecycle_report.md`：生命周期状态、元数据覆盖、质量规则和行动建议报告。
- `tests/test_lifecycle_metadata.py`：阶段二确定性测试。

## 非目标

本阶段不做 RAG、embedding、向量索引、JSON-LD/RDF、STIX/MISP、权限系统、多用户审核或自动写回实体状态。

本阶段不修改实体、关系、chunk 或发布包，只增加可复跑的派生治理层。
