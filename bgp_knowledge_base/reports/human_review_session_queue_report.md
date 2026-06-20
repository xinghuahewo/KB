# 人工复核会话队列报告

## 范围

本报告把人工复核工作簿和证据摘录机械切分为小批次会话。它只安排人工处理顺序，不判断实体是否应批准或拒绝。

## 摘要

- 队列记录数：112
- 会话大小：10
- 会话数：12
- 每项最多引用摘录数：3
- JSONL 输出：`datasets/human_review_session_queue.jsonl`
- CSV 输出：`datasets/human_review_session_queue.csv`
- 人工决策输入：`review_inputs/human_review_decisions.csv`

## 按队列状态统计

- blocked_by_llm：1
- manual_followup：4
- ready_to_apply：107

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

## 前 5 个会话

- review_session_001：10 条
- review_session_002：10 条
- review_session_003：10 条
- review_session_004：10 条
- review_session_005：10 条

## 第一会话条目

| 顺序 | 实体 | 类型 | 名称 | 摘录 | 下一步 |
| ---: | --- | --- | --- | --- | --- |
| 1 | `field_aggregator` | DataField | aggregator | `extract_field_aggregator_01`<br>`extract_field_aggregator_02`<br>`extract_field_aggregator_03` | 显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。 |
| 2 | `datasource_aspa` | DataSource | ASPA | `extract_datasource_aspa_01`<br>`extract_datasource_aspa_02`<br>`extract_datasource_aspa_03` | 显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。 |
| 3 | `mechanism_aspa_path_verification` | RoutingMechanism | ASPA Path Verification | `extract_mechanism_aspa_path_verification_01`<br>`extract_mechanism_aspa_path_verification_02`<br>`extract_mechanism_aspa_path_verification_03` | 显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。 |
| 4 | `field_asrank_rank` | DataField | asrank_rank | `extract_field_asrank_rank_01`<br>`extract_field_asrank_rank_02`<br>`extract_field_asrank_rank_03` | 显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。 |
| 5 | `field_asrank_relationship` | DataField | asrank_relationship | `extract_field_asrank_relationship_01`<br>`extract_field_asrank_relationship_02`<br>`extract_field_asrank_relationship_03` | 显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。 |
| 6 | `field_atomic_aggregate` | DataField | atomic_aggregate | `extract_field_atomic_aggregate_01`<br>`extract_field_atomic_aggregate_02`<br>`extract_field_atomic_aggregate_03` | 显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。 |
| 7 | `mechanism_bgp_decision_process` | RoutingMechanism | BGP Decision Process | `extract_mechanism_bgp_decision_process_01`<br>`extract_mechanism_bgp_decision_process_02`<br>`extract_mechanism_bgp_decision_process_03` | 显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。 |
| 8 | `mechanism_rib_model` | RoutingMechanism | BGP RIB Model | `extract_mechanism_rib_model_01`<br>`extract_mechanism_rib_model_02`<br>`extract_mechanism_rib_model_03` | 显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。 |
| 9 | `mechanism_route_leak_roles_otc` | RoutingMechanism | BGP Roles and OTC Route Leak Prevention | `extract_mechanism_route_leak_roles_otc_01`<br>`extract_mechanism_route_leak_roles_otc_02`<br>`extract_mechanism_route_leak_roles_otc_03` | 显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。 |
| 10 | `mechanism_update_withdrawal` | RoutingMechanism | BGP Update and Withdrawal Propagation | `extract_mechanism_update_withdrawal_01`<br>`extract_mechanism_update_withdrawal_02`<br>`extract_mechanism_update_withdrawal_03` | 显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。 |

## 跳过事项

- 未自动批准、拒绝或改写实体。
- 未判断摘录是否足以支持实体字段。
- `blocked_by_llm` 只作为状态保留，当前不执行语义流程或 LLM。
