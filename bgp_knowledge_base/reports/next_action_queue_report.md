# 下一步行动队列报告

## 范围

本报告把权威来源补充需求、实体人工复核包和必须跳过的语义任务合并成统一行动队列。该步骤只读已有结构化数据，不联网、不下载、不判断来源语义是否充分。

## 摘要

- 行动记录数：114
- JSONL 输出：`datasets/next_action_queue.jsonl`
- CSV 输出：`datasets/next_action_queue.csv`
- 因需要 LLM/语义判断而跳过的记录数：2

## 按行动类型统计

- entity_human_review：112
- semantic_task_skipped：2

## 按状态统计

- open：112
- skipped_by_policy：2

## 按优先级统计

- P3：34
- P4：78
- P90：1
- P91：1

## 前 30 条开放行动

| 顺序 | 优先级 | 类型 | 范围 | 名称 | 建议动作 |
| ---: | ---: | --- | --- | --- | --- |
| 1 | 3 | entity_human_review | `field_aggregator` | aggregator | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 2 | 3 | entity_human_review | `datasource_aspa` | ASPA | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 3 | 3 | entity_human_review | `mechanism_aspa_path_verification` | ASPA Path Verification | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 4 | 3 | entity_human_review | `field_asrank_rank` | asrank_rank | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 5 | 3 | entity_human_review | `field_asrank_relationship` | asrank_relationship | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 6 | 3 | entity_human_review | `field_atomic_aggregate` | atomic_aggregate | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 7 | 3 | entity_human_review | `mechanism_bgp_decision_process` | BGP Decision Process | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 8 | 3 | entity_human_review | `mechanism_rib_model` | BGP RIB Model | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 9 | 3 | entity_human_review | `mechanism_route_leak_roles_otc` | BGP Roles and OTC Route Leak Prevention | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 10 | 3 | entity_human_review | `mechanism_update_withdrawal` | BGP Update and Withdrawal Propagation | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 11 | 3 | entity_human_review | `field_bgp_identifier` | bgp_identifier | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 12 | 3 | entity_human_review | `field_bgp_role` | bgp_role | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 13 | 3 | entity_human_review | `mechanism_bgpsec_path_validation` | BGPsec Path Validation | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 14 | 3 | entity_human_review | `datasource_caida_asrank` | CAIDA ASRank | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 15 | 3 | entity_human_review | `field_customer_cone_asns` | customer_cone_asns | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 16 | 3 | entity_human_review | `field_hold_time` | hold_time | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 17 | 3 | entity_human_review | `field_local_pref` | local_pref | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 18 | 3 | entity_human_review | `field_med` | med | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 19 | 3 | entity_human_review | `field_mrt_file_type` | mrt_file_type | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 20 | 3 | entity_human_review | `field_next_hop` | next_hop | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 21 | 3 | entity_human_review | `field_nlri` | nlri | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 22 | 3 | entity_human_review | `field_origin_attribute` | origin_attribute | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 23 | 3 | entity_human_review | `field_otc_attribute` | otc_attribute | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 24 | 3 | entity_human_review | `field_path_attributes` | path_attributes | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 25 | 3 | entity_human_review | `datasource_peeringdb` | PeeringDB | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 26 | 3 | entity_human_review | `datasource_ripestat` | RIPEstat Data API | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 27 | 3 | entity_human_review | `field_routeviews_endpoint` | routeviews_endpoint | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 28 | 3 | entity_human_review | `mechanism_rpki_to_router_delivery` | RPKI-to-Router Delivery | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 29 | 3 | entity_human_review | `field_rpki_rtr_pdu` | rpki_rtr_pdu | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |
| 30 | 3 | entity_human_review | `field_ris_rrc` | rrc | 优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。 |

## 跳过事项

- `action_skipped_paper_method_expansion`：从论文正文扩展结构化方法需要语义判断或 LLM 介入，按用户要求跳过。
- `action_skipped_case_semantic_review`：事件角色、证据强度和影响范围判断需要语义流程或 LLM 介入，按用户要求跳过。
