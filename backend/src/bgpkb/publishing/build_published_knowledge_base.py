#!/usr/bin/env python3
import csv
import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import jsonschema

from bgpkb import paths
from bgpkb.ingestion.cleaning_v2.release import resolve_release


ROOT = paths.PROJECT_ROOT
PUBLISHED_DIR = paths.PUBLISHED_DIR
REPORT = paths.report_path("published_knowledge_base_report")

ENTITY_DIR = paths.ENTITIES_DIR
DATASET_DIR = paths.DATASETS_DIR
RELATIONSHIP_FILE = paths.RELATIONSHIPS_DIR / "relationships.jsonl"
SOURCE_INVENTORY = paths.INVENTORY_DIR / "sources.csv"

ENTITY_CATALOG = PUBLISHED_DIR / "entity_catalog.jsonl"
SOURCE_CATALOG = PUBLISHED_DIR / "source_catalog.jsonl"
CHUNK_CATALOG = PUBLISHED_DIR / "chunk_catalog.jsonl"
RELATIONSHIP_ADJACENCY = PUBLISHED_DIR / "relationship_adjacency.json"
LEXICAL_INDEX = PUBLISHED_DIR / "lexical_index.json"
MANIFEST = PUBLISHED_DIR / "manifest.json"
README = PUBLISHED_DIR / "README.md"

