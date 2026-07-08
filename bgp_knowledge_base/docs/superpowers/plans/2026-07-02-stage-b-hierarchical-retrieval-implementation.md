# 阶段 B：层级 Chunk 与混合检索实施计划

> **给智能执行者：** 必须逐任务使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 执行；所有功能与修复遵循 `superpowers:test-driven-development`，完成声明前使用 `superpowers:verification-before-completion`。步骤使用复选框跟踪。

**目标：** 在清洗 v2 权威层上交付 section catalog、层级 chunk、BM25+BGE-M3 混合召回、bge reranker 精排、query type 策略、受 token 预算约束的 context pack，以及可执行的阶段 B 结构与效果验收。

**架构：** `section_hierarchy` 从 approved Canonical Block v2 同时派生 section tree 与层级 chunk；发布层只接收 hierarchy resolved 的 v2 chunk。在线检索通过平台无关的 Retriever/Reranker/ContextAssembler 边界串联 SQLite FTS5 BM25、BGE-M3、RRF、远端 reranker、DeepSeek query type/摘要和确定性降级路径。

**技术栈：** Python 3.10+、pytest、JSON Schema、YAML、SQLite FTS5、FastAPI、Docker Compose、FlagEmbedding、PyTorch CUDA、DeepSeek API。

---

## 0. 执行约束

- 所有新增文档和报告使用中文。
- 只修改 v2 发布路径；v1 继续使用原 schema 和行为。
- 不执行完整的 v2→v1→v2 回滚演练，只做 v1/v2 schema 隔离测试。
- 不提交密码、私钥、API key、token 或服务器凭据。
- 不触碰工作区已有的 `uv.lock` 与 `src/bgpkb.egg-info/`，除非用户另行授权。
- 每个功能先写失败测试并确认失败原因，再写最小实现。
- 远端 GPU、DeepSeek 和外部 API 不进入离线 CI；使用 fake client 做契约测试。
- 真实模型制品必须记录精确 revision 与 SHA-256，不只记录可漂移的模型名。

## 1. 文件职责图

### 新建文件

- `src/bgpkb/cleaning_v2/section_hierarchy.py`：从 Canonical Block 构造 section tree、稳定 ID、内容哈希和 chunk 邻接关系。
- `src/bgpkb/service/retrievers.py`：BM25、dense Retriever 与 RRF 融合的稳定接口。
- `src/bgpkb/service/retrieval_model_client.py`：本地优先 Embedding/Reranker HTTP client 与 provider chain。
- `src/bgpkb/service/query_type_resolver.py`：显式 query type、DeepSeek 分类和规则回退。
- `src/bgpkb/service/token_budget.py`：真实 tokenizer adapter 与保守字符估算。
- `src/bgpkb/service/chunk_store.py`：按 chunk 文件和 section catalog 读取完整正文。
- `src/bgpkb/service/context_assembler.py`：父标题、相邻窗口、父片段/全文、摘要、去重和裁剪。
- `src/bgpkb/pipeline/evaluate_chunking.py`：阶段 B 指标、基线对比、中文报告和退出码。
- `metadata/schemas/section_catalog.schema.json`：section catalog 契约。
- `metadata/schemas/context_unit.schema.json`：context pack 输出单位契约。
- `tests/test_section_hierarchy.py`：section tree 和 chunk 层级派生测试。
- `tests/test_retrieval_model_client.py`：本地优先与 API 降级契约测试。
- `tests/test_retrievers.py`：BM25、dense、RRF 和通道失败测试。
- `tests/test_query_type_resolver.py`：显式类型、DeepSeek 和规则降级测试。
- `tests/test_token_budget.py`：预算公式和估算测试。
- `tests/test_context_assembler.py`：所有 query type、提升、去重和裁剪测试。
- `tests/test_chunking_evaluation.py`：指标口径、基线与硬门禁测试。
- `tests/test_retrieval_model_service.py`：GPU 服务 HTTP 契约测试，使用 fake model。
- `tests/test_gpu_device_selector.py`：GPU 排序、角色阈值、不同设备、精确 `.env` 与失败原子性测试。
- `tests/test_retrieval_model_deploy_release.py`：release symlink 切换、切换前失败和 Compose 回滚测试。
- `tests/test_release_manifest.py`：app/model/image 任一变化都会改变 release ID 的确定性测试。
- `tests/test_cleanup_release.py`：release ID、路径边界和 live link 拒删测试。
- `tests/test_stage_b_retrieval_integration.py`：完整 fake-provider 检索链路集成测试。
- `deploy/retrieval-models/Dockerfile`：CUDA/FlagEmbedding/FastAPI 镜像。
- `deploy/retrieval-models/Dockerfile.prepare`：在可联网环境下载并封存模型的小型准备镜像。
- `deploy/retrieval-models/requirements.in` 与 `requirements.lock`：锁定 GPU 服务依赖。
- `deploy/retrieval-models/service.py`：按角色提供 embeddings 或 rerank 接口。
- `deploy/retrieval-models/compose.yaml`：两个独立容器、端口、从 `.env` 读取 `EMBEDDING_GPU_CDI` 与 `RERANKER_GPU_CDI`、健康检查和持久模型卷，并拒绝两个变量指向同一 GPU。
- `deploy/retrieval-models/model_manifest.json`：模型 revision 与 SHA-256 清单。
- `deploy/retrieval-models/prepare_models.py`：按精确 revision 下载到持久目录并生成逐文件 SHA-256 锁文件。
- `deploy/retrieval-models/model_manifest.lock.json`：在本机模型准备阶段生成并提交的真实模型文件哈希清单。
- `deploy/retrieval-models/verify_runtime.py`：启动前 GPU、模型哈希与接口预检。
- `deploy/retrieval-models/gpu_policy.json`：声明 `allowed_indices=[2,3]` 及 Embedding/Reranker 各自的最低空闲显存 8192 MiB。
- `deploy/retrieval-models/select_gpu_devices.py`：按策略查询和选择两张不同 GPU，原子生成不入库的 `.env`；失败时保留旧文件且不得自动使用 GPU 0 或 GPU 1。
- `deploy/retrieval-models/build_release_manifest.py`：规范化哈希 app 部署树、模型 lock 与本地镜像 digest，生成 canonical `release_manifest.json` 和 64 位 release ID。
- `deploy/retrieval-models/deploy_release.py`：验证 release 后切换 live link，启动并健康检查新服务；失败时重新应用并验证旧 release，区分部署失败与回滚失败退出码。
- `deploy/retrieval-models/cleanup_release.py`：只按严格 64 位 release ID 删除非 live 的直接子目录。
- `docs/stages/stage_b_hierarchical_retrieval_v1.md`：中文交付与运维说明。

### 修改文件

