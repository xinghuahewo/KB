---
title: "阶段 4.5 BGE-M3 混合检索 v1"
document_type: "阶段说明"
purpose: "定义阶段 4.5 的终极目标、技术选型、约束边界、交付物、验收标准和阶段 B 后的现行 provider 口径。"
scope: "阶段 4.5"
status: "已完成；阶段 B 后已升级为私有 local_http BGE-M3 服务"
last_reviewed: "2026-07-08"
---
# 阶段 4.5 BGE-M3 混合检索 v1

## 终极目标

阶段 4.5 的终极目标是：

> 使用 BGE-M3 embedding 建立混合检索较优解 v1，让 BGP KB 同时具备向量召回、BM25/关键词召回、元数据过滤、融合排序、检索评测和可追溯 context pack。

完成后，阶段四应从“能调用 DeepSeek 回答”升级为“能用可评测的混合检索稳定提供证据，再由 DeepSeek 基于证据回答”。

## 技术选型

| 模块 | 选型 | 说明 |
| --- | --- | --- |
| LLM 回答 | DeepSeek API | 复用阶段 4.1-4.4 已验证能力。 |
| embedding | 私有 `local_http` `BAAI/bge-m3` 优先，SiliconFlow 与阿里云 PAI/EAS BGE-M3 兼容 | 现行默认指向 `10.99.8.28:8011`；外部 API 仅作为备用 provider。 |
| 关键词检索 | 现有检索框架 + BM25/FTS/规则命中 | 适合 RFC、AS 编号、协议字段、专有名词和精确短语。 |
| 向量检索 | 文件化 JSONL 向量索引 v1 | 数据量小，先做可复跑和可评测；Milvus 后置。 |
| 元数据索引 | source_type、entity_type、review_status、lifecycle_status、topic | 用于过滤、加权和排序解释。 |
| 融合排序 | RRF + metadata boost | 简单稳定，可解释，便于测试。 |
| 评测 | 固定问题集 + recall@k/MRR/citation hit rate | 与阶段 4.3/4.4 的答案评测衔接。 |

## Provider 策略

阶段 4.5 不把混合检索绑定到单个厂商。阶段 B 后，默认 provider 已从外部 API 切换为私有 `local_http` 服务。

| Provider | 用途 | 环境变量 | 接口形态 |
| --- | --- | --- | --- |
| `private_bge_m3_service` / `local_http` | 现行默认路径 | 无 API key；服务地址在 `metadata/config/rag_retrieval.yaml` 固定为内网 endpoint | OpenAI-compatible `/v1/embeddings`，模型 `BAAI/bge-m3`，端口 `8011` |
| `siliconflow_bge_m3` | 外部 API 备用路径 | `SILICONFLOW_API_KEY`、可选 `SILICONFLOW_BASE_URL` | OpenAI-compatible `/v1/embeddings`，模型 `BAAI/bge-m3` |
| `aliyun_eas_bge_m3` | 外部或自托管备用路径 | `ALIYUN_BGE_M3_ENDPOINT`、`ALIYUN_BGE_M3_API_KEY` | 阿里云 PAI/EAS endpoint |
| `fake_bge_m3` | 无 key 测试 | 无 | 确定性 fake embedding，用于单元测试和 CI |

Provider 通过命令行参数显式选择，不做静默自动切换：

```text
默认使用 private_bge_m3_service/local_http
-> 私有服务不可用时按配置显式选择外部 API provider
-> 离线 CI 使用 fake/mock provider
-> 单元测试和 CI 使用 fake_bge_m3
```

## 工业化混合检索链路

```text
用户查询
-> 查询规范化与中英文术语扩展
-> BM25/关键词召回 topN
-> BGE-M3 远程查询向量召回 topN
-> 元数据过滤与加权
-> RRF 融合排序
-> context pack 生成
-> DeepSeek 基于 context pack 回答
-> 答案、引用和检索指标进入评测报告
```

推荐默认参数：

| 参数 | 默认值 |
| --- | --- |
| lexical_top_k | 50 |
| vector_top_k | 50 |
| rrf_k | 60 |
| fused_top_k | 20 |
| context_top_k | 8 |
| min_similarity | 0.50，低于阈值的真实向量结果不作为证据 |

## 约束与边界

- 当前开发设备不常驻运行 BGE-M3；真实模型常驻在 `10.99.8.28` 的私有 GPU 服务上。
- 开发设备和 CI 不下载 BGE-M3、Qwen 或其它模型权重；部署准备流程可在显式操作下下载模型并生成 lock。
- API key、endpoint、token 只从环境变量读取。
- 无外部 API key 或私有服务不可用时，测试和结构评测必须能用 fake/mock client 运行。
- 阶段 4.5 不自动写回实体、关系、chunk、术语表或人工复核状态。
- 阶段 4.5 不强制引入 Milvus、Qdrant 或其它常驻向量数据库。
- pending 实体不作为已批准实体事实进入 context pack；pending chunk 仅在关联 approved entity evidence，或来源已完成确定性处理且保留溯源时进入检索，并保持原始 pending 标签。
- `deprecated`、`archived` 或被策略排除的内容不进入默认 context pack。
- 每条检索结果必须保留 `source_ref`、`chunk_id`、`review_status`、`source_type` 和排序解释。
- 生成报告和结果文件不得包含真实 API key。

