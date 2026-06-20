# 语义标识前置报告

## 范围

本报告描述阶段三点五新增的轻量语义标识层。该步骤只读取现有发布目录、关系和证据索引，生成派生出口，不改变主 JSONL、CSV 或 SQLite 格式。

## 命名空间与 URI 规则

- 前缀：`bgpkb`
- 词表命名空间：`https://w3id.org/bgpkb/vocab#`
- 资源基础 URI：`https://w3id.org/bgpkb/resource/`

| 类型 | URI 规则 |
| --- | --- |
| `entity` | `https://w3id.org/bgpkb/resource/entity/{id}` |
| `source` | `https://w3id.org/bgpkb/resource/source/{id}` |
| `chunk` | `https://w3id.org/bgpkb/resource/chunk/{id}` |
| `relationship` | `https://w3id.org/bgpkb/resource/relationship/{id}` |
| `evidence` | `https://w3id.org/bgpkb/resource/evidence/{id}` |

## JSON-LD Context

- 输出：`published/jsonld_context.json`
- context 前缀数：19
- 已包含：`bgpkb`、`skos`、`prov`、`schema`、`xsd`。

## 稳定 ID 映射

- 输出：`published/semantic_id_map.jsonl`
- 映射总数：2555
- 重复 URI 数：0
- 重复 semantic_id 数：0

| 类型 | 数量 |
| --- | ---: |
| `chunk` | 2037 |
| `entity` | 112 |
| `evidence` | 246 |
| `relationship` | 106 |
| `source` | 54 |

## 字段映射草案

| 字段 | JSON-LD | SKOS | PROV-O | 说明 |
| --- | --- | --- | --- | --- |
| `id` | @id |  |  | 本地稳定标识映射为 JSON-LD @id。 |
| `entity_type` | @type |  |  | 实体类型映射为 JSON-LD @type 或 bgpkb 自定义类型。 |
| `name` |  | skos:prefLabel |  | 名称映射为 SKOS 首选标签。 |
| `aliases` |  | skos:altLabel |  | 别名映射为 SKOS 备用标签集合。 |
| `definition` |  | skos:definition |  | 定义映射为 SKOS 定义。 |
| `description` |  | skos:definition |  | 描述类字段在轻量出口中先映射为 SKOS 定义。 |
| `source_refs` |  |  | prov:wasDerivedFrom | 来源引用映射为 PROV-O 派生来源。 |
| `generated_by` |  |  | prov:wasGeneratedBy | 生成脚本映射为 PROV-O 生成活动来源。 |
| `review_status` | bgpkb:reviewStatus |  |  | 复核状态保留为项目自定义治理字段。 |
| `lifecycle_status` | bgpkb:lifecycleStatus |  |  | 生命周期状态保留为项目自定义治理字段。 |
| `chunk_id` | bgpkb:chunkId |  |  | chunk 本地 ID 映射为项目自定义字段。 |
| `source_ref` |  |  | prov:atLocation | chunk 或证据中的原始来源位置映射为 PROV-O 位置提示。 |

## 下游使用边界

- 保留主格式：True
- 改写现有 JSONL：False
- 批准 pending 实体：False

适用下游：

- 阶段四 RAG context pack 稳定引用 @id。
- 阶段五 JSON-LD、SKOS、PROV-O 和 RDF 出口继续扩展。

## 需要处理的问题

- 未发现重复 URI 或重复 semantic_id。