- `src/bgpkb/cleaning_v2/derivation.py`：调用 section hierarchy 并为 v2 chunk 写入层级字段。
- `src/bgpkb/pipeline/build_cleaning_v2_migration.py`：汇总并原子写入 `section_catalog.jsonl`。
- `src/bgpkb/pipeline/build_published_knowledge_base.py`：隔离 unresolved chunk，并发布层级元数据。
- `src/bgpkb/pipeline/build_sqlite_knowledge_base.py`：扩展 chunks 表层级列并保持 FTS5。
- `src/bgpkb/pipeline/build_bge_m3_index.py`：使用本地优先 embedding provider chain，并记录模型 manifest。
- `src/bgpkb/service/hybrid_retrieval.py`：编排 Retriever、Reranker、QueryTypeResolver 和 ContextAssembler。
- `src/bgpkb/service/bge_m3_remote_client.py`：保留 SiliconFlow/阿里云 API provider，供 provider chain 降级。
- `src/bgpkb/service/llm_client.py`：增加版本化 query type 分类与 global 摘要方法。
- `src/bgpkb/service/repository.py`、`app.py`、`rag_answer.py`：暴露 top_n/query_type/token budget 并兼容既有调用。
- `src/bgpkb/pipeline/query_hybrid_rag.py`：新增 CLI 参数与错误码。
- `src/bgpkb/pipeline/run_rag_answer_eval.py`：记录 `is_critical` 和可比较的通过率。
- `src/bgpkb/pipeline/run_pipeline.py`：登记 section catalog 与 chunking 评测步骤。
- `src/bgpkb/pipeline/quality_check.py`：加载新 schema 和层级发布门禁。
- `metadata/config/rag_retrieval.yaml`：阶段 B 策略、provider、预算与提示词版本。
- `metadata/config/report_policy.yaml`：登记 chunking 报告。
- `metadata/config/stage_acceptance_gates.yaml`：登记阶段 B 验收。
- `metadata/schemas/chunk.schema.json`、`retrieval_result.schema.json`、`context_pack.schema.json`：扩展 v2 契约。
- `data/derived/datasets/rag_answer_eval_questions.jsonl`：增加显式 `is_critical` 字段，未指定样本为 `false`。
- `docs/roadmap/industry_alignment_improvement_plan_v1.md`：验收完成后更新阶段 B 状态。

## 2. 实施任务

### 任务 1：配置与 schema 契约

**文件：**

- 新建：`metadata/schemas/section_catalog.schema.json`
- 新建：`metadata/schemas/context_unit.schema.json`
- 修改：`metadata/schemas/chunk.schema.json`
- 修改：`metadata/schemas/retrieval_result.schema.json`
- 修改：`metadata/schemas/context_pack.schema.json`
- 修改：`metadata/config/rag_retrieval.yaml`
- 新建：`tests/test_stage_b_retrieval_contracts.py`

- [ ] **步骤 1：写失败的配置与 schema 测试**

测试至少表达以下期望：

```python
def test_stage_b_config_pins_retrieval_and_budget_contracts():
    cfg = load_yaml("metadata/config/rag_retrieval.yaml")
    assert cfg["version"] == "rag_retrieval_v2"
    assert cfg["hybrid_retrieval"]["lexical_top_k"] == 50
    assert cfg["hybrid_retrieval"]["vector_top_k"] == 50
    assert cfg["hybrid_retrieval"]["fused_top_k"] == 20
    assert cfg["hybrid_retrieval"]["rrf_k"] == 60
    assert cfg["reranker"]["top_n_default"] == 5
    assert cfg["reranker"]["top_n_min"] == 5
    assert cfg["reranker"]["top_n_max"] == 8
    assert cfg["context_pack"]["default_tokens"] == 6000
    assert cfg["context_pack"]["hard_max_tokens"] == 8000
    assert cfg["query_type"]["allowed_values"] == ["fact", "procedure", "policy", "global", "auto"]
```

同时用 `jsonschema` 验证 resolved v2 chunk、section catalog 和 context unit 的最小样例。

- [ ] **步骤 2：运行测试并确认正确失败**

运行：

```bash
python3 -m pytest tests/test_stage_b_retrieval_contracts.py -v
```

预期：因新 schema 缺失、配置仍为 `rag_retrieval_v1` 而失败。

- [ ] **步骤 3：写最小 schema 和配置**

配置必须明确：

```yaml
version: rag_retrieval_v2
hybrid_retrieval:
  lexical_top_k: 50
  vector_top_k: 50
  fused_top_k: 20
  rrf_k: 60
reranker:
  top_n_default: 5
  top_n_min: 5
  top_n_max: 8
  local_endpoint: http://10.99.8.28:8012/v1/rerank
embedding:
  local_endpoint: http://10.99.8.28:8011/v1/embeddings
query_type:
  allowed_values: [fact, procedure, policy, global, auto]
  default: auto
context_pack:
  default_tokens: 6000
  hard_max_tokens: 8000
```

不得在配置中写凭据；API key 只用环境变量名引用。

- [ ] **步骤 4：运行测试并确认通过**

```bash
python3 -m pytest tests/test_stage_b_retrieval_contracts.py tests/test_rag_framework_config.py -v
```

- [ ] **步骤 5：提交**

```bash
git add metadata/config/rag_retrieval.yaml metadata/schemas tests/test_stage_b_retrieval_contracts.py
git commit -m "feat: 定义阶段 B 层级检索契约"
```

### 任务 2：Section tree 与层级 chunk 派生

**文件：**

- 新建：`src/bgpkb/cleaning_v2/section_hierarchy.py`
- 修改：`src/bgpkb/cleaning_v2/derivation.py`
- 修改：`tests/test_cleaning_v2_derivation.py`
- 新建：`tests/test_section_hierarchy.py`

- [ ] **步骤 1：写稳定身份与 section 边界失败测试**

覆盖：文档根 section、嵌套 H2/H3、重复完整标题路径序号、正文修改只改变 `content_hash`、chunk 归属最近标题、`policy/global` 可遍历 section 子树。

期望 API：

```python
result = build_hierarchy(document, maximum_chunk_chars=1200)
assert result.sections[0]["section_id"].startswith("section_v2_")
assert result.sections[0]["child_section_ids"]
assert result.chunks[0]["hierarchy_status"] == "resolved"
```

- [ ] **步骤 2：运行测试并确认因模块缺失而失败**

```bash
python3 -m pytest tests/test_section_hierarchy.py -v
```

- [ ] **步骤 3：实现稳定 ID、内容哈希与 section tree**

关键纯函数签名：

```python
def build_section_id(doc_id: str, section_path: list[str], occurrence: int) -> str: ...
def build_content_hash(blocks: list[dict]) -> str: ...
def build_hierarchy(document: dict, maximum_chunk_chars: int = 1200) -> HierarchyResult: ...
```

普通片段使用直属 `child_chunk_ids`；section 子树通过 `child_section_ids` 遍历。

- [ ] **步骤 4：写特殊 Block 和邻接失败测试**

验证 paragraph/list/code/formula/table 纳入，picture 只保留引用，page_header/page_footer/unsupported 排除；表格/代码/公式不被内部截断；同一父 section 内 `previous_chunk_id/next_chunk_id` 互为反向链接。

- [ ] **步骤 5：运行失败测试**

```bash
python3 -m pytest tests/test_section_hierarchy.py -v
```

预期：特殊 Block 或邻接断言失败。