TOKEN_RE = re.compile(r"[A-Za-z0-9_./:-]{2,}")


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def load_sources():
    with SOURCE_INVENTORY.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _atomic_text(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def write_jsonl(path, records):
    _atomic_text(
        path,
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
    )


def write_json(path, payload):
    _atomic_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def entity_file_for(path):
    return path.relative_to(ROOT).as_posix()


def build_entity_catalog():
    evidence_by_entity = defaultdict(list)
    for record in load_jsonl(DATASET_DIR / "entity_source_evidence.jsonl"):
        evidence_by_entity[record.get("entity_id", "")].append(record)

    packet_by_entity = {
        record.get("entity_id"): record
        for record in load_jsonl(DATASET_DIR / "entity_review_packets.jsonl")
        if record.get("entity_id")
    }

    records = []
    for path in sorted(ENTITY_DIR.glob("*.jsonl")):
        for entity in load_jsonl(path):
            entity_id = entity.get("id", "")
            evidence = evidence_by_entity.get(entity_id, [])
            packet = packet_by_entity.get(entity_id, {})
            source_refs = entity.get("source_refs", [])
            records.append({
                "entity_id": entity_id,
                "entity_type": entity.get("entity_type", ""),
                "name": entity.get("name") or entity.get("paper") or entity.get("applies_to") or entity_id,
                "aliases": entity.get("aliases", []),
                "category": entity.get("category", ""),
                "review_status": entity.get("review_status", ""),
                "source_refs": source_refs,
                "source_ref_count": len(source_refs),
                "evidence_record_count": len(evidence),
                "chunk_count": sum(item.get("chunk_count", 0) for item in evidence),
                "case_observation_count": sum(item.get("case_observation_count", 0) for item in evidence),
                "review_bucket": packet.get("review_bucket", ""),
                "entity_file": entity_file_for(path),
                "entity_payload": entity,
            })
    records.sort(key=lambda item: (item["entity_type"], item["name"].lower(), item["entity_id"]))
    return records


def build_source_catalog():
    status_by_source = {
        record.get("source_id"): record
        for record in load_jsonl(DATASET_DIR / "source_processing_status.jsonl")
        if record.get("source_id")
    }
    records = []
    for source in load_sources():
        source_id = source.get("source_id", "")
        status = status_by_source.get(source_id, {})
        records.append({
            "source_id": source_id,
            "title": source.get("title", ""),
            "source_type": source.get("source_type", ""),
            "domain": source.get("domain", ""),
            "authority": source.get("authority", ""),
            "organization": source.get("organization", ""),
            "publish_date": source.get("publish_date", ""),
            "language": source.get("language", ""),
            "path": source.get("path", ""),
            "url": source.get("url", ""),
            "trust_level": source.get("trust_level", ""),
            "review_status": source.get("review_status", ""),
            "processing_status": status.get("processing_status", ""),
            "parsed_status": status.get("parsed_status", ""),
            "cleaned_status": status.get("cleaned_status", ""),
            "chunk_count": status.get("chunk_count", 0),
            "case_observation_count": status.get("case_observation_count", 0),
        })
    records.sort(key=lambda item: (item["source_type"], item["source_id"]))
    return records


def resolve_active_release(pointer_path=None, *, project_root=ROOT):
    pointer_path = Path(pointer_path or (paths.CONFIG_DIR / "corpus_release_pointer.json"))
    manifest = resolve_release(pointer_path)
    project_root = Path(project_root).resolve()
    chunks_path = Path(manifest["chunks"])
    if not chunks_path.is_absolute():
        chunks_path = project_root / chunks_path
    chunks_path = chunks_path.resolve()
    if not chunks_path.is_relative_to(project_root):
        raise ValueError("发布语料 chunks 路径必须位于项目目录内")
    if not chunks_path.is_dir():
        raise FileNotFoundError(f"发布语料 chunks 目录不存在: {chunks_path}")
    return {"manifest": manifest, "chunks_path": chunks_path}


def _validate_resolved_v2_chunks(chunks, sections):
    section_schema = json.loads(
        (paths.SCHEMAS_DIR / "section_catalog.schema.json").read_text(encoding="utf-8")
    )
    section_by_id = {}
    sections_by_doc = defaultdict(list)
    for section in sections:
        try:
            jsonschema.validate(section, section_schema)
        except jsonschema.ValidationError as exc:
            raise ValueError(f"section schema 错误 {exc.json_path}: {exc.message}") from exc
        section_id = section.get("section_id")
        if not section_id or section_id in section_by_id:
            raise ValueError(f"重复或缺失 section_id: {section_id}")
        section_by_id[section_id] = section
        sections_by_doc[section["doc_id"]].append(section)
    for section_id, section in section_by_id.items():
        doc_id = section["doc_id"]
        parent_id = section["parent_section_id"]
        if parent_id:
            parent = section_by_id.get(parent_id)
            if parent is None:
                raise ValueError(f"section parent 不存在: {section_id} -> {parent_id}")
            if parent["doc_id"] != doc_id:
                raise ValueError(f"section parent 跨文档: {section_id} -> {parent_id}")
            if section_id not in parent["child_section_ids"]:
                raise ValueError(f"section parent/child 不互反: {section_id} -> {parent_id}")
        for child_id in section["child_section_ids"]:
            child = section_by_id.get(child_id)
            if child is None:
                raise ValueError(f"section child 不存在: {section_id} -> {child_id}")
            if child["doc_id"] != doc_id:
                raise ValueError(f"section child 跨文档: {section_id} -> {child_id}")
            if child["parent_section_id"] != section_id:
                raise ValueError(f"section child/parent 不互反: {section_id} -> {child_id}")
    for doc_id, doc_sections in sections_by_doc.items():
        ordered = sorted(
            doc_sections, key=lambda section: (section["section_order"], section["section_id"])
        )
        for index, section in enumerate(ordered):
            expected_previous = ordered[index - 1]["section_id"] if index else None
            expected_next = ordered[index + 1]["section_id"] if index + 1 < len(ordered) else None
            if (
                section["previous_section_id"] != expected_previous
                or section["next_section_id"] != expected_next
            ):
                raise ValueError(f"section 邻接不连续或跨文档: {doc_id} -> {section['section_id']}")
    chunk_ids = set()
    by_parent = defaultdict(list)
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        if not chunk_id or chunk_id in chunk_ids:
            raise ValueError(f"重复 chunk_id: {chunk_id}")
        chunk_ids.add(chunk_id)
        if chunk.get("schema_version") != "chunk_v2_hierarchical":
            raise ValueError(
                f"resolved chunk schema_version 必须为 chunk_v2_hierarchical: {chunk_id}"
            )
        required = (
            "schema_version", "parent_section_id", "chunk_order", "previous_chunk_id",
            "next_chunk_id", "hierarchy_status", "source_block_ids", "section_path",
        )
        missing = [field for field in required if field not in chunk]
        if missing:
            raise ValueError(f"resolved chunk 缺少层级字段 {missing}: {chunk_id}")
        if not chunk.get("source_ref") or not chunk.get("source_block_ids"):
            raise ValueError(f"resolved chunk source_ref/source_block_ids 来源追溯为空: {chunk_id}")
        section = section_by_id.get(chunk["parent_section_id"])
        if section is None:
            raise ValueError(f"parent section 不存在: {chunk_id}")
        if section.get("doc_id") != chunk.get("doc_id"):
            raise ValueError(f"chunk 与 parent section 跨文档: {chunk_id}")
        by_parent[chunk["parent_section_id"]].append(chunk)
    for section_id, section in section_by_id.items():
        expected_child_ids = {chunk["chunk_id"] for chunk in by_parent.get(section_id, [])}
        actual_child_ids = set(section["child_chunk_ids"])
        if actual_child_ids != expected_child_ids:
            raise ValueError(
                f"section.child_chunk_ids 与 resolved chunks 不一致: {section_id}; "
                f"缺失={sorted(expected_child_ids - actual_child_ids)}; "
                f"多余={sorted(actual_child_ids - expected_child_ids)}"
            )
    for parent_id, siblings in by_parent.items():
        orders = [chunk.get("chunk_order") for chunk in siblings]
        if len(set(orders)) != len(orders) or sorted(orders) != list(range(len(siblings))):
            raise ValueError(f"父 section {parent_id} 的 chunk_order 不连续或重复")
        ordered = sorted(siblings, key=lambda chunk: chunk["chunk_order"])
        for index, chunk in enumerate(ordered):
            previous = ordered[index - 1]["chunk_id"] if index else None
            following = ordered[index + 1]["chunk_id"] if index + 1 < len(ordered) else None
            if chunk["previous_chunk_id"] != previous or chunk["next_chunk_id"] != following:
                raise ValueError(f"chunk 邻接不互反或越过父级: {chunk['chunk_id']}")


def build_chunk_catalog(
    chunk_dir, *, corpus_version, section_records=None, section_catalog_path=None,
    diagnostics=None, project_root=ROOT, sources_by_doc=None,
):
    if corpus_version not in {"v1", "v2"}:
        raise ValueError(f"未知 corpus_version: {corpus_version}")
    raw_records = []
    sources_by_doc = sources_by_doc or {}
    project_root = Path(project_root).resolve()
    for path in sorted(Path(chunk_dir).glob("*.jsonl")):
        chunk_file = path.resolve().relative_to(project_root).as_posix()
        for chunk in load_jsonl(path):
            raw_records.append((chunk, chunk_file))

    isolated_reasons = Counter()
    if corpus_version == "v2":
        chunk_schema = json.loads(
            (paths.SCHEMAS_DIR / "chunk.schema.json").read_text(encoding="utf-8")
        )
        resolved = []
        resolved_records = []
        for chunk, chunk_file in raw_records:
            try:
                jsonschema.validate(chunk, chunk_schema)
            except jsonschema.ValidationError as exc:
                raise ValueError(f"chunk schema 错误 {exc.json_path}: {exc.message}") from exc
            hierarchy_status = chunk.get("hierarchy_status")
            if hierarchy_status == "unresolved":
                isolated_reasons["hierarchy_status_unresolved"] += 1
                continue
            if hierarchy_status != "resolved":
                raise ValueError(
                    f"v2 chunk hierarchy_status 必须为 resolved 或 unresolved: "
                    f"{chunk.get('chunk_id', '<missing>')} -> {hierarchy_status!r}"
                )
            resolved.append(chunk)
            resolved_records.append((chunk, chunk_file))
        if section_records is None:
            section_records = load_jsonl(Path(section_catalog_path)) if section_catalog_path else []
        _validate_resolved_v2_chunks(resolved, section_records)
        raw_records = resolved_records

    records = []
    for chunk, chunk_file in raw_records:
        content = chunk.get("content", "")
        source = sources_by_doc.get(chunk.get("doc_id", ""), {})
        source_type = chunk.get("source_type", "")
        if source_type in {"", "document"}:
            source_type = source.get("source_type", source_type)
        record = {
                "chunk_id": chunk.get("chunk_id", ""),
                "doc_id": chunk.get("doc_id", ""),
                "title": chunk.get("title", "") or source.get("title", ""),
                "source_type": source_type,
                "chunk_type": chunk.get("chunk_type", ""),
                "topics": chunk.get("topics", []),
                "section_path": chunk.get("section_path", []),
                "source_ref": chunk.get("source_ref", ""),
                "language": chunk.get("language", "") or source.get("language", ""),
                "review_status": chunk.get("review_status", ""),
                "content_chars": len(content),
                "content_preview": " ".join(content.split())[:240],
                "chunk_file": chunk_file,
        }
        if corpus_version == "v2":
            for field in (
                "schema_version", "parent_section_id", "chunk_order", "previous_chunk_id",
                "next_chunk_id", "hierarchy_status", "source_block_ids",
            ):
                record[field] = chunk[field]
        records.append(record)
    records.sort(key=lambda item: (item["doc_id"], item["chunk_id"]))
    if diagnostics is not None:
        diagnostics.update({
            "published_resolved_count": len(records) if corpus_version == "v2" else 0,
            "isolated_unresolved_count": sum(isolated_reasons.values()),
            "isolated_reasons": dict(sorted(isolated_reasons.items())),
            "hierarchy_integrity": "pass" if corpus_version == "v2" else "not_applicable",
        })
    return records


def build_relationship_adjacency(entity_catalog):
    entity_ids = {record["entity_id"] for record in entity_catalog}
    outgoing = defaultdict(list)
    incoming = defaultdict(list)
    relation_counts = Counter()
    relationships = load_jsonl(RELATIONSHIP_FILE)
    for rel in relationships:
        src = rel.get("src_id", "")
        dst = rel.get("dst_id", "")
        item = {
            "relation": rel.get("relation", ""),
            "peer_id": dst,
            "peer_type": rel.get("dst_type", ""),
            "source_refs": rel.get("source_refs", []),
            "confidence": rel.get("confidence"),
        }
        outgoing[src].append(item)
        incoming[dst].append({
            "relation": rel.get("relation", ""),
            "peer_id": src,
            "peer_type": rel.get("src_type", ""),
            "source_refs": rel.get("source_refs", []),
            "confidence": rel.get("confidence"),
        })
        relation_counts[rel.get("relation", "")] += 1

    nodes = {}
    for entity in entity_catalog:
        entity_id = entity["entity_id"]
        nodes[entity_id] = {
            "entity_id": entity_id,
            "entity_type": entity["entity_type"],
            "name": entity["name"],
            "outgoing": sorted(outgoing.get(entity_id, []), key=lambda item: (item["relation"], item["peer_id"])),
            "incoming": sorted(incoming.get(entity_id, []), key=lambda item: (item["relation"], item["peer_id"])),
        }

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "node_count": len(nodes),
        "relationship_count": len(relationships),
        "relation_counts": dict(sorted(relation_counts.items())),
        "orphan_relationship_entity_ids": sorted(
            (
                {rel.get("src_id", "") for rel in relationships}
                | {rel.get("dst_id", "") for rel in relationships}
            )
            - entity_ids
        ),
        "nodes": nodes,
    }


