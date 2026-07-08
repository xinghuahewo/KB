# 阶段 B：层级 Chunk 与混合检索设计

## 1. 目标与范围

阶段 B 在清洗 v2 的 Canonical Block 权威层之上建立层级 chunk、可替换的混合召回、模型精排和受 token 预算约束的上下文回扩能力。

本阶段交付以下能力：

- 每个 v2 chunk 可稳定追溯到父 section，并可定位前后相邻 chunk。
- 使用 BM25 与 BGE-M3 进行混合召回，固定召回 `top_k=20`。
- 使用 `BAAI/bge-reranker-v2-m3` 精排，保留调用方指定的 `top_n=5~8`。
- 根据 `fact / procedure / policy / global / auto` 组装不同形态的 context pack。
- 在确定性 token 预算、去重、父级提升和裁剪规则下生成完整引用。
- 生成 chunking/retrieval 基线与对比报告，并执行结构质量硬门禁。

本阶段不改变 v1 chunk 或 v1 回滚行为，不引入完整检索平台，不部署本地生成式 LLM。`auto` 查询分类和 `global` 摘要继续使用 DeepSeek API，并提供确定性降级路径。本阶段不重复执行完整的 v2→v1→v2 回滚演练。

## 2. 设计原则

1. **v2 权威**：section catalog 只从 v2 Canonical Block 构建。
2. **稳定身份与内容版本分离**：引用使用稳定 section ID，变更检测使用内容哈希。
3. **平台可替换**：召回、精排和组包通过稳定接口解耦，未来替换为 Elasticsearch、OpenSearch、Milvus 或其他平台时无需重写上层策略。
4. **模型优先、可审计降级**：在线服务优先使用真实模型；模型不可用时显式记录降级原因。
5. **结构门禁不依赖网络**：CI、构建和发布结构检查使用 fake/mock provider，不依赖远端 GPU 或外部 API。
6. **v1/v2 隔离**：层级字段和组包策略只对 v2 发布路径生效。

## 3. 总体架构

```text
v2 Canonical Blocks
        ↓
Section Catalog Builder
        ↓
v2 Chunks + parent/previous/next/block references
        ↓
BM25 Retriever ─┐
                 ├→ Fusion(top_k=20) → Reranker(top_n=5~8)
BGE-M3 Retriever ┘                         ↓
                                  Query Type Resolver
                                             ↓
                                    Context Assembler
                                             ↓
                            去重、父级提升、预算裁剪、引用
```

核心接口如下：

```text
Retriever.search(query, top_k=20) -> candidates
Reranker.rerank(query, candidates, top_n) -> ranked_chunks
ContextAssembler.build(query, ranked_chunks, policy) -> context_pack
```

候选结果协议与具体检索平台无关，至少保留 `chunk_id`、`doc_id`、`source_ref`、召回通道、原始排名、通道分数、融合分数和内容。未来引入完整检索平台时，只替换 `Retriever` 实现和索引构建过程。

## 4. 数据设计

### 4.1 Section Catalog

新增 `data/derived/datasets/section_catalog.jsonl`。采用“轻 catalog + 按 child/block 组装”，不重复保存完整 section 正文。

每条 section 记录至少包含：

- `section_id`
- `content_hash`
- `doc_id`
- `heading`
- `section_path`
- `section_order`
- `parent_section_id`
- `child_section_ids`
- `previous_section_id`
- `next_section_id`
- `source_ref`
- `child_chunk_ids`
- `block_ids`
- `content_chars`
- `estimated_tokens`

`section_id` 基于 `doc_id + 标题层级路径 + 同路径序号` 生成。同路径序号是相同完整标题路径在文档中的出现顺序。正文变化只更新 `content_hash`，不改变逻辑 ID。`content_hash` 基于进入该 section 的规范化、有序内容计算。

section 边界规则固定如下：

- chunk 归属最近的上级标题。
- 文档首个标题之前的无标题 Block 归入合成的文档根 section。
- 普通父片段只读取 section 直属 chunk。
- `policy/global` 的父 section 全文模式读取整个 section 子树，包含全部后代 section。
- section tree 通过 `parent_section_id` 和 `child_section_ids` 显式表达，禁止仅靠标题级别在在线组包时重新猜测。

### 4.2 v2 Chunk 扩展

v2 chunk 新增以下必填字段：

- `parent_section_id`
- `chunk_order`
- `previous_chunk_id`
- `next_chunk_id`
- `hierarchy_status`

既有 `source_block_ids` 继续作为 chunk 到 Canonical Block 的追溯依据。`hierarchy_status` 只允许 `resolved` 或 `unresolved`。`resolved` chunk 必须具有合法父 section；`unresolved` chunk 进入隔离和报告，不进入可检索发布 catalog。发布门禁要求可检索 v2 chunk 的父子和相邻关系完整、一致且无跨文档引用。