- [ ] **步骤 6：实现 Block 策略和 chunk 层级字段**

`hierarchy_status` 仅允许 `resolved/unresolved`；不可映射块生成 unresolved 记录供隔离报告，不伪造父 section。

- [ ] **步骤 7：让 derivation 使用统一 hierarchy 结果**

`build_derivatives()` 返回值新增 `sections`，既有 markdown/assets/chunk ID 稳定性测试同步更新。禁止在 `derivation.py` 再维护第二套标题栈。

- [ ] **步骤 8：运行相关测试**

```bash
python3 -m pytest tests/test_section_hierarchy.py tests/test_cleaning_v2_derivation.py tests/test_cleaning_v2_migration.py -v
```

- [ ] **步骤 9：提交**

```bash
git add src/bgpkb/cleaning_v2/section_hierarchy.py src/bgpkb/cleaning_v2/derivation.py tests/test_section_hierarchy.py tests/test_cleaning_v2_derivation.py
git commit -m "feat: 从 Canonical Block 派生层级 chunk"
```

### 任务 3：Section catalog、发布隔离与 SQLite 层级字段

**文件：**

- 修改：`src/bgpkb/pipeline/build_cleaning_v2_migration.py`
- 修改：`src/bgpkb/pipeline/build_published_knowledge_base.py`
- 修改：`src/bgpkb/pipeline/build_sqlite_knowledge_base.py`
- 修改：`src/bgpkb/pipeline/quality_check.py`
- 修改：`tests/test_cleaning_v2_migration.py`
- 修改：`tests/test_published_knowledge_base_release.py`
- 修改：`tests/test_sqlite_knowledge_base.py`
- 新建：`tests/test_stage_b_hierarchy_gate.py`

- [ ] **步骤 1：写迁移汇总失败测试**

调用 `build_migration()` 后断言 `section_catalog.jsonl` 原子生成、按 `(doc_id, section_order)` 稳定排序、`child_chunk_ids` 全部存在。

- [ ] **步骤 2：运行并确认缺少 catalog 输出**

```bash
python3 -m pytest tests/test_cleaning_v2_migration.py -v
```

- [ ] **步骤 3：汇总并原子写 section catalog**

给 `build_migration()` 增加 `section_catalog_path`，默认写入 `data/derived/datasets/section_catalog.jsonl`。重复派生结果必须字节稳定。

- [ ] **步骤 4：写发布隔离与 100% 发布不变量失败测试**

样例包含一个 resolved 和一个 unresolved chunk；断言发布 catalog 只包含 resolved，且断链/跨文档邻接导致构建失败而不是静默跳过。

- [ ] **步骤 5：运行失败测试**

```bash
python3 -m pytest tests/test_published_knowledge_base_release.py tests/test_stage_b_hierarchy_gate.py -v
```

- [ ] **步骤 6：扩展发布 catalog 与门禁**

`build_chunk_catalog()` 保留：

```text
parent_section_id, chunk_order, previous_chunk_id, next_chunk_id,
hierarchy_status, source_block_ids, section_path
```

v1 active release 走原分支，不要求这些字段；v2 active release 才启用层级门禁。

- [ ] **步骤 7：扩展 SQLite chunks 表**

增加上述层级列和必要 JSON 列，但继续由 `chunk_fts` 承载 BM25。为旧 v1 输入提供空默认值，不改变 v1 查询结果。

- [ ] **步骤 8：运行发布和 SQLite 测试**

```bash
python3 -m pytest tests/test_published_knowledge_base_release.py tests/test_sqlite_knowledge_base.py tests/test_stage_b_hierarchy_gate.py -v
```

- [ ] **步骤 9：提交**

```bash
git add src/bgpkb/pipeline/build_cleaning_v2_migration.py src/bgpkb/pipeline/build_published_knowledge_base.py src/bgpkb/pipeline/build_sqlite_knowledge_base.py src/bgpkb/pipeline/quality_check.py tests
git commit -m "feat: 发布 section catalog 并隔离断链 chunk"
```

### 任务 4：远端 Embedding/Reranker 服务与本地优先 client

**文件：**

- 新建：`deploy/retrieval-models/Dockerfile`
- 新建：`deploy/retrieval-models/Dockerfile.prepare`
- 新建：`deploy/retrieval-models/requirements.in`
- 新建：`deploy/retrieval-models/requirements.lock`
- 新建：`deploy/retrieval-models/service.py`
- 新建：`deploy/retrieval-models/compose.yaml`
- 新建：`deploy/retrieval-models/model_manifest.json`
- 新建：`deploy/retrieval-models/prepare_models.py`
- 生成：`deploy/retrieval-models/model_manifest.lock.json`
- 新建：`deploy/retrieval-models/verify_runtime.py`
- 新建：`deploy/retrieval-models/select_gpu_devices.py`
- 新建：`deploy/retrieval-models/gpu_policy.json`
- 新建：`deploy/retrieval-models/build_release_manifest.py`
- 新建：`deploy/retrieval-models/deploy_release.py`
- 新建：`deploy/retrieval-models/cleanup_release.py`
- 新建：`src/bgpkb/service/retrieval_model_client.py`
- 修改：`src/bgpkb/service/bge_m3_remote_client.py`
- 新建：`tests/test_retrieval_model_service.py`
- 新建：`tests/test_retrieval_model_client.py`
- 新建：`tests/test_gpu_device_selector.py`
- 新建：`tests/test_release_manifest.py`
- 新建：`tests/test_retrieval_model_deploy_release.py`
- 新建：`tests/test_cleanup_release.py`

- [ ] **步骤 1：写 HTTP 契约失败测试**

使用 fake model 验证：

```python
assert client.post("/v1/embeddings", json={"model": "BAAI/bge-m3", "input": ["BGP"]}).status_code == 200
assert client.post("/v1/rerank", json={"model": "BAAI/bge-reranker-v2-m3", "query": "BGP", "documents": ["x"], "top_n": 5}).status_code == 200
assert client.get("/health").json()["loaded"] is True
```

非法 `top_n`、空文档、模型角色错误必须返回 4xx。

- [ ] **步骤 2：运行并确认服务模块缺失**

```bash
python3 -m pytest tests/test_retrieval_model_service.py -v
```

- [ ] **步骤 3：实现可注入 fake model 的 FastAPI 服务**

生产路径按 `SERVICE_ROLE=embedding|reranker` 延迟加载 `BGEM3FlagModel` 或 `FlagReranker`。`/health` 返回角色、模型、revision、device、loaded，不返回路径或凭据。

- [ ] **步骤 4：写 provider chain 失败测试**

验证本地成功不调用 API、本地超时才调用 API、两者失败返回聚合错误、`require_model=true` 时不使用 mock、响应保留 provider/model/revision/latency/degraded_reason。

- [ ] **步骤 5：运行失败测试**

```bash
python3 -m pytest tests/test_retrieval_model_client.py -v
```

- [ ] **步骤 6：实现 client 与 provider chain**

核心接口：

