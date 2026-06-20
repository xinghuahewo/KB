# 人工复核交接清单报告

## 范围

本报告把人工复核任务板转换为交接清单，逐项列出输入、人工输出目标、dry-run/写入命令和验证命令。它不执行命令，不调用 LLM，不下载来源，也不改变实体状态。

## 摘要

- 交接项数：25
- 可显式写入项：13
- 主输入缺失数：0
- 辅助输入缺失数：0
- JSONL 输出：`datasets/human_review_handoff.jsonl`
- CSV 输出：`datasets/human_review_handoff.csv`

## 按任务类型统计

- `apply_decisions`：1
- `audit_decisions`：1
- `review_session`：12
- `review_source`：10
- `validate_input`：1

## 交接清单

| 顺序 | 类型 | 标题 | 主输入 | 人工输出目标 | 验证命令 |
| ---: | --- | --- | --- | --- | --- |
| 1 | `review_session` | 复核 review_session_001 | `reports/human_review_session_guides/review_session_001.md` | 先在 review_inputs/human_review_session_decision_templates/review_session_001_decisions_template.csv 中填写人工判断，再显式导入到 review_inputs/human_review_decisions.csv。 | `python3 scripts/build_human_review_session_status.py` |
| 2 | `review_session` | 复核 review_session_002 | `reports/human_review_session_guides/review_session_002.md` | 先在 review_inputs/human_review_session_decision_templates/review_session_002_decisions_template.csv 中填写人工判断，再显式导入到 review_inputs/human_review_decisions.csv。 | `python3 scripts/build_human_review_session_status.py` |
| 3 | `review_session` | 复核 review_session_003 | `reports/human_review_session_guides/review_session_003.md` | 先在 review_inputs/human_review_session_decision_templates/review_session_003_decisions_template.csv 中填写人工判断，再显式导入到 review_inputs/human_review_decisions.csv。 | `python3 scripts/build_human_review_session_status.py` |
| 4 | `review_session` | 复核 review_session_004 | `reports/human_review_session_guides/review_session_004.md` | 先在 review_inputs/human_review_session_decision_templates/review_session_004_decisions_template.csv 中填写人工判断，再显式导入到 review_inputs/human_review_decisions.csv。 | `python3 scripts/build_human_review_session_status.py` |
| 5 | `review_session` | 复核 review_session_005 | `reports/human_review_session_guides/review_session_005.md` | 先在 review_inputs/human_review_session_decision_templates/review_session_005_decisions_template.csv 中填写人工判断，再显式导入到 review_inputs/human_review_decisions.csv。 | `python3 scripts/build_human_review_session_status.py` |
| 6 | `review_session` | 复核 review_session_006 | `reports/human_review_session_guides/review_session_006.md` | 先在 review_inputs/human_review_session_decision_templates/review_session_006_decisions_template.csv 中填写人工判断，再显式导入到 review_inputs/human_review_decisions.csv。 | `python3 scripts/build_human_review_session_status.py` |
| 7 | `review_session` | 复核 review_session_007 | `reports/human_review_session_guides/review_session_007.md` | 先在 review_inputs/human_review_session_decision_templates/review_session_007_decisions_template.csv 中填写人工判断，再显式导入到 review_inputs/human_review_decisions.csv。 | `python3 scripts/build_human_review_session_status.py` |
| 8 | `review_session` | 复核 review_session_008 | `reports/human_review_session_guides/review_session_008.md` | 先在 review_inputs/human_review_session_decision_templates/review_session_008_decisions_template.csv 中填写人工判断，再显式导入到 review_inputs/human_review_decisions.csv。 | `python3 scripts/build_human_review_session_status.py` |
| 9 | `review_session` | 复核 review_session_009 | `reports/human_review_session_guides/review_session_009.md` | 先在 review_inputs/human_review_session_decision_templates/review_session_009_decisions_template.csv 中填写人工判断，再显式导入到 review_inputs/human_review_decisions.csv。 | `python3 scripts/build_human_review_session_status.py` |
| 10 | `review_session` | 复核 review_session_010 | `reports/human_review_session_guides/review_session_010.md` | 先在 review_inputs/human_review_session_decision_templates/review_session_010_decisions_template.csv 中填写人工判断，再显式导入到 review_inputs/human_review_decisions.csv。 | `python3 scripts/build_human_review_session_status.py` |
| 11 | `review_session` | 复核 review_session_011 | `reports/human_review_session_guides/review_session_011.md` | 先在 review_inputs/human_review_session_decision_templates/review_session_011_decisions_template.csv 中填写人工判断，再显式导入到 review_inputs/human_review_decisions.csv。 | `python3 scripts/build_human_review_session_status.py` |
| 12 | `review_session` | 复核 review_session_012 | `reports/human_review_session_guides/review_session_012.md` | 先在 review_inputs/human_review_session_decision_templates/review_session_012_decisions_template.csv 中填写人工判断，再显式导入到 review_inputs/human_review_decisions.csv。 | `python3 scripts/build_human_review_session_status.py` |
| 13 | `review_source` | 按来源复核 rfc4271 | `reports/human_review_source_matrix_report.md` | 按来源核验证据后，把实体级人工判断写入 review_inputs/human_review_decisions.csv 或对应 session 模板。 | `python3 scripts/build_human_review_source_matrix.py` |
| 14 | `review_source` | 按来源复核 rfc6811 | `reports/human_review_source_matrix_report.md` | 按来源核验证据后，把实体级人工判断写入 review_inputs/human_review_decisions.csv 或对应 session 模板。 | `python3 scripts/build_human_review_source_matrix.py` |
| 15 | `review_source` | 按来源复核 ripe_ris_docs | `reports/human_review_source_matrix_report.md` | 按来源核验证据后，把实体级人工判断写入 review_inputs/human_review_decisions.csv 或对应 session 模板。 | `python3 scripts/build_human_review_source_matrix.py` |
| 16 | `review_source` | 按来源复核 caida_as_relationships | `reports/human_review_source_matrix_report.md` | 按来源核验证据后，把实体级人工判断写入 review_inputs/human_review_decisions.csv 或对应 session 模板。 | `python3 scripts/build_human_review_source_matrix.py` |
| 17 | `review_source` | 按来源复核 routeviews_api_doc | `reports/human_review_source_matrix_report.md` | 按来源核验证据后，把实体级人工判断写入 review_inputs/human_review_decisions.csv 或对应 session 模板。 | `python3 scripts/build_human_review_source_matrix.py` |
| 18 | `review_source` | 按来源复核 bear_2025 | `reports/human_review_source_matrix_report.md` | 按来源核验证据后，把实体级人工判断写入 review_inputs/human_review_decisions.csv 或对应 session 模板。 | `python3 scripts/build_human_review_source_matrix.py` |
| 19 | `review_source` | 按来源复核 bgpshield_2025 | `reports/human_review_source_matrix_report.md` | 按来源核验证据后，把实体级人工判断写入 review_inputs/human_review_decisions.csv 或对应 session 模板。 | `python3 scripts/build_human_review_source_matrix.py` |
| 20 | `review_source` | 按来源复核 bgpstream_docs | `reports/human_review_source_matrix_report.md` | 按来源核验证据后，把实体级人工判断写入 review_inputs/human_review_decisions.csv 或对应 session 模板。 | `python3 scripts/build_human_review_source_matrix.py` |
| 21 | `review_source` | 按来源复核 rfc7908 | `reports/human_review_source_matrix_report.md` | 按来源核验证据后，把实体级人工判断写入 review_inputs/human_review_decisions.csv 或对应 session 模板。 | `python3 scripts/build_human_review_source_matrix.py` |
| 22 | `review_source` | 按来源复核 rfc9234 | `reports/human_review_source_matrix_report.md` | 按来源核验证据后，把实体级人工判断写入 review_inputs/human_review_decisions.csv 或对应 session 模板。 | `python3 scripts/build_human_review_source_matrix.py` |
| 23 | `validate_input` | 校验主人工决策输入 | `review_inputs/human_review_decisions.csv` | 生成 reports/human_review_input_validation_report.md 和 datasets/human_review_input_validation.*，只校验主决策输入。 | `python3 scripts/build_human_review_decision_audit.py` |
| 24 | `audit_decisions` | 审计主人工决策文件 | `review_inputs/human_review_decisions.csv` | 生成 reports/human_review_decision_audit_report.md 和 datasets/human_review_decision_audit.*，只审计不应用。 | `python3 scripts/build_human_review_progress.py` |
| 25 | `apply_decisions` | 显式应用已审计通过的 approved/rejected 决策 | `datasets/human_review_decision_audit.jsonl` | 显式应用已审计通过且不需要 LLM 的 approved/rejected 决策，并生成应用报告。 | `python3 scripts/run_pipeline.py` |

## 跳过事项

- 未执行 dry-run、写入或验证命令。
- 未自动批准、拒绝或改写实体。
- 未调用 LLM，也不下载新来源。
- `needs_semantic_review` 仍按规则跳过并记录。
