# 阶段四 RAG 就绪与混合检索较优解实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 建立可审计、可复跑、可服务化的 RAG 就绪层，包含 DeepSeek API 候选增强、后续 Qwen/vLLM 可替换 LLM 层、BGE-M3 embedding、Milvus 混合检索、rerank、context pack 和只读 API。

**架构：** 保留现有 JSONL、SQLite 和语义标识层作为主线；新增派生候选层、检索索引层和 RAG 服务层。LLM provider 采用 OpenAI-compatible 适配层，第一阶段接 DeepSeek API，后续通过同一接口切换到本地 Qwen/vLLM；LLM 只生成候选数据，不直接改写 approved 实体。检索层使用 BGE-M3 dense+sparse 输出和 Milvus hybrid search，SQLite FTS5 作为审计、精确检索和兜底召回。

**技术栈：** Python、pytest、FastAPI、SQLite FTS5、JSONL/CSV、JSON Schema、`published/semantic_id_map.jsonl`、DeepSeek API、Qwen/vLLM OpenAI-compatible server、BAAI/BGE-M3、FlagEmbedding、Milvus Lite/Standalone、pymilvus。

---

## 约束和边界限制

### 数据与审批边界

- LLM 只能生成候选数据，所有候选必须写入 `datasets/*_candidates.jsonl`，默认状态为 `pending_review`。
- LLM 不得直接修改 `entities/*.jsonl`、`relationships/*.jsonl`、`chunks/*.jsonl`、`published/entity_catalog.jsonl` 或 SQLite 主库。
- LLM 不得把 `pending`、`candidate`、`reviewed` 实体升级为 `approved`。
- LLM 不得新增无来源事实；每个候选字段必须能追溯到 `chunk_id`、`source_ref` 或 `source_id`。
- RAG 默认可信集合只允许 `lifecycle_status=approved` 且无 blocker 的实体进入 context pack。
- `deprecated`、`archived`、策略排除实体不得进入默认 context pack；如被召回，必须进入 `excluded_by_policy` 并记录原因。

### Provider 与部署边界

- 第一阶段 LLM provider 默认为 `mock`，用于测试和离线流水线。
- 开启 DeepSeek API 必须显式设置配置开关和 `DEEPSEEK_API_KEY`；缺 key 时不能悄悄降级成真实调用失败。
- DeepSeek API 只用于候选增强，不用于最终答案生成，不用于自动审批。
- 后期 Qwen/vLLM 只通过 OpenAI-compatible endpoint 替换 provider；业务脚本不得直接绑定某个私有 SDK。
- 不在阶段四实现 Qwen 部署自动化，只预留 `base_url`、`model`、`api_key_env` 和 sampling 参数。

### Embedding 与检索边界

- 第一版真实 embedding 使用 `BAAI/bge-m3` 的 dense + sparse 输出。
- 第一版不启用 BGE-M3 ColBERT/multi-vector；ColBERT 只作为后续 rerank 增强项。
- 测试和 CI 必须使用 deterministic mock embedding，不依赖 GPU、模型下载、网络或 API key。
- Milvus Lite 只作为本地阶段四索引文件；生产部署切换到 Milvus Standalone 时必须保持 `embedding_manifest.json` 和检索 API 契约不变。
- SQLite FTS5 必须保留为精确检索、审计和无向量库兜底，不得被 Milvus 完全替换。

### 成本、性能与安全边界

- 默认只对 `published/chunk_catalog.jsonl` 中的 chunk 建索引；不索引 raw HTML/PDF 全文。
- 默认 context pack 有字符或 token 预算，超出必须截断并记录截断原因。
- 不在日志、报告或 published 产物中写入 API key、完整请求 header 或 provider secret。
- DeepSeek/Qwen 请求与响应摘要可以进入审计报告，但原始长响应不进入主发布包。
- 阶段四不生成自然语言最终答案，只生成可追溯 context pack。

---

## 文件结构

### 新增文件

