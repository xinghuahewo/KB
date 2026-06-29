# 阶段五标准化出口实施计划

> **面向代理执行者：** 必须使用 `superpowers:executing-plans` 或 `superpowers:subagent-driven-development` 按任务执行；所有步骤使用复选框跟踪。

**目标：** 在不改变现有 JSONL、CSV、SQLite 和 RAG 接口的前提下，交付可复跑的 JSON-LD、SKOS、PROV-O、RDF 样例以及受人工审核约束的模型映射候选链路。

**架构：** 确定性生成器读取现有发布目录和语义 ID，使用集中配置生成正式标准出口；模型仅生成 `pending_review` 候选，人工决策经审计和显式 `--write` 后形成批准映射覆盖层。正式出口只消费确定性配置和批准映射，不直接消费模型响应。

**技术栈：** Python 3.10+、PyYAML、JSON/JSONL/CSV、JSON-LD、SKOS、PROV-O、Turtle、pytest、OpenSpec。

---

## 文件职责

- `metadata/config/standard_exports.yaml`：类型、关系、输出、模型和安全边界配置。
- `metadata/schemas/standard_mapping_candidate.schema.json`：模型候选结构约束。
- `metadata/schemas/standard_mapping_audit.schema.json`：人工审核审计结构约束。
- `metadata/schemas/provenance_record.schema.json`：PROV 导出记录结构约束。
- `src/bgpkb/pipeline/build_standard_exports.py`：确定性 JSON-LD、PROV、Turtle 和报告生成。
- `src/bgpkb/pipeline/build_standard_mapping_candidates.py`：mock/DeepSeek 映射候选生成与响应校验。
- `src/bgpkb/pipeline/build_standard_mapping_decision_audit.py`：人工决策读取和审计。
- `src/bgpkb/pipeline/apply_standard_mapping_decisions.py`：dry-run 与显式批准映射写入。
- `tests/test_standard_exports.py`：确定性出口行为测试。
- `tests/test_standard_mapping_candidates.py`：模型候选安全边界测试。
- `tests/test_standard_mapping_review.py`：审核与显式应用测试。

### 任务 1：建立 OpenSpec 变更与阶段五配置骨架

**文件：**

- 新建：`openspec/changes/phase-5-standard-exports/`
- 新建：`metadata/config/standard_exports.yaml`
- 新建：`metadata/schemas/standard_mapping_candidate.schema.json`
- 新建：`metadata/schemas/standard_mapping_audit.schema.json`
- 新建：`metadata/schemas/provenance_record.schema.json`
- 修改：`docs/stages/phase_5_standard_exports_v1.md`

- [ ] 创建 OpenSpec proposal、design、spec 和 tasks，并验证为 apply-ready。
- [ ] 修正文档中“尚无 JSON-LD context 和命名空间”的过期基线。
- [ ] 定义确定性实体类型映射、关系谓词映射、允许前缀和模型安全策略。
- [ ] 定义候选、审计和溯源记录 Schema。
- [ ] 运行 `git diff --check`，确认中文文档和配置无格式错误。
- [ ] 提交：`docs: 准备阶段五标准化出口配置`。

### 任务 2：以 TDD 实现确定性标准出口

**文件：**

- 新建：`tests/test_standard_exports.py`
- 新建：`src/bgpkb/pipeline/build_standard_exports.py`
- 修改：`metadata/config/report_policy.yaml`

- [ ] 先写测试，断言 `build_entity_jsonld()` 为批准实体生成稳定 `@id`、`skos:Concept`、标签、定义和来源 URI。
- [ ] 运行 `PYTHONPATH=src python3 -m pytest tests/test_standard_exports.py -v`，确认因模块不存在而失败。
- [ ] 实现 JSONL/config 加载、URI 索引、实体与来源 JSON-LD 映射的最小代码。
- [ ] 重跑测试，确认实体与来源映射通过。
- [ ] 新增失败测试，要求 provenance 记录表达 source→raw→parsed→cleaned→chunk→entity 主链、生成活动和证据链。
- [ ] 实现 `build_provenance_records()`，并保证记录排序稳定。
- [ ] 新增失败测试，要求 Turtle 转义引号、反斜杠和换行，支持 IRI/CURIE/literal 三类对象，并按主语/谓词/宾语排序。
- [ ] 新增失败测试，要求未登记对象类型、IRI 中非法控制字符和 literal 中不允许的控制字符被显式拒绝。
- [ ] 实现仅覆盖本项目输出所需的 Turtle 序列化器，并用独立最小语法检查重新解析生成的三元组数量。
- [ ] 新增 CLI 集成测试，要求生成 `entity_catalog.jsonld`、`source_catalog.jsonld`、`provenance_map.jsonl`、Turtle 样例和中文报告。
- [ ] 实现 `main()`、报告统计和 `standardization_report` 报告策略。
- [ ] 运行 `PYTHONPATH=src python3 -m pytest tests/test_standard_exports.py -v`，确认全部通过。
- [ ] 提交：`feat: 生成阶段五确定性标准出口`。