def add_index_entry(index, token, kind, identifier):
    if not token:
        return
    bucket = index.setdefault(token.lower(), {"entities": set(), "chunks": set(), "sources": set()})
    bucket[kind].add(identifier)


def tokenize(*values):
    tokens = []
    for value in values:
        if isinstance(value, list):
            tokens.extend(tokenize(*value))
        elif isinstance(value, str):
            tokens.extend(TOKEN_RE.findall(value))
    return tokens


def build_lexical_index(entity_catalog, source_catalog, chunk_catalog):
    index = {}
    for entity in entity_catalog:
        entity_id = entity["entity_id"]
        payload = entity.get("entity_payload", {})
        terms = [entity["name"], entity["entity_id"], entity["entity_type"], entity.get("category", "")]
        terms.extend(entity.get("aliases", []))
        terms.extend(payload.get("related_terms", []))
        terms.extend(payload.get("related_concepts", []))
        for token in tokenize(*terms):
            add_index_entry(index, token, "entities", entity_id)

    for source in source_catalog:
        source_id = source["source_id"]
        for token in tokenize(source_id, source.get("title", ""), source.get("domain", ""), source.get("authority", "")):
            add_index_entry(index, token, "sources", source_id)

    for chunk in chunk_catalog:
        chunk_id = chunk["chunk_id"]
        for token in tokenize(chunk.get("doc_id", ""), chunk.get("title", ""), chunk.get("topics", []), chunk.get("section_path", [])):
            add_index_entry(index, token, "chunks", chunk_id)

    serializable = {}
    for token, refs in sorted(index.items()):
        serializable[token] = {
            "entities": sorted(refs["entities"])[:50],
            "chunks": sorted(refs["chunks"])[:50],
            "sources": sorted(refs["sources"])[:50],
        }
    return serializable


