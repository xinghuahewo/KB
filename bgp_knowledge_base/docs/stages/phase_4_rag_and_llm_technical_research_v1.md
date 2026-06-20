---
title: "BGP KB 阶段四 LLM 辅助知识加工与 RAG 就绪技术调研 v1"
document_type: "技术调研文档"
purpose: "定义阶段四在引入 LLM、embedding、向量索引和混合检索前必须完成的调研范围、方案比选、风险边界和 PoC 验收标准。"
scope: "LLM 辅助知识加工、chunk 语义增强、embedding、向量索引、混合检索、RAG context pack 和服务接口边界"
status: "调研草案"
last_reviewed: "2026-06-19"
---
# BGP KB 阶段四 LLM 辅助知识加工与 RAG 就绪技术调研 v1

## 1. 调研结论摘要

阶段四不应直接从“选择向量库”开始。当前 BGP KB 已有确定性数据底座、SQLite 发布包、只读 FastAPI 服务、生命周期治理和语义质量报告；阶段四前还应先完成轻量语义标识前置，至少冻结 JSON-LD `@context`、`bgpkb:` 命名空间和 URI/ID 规则。前序阶段仍有一批明确记录的 LLM 跳过项，包括 PaperMethod 结构化抽取、案例语义字段扩展、source-derived chunk 到实体关系推断、术语别名补全、定义润色和主题覆盖充分性判断。

阶段四的核心目标不是“让知识库能问答”，而是让 BGP KB 可以稳定、可追溯、可审计地向 RAG 或 Agent 提供可信上下文。因此，阶段四暂时不把自然语言答案生成作为交付目标，也不允许 LLM 自动改实体、自动批准实体或自动扩展关系表。

因此，阶段四应拆成两个连续子阶段：

1. `4A: LLM 辅助知识加工调研与 PoC`
   - 先解决 chunk、实体、证据、术语和人工复核辅助问题。
   - LLM 只生成候选结构化输出，不直接批准实体、不覆盖已批准事实。

2. `4B: RAG 就绪与混合检索调研与 PoC`
   - 在高质量 chunk 和语义元数据基础上，再评估 embedding、向量索引、混合检索、rerank 和 context pack。
   - 默认可信集合仅包含 `lifecycle_status=approved` 且无 blocker 的实体。

推荐路线是：

```text
先做 LLM 辅助知识加工 PoC
  -> 形成 chunk/实体/证据增强候选
  -> 人工复核与审计
  -> 再做 embedding 与混合检索 PoC
  -> 最后决定生产级向量库和服务接口
```

## 2. 当前项目基线

当前已具备的阶段四前置条件：

| 能力 | 当前状态 | 证据 |
| --- | --- | --- |
| 确定性流水线 | 已通过 | `reports/pipeline_report.md` |
| 发布包 | 已通过完整性校验 | `published/`、`published/bgp_knowledge_base.sqlite` |
| chunk 库 | 已生成 2037 条 | `chunks/`、`published/chunk_catalog.jsonl` |
| 实体库 | 已生成 112 条 | `entities/`、`published/entity_catalog.jsonl` |
| 生命周期治理 | 已建立 v1 | `reports/lifecycle_report.md` |
| 语义质量治理 | 已建立 v1 | `reports/semantic_quality_report.md` |
| 语义标识前置 | 待建设 | `docs/roadmap/phase_solution_matrix_v1.md` |
| 服务化查询 | 已有只读 REST 和页面 | `service/` |
| LLM 跳过记录 | 已明确记录 | `reports/llm_processing_skip_report.md` |

当前仍需处理的关键问题：

- 5 个 `candidate/pending` 实体尚未完全进入高可信集合，其中 4 个是 Case，1 个是 PaperMethod。
- 13 个 warning 和 3 个 info 级语义 findings 仍待处理。
- 当前 chunk 主要由确定性规则生成，缺少语义标题、摘要、证据类型、关键词、中英文同义映射和问题覆盖标签。
- 当前服务层有 SQLite/FTS 查询能力，但没有 embedding、向量索引、rerank、context pack 或 RAG 专用接口。

