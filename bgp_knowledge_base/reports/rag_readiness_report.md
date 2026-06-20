# RAG 就绪框架报告

## 范围

本报告验收阶段四在当前设备不运行模型条件下的完整 RAG 框架。默认路径不下载 BGE-M3、不调用 DeepSeek、不启动 Milvus、不部署 Qwen/vLLM。

## Provider 与运行边界

- 当前模式：`offline_framework`
- LLM 默认 provider：`mock`
- DeepSeek：已预留 OpenAI-compatible provider，默认启用：False。
- Qwen/vLLM：已预留 OpenAI-compatible provider，默认启用：False。
- Embedding 默认 provider：`deterministic_mock`。
- BGE-M3：模型 `BAAI/bge-m3`，默认启用：False。
- BGE-M3 ColBERT/multi-vector 默认启用：False。
- Vector store 默认 provider：`mock_jsonl`。
- Milvus Lite 默认启用：False。

## RAG 索引覆盖

- Embedding manifest：`published/embedding_manifest.json`
- Embedding 输入数：2037
- 真实模型执行：False
- Vector store：mock_jsonl
- SQLite FTS5 兜底：True

## 默认可信集合

- 允许 lifecycle_status：approved
- 排除 lifecycle_status：deprecated, archived
- 排除 semantic blocker：True

## 查询验收

- 查询数：6
- 通过数：6
- 失败数：0

| 查询 | 规范化查询 | 结果数 | Top chunks |
| --- | --- | ---: | --- |
| `route leak` | `route leak` | 5 | aws_route53_crypto_hijack_2018_s001_full_005, cert_eu_china_telecom_route_leak_2019_s001_page_1_002, china_telecom_europe_route_leak_2019_s001_full_005 |
| `路由泄露` | `路由泄露 route leak route leaks RFC 7908` | 5 | rfc7908_s003_6_001, rfc9234_s005_3_1_002, rfc9234_s018_8_001 |
| `prefix hijack` | `prefix hijack` | 5 | practical_defenses_2007_s001_full_001, practical_defenses_2007_s001_full_002, bgp2vec_2020_s002_page_2_003 |
| `RPKI invalid` | `RPKI invalid resource public key infrastructure route origin validation` | 5 | rfc8210_s002_1_001, rfc8210_s034_10_002, rfc8210_s037_13_001 |
| `AS_PATH` | `AS_PATH` | 5 | context_2026_as_path_001, artemis_2018_s007_page_7_002, bear_2025_s003_page_3_001 |
| `MOAS` | `MOAS` | 5 | beam_2024_s017_page_17_002, bgp2vec_2020_s006_page_6_001, artemis_2018_s010_page_10_002 |

## Context Pack

- 输出固定为 JSON context pack，不生成自然语言最终答案。
- 每条结果必须带 `@id`、`chunk_id`、`source_ref`、`review_status` 和 `retrieval_method`。
- 策略排除实体进入 `excluded_by_policy`。

## LLM 候选边界

- 候选只写入 `datasets/*_candidates.jsonl`。
- 默认状态为 `pending_review`。
- 不改写主实体、关系、chunk 或 SQLite 主库。

## 安全与成本边界

- 不在日志、报告或 published 产物中写入 API key。
- 当前设备不运行模型，不执行真实 DeepSeek/BGE-M3/Milvus/Qwen 路径。
- 真实 provider 只在显式配置启用并满足依赖时执行。

## API 入口

- `/api/v1/retrieval/search`
- `/api/v1/retrieval/evidence`
- `/api/v1/retrieval/context-pack`