def write_readme(manifest):
    lines = [
        "# Published BGP Knowledge Base",
        "",
        f"本目录当前使用 `{manifest['corpus_version']}` 语料，从 `{manifest['corpus_authority']}` 和版本化 chunk 目录机械派生；实体、关系与治理数据仍来自既有确定性数据集。",
        "",
        "生成过程不联网、不下载、不调用 LLM、不做语义审批，也不会把 `pending` 实体升级为 `approved`。",
        "",
        "## Files",
        "",
        "- `manifest.json`：发布快照计数、输入输出路径和当前处理边界。",
        "- `source_catalog.jsonl`：来源清单与确定性处理状态。",
        "- `entity_catalog.jsonl`：实体目录，包含原始实体 payload、来源数、证据数和复核桶。",
        "- `chunk_catalog.jsonl`：chunk 目录，包含 chunk 元数据、预览和所在 chunk 文件。",
        "- `relationship_adjacency.json`：实体关系邻接表。",
        "- `lexical_index.json`：按实体名、别名、来源标题、主题和章节路径生成的机械词项索引。",
        "- `bgp_knowledge_base.sqlite`：由 `src/bgpkb/pipeline/build_sqlite_knowledge_base.py` 生成的本地 SQL 查询入口。",
        "- `sqlite_schema.sql`：SQLite 表结构。",
        "",
        "## Snapshot",
        "",
        f"- 语料版本：{manifest['corpus_version']}",
        f"- 输入快照：{manifest['corpus_input_snapshot']}",
        f"- 来源：{manifest['counts']['sources']}",
        f"- 实体：{manifest['counts']['entities']}",
        f"- Chunks：{manifest['counts']['chunks']}",
        f"- 关系：{manifest['counts']['relationships']}",
        f"- 词项：{manifest['counts']['lexical_terms']}",
        f"- 需要人工复核实体：{manifest['counts']['pending_entities']}",
        f"- LLM/语义跳过行动：{manifest['counts']['semantic_skipped_actions']}",
        f"- 人工复核决策审计：{manifest['counts']['human_review_decision_audit']}",
        f"- 人工复核决策应用预览：{manifest['counts']['human_review_decision_apply_preview']}",
        f"- 人工复核输入校验：{manifest['counts']['human_review_input_validation']}",
        f"- 人工复核进度记录：{manifest['counts']['human_review_progress']}",
        f"- 人工复核逐字段清单：{manifest['counts']['human_review_field_checklist']}",
        f"- 人工复核来源矩阵：{manifest['counts']['human_review_source_matrix']}",
        f"- 人工复核任务板：{manifest['counts']['human_review_task_board']}",
        f"- 人工复核交接清单：{manifest['counts']['human_review_handoff']}",
        "",
        "## Boundary",
        "",
        "- `pending` 表示尚未人工批准，不代表事实错误。",
        "- PaperMethod 扩展、案例角色判断、证据强度判断和关系语义推断仍按策略跳过。",
        "- 使用本发布目录时，应优先通过 `source_refs`、`chunk_id` 和 `source_ref` 回溯原始证据。",
        "- 人工复核时可通过 SQLite 查询 `human_review_evidence_extracts` 或 `src/bgpkb/pipeline/query_knowledge_base.py extracts <entity_id>` 查看确定性 chunk 摘录。",
        "- 人工分批复核时可通过 SQLite 查询 `human_review_session_queue` 或 `src/bgpkb/pipeline/query_knowledge_base.py sessions --session-id <session_id>` 查看会话队列。",
        "- 人工复核进度跟踪可通过 SQLite 查询 `human_review_session_status` 查看 session 完成率、状态计数和下一条实体。",
        "- 人工复核执行入口可通过 SQLite 查询 `human_review_task_board` 和 `human_review_handoff` 查看任务板与交接清单。",
    ]
    _atomic_text(README, "\n".join(lines) + "\n")


