---
title: "阶段 A：语料质量画像 v1"
document_type: "阶段交付与验收说明"
purpose: "记录跨 parsed、cleaned、chunks 的确定性画像、可选 OCR 模型评估和质量门禁边界。"
scope: "语料质量画像、派生数据集、报告、Provider 与阶段验收"
status: "已交付"
last_reviewed: "2026-06-30"
---
# 阶段 A：语料质量画像 v1

## 交付结论

阶段 A 已建立语料质量的量化基线。确定性画像覆盖 parsed、cleaned 和 chunks 三层逻辑文档并集；可选 OCR 模型评估独立存储，默认离线，不参与质量门禁，也不修改主知识数据。

## 交付物

- 配置：`metadata/config/corpus_profiling.yaml`
- 画像 Schema：`metadata/schemas/corpus_profile.schema.json`
- OCR 评估 Schema：`metadata/schemas/corpus_ocr_assessment.schema.json`
- 确定性画像：`data/derived/datasets/corpus_profile.jsonl`
- 可选模型评估：`data/derived/datasets/corpus_ocr_assessments.jsonl`
- 中文报告：`data/generated/reports/corpus/corpus_profile_report.md`
- 画像脚本：`src/bgpkb/pipeline/profile_cleaned_corpus.py`
- OCR 评估脚本：`src/bgpkb/pipeline/assess_corpus_ocr_quality.py`

## 运行方式

生成确定性画像：

```bash
PYTHONPATH=src python3 -m bgpkb.pipeline.profile_cleaned_corpus
```

运行稳定 mock 评估：

```bash
PYTHONPATH=src python3 -m bgpkb.pipeline.assess_corpus_ocr_quality --provider mock
```

显式使用 DeepSeek：

```bash
DEEPSEEK_API_KEY=... PYTHONPATH=src python3 -m bgpkb.pipeline.assess_corpus_ocr_quality --provider deepseek
```

运行阶段验收：

```bash
PYTHONPATH=src python3 -m bgpkb.pipeline.run_stage_acceptance --stage phase_a_corpus_profiling_v1
```

## 确定性门禁

以下问题会先写出完整画像和报告，再让命令以非零状态退出：

1. cleaned 正文为空；
2. 出现 `U+FFFD` 替换字符；
3. parsed 或 cleaned 存在重复 `doc_id`；
4. chunk 的 `doc_id` 在 parsed 与 cleaned 中均不存在。

超短、超长、疑似表格、异常符号、空标题、重复标题和阶段缺失保持非阻断告警。

## 模型边界

- cleaned 文档只发送固定的首、中、尾抽样，不发送完整正文。
- 单篇字符、最大文档数、总输入字符和并发均由配置限制。
- API key 只从环境变量读取，不写入数据集、报告或日志。
- 模型只返回风险、理由和人工建议；治理字段由系统生成。
- 缺密钥、请求失败和非法响应不会改变确定性画像。

## 当前基线

- 画像文档：54 条。
- 确定性阻断：0 条。
- 正式 seed/context 通过显式逻辑标识映射纳入画像。
- 超长文档、疑似表格和重复标题仍需按后续任务人工抽样判断阈值是否合适。

## 后续依赖

阶段 B 层级 chunk、阶段 C 分类增强和检索效果调参可以复用本阶段的文档长度、section、chunk 和异常分布，不需要重新建立语料质量统计入口。
