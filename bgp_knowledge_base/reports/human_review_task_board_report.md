# 人工复核任务板报告

## 范围

本报告把 session、来源矩阵、字段清单、输入校验、决策审计和显式应用入口整理为可执行任务板。它只给出下一步入口和命令提示，不执行命令，不调用 LLM，也不修改实体状态。

## 摘要

- 任务数：25
- JSONL 输出：`datasets/human_review_task_board.jsonl`
- CSV 输出：`datasets/human_review_task_board.csv`

## 任务清单

| 顺序 | 类型 | 标题 | 主输入 | 建议命令 |
| ---: | --- | --- | --- | --- |
| 1 | `review_session` | 复核 review_session_001 | `reports/human_review_session_guides/review_session_001.md` | `python3 scripts/import_human_review_session_decisions.py --session-id review_session_001` |
| 2 | `review_session` | 复核 review_session_002 | `reports/human_review_session_guides/review_session_002.md` | `python3 scripts/import_human_review_session_decisions.py --session-id review_session_002` |
| 3 | `review_session` | 复核 review_session_003 | `reports/human_review_session_guides/review_session_003.md` | `python3 scripts/import_human_review_session_decisions.py --session-id review_session_003` |
| 4 | `review_session` | 复核 review_session_004 | `reports/human_review_session_guides/review_session_004.md` | `python3 scripts/import_human_review_session_decisions.py --session-id review_session_004` |
| 5 | `review_session` | 复核 review_session_005 | `reports/human_review_session_guides/review_session_005.md` | `python3 scripts/import_human_review_session_decisions.py --session-id review_session_005` |
| 6 | `review_session` | 复核 review_session_006 | `reports/human_review_session_guides/review_session_006.md` | `python3 scripts/import_human_review_session_decisions.py --session-id review_session_006` |
| 7 | `review_session` | 复核 review_session_007 | `reports/human_review_session_guides/review_session_007.md` | `python3 scripts/import_human_review_session_decisions.py --session-id review_session_007` |
| 8 | `review_session` | 复核 review_session_008 | `reports/human_review_session_guides/review_session_008.md` | `python3 scripts/import_human_review_session_decisions.py --session-id review_session_008` |
| 9 | `review_session` | 复核 review_session_009 | `reports/human_review_session_guides/review_session_009.md` | `python3 scripts/import_human_review_session_decisions.py --session-id review_session_009` |
| 10 | `review_session` | 复核 review_session_010 | `reports/human_review_session_guides/review_session_010.md` | `python3 scripts/import_human_review_session_decisions.py --session-id review_session_010` |
| 11 | `review_session` | 复核 review_session_011 | `reports/human_review_session_guides/review_session_011.md` | `python3 scripts/import_human_review_session_decisions.py --session-id review_session_011` |
| 12 | `review_session` | 复核 review_session_012 | `reports/human_review_session_guides/review_session_012.md` | `python3 scripts/import_human_review_session_decisions.py --session-id review_session_012` |
| 13 | `review_source` | 按来源复核 rfc4271 | `reports/human_review_source_matrix_report.md` | `python3 scripts/build_human_review_source_matrix.py` |
| 14 | `review_source` | 按来源复核 rfc6811 | `reports/human_review_source_matrix_report.md` | `python3 scripts/build_human_review_source_matrix.py` |
| 15 | `review_source` | 按来源复核 ripe_ris_docs | `reports/human_review_source_matrix_report.md` | `python3 scripts/build_human_review_source_matrix.py` |
| 16 | `review_source` | 按来源复核 caida_as_relationships | `reports/human_review_source_matrix_report.md` | `python3 scripts/build_human_review_source_matrix.py` |
| 17 | `review_source` | 按来源复核 routeviews_api_doc | `reports/human_review_source_matrix_report.md` | `python3 scripts/build_human_review_source_matrix.py` |
| 18 | `review_source` | 按来源复核 bear_2025 | `reports/human_review_source_matrix_report.md` | `python3 scripts/build_human_review_source_matrix.py` |
| 19 | `review_source` | 按来源复核 bgpshield_2025 | `reports/human_review_source_matrix_report.md` | `python3 scripts/build_human_review_source_matrix.py` |
| 20 | `review_source` | 按来源复核 bgpstream_docs | `reports/human_review_source_matrix_report.md` | `python3 scripts/build_human_review_source_matrix.py` |
| 21 | `review_source` | 按来源复核 rfc7908 | `reports/human_review_source_matrix_report.md` | `python3 scripts/build_human_review_source_matrix.py` |
| 22 | `review_source` | 按来源复核 rfc9234 | `reports/human_review_source_matrix_report.md` | `python3 scripts/build_human_review_source_matrix.py` |
| 23 | `validate_input` | 校验主人工决策输入 | `review_inputs/human_review_decisions.csv` | `python3 scripts/build_human_review_input_validation.py` |
| 24 | `audit_decisions` | 审计主人工决策文件 | `review_inputs/human_review_decisions.csv` | `python3 scripts/build_human_review_decision_audit.py` |
| 25 | `apply_decisions` | 显式应用已审计通过的 approved/rejected 决策 | `datasets/human_review_decision_audit.jsonl` | `python3 scripts/apply_human_review_decisions.py` |

## 跳过事项

- 未执行任务板中的命令。
- 未自动批准、拒绝或改写实体。
- 未调用 LLM，也不下载新来源。
