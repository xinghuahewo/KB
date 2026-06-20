# 语义质量治理报告

## 范围

本报告基于 `config/semantic_quality_rules.yaml` 生成，读取实体、关系、生命周期清单、行动队列和来源证据索引，输出确定性语义质量 findings。

该步骤不联网、不调用 LLM，不自动修改实体、关系、chunk、来源或发布包。

## 语义问题总览

- 配置版本：`semantic_quality_v1`
- finding 总数：16
- blocker 数：0
- warning 数：13
- info 数：3
- 高可信默认集合实体数：107

## 等级统计

| 等级 | 数量 |
| --- | ---: |
| `blocker` | 0 |
| `warning` | 13 |
| `info` | 3 |

## 规则统计

| 规则 | 数量 |
| --- | ---: |
| `anomaly_required_evidence_template_coverage` | 0 |
| `evidence_template_field_mapping` | 8 |
| `relationship_type_constraint` | 0 |
| `case_anomaly_type_mapping` | 0 |
| `datasource_field_lineage` | 3 |
| `candidate_excluded_from_trusted_rag` | 5 |
| `expired_validity_requires_action` | 0 |

## RAG 默认可信集合影响

- 当前没有 blocker 级语义问题；默认高可信集合主要由 approved 生命周期控制。
- candidate 排除提示数：5
- candidate 样例：`case_celerbridge_bgp_hijack`, `case_facebook_2021_outage`, `case_indosat_route_leak`, `case_pakistan_youtube_2008`, `paper_method_bgpshield`

## 人工复核建议

- 优先处理 blocker；warning 进入人工复核或语义映射补充。
- 每条 finding 的 `suggested_action` 可作为下一步行动队列候选来源。

## 后续 RAG 可依赖集合

- 默认策略：`lifecycle_status=approved` 且主体无 blocker。
- 当前可依赖实体数：107
- 样例：`anomaly_moas`, `anomaly_origin_change`, `anomaly_path_hijack`, `anomaly_path_manipulation`, `anomaly_prefix_hijack`, `anomaly_prefix_outage`, `anomaly_route_leak`, `anomaly_subprefix_hijack`, `concept_announcement`, `concept_as`, `concept_as_path`, `concept_as_relationship`, `concept_asn`, `concept_bgp`, `concept_bgp_session`, `concept_bgp_speaker`, `concept_bgp_update`, `concept_bgpstream`, `concept_customer_cone`, `concept_ebgp`

## Finding 样例

| 等级 | 规则 | 主体 | 字段 | 建议 |
| --- | --- | --- | --- | --- |
| `info` | `datasource_field_lineage` | `datasource_aspa` | `relationships` | 补充 DataSource provides/supports DataField 的关系，或在来源证据中说明字段链路。 |
| `info` | `datasource_field_lineage` | `datasource_bgpstream` | `relationships` | 补充 DataSource provides/supports DataField 的关系，或在来源证据中说明字段链路。 |
| `info` | `datasource_field_lineage` | `datasource_peeringdb` | `relationships` | 补充 DataSource provides/supports DataField 的关系，或在来源证据中说明字段链路。 |
| `warning` | `candidate_excluded_from_trusted_rag` | `case_celerbridge_bgp_hijack` | `lifecycle_status` | 完成人工复核与证据补齐后，再进入 approved 生命周期。 |
| `warning` | `candidate_excluded_from_trusted_rag` | `case_facebook_2021_outage` | `lifecycle_status` | 完成人工复核与证据补齐后，再进入 approved 生命周期。 |
| `warning` | `candidate_excluded_from_trusted_rag` | `case_indosat_route_leak` | `lifecycle_status` | 完成人工复核与证据补齐后，再进入 approved 生命周期。 |
| `warning` | `candidate_excluded_from_trusted_rag` | `case_pakistan_youtube_2008` | `lifecycle_status` | 完成人工复核与证据补齐后，再进入 approved 生命周期。 |
| `warning` | `candidate_excluded_from_trusted_rag` | `paper_method_bgpshield` | `lifecycle_status` | 完成人工复核与证据补齐后，再进入 approved 生命周期。 |
| `warning` | `evidence_template_field_mapping` | `evidence_moas` | `required_evidence` | 补充 DataField、Concept 或语义映射规则；无法自动判断时进入人工复核。 |
| `warning` | `evidence_template_field_mapping` | `evidence_origin_change` | `required_evidence` | 补充 DataField、Concept 或语义映射规则；无法自动判断时进入人工复核。 |
| `warning` | `evidence_template_field_mapping` | `evidence_path_hijack` | `required_evidence` | 补充 DataField、Concept 或语义映射规则；无法自动判断时进入人工复核。 |
| `warning` | `evidence_template_field_mapping` | `evidence_path_manipulation` | `required_evidence` | 补充 DataField、Concept 或语义映射规则；无法自动判断时进入人工复核。 |
| `warning` | `evidence_template_field_mapping` | `evidence_prefix_hijack` | `required_evidence` | 补充 DataField、Concept 或语义映射规则；无法自动判断时进入人工复核。 |
| `warning` | `evidence_template_field_mapping` | `evidence_prefix_outage` | `required_evidence` | 补充 DataField、Concept 或语义映射规则；无法自动判断时进入人工复核。 |
| `warning` | `evidence_template_field_mapping` | `evidence_route_leak` | `required_evidence` | 补充 DataField、Concept 或语义映射规则；无法自动判断时进入人工复核。 |
| `warning` | `evidence_template_field_mapping` | `evidence_subprefix_hijack` | `required_evidence` | 补充 DataField、Concept 或语义映射规则；无法自动判断时进入人工复核。 |
