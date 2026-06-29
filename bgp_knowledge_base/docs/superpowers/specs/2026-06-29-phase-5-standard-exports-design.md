---
title: "阶段五标准化出口与模型辅助映射设计"
document_type: "实施设计"
purpose: "定义阶段五确定性标准化出口、模型映射候选、人工审核闸门和验收边界。"
scope: "JSON-LD、SKOS、PROV-O、RDF 样例、模型候选、人工审核与发布完整性"
status: "待用户审阅"
last_reviewed: "2026-06-29"
---
# 阶段五标准化出口与模型辅助映射设计

## 1. 背景与目标

阶段三点五已经交付 `bgpkb:` 命名空间、稳定 URI、JSON-LD `@context` 和语义 ID 映射，因此阶段五不再重复建设这些基础能力。阶段五的目标是把现有实体、来源、关系和证据链导出为可交换、可验证、可审计的标准化发布物，并用模型辅助发现难以机械映射的语义候选。

阶段五采用“确定性出口为主、模型只生成候选、人工批准后生效”的结构。模型不得直接改写主实体、主关系、审核状态或最终发布物。

## 2. 方案选择

### 2.1 选定方案：三层混合架构

1. 确定性出口层负责 URI、类型、字段、SKOS、PROV-O 和 RDF 序列化。
2. 模型候选层负责为未知字段、关系和类型生成带证据的映射建议。
3. 人工审核层负责批准、拒绝或要求补充证据；只有通过审计的批准项才能进入确定性出口。

该方案兼顾语义覆盖率、可复跑性和审计要求，并复用项目现有的候选数据集、人工审核输入、审计报告和显式应用模式。

### 2.2 未采用方案

- 纯规则出口：稳定，但未知关系和跨词表映射只能长期留空。
- 模型直接生成 RDF：覆盖率高，但输出会随模型和提示词漂移，难以作为正式发布物。
- 引入重型本体或图数据库：超出阶段五的轻量出口范围，也会改变当前 JSONL、SQLite 主发布路径。

## 3. 总体架构

```text
实体、来源、关系、证据和语义 ID
        │
        ├── 确定性映射配置 ───────────────┐
        │                                  │
        └── 未映射字段与关系 ──> 模型候选 ─> 人工审核与审计
                                           │
                               仅批准结果 ──┘
                                           │
                                           v
                                确定性标准出口生成器
                                           │
                    ┌──────────────────────┼─────────────────────┐
                    v                      v                     v
             JSON-LD catalogs       PROV-O provenance      RDF/Turtle 样例
                    │                      │                     │
                    └──────────────────────┼─────────────────────┘
                                           v
                              完整性检查与中文验收报告
```

## 4. 组件设计

### 4.1 标准出口配置

新增 `metadata/config/standard_exports.yaml`，集中定义：

- 输出路径和发布版本；
- 本地实体类型到 `skos:`、`prov:`、`schema:` 和 `bgpkb:` 类型的确定性映射；
- 本地关系到标准谓词或 `bgpkb:` 自定义谓词的映射；
- 允许进入正式出口的复核状态；
- 模型 provider、置信度和候选安全边界；
- 不可映射字段的保留策略。

URI 继续由 `metadata/config/semantic_identity.yaml` 统一管理，阶段五不得另建第二套 URI 规则。

### 4.2 确定性标准出口生成器

新增 `src/bgpkb/pipeline/build_standard_exports.py`。该模块只读取现有发布物、关系、证据、配置和已审核映射，生成：

- `data/published/entity_catalog.jsonld`；
- `data/published/source_catalog.jsonld`；
- `data/published/provenance_map.jsonl`；
- `data/published/standard_exports/bgp_knowledge_sample.ttl`；
- `data/generated/reports/publishing/standardization_report.md`。

生成器必须排序输出、固定字段顺序并保留来源 URI，使同一输入能够生成字节级稳定结果。原始 JSONL、CSV、SQLite 和实体文件不得被修改。

### 4.3 模型辅助映射候选

新增 `src/bgpkb/pipeline/build_standard_mapping_candidates.py`。默认 `mock` provider 离线运行；`deepseek` provider 必须显式指定并从环境变量读取密钥。

每条候选至少包含：

