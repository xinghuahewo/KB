---
title: "Docling 私有知识清洗 v2"
status: "delivered"
---

# Docling 私有知识清洗 v2

## 交付范围

- 私有离线 GPU Docling 运行环境及锁定模型证据。
- Canonical Block v2、结构化表格、bbox、阅读顺序与自适应 OCR 证据。
- 可恢复批处理、显式 fallback、逐次 transformation 和审核隔离。
- 54 篇语料 resolved migration、人工高风险验收、发布门禁与 v1 回滚。

## 当前验收

- 54/54 文档达到 approved 终态并通过逐文档迁移门禁。
- 23 篇保留 Docling 主解析结果；31 篇因 HTML/YAML/Markdown 正文覆盖不足采用已审核 legacy-preservation fallback。
- 标题层级 F1 为 98.65%，阅读顺序与表格结构准确率为 100%，OCR CER 为 0%。
- v1 parsed、cleaned、chunks、发布 manifest 和回滚入口继续保留。

## 运行入口

```bash
python3 -m bgpkb.pipeline.resolve_cleaning_v2_migration
python3 -m bgpkb.pipeline.build_cleaning_v2_migration
python3 -m bgpkb.pipeline.build_cleaning_v2_acceptance_report
python3 -m bgpkb.pipeline.build_cleaning_v2_release_gate
```

发布切换必须在 `cleaning_v2_release_gate.json` 通过后显式执行，禁止静默切换。