def write_report(manifest):
    lines = [
        "# 发布知识库报告",
        "",
        "## 范围",
        "",
        "`data/published/` 是当前 BGP 知识库的确定性发布入口，只汇总已有事实、路径和引用，不做语义抽取、归纳或审批。",
        "",
        "## 输出",
        "",
    ]
    for rel in manifest["outputs"]:
        lines.append(f"- `{rel}`")
    lines.extend([
        "",
        "## 计数",
        "",
        f"- 语料版本：{manifest['corpus_version']}",
        f"- 输入快照：{manifest['corpus_input_snapshot']}",
    ])
    for key, value in manifest["counts"].items():
        lines.append(f"- {key}：{value}")
    lines.extend([
        "",
        "## 层级发布完整性",
        "",
        f"- 层级完整性：{manifest.get('hierarchy_integrity', 'not_applicable')}",
        f"- 已发布 resolved chunk：{manifest['counts'].get('published_resolved_chunks', 0)}",
        f"- 已隔离 unresolved chunk：{manifest['counts'].get('isolated_unresolved_chunks', 0)}",
    ])
    reasons = manifest.get("hierarchy_isolation_reasons", {})
    if reasons:
        lines.extend(f"- {reason}：{count}" for reason, count in sorted(reasons.items()))
    else:
        lines.append("- 隔离原因：无")
    lines.extend([
        "",
        "## 边界",
        "",
        "- 不联网、不下载资料。",
        "- 不使用 LLM。",
        "- 不把 pending 实体升级为 approved。",
        "- 不根据文本内容自动扩展 PaperMethod、Case 或语义关系。",
    ])
    _atomic_text(REPORT, "\n".join(lines) + "\n")


