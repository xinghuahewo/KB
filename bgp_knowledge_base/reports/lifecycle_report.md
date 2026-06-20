# 生命周期治理报告

## 范围

本报告基于 `config/lifecycle_policy.yaml` 生成，读取现有实体、证据索引、复核包、行动队列和人工决策审计，输出实体级生命周期治理视图。

该步骤不联网、不调用 LLM，不修改实体、关系、chunk 或发布包。

## 摘要

- 配置版本：`lifecycle_metadata_v1`
- 实体总数：112
- 生命周期状态数：6
- 质量规则数：5

## 生命周期状态统计

| 生命周期状态 | 实体数 |
| --- | ---: |
| 草稿 (`draft`) | 0 |
| 候选 (`candidate`) | 5 |
| 已复核 (`reviewed`) | 0 |
| 已批准 (`approved`) | 107 |
| 已弃用 (`deprecated`) | 0 |
| 已归档 (`archived`) | 0 |

## review_status 对照

| review_status | 实体数 |
| --- | ---: |
| `approved` | 107 |
| `pending` | 5 |

## 实体类型覆盖

| 实体类型 | 实体数 |
| --- | ---: |
| `AnomalyType` | 8 |
| `BGPConcept` | 31 |
| `Case` | 5 |
| `DataField` | 32 |
| `DataSource` | 9 |
| `EvidenceTemplate` | 8 |
| `FalsePositivePattern` | 4 |
| `PaperMethod` | 3 |
| `RoutingMechanism` | 12 |

## 元数据覆盖

| 字段 | 有值记录数 | 缺失或空值记录数 |
| --- | ---: | ---: |
| `entity_id` | 112 | 0 |
| `entity_type` | 112 | 0 |
| `display_name` | 112 | 0 |
| `review_status` | 112 | 0 |
| `lifecycle_status` | 112 | 0 |
| `lifecycle_reason` | 112 | 0 |
| `source_refs` | 112 | 0 |
| `source_ref_count` | 112 | 0 |
| `evidence_index` | 112 | 0 |
| `evidence_record_count` | 112 | 0 |
| `review_packet` | 112 | 0 |
| `review_packet_id` | 112 | 0 |
| `review_bucket` | 112 | 0 |
| `next_action` | 112 | 0 |
| `next_action_ids` | 112 | 0 |
| `reviewed_by` | 107 | 5 |
| `approved_at` | 107 | 5 |
| `valid_from` | 0 | 112 |
| `valid_until` | 0 | 112 |

## 质量规则结果

| 规则 | 状态 | 命中数 | 样例 |
| --- | --- | ---: | --- |
| `lifecycle_status_required` | 通过 | 0 | 无 |
| `approved_requires_review_evidence` | 通过 | 0 | 无 |
| `deprecated_or_archived_reference_warning` | 通过 | 0 | 无 |
| `expired_validity_requires_action` | 通过 | 0 | 无 |
| `review_lifecycle_consistency` | 通过 | 0 | 无 |

## 下一步行动

- 优先处理 `candidate` 实体的人工复核与来源补充，使其进入 `approved`。
- 对 `reviewed` 但缺少证据索引的实体补齐证据记录或降低生命周期状态。
- 仅在明确替代或失效时，通过策略显式标记 `deprecated` 或 `archived`。

## 候选与待处理实体样例

| 实体 | 类型 | 生命周期 | 行动项数 | 原因 |
| --- | --- | --- | ---: | --- |
| `case_celerbridge_bgp_hijack` | `Case` | `candidate` | 1 | 实体仍待复核，但已有来源、复核包、证据或行动项。 |
| `case_facebook_2021_outage` | `Case` | `candidate` | 1 | 实体仍待复核，但已有来源、复核包、证据或行动项。 |
| `case_indosat_route_leak` | `Case` | `candidate` | 1 | 实体仍待复核，但已有来源、复核包、证据或行动项。 |
| `case_pakistan_youtube_2008` | `Case` | `candidate` | 1 | 实体仍待复核，但已有来源、复核包、证据或行动项。 |
| `paper_method_bgpshield` | `PaperMethod` | `candidate` | 1 | 实体仍待复核，但已有来源、复核包、证据或行动项。 |
