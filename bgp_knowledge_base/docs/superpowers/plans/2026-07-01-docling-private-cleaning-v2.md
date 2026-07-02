# Docling 私有化成熟知识清洗 v2 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在独立 Linux GPU 服务器上建立离线、结构保真、可审计、可恢复的 Docling 批处理清洗平台，并把现有 54 篇语料安全迁移到以 cleaned Block v2 为权威数据的新链路。

**Architecture:** Docling 容器负责私有化版面解析和自适应 OCR，项目适配层把其输出转换为稳定 Canonical Block v2。分级清洗、transformation 审计和文档级状态机生成并行 v2 产物；全部差异、人工指标和硬门禁通过后，版本化发布指针原子切换到 v2，同时保留 v1 回滚。

**Tech Stack:** Python 3、Docling、CUDA/Linux GPU、Docker、PyYAML、JSON/JSONL、pytest、现有 BGP KB 阶段验收与制品治理。

---

## 文件职责总览

**部署与配置**

- `deploy/docling/Dockerfile`：生产 GPU 镜像，构建期下载模型，运行期离线。
- `deploy/docling/requirements.lock`：Docling 运行依赖精确锁。
- `deploy/docling/model_manifest.json`：模型文件、版本、SHA-256 和许可证。
- `deploy/docling/verify_offline_runtime.py`：容器、GPU、模型和断网冒烟检查。
- `metadata/config/docling_cleaning_v2.yaml`：路由、OCR、资源、重试、规则和发布门禁。
- `metadata/config/corpus_release.yaml`：当前权威语料版本与 v1/v2 路径。

**核心包**

- `src/bgpkb/cleaning_v2/contracts.py`：稳定 ID、类型和数据契约辅助函数。
- `src/bgpkb/cleaning_v2/preflight.py`：格式、页数、文本层、图片比例、加密和输入指纹。
- `src/bgpkb/cleaning_v2/docling_adapter.py`：Docling 对象到 Canonical Block v2。
- `src/bgpkb/cleaning_v2/ocr_policy.py`：自适应 OCR 决策与证据选择。
- `src/bgpkb/cleaning_v2/transformations.py`：分级规则与 transformation 审计。
- `src/bgpkb/cleaning_v2/batch.py`：状态机、幂等、恢复、重试、隔离和原子输出。
- `src/bgpkb/cleaning_v2/derivations.py`：approved Block 到 Markdown/assets/chunks v2。
- `src/bgpkb/cleaning_v2/migration.py`：v1/v2 差异、覆盖率和人工指标。
- `src/bgpkb/cleaning_v2/release.py`：门禁检查、指针切换与回滚。

**CLI 与测试**

- `src/bgpkb/pipeline/build_cleaning_v2.py`：预检、解析、清洗和批处理 CLI。
- `src/bgpkb/pipeline/build_cleaning_v2_derivatives.py`：派生 Markdown/assets/chunks。
- `src/bgpkb/pipeline/evaluate_cleaning_v2_migration.py`：差异与人工评测。
- `src/bgpkb/pipeline/switch_corpus_release.py`：显式切换和回滚。
- `tests/fixtures/docling/`：固定 Docling JSON、PDF/HTML/TXT/YAML 和错误 fixture。
- `tests/test_cleaning_v2_*.py`：契约、适配、OCR、治理、批处理、迁移和发布测试。

### Task 1: 锁定私有 GPU 运行环境

**Files:**
- Create: `bgp_knowledge_base/deploy/docling/Dockerfile`
- Create: `bgp_knowledge_base/deploy/docling/requirements.lock`
- Create: `bgp_knowledge_base/deploy/docling/model_manifest.json`
- Create: `bgp_knowledge_base/deploy/docling/verify_offline_runtime.py`
- Create: `bgp_knowledge_base/tests/test_docling_runtime_contract.py`
- Create: `bgp_knowledge_base/docs/operations/docling_private_runtime_v1.md`

- [ ] **Step 1: 记录目标 GPU 事实**

在目标服务器执行：

```bash
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
docker version
```

