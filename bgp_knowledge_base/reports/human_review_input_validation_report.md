# 人工复核输入校验报告

## 范围

本报告只校验 `review_inputs/human_review_decisions.csv` 的结构和机械一致性，不判断实体内容是否应批准或拒绝。

该步骤不联网、不下载、不调用 LLM、不做语义判断，也不修改 entities/*.jsonl。

## 摘要

- 校验记录数：8
- 错误问题数：0
- 警告问题数：1
- 信息提示数：107
- 状态统计：{"info": 1, "pass": 6, "warning": 1}
- JSONL 输出：`datasets/human_review_input_validation.jsonl`
- CSV 输出：`datasets/human_review_input_validation.csv`
- 人工决策输入：`review_inputs/human_review_decisions.csv`

## 校验项

| 顺序 | 类型 | 状态 | 严重度 | 检查数 | 问题数 | 是否需要 LLM | 说明 |
| ---: | --- | --- | --- | ---: | ---: | --- | --- |
| 1 | `input_file_exists` | pass | error | 1 | 0 | 否 | 主人工决策输入文件存在且可读取。 |
| 2 | `required_columns` | pass | error | 5 | 0 | 否 | 主人工决策输入包含必需列。 |
| 3 | `duplicate_entity_id` | pass | error | 112 | 0 | 否 | 每个 entity_id 在主人工决策输入中最多出现一次。 |
| 4 | `missing_entity_id` | pass | error | 112 | 0 | 否 | 非空人工决策行必须填写 entity_id。 |
| 5 | `known_entity_id` | pass | error | 112 | 0 | 否 | 人工决策行引用的 entity_id 都存在于当前实体库。 |
| 6 | `allowed_review_decision` | pass | error | 112 | 0 | 否 | review_decision 均在允许枚举内。 |
| 7 | `semantic_review_boundary` | warning | warning | 112 | 1 | 是 | 需要语义流程的人工决策会被记录并阻塞自动应用。 |
| 8 | `ready_to_apply_preview` | info | info | 112 | 107 | 否 | 本检查只统计显式 approved/rejected 行，提示后续可由应用脚本处理。 |

## 需处理问题

- `semantic_review_boundary`：1 项；行：109；实体：`paper_method_bgpshield`；建议：按当前规则跳过该类记录；只有获得明确语义/LLM 处理许可后再处理。
- `ready_to_apply_preview`：107 项；行：2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 105, 107, 108, 110, 111, 112, 113；实体：`anomaly_moas`, `anomaly_origin_change`, `anomaly_path_hijack`, `anomaly_path_manipulation`, `anomaly_prefix_hijack`, `anomaly_prefix_outage`, `anomaly_route_leak`, `anomaly_subprefix_hijack`, `case_vodafone_2021_route_leak`, `concept_announcement`, `concept_as`, `concept_as_path`, `concept_as_relationship`, `concept_asn`, `concept_bgp`, `concept_bgp_session`, `concept_bgp_speaker`, `concept_bgp_update`, `concept_bgpstream`, `concept_customer_cone`, `concept_ebgp`, `concept_fib`, `concept_ibgp`, `concept_irr`, `concept_moas`, `concept_mrt`, `concept_origin_as`, `concept_peer`, `concept_prefix`, `concept_rib`, `concept_ripe_ris`, `concept_roa`, `concept_route_collector`, `concept_routeviews`, `concept_rov`, `concept_rpki`, `concept_valley_free`, `concept_vantage_point`, `concept_whois_rdap`, `concept_withdrawal`, `datasource_aspa`, `datasource_bgpstream`, `datasource_caida_as_relationships`, `datasource_caida_asrank`, `datasource_peeringdb`, `datasource_ripe_ris`, `datasource_ripestat`, `datasource_routeviews`, `datasource_rpki_roa`, `evidence_moas`, `evidence_origin_change`, `evidence_path_hijack`, `evidence_path_manipulation`, `evidence_prefix_hijack`, `evidence_prefix_outage`, `evidence_route_leak`, `evidence_subprefix_hijack`, `field_aggregator`, `field_as_path`, `field_as_relationship_sequence`, `field_asrank_rank`, `field_asrank_relationship`, `field_atomic_aggregate`, `field_bgp_identifier`, `field_bgp_role`, `field_collector`, `field_customer_cone_asns`, `field_hold_time`, `field_local_pref`, `field_med`, `field_mrt_file_type`, `field_next_hop`, `field_nlri`, `field_origin_as`, `field_origin_attribute`, `field_otc_attribute`, `field_path_attributes`, `field_peer_asn`, `field_prefix`, `field_ris_rrc`, `field_roa_status`, `field_routeviews_endpoint`, `field_rpki_rtr_pdu`, `field_timestamp`, `field_update_type`, `field_vrp_asn`, `field_vrp_max_length`, `field_vrp_prefix`, `field_withdrawn_routes`, `fp_as_relationship_error`, `fp_legitimate_moas`, `fp_short_route_flap`, `fp_single_collector_bias`, `mechanism_as_path_prepending`, `mechanism_aspa_path_verification`, `mechanism_before_after_path_comparison`, `mechanism_bgp_decision_process`, `mechanism_bgpsec_path_validation`, `mechanism_path_vector`, `mechanism_rib_model`, `mechanism_route_leak_roles_otc`, `mechanism_route_origin_validation`, `mechanism_rpki_to_router_delivery`, `mechanism_update_withdrawal`, `mechanism_valley_free`, `paper_method_beam`, `paper_method_bear`；建议：先运行决策审计确认 can_apply，再显式运行应用脚本；不要自动批准。

## 跳过事项

- 未自动批准、拒绝或修改实体。
- `needs_semantic_review` 只记录为语义流程边界，当前规则下不自动处理。
