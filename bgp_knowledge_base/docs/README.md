---
title: "项目文档索引"
document_type: "归并索引"
purpose: "集中导航仍然有效的治理规范、阶段交付、后续路线和项目说明。"
scope: "docs 目录"
status: "现行索引"
last_reviewed: "2026-06-29"
---
# 项目文档索引

`docs/` 只保留仍对运行、验收、治理或后续建设有用的文档。已完成的临时实施计划、被正式规范覆盖的调研草稿和过期路线图不在这里长期保存，历史内容由 Git 记录。

## 推荐阅读顺序

1. 阅读根目录 [README](../README.md)，了解项目目标、运行命令和主要入口。
2. 阅读 [目录介绍](../目录介绍.md)，了解数据、元数据、代码、测试和报告的边界。
3. 按需要查阅下方治理规范、阶段交付或后续路线。
4. 查运行结果时使用 [报告索引](../data/reports/README.md)，不要在 `docs/` 查生成报告。

## 治理规范

| 文档 | 用途 |
| --- | --- |
| [数据管理体系](governance/data_management_v1.md) | 数据资产、模型、溯源、质量、生命周期、访问和出口的总体治理边界。 |
| [生命周期与元数据治理](governance/lifecycle_metadata_v1.md) | 生命周期状态、推导规则、治理证据和行动边界。 |
| [语义质量治理](governance/semantic_quality_v1.md) | 语义问题分级、可信集合和扫描范围。 |
| [语义标识规范](governance/semantic_identity_v1.md) | 命名空间、稳定 URI、JSON-LD context 和字段映射。 |

## 阶段交付

下列文档是现行验收依据或仍有明确后续价值的专项说明。

| 文档 | 状态与用途 |
| --- | --- |
| [语料质量画像](stages/phase_a_corpus_profiling_v1.md) | 已交付；记录三层语料画像、确定性门禁和可选 OCR Provider 边界。 |
| [语义标识前置](stages/phase_3_5_semantic_identity_v1.md) | 已交付；记录语义标识层的交付物和验收边界。 |
| [RAG 就绪框架](stages/phase_4_rag_framework_v1.md) | 已交付；记录检索框架、Provider 边界和离线验收。 |
| [RAG 答案质量评测](stages/phase_4_3_rag_answer_eval_v1.md) | 现行；记录固定评测集和质量门槛。 |
| [DeepSeek 批量评测](stages/phase_4_4_deepseek_eval_analysis_v1.md) | 现行；记录真实模型评测和失败分析边界。 |
| [BGE-M3 混合检索](stages/phase_4_5_bge_m3_hybrid_retrieval_v1.md) | 已交付并通过真实向量评测；记录远程 embedding、融合检索和验收边界。 |
| [轻量标准化出口](stages/phase_5_standard_exports_v1.md) | 已交付并通过验收；记录确定性标准出口、模型候选和人工审核闸门。 |

## 后续路线

| 文档 | 用途 |
| --- | --- |
| [工业界对齐改进方案](roadmap/industry_alignment_improvement_plan_v1.md) | 当前唯一的长期改进路线，覆盖语料画像、层级 chunk、分类、候选层、追溯和增量更新。 |

## 独立项目

| 文档 | 用途 |
| --- | --- |
| [对话前端](projects/chat_frontend_project_branch_v1.md) | 已交付的独立 Next.js 前端边界、接口和运行说明。 |

## 文档规则

新增、更新和删除文档时遵循 [文档 CRUD 规则](rules/document_crud_rules_v1.md)。长期文档必须进入本索引；临时实施计划完成后应删除，由 Git 保留历史。