把 GPU、显存、驱动、容器 runtime 和 CUDA 兼容范围写入中文运维文档。未获得目标服务器事实前，不选择 Docling 与 CUDA 锁定版本。

- [ ] **Step 2: 写运行环境失败测试**

测试要求镜像、依赖锁和模型 manifest 存在；manifest 每个模型必须含 `name`、`version`、`path`、`sha256`、`license`；离线验证器在 hash 不匹配或模型缺失时返回失败。

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_docling_runtime_contract.py -v`

Expected: FAIL，部署文件或验证器尚不存在。

- [ ] **Step 3: 创建锁定镜像与验证器**

Dockerfile 必须在构建阶段安装精确依赖并预下载 manifest 中全部模型；运行用户非 root；生产入口不得执行下载。验证器实现如下边界：

```python
def verify_runtime(manifest_path, model_root, expected_image_digest=None):
    """返回结构化检查结果；任一必需资产缺失或 hash 不符时 ok=False。"""
```

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_docling_runtime_contract.py -v`

Expected: PASS。

- [ ] **Step 5: 构建并断网验证容器**

```bash
docker build -t bgpkb-docling-v2:locked -f bgp_knowledge_base/deploy/docling/Dockerfile bgp_knowledge_base
docker run --rm --gpus all --network none bgpkb-docling-v2:locked python deploy/docling/verify_offline_runtime.py
```

Expected: GPU、依赖和全部模型 hash 通过；日志中没有下载或外网请求。

- [ ] **Step 6: 提交运行环境基线**

```bash
git add bgp_knowledge_base/deploy bgp_knowledge_base/tests/test_docling_runtime_contract.py bgp_knowledge_base/docs/operations/docling_private_runtime_v1.md
git commit -m "build: 锁定 Docling 私有 GPU 运行环境"
```

### Task 2: 定义配置与 Canonical Block v2 契约

**Files:**
- Create: `bgp_knowledge_base/metadata/config/docling_cleaning_v2.yaml`
- Create: `bgp_knowledge_base/metadata/schemas/cleaning_v2_preflight.schema.json`
- Create: `bgp_knowledge_base/metadata/schemas/canonical_block_v2.schema.json`
- Create: `bgp_knowledge_base/metadata/schemas/cleaning_v2_table.schema.json`
- Create: `bgp_knowledge_base/metadata/schemas/cleaning_v2_asset.schema.json`
- Create: `bgp_knowledge_base/src/bgpkb/cleaning_v2/__init__.py`
- Create: `bgp_knowledge_base/src/bgpkb/cleaning_v2/contracts.py`
- Create: `bgp_knowledge_base/tests/test_cleaning_v2_contracts.py`

- [ ] **Step 1: 写配置和 Schema 失败测试**

断言配置含 runtime、formats、OCR 触发、资源预算、fallback、重试、规则、质量门槛和 v2 路径；Block 必须含：

```python
REQUIRED_BLOCK_FIELDS = {
    "block_id", "doc_id", "page_id", "parent_block_id", "block_type",
    "heading_level", "reading_order", "bbox", "raw_text", "cleaned_text",
    "language", "quality", "provenance", "review_status", "generated_by",
}
```

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_cleaning_v2_contracts.py -v`

Expected: FAIL，配置、Schema 或模块不存在。

- [ ] **Step 2: 实现稳定 ID 和契约**

```python
def build_block_id(doc_id, page_number, reading_order, block_type, source_anchor):
    payload = f"{doc_id}|{page_number}|{reading_order}|{block_type}|{source_anchor}"
    return f"block_v2_{hashlib.sha256(payload.encode()).hexdigest()}"
```

ID 不得依赖生成时间、临时路径或 Python 对象地址。

- [ ] **Step 3: 运行测试确认 GREEN**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_cleaning_v2_contracts.py -v`

Expected: PASS。

- [ ] **Step 4: 提交数据契约**

```bash
git add bgp_knowledge_base/metadata/config/docling_cleaning_v2.yaml bgp_knowledge_base/metadata/schemas bgp_knowledge_base/src/bgpkb/cleaning_v2 bgp_knowledge_base/tests/test_cleaning_v2_contracts.py
git commit -m "feat: 定义 Canonical Block v2 契约"
```