- `config/rag_retrieval.yaml`：阶段四检索配置，登记可信集合规则、召回权重、rerank 参数、context pack 限制和验收查询。
- `config/llm_candidate_enrichment.yaml`：LLM 候选增强配置，登记 DeepSeek/Qwen provider、候选类型、输入范围、输出 schema、人工审计策略和禁止动作。
- `schemas/chunk_enrichment_candidate.schema.json`：chunk 语义增强候选 schema。
- `schemas/entity_link_candidate.schema.json`：chunk 到实体链接候选 schema。
- `schemas/retrieval_result.schema.json`：RAG 检索结果 schema。
- `schemas/context_pack.schema.json`：RAG context pack schema。
- `scripts/build_llm_candidate_enrichment.py`：生成或模拟 LLM 候选增强数据；默认使用 mock provider，配置允许切换 DeepSeek API。
- `scripts/build_rag_indexes.py`：构建 SQLite FTS 辅助索引、BGE-M3 embedding 缓存和 Milvus 向量索引。
- `scripts/query_rag.py`：命令行检索入口，用于验收查询。
- `scripts/build_rag_readiness_report.py`：生成阶段四报告。
- `datasets/chunk_enrichment_candidates.jsonl`：chunk 语义增强候选。
- `datasets/entity_link_candidates.jsonl`：chunk 到实体链接候选。
- `datasets/rag_query_eval.jsonl`：验收查询结果。
- `published/embedding_manifest.json`：BGE-M3 embedding 构建摘要、模型、输入哈希、dense/sparse 覆盖计数和 Milvus collection 信息。
- `published/rag_milvus.db`：Milvus Lite 本地数据库；生产环境可切换到 Milvus Standalone。
- `published/rag_retrieval_index.json`：检索索引摘要、Milvus collection、权重和过滤器说明。
- `reports/rag_readiness_report.md`：阶段四 RAG 就绪报告。
- `tests/test_llm_candidate_enrichment.py`：候选增强测试。
- `tests/test_rag_indexes.py`：BGE-M3/Milvus 索引构建测试。
- `tests/test_rag_retrieval.py`：检索、过滤和 context pack 测试。

### 修改文件

- `service/repository.py`：新增 retrieval 查询函数。
- `service/app.py`：新增 `/api/v1/retrieval/search`、`/api/v1/retrieval/evidence`、`/api/v1/retrieval/context-pack`。
- `scripts/run_pipeline.py`：接入候选增强、RAG 索引、RAG 报告。
- `scripts/build_artifact_manifest.py`：登记新增产物生产者，明确 `published/rag_milvus.db` 由 RAG 索引脚本生成。
- `scripts/quality_check.py`：校验新增 JSONL/schema/索引一致性。
- `scripts/build_data_management_report.py` 与 `config/data_management_capabilities.yaml`：登记阶段四资产与能力。
- `requirements-service.txt` 或新增 `requirements-rag.txt`：登记 `pymilvus`、`FlagEmbedding`、`openai` 等阶段四依赖。
- `config/stage_acceptance_gates.yaml`：新增 `phase_4_rag_optimal_v1` 验收门禁。
- `docs/stages/phase_4_rag_and_llm_technical_research_v1.md`：状态从调研草案更新为实施依据。
- `reports/README.md`、`docs/README.md`、`published/README.md`：加入阶段四入口。

---

### Task 1: 冻结阶段四配置与 schema

**Files:**
- Create: `config/rag_retrieval.yaml`
- Create: `config/llm_candidate_enrichment.yaml`
- Create: `schemas/chunk_enrichment_candidate.schema.json`
- Create: `schemas/entity_link_candidate.schema.json`
- Create: `schemas/retrieval_result.schema.json`
- Create: `schemas/context_pack.schema.json`
- Test: `tests/test_rag_retrieval.py`

- [ ] **Step 1: 写失败测试**

