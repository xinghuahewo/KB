# 阶段 A：语料质量画像实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立跨 parsed、cleaned、chunks 的确定性语料画像，以及与门禁隔离的可选 OCR 模型评估，并完成主流水线和阶段验收接入。

**Architecture:** `profile_cleaned_corpus.py` 负责稳定、离线的文档并集、指标、问题分级和中文报告；`assess_corpus_ocr_quality.py` 负责固定抽样、预算与 Provider 调度，模型结果独立写入 OCR 评估数据集。配置、Schema、质量检查、制品清单与阶段 gate 共同形成治理闭环。

**Tech Stack:** Python 3 标准库、PyYAML、pytest、JSONL、JSON Schema 子集校验、OpenSpec。

---

### Task 1: 配置与确定性画像契约

**Files:**
- Create: `bgp_knowledge_base/metadata/config/corpus_profiling.yaml`
- Create: `bgp_knowledge_base/metadata/schemas/corpus_profile.schema.json`
- Create: `bgp_knowledge_base/metadata/schemas/corpus_ocr_assessment.schema.json`
- Create: `bgp_knowledge_base/tests/test_corpus_profiling.py`

- [ ] **Step 1: 写配置和 Schema 失败测试**

测试加载配置，断言存在排除规则、文档阈值、表格阈值、模型预算和 Provider 白名单；加载两个 Schema 并断言 required 字段、枚举和 additionalProperties 边界。

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_corpus_profiling.py -v`

Expected: FAIL，提示配置或 Schema 文件不存在。

- [ ] **Step 3: 创建最小配置和 Schema**

配置必须包含 `exclude_globs`、`thresholds`、`table_detection`、`ocr_assessment`；画像 Schema 必须区分 `blocking_issues` 与 `warnings`；OCR Schema 必须约束 `status` 和 `risk_level`。

- [ ] **Step 4: 重跑目标测试确认 GREEN**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_corpus_profiling.py -v`

Expected: PASS。

- [ ] **Step 5: 提交配置与契约**

```bash
git add bgp_knowledge_base/metadata bgp_knowledge_base/tests/test_corpus_profiling.py
git commit -m "test: 定义阶段 A 语料画像契约"
```

### Task 2: 确定性画像生成器

**Files:**
- Create: `bgp_knowledge_base/src/bgpkb/pipeline/profile_cleaned_corpus.py`
- Modify: `bgp_knowledge_base/tests/test_corpus_profiling.py`

- [ ] **Step 1: 写并集、排除和指标失败测试**

使用 `tmp_path` 构造 parsed、cleaned、chunks 输入，断言输出是三层 `doc_id` 并集、README 被排除、seed 被保留，并精确检查字符、段落、section、chunk、替换字符、表格行、异常符号和标题指标。

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_corpus_profiling.py -k 'union or metrics' -v`

Expected: FAIL，提示模块或函数不存在。

- [ ] **Step 3: 实现输入加载和稳定画像**

实现 `load_parsed_documents()`、`load_cleaned_documents()`、`load_chunks()`、`build_corpus_profiles()`；所有记录和问题代码排序稳定，解析失败抛出带路径的异常。

- [ ] **Step 4: 写四类阻断与告警隔离失败测试**

分别覆盖 `empty_cleaned_content`、`replacement_character`、`duplicate_doc_id`、`orphan_chunk_document`，并证明超短、超长、表格、异常符号、空标题、重复标题和阶段缺失只进入 warnings。

- [ ] **Step 5: 运行测试确认 RED**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_corpus_profiling.py -k 'blocking or warning' -v`

Expected: FAIL，问题分类尚未实现。

- [ ] **Step 6: 实现问题分级、原子输出和中文报告**

实现稳定 JSONL、原子替换、报告汇总和 CLI；有阻断项时先写产物再返回 1，输入解析失败时不覆盖旧产物。

- [ ] **Step 7: 运行完整画像测试确认 GREEN**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_corpus_profiling.py -v`

Expected: PASS。

- [ ] **Step 8: 在当前语料生成基线**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m bgpkb.pipeline.profile_cleaned_corpus`

Expected: 写出 `corpus_profile.jsonl` 和中文报告；若命中硬错误，先补失败测试再修复数据或逻辑。

- [ ] **Step 9: 提交确定性画像**

```bash
git add bgp_knowledge_base/src/bgpkb/pipeline/profile_cleaned_corpus.py bgp_knowledge_base/tests/test_corpus_profiling.py bgp_knowledge_base/data/derived/datasets/corpus_profile.jsonl bgp_knowledge_base/data/generated/reports/corpus/corpus_profile_report.md
git commit -m "feat: 生成阶段 A 确定性语料画像"
```

### Task 3: 可选 OCR Provider 与评估数据集

**Files:**
- Create: `bgp_knowledge_base/src/bgpkb/service/corpus_ocr_provider.py`
- Create: `bgp_knowledge_base/src/bgpkb/pipeline/assess_corpus_ocr_quality.py`
- Create: `bgp_knowledge_base/tests/test_corpus_ocr_assessment.py`
- Modify: `bgp_knowledge_base/src/bgpkb/service/llm_client.py`
- Modify: `bgp_knowledge_base/src/bgpkb/pipeline/profile_cleaned_corpus.py`

- [ ] **Step 1: 写首中尾抽样和预算失败测试**

断言长文档抽样覆盖首、中、尾且不超过单篇上限；批次按稳定顺序遵守最大文档和总字符预算，超限项标记 skipped。

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_corpus_ocr_assessment.py -v`

Expected: FAIL，模块不存在。

- [ ] **Step 3: 实现抽样、指纹、预算和 mock Provider**

提供窄 Provider 协议；mock 产生稳定 `low|medium|high` 结构化结果，不访问网络。

- [ ] **Step 4: 写 DeepSeek 缺密钥、失败和非法响应测试**

注入假 HTTP 响应，不联网；断言治理字段由系统生成，密钥和原始响应不落盘，既有成功记录不被 skipped/failed 覆盖。

- [ ] **Step 5: 运行测试确认 RED**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_corpus_ocr_assessment.py -k 'deepseek or invalid or preserve' -v`

