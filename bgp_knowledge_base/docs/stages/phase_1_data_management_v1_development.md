---
title: "阶段一：数据管理体系 v1 详细开发文档"
document_type: "规划与治理文档"
purpose: "说明阶段一：数据管理体系 v1 详细开发文档的设计目标、治理边界和执行约束，供后续维护与阶段复核参考。"
scope: "知识库规划、治理与开发说明"
status: "现行参考"
last_reviewed: "2026-06-19"
---
# 阶段一：数据管理体系 v1 详细开发文档

## 1. 阶段目标

阶段一目标是把 DAMA-DMBOK 风格的数据管理目录落成 BGP KB 项目内的治理框架。

本阶段不改变现有数据生产流水线，不迁移目录，不修改实体内容，不改变 `published/` 的发布格式。它只新增一层可读、可审计、可自动生成的“数据管理体系说明”和“数据管理能力报告”。

完成后，项目应能回答以下问题：

- 当前有哪些数据资产？
- 每类资产存在哪里？
- 每类资产由哪个脚本生成？
- 每类资产受哪个 schema 或规则约束？
- 每类资产是否进入发布包？
- 当前已有多少治理能力，缺哪些能力？
- 后续新增数据资产应该如何登记？

## 2. 阶段范围

### 2.1 包含范围

- 建立数据管理体系说明文档。
- 建立机器可读的数据管理能力配置。
- 编写数据管理报告生成脚本。
- 生成数据管理报告。
- 把报告纳入 README 中的文档入口。

### 2.2 不包含范围

- 不修复当前流水线中的既有失败点。
- 不改变 `entities/`、`relationships/`、`chunks/`、`datasets/` 的现有数据结构。
- 不新增生命周期字段。
- 不新增语义质量规则。
- 不生成 embedding 或向量索引。
- 不做 JSON-LD/RDF/STIX/MISP 导出。
- 不调用 LLM。

## 3. 交付物

| 类型 | 路径 | 说明 |
| --- | --- | --- |
| 治理文档 | `docs/governance/data_management_v1.md` | 人读版数据管理体系说明 |
| 能力配置 | `config/data_management_capabilities.yaml` | 机器可读的数据资产和治理能力清单 |
| 生成脚本 | `scripts/build_data_management_report.py` | 从配置和现有文件生成报告 |
| 数据报告 | `reports/data_management_report.md` | 当前数据管理能力盘点报告 |
| 测试 | `tests/test_data_management_report.py` | 验证配置和报告生成逻辑 |
| README 更新 | `README.md` | 增加数据管理体系文档入口 |

## 4. 文件职责设计

### 4.1 `docs/governance/data_management_v1.md`

职责：

- 定义 BGP KB 数据管理体系 v1。
- 解释数据资产清单、数据模型标准、元数据与溯源、质量治理、生命周期、服务化访问、标准化出口七大模块。
- 标明每个模块当前项目已有能力、缺口和后续阶段。

建议结构：

```markdown
# BGP KB 数据管理体系 v1

## 1. 设计目标
## 2. 数据资产清单
## 3. 数据模型标准
## 4. 元数据与溯源
## 5. 质量治理
## 6. 生命周期
## 7. 服务化访问
## 8. 标准化出口
## 9. 当前成熟度
## 10. 后续演进
```

### 4.2 `config/data_management_capabilities.yaml`

职责：

- 用机器可读方式登记数据资产和治理能力。
- 作为报告生成脚本的输入。
- 避免报告中硬编码大量资产信息。

建议顶层结构：

```yaml
version: data_management_v1
generated_policy:
  report_path: reports/data_management_report.md
asset_groups:
  - id: entities
    name: 实体
    status: achieved
    paths:
      - entities/*.jsonl
      - published/entity_catalog.jsonl
    schemas:
      - schemas/concept.schema.json
      - schemas/case.schema.json
    generated_by:
      - scripts/extract_entities.py
      - scripts/build_published_knowledge_base.py
    quality_checks:
      - JSON schema check
      - duplicate entity_id check
      - source reference check
capability_groups:
  - id: data_asset_inventory
    name: 数据资产清单
    status: achieved
    evidence:
      - inventory/sources.csv
      - reports/artifact_manifest_report.md
```