```python
class EmbeddingProviderChain:
    def embed_texts(self, texts: list[str], require_model: bool = False) -> dict: ...

class RerankerProviderChain:
    def rerank(self, query: str, documents: list[str], top_n: int, require_model: bool = False) -> dict: ...
```

API reranker 通过 `RERANK_API_ENDPOINT/API_KEY/MODEL` 环境变量配置，不绑定特定厂商。

- [ ] **步骤 7：锁定模型 revision 并实现持久化准备脚本**

`model_manifest.json` 固定本计划编写时核验到的官方仓库 commit：

```json
{
  "models": [
    {"repo_id": "BAAI/bge-m3", "revision": "5617a9f61b028005a4858fdac845db406aefb181"},
    {"repo_id": "BAAI/bge-reranker-v2-m3", "revision": "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"}
  ]
}
```

`prepare_models.py --model-root <持久目录>` 必须使用 `snapshot_download(..., revision=<精确 commit>)`，禁止跟随 `main`；下载后对全部模型文件计算 SHA-256，原子生成 `model_manifest.lock.json`。若目标目录已有文件，只在 hash 与锁文件一致时复用。`Dockerfile.prepare` 提供锁定版本的 `huggingface_hub`，使准备步骤不依赖宿主机 Python 包。

- [ ] **步骤 8：写 Docker/Compose 与离线预检**

`gpu_policy.json` 使用以下锁定策略：

```json
{
  "allowed_indices": [2, 3],
  "embedding_min_free_mib": 8192,
  "reranker_min_free_mib": 8192
}
```

`select_gpu_devices.py --policy gpu_policy.json --output .env` 必须调用并解析：

```bash
nvidia-smi --query-gpu=index,memory.total,memory.used --format=csv,noheader,nounits
```

选择器按 `free = total - used` 计算空闲显存，只考虑 `allowed_indices`，并枚举全部有序且不同的 GPU 配对 `(embedding, reranker)`。每个角色必须分别满足自己的阈值；对合格配对依次按最大化最小角色 headroom、最大化总 headroom、embedding index 升序、reranker index 升序确定唯一选择。不得回退到 GPU 0 或 GPU 1。

成功时返回 `exit 0`，在目标文件同目录写临时文件并原子替换 `.env`，内容必须是精确四行且以换行结尾：

```dotenv
EMBEDDING_GPU_CDI=nvidia.com/gpu=<i>
RERANKER_GPU_CDI=nvidia.com/gpu=<i>
EMBEDDING_GPU_INDEX=<i>
RERANKER_GPU_INDEX=<i>
```

任何查询、解析、阈值或选择失败均返回 `exit 2`，向 stderr 输出中文或 JSON 诊断，至少包含各候选卡的 total、used、free、角色阈值和失败原因。失败路径删除选择器自身创建的临时文件，但旧 `.env` 字节不变。

`build_release_manifest.py` 对 app 部署文件逐文件记录规范化 relative path 与 SHA-256，再计算 `app_tree_sha256`；生成树哈希时排除输出文件、`.env` 和单独计入的 model lock，避免自引用。同时记录 `model_manifest.lock.json` 的 `model_lock_sha256` 和本地构建镜像的不可变 `image_digest`。脚本按稳定键序、UTF-8、无多余空白生成 canonical release_manifest.json；文件只包含可哈希事实，不写入自引用的 release ID。定义 `RELEASE_ID = sha256(canonical manifest)`，结果必须是 64 位小写十六进制。RELEASE_ID 必须覆盖 app 内容、model lock 和 image digest；app 内容、model lock 或 image digest 任一变化 ID 都必须变化。测试使用固定目录和 digest 验证确定性、逐项变化和路径排序。

检索镜像不得复用固定 `stage-b-v1` tag。构建临时镜像并取得不可变 image ID/digest 后生成 release manifest，再打不可变 tag `bgpkb-retrieval-models:<RELEASE_ID>`；旧 tag 必须保留用于回滚。Compose 固定两个独立服务：8011 embeddings、8012 rerank，均 `restart: unless-stopped`、只映射内网、只读挂载 `/srv/bgpkb/retrieval-models-models`，并使用 `pull_policy: never`。Compose 使用 `EMBEDDING_GPU_CDI` 与 `RERANKER_GPU_CDI` 两个 CDI 设备变量并验证两者不同；`deploy_release.py` 从每个 release 自己的 `.env` 与 manifest 导出 `RETRIEVAL_IMAGE=bgpkb-retrieval-models:<RELEASE_ID>`，禁止覆盖不可变 tag。GPU `.env` 必须加入 `.gitignore`，不得入库。

`deploy_release.py` 使用可注入的 command runner 与 health checker。切换前记录旧 app/model link 目标、旧 release manifest 和旧 image；manifest/hash/GPU prestart 失败前不得触碰 live link。验证通过后先在同目录创建临时 symlink，再以 `os.replace` 更新 `/srv/bgpkb/retrieval-models` 与 `/srv/bgpkb/retrieval-models-models`，然后在固定的 `COMPOSE_PROJECT_NAME=bgpkb-retrieval-models` project 中运行新 release 的 `docker compose up -d --pull never`，并检查 8011、8012 health。

若新 release 的 Compose up 或任一 health 失败，脚本必须停止或替换同一 project 的部分新容器，恢复两个旧 link，执行旧 release Compose 的 `docker compose up -d --pull never --force-recreate`，并再次验证两个旧 health。新 release 失败且旧 release 恢复健康时返回 `exit 3`；旧 link、旧 release Compose 或旧 health 任一恢复失败时返回更严重的 `exit 4` 并输出诊断。首次部署没有旧 release 时，新启动失败必须停止部分容器、移除本次 live link、返回非零，不能留下容器或 link。

`cleanup_release.py` 只接受 `--release-id`，且必须匹配 `^[0-9a-f]{64}$`。目标 resolve 后必须恰好是 `/srv/bgpkb/retrieval-releases/<id>` 的直接子目录；空值、短 ID、路径逃逸均非零退出。脚本解析两个 live symlink；若 app link 目标等于候选的 `app` 子目录、model link 目标等于候选的 `models` 子目录，或候选是任一 live 目标的父目录，必须拒绝删除。只有显式命令才允许删除，所有验证都必须在删除前完成。

`verify_runtime.py` 只使用 Python 标准库与 `nvidia-smi`，必须在启动前逐文件校验 lock manifest、GPU 选择和模型目录，启动后再校验健康端点。

- [ ] **步骤 9：写 GPU 选择与 release 部署失败测试**

`tests/test_gpu_device_selector.py` 使用固定 `nvidia-smi` 文本覆盖配对排序、阈值、不同 GPU、失败不覆盖旧 `.env`、成功精确四行输出，并包含“不同阈值下贪心会失败但交换角色可成功”的样例：GPU 2 free=9000、GPU 3 free=7000、Embedding 阈值=6000、Reranker 阈值=8000 时必须选择 `(embedding=3, reranker=2)`；同时断言 GPU 0/1 即使空闲也不会入选。`tests/test_release_manifest.py` 覆盖 app、model lock、image digest 任一变化都会改变 ID。`tests/test_retrieval_model_deploy_release.py` 用注入的 command runner 和 health checker 覆盖切换前失败、新服务成功、运行态失败后确实重启旧 release Compose 并验证旧 health、回滚失败 `exit 4`、首次部署失败无残留。`tests/test_cleanup_release.py` 覆盖合法非 live release 删除，以及空值、短 ID、路径逃逸、app/model live 目标全部非零且不删除。