### 任务 3：以 TDD 实现模型映射候选层

**文件：**

- 新建：`tests/test_standard_mapping_candidates.py`
- 新建：`src/bgpkb/pipeline/build_standard_mapping_candidates.py`
- 修改：`metadata/config/report_policy.yaml`

- [ ] 先写失败测试，要求 mock provider 对未映射本地关系生成稳定 `pending_review` 候选。
- [ ] 运行目标测试，确认因模块不存在而失败。
- [ ] 实现候选 ID、证据、置信度、provider/model/prompt_version 和状态字段。
- [ ] 新增失败测试，要求非法 JSON、未知前缀、无证据、缺少输入指纹和越权批准状态被拒绝。
- [ ] 实现 `validate_candidate()`、输入指纹、含指纹 candidate ID 和结构化 DeepSeek 响应解析函数。
- [ ] 新增失败测试，要求缺少 `DEEPSEEK_API_KEY` 时返回 skipped 且不覆盖既有候选。
- [ ] 实现 opt-in DeepSeek 调用边界；测试只注入假响应，不联网。
- [ ] 实现候选 JSONL 和中文生成报告。
- [ ] 运行目标测试，确认全部通过。
- [ ] 提交：`feat: 添加模型辅助标准映射候选`。

### 任务 4：以 TDD 实现人工审核与显式应用

**文件：**

- 新建：`tests/test_standard_mapping_review.py`
- 新建：`src/bgpkb/pipeline/build_standard_mapping_decision_audit.py`
- 新建：`src/bgpkb/pipeline/apply_standard_mapping_decisions.py`
- 新建：`data/review_inputs/standard_mapping_decisions.csv`
- 修改：`metadata/config/report_policy.yaml`

- [ ] 先写失败测试，覆盖 approved、rejected、needs_evidence、unreviewed、未知候选、陈旧指纹、缺少审核人/时间和冲突批准。
- [ ] 运行目标测试，确认因模块不存在而失败。
- [ ] 实现决策 CSV 解析、重复项检查和审计状态计算。
- [ ] 新增失败测试，要求默认运行只写 preview，不写批准映射。
- [ ] 实现 dry-run preview 和中文审计/应用报告。
- [ ] 新增失败测试，要求只有审计通过的 approved 项在 `--write` 时进入 `approved_standard_mappings.jsonl`。
- [ ] 实现显式写入、稳定排序和重复候选保护。
- [ ] 运行目标测试，确认全部通过。
- [ ] 提交：`feat: 添加标准映射人工审核闸门`。

### 任务 5：接入流水线、制品清单和阶段验收

**文件：**

- 修改：`src/bgpkb/pipeline/run_pipeline.py`
- 修改：`src/bgpkb/pipeline/build_artifact_manifest.py`
- 修改：`metadata/config/stage_acceptance_gates.yaml`
- 修改：`tests/test_stage_acceptance.py`
- 修改：`docs/README.md`
- 修改：`docs/stages/phase_5_standard_exports_v1.md`

- [ ] 先写失败测试，要求阶段五 gate 注册交付物、命令、报告检查和效果说明。
- [ ] 运行 `PYTHONPATH=src python3 -m pytest tests/test_stage_acceptance.py -v`，确认阶段五断言失败。
- [ ] 配置 `phase_5_standard_exports_v1` 验收 gate。
- [ ] 在确定性流水线中按“语义 ID → 候选 → 审计 → dry-run → 标准出口”的顺序接入步骤。
- [ ] 为新增数据集、发布物和报告登记制品 producer。
- [ ] 更新阶段五状态、运行命令、边界和项目索引。
- [ ] 生成离线候选、审核 preview 和正式标准出口。
- [ ] 运行阶段五目标测试与 `run_stage_acceptance --stage phase_5_standard_exports_v1`。
- [ ] 提交：`feat: 接入阶段五流水线与验收`。

### 任务 6：全量验证与收尾

**文件：**

- 修改：`openspec/changes/phase-5-standard-exports/tasks.md`
- 按生成结果修改：`data/derived/`、`data/published/`、`data/generated/`、`data/reports/`

- [ ] 运行 `PYTHONPATH=src python3 -m pytest -q`，确认全部测试通过。
- [ ] 运行阶段五四个 CLI，并确认第二次生成无非时间字段漂移。
- [ ] 运行 `git diff --check`，区分生成 CSV 的既有换行约定与真实格式问题。
- [ ] 扫描提交内容，确认没有 API key、token 或 `.env`。
- [ ] 检查 `git status`、阶段五产物清单和 OpenSpec 任务完成率。
- [ ] 提交：`chore: 完成阶段五标准化出口验收`。