### Task 3: 实现 Docling 适配与显式 fallback

**Files:**
- Create: `bgp_knowledge_base/src/bgpkb/cleaning_v2/docling_adapter.py`
- Create: `bgp_knowledge_base/tests/fixtures/docling/representative_document.json`
- Create: `bgp_knowledge_base/tests/fixtures/docling/table_document.json`
- Create: `bgp_knowledge_base/tests/test_cleaning_v2_docling_adapter.py`
- Create: `bgp_knowledge_base/tests/test_parse_documents.py`
- Modify: `bgp_knowledge_base/src/bgpkb/pipeline/parse_documents.py`

- [ ] **Step 1: 写适配器失败测试**

使用固定 Docling JSON，不加载模型；断言标题层级、父子关系、reading order、bbox、表格行列/表头/合并单元格、公式、代码、图片引用和来源页完整映射。

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_cleaning_v2_docling_adapter.py -v`

Expected: FAIL，适配器不存在。

- [ ] **Step 2: 实现最小适配器**

对外 API：

```python
def adapt_docling_document(docling_payload, source_meta, runtime_meta, config):
    """返回按 page_number、reading_order、block_id 稳定排序的 Canonical Block。"""
```

禁止把 Docling 未知类型静默降级为正文；未知类型应标记 `unsupported_block_type` 并进入隔离诊断。

- [ ] **Step 3: 写 fallback 失败测试**

断言 Docling 成功时不调用旧解析器；Docling 受控失败且配置允许时输出 `parser_mode=fallback`、原因和 pending_review；未经审核 fallback 不进入发布集合。

- [ ] **Step 4: 实现主引擎路由和 fallback**

旧 `parse_documents.py` 行为保持 v1 兼容；v2 通过独立适配入口调用旧函数，不原地改变 v1 输出。

- [ ] **Step 5: 运行测试确认 GREEN 并提交**

```bash
cd bgp_knowledge_base
PYTHONPATH=src python3 -m pytest tests/test_cleaning_v2_docling_adapter.py tests/test_parse_documents.py -v
git add src/bgpkb/cleaning_v2/docling_adapter.py tests/fixtures/docling tests/test_cleaning_v2_docling_adapter.py src/bgpkb/pipeline/parse_documents.py
git commit -m "feat: 添加 Docling Canonical Block 适配器"
```

### Task 4: 文档预检与自适应 OCR

**Files:**
- Create: `bgp_knowledge_base/src/bgpkb/cleaning_v2/preflight.py`
- Create: `bgp_knowledge_base/src/bgpkb/cleaning_v2/ocr_policy.py`
- Create: `bgp_knowledge_base/tests/fixtures/cleaning_v2/`
- Create: `bgp_knowledge_base/tests/test_cleaning_v2_preflight.py`
- Create: `bgp_knowledge_base/tests/test_cleaning_v2_ocr_policy.py`

- [ ] **Step 1: 写预检失败测试**

覆盖数字 PDF、扫描 PDF、加密 PDF、损坏 PDF、空页、HTML、TXT 和 YAML，断言格式、页数、文本覆盖、图片比例、加密状态、输入 hash 和推荐配置。

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_cleaning_v2_preflight.py -v`

Expected: FAIL，预检模块不存在。

- [ ] **Step 3: 实现预检与输入指纹**

```python
def preflight_document(path, config):
    """不修改输入，返回可序列化的格式、页面和 OCR 路由证据。"""

def processing_fingerprint(source_sha256, image_digest, model_hashes, config_hash):
    """形成幂等处理指纹。"""
```

- [ ] **Step 4: 写 OCR 决策失败测试**

断言高质量文本页不 OCR；无文本层、图片主导和异常低覆盖页启用 OCR；原生文本和 OCR 文本均保留；选择结果含原因、语言、引擎和置信度。

