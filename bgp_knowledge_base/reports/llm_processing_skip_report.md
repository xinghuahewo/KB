# LLM 介入处理跳过记录

## 原则

当前阶段只做 BGP 知识库数据底座。凡是处理文档时需要 LLM 介入才能完成的步骤，本阶段跳过，只记录待处理项。

不跳过的内容：

- 按文件格式进行确定性解析。
- 文本清洗。
- 按固定规则切分 chunks。
- JSONL / CSV / Markdown 报告生成。
- JSONL 结构和来源引用质量检查。

跳过的内容：

- 从论文正文中抽取结构化 PaperMethod。
- 从案例正文中抽取结构化 Case 字段，例如相关 AS、受影响 prefix、证据链和影响范围。
- 从正文中做语义关系抽取。
- 自动把 `pending` 记录升级为 `approved`。
- 需要理解、归纳、判断或改写文档语义的自动处理。

## 本轮已跳过事项

| 跳过项 | 原因 | 后续处理方式 |
| --- | --- | --- |
| 论文来源的 PaperMethod 结构化抽取 | 需要对论文正文做问题、输入、过程、输出等语义归纳 | 保留 parsed、cleaned、paper chunks，等待人工或明确允许的抽取流程 |
| 13 个案例来源的结构化 Case 扩展 | AS 角色、prefix 归属、证据强度和影响范围需要语义判断 | 已生成规则观察值 `datasets/case_observations.*`；结构化实体写入仍等待人工审阅 |
| source-derived chunks 到实体关系的自动推断 | 需要语义匹配和关系判断 | 暂不扩展 relationships/relationships.jsonl |
| pending 到 approved 的状态升级 | 需要来源核验和人工确认 | 维持 pending |
| 基于制品清单判断主题覆盖充分性 | 文件大小、行数和 SHA-256 只能证明制品存在且未漂移，不能判断内容是否覆盖充分 | 已生成 `datasets/artifact_manifest.*`；主题充分性仍等待人工或明确允许的语义流程 |
| 术语表别名补全和定义润色 | 判断同义词、缩写边界和更优定义需要语义判断 | 已生成机械派生的 `datasets/glossary.*`；新增别名和定义改写等待人工或明确允许的语义流程 |
| 根据复核队列自动审批实体 | 判断实体定义是否准确、证据是否充分需要人工或语义判断 | 已生成 `datasets/entity_review_queue.*` 供人工复核；实体仍保持 `pending` |
| 判断已归档来源是否足以支持实体批准 | 来源已完成确定性归档、解析、清洗和切分，但“内容是否充分支持实体字段”需要语义判断 | 已生成 `datasets/entity_review_queue.*`、`datasets/entity_review_packets.*` 和人工复核指南；实体仍保持 `pending` |

## 行动队列中的策略跳过项

- 跳过记录数：2

- `action_skipped_paper_method_expansion`：从论文正文扩展结构化方法需要语义判断或 LLM 介入，按用户要求跳过。
- `action_skipped_case_semantic_review`：事件角色、证据强度和影响范围判断需要语义流程或 LLM 介入，按用户要求跳过。

## 已保留的中间产物

- `parsed/papers`：HTML/PDF 论文来源解析结果。
- `cleaned/papers`：HTML/PDF 论文来源清洗文本。
- `chunks/paper_chunks.jsonl`：论文来源 chunks。
- `parsed/cases`：HTML/PDF 案例来源解析结果。
- `cleaned/cases`：HTML/PDF 案例来源清洗文本。
- `chunks/case_chunks.jsonl`：案例来源 chunks。
- `parsed/data_docs/peeringdb_api_docs.json`：PeeringDB OpenAPI YAML 的解析结果。
- `cleaned/data_docs/peeringdb_api_docs.md`：PeeringDB OpenAPI YAML 的清洗文本。
- `datasets/case_observations.jsonl`：正则抽取的案例观察值。
- `datasets/case_observations.csv`：案例观察值 CSV 版本。
- `datasets/source_processing_status.jsonl`：按来源汇总的确定性处理状态。
- `datasets/source_processing_status.csv`：来源处理状态 CSV 版本。
- `datasets/source_gap_queue.jsonl`：未完成来源的缺口队列。
- `datasets/source_gap_queue.csv`：来源缺口队列 CSV 版本。
- `datasets/entity_review_queue.jsonl`：待人工复核实体队列。
- `datasets/entity_review_queue.csv`：实体复核队列 CSV 版本。
- `datasets/glossary.jsonl`：从实体机械派生的术语表。
- `datasets/glossary.csv`：术语表 CSV 版本。
- `datasets/artifact_manifest.jsonl`：文件级制品清单。
- `datasets/artifact_manifest.csv`：制品清单 CSV 版本。
