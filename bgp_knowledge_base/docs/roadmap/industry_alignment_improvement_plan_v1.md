---
title: "BGP 知识库工业界对齐改进方案 v1"
document_type: "规划与治理文档"
purpose: "基于当前知识清洗、拆分、分类、结构化、追溯和更新能力，给出贴近工业界成熟知识工程实践的本地改进路线。"
scope: "BGP 知识库数据准备、治理、RAG 就绪和发布维护链路"
status: "现行参考；阶段 A 已交付"
last_reviewed: "2026-06-30"
---
# BGP 知识库工业界对齐改进方案 v1

## 1. 结论

当前项目已经具备确定性流水线、质量检查、人工复核、发布包和追溯索引，适合作为 BGP 知识库数据底座。与工业界成熟知识工程相比，差距不在“有没有数据链路”，而在以下五点：

1. 清洗仍以文本规范化为主，缺少版面、表格、OCR 质量和语料 profiling。
2. chunk 已有段落/句子级切分，但缺少父子层级、语义边界和检索效果驱动调参。
3. 分类体系已经存在，但自动分类主要靠少量关键词规则，缺少同义词、置信度和人工校正闭环。
4. 实体和关系结构化结果较完整，但自动候选抽取仍是占位能力，主要依赖人工 JSONL 种子。
5. 追溯和更新机制稳健，但还没有形成标准化 lineage 事件、增量构建、CI 调度和过期知识监控。

改进原则是：不推倒重来，不直接引入重型平台；在现有目录和流水线上补齐 profiling、候选层、置信度、增量依赖、标准化出口和验收指标。

## 2. 改进路线总览

| 阶段 | 目标 | 本地新增或修改 | 验收方式 |
| --- | --- | --- | --- |
| 阶段 A：语料质量画像 | 已交付：让清洗质量可量化 | 已新增语料 profiling、独立 OCR 评估、报告和指标数据集 | 已能看到长度分布、异常文档、表格/替换字符/OCR 风险 |
| 阶段 B：层级 chunk | 让检索可在段落和章节之间回扩 | 扩展 chunk schema，新增父子 chunk 或 section catalog | 查询命中子 chunk 时可定位父 section |
| 阶段 C：分类增强 | 让主题标签有置信度和人工闭环 | 新增同义词配置、分类候选数据集和低置信复核队列 | chunk topic 覆盖率、置信度分布和复核队列可报告 |
| 阶段 D：结构化候选层 | 从人工实体种子升级为“自动候选 + 人工批准” | 新增实体候选、关系候选、字段候选抽取脚本 | 候选不会直接写入主实体，必须经审计和人工复核 |
| 阶段 E：追溯标准化 | 把内部追溯升级为可交换 lineage | 新增 run manifest、输入输出依赖和 PROV/JSON-LD 样例出口 | 每次流水线运行可追到输入、输出、脚本和 hash |
| 阶段 F：增量更新与 CI | 降低维护成本，形成持续运营 | 新增依赖图、增量重跑命令、CI 检查脚本 | 修改单个来源或实体时只提示受影响步骤 |

## 3. 六个维度的本地落地方案

### 3.1 知识清洗

交付状态：阶段 A 已于 2026-06-30 完成。确定性画像、四类硬门禁、可选 OCR Provider、派生数据集和中文报告均已进入主流水线与阶段验收。

当前基线：

- `src/bgpkb/pipeline/parse_documents.py` 已支持 TXT、HTML、YAML、PDF。
- `data/corpus/cleaned/` 已有 Markdown 语料。
- `quality_check.py` 已检查 parsed、cleaned、chunk、实体和引用一致性。

工业界成熟做法：

- 文档解析不仅提取文本，还识别表格、标题层级、页眉页脚、阅读顺序和 OCR 风险。
- 清洗前后有 profiling，能持续观察长度分布、空文档、替换字符、乱码、异常章节和重复内容。
- 复杂 PDF 采用版面感知解析工具；在本项目中可先用轻量 profiling 做门禁，不急于替换解析器。

本地改进：

