# 阶段 4.4 RAG 答案失败样本分析报告

## 摘要

- 生成时间：2026-06-20T16:57:32
- 输入文件：`datasets/deepseek_rag_answer_eval_results.jsonl`
- 问题数：20
- 通过数：20
- 失败数：0
- 密钥记录：未读取、未写入、未报告。

## 失败检查分布

- 无失败检查。

## 状态迁移分布

- answered->answered：17
- no_evidence->no_evidence：3

## 失败样本

- 无失败样本。

## 建议

- 如果失败集中在 `must_have_terms_missing`，优先检查提示词和答案约束。
- 如果失败集中在 `missing_citations`，优先检查检索召回和 context pack。
- 如果失败集中在 `answer_status_mismatch`，优先检查无证据查询和检索阈值。