- [ ] **步骤 10：运行本地契约测试**

```bash
python3 -m pytest tests/test_retrieval_model_service.py tests/test_retrieval_model_client.py tests/test_bge_m3_remote_client.py tests/test_gpu_device_selector.py tests/test_release_manifest.py tests/test_retrieval_model_deploy_release.py tests/test_cleanup_release.py -v
```

- [ ] **步骤 11：提交**

```bash
git add deploy/retrieval-models src/bgpkb/service/retrieval_model_client.py src/bgpkb/service/bge_m3_remote_client.py tests/test_retrieval_model_service.py tests/test_retrieval_model_client.py tests/test_gpu_device_selector.py tests/test_release_manifest.py tests/test_retrieval_model_deploy_release.py tests/test_cleanup_release.py
git commit -m "feat: 增加本地优先检索模型服务"
```

### 任务 5：SQLite BM25、BGE-M3 dense 与 RRF Retriever

**文件：**

- 新建：`src/bgpkb/service/retrievers.py`
- 修改：`src/bgpkb/service/hybrid_retrieval.py`
- 修改：`src/bgpkb/pipeline/build_bge_m3_index.py`
- 新建：`tests/test_retrievers.py`
- 修改：`tests/test_hybrid_retrieval.py`
- 修改：`tests/test_build_bge_m3_index.py`

- [x] **步骤 1：写 BM25 与 dense adapter 失败测试**

测试 `Bm25Retriever.search(query, top_k=50)` 真正执行 SQLite `bm25(chunk_fts)`，将 SQLite 越小越好的分数转换为稳定的“越大越好”展示分数，同时保留 `raw_score/raw_rank`。Dense 使用 cosine 并保留相似度。

- [x] **步骤 2：运行并确认模块缺失**

```bash
python3 -m pytest tests/test_retrievers.py -v
```

- [x] **步骤 3：实现 Retriever 协议和两个 adapter**

```python
class Retriever(Protocol):
    def search(self, query: str, top_k: int) -> RetrievalChannelResult: ...
```

BM25 查询失败和 dense provider/index 失败必须返回结构化 channel error，不能伪装成零结果。

- [x] **步骤 4：写 RRF 与通道故障失败测试**

断言每路输入最多 50、`rrf_k=60`、按 `chunk_id` 去重、输出固定最多 20；单路失败继续且 `degraded=true`，双路失败抛 `RetrievalUnavailable`。

- [x] **步骤 5：运行失败测试**

```bash
python3 -m pytest tests/test_retrievers.py tests/test_hybrid_retrieval.py -v
```

- [x] **步骤 6：实现 RRF 编排并替换旧词法打分路径**

保留旧 `retrieval_framework.search()` 供 v1；v2 `hybrid_retrieval.search()` 使用新 adapter。候选必须携带 lexical/vector 原分、原排名、RRF 分和 match channels。

- [x] **步骤 7：让索引构建使用本地优先 EmbeddingProviderChain**

manifest 新增模型 revision、hash、provider chain 和降级原因。离线缺模型时保留既有制品，不用空索引覆盖。

- [x] **步骤 8：运行测试**

```bash
python3 -m pytest tests/test_retrievers.py tests/test_hybrid_retrieval.py tests/test_build_bge_m3_index.py -v
```

- [x] **步骤 9：提交**

```bash
git add src/bgpkb/service/retrievers.py src/bgpkb/service/hybrid_retrieval.py src/bgpkb/pipeline/build_bge_m3_index.py tests
git commit -m "feat: 使用 BM25 和 BGE-M3 执行混合召回"
```

### 任务 6：Reranker 与 Query Type Resolver

**文件：**

- 新建：`src/bgpkb/service/query_type_resolver.py`
- 修改：`src/bgpkb/service/llm_client.py`
- 修改：`src/bgpkb/service/hybrid_retrieval.py`
- 新建：`tests/test_query_type_resolver.py`
- 新建：`tests/test_reranking_pipeline.py`
- 修改：`tests/test_llm_client.py`

- [x] **步骤 1：写 top_n 验证和 rerank 失败测试**

断言默认 5，合法范围 5–8，4/9/字符串直接报错；传给 reranker 的候选最多 20；返回顺序按 relevance score 降序，稳定 tie-break 使用原 RRF rank。

- [x] **步骤 2：运行并确认失败**

```bash
python3 -m pytest tests/test_reranking_pipeline.py -v
```

- [x] **步骤 3：接入 RerankerProviderChain**

无模型时按配置调用 API；若两者失败且 `require_model=false`，使用 RRF 顺序作为显式降级，不伪造 rerank 分；`require_model=true` 直接报错。

- [x] **步骤 4：写 query type 失败测试**

请求值只接受五值枚举；显式类型不调用 DeepSeek。`auto` 的解析结果只允许 `fact/procedure/policy/global` 四值，DeepSeek 返回 `auto` 必须视为非法响应并走规则回退。DeepSeek JSON 非法/超时同样走可审计规则；规则最后兜底 `fact`。响应记录 requested/resolved type、理由、prompt version 和降级原因。

- [x] **步骤 5：运行失败测试**

```bash
python3 -m pytest tests/test_query_type_resolver.py tests/test_llm_client.py -v
```

- [x] **步骤 6：实现 DeepSeek 结构化分类方法和规则回退**

为 `llm_client.DeepSeekClient` 增加：

```python
def classify_query_type(self, query: str, prompt_version: str) -> dict: ...
def summarize_context(self, query: str, context: str, max_tokens: int, prompt_version: str) -> dict: ...
```

两者使用独立版本化提示词，温度为 0；摘要不得新增引用，只返回文本。

- [x] **步骤 7：运行测试**

```bash
python3 -m pytest tests/test_reranking_pipeline.py tests/test_query_type_resolver.py tests/test_llm_client.py -v
```

- [x] **步骤 8：提交**

```bash
git add src/bgpkb/service/query_type_resolver.py src/bgpkb/service/llm_client.py src/bgpkb/service/hybrid_retrieval.py tests
git commit -m "feat: 增加模型精排与查询类型解析"
```

### 任务 7：Token 预算与完整内容读取

**文件：**

- 新建：`src/bgpkb/service/token_budget.py`
- 新建：`src/bgpkb/service/chunk_store.py`
- 新建：`tests/test_token_budget.py`
- 新建：`tests/test_chunk_store.py`

- [x] **步骤 1：写预算公式失败测试**

默认 6000、硬上限 8000。测试必须覆盖动态公式，而不只检查默认常数：

