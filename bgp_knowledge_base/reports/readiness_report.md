# 知识库就绪度报告

## 范围

本报告把 `context.md` 中的目标产物映射到当前确定性证据。它不做语义判断、不调用 LLM、不自动批准实体。

## 摘要

- 总体状态：ready_deterministic
- 已达到：13
- 需人工或语义流程：1
- 未完成：0
- JSON 输出：`published/readiness_summary.json`

## 目标产物映射

| 目标产物 | 状态 | 数量 | 证据 | 说明 |
| --- | --- | ---: | --- | --- |
| BGP 原始资料库 | achieved | 54 | `inventory/sources.csv`<br>`raw/`<br>`datasets/source_processing_status.jsonl` | 来源层无缺口；不做全量下载。 |
| BGP 清洗文本库 | achieved | 54 | `cleaned/`<br>`reports/parse_report.md` | TXT/HTML/YAML/PDF 可抽取文本已进入 cleaned 层。 |
| BGP 知识片段库 | achieved | 2037 | `chunks/`<br>`published/chunk_catalog.jsonl` | chunk 目录和发布 catalog 已生成。 |
| BGP 概念实体库 | achieved | 31 | `entities/bgp_concepts.jsonl`<br>`published/entity_catalog.jsonl` | 实体保持 pending，等待人工来源复核。 |
| BGP 异常类型库 | achieved | 8 | `entities/anomaly_types.jsonl`<br>`entities/evidence_templates.jsonl` | 异常类型与证据模板已建立。 |
| BGP 数据源说明库 | achieved | 9 | `entities/data_sources.jsonl`<br>`published/source_catalog.jsonl` | 覆盖 RouteViews、RIPE RIS、BGPStream、CAIDA、RIPEstat、PeeringDB 等来源。 |
| BGP 证据字段库 | achieved | 32 | `entities/data_fields.jsonl`<br>`entities/evidence_templates.jsonl` | 字段和证据模板已结构化，仍需人工批准。 |
| BGP 案例库 | achieved | 5 | `entities/cases.jsonl`<br>`datasets/case_observations.jsonl`<br>`reports/case_observation_guides/` | 案例观察值已机械抽取；角色、影响范围、证据强度仍需人工或语义流程。 |
| BGP 术语表 | achieved | 112 | `datasets/glossary.jsonl`<br>`published/bgp_knowledge_base.sqlite` | 术语表从实体机械派生，不自动润色或补同义词。 |
| BGP 关系表 | achieved | 106 | `relationships/relationships.jsonl`<br>`published/relationship_adjacency.json` | 关系表已达 MVP 目标；不从正文自动推断新语义关系。 |
| 质量检查报告 | achieved | 53 | `reports/quality_report.md`<br>`reports/published_integrity_report.md` | 发布完整性 gate 通过，质量问题计数由 quality_report 记录。 |
| 可查询发布包 | achieved | 112 | `published/`<br>`published/bgp_knowledge_base.sqlite`<br>`scripts/query_knowledge_base.py` | 发布包含 JSONL/JSON/SQLite/查询 CLI/完整性摘要。 |
| 语义/LLM 跳过边界 | achieved | 2 | `reports/llm_processing_skip_report.md`<br>`datasets/next_action_queue.jsonl` | 按用户要求，PaperMethod 扩展和案例语义核验跳过并记录。 |
| 人工复核边界 | requires_human_or_semantic | 112 | `datasets/human_review_workbook.jsonl`<br>`reports/human_review_guides/` | pending 实体需要人工来源核验；当前不自动批准。 |