def build_manifest_inputs(release_manifest):
    inputs = [
        "data/sources/inventory/sources.csv",
        f"{release_manifest['chunks']}/*.jsonl",
        "data/knowledge/entities/*.jsonl",
        "data/knowledge/relationships/relationships.jsonl",
        "data/derived/datasets/entity_source_evidence.jsonl",
        "data/derived/datasets/entity_review_packets.jsonl",
        "data/derived/datasets/source_processing_status.jsonl",
        "data/derived/datasets/next_action_queue.jsonl",
        "data/derived/datasets/human_review_decision_audit.jsonl",
        "data/derived/datasets/human_review_decision_apply_preview.jsonl",
        "data/derived/datasets/human_review_input_validation.jsonl",
        "data/derived/datasets/human_review_progress.jsonl",
        "data/derived/datasets/human_review_field_checklist.jsonl",
        "data/derived/datasets/human_review_source_matrix.jsonl",
        "data/derived/datasets/human_review_task_board.jsonl",
        "data/derived/datasets/human_review_handoff.jsonl",
    ]
    if release_manifest["version"] == "v2":
        inputs.append("data/derived/datasets/section_catalog.jsonl")
    return inputs


def main():
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)

    active_release = resolve_active_release()
    entity_catalog = build_entity_catalog()
    source_catalog = build_source_catalog()
    sources_by_doc = {row["source_id"]: row for row in source_catalog}
    hierarchy_diagnostics = {}
    chunk_catalog = build_chunk_catalog(
        active_release["chunks_path"],
        corpus_version=active_release["manifest"]["version"],
        section_catalog_path=DATASET_DIR / "section_catalog.jsonl",
        diagnostics=hierarchy_diagnostics,
        sources_by_doc=sources_by_doc,
    )
    relationship_adjacency = build_relationship_adjacency(entity_catalog)
    lexical_index = build_lexical_index(entity_catalog, source_catalog, chunk_catalog)
    next_actions = load_jsonl(DATASET_DIR / "next_action_queue.jsonl")

    write_jsonl(ENTITY_CATALOG, entity_catalog)
    write_jsonl(SOURCE_CATALOG, source_catalog)
    write_jsonl(CHUNK_CATALOG, chunk_catalog)
    write_json(RELATIONSHIP_ADJACENCY, relationship_adjacency)
    write_json(LEXICAL_INDEX, lexical_index)

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "generated_by": "src/bgpkb/pipeline/build_published_knowledge_base.py",
        "corpus_version": active_release["manifest"]["version"],
        "corpus_input_snapshot": active_release["manifest"]["input_snapshot"],
        "corpus_authority": active_release["manifest"]["authority"],
        "historical_review_evidence_corpus_version": "v1",
        "inputs": build_manifest_inputs(active_release["manifest"]),
        "outputs": [
            "data/published/README.md",
            "data/published/manifest.json",
            "data/published/source_catalog.jsonl",
            "data/published/entity_catalog.jsonl",
            "data/published/chunk_catalog.jsonl",
            "data/published/relationship_adjacency.json",
            "data/published/lexical_index.json",
        ],
        "counts": {
            "sources": len(source_catalog),
            "entities": len(entity_catalog),
            "chunks": len(chunk_catalog),
            "published_resolved_chunks": hierarchy_diagnostics["published_resolved_count"],
            "isolated_unresolved_chunks": hierarchy_diagnostics["isolated_unresolved_count"],
            "relationships": relationship_adjacency["relationship_count"],
            "lexical_terms": len(lexical_index),
            "pending_entities": sum(1 for item in entity_catalog if item["review_status"] == "pending"),
            "semantic_skipped_actions": sum(1 for item in next_actions if item.get("needs_llm")),
            "source_gap_items": len(load_jsonl(DATASET_DIR / "source_gap_queue.jsonl")),
            "human_review_decision_audit": len(load_jsonl(DATASET_DIR / "human_review_decision_audit.jsonl")),
            "human_review_decision_apply_preview": len(load_jsonl(DATASET_DIR / "human_review_decision_apply_preview.jsonl")),
            "human_review_input_validation": len(load_jsonl(DATASET_DIR / "human_review_input_validation.jsonl")),
            "human_review_progress": len(load_jsonl(DATASET_DIR / "human_review_progress.jsonl")),
            "human_review_field_checklist": len(load_jsonl(DATASET_DIR / "human_review_field_checklist.jsonl")),
            "human_review_source_matrix": len(load_jsonl(DATASET_DIR / "human_review_source_matrix.jsonl")),
            "human_review_task_board": len(load_jsonl(DATASET_DIR / "human_review_task_board.jsonl")),
            "human_review_handoff": len(load_jsonl(DATASET_DIR / "human_review_handoff.jsonl")),
        },
        "review_status_counts": dict(sorted(Counter(item["review_status"] for item in entity_catalog).items())),
        "entity_type_counts": dict(sorted(Counter(item["entity_type"] for item in entity_catalog).items())),
        "hierarchy_integrity": hierarchy_diagnostics["hierarchy_integrity"],
        "hierarchy_isolation_reasons": hierarchy_diagnostics["isolated_reasons"],
        "boundary": {
            "uses_llm": False,
            "downloads_sources": False,
            "approves_pending_entities": False,
            "semantic_extraction": False,
        },
    }
    write_json(MANIFEST, manifest)
    write_readme(manifest)
    write_report(manifest)

    for output in manifest["outputs"]:
        print(f"Wrote {output}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