### 4.3 特殊 Block 策略

- 默认纳入：正文、列表、代码、公式、表格。
- 图片只保留资产引用，不生成模型语义解释。
- 默认排除：页眉、页脚、页码、导航碎片和重复标题。
- 表格、代码和公式不可从中间截断；预算不足时整体降级为引用或摘要占位。

实际实现按仓库现有 Canonical Block 枚举建立显式映射，未知类型默认不静默进入 context pack，并记录审计原因。

## 5. 检索与精排

### 5.1 混合召回

- BM25 使用当前 SQLite FTS5 路径。
- Dense retrieval 使用 BGE-M3。
- BM25 与 dense 各自召回前 50 个候选。
- Dense 索引继续使用版本化 `data/published/bge_m3_vector_index.jsonl` 和对应 manifest；文档向量由远端 BGE-M3 服务构建，查询向量在线调用本地优先 provider，并使用 cosine similarity 排序。
- 两路结果以 `chunk_id` 去重并使用 RRF 融合，固定 `rrf_k=60`。同一 chunk 同时命中两路时累加 RRF 分数。
- `top_k=20` 指 RRF 融合后的输出数量，不是每个通道的输入数量。
- 候选记录保留各通道原始分数、原始排名、融合分数和命中通道，以支持评测与问题诊断。
- 单通道失败时使用另一通道继续并标记降级；两路均失败时返回检索错误，不生成空的正常响应。

### 5.2 Reranker

- 默认模型：`BAAI/bge-reranker-v2-m3`。
- `top_n` 由调用方显式指定，合法范围为 5 到 8；未指定时为 5；非法值直接报错，不自动扩缩。
- 本地 GPU provider 优先，资源不足或服务不可用时才调用配置的 API provider。
- 响应记录 provider、model、模型版本、耗时和降级状态。

## 6. Query Type

允许值固定为：

```yaml
query_type:
  allowed_values: [fact, procedure, policy, global, auto]
  default: auto
```

| 类型 | 目标 | 默认相邻窗口 | 父级提升 | 父 section 全文资格 |
| --- | --- | ---: | --- | --- |
| `fact` | 精确事实、定义、参数和区别 | 1 | 否 | 无 |
| `procedure` | 流程、步骤、算法和状态机 | 2 | 是 | 无，只允许片段 |
| `policy` | 规范、条款、约束、标书和合同 | 2 | 是 | 有 |
| `global` | 总结、综述和跨章节综合 | 1 | 是 | 有，但不是默认放任全文 |
| `auto` | 未显式分类 | 取决于解析结果 | 取决于解析结果 | 取决于解析结果 |

显式 `query_type` 始终优先。`auto` 默认调用 DeepSeek API 进行受限枚举分类；失败时使用可审计规则，最终兜底 `fact`。`auto` 本身不直接获得父 section 全文资格。

## 7. Context Pack 组装

### 7.1 基本规则

每个命中必须携带：

- `doc_id`
- `section_path`
- 父 section 标题
- 原始 chunk 引用

对 `procedure/policy/global`，同一父 section 下 rerank 后有效命中子 chunk 至少 2 个时，触发父 section 片段提升。`fact` 不执行父级提升。片段先按“命中 chunk + 相邻窗口”的并集构造，不直接取首尾之间的完整正文。

- `fact` 超限时优先保留高分证据。
- `procedure` 超限时优先保持流程连续性，并允许填补小间隙。
- `policy` 强调连续性；小 section 可按全文预算纳入。
- `global` 强调多 section 和来源多样性，可在预算内纳入有限数量的父 section 全文或 DeepSeek 摘要。

确定性组装规则固定如下：

- 去重首先使用 `chunk_id`；若不同 chunk 的 `source_block_ids` 集合完全相同，再按 Block 集合去重，并保留 rerank 分更高者。
- 同一 section 内的窗口按 `chunk_order` 合并和排序。
- `procedure` 仅在两个窗口之间缺少 1 个 chunk 时填补间隙；间隙超过 1 个 chunk 时不填补。
- `policy` 从首个命中到末个命中的连续区间未超过对应预算时使用连续区间；超过时退回窗口并集。
- “小 section”指整个 section 子树未超过 `policy` 全文预算，且纳入后 context pack 仍不超过总预算。
- `global` 先按每个 `doc_id` 选择一个最高分 section，再按分数补充其他 section；全文数量和占比继续服从专用预算。
- 最终 section 组按组内最高 rerank 分降序排列；同组内部按文档顺序排列。

`global` 使用以下确定性决策树：

