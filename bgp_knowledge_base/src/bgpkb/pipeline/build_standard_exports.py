#!/usr/bin/env python3
"""生成阶段五确定性 JSON-LD、PROV-O 与 Turtle 标准出口。"""

import json
import re
import copy
from collections import defaultdict
from urllib.parse import quote, urlsplit

import yaml

from bgpkb import paths


GENERATED_BY = "src/bgpkb/pipeline/build_standard_exports.py"
CONFIG_PATH = paths.CONFIG_DIR / "standard_exports.yaml"


def apply_approved_mappings(config, approved_mappings):
    """把人工批准映射叠加到配置副本，不修改原始配置。"""
    effective = copy.deepcopy(config)
    relation_mappings = effective.setdefault("relation_mappings", {})
    for mapping in approved_mappings:
        if mapping.get("candidate_type") == "relation":
            relation_mappings[mapping["local_value"]] = mapping["suggested_mapping"]
    return effective
GENERATION_ACTIVITY_URI = "https://w3id.org/bgpkb/resource/activity/standard_exports_v1"
PROV_ACTIVITY_URI = "http://www.w3.org/ns/prov#Activity"


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
        result["prov:wasDerivedFrom"] = [{"@id": uri} for uri in resolved_sources]
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
        result["schema:url"] = {"@id": source["url"]}
    if source.get("review_status"):
        result["bgpkb:reviewStatus"] = source["review_status"]
    return result


def node_reference_ids(value):
    """验证并提取 JSON-LD 节点引用，避免把 IRI 误写成字符串 literal。"""
    if not isinstance(value, list) or any(
        not isinstance(item, dict) or set(item) != {"@id"} or not isinstance(item["@id"], str)
        for item in value
    ):
        raise ValueError("JSON-LD node references must be objects containing only @id")
    return [item["@id"] for item in value]


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


def validate_turtle_curie(value, namespaces=None):
    """校验 v1 范围内的紧凑 IRI。"""
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]*:[^\s:]+", value):
        raise ValueError(f"Invalid Turtle CURIE: {value!r}")
    if namespaces is not None and value.split(":", 1)[0] not in namespaces:
        raise ValueError(f"Unknown Turtle CURIE prefix: {value!r}")


def serialize_turtle(triples, namespaces):
    """按三元组排序输出轻量 Turtle；对象显式区分 URI、CURIE 和 literal。"""
    merged_namespaces = {"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"}
    merged_namespaces.update(namespaces)
    lines = [f"@prefix {prefix}: <{uri}> ." for prefix, uri in sorted(merged_namespaces.items())]
    lines.append("")
    for subject, predicate, obj in sorted(triples, key=lambda item: (item[0], item[1], item[2][0], item[2][1])):
        validate_turtle_iri(subject)
        validate_turtle_curie(predicate, merged_namespaces)
        object_type, value = obj
        if object_type == "uri":
            validate_turtle_iri(value)
            rendered = f"<{value}>"
        elif object_type == "curie":
            validate_turtle_curie(value, merged_namespaces)
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
    maps = {"entity": {}, "source": {}, "evidence": {}, "chunk": {}}
    for record in records:
        resource_type = record.get("resource_type")
        if resource_type in maps and record.get("local_id") and record.get("uri"):
            maps[resource_type][record["local_id"]] = record["uri"]
    return maps


def artifact_uri(path):
    """把项目相对路径转换为稳定且可逆的制品 IRI。"""
    return f"https://w3id.org/bgpkb/resource/artifact/{quote(path, safe='')}"


