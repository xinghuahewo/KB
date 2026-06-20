# 人工复核进度报告

## 范围

本报告从人工复核工作簿和人工复核决策审计结果机械汇总，只统计状态和下一步动作，不判断来源是否足以批准实体。

## 摘要

- 复核范围实体数：112
- pending：5
- approved：107
- rejected：0
- 可显式应用决策：107
- 需要 LLM/语义流程阻塞：1
- 完成率：95.54%
- JSONL 输出：`datasets/human_review_progress.jsonl`
- CSV 输出：`datasets/human_review_progress.csv`

## 下一步

- 运行 scripts/apply_human_review_decisions.py 显式应用已审计通过的 approved/rejected 决策。

## 分组进度

| 范围 | 值 | 实体数 | pending | approved | rejected | 可应用 | LLM 阻塞 | 完成率 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| entity_type | AnomalyType | 8 | 0 | 8 | 0 | 8 | 0 | 100.0% |
| entity_type | BGPConcept | 31 | 0 | 31 | 0 | 31 | 0 | 100.0% |
| entity_type | Case | 5 | 4 | 1 | 0 | 1 | 0 | 20.0% |
| entity_type | DataField | 32 | 0 | 32 | 0 | 32 | 0 | 100.0% |
| entity_type | DataSource | 9 | 0 | 9 | 0 | 9 | 0 | 100.0% |
| entity_type | EvidenceTemplate | 8 | 0 | 8 | 0 | 8 | 0 | 100.0% |
| entity_type | FalsePositivePattern | 4 | 0 | 4 | 0 | 4 | 0 | 100.0% |
| entity_type | PaperMethod | 3 | 1 | 2 | 0 | 2 | 1 | 66.67% |
| entity_type | RoutingMechanism | 12 | 0 | 12 | 0 | 12 | 0 | 100.0% |
| review_batch | 01_ready_without_manual_note | 34 | 0 | 34 | 0 | 34 | 0 | 100.0% |
| review_batch | 02_ready_with_manual_note | 78 | 5 | 73 | 0 | 73 | 1 | 93.59% |
| review_bucket | ready_with_manual_note | 78 | 5 | 73 | 0 | 73 | 1 | 93.59% |
| review_bucket | ready_without_manual_note | 34 | 0 | 34 | 0 | 34 | 0 | 100.0% |

## 跳过事项

- 未自动批准、拒绝或改写任何实体。
- 未判断证据充分性。
- 未处理 `needs_semantic_review`，该类仍需语义流程或 LLM，按当前规则跳过并记录。
