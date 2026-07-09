---
title: "Markdown 文档 CRUD 规则 v1"
document_type: "文档规则"
purpose: "定义后续新增、读取、更新、删除或归档 Markdown 文档时必须遵守的元数据、目录归属、索引维护和自动校验规则。"
scope: "当前仓库内所有 Markdown 文档"
status: "现行规则"
last_reviewed: "2026-06-29"
---
# Markdown 文档 CRUD 规则 v1

## 文档保留原则

`docs/` 只长期保留治理规范、现行验收依据、仍有效的路线图和稳定项目说明。以下内容完成使命后应删除，由 Git 历史承担追溯：

- 已完成的一次性实施计划和任务拆解。
- 已被正式规范或现行阶段文档覆盖的设计稿、调研草案。
- 基线、路径或阶段结论已经失效的路线图。
- 与代码、配置或生成报告重复，且没有独立决策价值的说明。

删除文档时必须同步更新最近的索引和所有显式引用；仍被验收配置、测试或运行流程引用的文档不得直接删除。

## 1. 规则目标

本规则用于约束后续 Markdown 文档的 CRUD 操作，使文档可被人阅读、可被索引归并、可被脚本自动校验。

本规则只管理 Markdown 文档，不改变数据流水线、不替代 JSONL、CSV、SQLite、YAML Schema 或 Python 脚本。

## 2. 适用范围

| 范围 | 是否适用 | 说明 |
| --- | --- | --- |
| `context.md` | 是 | 项目总上下文。 |
| `bgp_knowledge_base/**/*.md` | 是 | 知识库内所有 Markdown 文档。 |
| `data/sources/raw/` 原始资料 | 仅 Markdown 适用 | 非 Markdown 原始文件不受本规则约束。 |
| `data/corpus/parsed/`、`data/corpus/chunks/`、`data/knowledge/entities/`、`data/knowledge/relationships/`、`data/derived/datasets/` | 否 | 这些目录以机器数据为主，不按 Markdown CRUD 管理。 |
| 由脚本生成的报告 | 是 | 可补充 Frontmatter 和索引，但正文统计以生成脚本为准。 |

## 3. 文档分类

每个 Markdown 必须归入一个明确的 `document_type`。新增文档优先复用现有类型，确实需要新类型时，先更新本规则。

| 类型 | 典型目录 | 用途 |
| --- | --- | --- |
| `目录入口说明` | `bgp_knowledge_base/README.md` | 根入口。 |
| `目录使用说明` | `bgp_knowledge_base/目录介绍.md` | 面向人工浏览的目录说明。 |
| `归并索引` | `docs/README.md`、`data/reports/README.md`、`data/corpus/cleaned/README.md` | 将同类文档收束为可导航入口。 |
| `阶段方案矩阵` | `docs/roadmap/*matrix*.md` | 对比每个阶段的较优解、简易版、推荐路径和取舍。 |
| `规划与治理文档` | `docs/roadmap/*.md`、`docs/governance/*.md` | 路线规划、数据治理、生命周期和语义质量设计。 |
| `阶段设计文档` | `docs/stages/*.md` | 单个阶段的详细开发方案、标准出口方案或实施边界。 |
| `技术调研文档` | `docs/stages/*research*.md` | 技术路线、PoC、方案比选和风险边界。 |
| `文档规则` | `docs/rules/*rules*.md` | 文档维护与 CRUD 规则。 |
| `项目上下文` | `context.md` | 项目方案、范围和背景上下文。 |
| `项目报告` | `data/reports/{gates,reference,actions}/*_report.md`、`data/generated/reports/**/*.md` | 门禁、参考、行动入口和可再生成明细报告。 |
| `人工复核清单` | `data/generated/reports/review/human_review_guides/*.md` | 人工复核分组清单。 |
| `人工复核会话指南` | `data/generated/reports/review/human_review_session_guides/*.md` | 单个 session 的复核材料。 |
| `案例观察值核验指南` | `data/generated/reports/review/case_observation_guides/*.md` | 单个案例的观察值核验材料。 |
| `清洗后的标准资料` | `data/corpus/cleaned/standards/*.md` | RFC 与标准语料。 |
| `清洗后的数据源文档` | `data/corpus/cleaned/data_docs/*.md` | 数据源和 API 文档语料。 |
| `清洗后的研究论文` | `data/corpus/cleaned/papers/*.md` | 论文语料。 |
| `清洗后的案例资料` | `data/corpus/cleaned/cases/*.md` | 案例报告语料。 |
| `清洗上下文摘要` | `data/corpus/cleaned/notes/*.md` | 上下文摘要语料。 |
| `发布包入口说明` | `data/published/README.md` | 发布包入口和查询说明。 |
| `人工复核输入模板说明` | `data/review_inputs/**/*.md` | 人工复核输入模板说明。 |