```python
assert parent_budget("normal", 3000).per_parent == 900
assert parent_budget("normal", 6000).per_parent == 1200
assert parent_budget("policy", 4000).per_parent == 2000
assert parent_budget("policy", 8000).per_parent == 3000
assert parent_budget("policy", 8000).max_full_parent_sections == 1
assert parent_budget("global", 4000).per_parent == 1400
assert parent_budget("global", 8000).per_parent == 2000
assert parent_budget("global", 6000).max_total_full_tokens == 3600
assert parent_budget("global", 6000).max_full_parent_sections == 2
```

预算超过 8000 或非正数直接报错。

- [x] **步骤 2：运行并确认模块缺失**

```bash
python3 -m pytest tests/test_token_budget.py -v
```

- [x] **步骤 3：实现 TokenCounter 与 ParentBudget**

```python
class TokenCounter:
    def count(self, text: str) -> TokenCount: ...

def parent_budget(query_type: str, context_budget: int) -> dict: ...
```

注入真实 tokenizer 时使用真实值；不可用时使用保守字符估算并标记 `estimated=true`。

- [x] **步骤 4：写 chunk/section store 失败测试**

验证按 `chunk_file` 懒加载完整 content、缓存文件、拒绝路径逃逸、按 section tree 取得直属 chunk 或整个子树、找不到 chunk 时结构化报错。

- [x] **步骤 5：运行失败测试并实现 store**

```bash
python3 -m pytest tests/test_chunk_store.py -v
```

- [x] **步骤 6：运行两组测试**

```bash
python3 -m pytest tests/test_token_budget.py tests/test_chunk_store.py -v
```

- [x] **步骤 7：提交**

```bash
git add src/bgpkb/service/token_budget.py src/bgpkb/service/chunk_store.py tests/test_token_budget.py tests/test_chunk_store.py
git commit -m "feat: 增加层级上下文 token 预算与内容存储"
```

### 任务 8：Context Assembler

**文件：**

- 新建：`src/bgpkb/service/context_assembler.py`
- 新建：`tests/test_context_assembler.py`
- 修改：`metadata/schemas/context_unit.schema.json`

- [ ] **步骤 1：写 fact/procedure/policy 行为失败测试**

覆盖：fact 前后各 1 且不提升；procedure 前后各 2、同父两个命中后提升、只填 1 个 gap；policy 连续区间在预算内取连续片段、小 section 子树可全文。

- [ ] **步骤 2：运行并确认模块缺失**

```bash
python3 -m pytest tests/test_context_assembler.py -v
```

- [ ] **步骤 3：实现窗口、提升、排序与去重**

先按 chunk_id 去重，再按相同 `source_block_ids` 集合去重；section 组按最高 rerank 分降序、组内按 chunk order。

- [ ] **步骤 4：写 global 决策树失败测试**

覆盖：同父至少 2 命中且子树在专用预算内才全文；否则片段；合计超预算才调用 DeepSeek 摘要；摘要最多 400 tokens；API 失败裁高分原文；最多 2 个全文。global 候选选择必须先为每个 `doc_id` 选最高 rerank 分 section，再按分数补充同 doc 的其他 section；测试用交错分数 fixture 证明这一顺序。

- [ ] **步骤 5：运行失败测试并实现 global 策略**

```bash
python3 -m pytest tests/test_context_assembler.py -v
```

- [ ] **步骤 6：写裁剪顺序与不可截断 Block 失败测试**

用 `trim_events` 断言顺序：去重→裁相邻→全文降级→低分命中→内部裁剪。table/code/formula 只能整体保留或整体移除。

- [ ] **步骤 7：实现引用不变量**

每个 context unit 输出：

```text
context_id, mode, parent_section_id, included_chunk_ids,
doc_id, section_path, parent_section_heading,
included_block_ids, content, estimated_tokens, actual_tokens,
max_rerank_score, trim_events, citations
```

缺少精确 `(chunk_id, source_ref)` 的 unit 不得返回。

- [ ] **步骤 8：运行测试**

```bash
python3 -m pytest tests/test_context_assembler.py tests/test_token_budget.py tests/test_chunk_store.py -v
```

- [ ] **步骤 9：提交**

```bash
git add src/bgpkb/service/context_assembler.py metadata/schemas/context_unit.schema.json tests/test_context_assembler.py
git commit -m "feat: 按查询类型组装层级上下文"
```

### 任务 9：服务 API、评测和流水线门禁

**文件：**

- 修改：`src/bgpkb/service/hybrid_retrieval.py`
- 修改：`src/bgpkb/service/repository.py`
- 修改：`src/bgpkb/service/app.py`
- 修改：`src/bgpkb/service/rag_answer.py`
- 修改：`src/bgpkb/pipeline/query_hybrid_rag.py`
- 新建：`src/bgpkb/pipeline/evaluate_chunking.py`
- 修改：`src/bgpkb/pipeline/run_rag_answer_eval.py`
- 修改：`src/bgpkb/pipeline/run_pipeline.py`
- 修改：`src/bgpkb/pipeline/quality_check.py`
- 修改：`metadata/config/report_policy.yaml`
- 修改：`metadata/config/stage_acceptance_gates.yaml`
- 修改：`data/derived/datasets/rag_answer_eval_questions.jsonl`
- 新建：`tests/test_chunking_evaluation.py`
- 修改：`tests/test_service_api.py`
- 修改：`tests/test_rag_answer.py`
- 修改：`tests/test_stage_acceptance.py`

- [ ] **步骤 1：写 API 失败测试**

`/api/v1/hybrid/context-pack` 接受 `top_n=5..8`、`query_type`、`token_budget<=8000`、`require_model`。非法 top_n/query type/budget 返回 422。旧 `limit` 仅作为兼容别名映射到合法 top_n，并在响应标记 deprecated；v1 retrieval endpoint 不变。

- [ ] **步骤 2：运行并确认参数尚未实现**

```bash
python3 -m pytest tests/test_service_api.py tests/test_rag_answer.py -v
```

- [ ] **步骤 3：接通完整在线数据流**

`hybrid_retrieval.context_pack()` 执行：召回20→rerank 5–8→resolve query type→assemble。RAG answer 只把 context unit content 传给 DeepSeek，引用仍由 assembler 生成。

- [ ] **步骤 4：写评测指标失败测试**

构造 fixture 精确验证：resolved 覆盖率、发布父级追溯率、父 section 覆盖率、前后链接正确率、included chunk 引用完整率、来源覆盖率、总体 pass rate、`is_critical=true` 子集 pass rate和百分点退化。逐题结果必须断言 `candidate_chunk_count` 为融合后候选数、`reranked_chunk_count` 为精排后命中数。

- [ ] **步骤 5：运行并确认评测模块缺失**

```bash
python3 -m pytest tests/test_chunking_evaluation.py -v
```

- [ ] **步骤 6：实现 `evaluate_chunking.py`**

输出：

- `data/derived/datasets/chunking_eval_results.jsonl`
- `data/generated/reports/rag/chunking_evaluation_report.md`

每题记录候选 chunk 数、rerank 后 chunk 数、命中父 section 数、预期来源覆盖和引用状态；汇总报告包含父 section 覆盖率。无成熟基线时写 baseline，不执行答案退化阻断；有兼容 prompt/model 版本的基线时执行 3/5 个百分点门禁。

