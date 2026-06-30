#!/usr/bin/env python3
import hashlib
import json
from collections import Counter
from pathlib import Path

from bgpkb import paths
from urllib.parse import quote

import yaml


ROOT = paths.PROJECT_ROOT
CONFIG = paths.CONFIG_DIR / "semantic_identity.yaml"
PUBLISHED_DIR = paths.PUBLISHED_DIR
DATASET_DIR = paths.DATASETS_DIR
RELATIONSHIP_FILE = paths.RELATIONSHIPS_DIR / "relationships.jsonl"


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def load_config():
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def uri_for(config, resource_type, local_id):
    pattern = config["uri_patterns"][resource_type]
    return pattern.format(id=quote(str(local_id), safe="_-.~"))


def curie_for(config, resource_type, local_id):
    return f"{config['namespace']['prefix']}:{resource_type}/{local_id}"


def relationship_local_id(record):
    canonical = "|".join([
        record.get("src_id", ""),
        record.get("relation", ""),
        record.get("dst_id", ""),
    ])
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"relationship_{digest}"


def display_name(entity):
    payload = entity.get("entity_payload", {})
    return (
        entity.get("name")
        or payload.get("name")
        or payload.get("paper")
        or payload.get("applies_to")
        or entity.get("entity_id", "")
    )


def base_record(config, resource_type, local_id, label="", source_path="", source_ref=""):
    return {
        "semantic_id": f"{resource_type}:{local_id}",
        "resource_type": resource_type,
        "local_id": local_id,
        "uri": uri_for(config, resource_type, local_id),
        "curie": curie_for(config, resource_type, local_id),
        "jsonld_type": config["jsonld_types"][resource_type],
        "label": label,
        "source_path": source_path,
        "source_ref": source_ref,
        "generated_by": "src/bgpkb/pipeline/build_semantic_identity.py",
    }


def build_context(config):
    namespace = config["namespace"]
    return {
        "@context": {
            "bgpkb": namespace["vocab_uri"],
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "prov": "http://www.w3.org/ns/prov#",
            "schema": "https://schema.org/",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "id": "@id",
            "type": "@type",
            "entity_id": "bgpkb:entityId",
            "entity_type": "bgpkb:entityType",
            "name": "skos:prefLabel",
            "aliases": {"@id": "skos:altLabel", "@container": "@set"},
            "definition": "skos:definition",
            "description": "skos:definition",
            "source_refs": {"@id": "prov:wasDerivedFrom", "@container": "@set"},
            "generated_by": "prov:wasGeneratedBy",
            "review_status": "bgpkb:reviewStatus",
            "lifecycle_status": "bgpkb:lifecycleStatus",
            "chunk_id": "bgpkb:chunkId",
            "source_ref": "prov:atLocation",
        }
    }


def build_id_map(config):
    records = []

    for entity in load_jsonl(PUBLISHED_DIR / "entity_catalog.jsonl"):
        local_id = entity.get("entity_id", "")
        if not local_id:
            continue
        records.append(base_record(
            config,
            "entity",
            local_id,
            label=display_name(entity),
            source_path=entity.get("entity_file", ""),
        ))

    for source in load_jsonl(PUBLISHED_DIR / "source_catalog.jsonl"):
        local_id = source.get("source_id", "")
        if not local_id:
            continue
        records.append(base_record(
            config,
            "source",
            local_id,
            label=source.get("title", "") or local_id,
            source_path=source.get("path", ""),
        ))

    for chunk in load_jsonl(PUBLISHED_DIR / "chunk_catalog.jsonl"):
        local_id = chunk.get("chunk_id", "")
        if not local_id:
            continue
        records.append(base_record(
            config,
            "chunk",
            local_id,
            label=chunk.get("title", "") or local_id,
            source_path=chunk.get("chunk_file", ""),
            source_ref=chunk.get("source_ref", ""),
        ))

    for rel in load_jsonl(RELATIONSHIP_FILE):
        local_id = relationship_local_id(rel)
        label = f"{rel.get('src_id', '')} {rel.get('relation', '')} {rel.get('dst_id', '')}".strip()
        item = base_record(config, "relationship", local_id, label=label)
        item["canonical_key"] = "|".join([rel.get("src_id", ""), rel.get("relation", ""), rel.get("dst_id", "")])
        records.append(item)

    for evidence in load_jsonl(DATASET_DIR / "entity_source_evidence.jsonl"):
        local_id = evidence.get("evidence_id", "")
        if not local_id:
            continue
        label = f"{evidence.get('entity_id', '')} <- {evidence.get('source_id', '')}".strip()
        records.append(base_record(
            config,
            "evidence",
            local_id,
            label=label,
            source_path=evidence.get("source_path", ""),
        ))

    records.sort(key=lambda item: (item["resource_type"], item["local_id"]))
    return records


