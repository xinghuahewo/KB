# 人工复核逐字段清单报告

## 范围

本报告把待人工复核实体的结构化字段机械展开为逐字段核验清单。它只展示字段和值，不判断字段是否被来源支持，不调用 LLM，也不修改实体状态。

## 摘要

- 字段核验项数：834
- 覆盖实体数：112
- JSONL 输出：`datasets/human_review_field_checklist.jsonl`
- CSV 输出：`datasets/human_review_field_checklist.csv`
- 人工决策输入：`review_inputs/human_review_decisions.csv`

## 按实体类型统计

- AnomalyType：72
- BGPConcept：217
- Case：40
- DataField：256
- DataSource：81
- EvidenceTemplate：40
- FalsePositivePattern：20
- PaperMethod：24
- RoutingMechanism：84

## 高频字段

- source_refs：112
- name：101
- definition：55
- category：48
- used_for：44
- belongs_to：32
- common_errors：32
- interpretation_rules：32
- meaning：32
- type：32
- aliases：31
- common_misunderstandings：31
- related_terms：31
- limitations：24
- evidence：17
- optional_evidence：16
- required_evidence：16
- depends_on：12
- applies_to：12
- data_objects：9

## 按 session 统计

- review_session_001：76
- review_session_002：80
- review_session_003：81
- review_session_004：64
- review_session_005：64
- review_session_006：74
- review_session_007：76
- review_session_008：77
- review_session_009：78
- review_session_010：77
- review_session_011：73
- review_session_012：14

## 前 20 个核验项

| Session | 实体 | 字段 | 值预览 | 提示 |
| --- | --- | --- | --- | --- |
| `review_session_001` | `field_aggregator` | `belongs_to` | ["BGP Update", "Path Attributes"] | 核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。 |
| `review_session_001` | `field_aggregator` | `common_errors` | ["Treating AGGREGATOR as the prefix origin AS."] | 核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。 |
| `review_session_001` | `field_aggregator` | `interpretation_rules` | ["Use with ATOMIC_AGGREGATE and AS_PATH context to interpret summarized routes."] | 核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。 |
| `review_session_001` | `field_aggregator` | `meaning` | "AGGREGATOR identifies the AS and BGP speaker that performed route aggregation when the attribute is present." | 核对该文字字段是否能在来源或摘录中找到直接支撑；不能直接确认时不要批准。 |
| `review_session_001` | `field_aggregator` | `name` | "aggregator" | 核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。 |
| `review_session_001` | `field_aggregator` | `source_refs` | ["rfc4271"] | 核对 source_refs 是否都是当前实体字段的直接或必要来源；缺少直接证据时保持 pending 或标记 needs_source。 |
| `review_session_001` | `field_aggregator` | `type` | "object" | 核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。 |
| `review_session_001` | `field_aggregator` | `used_for` | ["aggregation provenance", "route summarization context"] | 核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。 |
| `review_session_001` | `datasource_aspa` | `category` | "RPKI path authorization" | 核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。 |
| `review_session_001` | `datasource_aspa` | `data_objects` | ["ASPA object", "customer AS", "provider AS set", "ASPA validation result"] | 核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。 |
| `review_session_001` | `datasource_aspa` | `description` | "Autonomous System Provider Authorization records allow an AS holder to authorize upstream provider ASNs and support BGP path verification and route-leak prevention work." | 核对该文字字段是否能在来源或摘录中找到直接支撑；不能直接确认时不要批准。 |
| `review_session_001` | `datasource_aspa` | `limitations` | ["ASPA deployment is partial, so unknown paths must be handled carefully.", "Provider lists must be kept up to date or valid routes may be rejected.", "ASPA does not replace raw BGP evidence or operator policy context."] | 核对该限制或误报边界是否被来源直接支持；需要归纳判断时标记 needs_semantic_review。 |
| `review_session_001` | `datasource_aspa` | `name` | "ASPA" | 核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。 |
| `review_session_001` | `datasource_aspa` | `related_tools` | ["RPKI validators", "rpki-rtr"] | 核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。 |
| `review_session_001` | `datasource_aspa` | `source_refs` | ["arin_aspa_doc", "ripe_aspa_doc", "rfc6480"] | 核对 source_refs 是否都是当前实体字段的直接或必要来源；缺少直接证据时保持 pending 或标记 needs_source。 |
| `review_session_001` | `datasource_aspa` | `suitable_for` | ["route leak prevention", "BGP path plausibility checks", "provider authorization checks", "ASPA-aware route validation"] | 核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。 |
| `review_session_001` | `datasource_aspa` | `time_granularity` | {"validation": "depends on RPKI repository and validator refresh"} | 核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。 |
| `review_session_001` | `mechanism_aspa_path_verification` | `definition` | "ASPA-based path verification uses RPKI ASPA objects that authorize upstream providers to evaluate whether AS paths are plausible with respect to provider relationships." | 核对该文字字段是否能在来源或摘录中找到直接支撑；不能直接确认时不要批准。 |
| `review_session_001` | `mechanism_aspa_path_verification` | `depends_on` | ["ASPA object", "RPKI", "Provider AS Set", "AS_PATH"] | 核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。 |
| `review_session_001` | `mechanism_aspa_path_verification` | `evidence` | ["ASPA objects", "AS_PATH", "provider authorization set"] | 核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。 |

## 跳过事项

- 未判断字段是否被来源充分支持。
- 未自动批准、拒绝或改写实体。
- 需要解释、归纳或证据强度判断时，仍按规则记录为 `needs_semantic_review` 或保持 `unreviewed`。