def build_provenance_chain_records(
    sources, evidence_records, semantic_records, allowed_entity_ids=None, allowed_source_ids=None,
):
    """构建 source→制品→chunk→evidence→entity 与生成 Activity 的 PROV-O 主链。"""
    source_rows = {row.get("source_id"): row for row in sources if row.get("source_id")}
    uri_maps = semantic_uri_maps(semantic_records)
    chunk_uris = uri_maps["chunk"]
    evidence_uris = uri_maps["evidence"]
    links = set()
    unresolved = []

    def add_link(subject_uri, predicate, object_uri, source_ref, stage):
        if subject_uri and object_uri:
            links.add((subject_uri, predicate, object_uri, source_ref, stage))

    add_link(GENERATION_ACTIVITY_URI, "rdf:type", PROV_ACTIVITY_URI, "", "activity_type")

    for evidence in sorted(
        evidence_records,
        key=lambda row: (row.get("entity_id", ""), row.get("source_id", ""), row.get("evidence_id", "")),
    ):
        entity_id = evidence.get("entity_id", "")
        source_id = evidence.get("source_id", "")
        if allowed_entity_ids is not None and entity_id not in allowed_entity_ids:
            continue
        if allowed_source_ids is not None and source_id not in allowed_source_ids:
            continue
        evidence_id = evidence.get("evidence_id", "")
        source_uri = uri_maps["source"].get(source_id)
        entity_uri = uri_maps["entity"].get(entity_id)
        evidence_uri = evidence_uris.get(evidence_id)
        source = source_rows.get(source_id, {})
        if not source_uri:
            unresolved.append({"entity_id": entity_id, "source_ref": source_id, "stage": "source"})
            continue
        if not entity_uri:
            unresolved.append({"entity_id": entity_id, "source_ref": source_id, "stage": "entity"})
        if not evidence_uri:
            unresolved.append({"entity_id": entity_id, "source_ref": source_id, "stage": "evidence"})

        parent_uri = source_uri
        raw_path = source.get("path", "")
        if raw_path:
            raw_uri = artifact_uri(raw_path)
            add_link(raw_uri, "prov:wasDerivedFrom", parent_uri, source_id, "raw")
            parent_uri = raw_uri
        parsed_path = evidence.get("parsed_path", "")
        if parsed_path:
            parsed_uri = artifact_uri(parsed_path)
            add_link(parsed_uri, "prov:wasDerivedFrom", parent_uri, source_id, "parsed")
            parent_uri = parsed_uri
        cleaned_path = evidence.get("cleaned_path", "")
        if cleaned_path:
            cleaned_uri = artifact_uri(cleaned_path)
            add_link(cleaned_uri, "prov:wasDerivedFrom", parent_uri, source_id, "cleaned")
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
            add_link(chunk_uri, "prov:wasDerivedFrom", parent_uri, source_id, "chunk")
            add_link(evidence_uri, "prov:wasDerivedFrom", chunk_uri, source_id, "evidence")
        if evidence_uri and not evidence.get("chunk_sample_ids"):
            add_link(evidence_uri, "prov:wasDerivedFrom", parent_uri, source_id, "evidence")
        add_link(evidence_uri, "prov:wasGeneratedBy", GENERATION_ACTIVITY_URI, source_id, "activity")
        add_link(entity_uri, "prov:wasDerivedFrom", evidence_uri, source_id, "entity")

    records = []
    for index, (subject_uri, predicate, object_uri, source_ref, stage) in enumerate(sorted(links), start=1):
        records.append({
            "record_id": f"provenance_chain_{index:06d}",
            "subject_uri": subject_uri,
            "predicate": predicate,
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


def build_relationship_triples(relationships, semantic_records, config, allowed_entity_ids=None):
    """把全部关系映射为 Turtle 三元组，并记录受控 fallback 与阻塞项。"""
    entity_uris = semantic_uri_maps(semantic_records)["entity"]
    mappings = config.get("relation_mappings", {})
    namespaces = config.get("namespaces", {})
    fallback_prefix = config.get("export_policy", {}).get("unmapped_relation_prefix", "")
    triples = []
    fallback_counts = defaultdict(int)
    unsafe = []

    for row in sorted(
        relationships,
        key=lambda item: (item.get("src_id", ""), item.get("relation", ""), item.get("dst_id", "")),
    ):
        if allowed_entity_ids is not None and (
            row.get("src_id") not in allowed_entity_ids or row.get("dst_id") not in allowed_entity_ids
        ):
            continue
        relation = row.get("relation", "")
        predicate = mappings.get(relation)
        used_fallback = False
        if not predicate:
            if not re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*", relation) or fallback_prefix not in namespaces:
                unsafe.append({"relation": relation, "reason": "无法构造受控 camelCase fallback"})
                continue
            parts = relation.split("_")
            local_name = parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])
            predicate = f"{fallback_prefix}:{local_name}"
            used_fallback = True
        try:
            validate_turtle_curie(predicate, namespaces)
        except ValueError as exc:
            unsafe.append({"relation": relation, "reason": str(exc)})
            continue

        subject_uri = entity_uris.get(row.get("src_id", ""))
        object_uri = entity_uris.get(row.get("dst_id", ""))
        if not subject_uri or not object_uri:
            unsafe.append({
                "relation": relation,
                "reason": f"关系端点缺少 URI：{row.get('src_id', '')} → {row.get('dst_id', '')}",
            })
            continue
        triples.append((subject_uri, predicate, ("uri", object_uri)))
        if used_fallback:
            fallback_counts[(relation, predicate)] += 1

    fallbacks = [
        {"relation": relation, "predicate": predicate, "count": count}
        for (relation, predicate), count in sorted(fallback_counts.items())
    ]
    unsafe.sort(key=lambda item: (item["relation"], item["reason"]))
    return sorted(triples), fallbacks, unsafe


