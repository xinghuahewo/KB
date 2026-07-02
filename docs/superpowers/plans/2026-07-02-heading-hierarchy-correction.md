# 确定性标题层级校正实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不按文档硬编码的前提下，修复 Docling 退化标题层级，恢复 fallback 文档章节结构，并使 12 篇高风险验收集标题层级 F1 达到 95%。

**Architecture:** 新增纯函数标题推断器，基于原始层级可靠性、编号体系和文档顺序输出候选标题、父级、证据与置信度。运行时通过结构 transformation 应用候选；评测复用同一推断器，避免评测逻辑与生产逻辑漂移。既有 parsed Block 保持不变，校正只作用于 cleaned 派生层。

**Tech Stack:** Python 3.11、pytest、Canonical Block v2、JSON Schema、OpenSpec。

---

### Task 1: 标题层级推断器

**Files:**
- Create: `bgp_knowledge_base/src/bgpkb/cleaning_v2/heading_hierarchy.py`
- Create: `bgp_knowledge_base/tests/test_cleaning_v2_heading_hierarchy.py`

- [x] 先写失败测试：识别层级全部相同的退化输出。
- [x] 运行单测确认因模块缺失而失败。
- [x] 实现阿拉伯数字、罗马数字、字母章节、附录与默认标题规则。
- [x] 增加文档级顺序状态和“最多跳一级、父级必须存在”约束。
- [x] 增加 RFC/YAML fallback 段落标题提升，以及明确的 MANRS Action/Discussion 类通用模式。
- [x] 输出 `block_id/text/level/parent_block_id/evidence/confidence/promoted`，不修改输入。
- [x] 运行新模块单测并提交。

### Task 2: transformation 与运行时接入

**Files:**
- Modify: `bgp_knowledge_base/src/bgpkb/cleaning_v2/transformations.py`
- Modify: `bgp_knowledge_base/src/bgpkb/cleaning_v2/runtime_pipeline.py`
- Modify: `bgp_knowledge_base/metadata/config/docling_cleaning_v2.yaml`
- Modify: `bgp_knowledge_base/tests/test_cleaning_v2_transformations.py`
- Modify: `bgp_knowledge_base/tests/test_cleaning_v2_runtime_pipeline.py`

- [x] 先写失败测试：层级校正及 paragraph-to-heading 提升必须产生结构 transformation。
- [x] 运行测试确认失败原因正确。
- [x] 实现 `infer_heading_hierarchy` 结构规则，保存 before/after、规则证据和置信度。
- [x] 保留 parsed 原始 Block，结构变更进入复核队列；经显式批次决策批准后才可发布。
- [x] 运行 transformation 与 runtime 测试并提交。

### Task 3: 金标一致性与正式评测

**Files:**
- Modify: `bgp_knowledge_base/src/bgpkb/cleaning_v2/evaluation.py`
- Modify: `bgp_knowledge_base/src/bgpkb/pipeline/build_cleaning_v2_acceptance_report.py`
- Modify: `bgp_knowledge_base/data/review_inputs/cleaning_v2_gold_annotations.json`
- Modify: `bgp_knowledge_base/tests/test_cleaning_v2_evaluation.py`

- [x] 先写失败测试：评测必须复用生产推断结果，且不得按 `doc_id` 查表。
- [x] 修正金标中与已批准编号规则冲突的明显层级（如 `3.1` 必须低于 `3`），保留修改审计说明。
- [x] 将评测输入切换为生产标题候选，而不是未经校正的 Docling `level`。
- [x] 运行 12 篇评测；若 F1 仍低于 95%，只根据可泛化模式补规则，不加文档特例。
- [x] 生成机器结果和中文报告并提交。

### Task 4: 全量验证与任务状态

**Files:**
- Modify: `openspec/changes/docling-private-cleaning-v2/tasks.md`
- Regenerate: `bgp_knowledge_base/data/derived/datasets/cleaning_v2_human_acceptance.json`
- Regenerate: `bgp_knowledge_base/data/generated/reports/corpus/cleaning_v2_human_acceptance_report.md`
- Regenerate: `bgp_knowledge_base/data/derived/datasets/artifact_manifest.*`
- Regenerate: `bgp_knowledge_base/data/reports/gates/quality_report.md`

- [x] 运行标题模块、transformation、runtime 和评测定向测试。
- [x] 运行完整 pytest、质量检查和 OpenSpec strict validate。
- [x] 确认四项人工验收指标全部达到门槛。
- [x] 勾选 7.3，并提交中文验收证据。