1. 候选父 section 至少有 2 个 rerank 命中，且 section 子树不超过单父全文预算时，优先使用全文；最多使用 2 个全文父 section。
2. 不满足全文条件时，构造命中窗口并集的原文片段。
3. 所有候选原文片段合计超过 context pack 总预算时，才调用 DeepSeek 对超限父片段生成摘要；每个摘要最多 400 tokens。
4. DeepSeek 不可用时，围绕高分命中裁剪原文片段，不阻断请求。
5. 摘要必须保留其全部来源 `included_chunk_ids` 和精确引用，不允许产生无来源摘要。
6. 裁剪时，只要预算允许，不删除某个 `doc_id` 的最后一个 context unit 而让另一个 `doc_id` 保留多个；若单个 context unit 本身超过预算，则整体删除该单位。

每个 context 输出单位至少包含：

- `context_id`
- `mode`
- `parent_section_id`
- `included_chunk_ids`
- `included_block_ids`
- `content`
- `estimated_tokens`
- `actual_tokens`
- `max_rerank_score`
- `trim_events`

引用按 context 输出单位生成，必须列出该单位包含的全部 `(chunk_id, source_ref)`，不得只引用一个代表 chunk。

### 7.2 Token 预算

- 默认 context pack 总预算：6000 tokens。
- context pack 硬上限：8000 tokens。
- 入库阶段：使用本地确定性字符估算。
- 在线组包阶段：优先使用目标模型真实 tokenizer；不可用时使用保守字符估算。

父级预算公式：

```yaml
parent_budget:
  normal_span:
    limit: min(1200, context_pack_budget * 0.30)

  policy_full_section:
    limit: min(3000, context_pack_budget * 0.50)
    max_full_parent_sections: 1

  global_full_section:
    limit: min(2000, context_pack_budget * 0.35)
    max_full_parent_sections: 2
    max_total_full_section_tokens: context_pack_budget * 0.60
```

1200 tokens 与 30% 只约束普通父 section 片段，不约束 `policy/global` 的专用全文模式。所有模式仍服从 context pack 总预算硬上限。

### 7.3 超预算裁剪顺序

1. 去重。
2. 裁相邻 chunk。
3. 将父 section 全文或较大片段降级为较小父片段。
4. 裁低分命中 chunk，并保留来源多样性约束。
5. 最后才裁 chunk 内部内容。

表格、代码和公式不得执行内部裁剪。

## 8. 模型部署

模型部署在 `root@10.99.8.28` 的 4 × NVIDIA GeForce RTX 2080 Ti 主机上，每张 GPU 显存为 11264 MiB。Embedding 与 Reranker 使用两个独立 Docker 容器，每个容器只绑定单张 GPU：

| 服务 | 模型 | 端口 | 主要接口 |
| --- | --- | ---: | --- |
| Embedding | BGE-M3 | 8011 | `POST /v1/embeddings` |
| Reranker | `BAAI/bge-reranker-v2-m3` | 8012 | `POST /v1/rerank` |

部署约束：

- Docker 通过 CDI `nvidia.com/gpu=` 设备名暴露 GPU，不使用共享全部 GPU 的参数。
- GPU 2、GPU 3 是检索模型候选池；每次运行前必须用 `nvidia-smi` 实时检查显存，再为两个容器选择两张不同且满足显存要求的卡，不得假定候选卡已空闲。
- GPU 0、GPU 1 不得由检索部署自动使用；GPU 1 保留为 Docling 默认计算路由，GPU 0 曾被其他任务占用。候选池不足两张合格卡时停止本地部署并走配置的 API 降级路径。
- 使用 `restart: unless-stopped`。
- 远端部署代码存放在 `/srv/bgpkb/retrieval-models`，模型存放在持久目录 `/srv/bgpkb/retrieval-models-models`，不使用 `/tmp`。
- 服务只监听受控内网，不暴露公网。
- `/health` 返回模型名、加载状态、设备和版本。
- 仓库中不得记录密码、私钥、token 或其他凭据。
- 部署 manifest 必须锁定 BGE-M3、reranker 和 tokenizer 的模型 revision 与文件 SHA-256；禁止只记录可漂移的模型名。

Reranker 请求协议至少包含模型、query、documents 和 `top_n`；响应包含原文索引、相关度分数、模型版本和耗时。

DeepSeek 的 query type 分类与 `global` 摘要分别使用独立、显式版本化的提示词和响应协议。评测报告必须记录提示词版本、provider 和 model；版本变化时不得与旧基线直接混算。

## 9. 故障与降级

- 本地 Embedding 不可用时，调用已配置的 embedding API provider。
- 本地 Reranker 不可用时，调用已配置的 reranker API provider。
- DeepSeek query type 分类失败时，回退可审计规则，最终兜底 `fact`。
- DeepSeek `global` 摘要失败时，不生成模型摘要，改用多 section 原文片段。
- 降级响应必须包含 `degraded=true`、`degraded_reason` 和实际 provider/model。
- 调用方可声明模型能力必须成功；此时失败直接报错，不静默降级。
- 模型不可用不阻断 section catalog、层级 chunk 等结构数据构建。