状态枚举：

```text
achieved
partial
planned
not_started
deferred
```

### 4.3 `scripts/build_data_management_report.py`

职责：

- 读取 `config/data_management_capabilities.yaml`。
- 检查配置中声明的路径是否存在。
- 统计 asset group 和 capability group 的状态分布。
- 输出 `reports/data_management_report.md`。

脚本边界：

- 只读现有数据文件。
- 只写 `reports/data_management_report.md`。
- 不调用网络。
- 不调用 LLM。
- 不修改实体、chunk、关系或发布包。

报告内容应包括：

- 摘要。
- 数据资产清单。
- 数据模型标准覆盖。
- 元数据与溯源覆盖。
- 质量治理能力。
- 生命周期现状。
- 服务化访问现状。
- 标准化出口现状。
- 缺口与下一步建议。

### 4.4 `tests/test_data_management_report.py`

职责：

- 验证 YAML 配置可解析。
- 验证所有 asset group 都有 id、name、status、paths。
- 验证 status 属于允许枚举。
- 验证报告生成脚本可运行。
- 验证生成报告包含七大模块标题。

## 5. 数据资产登记范围

阶段一至少登记以下数据资产：

| 资产组 | 当前路径 | 发布出口 |
| --- | --- | --- |
| 实体 | `entities/*.jsonl` | `published/entity_catalog.jsonl`、SQLite `entities` |
| 关系 | `relationships/relationships.jsonl` | `published/relationship_adjacency.json`、SQLite `relationships` |
| source | `inventory/sources.csv` | `published/source_catalog.jsonl`、SQLite `sources` |
| chunk | `chunks/*.jsonl` | `published/chunk_catalog.jsonl`、SQLite `chunks` |
| 术语表 | `datasets/glossary.*` | SQLite `glossary` |
| 证据模板 | `entities/evidence_templates.jsonl` | `published/entity_catalog.jsonl`、SQLite `entities` |
| 案例 | `entities/cases.jsonl`、`datasets/case_observations.*` | SQLite `entities`、`case_observations` |
| 人工复核工作簿 | `datasets/human_review_workbook.*` | SQLite `human_review_workbook` |
| 行动队列 | `datasets/next_action_queue.*` | SQLite `next_actions` |
| 发布包 | `published/` | 文件化发布入口 |
| 服务化 API | `service/` | FastAPI/OpenAPI |

## 6. 能力模块登记范围

阶段一至少登记以下能力模块：

### 6.1 数据资产清单

包括：

- 实体。
- 关系。
- source。
- chunk。
- 术语表。
- 证据模板。
- 案例。

当前状态：已基本完成。

### 6.2 数据模型标准

包括：

- entity schema。
- relation schema。
- taxonomy。
- required fields。
- naming convention。

当前状态：部分完成。

已完成：

- JSON Schema。
- topic taxonomy。
- entity types。

缺口：

- 命名规范尚未形成集中说明。
- 跨实体类型约束尚未机器化。
- 必填字段规则分散在 schema 和脚本中。

### 6.3 元数据与溯源

包括：

- source_ref。
- chunk_id。
- raw file。
- extracted_at。
- reviewed_by。
- approved_at。

当前状态：部分完成。

已完成：

- source_ref。
- chunk_id。
- raw/parsed/cleaned/chunk/entity 链路。

缺口：

- extracted_at 不统一。
- reviewed_by/approved_at 未进入实体统一字段。

### 6.4 质量治理

包括：

- JSON schema check。
- duplicate check。
- orphan reference check。
- semantic consistency check。
- validity period check。

当前状态：结构质量已完成，语义质量待建设。

### 6.5 生命周期

包括：

- draft。
- candidate。
- reviewed。
- approved。
- deprecated。
- archived。

当前状态：待建设。

当前项目主要使用 `pending/approved`，阶段二再扩展生命周期模型。

### 6.6 服务化访问

包括：

