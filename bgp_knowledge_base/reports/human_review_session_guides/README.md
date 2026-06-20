# 人工复核会话指南

## 范围

本目录从人工复核会话队列和证据摘录机械生成。它只把待复核实体按 session 展开为可读操作入口，不判断实体是否应批准或拒绝。

## 使用方式

1. 打开一个 session 文件，从上到下核验实体、来源路径和摘录。
2. 如需逐 session 填写参考，可打开 `review_inputs/human_review_session_decision_templates/` 中对应模板。
3. 人工判断后，在 `review_inputs/human_review_decisions.csv` 中填写 `entity_id`、`review_decision`、`reviewer`、`reviewed_at` 和 `decision_note`。
4. 若需要语义判断或 LLM，填写 `needs_semantic_review` 或保持 `unreviewed`，不要在流水线中自动判定。
5. 填写后运行 `python3 scripts/build_human_review_decision_audit.py` 审计，再按需显式应用。

## 摘要

- 队列记录数：112
- session 数：12
- 人工决策输入：`review_inputs/human_review_decisions.csv`

## 按队列状态统计

- blocked_by_llm：1
- manual_followup：4
- ready_to_apply：107

## Session 文件

- `review_session_001.md`：10 条
- `review_session_002.md`：10 条
- `review_session_003.md`：10 条
- `review_session_004.md`：10 条
- `review_session_005.md`：10 条
- `review_session_006.md`：10 条
- `review_session_007.md`：10 条
- `review_session_008.md`：10 条
- `review_session_009.md`：10 条
- `review_session_010.md`：10 条
- `review_session_011.md`：10 条
- `review_session_012.md`：2 条

## 跳过事项

- 未自动批准、拒绝或改写实体。
- 未判断摘录是否足以支持实体字段。
- 未调用 LLM，也不下载新来源。
