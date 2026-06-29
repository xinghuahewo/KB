---
title: "语义标识前置 v1"
document_type: "治理规范"
purpose: "在 RAG 和标准化出口前冻结 bgpkb 命名空间、URI 规则、JSON-LD context 和字段映射草案。"
scope: "实体、来源、chunk、关系和证据的轻量语义标识层"
status: "现行规范"
last_reviewed: "2026-06-19"
---
# 语义标识前置 v1

## 1. 目标

阶段三点五不迁移现有 JSONL、CSV、SQLite 主格式，只新增一个可复跑的派生语义标识层。

该层解决三个问题：

- RAG context pack 可以使用稳定 `@id`，避免临时字段名进入接口。
- 阶段五标准化出口可以沿用同一套 `bgpkb:` 命名空间和 URI 规则。
- 字段到 JSON-LD、SKOS、PROV-O 的初步映射有机器可读来源。

## 2. 命名空间

项目命名空间前缀为 `bgpkb`。

- 词表命名空间：`https://w3id.org/bgpkb/vocab#`
- 资源 URI 基础路径：`https://w3id.org/bgpkb/resource/`

当前阶段只承诺项目内稳定，不承诺外部永久解析服务已经上线。

## 3. URI 规则

URI 规则由 `metadata/config/semantic_identity.yaml` 维护，并由 `src/bgpkb/pipeline/build_semantic_identity.py` 生成映射。

| 类型 | URI 形态 |
| --- | --- |
| entity | `https://w3id.org/bgpkb/resource/entity/{id}` |
| source | `https://w3id.org/bgpkb/resource/source/{id}` |
| chunk | `https://w3id.org/bgpkb/resource/chunk/{id}` |
| relationship | `https://w3id.org/bgpkb/resource/relationship/{id}` |
| evidence | `https://w3id.org/bgpkb/resource/evidence/{id}` |

关系没有主数据 ID 时，派生层用 `src_id|relation|dst_id` 的规范串生成短哈希 ID。该 ID 不反写到主关系文件。

## 4. 派生产物

- `data/published/jsonld_context.json`：JSON-LD `@context`。
- `data/published/semantic_id_map.jsonl`：实体、来源、chunk、关系和证据的本地 ID 到 URI 映射。
- `data/generated/reports/publishing/semantic_identity_report.md`：人读验收报告。

## 5. 边界

- 不改变 `data/knowledge/entities/*.jsonl`、`data/corpus/chunks/*.jsonl`、`data/knowledge/relationships/*.jsonl` 的字段。
- 不把 pending 实体升级为 approved。
- 不做 RDF/OWL 全量建模。
- 不替代阶段五标准化出口，只为其提供稳定底座。