## 4. Frontmatter 规则

### 4.1 必填字段

每个 Markdown 第一行必须是 YAML Frontmatter，并包含以下字段：

```yaml
---
title: "中文或原文标题"
document_type: "文档类型"
purpose: "一句话说明文档作用"
scope: "适用范围"
status: "现行规则"
last_reviewed: "YYYY-MM-DD"
---
```

字段含义：

| 字段 | 规则 | 可自动校验 |
| --- | --- | --- |
| `title` | 必填，不能为空，应与文档 H1 或实际用途一致。 | 是 |
| `document_type` | 必填，优先使用第 3 节列出的类型。 | 是 |
| `purpose` | 必填，用一句话说明文档存在的原因。 | 是 |
| `scope` | 必填，说明文档适用目录、流程或对象。 | 是 |
| `status` | 必填，使用受控状态。 | 是 |
| `last_reviewed` | 必填，格式为 `YYYY-MM-DD`。 | 是 |

### 4.2 状态枚举

`status` 必须从以下状态中选择：

| 状态 | 含义 |
| --- | --- |
| `现行入口` | 当前有效的主入口。 |
| `现行索引` | 当前有效的归并索引。 |
| `现行规则` | 当前有效的规则文档。 |
| `现行参考` | 当前有效的参考文档。 |
| `现行报告` | 当前有效的报告。 |
| `现行指南` | 当前有效的指南入口。 |
| `清洗语料` | 当前有效的清洗文本语料。 |
| `发布入口` | 当前有效的发布包入口。 |
| `待人工复核` | 等待人工确认的复核材料。 |
| `待人工核验` | 等待人工核验证据或观察值的材料。 |
| `现行模板说明` | 当前有效的模板说明。 |
| `已归档` | 已被替代或不再作为现行入口使用。 |

### 4.3 可选字段

可选字段只在需要时添加：

| 字段 | 使用场景 |
| --- | --- |
| `tags` | 需要主题检索时使用，值为字符串数组。 |
| `owner` | 有明确维护人时使用。 |
| `generated_by` | 文档由脚本生成时使用。 |
| `source_path` | 文档从某个原始或解析文件派生时使用。 |
| `replaces` | 新文档替代旧文档时使用。 |
| `replaced_by` | 旧文档被新文档替代时使用。 |
| `archived_at` | 文档归档时使用。 |

## 5. 正文结构规则

| 规则编号 | 规则 | 可自动校验 |
| --- | --- | --- |
| `BODY-001` | Frontmatter 后必须有正文。 | 是 |
| `BODY-002` | 除 `context.md` 等历史上下文外，正文第一段应以一级标题 `# ` 开头。 | 是 |
| `BODY-003` | 一级标题应与 `title` 含义一致，不要求逐字相同。 | 人工判断 |
| `BODY-004` | 新增规则、索引、规划文档必须使用中文正文。 | 人工判断 |
| `BODY-005` | 不在报告或语料正文中写入未经人工确认的结论。 | 人工判断 |

## 6. 路径与命名规则

### 6.1 路径归属

