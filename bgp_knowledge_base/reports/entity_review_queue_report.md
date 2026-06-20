# 实体复核队列报告

## 范围

本报告从 `entities/*.jsonl` 和 `datasets/source_processing_status.jsonl` 机械生成待复核队列。该步骤不改变实体审核状态，不判断定义是否正确，只标出来源处理状态是否足以进入人工复核。

## 摘要

- 队列记录数：5
- JSONL 输出：`datasets/entity_review_queue.jsonl`
- CSV 输出：`datasets/entity_review_queue.csv`

## 按建议动作统计

- human_review_ready：5

## 按实体类型统计

- Case：4
- PaperMethod：1