测试要求：
- `rag_retrieval.yaml` 定义默认可信集合：`approved`、无 blocker、排除 `archived/deprecated`。
- `rag_retrieval.yaml` 定义 embedding provider：生产为 `bge_m3`，测试为 `deterministic_mock`。
- `rag_retrieval.yaml` 定义 vector store：本地为 `milvus_lite`，生产可切 `milvus_standalone`。
- `llm_candidate_enrichment.yaml` 定义 provider：`mock`、`deepseek`、`qwen_vllm`，且默认 provider 为 `mock`。
- `llm_candidate_enrichment.yaml` 必须声明 `writes_primary_entities: false`、`approves_entities: false`、`generates_final_answers: false`。
- 检索结果 schema 必须包含 `@id`、`entity_id`、`chunk_id`、`source_ref`、`review_status`、`lifecycle_status`、`retrieval_method`、`score`。
- context pack schema 必须包含 `query`、`results`、`citations`、`excluded_by_policy`。

Run: `python3 -m pytest tests/test_rag_retrieval.py -v`

Expected: FAIL，因为配置和 schema 尚不存在。

- [ ] **Step 2: 实现最小配置和 schema**

配置只描述契约，不执行真实 provider。`llm_candidate_enrichment.yaml` 默认 provider 为 `mock`，DeepSeek 配置使用 OpenAI-compatible `base_url=https://api.deepseek.com`，Qwen/vLLM 配置使用本地 OpenAI-compatible endpoint，例如 `http://localhost:8000/v1`。

- [ ] **Step 3: 运行测试转绿**

Run: `python3 -m pytest tests/test_rag_retrieval.py -v`

Expected: PASS。

---

### Task 2: LLM 候选增强层

**Files:**
- Create: `scripts/build_llm_candidate_enrichment.py`
- Create: `datasets/chunk_enrichment_candidates.jsonl`
- Create: `datasets/entity_link_candidates.jsonl`
- Test: `tests/test_llm_candidate_enrichment.py`

- [ ] **Step 1: 写失败测试**

测试要求：
- 脚本默认使用 mock provider，不联网、不调用真实 LLM。
- 当 provider 配置为 `deepseek` 但 `DEEPSEEK_API_KEY` 缺失时，脚本必须失败并给出明确错误；不得静默回退到真实半成品输出。
- 当 provider 配置为 `qwen_vllm` 时，脚本只读取 OpenAI-compatible `base_url/model/api_key_env`，不得绑定 Qwen 私有 SDK。
- 每条 chunk 候选包含 `candidate_id`、`chunk_id`、`semantic_title`、`summary`、`keywords`、`evidence_type`、`source_ref`、`review_status=pending_review`、`generated_by`。
- 每条实体链接候选包含 `candidate_id`、`chunk_id`、`entity_id`、`confidence`、`source_ref`、`review_status=pending_review`。
- 候选不得修改 `entities/*.jsonl`。
- 候选不得包含 `approved` 状态，不得包含无 `chunk_id` 或无 `source_ref` 的事实字段。

Run: `python3 -m pytest tests/test_llm_candidate_enrichment.py -v`

Expected: FAIL。

- [ ] **Step 2: 实现 mock 候选生成**

从 `published/chunk_catalog.jsonl`、`published/entity_catalog.jsonl`、`published/semantic_id_map.jsonl` 读取输入。先为高价值查询相关 chunk 生成确定性 mock 候选，覆盖 route leak、prefix hijack、RPKI、AS_PATH、MOAS。DeepSeek provider 只实现接口和结构化输出校验；默认流水线不调用真实 DeepSeek。

- [ ] **Step 3: 输出报告片段**

脚本 stdout 输出写入文件、候选数量、provider、边界声明。

- [ ] **Step 4: 运行测试转绿**

Run: `python3 -m pytest tests/test_llm_candidate_enrichment.py -v`

Expected: PASS。

---

### Task 3: BGE-M3 Embedding 缓存与 Milvus 索引

**Files:**
- Create: `scripts/build_rag_indexes.py`
- Create: `published/embedding_manifest.json`
- Create: `published/rag_milvus.db`
- Create: `published/rag_retrieval_index.json`
- Create: `requirements-rag.txt`
- Test: `tests/test_rag_indexes.py`

- [ ] **Step 1: 写失败测试**

