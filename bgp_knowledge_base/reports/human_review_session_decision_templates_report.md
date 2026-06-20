# 人工复核会话决策模板报告

## 范围

本报告记录按 session 生成的人工决策模板。它只切分和预填上下文字段，不判断实体是否应批准或拒绝，不覆盖主人工决策文件。

## 摘要

- 模板文件数：12
- 模板记录数：112
- 输出目录：`review_inputs/human_review_session_decision_templates/`
- 主人工决策文件：`review_inputs/human_review_decisions.csv`

## 按队列状态统计

- blocked_by_llm：1
- manual_followup：4
- ready_to_apply：107

## 按 session 大小统计

- 2 条/session：1 个
- 10 条/session：11 个

## 模板清单

- `review_inputs/human_review_session_decision_templates/review_session_001_decisions_template.csv`
- `review_inputs/human_review_session_decision_templates/review_session_002_decisions_template.csv`
- `review_inputs/human_review_session_decision_templates/review_session_003_decisions_template.csv`
- `review_inputs/human_review_session_decision_templates/review_session_004_decisions_template.csv`
- `review_inputs/human_review_session_decision_templates/review_session_005_decisions_template.csv`
- `review_inputs/human_review_session_decision_templates/review_session_006_decisions_template.csv`
- `review_inputs/human_review_session_decision_templates/review_session_007_decisions_template.csv`
- `review_inputs/human_review_session_decision_templates/review_session_008_decisions_template.csv`
- `review_inputs/human_review_session_decision_templates/review_session_009_decisions_template.csv`
- `review_inputs/human_review_session_decision_templates/review_session_010_decisions_template.csv`
- `review_inputs/human_review_session_decision_templates/review_session_011_decisions_template.csv`
- `review_inputs/human_review_session_decision_templates/review_session_012_decisions_template.csv`

## 跳过事项

- 未自动批准、拒绝或改写实体。
- 未把 session 模板自动合并进 `review_inputs/human_review_decisions.csv`。
- 未执行语义判断、LLM 或新来源下载。
