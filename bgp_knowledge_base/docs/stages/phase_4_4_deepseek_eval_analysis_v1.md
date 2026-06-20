---
title: "阶段 4.4 DeepSeek 批量评测与失败分析 v1"
document_type: "阶段说明"
purpose: "说明真实 DeepSeek 批量评测、离线失败样本分析和密钥边界。"
scope: "阶段 4.4"
status: "现行"
last_reviewed: "2026-06-20"
---
# 阶段 4.4 DeepSeek 批量评测与失败分析 v1

## 目标

阶段 4.4 在阶段 4.3 固定评测集之上运行真实 DeepSeek 批量评测，并将失败样本归因到可行动的检查项。该阶段用于判断真实模型回答是否稳定满足引用、拒答和边界要求。

## 新增能力

- `scripts/run_deepseek_rag_answer_eval.py` 使用真实 DeepSeek API 运行批量评测。
- `datasets/deepseek_rag_answer_eval_results.jsonl` 保存真实评测逐题结果。
- `reports/deepseek_rag_answer_eval_report.md` 保存真实评测中文报告。
- `scripts/build_rag_answer_failure_analysis.py` 生成失败样本分析。
- `reports/rag_answer_failure_analysis_report.md` 汇总失败检查分布、状态迁移和样本建议。

## 运行方式

```bash
export DEEPSEEK_API_KEY="你的 DeepSeek API key"
python3 scripts/run_deepseek_rag_answer_eval.py
python3 scripts/build_rag_answer_failure_analysis.py
```

失败分析脚本不读取密钥。如果真实评测结果存在，它优先分析真实结果；否则分析阶段 4.3 的离线评测结果。

## 边界

- API key 只从环境变量读取。
- 报告和数据集不保存 API key。
- 当前设备不运行本地模型。
- 不自动写回实体、关系、chunk 或发布包。
- CI 不强制调用 DeepSeek API，只运行离线失败分析。

## 验收门槛

- 真实评测报告已生成。
- 失败分析报告已生成。
- 密钥扫描未发现真实 key。
- 质量检查 JSON 错误数和 Schema 错误数均为 0。
