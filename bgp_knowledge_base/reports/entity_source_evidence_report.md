# 实体来源证据索引报告

## 范围

本报告从 `entities/*.jsonl`、来源处理状态、chunks 和案例观察值机械生成实体到来源的证据索引。该步骤不判断来源是否真正支持实体定义，也不改变审核状态，只列出人工复核可打开的证据位置。

## 摘要

- 证据索引记录数：246
- JSONL 输出：`datasets/entity_source_evidence.jsonl`
- CSV 输出：`datasets/entity_source_evidence.csv`
- chunk_sample_ids 每条最多保留：20
- chunk_sample_ids 选择规则：优先保留与实体 ID、名称、事件类型、AS 编号、prefix 等字段机械匹配的 chunk；不足时按文档顺序补齐。
- 非 manual note 且 chunk_count=0 的记录数：0
- 非 manual note 且缺失 parsed_path 的记录数：0

## 按实体类型统计

- AnomalyType：24
- BGPConcept：75
- Case：11
- DataField：53
- DataSource：20
- EvidenceTemplate：21
- FalsePositivePattern：10
- PaperMethod：6
- RoutingMechanism：26

## 按来源状态统计

- complete_deterministic：168
- manual_note：78

## 按来源类型统计

- case_report：4
- data_doc：49
- manual_note：78
- paper：20
- standard：87
- tool_doc：8

## 需要注意的机械缺口

- 无