- [ ] **步骤 7：登记报告、阶段验收和流水线**

`run_pipeline.py` 在 v2 迁移后构建 section catalog，在发布和检索索引后运行 chunking 评测。`quality_check.py` 对发布记录执行 100% 父级/邻接/引用不变量，对全量生成数据执行 99% resolved KPI。

- [ ] **步骤 8：写完整 fake-provider 链路集成测试**

新建 `tests/test_stage_b_retrieval_integration.py`，使用临时 SQLite FTS5、内存 dense 索引、fake embedding、fake reranker、fake query type 和临时 section/chunk 文件，一次调用断言：

```text
BM25+dense → RRF(top 20) → rerank(top_n) → resolve query type
→ section/window 扩展 → token budget → context units + exact citations
```

测试同时覆盖单一模型 provider 降级标记，禁止 patch 掉任一核心编排阶段。

- [ ] **步骤 9：运行服务、集成与评测测试**

```bash
python3 -m pytest tests/test_service_api.py tests/test_rag_answer.py tests/test_stage_b_retrieval_integration.py tests/test_chunking_evaluation.py tests/test_stage_acceptance.py -v
```

- [ ] **步骤 10：提交**

```bash
git add src/bgpkb/service src/bgpkb/pipeline metadata/config data/derived/datasets/rag_answer_eval_questions.jsonl tests
git commit -m "feat: 接通阶段 B 服务与质量门禁"
```

### 任务 10：生成全量产物、部署真实模型并完成验收

**文件：**

- 新建：`docs/stages/stage_b_hierarchical_retrieval_v1.md`
- 修改：`docs/roadmap/industry_alignment_improvement_plan_v1.md`
- 生成：`data/derived/datasets/section_catalog.jsonl`
- 生成：`data/derived/datasets/chunking_eval_results.jsonl`
- 生成：`data/generated/reports/rag/chunking_evaluation_report.md`
- 更新：`data/corpus/chunks_v2/*.jsonl`
- 更新：相关 `data/published/`、SQLite、manifest 和中文报告

- [ ] **步骤 0：检查本机与远端部署前提**

```bash
docker info
docker buildx inspect
df -h "$HOME"
ssh root@10.99.8.28 \
  'docker info >/dev/null && nvidia-smi && df -h /srv/bgpkb'
```

若本机 Docker daemon 未运行，先启动 Docker Desktop；若本机 cache 或远端 `/srv/bgpkb` 空间不足，停止部署并清理非项目缓存，不把模型转移到 `/tmp`。远端检查只收集实时状态，不得据此永久声明 GPU 2、GPU 3 处于空闲状态。

- [ ] **步骤 1：先运行阶段 B 定向测试**

```bash
python3 -m pytest \
  tests/test_stage_b_retrieval_contracts.py \
  tests/test_section_hierarchy.py \
  tests/test_stage_b_hierarchy_gate.py \
  tests/test_retrieval_model_service.py \
  tests/test_retrieval_model_client.py \
  tests/test_gpu_device_selector.py \
  tests/test_release_manifest.py \
  tests/test_retrieval_model_deploy_release.py \
  tests/test_cleanup_release.py \
  tests/test_retrievers.py \
  tests/test_reranking_pipeline.py \
  tests/test_query_type_resolver.py \
  tests/test_token_budget.py \
  tests/test_chunk_store.py \
  tests/test_context_assembler.py \
  tests/test_chunking_evaluation.py \
  tests/test_stage_b_retrieval_integration.py -v
```

预期：全部通过。

- [ ] **步骤 2：重新派生 v2 chunks 与 section catalog**

```bash
python3 -m bgpkb.pipeline.build_cleaning_v2_migration
```

检查：54 篇输入全部终态；`resolved` 覆盖率≥99%；可发布 chunk 的父级和邻接关系 100%。

- [ ] **步骤 3：重建发布包、SQLite 与离线索引**

```bash
python3 -m bgpkb.pipeline.build_published_knowledge_base
python3 -m bgpkb.pipeline.build_sqlite_knowledge_base
python3 -m bgpkb.pipeline.build_rag_indexes
```

- [ ] **步骤 4：部署两个独立 GPU 容器**

```bash
set -euo pipefail

MODEL_STAGE_DIR="$HOME/.cache/bgpkb/model-stage"
mkdir -p "$MODEL_STAGE_DIR"
docker build -f deploy/retrieval-models/Dockerfile.prepare \
  -t bgpkb-model-preparer:stage-b-v1 deploy/retrieval-models
docker run --rm \
  -v "$PWD/deploy/retrieval-models:/app" \
  -v "$MODEL_STAGE_DIR:/models" \
  bgpkb-model-preparer:stage-b-v1 \
  python /app/prepare_models.py \
    --manifest /app/model_manifest.json \
    --model-root /models \
    --lock-output /app/model_manifest.lock.json
TEMP_IMAGE="bgpkb-retrieval-models:build-$(date +%s)-$$"
docker buildx build --platform linux/amd64 \
  -t "$TEMP_IMAGE" \
  --load -f deploy/retrieval-models/Dockerfile deploy/retrieval-models
IMAGE_ID="$(docker image inspect --format '{{.Id}}' "$TEMP_IMAGE")"
RELEASE_METADATA_DIR="$HOME/.cache/bgpkb/release-metadata"
RELEASE_MANIFEST="$RELEASE_METADATA_DIR/release_manifest.json"
mkdir -p "$RELEASE_METADATA_DIR"
python3 deploy/retrieval-models/build_release_manifest.py \
  --app-root deploy/retrieval-models \
  --model-lock deploy/retrieval-models/model_manifest.lock.json \
  --image-digest "$IMAGE_ID" \
  --output "$RELEASE_MANIFEST"
RELEASE_ID="$(shasum -a 256 "$RELEASE_MANIFEST" | awk '{print $1}')"
[[ "$RELEASE_ID" =~ ^[0-9a-f]{64}$ ]]
RELEASE_IMAGE="bgpkb-retrieval-models:$RELEASE_ID"
docker tag "$TEMP_IMAGE" "$RELEASE_IMAGE"
REMOTE_STAGE="/srv/bgpkb/retrieval-releases/.incoming-$RELEASE_ID"
REMOTE_RELEASE="/srv/bgpkb/retrieval-releases/$RELEASE_ID"
docker save "$RELEASE_IMAGE" | gzip | \
  ssh root@10.99.8.28 'gunzip | docker load'
ssh root@10.99.8.28 "set -euo pipefail; \
  mkdir -p /srv/bgpkb/retrieval-releases; \
  test ! -e '$REMOTE_STAGE'; \
  test ! -e '$REMOTE_RELEASE'; \
  mkdir -p '$REMOTE_STAGE/app' '$REMOTE_STAGE/models'"
rsync -az -e ssh deploy/retrieval-models/ \
  "root@10.99.8.28:$REMOTE_STAGE/app/"
rsync -az -e ssh "$RELEASE_MANIFEST" \
  "root@10.99.8.28:$REMOTE_STAGE/app/release_manifest.json"
rsync -az -e ssh "$MODEL_STAGE_DIR/" \
  "root@10.99.8.28:$REMOTE_STAGE/models/"
ssh root@10.99.8.28 "set -euo pipefail; \
  cd '$REMOTE_STAGE/app'; \
  nvidia-smi; \
  python3 select_gpu_devices.py --policy gpu_policy.json --output .env; \
  mv '$REMOTE_STAGE' '$REMOTE_RELEASE'; \
  cd '$REMOTE_RELEASE/app'; \
  python3 deploy_release.py \
    --release-root '$REMOTE_RELEASE' \
    --app-link /srv/bgpkb/retrieval-models \
    --models-link /srv/bgpkb/retrieval-models-models \
    --prestart-command 'python3 verify_runtime.py --phase prestart --model-root $REMOTE_RELEASE/models' \
    --compose-command 'COMPOSE_PROJECT_NAME=bgpkb-retrieval-models docker compose up -d --pull never' \
    --rollback-compose-command 'COMPOSE_PROJECT_NAME=bgpkb-retrieval-models docker compose up -d --pull never --force-recreate' \
    --health-url http://127.0.0.1:8011/health \
    --health-url http://127.0.0.1:8012/health"
```

