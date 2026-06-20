---
title: "规划与治理文档索引"
document_type: "归并索引"
purpose: "提供 docs 目录的最小阅读入口，避免阶段规划、治理规则和实施计划重复展开。"
scope: "docs 目录"
status: "现行索引"
last_reviewed: "2026-06-20"
---
# 规划与治理文档索引

## 推荐阅读顺序

1. 先读仓库根目录 `README.md` 和 `目录介绍.md`，确认项目目标、目录和运行入口。
2. 再读 [roadmap/phase_solution_matrix_v1.md](roadmap/phase_solution_matrix_v1.md)，判断当前阶段取舍。
3. 需要执行下一步时，读 [roadmap/next_stage_plan_v1.md](roadmap/next_stage_plan_v1.md)。
4. 需要阶段细节时，只进入对应 `stages/` 文档。
5. 需要落地开发时，再读 `docs/superpowers/plans/` 下的实施计划。

## 当前主线

当前阶段主线是阶段四：RAG 就绪与混合检索。

| 子阶段 | 状态 | 关键文档 |
| --- | --- | --- |
| 4.1 RAG Answer API | 已完成 | `docs/superpowers/plans/2026-06-20-phase-4-1-rag-answer.md` |
| 4.2 DeepSeek smoke | 已完成 | 根目录 `README.md` 与 smoke 报告 |
| 4.3 RAG 答案评测 | 已完成 | [stages/phase_4_3_rag_answer_eval_v1.md](stages/phase_4_3_rag_answer_eval_v1.md) |
| 4.4 DeepSeek 批量评测 | 已完成，分支待并入主线 | [stages/phase_4_4_deepseek_eval_analysis_v1.md](stages/phase_4_4_deepseek_eval_analysis_v1.md) |
| 4.5 BGE-M3 混合检索 | 下一步 | [stages/phase_4_5_bge_m3_hybrid_retrieval_v1.md](stages/phase_4_5_bge_m3_hybrid_retrieval_v1.md) |

## 文档分组

| 目录 | 用途 | 精简边界 |
| --- | --- | --- |
| `roadmap/` | 阶段路线、取舍和下一步。 | 只写决策摘要，不重复阶段实现细节。 |
| `stages/` | 单阶段目标、边界、交付物和验收标准。 | 每个阶段一篇主文档，历史文档保留但不扩写。 |
| `governance/` | 数据治理、生命周期、语义质量和语义标识规则。 | 只写治理规则，不承载阶段实施计划。 |
| `rules/` | 文档维护规则。 | 只约束 Markdown CRUD 和索引维护。 |
| `superpowers/plans/` | 可执行实施计划。 | 只放开发任务拆解，不写路线图背景。 |

## 核心文档

| 文档 | 定位 |
| --- | --- |
| [roadmap/phase_solution_matrix_v1.md](roadmap/phase_solution_matrix_v1.md) | 当前阶段采用较优解还是简易版的决策表。 |
| [roadmap/next_stage_plan_v1.md](roadmap/next_stage_plan_v1.md) | 近期下一步建设计划。 |
| [stages/phase_4_5_bge_m3_hybrid_retrieval_v1.md](stages/phase_4_5_bge_m3_hybrid_retrieval_v1.md) | 阶段 4.5 终极目标、技术选型、边界和验收标准。 |
| [superpowers/plans/2026-06-20-phase-4-5-bge-m3-hybrid.md](superpowers/plans/2026-06-20-phase-4-5-bge-m3-hybrid.md) | 阶段 4.5 可执行开发计划。 |

## 维护规则

- 新增阶段只新增一篇 `stages/phase_xxx.md` 和必要的一篇实施计划。
- 索引文档只做导航，不复制阶段细节。
- 路线图只记录当前状态、下一步和边界约束。
- 所有生成文档使用中文。