## 3. 调研原则

### 3.1 先治理，再检索

如果 chunk 和实体语义标签质量不稳，向量库只能放大噪声。阶段四必须先评估 LLM 如何补强知识加工，再评估 RAG 基础设施。

### 3.2 LLM 只做候选，不做审批

LLM 可以生成：

- chunk 摘要候选。
- chunk 主题标签候选。
- chunk 证据类型候选。
- PaperMethod 字段候选。
- Case 角色、影响范围、证据链候选。
- EvidenceTemplate 到 DataField/BGPConcept 的映射候选。
- 术语别名和中英文对齐候选。

LLM 不允许直接执行：

- 自动把 `pending` 改为 `approved`。
- 自动覆盖已批准实体定义。
- 无来源地生成事实。
- 无人工审计地扩展关系表。
- 把 candidate 实体放入默认可信 RAG 集合。

### 3.3 所有候选输出必须结构化

LLM 输出必须符合 JSON Schema 或等价结构约束，并进入候选数据集、审计报告和人工复核流程。OpenAI Structured Outputs 文档说明，结构化输出可让模型响应遵循提供的 JSON Schema；Anthropic 也提供 JSON outputs / tool use 形式的结构化输出能力。阶段四不应使用自由文本作为可入库结果。

参考：

- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Anthropic Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [Anthropic Tool Use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

### 3.4 检索结果必须保留治理边界

RAG 检索结果必须返回：

- `entity_id`
- `chunk_id`
- `source_ref`
- `source_id`
- `review_status`
- `lifecycle_status`
- `semantic_quality_level`
- `evidence_type`
- `retrieval_method`
- `score`

缺少这些字段的结果不能进入 context pack。

## 4. 需要调研的 LLM 辅助知识加工点

### 4.1 chunk 语义增强

当前 chunk 是阶段四最重要的前置问题。调研不应只问“向量检索效果如何”，还要问“被向量化的文本是否适合检索”。

建议为每个 chunk 研究以下增强字段：

| 字段 | 作用 | LLM 介入方式 | 是否可自动入库 |
| --- | --- | --- | --- |
| `semantic_title` | 提升搜索结果可读性 | 生成候选标题 | 否，先进入候选数据集 |
| `summary` | 支持 context pack 压缩 | 生成 1-3 句摘要 | 否 |
| `keywords` | 增强 lexical/FTS 召回 | 提取候选关键词 | 否 |
| `topic_tags` | 支持主题过滤 | 映射到 `config/topic_taxonomy.yaml` | 否 |
| `evidence_type` | 区分定义、机制、案例、字段、方法证据 | 分类候选 | 否 |
| `question_coverage` | 标记可回答的问题类型 | 生成候选问题 | 否 |
| `entity_mentions` | 连接 chunk 与实体 | 候选实体链接 | 否 |
| `language_pair_terms` | 中英文术语对齐 | 候选别名映射 | 否 |

候选 chunk 技术路线：

| 路线 | 说明 | 优点 | 风险 |
| --- | --- | --- | --- |
| 保留现有 chunk，仅补元数据 | 不改变 `chunk_id` 和内容，只新增候选增强层 | 对现有发布包影响最小 | 无法修复切分边界问题 |
| 语义重切分候选 | 基于句子相似度或段落结构生成新候选 chunk | 可能显著提升召回质量 | 会影响稳定 ID、引用和回归测试 |
| 双轨 chunk | 保留原 chunk 作为证据层，新增 semantic chunk 作为检索层 | 兼顾溯源和检索质量 | 数据模型更复杂 |

推荐先采用“双轨 chunk”调研：原始 deterministic chunk 保持不变，新增 `semantic_chunk_candidates` 作为 PoC 输出。只有通过人工复核和回归测试后，才考虑成为发布层资产。

可参考的技术资料：

- LangChain RecursiveCharacterTextSplitter 文档说明它按分隔符递归切分，尽量保留段落、句子和词组等相对强相关片段：[LangChain recursive splitter](https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter)
- LlamaIndex SemanticSplitterNodeParser 文档说明 semantic splitter 会基于 embedding 相似度在句子之间自适应选择断点：[LlamaIndex semantic splitter](https://developers.llamaindex.ai/python/framework-api-reference/node_parsers/semantic_splitter/)

### 4.2 PaperMethod 结构化抽取

当前跳过项中明确记录“从论文正文中抽取结构化 PaperMethod”需要语义判断。阶段四应调研 LLM 是否可生成以下候选字段：

- `problem`
- `input_data`
- `method_steps`
- `model_or_algorithm`
- `output`
- `evaluation_dataset`
- `limitations`
- `bgp_objects_used`
- `anomaly_types_supported`
- `source_chunk_ids`
- `confidence_reason`

准入要求：

- 必须引用 `paper_chunks.jsonl` 中的 chunk。
- 每个字段必须带 `source_chunk_ids`。
- 不允许把论文没有明确表达的内容写成事实。
- 输出只进入 `review_inputs/` 或 `datasets/*_candidates.*`。

### 4.3 Case 语义字段扩展

当前案例来源已有机械观察值，但事件角色、受影响范围、证据强度和归因边界仍需语义流程。阶段四应调研：

- `involved_asns`
- `victim_as`
- `leaking_or_hijacking_as`
- `affected_prefixes`
- `event_start`
- `event_end`
- `impact_scope`
- `evidence_strength`
- `anomaly_type_mapping`
- `false_positive_risks`
- `source_chunk_ids`

准入要求：

- LLM 候选必须和 `datasets/case_observations.*` 对照。
- 所有 ASN、prefix、时间和角色字段必须可追溯到 chunk。
- “攻击者”“受害者”等高风险标签必须默认进入人工复核，不可自动确认。

### 4.4 EvidenceTemplate 映射补强

当前语义质量报告中 `evidence_template_field_mapping` 有 8 条 warning。阶段四应调研 LLM 是否能辅助把 required evidence 映射到：

- `DataField`
- `BGPConcept`
- `DataSource`
- `Relationship`

输出必须是候选映射，不直接修改 `relationships/relationships.jsonl`。

### 4.5 术语别名与中英文对齐

当前术语表是从实体机械派生的，别名和中文术语不足会影响中文查询。阶段四应调研：

- `route leak` / `路由泄露`
- `prefix hijack` / `前缀劫持`
- `subprefix hijack` / `子前缀劫持`
- `AS_PATH` / `AS 路径`
- `RPKI invalid` / `RPKI 无效`
- `origin AS` / `起源 AS`
- `MOAS` / `多源 AS`
- `route flap` / `路由震荡`

候选别名必须保留：

- 来源 chunk。
- 对应实体。
- 是否缩写。
- 是否中文直译。
- 是否行业常用译法。

## 5. embedding 模型调研

### 5.1 评价维度

embedding 模型必须按以下维度比较：

| 维度 | 说明 |
| --- | --- |
| 中英文混合检索 | 中文查询召回英文 BGP 知识的能力 |
| 专业术语保真 | AS_PATH、RPKI、ROA、MOAS、route leak 等术语表现 |
| 长文本支持 | 是否能处理较长 chunk 或上下文摘要 |
| 成本 | API token 成本或本地推理成本 |
| 可复现性 | 模型版本、向量维度和重建索引成本 |
| 隐私 | 是否需要把资料发到外部 API |
| 批处理能力 | 是否适合离线构建 2037+ chunk 的向量 |
| 服务复杂度 | 是否需要 GPU、模型服务、缓存和重试 |
| rerank 支持 | 是否有同生态 reranker 或 cross-encoder |

### 5.2 候选模型方向

| 方向 | 代表 | 适用性 | 初步判断 |
| --- | --- | --- | --- |
| API embedding | OpenAI `text-embedding-3-*` | 快速 PoC、低运维 | 适合先做小样本对照，但需评估数据外发和成本 |
| 本地多语言 embedding | BGE-M3、multilingual E5 | 中英混合、可复现、离线构建 | 更适合长期自主管理 |
| SentenceTransformers 生态 | 多种 bi-encoder / reranker / sparse encoder | 易实验、模型选择丰富 | 适合作为评测框架和模型加载层 |

参考资料：

- OpenAI embedding 文档说明当前提供第三代 embedding 模型，并按输入 token 计费：[OpenAI embeddings](https://developers.openai.com/api/docs/guides/embeddings)
- BGE-M3 文档说明其支持 dense retrieval、multi-vector retrieval、sparse retrieval，支持多语言和最长 8192 token 粒度：[BGE-M3 docs](https://bge-model.com/bge/bge_m3.html)
- BGE-M3 论文说明该模型支持 100+ 工作语言，并同时支持 dense、multi-vector、sparse 检索：[M3-Embedding paper](https://arxiv.org/abs/2402.03216)
- Multilingual E5 技术报告说明其提供 small/base/large 多种尺寸，在效率和质量之间取舍，并使用大规模多语言文本对训练：[Multilingual E5 paper](https://arxiv.org/abs/2402.05672)
- SentenceTransformers 文档说明其支持 embedding、reranker 和 sparse encoder，并有大量预训练模型可用：[SentenceTransformers docs](https://sbert.net/)

### 5.3 初步推荐

PoC 阶段至少比较两类模型：

1. API 模型：快速建立上限基线。
2. 本地模型：建立可复现、可离线运行的生产候选。

不要只测英文 query。必须包含中文查询、英文查询、缩写查询和混合查询。

## 6. 向量索引与混合检索调研

### 6.1 当前 SQLite/FTS 的位置

SQLite FTS5 是当前项目最自然的 lexical baseline。SQLite 官方文档说明 FTS5 是 SQLite 的全文搜索虚拟表模块，可用于在大文本集合中高效搜索包含查询词的文档。

参考：[SQLite FTS5](https://sqlite.org/fts5.html)

阶段四不应替代 SQLite，而应把 SQLite 作为：

- 权威发布包。
- metadata filter 来源。
- FTS/BM25 baseline。
- 结果回填与溯源查询层。

### 6.2 候选向量索引

| 方案 | 优点 | 风险 | 适用阶段 |
| --- | --- | --- | --- |
| SQLite FTS + rerank，无向量库 | 最小依赖，便于验证 chunk/术语增强价值 | 无法验证真正语义召回 | 4A 前置基线 |
| FAISS | 高效 dense vector 检索，适合本地离线 PoC | metadata filter 和服务化能力需自行补 | 4B 本地 PoC |
| Chroma | 支持 embedding、metadata、dense/sparse/hybrid/full-text 能力，开发门槛低 | 生产治理和部署策略需评估 | 4B 快速 PoC |
| Qdrant | 对 hybrid dense+sparse、过滤、服务化更成熟 | 引入独立服务，运维复杂度更高 | 生产候选 |

参考资料：

- FAISS 官方文档说明其是用于 dense vector 高效相似度搜索和聚类的库：[FAISS docs](https://faiss.ai/index.html)
- Chroma 文档说明其支持存储 embedding 和 metadata、dense/sparse/hybrid search、full-text/regex 和 metadata filtering：[Chroma docs](https://docs.trychroma.com/docs/overview/introduction)
- Qdrant hybrid search 文档说明混合检索常用于结合 dense vector 的语义理解和 sparse vector 的精确词匹配，并提醒不同分数尺度直接线性加权不可靠，RRF 或 DBSF 更稳妥：[Qdrant hybrid search](https://qdrant.tech/documentation/search/hybrid-queries/)

### 6.3 初步推荐

PoC 顺序建议：

1. SQLite FTS baseline：测当前搜索能力。
2. SQLite FTS + 术语别名扩展：测中文召回改善。
3. FAISS 或 Chroma 本地向量 PoC：快速验证 embedding 价值。
4. Qdrant hybrid PoC：验证 dense+sparse+filter+RRF/DBSF。
5. 再决定是否把 Qdrant 作为生产候选。

## 7. RAG context pack 设计候选

阶段四不应直接做“问答生成”。应先提供可被问答系统消费的 context pack。

建议 context pack 结构：

```json
{
  "query": "路由泄露",
  "policy": {
    "trusted_only": true,
    "allowed_lifecycle_statuses": ["approved"],
    "exclude_semantic_blockers": true
  },
  "entities": [],
  "evidence_templates": [],
  "chunks": [],
  "sources": [],
  "relationships": [],
  "excluded": [],
  "trace": {
    "retrieval_methods": ["fts", "vector", "rerank"],
    "index_version": "string",
    "generated_at": "string"
  }
}
```

context pack 必须支持：

- 按实体类型过滤。
- 按来源类型过滤。
- 按 review/lifecycle 状态过滤。
- 展示被排除结果及原因。
- 限制 token 预算。
- 保留 chunk 到 source 的链路。
- 保留 evidence template 到 anomaly type 的链路。

context pack 中每条结果至少应保留以下字段：

```json
{
  "id": "",
  "type": "",
  "title": "",
  "text": "",
  "source_ref": "",
  "source_id": "",
  "chunk_id": "",
  "entity_id": "",
  "review_status": "",
  "lifecycle_status": "",
  "semantic_quality_level": "",
  "retrieval_method": "",
  "score": 0.0
}
```

## 8. API 边界调研

阶段四可规划但不应立即实现的接口：

| 接口 | 目的 | 是否生成答案 |
| --- | --- | --- |
| `/api/v1/retrieval/search` | 返回混合检索结果 | 否 |
| `/api/v1/retrieval/evidence` | 围绕实体或异常类型返回证据 | 否 |
| `/api/v1/retrieval/context-pack` | 返回可供 RAG 使用的上下文包 | 否 |
| `/api/v1/retrieval/evaluate` | 运行固定查询集评测 | 否 |

接口不负责：

- 生成自然语言最终答案。
- 调用 LLM 自动判断事实。
- 写入实体、关系或审批状态。
- 隐式包含 candidate/pending 结果。
- 替代人工复核。

## 9. PoC 查询集

PoC 必须覆盖英文、中文、缩写、案例和机制类查询。

| 查询 | 目标 |
| --- | --- |
| `route leak` | 召回 Route Leak 异常类型、证据模板、RFC7908、案例 chunk |
| `路由泄露` | 召回英文 route leak 相关实体和 chunk |
| `prefix hijack` | 召回 Prefix Hijack、Subprefix Hijack、相关证据字段 |
| `AS_PATH` | 召回 AS_PATH 概念、路径操纵、BEAR/BGPShield 相关 chunk |
| `RPKI invalid` | 召回 RPKI、ROA、ROV、ROA Misconfiguration 相关知识 |
| `Facebook outage` | 召回 Facebook 2021 outage 相关案例，且如果仍是 candidate 要明确标出 |
| `BGP community` | 用于验证知识覆盖缺口，不应伪造不存在实体 |
| `MOAS` | 召回 MOAS 异常类型、误报边界和证据模板 |

## 10. PoC 验收指标

### 10.1 检索质量

- 每个固定查询 top 5 至少包含 1 个目标实体或目标 evidence template。
- 中文“路由泄露”必须召回英文 Route Leak 相关知识。
- 缩写查询 `AS_PATH`、`MOAS`、`RPKI` 不应被改写丢失。
- candidate/pending 结果默认不进入 trusted context pack。

### 10.2 溯源完整性

每条返回结果必须包含：

- `source_ref`
- `chunk_id` 或 `entity_id`
- `review_status`
- `lifecycle_status`
- `retrieval_method`
- `score`

### 10.3 治理一致性

- 语义 blocker 结果默认排除。
- candidate 结果可在非 trusted 模式展示，但必须标明原因。
- LLM 生成候选不能直接修改发布包。
- 所有候选输出必须可重复审计。

### 10.4 回归稳定性

- 向量索引必须有 manifest，记录模型名、维度、输入文件 hash、生成时间。
- embedding 模型变更必须触发全量重建索引。
- 检索评测报告必须写入 `reports/`。

## 11. 推荐阶段拆分

### 阶段 4A：LLM 辅助知识加工 PoC

交付物建议：

- `schemas/llm_chunk_enrichment_candidate.schema.json`
- `schemas/llm_case_extraction_candidate.schema.json`
- `schemas/llm_paper_method_candidate.schema.json`
- `datasets/llm_chunk_enrichment_candidates.jsonl`
- `datasets/llm_case_extraction_candidates.jsonl`
- `datasets/llm_paper_method_candidates.jsonl`
- `reports/llm_knowledge_processing_poc_report.md`

验收：

- 不改现有 approved 实体。
- 不改现有 deterministic chunk。
- 每条候选都有 `source_chunk_ids`。
- 人工复核可以按候选记录逐条接受、拒绝或要求补证据。

### 阶段 4B：embedding 与混合检索 PoC

交付物建议：

- `config/retrieval_models.yaml`
- `datasets/retrieval_eval_queries.jsonl`
- `published/vector_index_manifest.json`
- `reports/retrieval_eval_report.md`
- `service/retrieval_*` 相关只读模块草案。

验收：

- SQLite FTS baseline、向量检索和混合检索可对比。
- 每个查询的命中结果、排除结果和失败原因可解释。
- context pack 不生成答案，只组装可信上下文。

## 12. 暂不实施项

阶段四调研期间暂不做：

- 不直接上线生产向量库。
- 不直接把所有 chunk 重切分并替换原 chunk。
- 不做无审计的 LLM 自动实体抽取入库。
- 不做自然语言问答生成。
- 不做 Agent 工作流。
- 不做完整 JSON-LD/RDF 标准化出口；阶段四可以复用阶段三点五提供的 `@context` 和稳定 URI。
- 不做权限系统、多租户或用户画像。

这些事项可以进入后续路线，但不应混入阶段四 PoC。

## 13. 决策门槛

进入实现前必须回答：

1. 是否允许使用外部 API embedding 或 LLM？
2. 是否要求全流程本地可复现？
3. 是否优先保证中文查询质量？
4. 是否接受新增 semantic chunk 层，而不替换原 chunk？
5. 是否把 Qdrant 作为生产候选，还是先用 FAISS/Chroma 做本地 PoC？
6. LLM 候选进入人工复核后，谁负责批准？
7. context pack 是否只服务内部 RAG，还是需要成为公开 API？

## 14. 初步建议

本项目更适合采用保守演进路线：

```text
4A.1 固定查询集和评测指标
4A.2 LLM chunk 增强候选 schema
4A.3 小样本 chunk / Case / PaperMethod 候选生成
4A.4 人工复核候选质量
4B.1 SQLite FTS baseline
4B.2 SQLite FTS + 术语别名扩展
4B.3 BGE-M3 / OpenAI embedding 对比
4B.4 FAISS 或 Chroma 本地 PoC
4B.5 Qdrant hybrid PoC
4B.6 context pack 草案
4B.7 决定生产架构
```

最重要的判断是：阶段四的第一目标不是“能不能搜”，而是“能不能稳定、可追溯、可审计地把 BGP KB 变成可被 RAG 使用的可信上下文”。只有前序 LLM 辅助加工和治理边界跑通后，embedding 与向量库选型才有意义。
