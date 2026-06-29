#!/usr/bin/env python3
"""生成阶段五确定性 JSON-LD、PROV-O 与 Turtle 标准出口。"""

import json
import re
from collections import defaultdict
from urllib.parse import quote, urlsplit

import yaml

from bgpkb import paths


GENERATED_BY = "src/bgpkb/pipeline/build_standard_exports.py"
CONFIG_PATH = paths.CONFIG_DIR / "standard_exports.yaml"


def build_entity_jsonld(entity, entity_uri, source_uris, config):
    """把一个发布实体映射为不改变主数据的 JSON-LD 记录。"""
    payload = entity.get("entity_payload", {})
    entity_type = entity.get("entity_type") or payload.get("entity_type", "")
    result = {
        "@id": entity_uri,
        "@type": list(config.get("entity_type_mappings", {}).get(entity_type, [f"bgpkb:{entity_type}"])),
        "skos:prefLabel": entity.get("name") or payload.get("name") or entity.get("entity_id", ""),
    }
    aliases = entity.get("aliases") or payload.get("aliases") or []
    if aliases:
        result["skos:altLabel"] = list(aliases)
    definition = entity.get("definition") or payload.get("definition") or payload.get("description")
    if definition:
        result["skos:definition"] = definition
    source_refs = entity.get("source_refs") or payload.get("source_refs") or []
    resolved_sources = [source_uris[source_ref] for source_ref in source_refs if source_ref in source_uris]
    if resolved_sources:
        result["prov:wasDerivedFrom"] = resolved_sources
    if config.get("export_policy", {}).get("preserve_review_status", True):
        review_status = entity.get("review_status") or payload.get("review_status")
        if review_status:
            result["bgpkb:reviewStatus"] = review_status
    lifecycle_status = entity.get("lifecycle_status") or payload.get("lifecycle_status")
    if lifecycle_status:
        result["bgpkb:lifecycleStatus"] = lifecycle_status
    return result


def build_source_jsonld(source, source_uri):
    """把来源目录记录映射为 PROV 与 Schema.org 兼容的 JSON-LD。"""
    result = {
        "@id": source_uri,
        "@type": ["prov:Entity", "schema:CreativeWork"],
        "dcterms:title": source.get("title") or source.get("source_id", ""),
        "dcterms:type": source.get("source_type", ""),
    }
    if source.get("url"):
        result["schema:url"] = source["url"]
    if source.get("review_status"):
        result["bgpkb:reviewStatus"] = source["review_status"]
    return result


def build_provenance_records(entities, entity_uris, source_uris):
    """生成实体到来源的确定性 PROV-O 记录与未解析引用。"""
    records = []
    unresolved = []
    for entity in sorted(entities, key=lambda item: item.get("entity_id", "")):
        entity_id = entity.get("entity_id", "")
        subject_uri = entity_uris.get(entity_id)
        if not subject_uri:
            continue
        for source_ref in sorted(set(entity.get("source_refs", []))):
            object_uri = source_uris.get(source_ref)
            if not object_uri:
                unresolved.append({"entity_id": entity_id, "source_ref": source_ref})
                continue
            records.append({
                "record_id": f"provenance_{entity_id}__{source_ref}",
                "subject_uri": subject_uri,
                "predicate": "prov:wasDerivedFrom",
                "object_uri": object_uri,
                "source_ref": source_ref,
                "generated_by": GENERATED_BY,
            })
    return records, unresolved


def turtle_literal(value):
    """序列化阶段五所需的纯文本 Turtle literal。"""
    if not isinstance(value, str):
        raise ValueError("Turtle v1 literals must be plain strings")
    for character in value:
        if ord(character) < 32 and character not in "\t\n\r":
            raise ValueError(f"Unsupported Turtle control character: U+{ord(character):04X}")
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\t", "\\t")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )
    return f'"{escaped}"'


def validate_turtle_iri(value):
    """校验 v1 范围内可安全放进尖括号的绝对 IRI。"""
    illegal = set('<>"{}|^`\\')
    if (
        not isinstance(value, str)
        or not urlsplit(value).scheme
        or any(character.isspace() or character in illegal or ord(character) < 32 for character in value)
    ):
        raise ValueError(f"Invalid Turtle IRI: {value!r}")


def validate_turtle_curie(value):
    """校验 v1 范围内的紧凑 IRI。"""
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]*:[^\s:]+", value):
        raise ValueError(f"Invalid Turtle CURIE: {value!r}")