- SQLite。
- FTS。
- REST API。
- vector index。
- RAG interface。

当前状态：部分完成。

已完成：

- SQLite。
- FTS。
- REST API。
- 简单 HTML 浏览页。

缺口：

- vector index。
- RAG interface。

### 6.7 标准化出口

包括：

- JSON。
- JSON-LD。
- RDF。
- CSV。
- STIX/MISP。

当前状态：部分完成。

已完成：

- JSON/JSONL。
- CSV。
- SQLite。

缺口：

- JSON-LD。
- RDF。
- STIX/MISP，仅在需要时建设。

## 7. 开发步骤

### Task 1：创建数据管理体系说明文档

文件：

- 新建：`docs/governance/data_management_v1.md`

步骤：

1. 写入七大模块说明。
2. 每个模块包含：目标、当前状态、项目证据、缺口、下一阶段。
3. 确认文档全部使用中文。

验收：

- 文档包含七大模块。
- 文档明确说明“不重排目录、不替代流水线”。

### Task 2：创建机器可读能力配置

文件：

- 新建：`config/data_management_capabilities.yaml`

步骤：

1. 定义 `version`。
2. 定义 `allowed_statuses`。
3. 登记 asset_groups。
4. 登记 capability_groups。
5. 每条记录包含 id、name、status、description、evidence。

验收：

- YAML 可解析。
- 所有 status 属于允许枚举。
- 每个资产组至少包含一个 evidence 路径。

### Task 3：编写报告生成脚本

文件：

- 新建：`scripts/build_data_management_report.py`

步骤：

1. 读取 YAML 配置。
2. 检查 evidence 路径是否存在。
3. 汇总 asset_groups 和 capability_groups。
4. 写入 Markdown 报告。
5. 输出写入路径。

验收：

- 运行 `python3 scripts/build_data_management_report.py` 成功。
- 生成 `reports/data_management_report.md`。
- 报告包含状态统计和缺口列表。

### Task 4：编写测试

文件：

- 新建：`tests/test_data_management_report.py`

步骤：

1. 测试 YAML 能解析。
2. 测试状态枚举合法。
3. 测试核心资产组存在。
4. 测试报告脚本可执行。
5. 测试报告包含七大模块标题。

验收：

- 运行 `pytest tests/test_data_management_report.py -v` 通过。

### Task 5：更新 README

文件：

- 修改：`README.md`

步骤：

1. 增加“数据管理体系”章节。
2. 链接 `docs/governance/data_management_v1.md`。
3. 链接 `reports/data_management_report.md`。
4. 增加报告生成命令。

验收：

- README 可说明如何查看和生成数据管理报告。

## 8. 测试计划

### 单项测试

```bash
cd bgp_knowledge_base
pytest tests/test_data_management_report.py -v
```

预期：

```text
全部通过
```

### 报告生成测试

```bash
cd bgp_knowledge_base
python3 scripts/build_data_management_report.py
```

预期：

```text
Wrote reports/data_management_report.md
```

### 服务回归测试

```bash
cd /Users/botongwu/Desktop/DB
python3 -m pytest bgp_knowledge_base/tests -v
```

预期：

```text
现有服务测试继续通过
```

## 9. 完成标准

阶段一完成标准：

- `docs/governance/data_management_v1.md` 存在，且完整描述七大模块。
- `config/data_management_capabilities.yaml` 存在，且可解析。
- `scripts/build_data_management_report.py` 能生成报告。
- `reports/data_management_report.md` 存在，且包含资产状态和能力状态。
- `tests/test_data_management_report.py` 通过。
- README 有入口说明。
- 未修改实体、关系、chunk、source、published 数据内容。

## 10. 后续衔接

阶段一完成后，进入阶段二：

> 生命周期与元数据治理。

阶段二应基于阶段一的资产清单，新增 `lifecycle_status` 和统一治理字段，而不是直接修改所有数据资产的业务字段。

阶段一的报告将作为阶段二的输入，用于判断哪些资产已经具备生命周期扩展条件，哪些资产需要先补 schema 或溯源字段。