def duplicate_values(values):
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def build_report(config, context, records):
    by_type = Counter(record["resource_type"] for record in records)
    duplicate_uris = duplicate_values(record["uri"] for record in records)
    duplicate_semantic_ids = duplicate_values(record["semantic_id"] for record in records)
    boundary = config.get("downstream_boundary", {})

    lines = [
        "# 语义标识前置报告",
        "",
        "## 范围",
        "",
        "本报告描述阶段三点五新增的轻量语义标识层。该步骤只读取现有发布目录、关系和证据索引，生成派生出口，不改变主 JSONL、CSV 或 SQLite 格式。",
        "",
        "## 命名空间与 URI 规则",
        "",
        f"- 前缀：`{config['namespace']['prefix']}`",
        f"- 词表命名空间：`{config['namespace']['vocab_uri']}`",
        f"- 资源基础 URI：`{config['namespace']['base_uri']}`",
        "",
        "| 类型 | URI 规则 |",
        "| --- | --- |",
    ]
    for resource_type, pattern in config["uri_patterns"].items():
        lines.append(f"| `{resource_type}` | `{pattern}` |")

    lines.extend([
        "",
        "## JSON-LD Context",
        "",
        "- 输出：`data/published/jsonld_context.json`",
        f"- context 前缀数：{len(context['@context'])}",
        "- 已包含：`bgpkb`、`skos`、`prov`、`schema`、`xsd`。",
        "",
        "## 稳定 ID 映射",
        "",
        "- 输出：`data/published/semantic_id_map.jsonl`",
        f"- 映射总数：{len(records)}",
        f"- 重复 URI 数：{len(duplicate_uris)}",
        f"- 重复 semantic_id 数：{len(duplicate_semantic_ids)}",
        "",
        "| 类型 | 数量 |",
        "| --- | ---: |",
    ])
    for resource_type, count in sorted(by_type.items()):
        lines.append(f"| `{resource_type}` | {count} |")

    lines.extend([
        "",
        "## 字段映射草案",
        "",
        "| 字段 | JSON-LD | SKOS | PROV-O | 说明 |",
        "| --- | --- | --- | --- | --- |",
    ])
    for field, mapping in config["field_mappings"].items():
        lines.append(
            f"| `{field}` | {mapping.get('jsonld', '')} | {mapping.get('skos', '')} | {mapping.get('prov', '')} | {mapping.get('description', '')} |"
        )

    lines.extend([
        "",
        "## 下游使用边界",
        "",
        f"- 保留主格式：{boundary.get('preserves_primary_formats')}",
        f"- 改写现有 JSONL：{boundary.get('changes_existing_jsonl')}",
        f"- 批准 pending 实体：{boundary.get('approves_pending_entities')}",
        "",
        "适用下游：",
        "",
    ])
    for item in boundary.get("intended_for", []):
        lines.append(f"- {item}")

    if duplicate_uris or duplicate_semantic_ids:
        lines.extend(["", "## 需要处理的问题", ""])
        for uri in duplicate_uris[:20]:
            lines.append(f"- 重复 URI：`{uri}`")
        for semantic_id in duplicate_semantic_ids[:20]:
            lines.append(f"- 重复 semantic_id：`{semantic_id}`")
    else:
        lines.extend(["", "## 需要处理的问题", "", "- 未发现重复 URI 或重复 semantic_id。"])

    return "\n".join(lines) + "\n"


def append_readme_section(config, counts):
    readme = PUBLISHED_DIR / "README.md"
    if not readme.exists():
        return
    text = readme.read_text(encoding="utf-8")
    marker = "## Semantic Identity"
    if marker in text:
        text = text.split(marker, 1)[0].rstrip() + "\n\n"
    section = [
        marker,
        "",
        "阶段三点五新增轻量语义标识派生产物：",
        "",
        f"- `jsonld_context.json`：JSON-LD `@context`，登记 `{config['namespace']['prefix']}:`、SKOS 和 PROV-O 前缀。",
        f"- `semantic_id_map.jsonl`：实体、来源、chunk、关系和证据的稳定 URI 映射，共 {sum(counts.values())} 条。",
        "",
    ]
    readme.write_text(text.rstrip() + "\n\n" + "\n".join(section), encoding="utf-8")


def main():
    config = load_config()
    context = build_context(config)
    records = build_id_map(config)
    counts = Counter(record["resource_type"] for record in records)

    context_path = ROOT / config["generated_policy"]["context_path"]
    id_map_path = ROOT / config["generated_policy"]["id_map_path"]
    report_path = ROOT / config["generated_policy"]["report_path"]

    write_json(context_path, context)
    write_jsonl(id_map_path, records)
    report_path.write_text(build_report(config, context, records), encoding="utf-8")
    append_readme_section(config, counts)

    print(f"Wrote {context_path.relative_to(ROOT)}")
    print(f"Wrote {id_map_path.relative_to(ROOT)}")
    print(f"Wrote {report_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