def serialize_turtle(triples, namespaces):
    """按三元组排序输出轻量 Turtle；对象显式区分 URI、CURIE 和 literal。"""
    merged_namespaces = {"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"}
    merged_namespaces.update(namespaces)
    lines = [f"@prefix {prefix}: <{uri}> ." for prefix, uri in sorted(merged_namespaces.items())]
    lines.append("")
    for subject, predicate, obj in sorted(triples, key=lambda item: (item[0], item[1], item[2][0], item[2][1])):
        validate_turtle_iri(subject)
        validate_turtle_curie(predicate)
        object_type, value = obj
        if object_type == "uri":
            validate_turtle_iri(value)
            rendered = f"<{value}>"
        elif object_type == "curie":
            validate_turtle_curie(value)
            rendered = value
        elif object_type == "literal":
            rendered = turtle_literal(value)
        else:
            raise ValueError(f"Unsupported Turtle object type: {object_type}")
        lines.append(f"<{subject}> {predicate} {rendered} .")
    return "\n".join(lines).rstrip() + "\n"


def read_jsonl(path):
    """读取 JSONL；空行不产生记录。"""
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path, data):
    """以稳定的 UTF-8 表示写入 JSON。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path, records):
    """以稳定键序写入 JSONL。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        for record in records
    )
    path.write_text(text, encoding="utf-8")


def semantic_uri_maps(records):
    """从既有语义标识表构造实体与来源 URI 映射。"""
    maps = {"entity": {}, "source": {}}
    for record in records:
        resource_type = record.get("resource_type")
        if resource_type in maps and record.get("local_id") and record.get("uri"):
            maps[resource_type][record["local_id"]] = record["uri"]
    return maps


def artifact_uri(path):
    """把项目相对路径转换为稳定且可逆的制品 IRI。"""
    return f"https://w3id.org/bgpkb/resource/artifact/{quote(path, safe='')}"


def build_provenance_chain_records(sources, evidence_records, semantic_records):
    """构建 source→raw→parsed→cleaned→chunk→entity 的 PROV-O 主链。"""
    source_rows = {row.get("source_id"): row for row in sources if row.get("source_id")}
    uri_maps = semantic_uri_maps(semantic_records)
    chunk_uris = {
        row["local_id"]: row["uri"]
        for row in semantic_records
        if row.get("resource_type") == "chunk" and row.get("local_id") and row.get("uri")
    }
    links = set()
    unresolved = []

    def add_link(subject_uri, object_uri, source_ref, stage):
        if subject_uri and object_uri:
            links.add((subject_uri, object_uri, source_ref, stage))

    for evidence in sorted(
        evidence_records,
        key=lambda row: (row.get("entity_id", ""), row.get("source_id", ""), row.get("evidence_id", "")),
    ):
        entity_id = evidence.get("entity_id", "")
        source_id = evidence.get("source_id", "")
        source_uri = uri_maps["source"].get(source_id)
        entity_uri = uri_maps["entity"].get(entity_id)
        source = source_rows.get(source_id, {})
        if not source_uri:
            unresolved.append({"entity_id": entity_id, "source_ref": source_id, "stage": "source"})
            continue
        if not entity_uri:
            unresolved.append({"entity_id": entity_id, "source_ref": source_id, "stage": "entity"})

        parent_uri = source_uri
        raw_path = source.get("path", "")
        if raw_path:
            raw_uri = artifact_uri(raw_path)
            add_link(raw_uri, parent_uri, source_id, "raw")
            parent_uri = raw_uri
        parsed_path = evidence.get("parsed_path", "")
        if parsed_path:
            parsed_uri = artifact_uri(parsed_path)
            add_link(parsed_uri, parent_uri, source_id, "parsed")
            parent_uri = parsed_uri
        cleaned_path = evidence.get("cleaned_path", "")
        if cleaned_path:
            cleaned_uri = artifact_uri(cleaned_path)
            add_link(cleaned_uri, parent_uri, source_id, "cleaned")
            parent_uri = cleaned_uri

        for chunk_id in sorted(set(evidence.get("chunk_sample_ids", []))):
            chunk_uri = chunk_uris.get(chunk_id)
            if not chunk_uri:
                unresolved.append({
                    "entity_id": entity_id,
                    "source_ref": source_id,
                    "stage": "chunk",
                    "chunk_id": chunk_id,
                })
                continue
            add_link(chunk_uri, parent_uri, source_id, "chunk")
            add_link(entity_uri, chunk_uri, source_id, "entity")

    records = []
    for index, (subject_uri, object_uri, source_ref, stage) in enumerate(sorted(links), start=1):
        records.append({
            "record_id": f"provenance_chain_{index:06d}",
            "subject_uri": subject_uri,
            "predicate": "prov:wasDerivedFrom",
            "object_uri": object_uri,
            "source_ref": source_ref,
            "generated_by": GENERATED_BY,
        })
    unresolved.sort(key=lambda row: tuple(str(row.get(key, "")) for key in ("entity_id", "source_ref", "stage", "chunk_id")))
    return records, unresolved


def evidence_source_refs(evidence_records):
    """按实体汇总证据表中实际存在的来源引用。"""
    refs = defaultdict(set)
    for record in evidence_records:
        if record.get("entity_id") and record.get("source_id"):
            refs[record["entity_id"]].add(record["source_id"])
    return {entity_id: sorted(source_ids) for entity_id, source_ids in refs.items()}