测试要求：
- 索引构建不破坏现有 `published/chunk_catalog.jsonl`。
- embedding manifest 包含 provider、model、input_count、dense_dimension、sparse_enabled、colbert_enabled、input_hash。
- 默认测试 provider 为 deterministic mock embedding，保证离线可复跑。
- 真实 provider 名称为 `bge_m3`，模型为 `BAAI/bge-m3`。
- 第一版真实索引必须启用 dense + sparse，必须禁用 ColBERT/multi-vector。
- `published/rag_milvus.db` 由 Milvus Lite 生成；如果环境缺少 `pymilvus` 或 `FlagEmbedding`，真实索引任务应给出明确缺依赖错误。
- `rag_retrieval_index.json` 必须登记 Milvus collection、SQLite FTS 兜底和 semantic id 输入。
- `requirements-rag.txt` 必须登记 `pymilvus`、`FlagEmbedding` 以及必要的模型运行依赖；服务基础依赖仍留在 `requirements-service.txt`。

Run: `python3 -m pytest tests/test_rag_indexes.py -v`

Expected: FAIL。

- [ ] **Step 2: 实现 deterministic mock embedding 与 BGE-M3 provider 接口**

使用稳定哈希生成固定维度 dense/sparse mock 输出，作为无外部依赖的测试 provider。BGE-M3 provider 使用 `FlagEmbedding` 或 `pymilvus.model.hybrid.BGEM3EmbeddingFunction`，但默认测试不下载模型。

- [ ] **Step 3: 实现 Milvus Lite 写入边界**

本地索引写入 `published/rag_milvus.db`。collection payload 至少包含 `@id`、`chunk_id`、`source_ref`、`review_status`、`source_type`、`topics`。不得把 raw HTML/PDF 全文写入 Milvus，只写 chunk content 和必要 metadata。

- [ ] **Step 4: 构建索引摘要**

`rag_retrieval_index.json` 记录：
- lexical 输入：SQLite/FTS/chunk catalog。
- vector 输入：Milvus Lite URI、collection、dense/sparse 字段。
- semantic id 输入：`semantic_id_map.jsonl`。
- embedding 输入哈希和 chunk 覆盖计数。
- 默认过滤器和权重。

- [ ] **Step 5: 运行测试转绿**

Run: `python3 -m pytest tests/test_rag_indexes.py -v`

Expected: PASS。

---

### Task 4: 混合检索与 rerank CLI

**Files:**
- Create: `scripts/query_rag.py`
- Modify: `service/repository.py`
- Test: `tests/test_rag_retrieval.py`

- [ ] **Step 1: 写失败测试**

测试要求：
- `route leak` 召回 route leak 异常类型、证据模板或相关 chunk。
- `路由泄露` 能通过别名/关键词扩展召回 route leak 相关内容。
- 每条结果包含稳定 `@id`、`source_ref`、`chunk_id`、`review_status`。
- 默认结果不包含 pending/candidate/archived/deprecated 实体作为可信实体。
- DeepSeek/Qwen 候选字段不得影响默认排序，除非候选已通过人工审计。
- Milvus 不可用时，CLI 必须能以 SQLite FTS5 fallback 模式返回可解释结果，并在 `retrieval_method` 中标记 fallback。

Run: `python3 -m pytest tests/test_rag_retrieval.py -v`

Expected: FAIL。

- [ ] **Step 2: 实现 SQLite FTS5 + BGE-M3 dense/sparse 合并**

检索流程：
1. query normalization。
2. 中文/英文术语扩展。
3. SQLite FTS5 或现有 lexical index 召回。
4. Milvus dense recall。
5. Milvus sparse recall。
6. 使用 RRF 或配置化加权融合。
7. 应用 lifecycle 和 semantic quality 过滤。
8. 注入 `@id`。
9. 记录被过滤实体到 `excluded_by_policy`。

- [ ] **Step 3: 实现 CLI**

命令：

```bash
python3 scripts/query_rag.py search "route leak" --limit 5
python3 scripts/query_rag.py context-pack "路由泄露" --limit 5
```

- [ ] **Step 4: 运行测试转绿**

Run: `python3 -m pytest tests/test_rag_retrieval.py -v`

Expected: PASS。

---

### Task 5: RAG context pack

