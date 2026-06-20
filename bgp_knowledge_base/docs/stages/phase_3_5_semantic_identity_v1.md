---
title: "阶段三点五：语义标识前置 v1"
document_type: "阶段说明"
purpose: "交付小步较优解，为 RAG 和标准化出口冻结 bgpkb 命名空间、URI 规则和 JSON-LD context。"
scope: "阶段三之后、阶段四之前的轻量语义标识层"
status: "已交付"
last_reviewed: "2026-06-19"
---
# 阶段三点五：语义标识前置 v1

## 1. 目标

本阶段执行阶段方案矩阵中的“小步较优解”：在不改变主数据格式的前提下，新增可复跑的语义标识层。

## 2. 交付物

- `docs/governance/semantic_identity_v1.md`
- `config/semantic_identity.yaml`
- `scripts/build_semantic_identity.py`
- `published/jsonld_context.json`
- `published/semantic_id_map.jsonl`
- `reports/semantic_identity_report.md`
- `tests/test_semantic_identity.py`

## 3. 验收标准

- 每个实体、source、chunk 都能生成稳定 URI。
- RAG context pack 可以引用稳定 `@id`。
- JSON-LD context 已登记 `bgpkb:`、SKOS 和 PROV-O 前缀。
- 字段映射草案已覆盖 `id`、`name`、`source_refs`、`generated_by`、`review_status` 等核心字段。
- 现有 JSONL、CSV、SQLite 主格式保持不变。

## 4. 下游依赖

阶段四 RAG PoC 可直接使用 `published/semantic_id_map.jsonl` 给实体、来源和 chunk 绑定 `@id`。

阶段五标准化出口可在 `published/jsonld_context.json` 的基础上继续扩展 SKOS、PROV-O 和 RDF 导出。