- 新增 `src/bgpkb/pipeline/profile_cleaned_corpus.py`，读取 `data/corpus/parsed/`、`data/corpus/cleaned/`、`data/corpus/chunks/`，输出 `data/derived/datasets/corpus_profile.jsonl` 和 `data/generated/reports/corpus/corpus_profile_report.md`。
- 指标至少包含：字符数、section 数、chunk 数、平均段落长度、超短/超长文档、替换字符数量、疑似表格行数、疑似 OCR 噪声、空标题、重复标题。
- 将 profiling 摘要接入 `src/bgpkb/pipeline/build_coverage_report.py` 或新增独立报告入口，不先阻断流水线。
- 当 profiling 连续稳定后，再把关键指标接入 `quality_check.py`，例如“替换字符数必须为 0”“cleaned 正文不能为空”“疑似空 PDF 必须进入缺口队列”。

暂不做：

- 暂不直接引入完整 OCR 或商业解析服务。
- 暂不把 `parse_documents.py` 全量替换为 Docling/Unstructured，先保留确定性解析器。

### 3.2 知识拆分

当前基线：

- `src/bgpkb/pipeline/build_chunks.py` 已按 section、段落、句子和字符逐级切分。
- chunk 包含 `doc_id`、`source_type`、`section_path`、`topics`、`source_ref`。

工业界成熟做法：

- 技术文档采用结构感知切分，保留章节、表格、代码块和父子层级。
- RAG 检索常用多粒度策略：先召回小 chunk，再回扩父 section 或相邻上下文。
- chunk 参数通过评测集调参，而不是只凭经验固定。

本地改进：

- 新增 `data/derived/datasets/section_catalog.jsonl`，由 `data/corpus/parsed/*.json` 生成 section 级父节点，字段包含 `section_id`、`doc_id`、`heading`、`source_ref`、`child_chunk_ids`、`content_chars`。
- 扩展 chunk 记录或发布目录，增加 `parent_section_id`、`chunk_order`、`previous_chunk_id`、`next_chunk_id`。
- 修改 `src/bgpkb/service/retrieval_framework.py` 的 context pack 逻辑：召回 chunk 后，可按配置附带父 section 标题、前后 chunk 或父 section 摘要。
- 新增 `src/bgpkb/pipeline/evaluate_chunking.py`，用 `data/derived/datasets/rag_answer_eval_questions.jsonl` 统计每个问题命中的 chunk 数、来源覆盖、父 section 覆盖和引用完整度。

暂不做：

- 暂不默认启用 embedding 语义切分。
- 暂不引入大 overlap；是否需要 overlap 由评测结果决定。

### 3.3 知识分类

当前基线：

- `metadata/config/topic_taxonomy.yaml` 已定义主题体系。
- `build_chunks.py` 通过关键词规则生成 `topics`。

工业界成熟做法：

- taxonomy 由受控词表、同义词、父子关系、反例和维护人共同组成。
- 自动分类输出置信度，低置信进入人工复核。
- 分类质量通过覆盖率、误分类样本、零结果查询和人工修正率持续运营。

本地改进：

- 新增 `metadata/config/topic_synonyms.yaml`，为每个 topic 配置同义词、缩写、反例词和优先级。
- 新增 `src/bgpkb/pipeline/build_topic_classification_candidates.py`，对 chunk 生成候选 topic、匹配理由、置信度和命中词。
- 输出 `data/derived/datasets/topic_classification_candidates.jsonl`、`data/derived/datasets/topic_review_queue.jsonl` 和 `data/generated/reports/knowledge/topic_classification_report.md`。
- 修改 `build_chunks.py`：先继续写入保守 topic；低置信或多主题冲突不自动覆盖，而是进入复核队列。
- 在 `quality_check.py` 中增加 topic 检查：未知 topic、空 topic、topic 不在 taxonomy、候选 topic 与现有 topic 冲突。

暂不做：

- 暂不让 LLM 直接改写 chunk topic。
- 暂不训练专用分类模型；等复核样本积累后再评估。

### 3.4 知识结构化

当前基线：

- `data/knowledge/entities/*.jsonl` 已有 112 个实体，9 种实体类型。
- `data/knowledge/relationships/relationships.jsonl` 已有 106 条关系。
- `extract_entities.py` 和 `build_relationships.py` 当前仍偏占位，结构化主要依赖人工种子。

