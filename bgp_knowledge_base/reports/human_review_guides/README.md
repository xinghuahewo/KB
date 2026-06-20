# 人工复核指南

## 范围

本目录从人工复核工作簿机械生成，只用于把 pending 实体按批次展开为可读复核入口。生成过程不使用 LLM、不做语义判断、不下载资料、不修改实体状态。

## 文件入口

- `reports/human_review_guides/01_ready_without_manual_note.md`：34 条
- `reports/human_review_guides/02_ready_with_manual_note.md`：78 条

## 复核规则

- 先打开 `cleaned_paths` 和 `parsed_paths`，再用 `chunk_sample_ids` 定位具体片段。
- `context_2026` 只作为项目范围提示，不能单独作为批准依据。
- 若实体字段被非 manual_note 来源直接支持，可在 `datasets/human_review_workbook.*` 中把 `review_decision` 改为 `approved`，之后再运行决策审计。
- 若来源不支持实体字段，或需要解释、归纳、判定证据强度，应保持 `unreviewed` 或记录为后续人工处理；不要用 LLM 补判。

## 统计

- 复核实体总数：112
- 01_ready_without_manual_note：34
- 02_ready_with_manual_note：78
- review_decision=unreviewed：112

## 按实体类型统计

- AnomalyType：8
- BGPConcept：31
- Case：5
- DataField：32
- DataSource：9
- EvidenceTemplate：8
- FalsePositivePattern：4
- PaperMethod：3
- RoutingMechanism：12

## 已按规则跳过的语义事项

- `action_skipped_paper_method_expansion`：PaperMethod 目标缺口；原因：从论文正文扩展结构化方法需要语义判断或 LLM 介入，按用户要求跳过。
- `action_skipped_case_semantic_review`：案例观察值语义核验；原因：事件角色、证据强度和影响范围判断需要语义流程或 LLM 介入，按用户要求跳过。