- [ ] **Step 5: 实现 OCR 策略并确认 GREEN**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_cleaning_v2_preflight.py tests/test_cleaning_v2_ocr_policy.py -v`

Expected: PASS。

- [ ] **Step 6: 提交预检与 OCR**

```bash
git add bgp_knowledge_base/src/bgpkb/cleaning_v2 bgp_knowledge_base/tests/fixtures/cleaning_v2 bgp_knowledge_base/tests/test_cleaning_v2_preflight.py bgp_knowledge_base/tests/test_cleaning_v2_ocr_policy.py
git commit -m "feat: 添加文档预检与自适应 OCR"
```

### Task 5: 清洗规则、转换审计与审核隔离

**Files:**
- Create: `bgp_knowledge_base/metadata/schemas/cleaning_transformation_v2.schema.json`
- Create: `bgp_knowledge_base/metadata/schemas/cleaning_review_decision_v2.schema.json`
- Create: `bgp_knowledge_base/src/bgpkb/cleaning_v2/transformations.py`
- Create: `bgp_knowledge_base/tests/test_cleaning_v2_transformations.py`

- [ ] **Step 1: 写规则分级失败测试**

覆盖 Unicode/空白规范化、重复页眉页脚、标题修正、跨页段落、跨页表格和禁止语义改写；每个变化必须产生 transformation。

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_cleaning_v2_transformations.py -v`

Expected: FAIL，转换模块不存在。

- [ ] **Step 3: 实现规则注册与转换审计**

```python
@dataclass(frozen=True)
class CleaningRule:
    rule_id: str
    version: str
    level: str  # lossless | structural | semantic

def apply_rules(raw_blocks, rules, config):
    """返回 cleaned_blocks、transformations 和 review_items。"""
```

结构规则必须记录输入/输出 Block 和前后值；semantic 规则只能生成 review item。

- [ ] **Step 4: 写下游隔离失败测试**

断言 approved Block 可派生；pending、fallback、低置信 OCR 和 conflict Block 被排除并进入复核队列；原始 Block 不被覆盖。

- [ ] **Step 5: 实现隔离并确认 GREEN**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_cleaning_v2_transformations.py -v`

Expected: PASS。

- [ ] **Step 6: 提交转换治理**

```bash
git add bgp_knowledge_base/metadata/schemas/cleaning_* bgp_knowledge_base/src/bgpkb/cleaning_v2/transformations.py bgp_knowledge_base/tests/test_cleaning_v2_transformations.py
git commit -m "feat: 添加清洗转换审计与审核隔离"
```

### Task 6: 可恢复批处理编排

**Files:**
- Create: `bgp_knowledge_base/metadata/schemas/cleaning_run_v2.schema.json`
- Create: `bgp_knowledge_base/metadata/schemas/cleaning_document_status_v2.schema.json`
- Create: `bgp_knowledge_base/src/bgpkb/cleaning_v2/batch.py`
- Create: `bgp_knowledge_base/src/bgpkb/pipeline/build_cleaning_v2.py`
- Create: `bgp_knowledge_base/tests/test_cleaning_v2_batch.py`

- [ ] **Step 1: 写状态机和幂等失败测试**

断言合法状态迁移、非法回退拒绝、相同指纹跳过、配置变化失效、指定阶段恢复和单篇失败不终止批次。

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_cleaning_v2_batch.py -v`

Expected: FAIL，批处理模块不存在。

- [ ] **Step 3: 实现状态机与原子文档事务**

```python
TERMINAL_STATES = {"approved", "quarantined"}

def run_document(job, handlers, state_store, output_root):
    """逐阶段执行；在临时目录校验成功后原子发布单篇产物。"""
```

- [ ] **Step 4: 写故障与重试失败测试**

注入 OOM、超时、暂态模型错误、内容错误、Schema 错误和半写异常；仅前三类有限重试，其他直接隔离；重试达到上限必须终止单篇。

- [ ] **Step 5: 实现重试、隔离和中文报告**

报告包含每篇耗时、页数、OCR 页数、显存、重试、fallback、输出计数，以及批次吞吐、p50/p95 和失败率。

- [ ] **Step 6: 运行测试确认 GREEN 并提交**

