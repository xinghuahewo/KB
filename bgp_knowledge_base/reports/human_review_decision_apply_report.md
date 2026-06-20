# 人工复核决策应用报告

## 范围

本脚本只处理 `datasets/human_review_decision_audit.jsonl` 中已审计为 `ready_to_apply`、`can_apply=true` 且不需要 LLM 的 `approved/rejected` 决策。

默认模式为 dry-run；只有传入 `--write` 才会修改 `entities/*.jsonl`。

## 摘要

- 运行模式：dry-run
- 可应用决策数：107
- 将更新实体数：0
- 已是目标状态的实体数：107
- 未找到实体数：0
- JSONL 输出：`datasets/human_review_decision_apply_preview.jsonl`
- CSV 输出：`datasets/human_review_decision_apply_preview.csv`

## 按文件更新数

- 无

## 跳过的审计状态

- blocked_by_llm：1
- manual_followup：4

## 本次更新预览

- 无

## 跳过事项

- 未应用 `needs_semantic_review`，因为该状态需要语义流程或 LLM。
- 未应用 `needs_source` 或 `unreviewed`。
- 本脚本不会下载来源，也不会判断证据是否充分。
- 未传入 `--write` 时，不修改任何实体文件。
