# 人工复核工作簿报告

## 范围

本报告从实体人工复核包和下一步行动队列机械生成。该工作簿只提供人工复核入口，不自动批准、拒绝或改写任何实体。

## 摘要

- 工作簿记录数：112
- JSONL 输出：`datasets/human_review_workbook.jsonl`
- CSV 输出：`datasets/human_review_workbook.csv`
- 默认 review_decision：`unreviewed`
- 每条最多保留 chunk_sample_ids：12

## 按复核批次统计

- 01_ready_without_manual_note：34
- 02_ready_with_manual_note：78

## 按实体类型统计

- AnomalyType：8
- BGPConcept：31
- Case：5
- DataField：32
- DataSource：9
- EvidenceTemplate：8
- FalsePositivePattern：4
- PaperMethod：3
- RoutingMechanism：12

## 按人工决策状态统计

- unreviewed：112

## 前 30 条复核入口

| 顺序 | 批次 | 实体类型 | 实体 ID | 名称 | 来源数 | chunk 样例数 |
| ---: | --- | --- | --- | --- | ---: | ---: |
| 1 | 01_ready_without_manual_note | DataField | `field_aggregator` | aggregator | 1 | 12 |
| 2 | 01_ready_without_manual_note | DataSource | `datasource_aspa` | ASPA | 3 | 12 |
| 3 | 01_ready_without_manual_note | RoutingMechanism | `mechanism_aspa_path_verification` | ASPA Path Verification | 2 | 12 |
| 4 | 01_ready_without_manual_note | DataField | `field_asrank_rank` | asrank_rank | 1 | 7 |
| 5 | 01_ready_without_manual_note | DataField | `field_asrank_relationship` | asrank_relationship | 2 | 12 |
| 6 | 01_ready_without_manual_note | DataField | `field_atomic_aggregate` | atomic_aggregate | 1 | 12 |
| 7 | 01_ready_without_manual_note | RoutingMechanism | `mechanism_bgp_decision_process` | BGP Decision Process | 1 | 12 |
| 8 | 01_ready_without_manual_note | RoutingMechanism | `mechanism_rib_model` | BGP RIB Model | 3 | 12 |
| 9 | 01_ready_without_manual_note | RoutingMechanism | `mechanism_route_leak_roles_otc` | BGP Roles and OTC Route Leak Prevention | 1 | 12 |
| 10 | 01_ready_without_manual_note | RoutingMechanism | `mechanism_update_withdrawal` | BGP Update and Withdrawal Propagation | 3 | 12 |
| 11 | 01_ready_without_manual_note | DataField | `field_bgp_identifier` | bgp_identifier | 1 | 12 |
| 12 | 01_ready_without_manual_note | DataField | `field_bgp_role` | bgp_role | 1 | 12 |
| 13 | 01_ready_without_manual_note | RoutingMechanism | `mechanism_bgpsec_path_validation` | BGPsec Path Validation | 2 | 12 |
| 14 | 01_ready_without_manual_note | DataSource | `datasource_caida_asrank` | CAIDA ASRank | 2 | 12 |
| 15 | 01_ready_without_manual_note | DataField | `field_customer_cone_asns` | customer_cone_asns | 2 | 12 |
| 16 | 01_ready_without_manual_note | DataField | `field_hold_time` | hold_time | 1 | 12 |
| 17 | 01_ready_without_manual_note | DataField | `field_local_pref` | local_pref | 1 | 12 |
| 18 | 01_ready_without_manual_note | DataField | `field_med` | med | 1 | 12 |
| 19 | 01_ready_without_manual_note | DataField | `field_mrt_file_type` | mrt_file_type | 2 | 7 |
| 20 | 01_ready_without_manual_note | DataField | `field_next_hop` | next_hop | 1 | 12 |
| 21 | 01_ready_without_manual_note | DataField | `field_nlri` | nlri | 1 | 12 |
| 22 | 01_ready_without_manual_note | DataField | `field_origin_attribute` | origin_attribute | 1 | 12 |
| 23 | 01_ready_without_manual_note | DataField | `field_otc_attribute` | otc_attribute | 1 | 12 |
| 24 | 01_ready_without_manual_note | DataField | `field_path_attributes` | path_attributes | 1 | 12 |
| 25 | 01_ready_without_manual_note | DataSource | `datasource_peeringdb` | PeeringDB | 1 | 12 |
| 26 | 01_ready_without_manual_note | DataSource | `datasource_ripestat` | RIPEstat Data API | 2 | 7 |
| 27 | 01_ready_without_manual_note | DataField | `field_routeviews_endpoint` | routeviews_endpoint | 1 | 12 |
| 28 | 01_ready_without_manual_note | RoutingMechanism | `mechanism_rpki_to_router_delivery` | RPKI-to-Router Delivery | 2 | 12 |
| 29 | 01_ready_without_manual_note | DataField | `field_rpki_rtr_pdu` | rpki_rtr_pdu | 1 | 12 |
| 30 | 01_ready_without_manual_note | DataField | `field_ris_rrc` | rrc | 3 | 6 |

## 跳过事项

- 未使用 LLM 判断证据是否足以批准实体。
- 未从论文正文或案例正文抽取新结构化字段。
- 未自动修改 entities/*.jsonl 中的 review_status。