## 计划交付物

| 类型 | 路径 |
| --- | --- |
| 配置 | `config/rag_retrieval.yaml` |
| BGE-M3 远程客户端 | `src/bgpkb/service/bge_m3_remote_client.py` |
| 混合检索模块 | `src/bgpkb/service/hybrid_retrieval.py` |
| 向量索引构建脚本 | `src/bgpkb/pipeline/build_bge_m3_index.py` |
| 混合检索查询脚本 | `src/bgpkb/pipeline/query_hybrid_rag.py` |
| 混合检索评测脚本 | `src/bgpkb/pipeline/run_hybrid_retrieval_eval.py` |
| 向量索引 | `data/published/bge_m3_vector_index.jsonl`，配置真实远程 key 后生成 |
| embedding manifest | `data/published/bge_m3_embedding_manifest.json` |
| 构建报告 | `data/generated/reports/rag/bge_m3_embedding_report.md` |
| 检索评测报告 | `data/generated/reports/rag/hybrid_retrieval_eval_report.md` |
| 阶段验收文档 | `docs/stages/phase_4_5_bge_m3_hybrid_retrieval_v1.md` |

## 评测指标

| 指标 | 目标 |
| --- | --- |
| recall@5 | 路由泄露、劫持、RPKI、ROA、ASPA、route flap 等核心问题能召回预期来源。 |
| recall@8 | 中英文同义查询能稳定召回相关 chunk。 |
| MRR | 协议定义类问题的 RFC/standards 结果排名靠前。 |
| source coverage | standards、cases、papers、datasets 均能按查询意图出现。 |
| citation hit rate | RAG Answer 的引用来自当前 context pack。 |
| no-evidence rejection | 无证据问题继续拒答。 |

## 验收标准

- SiliconFlow BGE-M3 provider 支持真实调用和 fake client 测试。
- 阿里云 PAI/EAS BGE-M3 provider 保留兼容接口。
- 无 key 时不会阻塞单元测试、结构检查和离线评测。
- embedding manifest 记录模型名、provider、维度、输入数量、输入 hash 和生成时间。
- 混合检索输出 lexical score、vector score、metadata boost、fusion score 和命中原因。
- 中文“路由泄露”能扩展并召回 `route leak` 相关证据。
- RFC/标准类问题优先返回 standards 来源。
- 事件类问题优先返回 cases 来源。
- 检索评测报告列出通过、失败和需人工复核的问题。
- 当前默认真实 embedding provider 为私有 `local_http`；本机本地模型仍不作为默认路径。
- 质量检查 JSON 错误数和 Schema 错误数均为 0。
- 仓库中不包含真实 DeepSeek、SiliconFlow 或阿里云 API key。

## 当前实施结果

- 远程 provider、文件化索引构建、混合检索、CLI、API、RAG Answer 接入和阶段评测框架均已实现，并在阶段 B 中接入私有模型服务。
- embedding 输入共 58,792 条：58,560 个 chunk、112 个 entity、112 个 glossary、8 个 evidence template。
- 私有 `local_http` `BAAI/bge-m3` 已生成 58,792 条、1024 维真实向量，manifest 状态为 `complete`。
- 当前 embedding endpoint：`http://10.99.8.28:8011/v1/embeddings`，模型 revision 为 `5617a9f61b028005a4858fdac845db406aefb181`。
- 阶段 B 另部署 reranker endpoint：`http://10.99.8.28:8012/v1/rerank`，模型 revision 为 `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`。
- 当前模型服务 release：`d7f62ed1ccf6f7a0fa52142a0c39328b73ed76c92cc258dad78923f32804d8b0`。
- 真实混合检索评测 20/20 通过，Recall@5 为 89.22%，Recall@8 为 89.22%，MRR 为 0.8971，无证据拒答率为 100%。
- 初次真实评测发现无意义查询最高相似度为 0.4493，而有效查询最低最高相似度为 0.5892；据此将真实向量证据阈值设为 0.50。
- 来源类型覆盖 `case_report`、`data_doc`、`paper`、`standard`、`tool_doc`。
- 后续数据或模型变化时复用同一评测集，持续比较 Recall、MRR 和无证据拒答率。

## 参考资料

- SiliconFlow Embeddings API 文档说明 `/v1/embeddings` 接口支持 `BAAI/bge-m3`，该模型最大输入长度为 8192 tokens：https://docs.siliconflow.com/cn/api-reference/embeddings/create-embeddings
- 阿里云 PAI Model Gallery 文档说明可从 PAI 部署 `bge-m3` embedding 模型，并查看 EAS 调用 URL 和 Token：https://help.aliyun.com/zh/es/user-guide/configuration-template-pai-model-gallery
- 阿里云 DataWorks 文档将 BGE-M3 列为向量模型，并说明其支持密集检索、多向量检索、稀疏检索、最长 8192 tokens 输入和 100 多种自然语言：https://www.alibabacloud.com/help/tc/dataworks/user-guide/llm-service-management/
- BGE-M3 官方文档说明其面向多功能、多语言、多粒度检索：https://bge-model.com/bge/bge_m3.html