**Files:**
- Modify: `scripts/query_rag.py`
- Modify: `service/repository.py`
- Create/Update: `datasets/rag_query_eval.jsonl`
- Test: `tests/test_rag_retrieval.py`

- [ ] **Step 1: 写失败测试**

测试要求：
- context pack 包含 `query`、`normalized_query`、`results`、`citations`、`excluded_by_policy`。
- 每个 citation 能追溯到 `source_ref` 或 `source_id`。
- context pack 有 token/字符预算，超出时按得分截断。
- 排除项记录原因，例如 `not_approved`、`semantic_blocker`。
- context pack 不包含自然语言最终答案，只包含可追溯上下文。
- context pack 不包含 API key、provider 原始 header 或未审计 LLM 长响应。

Run: `python3 -m pytest tests/test_rag_retrieval.py::test_context_pack -v`

Expected: FAIL。

- [ ] **Step 2: 实现 context pack builder**

固定模板输出 JSON，不生成自然语言答案。默认包含 chunks、相关实体、证据模板和来源引用。
结果必须引用 `published/semantic_id_map.jsonl` 中的稳定 `@id`。

- [ ] **Step 3: 生成验收查询结果**

把最小查询集写入 `datasets/rag_query_eval.jsonl`：
- `route leak`
- `路由泄露`
- `prefix hijack`
- `RPKI invalid`
- `AS_PATH`
- `MOAS`

- [ ] **Step 4: 运行测试转绿**

Run: `python3 -m pytest tests/test_rag_retrieval.py -v`

Expected: PASS。

---

### Task 6: FastAPI RAG 接口

**Files:**
- Modify: `service/app.py`
- Modify: `service/repository.py`
- Test: `tests/test_service_api.py`

- [ ] **Step 1: 写失败测试**

测试接口：
- `GET /api/v1/retrieval/search?q=route%20leak`
- `GET /api/v1/retrieval/evidence?entity_id=anomaly_route_leak`
- `GET /api/v1/retrieval/context-pack?q=路由泄露`

要求返回 JSON，字段满足 retrieval/context pack schema。

Run: `python3 -m pytest tests/test_service_api.py -v`

Expected: FAIL。

- [ ] **Step 2: 实现只读 API**

API 只读取 published/datasets，不写入候选或实体。错误时返回清晰 4xx/5xx。

- [ ] **Step 3: 运行服务测试转绿**

Run: `python3 -m pytest tests/test_service_api.py -v`

Expected: PASS。

---

### Task 7: 报告、数据管理和质量门禁

**Files:**
- Create: `scripts/build_rag_readiness_report.py`
- Create: `reports/rag_readiness_report.md`
- Modify: `scripts/run_pipeline.py`
- Modify: `scripts/build_artifact_manifest.py`
- Modify: `scripts/quality_check.py`
- Modify: `config/data_management_capabilities.yaml`
- Modify: `reports/README.md`
- Modify: `published/README.md`
- Test: `tests/test_data_management_report.py`

- [ ] **Step 1: 写失败测试**

测试要求：
- RAG 报告包含索引覆盖、查询验收、过滤策略、候选增强边界、API 入口。
- RAG 报告包含 provider 边界：DeepSeek 只做候选、Qwen/vLLM 只做兼容替换目标、BGE-M3 dense+sparse、ColBERT 暂不启用。
- RAG 报告包含安全边界：不记录 API key、不改主 JSONL、不自动审批。
- 数据管理配置登记 RAG 资产组。
- 质量检查识别新增 JSONL 和 published 产物。

Run: `python3 -m pytest tests/test_data_management_report.py -v`

Expected: FAIL。

- [ ] **Step 2: 实现报告脚本**

报告必须包含：
- `## RAG 索引覆盖`
- `## 默认可信集合`
- `## 查询验收`
- `## Context Pack`
- `## LLM 候选边界`
- `## Provider 与部署边界`
- `## 安全与成本边界`
- `## API 入口`

- [ ] **Step 3: 接入流水线和制品清单**

在 `run_pipeline.py` 中顺序放置：
1. `build_llm_candidate_enrichment.py`
2. `build_rag_indexes.py`
3. `build_rag_readiness_report.py`
4. `build_artifact_manifest.py`
5. `quality_check.py`

