# 人工复核证据摘录报告

## 范围

本报告从人工复核工作簿、实体复核包和现有 chunks 机械生成。它只摘录 chunk 文本并记录词项匹配，不判断来源是否支持实体字段。

## 摘要

- 覆盖实体数：112
- 摘录记录数：672
- 每个实体最多摘录数：6
- 缺失 chunk 引用数：0
- 零词项匹配摘录数：0
- JSONL 输出：`datasets/human_review_evidence_extracts.jsonl`
- CSV 输出：`datasets/human_review_evidence_extracts.csv`

## 按实体类型统计

- AnomalyType：48
- BGPConcept：186
- Case：30
- DataField：192
- DataSource：54
- EvidenceTemplate：48
- FalsePositivePattern：24
- PaperMethod：18
- RoutingMechanism：72

## 按复核批次统计

- 01_ready_without_manual_note：204
- 02_ready_with_manual_note：468

## 前 20 条摘录索引

| 实体 | 名称 | chunk | 分数 | 匹配词项 |
| --- | --- | --- | ---: | --- |
| `field_aggregator` | aggregator | `rfc4271_s026_4_002` | 12 | aggregator, as_path, atomic_aggregate, attribute, attributes, context, origin, path |
| `field_aggregator` | aggregator | `rfc4271_s076_10_003` | 12 | aggregation, aggregator, as_path, atomic_aggregate, attribute, path, prefix, rfc4271 |
| `field_aggregator` | aggregator | `rfc4271_s021_2_002` | 10 | aggregator, attribute, attributes, path, prefix, rfc4271, routes, speaker |
| `field_aggregator` | aggregator | `rfc4271_s006_1_1_002` | 9 | attribute, attributes, path, prefix, rfc4271, routes, speaker, update |
| `field_aggregator` | aggregator | `rfc4271_s010_3_1_001` | 9 | attribute, attributes, path, prefix, rfc4271, routes, speaker, update |
| `field_aggregator` | aggregator | `rfc4271_s015_4_3_002` | 9 | attribute, attributes, path, prefix, present, rfc4271, routes, update |
| `datasource_aspa` | ASPA | `arin_aspa_doc_s001_full_002` | 13 | allow, arin_aspa_doc, aspa, authorization, authorize, autonomous, customer, holder |
| `datasource_aspa` | ASPA | `arin_aspa_doc_s001_full_001` | 9 | arin_aspa_doc, aspa, authorization, autonomous, provider, records, rpki, set |
| `datasource_aspa` | ASPA | `arin_aspa_doc_s001_full_004` | 9 | arin_aspa_doc, aspa, authorization, autonomous, object, provider, rpki, set |
| `datasource_aspa` | ASPA | `rfc6480_s002_1_001` | 9 | authorization, authorize, autonomous, holder, object, rfc6480, rpki, set |
| `datasource_aspa` | ASPA | `rfc6480_s002_1_003` | 8 | authorization, authorize, autonomous, object, rfc6480, rpki, system, validation |
| `datasource_aspa` | ASPA | `arin_aspa_doc_s001_full_003` | 7 | arin_aspa_doc, aspa, authorization, autonomous, provider, rpki, system |
| `mechanism_aspa_path_verification` | ASPA Path Verification | `ripe_aspa_doc_s001_full_007` | 14 | are, aspa, authorization, evaluate, objects, path, paths, plausible |
| `mechanism_aspa_path_verification` | ASPA Path Verification | `ripe_aspa_doc_s001_full_008` | 11 | are, aspa, authorization, path, paths, plausible, provider, providers |
| `mechanism_aspa_path_verification` | ASPA Path Verification | `ripe_aspa_doc_s001_full_009` | 11 | are, as_path, aspa, aspa-based, authorization, path, paths, provider |
| `mechanism_aspa_path_verification` | ASPA Path Verification | `ripe_aspa_doc_s001_full_010` | 11 | are, aspa, authorization, objects, path, paths, provider, ripe_aspa_doc |
| `mechanism_aspa_path_verification` | ASPA Path Verification | `ripe_aspa_doc_s001_full_006` | 10 | are, aspa, authorization, path, provider, providers, ripe_aspa_doc, rpki |
| `mechanism_aspa_path_verification` | ASPA Path Verification | `arin_aspa_doc_s001_full_001` | 7 | are, arin_aspa_doc, aspa, authorization, provider, rpki, set |
| `field_asrank_rank` | asrank_rank | `caida_asrank_api_s001_full_001` | 12 | asrank, caida, caida_asrank_api, does, high, low, not, only |
| `field_asrank_rank` | asrank_rank | `caida_asrank_api_s001_full_002` | 6 | asrank, caida, caida_asrank_api, low, rank, use |

## 跳过事项

- 未判断摘录是否足以批准实体。
- 未从摘录中抽取新实体、关系或案例字段。
- 未处理需要语义判断或 LLM 的复核事项。
