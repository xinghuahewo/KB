# 人工复核会话状态报告

## 范围

本报告从人工复核会话队列机械汇总每个 session 的进度、状态计数和下一条待处理实体。它不判断证据充分性，不批准或拒绝实体，也不调用 LLM。

## 摘要

- 会话数：12
- 队列实体数：112
- 已完成决策数（approved/rejected）：107
- 总完成率：95.54%
- 等待人工复核数：0
- 可显式应用数：107
- 需人工补充数：4
- LLM/语义流程阻塞数：1
- JSONL 输出：`datasets/human_review_session_status.jsonl`
- CSV 输出：`datasets/human_review_session_status.csv`
- 人工决策输入：`review_inputs/human_review_decisions.csv`

## Session 状态

| Session | 条目 | 完成率 | 等待人工 | 可应用 | 需补充 | LLM 阻塞 | 下一实体 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `review_session_001` | 10 | 100.0% | 0 | 10 | 0 | 0 | `field_aggregator` / aggregator |
| `review_session_002` | 10 | 100.0% | 0 | 10 | 0 | 0 | `field_bgp_identifier` / bgp_identifier |
| `review_session_003` | 10 | 100.0% | 0 | 10 | 0 | 0 | `field_nlri` / nlri |
| `review_session_004` | 10 | 100.0% | 0 | 10 | 0 | 0 | `field_vrp_asn` / vrp_asn |
| `review_session_005` | 10 | 100.0% | 0 | 10 | 0 | 0 | `evidence_prefix_outage` / anomaly_prefix_outage |
| `review_session_006` | 10 | 90.0% | 0 | 9 | 0 | 1 | `concept_asn` / ASN |
| `review_session_007` | 10 | 70.0% | 0 | 7 | 3 | 0 | `datasource_caida_as_relationships` / CAIDA AS Relationships |
| `review_session_008` | 10 | 90.0% | 0 | 9 | 1 | 0 | `paper_method_beam` / Learning with Semantics / BEAM |
| `review_session_009` | 10 | 100.0% | 0 | 10 | 0 | 0 | `anomaly_path_manipulation` / Path Manipulation |
| `review_session_010` | 10 | 100.0% | 0 | 10 | 0 | 0 | `datasource_ripe_ris` / RIPE RIS |
| `review_session_011` | 10 | 100.0% | 0 | 10 | 0 | 0 | `datasource_rpki_roa` / RPKI / ROA |
| `review_session_012` | 2 | 100.0% | 0 | 2 | 0 | 0 | `concept_whois_rdap` / WHOIS / RDAP |

## 跳过事项

- 未自动批准、拒绝或改写实体。
- 未判断摘录是否足以支持实体字段。
- 需要 LLM 或语义判断的条目只统计为阻塞，不在本流程处理。