def build_turtle_sample(entity_graph, limit, namespaces, relationship_triples=None):
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
        for source_reference in entity.get("prov:wasDerivedFrom", []):
            triples.append((subject, "prov:wasDerivedFrom", ("uri", source_reference["@id"])))
    triples.extend(relationship_triples or [])
    return serialize_turtle(triples, namespaces)


def build_diagnostics(
    entities, sources, semantic_records, relationships, entity_graph, provenance, config,
    identity_errors=None, allowed_entity_ids=None,
):
    """统计标准词汇覆盖、未映射项以及 URI/来源解析完整性。"""
    total = len(entity_graph)

    def prefix_coverage(prefix):
        covered = 0
        marker = f"{prefix}:"
        for row in entity_graph:
            values = row.get("@type", [])
            if any(key.startswith(marker) for key in row if not key.startswith("@")) or any(
                isinstance(value, str) and value.startswith(marker) for value in values
            ):
                covered += 1
        return {"count": covered, "percent": (covered * 100 / total) if total else 0.0}

    mapped_entity_fields = {
        "entity_id", "entity_type", "name", "aliases", "review_status", "source_refs",
        "entity_payload", "definition", "description", "lifecycle_status",
    }
    mapped_payload_fields = {
        "id", "entity_type", "name", "aliases", "review_status", "source_refs",
        "definition", "description", "lifecycle_status",
    }
    mapped_source_fields = {"source_id", "title", "url", "source_type", "review_status"}
    unmapped_fields = set()
    for row in entities:
        unmapped_fields.update(f"entity.{key}" for key in row if key not in mapped_entity_fields)
        payload = row.get("entity_payload", {})
        unmapped_fields.update(f"entity_payload.{key}" for key in payload if key not in mapped_payload_fields)
    for row in sources:
        unmapped_fields.update(f"source.{key}" for key in row if key not in mapped_source_fields)

    _, fallback_relations, unsafe_relations = build_relationship_triples(
        relationships, semantic_records, config, allowed_entity_ids=allowed_entity_ids
    )
    by_uri = defaultdict(list)
    for row in semantic_records:
        if row.get("uri"):
            by_uri[row["uri"]].append(f"{row.get('resource_type', '')}:{row.get('local_id', '')}")
    duplicate_uris = [
        {"uri": uri, "resources": sorted(resources)}
        for uri, resources in sorted(by_uri.items()) if len(resources) > 1
    ]

    error_markers = ("error", "failed", "missing")
    source_errors = []
    for row in sources:
        for field in ("parsed_status", "cleaned_status", "processing_status"):
            value = str(row.get(field, "")).lower()
            if any(marker in value for marker in error_markers):
                source_errors.append({"source_id": row.get("source_id", ""), "field": field, "status": value})

    return {
        "coverage": {prefix: prefix_coverage(prefix) for prefix in ("skos", "prov", "bgpkb")},
        "unmapped_fields": sorted(unmapped_fields),
        "fallback_relations": fallback_relations,
        "unsafe_relations": unsafe_relations,
        "duplicate_uris": duplicate_uris,
        "source_errors": source_errors,
        "identity_errors": sorted(
            identity_errors or [], key=lambda item: (item["resource_type"], item["local_id"])
        ),
        "prov_predicate_count": sum(row.get("predicate", "").startswith("prov:") for row in provenance),
    }