```bash
cd bgp_knowledge_base
PYTHONPATH=src python3 -m pytest tests/test_cleaning_v2_batch.py -v
git add metadata/schemas/cleaning_run_v2.schema.json metadata/schemas/cleaning_document_status_v2.schema.json src/bgpkb/cleaning_v2/batch.py src/bgpkb/pipeline/build_cleaning_v2.py tests/test_cleaning_v2_batch.py
git commit -m "feat: 添加可恢复 Docling 清洗批处理"
```

### Task 7: v2 派生与逐文档差异

**Files:**
- Create: `bgp_knowledge_base/src/bgpkb/cleaning_v2/derivations.py`
- Create: `bgp_knowledge_base/src/bgpkb/cleaning_v2/migration.py`
- Create: `bgp_knowledge_base/src/bgpkb/pipeline/build_cleaning_v2_derivatives.py`
- Create: `bgp_knowledge_base/src/bgpkb/pipeline/evaluate_cleaning_v2_migration.py`
- Create: `bgp_knowledge_base/tests/test_cleaning_v2_derivations.py`
- Create: `bgp_knowledge_base/tests/test_cleaning_v2_migration.py`

- [ ] **Step 1: 写派生失败测试**

断言只有 approved Block 进入 Markdown/chunks；表格、代码、公式和图片引用保留；source_ref、页码与 Block ID 可回溯；相同输入输出稳定。

- [ ] **Step 2: 实现派生器并确认 GREEN**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_cleaning_v2_derivations.py -v`

- [ ] **Step 3: 写 v1/v2 差异失败测试**

差异必须覆盖正文覆盖率、标题、section、表格、图片、chunk、来源引用和 transformation 归因；低于 99.5% 或存在不可归因删除时阻断。

- [ ] **Step 4: 实现差异与稳定性评测**

```python
def compare_document_v1_v2(v1, v2, transformations, thresholds):
    """返回机器可读指标、阻断问题和中文解释。"""