| 文档用途 | 放置位置 |
| --- | --- |
| 项目入口 | `bgp_knowledge_base/README.md` |
| 目录导航 | `bgp_knowledge_base/目录介绍.md` |
| 文档归并入口 | `bgp_knowledge_base/docs/README.md` |
| 路线图与阶段取舍 | `bgp_knowledge_base/docs/roadmap/` |
| 治理设计 | `bgp_knowledge_base/docs/governance/` |
| 阶段详细方案 | `bgp_knowledge_base/docs/stages/` |
| 文档规则 | `bgp_knowledge_base/docs/rules/` |
| 报告入口 | `bgp_knowledge_base/data/reports/` |
| 生成报告与子指南 | `bgp_knowledge_base/data/generated/reports/` |
| 清洗语料 | `bgp_knowledge_base/cleaned/<source_group>/` |
| 发布包入口 | `bgp_knowledge_base/published/README.md` |
| 人工复核输入说明 | `bgp_knowledge_base/review_inputs/**/README.md` |

### 6.2 文件命名

| 规则编号 | 规则 | 可自动校验 |
| --- | --- | --- |
| `PATH-001` | 新增英文文件名使用小写 snake_case。 | 是 |
| `PATH-002` | 版本化规则或治理文档使用 `_v1`、`_v2` 等后缀。 | 是 |
| `PATH-003` | 报告文件优先使用 `*_report.md`。 | 是 |
| `PATH-004` | 目录入口文件使用 `README.md`。 | 是 |
| `PATH-005` | 中文文件名仅保留已有入口或确有必要的人工导航文档。 | 人工判断 |

## 7. 索引归并规则

每次 CRUD 后必须维护最近的归并入口。

| 文档位置 | 必须维护的索引 |
| --- | --- |
| `docs/**/*.md` | `docs/README.md` |
| `data/reports/{gates,reference,actions}/*.md` | `data/reports/README.md` |
| `data/generated/reports/**/*.md` | 最近的 generated 分区 README 或 `data/reports/README.md` |
| `data/generated/reports/review/case_observation_guides/*.md` | `data/generated/reports/review/case_observation_guides/README.md`，必要时同步 `data/reports/README.md` |
| `data/generated/reports/review/human_review_guides/*.md` | `data/generated/reports/review/human_review_guides/README.md`，必要时同步 `data/reports/README.md` |
| `data/generated/reports/review/human_review_session_guides/*.md` | `data/generated/reports/review/human_review_session_guides/README.md`，必要时同步 `data/reports/README.md` |
| `data/corpus/cleaned/**/*.md` | `data/corpus/cleaned/README.md` |
| `data/published/README.md` | `README.md` 与 `docs/README.md` 的入口关系 |
| `data/review_inputs/**/*.md` | 对应目录 `README.md`，必要时同步 `README.md` 的人工复核说明 |

归并索引不必须逐条列出所有语料文件，但必须至少按分组覆盖，并说明每组用途。

## 8. CRUD 操作规则

### 8.1 Create 新增

新增 Markdown 时必须完成：

1. 确定 `document_type`、路径和文件名。
2. 写入完整 Frontmatter。
3. 正文第一段写清文档用途或标题。
4. 更新最近的归并索引。
5. 若新增入口级文档，同时更新上一级入口。
6. 校验本地相对链接。

自动校验规则：`FM-*`、`PATH-*`、`BODY-001`、`BODY-002`、`LINK-001`、`INDEX-001`。

### 8.2 Read 读取

读取 Markdown 时必须遵守：

1. 先看 Frontmatter 的 `document_type`、`purpose`、`scope`。
2. 再看最近的归并索引，确认该文档在整体结构中的位置。
3. 对报告，优先把报告视为当前快照，不把它当作永久事实来源。
4. 对清洗语料，优先把它视为证据材料，不把它当作人工结论。

自动校验规则：无强制写入动作，但读取工具可以利用 Frontmatter 过滤文档。

### 8.3 Update 更新

更新 Markdown 时必须完成：

1. 不改变已有路径，除非明确执行归档或迁移。
2. 若修改标题、用途、类型、路径或维护状态，必须同步更新相关索引。
3. 若修改正文事实或规则，更新 `last_reviewed`。
4. 若只是修正错别字、标点或链接，可更新 `last_reviewed`，但不强制。
5. 报告正文若由脚本生成，原则上不手工改统计结果；应改生成逻辑或重跑脚本。