def build_turtle_sample(entity_graph, limit, namespaces):
    """从排序后的 JSON-LD 实体生成有上限的确定性 Turtle 样例。"""
    triples = []
    for entity in entity_graph[:limit]:
        subject = entity["@id"]
        for entity_type in entity.get("@type", []):
            triples.append((subject, "rdf:type", ("curie", entity_type)))
        if entity.get("skos:prefLabel"):
            triples.append((subject, "skos:prefLabel", ("literal", entity["skos:prefLabel"])))
        if entity.get("skos:definition"):
            triples.append((subject, "skos:definition", ("literal", entity["skos:definition"])))
        for source_uri in entity.get("prov:wasDerivedFrom", []):
            triples.append((subject, "prov:wasDerivedFrom", ("uri", source_uri)))
    return serialize_turtle(triples, namespaces)


def build_report(entity_count, source_count, provenance_count, unresolved, sample_count):
    """生成中文标准化出口摘要。"""
    lines = [
        "# 标准化出口报告",
        "",
        "本报告记录从既有发布目录与证据索引确定性派生的标准格式出口；原始发布 JSONL 未被修改。",
        "",
        "## 生成结果",
        "",
        f"- 实体 JSON-LD：{entity_count} 条",
        f"- 来源 JSON-LD：{source_count} 条",
        f"- PROV-O 来源关系：{provenance_count} 条",
        f"- Turtle 样例实体：{sample_count} 条",
        f"- 未解析来源引用：{len(unresolved)} 条",
        "",
        "## 输出文件",
        "",
        "- `data/published/entity_catalog.jsonld`",
        "- `data/published/source_catalog.jsonld`",
        "- `data/published/provenance_map.jsonl`",
        "- `data/published/standard_exports/bgp_knowledge_sample.ttl`",
        "",
        "## 边界",
        "",
        "这些文件是兼容 JSON-LD、PROV-O、SKOS 与 Turtle 的派生出口，不替代现有主发布格式，也不改变复核状态。",
    ]
    if unresolved:
        lines.extend(["", "## 未解析引用", ""])
        lines.extend(
            f"- `{item['entity_id']}` → `{item['source_ref']}`"
            for item in unresolved
        )
    return "\n".join(lines).rstrip() + "\n"


def main():
    """从现有发布文件生成全部标准出口。"""
    root = paths.PROJECT_ROOT
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    outputs = config["outputs"]

    entities = read_jsonl(root / "data/published/entity_catalog.jsonl")
    sources = read_jsonl(root / "data/published/source_catalog.jsonl")
    semantic_records = read_jsonl(root / "data/published/semantic_id_map.jsonl")
    evidence = read_jsonl(root / "data/derived/datasets/entity_source_evidence.jsonl")

    uri_maps = semantic_uri_maps(semantic_records)
    entity_uris = uri_maps["entity"]
    source_uris = uri_maps["source"]
    refs_by_entity = evidence_source_refs(evidence)
    statuses = set(config.get("export_policy", {}).get("include_review_statuses", []))

    included_entities = []
    for entity in entities:
        if statuses and entity.get("review_status") not in statuses:
            continue
        entity_id = entity.get("entity_id", "")
        if entity_id not in entity_uris:
            continue
        enriched = dict(entity)
        enriched["source_refs"] = refs_by_entity.get(entity_id, [])
        included_entities.append(enriched)

    included_sources = [
        source for source in sources
        if source.get("source_id") in source_uris
        and (not statuses or source.get("review_status") in statuses)
    ]

    entity_graph = sorted(
        (
            build_entity_jsonld(entity, entity_uris[entity["entity_id"]], source_uris, config)
            for entity in included_entities
        ),
        key=lambda item: item["@id"],
    )
    source_graph = sorted(
        (
            build_source_jsonld(source, source_uris[source["source_id"]])
            for source in included_sources
        ),
        key=lambda item: item["@id"],
    )
    provenance, unresolved = build_provenance_chain_records(included_sources, evidence, semantic_records)

    context = dict(sorted(config["namespaces"].items()))
    write_json(root / outputs["entity_catalog"], {"@context": context, "@graph": entity_graph})
    write_json(root / outputs["source_catalog"], {"@context": context, "@graph": source_graph})
    write_jsonl(root / outputs["provenance_map"], provenance)

    sample_limit = config.get("export_policy", {}).get("turtle_sample_limit", 25)
    turtle_path = root / outputs["turtle_sample"]
    turtle_path.parent.mkdir(parents=True, exist_ok=True)
    turtle_path.write_text(
        build_turtle_sample(entity_graph, sample_limit, config["namespaces"]),
        encoding="utf-8",
    )

    report_path = root / outputs["report"]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        build_report(len(entity_graph), len(source_graph), len(provenance), unresolved, min(sample_limit, len(entity_graph))),
        encoding="utf-8",
    )

    for output_key in ("entity_catalog", "source_catalog", "provenance_map", "turtle_sample", "report"):
        print(f"Wrote {outputs[output_key]}")


if __name__ == "__main__":
    main()
