# 人工复核决策审计报告

## 范围

本报告从人工复核工作簿机械生成，用于审计人工决策是否可以被后续显式应用。该步骤不修改 entities/*.jsonl，不自动批准或拒绝实体。

## 摘要

- 审计记录数：112
- 可应用记录数：107
- 需要 LLM/语义流程而阻塞的记录数：1
- 人工决策输入记录数：112
- 人工决策输入错误数：0
- JSONL 输出：`datasets/human_review_decision_audit.jsonl`
- CSV 输出：`datasets/human_review_decision_audit.csv`
- 人工决策输入：`review_inputs/human_review_decisions.csv`

## 按应用状态统计

- blocked_by_llm：1
- manual_followup：4
- ready_to_apply：107

## 按人工决策统计

- approved：107
- needs_semantic_review：1
- needs_source：4

## 按决策来源统计

- review_inputs/human_review_decisions.csv：112

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

## 人工决策输入错误

- 无

## 可应用决策

- `anomaly_moas` -> approved（entities/anomaly_types.jsonl）
- `anomaly_origin_change` -> approved（entities/anomaly_types.jsonl）
- `anomaly_path_hijack` -> approved（entities/anomaly_types.jsonl）
- `anomaly_path_manipulation` -> approved（entities/anomaly_types.jsonl）
- `anomaly_prefix_hijack` -> approved（entities/anomaly_types.jsonl）
- `anomaly_prefix_outage` -> approved（entities/anomaly_types.jsonl）
- `anomaly_route_leak` -> approved（entities/anomaly_types.jsonl）
- `anomaly_subprefix_hijack` -> approved（entities/anomaly_types.jsonl）
- `concept_announcement` -> approved（entities/bgp_concepts.jsonl）
- `concept_as` -> approved（entities/bgp_concepts.jsonl）
- `concept_as_relationship` -> approved（entities/bgp_concepts.jsonl）
- `concept_as_path` -> approved（entities/bgp_concepts.jsonl）
- `concept_asn` -> approved（entities/bgp_concepts.jsonl）
- `concept_bgp` -> approved（entities/bgp_concepts.jsonl）
- `concept_bgp_session` -> approved（entities/bgp_concepts.jsonl）
- `concept_bgp_speaker` -> approved（entities/bgp_concepts.jsonl）
- `concept_bgp_update` -> approved（entities/bgp_concepts.jsonl）
- `concept_bgpstream` -> approved（entities/bgp_concepts.jsonl）
- `concept_customer_cone` -> approved（entities/bgp_concepts.jsonl）
- `concept_ebgp` -> approved（entities/bgp_concepts.jsonl）
- `concept_fib` -> approved（entities/bgp_concepts.jsonl）
- `concept_ibgp` -> approved（entities/bgp_concepts.jsonl）
- `concept_irr` -> approved（entities/bgp_concepts.jsonl）
- `concept_moas` -> approved（entities/bgp_concepts.jsonl）
- `concept_mrt` -> approved（entities/bgp_concepts.jsonl）
- `concept_origin_as` -> approved（entities/bgp_concepts.jsonl）
- `concept_peer` -> approved（entities/bgp_concepts.jsonl）
- `concept_prefix` -> approved（entities/bgp_concepts.jsonl）
- `concept_rib` -> approved（entities/bgp_concepts.jsonl）
- `concept_ripe_ris` -> approved（entities/bgp_concepts.jsonl）
- `concept_roa` -> approved（entities/bgp_concepts.jsonl）
- `concept_route_collector` -> approved（entities/bgp_concepts.jsonl）
- `concept_routeviews` -> approved（entities/bgp_concepts.jsonl）
- `concept_rov` -> approved（entities/bgp_concepts.jsonl）
- `concept_rpki` -> approved（entities/bgp_concepts.jsonl）
- `concept_valley_free` -> approved（entities/bgp_concepts.jsonl）
- `concept_vantage_point` -> approved（entities/bgp_concepts.jsonl）
- `concept_whois_rdap` -> approved（entities/bgp_concepts.jsonl）
- `concept_withdrawal` -> approved（entities/bgp_concepts.jsonl）
- `case_vodafone_2021_route_leak` -> approved（entities/cases.jsonl）
- `field_aggregator` -> approved（entities/data_fields.jsonl）
- `field_as_path` -> approved（entities/data_fields.jsonl）
- `field_as_relationship_sequence` -> approved（entities/data_fields.jsonl）
- `field_asrank_rank` -> approved（entities/data_fields.jsonl）
- `field_asrank_relationship` -> approved（entities/data_fields.jsonl）
- `field_atomic_aggregate` -> approved（entities/data_fields.jsonl）
- `field_bgp_identifier` -> approved（entities/data_fields.jsonl）
- `field_bgp_role` -> approved（entities/data_fields.jsonl）
- `field_collector` -> approved（entities/data_fields.jsonl）
- `field_customer_cone_asns` -> approved（entities/data_fields.jsonl）

## 跳过事项

- 未自动修改实体文件；只有显式运行应用脚本时才应写入 review_status。
- `needs_semantic_review` 决策需要语义流程或 LLM，按当前规则阻塞并记录。