def build_report(entity_count, source_count, provenance_count, unresolved, sample_count, diagnostics=None):
    """生成中文标准化出口摘要。"""
    diagnostics = diagnostics or {
        "coverage": {prefix: {"count": 0, "percent": 0.0} for prefix in ("skos", "prov", "bgpkb")},
        "unmapped_fields": [], "fallback_relations": [], "unsafe_relations": [],
        "duplicate_uris": [], "source_errors": [], "identity_errors": [],
    }
    blocked = bool(
        unresolved or diagnostics["duplicate_uris"] or diagnostics["source_errors"]
        or diagnostics["unsafe_relations"] or diagnostics["identity_errors"]
    )
    conclusion = "阻塞" if blocked else "通过"
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
        f"- 结论：{conclusion}",
        "",
        "## 标准覆盖率",
        "",
        f"- SKOS 覆盖率：{diagnostics['coverage']['skos']['percent']:.2f}%（{diagnostics['coverage']['skos']['count']}/{entity_count}）",
        f"- PROV-O 覆盖率：{diagnostics['coverage']['prov']['percent']:.2f}%（{diagnostics['coverage']['prov']['count']}/{entity_count}）",
        f"- bgpkb 覆盖率：{diagnostics['coverage']['bgpkb']['percent']:.2f}%（{diagnostics['coverage']['bgpkb']['count']}/{entity_count}）",
        "",
        "## 映射与完整性",
        "",
        f"- 未映射字段：{len(diagnostics['unmapped_fields'])} 个",
        f"- 自定义回退关系：{len(diagnostics['fallback_relations'])} 个",
        f"- 无法安全回退关系：{len(diagnostics['unsafe_relations'])} 条",
        f"- 重复 URI：{len(diagnostics['duplicate_uris'])} 组",
        f"- 来源解析错误：{len(diagnostics['source_errors'])} 条",
        f"- 语义 URI 缺失：{len(diagnostics['identity_errors'])} 条",
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
    if diagnostics["unmapped_fields"]:
        lines.extend(["", "### 未映射字段明细", ""])
        lines.extend(f"- `{item}`" for item in diagnostics["unmapped_fields"])
    if diagnostics["fallback_relations"]:
        lines.extend(["", "### 自定义回退关系明细", ""])
        lines.extend(
            f"- `{item['relation']}` → `{item['predicate']}`（{item['count']} 条）"
            for item in diagnostics["fallback_relations"]
        )
    if diagnostics["unsafe_relations"]:
        lines.extend(["", "### 无法安全回退关系明细", ""])
        lines.extend(
            f"- `{item['relation']}`：{item['reason']}"
            for item in diagnostics["unsafe_relations"]
        )
    if diagnostics["duplicate_uris"]:
        lines.extend(["", "### 重复 URI 明细", ""])
        lines.extend(f"- `{item['uri']}`：{', '.join(item['resources'])}" for item in diagnostics["duplicate_uris"])
    if diagnostics["source_errors"]:
        lines.extend(["", "### 来源解析错误明细", ""])
        lines.extend(
            f"- `{item['source_id']}` `{item['field']}` = `{item['status']}`"
            for item in diagnostics["source_errors"]
        )
    if diagnostics["identity_errors"]:
        lines.extend(["", "### 语义 URI 缺失明细", ""])
        lines.extend(
            f"- `{item['resource_type']}`：`{item['local_id']}`"
            for item in diagnostics["identity_errors"]
        )
    if unresolved:
        lines.extend(["", "## 未解析引用", ""])
        for item in unresolved:
            detail = f"- `{item['entity_id']}` → `{item['source_ref']}`；阶段：`{item.get('stage', 'source')}`"
            if item.get("chunk_id"):
                detail += f"；chunk：`{item['chunk_id']}`"
            lines.append(detail)
    return "\n".join(lines).rstrip() + "\n"


