---
title: "阶段 4.3 RAG 答案质量评测 v1"
document_type: "阶段说明"
purpose: "说明 RAG 答案质量、引用质量和拒答行为的可复跑评测体系。"
scope: "阶段 4.3"
status: "现行"
last_reviewed: "2026-06-20"
---
# 阶段 4.3 RAG 答案质量评测 v1

## 目标

阶段 4.3 将 RAG 从“能回答”推进到“可持续评估”。本阶段建立固定问题集、自动评测脚本和中文报告，用于检查答案状态、引用覆盖、无证据拒答、禁用说法和运行边界。

## 新增能力

- `datasets/rag_answer_eval_questions.jsonl` 保存固定评测问题。
- `scripts/run_rag_answer_eval.py` 运行答案质量评测。
- `datasets/rag_answer_eval_results.jsonl` 保存逐题结果。
- `reports/rag_answer_eval_report.md` 汇总引用覆盖率、拒答率和失败项。
- 检索排序加入轻量意图权重，使定义类问题优先标准、事件类问题优先案例、方法类问题优先论文。

## 运行方式

```bash
python3 scripts/run_rag_answer_eval.py
```

如果环境变量 `DEEPSEEK_API_KEY` 不存在，脚本使用离线结构检查客户端，不调用外部 API。设置 `DEEPSEEK_API_KEY` 后，同一脚本可调用真实 DeepSeek API。

## 验收边界

- 当前设备不运行本地模型。
- 不接入 BGE-M3、Milvus 或本地 Qwen。
- 不自动写回实体、关系、chunk 或发布包。
- 不把 API key 写入报告、数据集或仓库。
- 无证据问题必须返回 `no_evidence`。

## 当前评测门槛

- 评测集至少 20 条问题。
- 有证据问题引用覆盖率不低于 95%。
- 无证据拒答率为 100%。
- citations 必须全部来自当前 context pack。
- 质量检查中 JSON 错误数和 Schema 错误数必须为 0。