工业界成熟做法：

- 主库和候选库分离。
- 自动抽取只生成候选，不直接进入可信实体。
- 候选有来源、chunk、字段级证据、置信度、冲突解释和人工复核状态。
- 实体合并、别名归一、关系抽取和字段补全都要有审计记录。

本地改进：

- 新增 `data/derived/datasets/entity_candidates.jsonl`、`data/derived/datasets/relationship_candidates.jsonl`、`data/derived/datasets/field_enrichment_candidates.jsonl`。
- 将 `src/bgpkb/pipeline/extract_entities.py` 改为候选生成脚本，只读取 chunks 和已有 entities，不写主实体。
- 将 `src/bgpkb/pipeline/build_relationships.py` 改为候选关系生成或关系校验脚本，不直接覆盖 `data/knowledge/relationships/relationships.jsonl`。
- 新增 `src/bgpkb/pipeline/build_candidate_review_packets.py`，把候选实体、候选关系、来源 chunk、匹配字段和冲突项合并为人工复核包。
- 复用现有人工复核模式：只有人工在 `data/review_inputs/` 显式批准后，才允许通过专门脚本合并到主实体或关系文件。

暂不做：

- 暂不自动批准 PaperMethod、Case 角色、影响范围和证据强度。
- 暂不把 Neo4j/RDF 作为主存储；当前 SQLite + JSONL 足够支撑本规模。

### 3.5 知识追溯

交付状态补充：阶段五已经交付确定性 JSON-LD、SKOS、PROV-O 与 Turtle 出口，覆盖下述 PROV/JSON-LD 样例目标。后续只需补充 run manifest 与 artifact lineage，不重复建设标准化出口。

当前基线：

- 实体有 `source_refs`。
- chunk 有 `source_ref`。
- `build_entity_source_evidence.py` 已生成实体到来源和 chunk 样例的证据索引。
- `build_artifact_manifest.py` 已生成文件级 hash、producer 和制品清单。
- `semantic_identity.yaml` 和 `jsonld_context.json` 已有轻量语义标识基础。

工业界成熟做法：

- lineage 不只存在于报告中，还以机器可读事件记录每次运行的输入、输出、脚本、参数、版本和状态。
- 事实级 provenance 能从实体追到 chunk，再追到原始来源和生成步骤。
- 发布物有版本、hash、生成时间和输入快照。

本地改进：

- 新增 `data/derived/datasets/pipeline_runs.jsonl`，每次 `run_pipeline.py` 记录 run_id、开始时间、结束时间、步骤、返回码、输入摘要、输出摘要。
- 新增 `data/derived/datasets/artifact_lineage.jsonl`，记录每个制品的 producer、inputs、outputs、sha256 和上游依赖。
- 扩展 `build_artifact_manifest.py`，把 producer 从字符串升级为可追踪依赖记录。
- 新增 `src/bgpkb/pipeline/export_prov_jsonld.py`，从 entity、source、chunk、relationship、evidence 和 artifact lineage 生成轻量 PROV/JSON-LD 样例。
- 在 `data/published/manifest.json` 中增加 release_id、source_snapshot_hash、entity_snapshot_hash、chunk_snapshot_hash。

暂不做：

- 暂不建设独立 lineage server。
- 暂不全量 RDF 三元组化，先输出可审计 JSON-LD 样例。

### 3.6 知识更新

当前基线：

- `run_pipeline.py` 全量重跑确定性流水线。
- 人工复核采用 template、validation、audit、dry-run、`--write` 的闸门式流程。
- 当前更偏全量发布，不是增量构建。

工业界成熟做法：

- Write-Audit-Publish。
- CI 自动跑结构检查和关键回归测试。
- 文件变更能定位受影响下游产物。
- 知识有生命周期、有效期、废弃和过期提醒。

本地改进：