def generate_standard_exports(root, config):
    """生成标准出口；有未解析引用时仅写阻塞报告并返回非零。"""
    outputs = config["outputs"]
    approved_path = root / outputs.get("approved_mappings", "data/derived/datasets/approved_standard_mappings.jsonl")
    approved_mappings = read_jsonl(approved_path) if approved_path.exists() else []
    config = apply_approved_mappings(config, approved_mappings)

    entities = read_jsonl(root / "data/published/entity_catalog.jsonl")
    sources = read_jsonl(root / "data/published/source_catalog.jsonl")
    semantic_records = read_jsonl(root / "data/published/semantic_id_map.jsonl")
    evidence = read_jsonl(root / "data/derived/datasets/entity_source_evidence.jsonl")
    relationships = read_jsonl(root / "data/knowledge/relationships/relationships.jsonl")

    uri_maps = semantic_uri_maps(semantic_records)
    entity_uris = uri_maps["entity"]
    source_uris = uri_maps["source"]
    refs_by_entity = evidence_source_refs(evidence)
    statuses = set(config.get("export_policy", {}).get("include_review_statuses", []))

    eligible_entities = [
        entity for entity in entities if not statuses or entity.get("review_status") in statuses
    ]
    eligible_sources = [
        source for source in sources if not statuses or source.get("review_status") in statuses
    ]
    identity_errors = [
        {"resource_type": "entity", "local_id": entity.get("entity_id", "")}
        for entity in eligible_entities if entity.get("entity_id", "") not in entity_uris
    ] + [
        {"resource_type": "source", "local_id": source.get("source_id", "")}
        for source in eligible_sources if source.get("source_id", "") not in source_uris
    ]

    included_entity_ids = {
        entity.get("entity_id", "") for entity in eligible_entities if entity.get("entity_id", "") in entity_uris
    }
    included_source_ids = {
        source.get("source_id", "") for source in eligible_sources if source.get("source_id", "") in source_uris
    }
    included_source_uris = {source_id: source_uris[source_id] for source_id in included_source_ids}

    included_entities = []
    for entity in eligible_entities:
        entity_id = entity.get("entity_id", "")
        if entity_id not in included_entity_ids:
            continue
        enriched = dict(entity)
        enriched["source_refs"] = refs_by_entity.get(entity_id, [])
        included_entities.append(enriched)

    included_sources = [source for source in eligible_sources if source.get("source_id") in included_source_ids]

    entity_graph = sorted(
        (
            build_entity_jsonld(entity, entity_uris[entity["entity_id"]], included_source_uris, config)
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
    provenance, unresolved = build_provenance_chain_records(
        included_sources, evidence, semantic_records,
        allowed_entity_ids=included_entity_ids, allowed_source_ids=included_source_ids,
    )
    relationship_triples, _, _ = build_relationship_triples(
        relationships, semantic_records, config, allowed_entity_ids=included_entity_ids
    )

    context = dict(sorted(config["namespaces"].items()))
    sample_limit = config.get("export_policy", {}).get("turtle_sample_limit", 25)
    diagnostics = build_diagnostics(
        included_entities, included_sources, semantic_records, relationships, entity_graph, provenance, config,
        identity_errors=identity_errors, allowed_entity_ids=included_entity_ids,
    )
    report_path = root / outputs["report"]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        build_report(
            len(entity_graph), len(source_graph), len(provenance), unresolved,
            min(sample_limit, len(entity_graph)), diagnostics,
        ),
        encoding="utf-8",
    )
    blocking_count = (
        len(unresolved) + len(diagnostics["duplicate_uris"]) + len(diagnostics["source_errors"])
        + len(diagnostics["unsafe_relations"]) + len(diagnostics["identity_errors"])
    )
    if blocking_count:
        print(f"Blocked: {blocking_count} standard export integrity issues")
        print(f"Wrote {outputs['report']}")
        return 1

    write_json(root / outputs["entity_catalog"], {"@context": context, "@graph": entity_graph})
    write_json(root / outputs["source_catalog"], {"@context": context, "@graph": source_graph})
    write_jsonl(root / outputs["provenance_map"], provenance)
    turtle_path = root / outputs["turtle_sample"]
    turtle_path.parent.mkdir(parents=True, exist_ok=True)
    turtle_path.write_text(
        build_turtle_sample(entity_graph, sample_limit, config["namespaces"], relationship_triples), encoding="utf-8"
    )

    for output_key in ("entity_catalog", "source_catalog", "provenance_map", "turtle_sample", "report"):
        print(f"Wrote {outputs[output_key]}")
    return 0


def main():
    """从现有发布文件生成全部标准出口。"""
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    return generate_standard_exports(paths.PROJECT_ROOT, config)


if __name__ == "__main__":
    raise SystemExit(main())