```

- [ ] **Step 5: 运行目标测试并提交**

```bash
cd bgp_knowledge_base
PYTHONPATH=src python3 -m pytest tests/test_cleaning_v2_derivations.py tests/test_cleaning_v2_migration.py -v
git add src/bgpkb/cleaning_v2/derivations.py src/bgpkb/cleaning_v2/migration.py src/bgpkb/pipeline/build_cleaning_v2_derivatives.py src/bgpkb/pipeline/evaluate_cleaning_v2_migration.py tests/test_cleaning_v2_derivations.py tests/test_cleaning_v2_migration.py
git commit -m "feat: 生成清洗 v2 派生产物与差异评测"
```

### Task 8: 全量迁移与人工高风险验收

**Files:**
- Create: `bgp_knowledge_base/data/review_inputs/cleaning_v2_gold_annotations.json`（缩进 JSON 数组，便于人工审阅）
- Create: `bgp_knowledge_base/data/derived/datasets/cleaning_v2_gold_eval_results.jsonl`
- Create: `bgp_knowledge_base/docs/review/cleaning_v2_gold_annotation_guide.md`
- Create: `bgp_knowledge_base/tests/test_cleaning_v2_gold_eval.py`
- Generated: `bgp_knowledge_base/data/corpus/*_v2/`
- Generated: `bgp_knowledge_base/data/generated/reports/corpus/cleaning_v2/`

- [ ] **Step 1: 全量运行 54 篇语料**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m bgpkb.pipeline.build_cleaning_v2 --all`

Expected: 每篇进入 approved 或 quarantined；单篇错误不丢失；v1 未改变。

- [ ] **Step 2: 修复所有 quarantined 与 fallback 阻断项**

每个修复先新增失败 fixture 或回归测试；禁止通过降低门槛静默放行。

- [ ] **Step 3: 选择并标注约 12 篇高风险文档**

必须覆盖复杂 PDF、扫描页、表格、RFC、HTML、超长文档和中英混排。指南定义标题、阅读顺序、表格单元格和 OCR 字符标注方式。

- [ ] **Step 4: 写人工指标计算失败测试并实现评测**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_cleaning_v2_gold_eval.py -v`

门槛：标题 F1 ≥95%、阅读顺序 ≥98%、表格结构 ≥95%、OCR CER ≤2%。

- [ ] **Step 5: 连续运行两次并比较稳定性**

除允许时间字段外，第二次运行必须无差异；保存两次 run_id 和比较报告。

- [ ] **Step 6: 提交迁移数据与证据**

提交前确认生成数据规模、二进制资产策略和 Git/LFS 边界；不得把未登记的大模型文件提交仓库。

### Task 9: 发布指针、回滚与阶段集成

**Files:**
- Create: `bgp_knowledge_base/metadata/config/corpus_release.yaml`
- Create: `bgp_knowledge_base/src/bgpkb/cleaning_v2/release.py`
- Create: `bgp_knowledge_base/src/bgpkb/pipeline/switch_corpus_release.py`
- Create: `bgp_knowledge_base/tests/test_cleaning_v2_release.py`
- Modify: `bgp_knowledge_base/src/bgpkb/pipeline/quality_check.py`
- Modify: `bgp_knowledge_base/src/bgpkb/pipeline/build_artifact_manifest.py`
- Modify: `bgp_knowledge_base/src/bgpkb/pipeline/run_pipeline.py`
- Modify: `bgp_knowledge_base/metadata/config/report_policy.yaml`
- Modify: `bgp_knowledge_base/metadata/config/stage_acceptance_gates.yaml`
- Create: `bgp_knowledge_base/docs/stages/docling_private_cleaning_v2.md`
- Modify: `bgp_knowledge_base/docs/roadmap/industry_alignment_improvement_plan_v1.md`

- [ ] **Step 1: 写发布与回滚失败测试**

断言硬门禁或人工指标未通过时禁止切换；切换必须显式、原子、生成新 manifest；回滚恢复 v1 并保留 v2 证据。

- [ ] **Step 2: 实现发布指针和命令**

```python
def switch_release(target_version, gate_result, expected_current, config_path):
    """先校验 current 与 gate，再原子写入版本化发布指针。"""
```

- [ ] **Step 3: 接入质量、制品、流水线和阶段 gate**

主流水线在切换前运行并行 v2，但仍从 release pointer 选择权威版本；质量检查同时验证当前版本和迁移门禁；报告全部登记 producer。

- [ ] **Step 4: 运行目标与全量测试**

```bash
cd bgp_knowledge_base
PYTHONPATH=src python3 -m pytest tests/test_cleaning_v2_*.py -v
PYTHONPATH=src python3 -m pytest -q
PYTHONPATH=src python3 -m bgpkb.pipeline.run_pipeline
```

Expected: 0 failures，确定性流水线通过。

- [ ] **Step 5: 运行阶段验收和 OpenSpec 校验**

```bash
cd bgp_knowledge_base
PYTHONPATH=src python3 -m bgpkb.pipeline.run_stage_acceptance --stage docling_private_cleaning_v2
cd ..
openspec validate docling-private-cleaning-v2 --strict
git diff --check
```

- [ ] **Step 6: 显式切换、回滚演练并恢复 v2**

```bash
cd bgp_knowledge_base
PYTHONPATH=src python3 -m bgpkb.pipeline.switch_corpus_release --target v2 --write
PYTHONPATH=src python3 -m bgpkb.pipeline.run_pipeline
PYTHONPATH=src python3 -m bgpkb.pipeline.switch_corpus_release --target v1 --write
PYTHONPATH=src python3 -m bgpkb.pipeline.switch_corpus_release --target v2 --write
PYTHONPATH=src python3 -m bgpkb.pipeline.run_pipeline
```

Expected: 三次切换均有审计；最终指针为 v2；v1 数据仍完整。

- [ ] **Step 7: 敏感信息、模型文件和工作树检查**

确认无 API key、`.env`、未登记模型、容器缓存、临时目录或未审查二进制；确认所有 OpenSpec 任务完成。

- [ ] **Step 8: 提交最终验收证据**

```bash
git add openspec/changes/docling-private-cleaning-v2 bgp_knowledge_base
git commit -m "chore: 完成 Docling 私有化清洗 v2 验收"
```
