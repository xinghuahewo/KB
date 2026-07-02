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

## 切换前验收证据

- 本地全量回归：244 项通过，1 项上游 Starlette 弃用警告，无失败。
- 离线 GPU 容器：在 `NVIDIA TITAN RTX 24 GB`、驱动 `570.133.07` 上以 `--network none` 运行；Docling 健康预检通过，5 个锁定模型哈希全部匹配。
- 全量迁移：54/54 文档通过，隔离数为 0，发布门禁阻断项为 0。
- 数据质量：Schema 错误、制品清单大小不一致和 SHA-256 不一致均为 0。
- 敏感信息检查：对 v2 Block、Markdown、chunk、迁移差异和人工决策扫描本机绝对路径、私钥头、AWS/OpenAI/GitHub 密钥模式，命中数为 0。

## 发布与回滚验收证据

- 发布指针已显式切换到 v2，主发布 chunk 目录、RAG 索引和 SQLite 均从 59,341 个 approved v2 chunk 重建。
- 发布 manifest 记录 `corpus_version=v2`、v2 输入快照和 Canonical Block v2 权威路径。
- 既有人工复核证据仍引用 v1 chunk ID；它们被隔离到 SQLite `historical_evidence_chunks` 表，未混入活动检索 chunk。
- 已执行 v2 → v1 真实回滚，v1 下游以 2,037 个 chunk 重建成功，v2 manifest 和诊断证据保留。
- 回滚演练后已恢复 v2；指针历史完整记录 v2 切换、v1 回滚和 v2 恢复，SQLite 外键检查错误为 0。

## 最终验收

- 全量回归：246 项通过，1 项上游 Starlette 弃用警告，无失败。
- OpenSpec：`openspec validate docling-private-cleaning-v2 --strict` 通过。
- 阶段验收：`docling_private_cleaning_v2` 结论为 `pass`。
- 质量门禁：Schema 错误、清洗 v2 阻断项、制品清单大小不一致和 SHA-256 不一致均为 0。
- 发布状态：活动指针、发布 manifest 和 SQLite 均为 v2，SQLite 外键检查错误为 0。
- 工作树检查：变更范围仅包含本阶段的发布切换、下游兼容、测试、规格任务和机器生成制品；`git diff --check` 通过。
