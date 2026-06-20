# 权威来源补充需求报告

## 范围

本报告从实体人工复核包中机械筛出 `context_only_needs_authoritative_source` 记录，生成补充权威来源的需求队列。该步骤不联网、不下载资料、不判断候选来源是否足以批准实体。

## 摘要

- 需求记录数：0
- JSONL 输出：`datasets/authoritative_source_requirements.jsonl`
- CSV 输出：`datasets/authoritative_source_requirements.csv`
- 下载范围：不要全量下载；确认单条候选来源后再登记归档。

## 按需求类型统计


## 按实体类型统计


## 需求明细

| 实体 ID | 类型 | 名称 | 推荐来源类别 | 检索提示 |
| --- | --- | --- | --- | --- |

## 跳过事项

- 未使用 LLM 判断候选来源相关性。
- 未从网页、论文或案例正文中抽取新实体。
- 未批量下载资料；下一步应只对人工确认的少量来源做单条归档。
