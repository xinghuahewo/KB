# 实体人工复核包报告

## 范围

本报告从实体、实体复核队列和实体来源证据索引机械生成。它不判断实体是否正确，也不把实体改为 approved，只把人工复核需要打开的路径、chunk 样例和检查清单汇总到同一入口。

## 摘要

- 复核包记录数：112
- pending 记录数：5
- JSONL 输出：`datasets/entity_review_packets.jsonl`
- CSV 输出：`datasets/entity_review_packets.csv`
- 仅含 manual_note/context 来源的记录数：0

## 按复核桶统计

- ready_with_manual_note：78
- ready_without_manual_note：34

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

## 建议优先复核顺序前 30 条

| 顺序 | 实体类型 | 实体 ID | 名称 | 复核桶 | 非 manual 来源 | manual 来源 | chunk 总数 |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | RoutingMechanism | `mechanism_aspa_path_verification` | ASPA Path Verification | ready_without_manual_note | 2 | 0 | 16 |
| 2 | RoutingMechanism | `mechanism_bgp_decision_process` | BGP Decision Process | ready_without_manual_note | 1 | 0 | 129 |
| 3 | RoutingMechanism | `mechanism_rib_model` | BGP RIB Model | ready_without_manual_note | 3 | 0 | 136 |
| 4 | RoutingMechanism | `mechanism_route_leak_roles_otc` | BGP Roles and OTC Route Leak Prevention | ready_without_manual_note | 1 | 0 | 19 |
| 5 | RoutingMechanism | `mechanism_update_withdrawal` | BGP Update and Withdrawal Propagation | ready_without_manual_note | 3 | 0 | 132 |
| 6 | RoutingMechanism | `mechanism_bgpsec_path_validation` | BGPsec Path Validation | ready_without_manual_note | 2 | 0 | 123 |
| 7 | RoutingMechanism | `mechanism_rpki_to_router_delivery` | RPKI-to-Router Delivery | ready_without_manual_note | 2 | 0 | 97 |
| 8 | DataField | `field_aggregator` | aggregator | ready_without_manual_note | 1 | 0 | 129 |
| 9 | DataField | `field_asrank_rank` | asrank_rank | ready_without_manual_note | 1 | 0 | 7 |
| 10 | DataField | `field_asrank_relationship` | asrank_relationship | ready_without_manual_note | 2 | 0 | 22 |
| 11 | DataField | `field_atomic_aggregate` | atomic_aggregate | ready_without_manual_note | 1 | 0 | 129 |
| 12 | DataField | `field_bgp_identifier` | bgp_identifier | ready_without_manual_note | 1 | 0 | 129 |
| 13 | DataField | `field_bgp_role` | bgp_role | ready_without_manual_note | 1 | 0 | 19 |
| 14 | DataField | `field_customer_cone_asns` | customer_cone_asns | ready_without_manual_note | 2 | 0 | 22 |
| 15 | DataField | `field_hold_time` | hold_time | ready_without_manual_note | 1 | 0 | 129 |
| 16 | DataField | `field_local_pref` | local_pref | ready_without_manual_note | 1 | 0 | 129 |
| 17 | DataField | `field_med` | med | ready_without_manual_note | 1 | 0 | 129 |
| 18 | DataField | `field_mrt_file_type` | mrt_file_type | ready_without_manual_note | 2 | 0 | 7 |
| 19 | DataField | `field_next_hop` | next_hop | ready_without_manual_note | 1 | 0 | 129 |
| 20 | DataField | `field_nlri` | nlri | ready_without_manual_note | 1 | 0 | 129 |
| 21 | DataField | `field_origin_attribute` | origin_attribute | ready_without_manual_note | 1 | 0 | 129 |
| 22 | DataField | `field_otc_attribute` | otc_attribute | ready_without_manual_note | 1 | 0 | 19 |
| 23 | DataField | `field_path_attributes` | path_attributes | ready_without_manual_note | 1 | 0 | 129 |
| 24 | DataField | `field_routeviews_endpoint` | routeviews_endpoint | ready_without_manual_note | 1 | 0 | 27 |
| 25 | DataField | `field_rpki_rtr_pdu` | rpki_rtr_pdu | ready_without_manual_note | 1 | 0 | 54 |
| 26 | DataField | `field_ris_rrc` | rrc | ready_without_manual_note | 3 | 0 | 6 |
| 27 | DataField | `field_vrp_asn` | vrp_asn | ready_without_manual_note | 1 | 0 | 15 |
| 28 | DataField | `field_vrp_max_length` | vrp_max_length | ready_without_manual_note | 1 | 0 | 15 |
| 29 | DataField | `field_vrp_prefix` | vrp_prefix | ready_without_manual_note | 1 | 0 | 15 |
| 30 | DataField | `field_withdrawn_routes` | withdrawn_routes | ready_without_manual_note | 1 | 0 | 129 |

## 需要补权威来源的实体

- 无

## 跳过事项

- 未从论文正文或案例正文新增结构化实体，因为这需要语义判断或 LLM 介入。
- 未自动批准任何 pending 实体，因为批准需要人工确认来源是否直接支持实体字段。
