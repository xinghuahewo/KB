# 人工复核来源矩阵报告

## 范围

本报告按来源聚合待人工复核实体、字段核验项、session 和证据路径，帮助人工按高复用来源批量核验。它不判断来源是否足够支持实体字段，不调用 LLM，也不修改实体状态。

## 摘要

- 来源记录数：31
- 来源-实体引用数：246
- JSONL 输出：`datasets/human_review_source_matrix.jsonl`
- CSV 输出：`datasets/human_review_source_matrix.csv`
- 人工决策输入：`review_inputs/human_review_decisions.csv`

## 按来源类型统计

- case_report：4
- data_doc：11
- manual_note：1
- paper：3
- standard：11
- tool_doc：1

## 按处理状态统计

- complete_deterministic：30
- manual_note：1

## 高复用来源前 30 个

| 来源 | 类型 | 实体数 | 字段核验项 | session | 路径 |
| --- | --- | ---: | ---: | --- | --- |
| `context_2026` | manual_note | 78 | 565 | `review_session_004`<br>`review_session_005`<br>`review_session_006`<br>`review_session_007`<br>`review_session_008`<br>`review_session_009`<br>`review_session_010`<br>`review_session_011`<br>`review_session_012` | `../context.md` |
| `rfc4271` | standard | 43 | 316 | `review_session_001`<br>`review_session_002`<br>`review_session_003`<br>`review_session_004`<br>`review_session_005`<br>`review_session_006`<br>`review_session_007`<br>`review_session_008`<br>`review_session_009`<br>`review_session_011`<br>`review_session_012` | `raw/standards/rfc4271.txt` |
| `rfc6811` | standard | 22 | 160 | `review_session_004`<br>`review_session_005`<br>`review_session_008`<br>`review_session_009`<br>`review_session_010`<br>`review_session_011` | `raw/standards/rfc6811.txt` |
| `ripe_ris_docs` | data_doc | 12 | 89 | `review_session_003`<br>`review_session_006`<br>`review_session_007`<br>`review_session_008`<br>`review_session_009`<br>`review_session_010`<br>`review_session_011` | `raw/data_docs/ripe_ris_docs.html` |
| `caida_as_relationships` | data_doc | 10 | 75 | `review_session_001`<br>`review_session_002`<br>`review_session_005`<br>`review_session_007`<br>`review_session_011` | `raw/data_docs/caida_as_relationships.html` |
| `routeviews_api_doc` | data_doc | 10 | 75 | `review_session_003`<br>`review_session_007`<br>`review_session_009`<br>`review_session_010`<br>`review_session_011` | `raw/data_docs/routeviews_api_doc.html` |
| `bear_2025` | paper | 8 | 62 | `review_session_004`<br>`review_session_005`<br>`review_session_006`<br>`review_session_009`<br>`review_session_011` | `raw/papers/bear_2025.pdf` |
| `bgpshield_2025` | paper | 8 | 61 | `review_session_004`<br>`review_session_006`<br>`review_session_007`<br>`review_session_008`<br>`review_session_009`<br>`review_session_011` | `raw/papers/bgpshield_2025.pdf` |
| `bgpstream_docs` | tool_doc | 8 | 60 | `review_session_001`<br>`review_session_006`<br>`review_session_007`<br>`review_session_008`<br>`review_session_009`<br>`review_session_011` | `raw/tools_docs/bgpstream_docs.html` |
| `rfc7908` | standard | 7 | 48 | `review_session_005`<br>`review_session_010`<br>`review_session_011` | `raw/standards/rfc7908.txt` |
| `rfc9234` | standard | 5 | 37 | `review_session_001`<br>`review_session_002`<br>`review_session_003`<br>`review_session_005`<br>`review_session_010` | `raw/standards/rfc9234.txt` |
| `caida_asrank_api` | data_doc | 4 | 33 | `review_session_001`<br>`review_session_002` | `raw/data_docs/caida_asrank_api.html` |
| `ripe_ris_raw_data` | data_doc | 4 | 30 | `review_session_001`<br>`review_session_002`<br>`review_session_003` | `raw/data_docs/ripe_ris_raw_data.html` |
| `beam_2024` | paper | 4 | 29 | `review_session_005`<br>`review_session_008`<br>`review_session_010`<br>`review_session_011` | `raw/papers/beam_2024.pdf` |
| `rfc6480` | standard | 3 | 23 | `review_session_001`<br>`review_session_002`<br>`review_session_003` | `raw/standards/rfc6480.txt` |
| `arin_aspa_doc` | data_doc | 2 | 16 | `review_session_001` | `raw/data_docs/arin_aspa_doc.html` |
| `ripe_aspa_doc` | data_doc | 2 | 16 | `review_session_001` | `raw/data_docs/ripe_aspa_doc.html` |
| `rfc8210` | standard | 2 | 15 | `review_session_003` | `raw/standards/rfc8210.txt` |
| `routeviews_archive_index` | data_doc | 2 | 15 | `review_session_001`<br>`review_session_002` | `raw/data_docs/routeviews_archive_index.html` |
| `peeringdb_api_docs` | data_doc | 1 | 9 | `review_session_003` | `raw/data_docs/peeringdb_api_docs.yaml` |
| `ripestat_api_docs` | data_doc | 1 | 9 | `review_session_003` | `raw/data_docs/ripestat_api_docs.html` |
| `facebook_outage_cloudflare_2021` | case_report | 1 | 8 | `review_session_007` | `raw/cases/facebook_outage_cloudflare_2021.html` |
| `facebook_outage_meta_2021` | case_report | 1 | 8 | `review_session_007` | `raw/cases/facebook_outage_meta_2021.html` |
| `indosat_route_leak_2014` | case_report | 1 | 8 | `review_session_007` | `raw/cases/indosat_route_leak_2014.html` |
| `ripe_ris_route_collectors` | data_doc | 1 | 8 | `review_session_003` | `raw/data_docs/ripe_ris_route_collectors.html` |
| `youtube_hijack_google_2008` | case_report | 1 | 8 | `review_session_008` | `raw/cases/youtube_hijack_google_2008.html` |
| `rfc2622` | standard | 1 | 7 | `review_session_007` | `raw/standards/rfc2622.txt` |
| `rfc3912` | standard | 1 | 7 | `review_session_012` | `raw/standards/rfc3912.txt` |
| `rfc8205` | standard | 1 | 7 | `review_session_002` | `raw/standards/rfc8205.txt` |
| `rfc9082` | standard | 1 | 7 | `review_session_012` | `raw/standards/rfc9082.txt` |

## 跳过事项

- 未判断来源是否足以批准实体。
- 未自动批准、拒绝或改写实体。
- 需要解释、归纳或证据强度判断时，仍按规则记录为 `needs_semantic_review` 或保持 `unreviewed`。