- 新增 `metadata/config/pipeline_dependencies.yaml`，描述每个脚本的输入、输出和下游依赖。
- 新增 `src/bgpkb/pipeline/plan_incremental_run.py`，根据 git diff 或文件 mtime 输出建议重跑步骤，不直接执行。
- 新增 `src/bgpkb/pipeline/run_incremental_pipeline.py`，在确认依赖规则稳定后执行受影响步骤。
- 新增 `src/bgpkb/pipeline/check_release_readiness.py`，作为 CI 入口，运行非联网、非 LLM、非写主实体的检查命令。
- 扩展生命周期治理：对 `valid_until`、`deprecated`、`archived` 和替代实体关系生成行动队列。
- 新增 `data/generated/reports/publishing/release_notes/` 或 `data/published/release_notes.md`，记录每次发布的实体变化、来源变化、chunk 变化和质量状态；生成报告先登记到 `metadata/config/report_policy.yaml`。

暂不做：

- 暂不让 CI 自动应用人工复核决策。
- 暂不默认联网更新来源；外部采集仍应显式运行并审查。

## 4. 推荐实施顺序

### 第一批：低风险治理增强

1. 语料 profiling（已完成）。
2. topic synonym 配置。
3. section catalog。
4. pipeline dependency 配置。

原因：这些改动主要新增派生数据和报告，不改变主实体、主关系和发布语义，风险低。

### 第二批：检索和分类质量提升

1. topic classification candidates。
2. chunk 层级回扩。
3. chunking/retrieval 评测脚本。
4. context pack 增加父 section 和相邻 chunk 配置。

原因：这批直接影响 RAG 答案质量，但可以通过现有评测集验证。

### 第三批：结构化候选层

1. entity candidates。
2. relationship candidates。
3. candidate review packets。
4. 候选合并 dry-run。

原因：这是提升工业成熟度的关键，但必须严格保持“候选不自动入主库”。

### 第四批：标准化追溯和增量发布

1. pipeline_runs。
2. artifact_lineage。
3. PROV/JSON-LD 样例出口。
4. incremental run planner。
5. release notes。

原因：这批让项目从“本地可复跑”升级为“可审计、可发布、可持续维护”。

## 5. 验收指标

| 能力 | 验收指标 |
| --- | --- |
| 清洗 | `corpus_profile_report.md` 能列出异常语料；质量报告能检查关键清洗问题。 |
| 拆分 | 每个 chunk 可追到父 section；context pack 可配置回扩策略。 |
| 分类 | topic 候选有置信度；未知 topic 和低置信 topic 有复核队列。 |
| 结构化 | 自动脚本只生成候选；主实体和主关系只能由人工审计后显式合并。 |
| 追溯 | 每个发布制品能追到生成脚本、输入、输出和 hash。 |
| 更新 | 能根据变更生成增量重跑计划；全量流水线仍可作为最终发布兜底。 |

## 6. 风险控制

- 不让 LLM 或候选脚本直接修改 `data/knowledge/entities/*.jsonl`、`data/knowledge/relationships/*.jsonl`。
- 不把低置信分类写入正式 chunk，只进入候选或复核队列。
- 不默认联网下载或覆盖 raw 来源。
- 不把增量流水线作为唯一发布路径；全量流水线仍是最终一致性校验。
- 不在没有评测集的情况下调大 chunk overlap 或切换语义切分。

## 7. 下一步最小落地包

以下最小闭环中的语料画像部分已于 2026-06-30 完成；下一项转向 topic 分类增强：

1. 新增 `src/bgpkb/pipeline/profile_cleaned_corpus.py`。
2. 新增 `data/generated/reports/corpus/corpus_profile_report.md` 和 `data/derived/datasets/corpus_profile.jsonl`。
3. 新增 `metadata/config/topic_synonyms.yaml`。
4. 新增 `src/bgpkb/pipeline/build_topic_classification_candidates.py`。
5. 新增 `data/derived/datasets/topic_classification_candidates.jsonl` 和 `data/generated/reports/knowledge/topic_classification_report.md`。
6. 更新 `quality_check.py`，只检查新增数据集的结构和 topic 是否在 taxonomy 中。

这个包不会改变主知识库事实，但会让“清洗质量”和“分类质量”先变成可度量、可复核、可持续改进的本地能力。