Expected: FAIL，真实适配边界尚未实现。

- [ ] **Step 6: 实现 DeepSeek 结构化适配与独立数据集**

扩展现有客户端的 OCR payload/调用方法；CLI 默认 disabled，显式 `--provider mock|deepseek` 才执行；原子写入经过校验的记录。

- [ ] **Step 7: 合并模型状态到中文报告**

报告分区展示确定性指标与模型结果，明确模型不参与门禁；无评估或缺密钥时显示 skipped 原因。

- [ ] **Step 8: 运行 OCR 与画像测试确认 GREEN**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_corpus_ocr_assessment.py tests/test_corpus_profiling.py tests/test_llm_client.py -v`

Expected: PASS。

- [ ] **Step 9: 生成离线评估基线并提交**

```bash
cd bgp_knowledge_base
PYTHONPATH=src python3 -m bgpkb.pipeline.assess_corpus_ocr_quality --provider mock --generated-at 2026-06-30T00:00:00Z
git add src/bgpkb/service src/bgpkb/pipeline tests data/derived/datasets/corpus_ocr_assessments.jsonl data/generated/reports/corpus/corpus_profile_report.md
git commit -m "feat: 添加可选 OCR 质量评估"
```

### Task 4: 治理与流水线接入

**Files:**
- Modify: `bgp_knowledge_base/metadata/config/report_policy.yaml`
- Modify: `bgp_knowledge_base/metadata/config/stage_acceptance_gates.yaml`
- Modify: `bgp_knowledge_base/src/bgpkb/pipeline/build_artifact_manifest.py`
- Modify: `bgp_knowledge_base/src/bgpkb/pipeline/quality_check.py`
- Modify: `bgp_knowledge_base/src/bgpkb/pipeline/run_pipeline.py`
- Create: `bgp_knowledge_base/docs/stages/phase_a_corpus_profiling_v1.md`
- Create: `bgp_knowledge_base/tests/test_corpus_profiling_integration.py`
- Modify: `bgp_knowledge_base/tests/test_stage_acceptance.py`
- Modify: `bgp_knowledge_base/docs/roadmap/industry_alignment_improvement_plan_v1.md`
- Modify: `bgp_knowledge_base/docs/README.md`
- Modify: `bgp_knowledge_base/README.md`

- [ ] **Step 1: 写治理接入失败测试**

断言报告已注册、producer 正确、质量检查校验两个 Schema 且只阻断确定性问题、主流水线包含离线画像步骤、阶段 A gate 具备交付物和效果说明。

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_corpus_profiling_integration.py tests/test_stage_acceptance.py -v`

Expected: FAIL，接入项尚未注册。

- [ ] **Step 3: 实现报告、producer、质量检查和主流水线接入**

确定性画像在 chunk 生成后运行；默认 OCR 步骤只生成 disabled/skipped 状态，不联网；制品清单必须登记新增数据集、报告、配置和 Schema。

- [ ] **Step 4: 新增中文阶段文档、gate 与路线图状态更新**

文档说明能力、命令、硬门禁、模型边界和剩余人工事项；路线图标记阶段 A 已交付，并标注阶段五已覆盖 PROV/JSON-LD 部分。

- [ ] **Step 5: 运行集成测试确认 GREEN**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_corpus_profiling_integration.py tests/test_stage_acceptance.py -v`

Expected: PASS。

- [ ] **Step 6: 提交治理接入**

```bash
git add bgp_knowledge_base
git commit -m "feat: 接入阶段 A 流水线与验收"
```

### Task 5: 全量验证与最终证据

**Files:**
- Modify: `openspec/changes/phase-a-corpus-profiling/tasks.md`
- Modify: generated reports and manifests produced by verification commands

- [ ] **Step 1: 运行阶段 A 目标测试**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest tests/test_corpus_profiling.py tests/test_corpus_ocr_assessment.py tests/test_corpus_profiling_integration.py tests/test_stage_acceptance.py tests/test_llm_client.py -v`

Expected: PASS，0 failures。

- [ ] **Step 2: 运行完整确定性流水线**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m bgpkb.pipeline.run_pipeline`

Expected: 总体状态通过，阶段 A 步骤不访问网络。

- [ ] **Step 3: 运行全量测试**

Run: `cd bgp_knowledge_base && PYTHONPATH=src python3 -m pytest -q`

Expected: PASS，0 failures。

- [ ] **Step 4: 运行阶段 A 验收与 OpenSpec 校验**

```bash
cd bgp_knowledge_base
PYTHONPATH=src python3 -m bgpkb.pipeline.run_stage_acceptance --stage phase_a_corpus_profiling_v1
cd ..
openspec validate phase-a-corpus-profiling --strict
```

Expected: 阶段结论 `pass`；OpenSpec valid。

- [ ] **Step 5: 检查格式、敏感信息与任务完成率**

```bash
git diff --check
git grep -nE 'sk-[A-Za-z0-9]{16,}|DEEPSEEK_API_KEY=' -- ':!*.example' ':!docs/**'
openspec status --change phase-a-corpus-profiling
git status --short
```

Expected: 无真实密钥；所有任务完成；只有预期变更。

- [ ] **Step 6: 提交最终验收证据**

```bash
git add openspec/changes/phase-a-corpus-profiling bgp_knowledge_base
git commit -m "chore: 完成阶段 A 语料画像验收"
```
