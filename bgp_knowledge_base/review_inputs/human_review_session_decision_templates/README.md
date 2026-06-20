# 人工复核会话决策模板

## 范围

本目录按 session 生成可填写参考模板，方便逐批复核。模板可以由流水线覆盖；人工最终决策仍应写入主文件 `review_inputs/human_review_decisions.csv`。

## 使用方式

1. 打开对应 session 的指南和模板 CSV。
2. 只把人工确认后的 `entity_id`、`review_decision`、`reviewer`、`reviewed_at`、`decision_note` 写入主决策文件。
3. 如果先填写 session 模板，可运行 `python3 scripts/import_human_review_session_decisions.py --session-id review_session_001` 做 dry-run；确认后显式加 `--write` 合并到主决策文件。
4. 若需要语义判断或 LLM，填写 `needs_semantic_review` 或保持 `unreviewed`，当前流水线只记录并跳过。
5. 填写主决策文件后运行 `python3 scripts/build_human_review_decision_audit.py`。

## 模板文件

- `review_session_001_decisions_template.csv`：10 条
- `review_session_002_decisions_template.csv`：10 条
- `review_session_003_decisions_template.csv`：10 条
- `review_session_004_decisions_template.csv`：10 条
- `review_session_005_decisions_template.csv`：10 条
- `review_session_006_decisions_template.csv`：10 条
- `review_session_007_decisions_template.csv`：10 条
- `review_session_008_decisions_template.csv`：10 条
- `review_session_009_decisions_template.csv`：10 条
- `review_session_010_decisions_template.csv`：10 条
- `review_session_011_decisions_template.csv`：10 条
- `review_session_012_decisions_template.csv`：2 条

## 跳过事项

- 未自动批准、拒绝或改写实体。
- 未把 session 模板自动合并进主决策文件。
- `scripts/import_human_review_session_decisions.py` 默认 dry-run，只有显式 `--write` 才会写入主决策文件。
- 未调用 LLM，也不下载新来源。