- [ ] **Step 4: 运行测试转绿**

Run: `python3 -m pytest tests/test_data_management_report.py -v`

Expected: PASS。

---

### Task 8: 阶段四验收门禁

**Files:**
- Modify: `config/stage_acceptance_gates.yaml`
- Modify: `tests/test_stage_acceptance.py`
- Create: `docs/stages/phase_4_rag_optimal_v1.md`

- [ ] **Step 1: 写失败测试**

测试要求：
- 新增 stage id：`phase_4_rag_optimal_v1`。
- required files 包含配置、schema、脚本、索引、报告、API 测试。
- commands 包含 RAG 索引构建、RAG 测试、服务 API 测试。
- report checks 包含 RAG 报告、pipeline 报告和 quality 报告。

Run: `python3 -m pytest tests/test_stage_acceptance.py -v`

Expected: FAIL。

- [ ] **Step 2: 增加阶段说明文档**

`docs/stages/phase_4_rag_optimal_v1.md` 用中文记录目标、交付物、验收标准、非目标和后续阶段依赖。

- [ ] **Step 3: 实现验收配置**

阶段四验收必须检查：
- `route leak` 与 `路由泄露` 查询结果。
- context pack 不包含策略排除实体。
- DeepSeek 缺少 API key 时不会隐式真实调用。
- 默认 embedding provider 为 deterministic mock，真实 provider 配置为 BGE-M3。
- ColBERT/multi-vector 默认关闭。
- RAG API 可用。
- 质量报告关键项为 0。

- [ ] **Step 4: 运行阶段验收**

Run: `python3 scripts/run_stage_acceptance.py --stage phase_4_rag_optimal_v1`

Expected: PASS。

---

### Task 9: 最终验证

**Files:**
- No new files.

- [ ] **Step 1: 运行全量测试**

Run: `python3 -m pytest -v`

Expected: 全部 PASS。

- [ ] **Step 2: 运行完整流水线**

Run: `python3 scripts/run_pipeline.py`

Expected: exit 0，`reports/pipeline_report.md` 总体状态为通过。

- [ ] **Step 3: 运行阶段四验收**

Run: `python3 scripts/run_stage_acceptance.py --stage phase_4_rag_optimal_v1`

Expected: `reports/stage_acceptance_report.md` 结论为 `pass`。

- [ ] **Step 4: 重建制品清单并跑质量检查**

Run: `python3 scripts/build_artifact_manifest.py && python3 scripts/quality_check.py`

Expected: exit 0，JSON 错误数、Schema 错误数、制品清单未登记文件数均为 0。

- [ ] **Step 5: 检查关键查询**

Run:

```bash
python3 scripts/query_rag.py search "route leak" --limit 5
python3 scripts/query_rag.py search "路由泄露" --limit 5
python3 scripts/query_rag.py context-pack "route leak" --limit 5
```

Expected: 输出包含 `source_ref`、`chunk_id`、`review_status`、`@id`，且无默认策略排除实体进入 context pack。

---

## 实施边界

- 不自动批准 pending/candidate 实体。
- 不直接改写 approved 实体事实。
- 不把 LLM 输出作为事实入主库。
- DeepSeek API 只作为候选增强 provider，缺少 `DEEPSEEK_API_KEY` 时不得执行真实调用。
- Qwen/vLLM 只作为后期 OpenAI-compatible provider 替换目标，本阶段不自动部署 Qwen。
- 第一版真实 embedding 使用 BGE-M3 dense + sparse；ColBERT/multi-vector 默认关闭。
- 测试和 CI 使用 deterministic mock embedding 建立可测试契约，不依赖模型下载、GPU、网络或 API key。
- Milvus Lite 是本地索引起点；生产切 Milvus Standalone 时不得改变检索 API 和 manifest 契约。
- SQLite FTS5 保留为精确检索和兜底，不得被向量库完全替代。
- 不迁移现有 SQLite/JSONL 主格式。
- 不在阶段四生成自然语言答案，只生成可追溯 context pack。