- `candidate_id`、候选类型和本地字段或关系；
- 建议的标准类型或谓词；
- 输入实体、关系和 `source_refs`；
- 置信度、简短理由和证据摘要；
- provider、model、prompt_version 和生成时间；
- 固定状态 `pending_review`。

模型必须返回结构化 JSON。解析失败、未知前缀、缺少证据或越权建议只记录错误，不进入批准集合。模型原始响应不得包含密钥，也不得写入主数据。

### 4.4 人工审核与显式应用

新增人工输入 `data/review_inputs/standard_mapping_decisions.csv`，允许的决策为：

- `approved`：候选可以进入已批准映射集合；
- `rejected`：候选被拒绝；
- `needs_evidence`：证据不足，保持待处理；
- `unreviewed`：不产生任何效果。

新增 `src/bgpkb/pipeline/build_standard_mapping_decision_audit.py`，输出审核审计数据集和中文报告。新增 `src/bgpkb/pipeline/apply_standard_mapping_decisions.py`，默认只预览；仅显式 `--write` 时生成 `data/derived/datasets/approved_standard_mappings.jsonl`。它不得修改配置文件、实体或关系。

确定性出口生成器只消费内置确定性规则和 `approved_standard_mappings.jsonl`，不直接消费未经审核的模型响应。

### 4.5 Schema 与报告

新增候选、审核记录和 PROV 映射的 JSON Schema。标准化报告至少呈现：

- 各资源类型的导出数量；
- SKOS、PROV-O 和自定义词汇覆盖率；
- 未映射字段和关系；
- 模型候选数、批准数和阻塞数；
- URI、来源引用和重复三元组检查结果；
- 是否保持原发布包兼容。

## 5. 数据流与状态边界

```text
unknown
  -> pending_review（模型或 mock 候选）
      -> approved（人工批准并通过审计）
      -> rejected（人工拒绝）
      -> needs_evidence（证据不足）

只有 approved 才能通过显式 --write 进入 approved_standard_mappings.jsonl。
```

任何候选都不能改变实体的 `review_status`。实体本身若为 `pending`，可以在导出中保留治理信息，但不得被模型描述成已批准事实。

## 6. 错误处理

- 缺少模型密钥：返回 `skipped`，确定性出口继续运行。
- 模型请求失败：记录 provider、错误码和候选批次，不回退为编造候选。
- 非法 JSON 或未知词表：候选标记为 invalid，不进入审核输入。
- 来源引用无法解析：确定性出口失败并在报告中列出阻塞项。
- 重复 URI 或候选 ID：验收失败。
- 人工决策引用不存在的候选：审计失败，`--write` 禁止执行。
- RDF 样例无法通过内部语法和引用检查：阶段验收失败。

## 7. 测试与验收

实施遵循 TDD，先写失败测试，再实现最小逻辑。测试范围包括：

1. 类型、字段和关系的确定性映射；
2. JSON-LD catalog 的稳定 URI、SKOS 标签和来源引用；
3. PROV-O 链路从实体或 chunk 回到 source；
4. Turtle 样例的稳定排序和基本语法；
5. mock 模型候选的结构、证据与安全状态；
6. DeepSeek 响应的结构化解析和错误路径，不发真实网络请求；
7. 人工审核审计、dry-run、显式写入和非法决策阻塞；
8. 重复 URI、未知前缀、缺失来源和未审核候选不得污染正式出口；
9. 全量现有测试保持通过；
10. 阶段五验收 gate 检查交付物、命令、报告和剩余人工事项。

## 8. 实施顺序

1. 修正阶段五文档基线并建立配置、Schema 和失败测试。
2. 实现确定性 JSON-LD、PROV-O、RDF 样例和报告。
3. 实现 mock/DeepSeek 模型候选层。
4. 实现人工审核、审计和显式应用。
5. 接入报告策略、发布清单、阶段验收和项目索引。
6. 运行全量测试、阶段验收与敏感信息扫描。

## 9. 完成标准

- 阶段五交付物全部由命令可复跑生成；
- 正式出口不依赖模型在线可用；
- 模型只能产生待审核候选；
- 未经人工批准的候选不会进入正式标准出口；
- JSON-LD、PROV-O 和 RDF 样例保留稳定 URI 与来源链；
- 原有 JSONL、CSV、SQLite、RAG 和前端接口不发生破坏性变化；
- 全量测试和阶段五验收 gate 通过。
