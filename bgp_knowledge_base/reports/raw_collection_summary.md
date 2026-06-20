---
title: "原始资料采集摘要"
document_type: "项目报告"
purpose: "汇总原始资料采集摘要相关的当前结果、统计信息、检查结论和后续处理入口，供阶段复核与交付判断使用。"
scope: "reports 自动或人工整理报告"
status: "现行报告"
last_reviewed: "2026-06-19"
---
# 原始资料采集摘要

## 日期

2026-06-08

## 范围

本步骤只采集原始资料，不解析、不清洗、不切分 chunk、不抽取实体、不构建关系，也不批准知识记录。

## 结果

- 采集脚本下载目标数：53
- 成功下载数：53
- 重试后仍失败数：0
- `raw/` 下现存原始文件数：53
- inventory 登记来源数：54

## 已采集层级

| 原始资料目录 | 数量 | 格式 |
| --- | ---: | --- |
| `raw/standards` | 11 | TXT |
| `raw/data_docs` | 14 | HTML / PDF / YAML |
| `raw/tools_docs` | 2 | HTML |
| `raw/papers` | 13 | PDF / HTML |
| `raw/cases` | 13 | HTML / PDF |

## 缺失原始来源

- 无。`bgpshield_2025` 已通过 arXiv 单源回填归档为 `raw/papers/bgpshield_2025.pdf`；`rfc2622`、`rfc3912`、`rfc9082`、`rfc9083` 已按“不全量下载”原则单条补充归档。

## 日志

逐来源采集状态见 `reports/raw_collection_report.csv`。

## 后续状态

当前流水线已经在采集结果基础上完成 TXT、HTML、YAML 和可抽取文本 PDF 的 parsed、cleaned 与 chunk 生成；最新覆盖以 `reports/coverage_report.md` 和 `reports/quality_report.md` 为准。