自动校验规则：`FM-*`、`LINK-001`、`INDEX-001`。

### 8.4 Delete 删除与归档

默认不直接删除 Markdown。确需移除时，优先归档。

归档规则：

1. 将 `status` 改为 `已归档`。
2. 增加 `archived_at`。
3. 如有替代文档，增加 `replaced_by`。
4. 从现行索引中移到“已归档”或“历史参考”分组。
5. 不删除清洗语料、来源证据、人工复核材料，除非确认它们可由流水线重新生成且路径引用已经处理。

自动校验规则：`ARCHIVE-001`、`ARCHIVE-002`、`LINK-001`。

## 9. 自动校验规则清单

后续可用脚本按以下规则实现校验。

| 规则编号 | 内容 | 失败条件 |
| --- | --- | --- |
| `FM-001` | 文件必须以 Frontmatter 开头。 | 第一行不是 `---`。 |
| `FM-002` | Frontmatter 必须闭合。 | 找不到第二个 `---`。 |
| `FM-003` | 必填字段完整。 | 缺少 `title`、`document_type`、`purpose`、`scope`、`status`、`last_reviewed`。 |
| `FM-004` | `last_reviewed` 必须是 `YYYY-MM-DD`。 | 日期格式不匹配。 |
| `FM-005` | `document_type` 必须在受控类型中。 | 使用未知类型且未更新本规则。 |
| `FM-006` | `status` 必须在受控状态中。 | 使用未知状态。 |
| `BODY-001` | Frontmatter 后正文不能为空。 | 去除空白后无正文。 |
| `BODY-002` | 正文应以 H1 开头。 | 非豁免文件正文第一段不是 `# `。 |
| `PATH-001` | 新增英文文件名使用小写 snake_case。 | 文件名含大写、空格或非约定分隔符。 |
| `PATH-002` | 版本化规则或治理文档有版本后缀。 | 规则或治理文档缺少 `_vN`。 |
| `PATH-003` | 报告文件使用 `*_report.md`，且先登记到 `metadata/config/report_policy.yaml`。 | 未登记报告、旧顶层报告或命名不符合策略。 |
| `LINK-001` | Markdown 本地相对链接必须可解析。 | 链接目标不存在。 |
| `INDEX-001` | 新增或改名文档必须进入最近归并索引。 | 无索引覆盖记录或分组说明。 |
| `ARCHIVE-001` | `已归档` 文档必须有 `archived_at`。 | 缺少归档日期。 |
| `ARCHIVE-002` | 有替代关系时必须双向说明。 | 新旧文档只单边记录替代关系。 |

## 10. 当前豁免

| 豁免项 | 原因 |
| --- | --- |
| `context.md` 正文不强制第一段为 H1 | 该文件保留原始项目说明开头，历史上下文价值高于格式统一。 |
| `data/corpus/cleaned/**/*.md` 的正文标题不强制与 `title` 完全一致 | 清洗文本可能保留原始网页、PDF 或 RFC 解析噪声。 |
| 语料文件不要求全部逐条列入总索引 | `data/corpus/cleaned/README.md` 以分组归并为主，避免索引过度膨胀。 |
| 脚本生成报告的正文统计不要求人工维护 | 报告事实应由生成脚本和流水线维护。 |

## 11. 最小校验命令草案

在尚未新增正式脚本前，可用以下检查思路验证规则：

```text
1. 扫描所有 Markdown。
2. 检查 Frontmatter 开头、闭合和必填字段。
3. 校验 document_type 与 status 是否在受控列表中。
4. 校验 last_reviewed 日期格式。
5. 校验正文是否为空。
6. 校验索引文档中的本地相对链接是否存在。
7. 对已归档文档校验 archived_at 和替代关系。
```

正式脚本若后续添加，建议命名为 `src/bgpkb/pipeline/check_markdown_documents.py`，输出报告可写入 `data/generated/reports/knowledge/document_rules_report.md`，并先登记到 `metadata/config/report_policy.yaml`。在添加脚本前，本规则文档就是 Markdown CRUD 的准入标准。