服务器已知不能访问 Hugging Face，因此模型必须在本机可联网准备容器中按精确 commit 下载并生成真实逐文件 SHA-256 lock，再同步到服务器。服务镜像也在本机交叉构建为 `linux/amd64` 并通过 `docker load` 导入；服务器启动过程不得联网拉取镜像或模型。`RELEASE_ID` 是 app tree、model lock 和不可变 image digest 的 canonical manifest SHA-256；命令顺序固定为构建临时镜像、获取 image ID、生成 release manifest/ID、打 release tag、`docker save` 该 tag、同步 release。代码和模型先同步到唯一且为空的临时目录，再 rename 为 `/srv/bgpkb/retrieval-releases/$RELEASE_ID/{app,models}`。正式路径 `/srv/bgpkb/retrieval-models` 与 `/srv/bgpkb/retrieval-models-models` 只作为 live symlink，不直接接收 rsync，也不得回退到 `/tmp`。

部署命令必须先执行 `nvidia-smi`，再执行精确命令 `select_gpu_devices.py --policy gpu_policy.json --output .env`。`deploy_release.py` 从 manifest 校验并导出 `RETRIEVAL_IMAGE=bgpkb-retrieval-models:<RELEASE_ID>`，在 release 目录内完成 manifest/hash/GPU prestart 验证后才切换两个 live symlink，并在固定 Compose project 中以 `docker compose up -d --pull never` 启动和验证两个 health；任何预检失败不得触碰 live link。新运行态失败按任务 4 契约恢复旧 link、重新运行旧 Compose 并验证旧 health。候选池不足两张时停止 Compose 并走 API 降级；不得自动使用 GPU 0 或 GPU 1，也不得硬编码 GPU 2、GPU 3 处于空闲状态。

旧 release 清理不得成为部署路径的一部分，也不得顺带删除任何正式目录。确认某个 release 已不被 live link 引用后，只能在独立维护窗口调用安全清理器：

```bash
OLD_RELEASE_ID="填写已人工确认的旧版本哈希"
ssh root@10.99.8.28 \
  "cd /srv/bgpkb/retrieval-models && python3 cleanup_release.py --release-id '$OLD_RELEASE_ID'"
```

- [ ] **步骤 5：验证模型 revision、hash、GPU 与健康端点**

```bash
ssh root@10.99.8.28 \
  'cd /srv/bgpkb/retrieval-models && \
   python3 verify_runtime.py --phase running --model-root /srv/bgpkb/retrieval-models-models'
curl --fail http://10.99.8.28:8011/health
curl --fail http://10.99.8.28:8012/health
```

本机生成的 lock manifest 必须提交到仓库；后续部署在同步前后都按它校验文件，任何缺失或 hash 漂移都阻断启动。模型二进制只保存在本机 cache 与服务器持久目录，不进入 Git。

- [ ] **步骤 6：用真实 BGE-M3 重建 dense 索引并做 reranker 冒烟**

```bash
python3 -m bgpkb.pipeline.build_bge_m3_index --provider local_bge_m3
python3 -m bgpkb.pipeline.query_hybrid_rag context-pack "什么是 BGP 路由泄露？" \
  --top-n 5 --query-type fact --token-budget 6000
```

验证响应显示本地 embedding/reranker provider；不得出现凭据或本机绝对路径。

- [ ] **步骤 7：运行 chunking 评测与阶段验收**

```bash
python3 -m bgpkb.pipeline.evaluate_chunking
python3 -m bgpkb.pipeline.run_stage_acceptance --stage stage_b_hierarchical_retrieval_v1
```

硬门禁：生成 resolved≥99%；发布父级/邻接/引用=100%；历史/降级 KPI 引用≥95%、邻接≥98%；成熟答案基线时总体/关键退化≤3/5 个百分点。

- [ ] **步骤 8：运行完整测试和确定性流水线**

```bash
python3 -m pytest -q
python3 -m bgpkb.pipeline.run_pipeline
git diff --check
```

不执行完整 v2→v1→v2 回滚演练。

- [ ] **步骤 9：更新中文交付文档与路线图**

文档记录模型服务端口、健康检查、降级路径、指标实测值、已知限制和运维命令；路线图仅在所有门禁通过后将阶段 B 标为已交付。

- [ ] **步骤 10：提交生成物与交付文档**

```bash
git add src tests metadata deploy data docs
git status --short
git commit -m "feat: 交付阶段 B 层级检索"
```

提交前核对暂存区，排除 `uv.lock`、`src/bgpkb.egg-info/`、凭据、模型二进制、缓存和服务器日志。

## 3. 最终验收清单

- [ ] v2 chunk 均有 `hierarchy_status`；生成 resolved 覆盖率≥99%。
- [ ] 可检索发布 chunk 的父 section 和前后邻接正确率均为 100%。
- [ ] `section_catalog.jsonl` 由 Canonical Block v2 确定性生成且 schema 通过。
- [ ] SQLite FTS5 BM25 与 BGE-M3 dense 各取前 50，RRF(k=60) 输出前 20。
- [ ] reranker 默认本地 `BAAI/bge-reranker-v2-m3`，top_n 仅允许 5–8。
- [ ] `query_type` 仅允许五值；auto 的 DeepSeek 失败可审计降级到规则/fact。
- [ ] context pack 默认 6000、硬上限 8000，预算公式和裁剪顺序有测试证据。
- [ ] 正式 context unit 的 included chunk 引用完整率为 100%。
- [ ] 8011/8012 两个独立容器常驻、健康、使用持久模型目录并锁定 hash。
- [ ] 离线 CI 不依赖 GPU、DeepSeek 或外部 API。
- [ ] 阶段 B 报告和阶段验收通过。
- [ ] 全量 pytest 与确定性流水线通过。
- [ ] 未执行繁琐的完整回滚演练，v1/v2 隔离由自动化测试覆盖。
