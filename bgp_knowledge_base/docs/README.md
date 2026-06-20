---
title: "规划与治理文档归并索引"
document_type: "归并索引"
purpose: "归并项目级规划、治理、阶段方案和文档规则，说明阅读顺序、目录分组和维护边界。"
scope: "docs 目录与项目级 Markdown 入口"
status: "现行索引"
last_reviewed: "2026-06-19"
---
# 规划与治理文档归并索引

## 阅读顺序

1. 先读根目录 [README](../README.md)，确认知识库目标、范围、目录结构和流水线入口。
2. 再读 [目录介绍](../目录介绍.md)，按目录理解数据层、发布包、报告和人工复核入口。
3. 需要理解项目总体背景时，回到仓库根部的 [context.md](../../context.md)。
4. 需要判断下一步怎么做时，优先读 [阶段方案矩阵](roadmap/phase_solution_matrix_v1.md)。
5. 需要查具体规则、阶段设计或技术调研时，再进入下方分组文档。

## 目录分组

| 分组 | 作用 | 维护边界 |
| --- | --- | --- |
| [roadmap/](roadmap/) | 路线图、阶段方案矩阵和跨阶段取舍。 | 只记录阶段级目标、顺序、较优解、简易版和验收边界。 |
| [governance/](governance/) | 数据管理、生命周期、语义质量等治理设计。 | 说明治理模型和规则，不替代生成脚本或报告事实。 |
| [stages/](stages/) | 单个阶段的详细开发、技术调研和标准出口方案。 | 记录阶段内实施方案、PoC 边界和交付物。 |
| [rules/](rules/) | Markdown 文档维护规则。 | 约束文档 CRUD、Frontmatter、路径、索引和链接维护。 |

## 路线图文档

| 文档 | 定位 |
| --- | --- |
| [roadmap/phase_solution_matrix_v1.md](roadmap/phase_solution_matrix_v1.md) | 每个阶段的较优解、简易版、推荐采用方式和取舍说明。 |
| [roadmap/next_stage_plan_v1.md](roadmap/next_stage_plan_v1.md) | 下一阶段建设计划，用于判断阶段顺序和总体路线。 |

## 治理文档

| 文档 | 定位 |
| --- | --- |
| [governance/data_management_v1.md](governance/data_management_v1.md) | 数据管理体系总说明，用于理解资产、模型、元数据、质量、生命周期和访问能力。 |
| [governance/lifecycle_metadata_v1.md](governance/lifecycle_metadata_v1.md) | 生命周期与元数据治理说明，用于理解状态字段、阶段边界和治理证据。 |
| [governance/semantic_quality_v1.md](governance/semantic_quality_v1.md) | 语义质量治理说明，用于理解 blocker/warning/info、可信默认集合和语义扫描边界。 |
| [governance/semantic_identity_v1.md](governance/semantic_identity_v1.md) | 语义标识前置说明，用于理解 `bgpkb:`、URI 规则、JSON-LD context 和字段映射边界。 |

## 阶段文档

| 文档 | 定位 |
| --- | --- |
| [stages/phase_1_data_management_v1_development.md](stages/phase_1_data_management_v1_development.md) | 阶段一数据管理体系的详细开发说明，用于回看该阶段设计和落地范围。 |
| [stages/phase_3_5_semantic_identity_v1.md](stages/phase_3_5_semantic_identity_v1.md) | 阶段三点五语义标识前置交付说明，用于确认小步较优解的交付物和验收标准。 |
| [stages/phase_4_rag_framework_v1.md](stages/phase_4_rag_framework_v1.md) | 阶段四 RAG 就绪框架交付说明，用于确认当前设备不运行模型条件下的框架、边界和验收标准。 |
| [stages/phase_4_rag_and_llm_technical_research_v1.md](stages/phase_4_rag_and_llm_technical_research_v1.md) | 阶段四技术调研，用于评估 LLM 辅助知识加工、embedding、向量索引、混合检索和 RAG context pack。 |
| [stages/phase_5_standard_exports_v1.md](stages/phase_5_standard_exports_v1.md) | 阶段五标准化出口方案，用于规划 JSON-LD、SKOS、PROV-O 和 RDF 的渐进式建设。 |

## 规则文档

| 文档 | 定位 |
| --- | --- |
| [rules/document_crud_rules_v1.md](rules/document_crud_rules_v1.md) | Markdown 文档 CRUD 规则，用于约束后续新增、读取、更新、删除或归档文档。 |

## 与其他归并入口的关系

| 入口 | 何时使用 |
| --- | --- |
| [../reports/README.md](../reports/README.md) | 需要找阶段报告、质量报告、发布报告、人工复核报告时使用。 |
| [../cleaned/README.md](../cleaned/README.md) | 需要找清洗后的标准、数据源、论文、案例语料时使用。 |
| [../published/README.md](../published/README.md) | 需要使用可交付知识库包、SQLite、JSONL 和查询入口时使用。 |
