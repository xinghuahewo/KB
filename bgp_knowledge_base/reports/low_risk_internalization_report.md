---
title: "低风险内化报告"
document_type: "项目报告"
purpose: "汇总低风险内化相关的当前结果、统计信息、检查结论和后续处理入口，供阶段复核与交付判断使用。"
scope: "reports 自动或人工整理报告"
status: "现行报告"
last_reviewed: "2026-06-19"
---
# 低风险内化报告

## 范围

本报告记录早期低风险内化阶段的边界和当前状态。早期阶段只处理已解析的 RFC TXT 与官方 HTML 文档；当前流水线已经扩展到可由 `pypdf` 确定性抽取文本的 PDF。

当前已进入确定性文本层的范围：

- `parsed/standards`
- `parsed/data_docs`
- `parsed/papers`
- `parsed/cases`
- `cleaned/standards`
- `cleaned/data_docs`
- `cleaned/papers`
- `cleaned/cases`
- `chunks/*.jsonl`

## 已新增知识范围

| 范围 | 当前结果 |
| --- | ---: |
| DataSource | 9 |
| DataField | 33 |
| RoutingMechanism | 12 |
| Relationship | 106 |

## 新增数据源主题

- CAIDA ASRank。
- RIPEstat Data API。
- PeeringDB。
- ASPA。
- MANRS Network Operators Actions。

## 新增字段主题

- BGP UPDATE 字段：NLRI、withdrawn routes、path attributes。
- BGP 路径属性：ORIGIN、NEXT_HOP、LOCAL_PREF、MED、ATOMIC_AGGREGATE、AGGREGATOR、OTC。
- BGP 会话字段：BGP Identifier、Hold Time、BGP Role。
- RPKI/ROV 字段：VRP prefix、max length、ASN、RPKI-to-Router PDU。
- 数据源字段：ASRank rank、customer cone、AS relationship、RIS RRC、MRT file type、RouteViews endpoint。

## 新增机制主题

- BGP decision process。
- BGP RIB model。
- BGP update and withdrawal propagation。
- BGP Roles 和 OTC route leak prevention。
- RPKI-to-Router delivery。
- ASPA path verification。
- BGPsec path validation。

## 质量状态

`scripts/quality_check.py` 已通过当前流水线校验：

- JSON 错误：0。
- Schema 错误：0。
- 重复实体 ID：0。
- 缺失必填字段：0。
- 未知来源引用：0。
- 孤立关系：0。
- 制品清单不一致：0。

## 当前边界

- 新记录仍保持 `pending`；它们有来源引用，但尚未人工批准。
- PaperMethod 仍低于目标，因为从论文正文抽取结构化方法需要语义判断，按规则跳过。
- 案例观察值已用正则抽取，但案例角色、证据强度和影响范围仍需人工或明确允许的语义流程。
- `bgpshield_2025` 已归档为 `raw/papers/bgpshield_2025.pdf`，对应实体仍需人工审阅后才能批准。
- PeeringDB 的 OpenAPI YAML 已归档并进入 parsed、cleaned 和 chunks 层；后续只在人工核验时判断其内容充分性。
