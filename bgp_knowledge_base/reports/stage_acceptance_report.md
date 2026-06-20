# 阶段验收报告

## 结论

- 阶段：RAG 答案质量评测 v1 (`phase_4_3_rag_answer_eval_v1`)
- 结论：pass
- 验收模式：`deterministic_with_effect_review`
- 生成时间：2026-06-20T11:49:06

当前 KB 已具备可复跑的 RAG 答案质量、引用质量和拒答行为评测体系。

## 交付物验收

| 文件 | 状态 |
| --- | --- |
| `docs/stages/phase_4_3_rag_answer_eval_v1.md` | 通过 |
| `datasets/rag_answer_eval_questions.jsonl` | 通过 |
| `datasets/rag_answer_eval_results.jsonl` | 通过 |
| `reports/rag_answer_eval_report.md` | 通过 |
| `scripts/run_rag_answer_eval.py` | 通过 |
| `tests/test_rag_answer_eval_dataset.py` | 通过 |
| `tests/test_rag_answer_eval_script.py` | 通过 |
| `tests/test_rag_retrieval_ranking.py` | 通过 |

## 效果验收

### 新增能力

- 建立了 20 条固定 RAG 答案评测问题，覆盖概念、异常、数据源、中英文查询和无证据查询。
- 建立了答案质量评测脚本，可检查状态、引用、禁用说法、must-have 术语和运行边界。
- 建立了答案评测报告，输出引用覆盖率、无证据拒答率、逐题结论和人工复核项。
- 为检索排序加入轻量意图权重，使定义、事件和方法类查询更稳定命中对应来源。

### 使用者现在能做什么

- 一条命令复跑 RAG 答案质量评测并查看中文报告。
- 在没有 API key 时做离线结构检查，在有 API key 时做真实答案评测。
- 通过失败检查定位检索、引用或生成边界的问题。

### 后续阶段能依赖什么

- 阶段五可引用评测报告判断 RAG 输出是否适合进入标准化出口样例。
- 后续 BGE-M3/Milvus 接入可复用同一评测集比较召回质量。
- 后续答案生成策略可复用 must-have、forbidden 和 citation 检查作为回归门禁。

## 证据验收

### 命令结果

| 命令 | 状态 | 摘要 |
| --- | --- | --- |
| `python3 scripts/run_rag_answer_eval.py` | 通过 | Wrote reports/rag_answer_eval_report.md |
| `python3 -m pytest tests/test_rag_answer_eval_dataset.py tests/test_rag_answer_eval_script.py tests/test_rag_retrieval_ranking.py -v` | 通过 | ============================== 5 passed in 0.23s =============================== |

### 报告检查

| 报告 | 状态 | 缺失项 |
| --- | --- | --- |
| `reports/rag_answer_eval_report.md` | 通过 | 无 |
| `reports/pipeline_report.md` | 通过 | 无 |
| `reports/quality_report.md` | 通过 | 无 |

## 风险与剩余人工事项

- 当前离线结构检查不替代真实 DeepSeek 内容质量评审。
- expected_source_refs 只作为召回观察信号，暂不作为阻塞性失败条件。

## 建议

- 可进入下一阶段；保留人工事项不阻塞阶段通过。