## 10. 发布与兼容性

- B 阶段能力只在 v2 发布路径启用。
- 全部生成的 v2 chunk 都必须具有 `hierarchy_status`；`unresolved` chunk 必须隔离。
- 阶段验收要求 `resolved chunk 数 ÷ 全部生成 v2 chunk 数 ≥99%`。
- 可检索发布 catalog 只接收 `resolved` chunk，其父 section 可追溯率必须为 100%。
- 可检索发布 chunk 的父子和前后链接必须 100% 正确；错误 chunk 必须隔离。
- 正式 context pack 中每个 included chunk 必须具有精确 `(chunk_id, source_ref)` 引用；缺失引用的 context unit 不得返回。
- v1 回滚保持原 schema、原数据和原 context pack 行为。
- 所有 schema 扩展采用显式版本标识，消费者不得根据字段是否偶然存在来猜测版本。

## 11. 测试与验收

### 11.1 测试层次

- 单元测试：稳定 section ID、内容哈希、父子关系、相邻关系、query type 校验、预算公式、父级提升、特殊 Block 和裁剪顺序。
- Provider 契约测试：本地 Embedding、Reranker、DeepSeek 和 API 降级；测试默认不真实联网。
- 集成测试：`BM25 + dense -> fusion -> rerank -> context pack`。
- 兼容性测试：通过 schema 和单元测试确认 v1 路径不读取 v2 层级字段，不执行完整回滚演练。
- 真实模型冒烟测试：独立运行并报告，不作为离线 CI 的前置条件。

### 11.2 评测数据与报告

新增 `src/bgpkb/pipeline/evaluate_chunking.py`，读取 `data/derived/datasets/rag_answer_eval_questions.jsonl`。关键问题由数据字段 `is_critical=true` 显式标记，不通过主题规则推断。

报告至少统计：

- 每个问题的候选 chunk 数和 rerank 后 chunk 数。
- 来源覆盖率。
- 父 section 覆盖率。
- 引用完整率。
- 相邻上下文正确率。
- 平均答案质量与关键问题质量的基线/对比变化。

指标计算口径固定如下：

- 父 section 可追溯率：`parent_section_id` 非空、目标 section 存在且 `doc_id` 一致的 v2 chunk 数，除以全部可检索 v2 chunk 数。另行报告 `resolved chunk 数 ÷ 全部生成 v2 chunk 数` 作为阶段覆盖率。
- 引用完整率：context pack 中具有精确 `(chunk_id, source_ref)` 引用的 included chunk 数，除以全部 included chunk 数。
- 相邻上下文正确率：按同一父 section 的 `chunk_order` 推导全部期望 `previous/next` 链接，实际正确链接数除以期望链接数；首尾空链接也必须正确。
- 来源覆盖率：每题命中的 `expected_source_refs` 数除以该题全部 `expected_source_refs` 数；该指标只报告，不新增发布硬门禁。
- 答案质量：复用 `run_rag_answer_eval.py` 的二元 `decision=pass/fail`，总体质量为全部样本通过率，关键问题质量为 `is_critical=true` 子集通过率。

评测数据集新增可选布尔字段 `is_critical`，缺省为 `false`。答案质量退化使用新通过率相对基线通过率下降的百分点计算，不使用相对百分比。

### 11.3 硬门禁

- 全部生成 v2 chunk 的 `resolved` 覆盖率不低于 99%。
- 可检索发布 v2 chunk 的父 section 可追溯率为 100%。
- 可检索发布 v2 chunk 的相邻关系正确率为 100%。
- 正式 context pack included chunk 的引用完整率为 100%。
- 95% 引用完整率和 98% 相邻上下文正确率保留为全量生成数据、历史样本或降级评测的最低阶段 KPI；KPI 达标不能覆盖上述发布记录级失败。

如果已有成熟答案基线：

- 总体答案通过率相对基线下降不得超过 3 个百分点。
- `is_critical=true` 样本通过率相对基线下降不得超过 5 个百分点。

如果没有成熟答案基线，先生成基线报告；B 阶段只阻断结构完整性不达标的发布。

## 12. 后续引入完整检索平台

未来引入 Elasticsearch、OpenSearch、Milvus 或其他完整检索平台时：

- 替换 BM25/dense 的索引和 `Retriever` adapter。
- 重建 v2 chunk 索引。
- 保留 section catalog、chunk 层级字段、Reranker、Query Type、Context Assembler、token budget 和评测集。

因此平台迁移是索引与适配工作，不需要推倒重写阶段 B 的上层能力。
