# 人工复核决策输入模板报告

## 范围

本报告记录人工复核决策输入区的确定性生成结果。模板可被覆盖再生成；人工填写文件只在不存在时初始化表头，不会被流水线覆盖。

## 摘要

- 模板记录数：112
- 模板输出：`review_inputs/human_review_decisions_template.csv`
- 人工填写文件：`review_inputs/human_review_decisions.csv`
- 本次是否初始化人工填写文件：否
- 允许的 review_decision：`approved`、`rejected`、`needs_source`、`needs_semantic_review`；留空或 `unreviewed` 表示不应用。

## 按复核批次统计

- 01_ready_without_manual_note：34
- 02_ready_with_manual_note：78

## 跳过事项

- 未判断任何实体是否应批准或拒绝。
- 未修改 `entities/*.jsonl`。
- `needs_semantic_review` 只作为人工标记进入审计，后续仍按规则跳过语义/LLM 处理。
