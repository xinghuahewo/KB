#!/usr/bin/env python3
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from bgpkb import paths
from bgpkb.cleaning_v2.release import resolve_release


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


def write_jsonl(path, records):
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def build_chunk_catalog(chunk_dir, *, project_root=ROOT, sources_by_doc=None):
    records = []
    sources_by_doc = sources_by_doc or {}
    project_root = Path(project_root).resolve()
    for path in sorted(Path(chunk_dir).glob("*.jsonl")):
        chunk_file = path.resolve().relative_to(project_root).as_posix()
        for chunk in load_jsonl(path):
            content = chunk.get("content", "")
            source = sources_by_doc.get(chunk.get("doc_id", ""), {})
            source_type = chunk.get("source_type", "")
            if source_type in {"", "document"}:
                source_type = source.get("source_type", source_type)
            records.append({
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
            })
    records.sort(key=lambda item: (item["doc_id"], item["chunk_id"]))
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
    README.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
        "## 边界",
        "",
        "- 不联网、不下载资料。",
        "- 不使用 LLM。",
        "- 不把 pending 实体升级为 approved。",
        "- 不根据文本内容自动扩展 PaperMethod、Case 或语义关系。",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)

    active_release = resolve_active_release()
    entity_catalog = build_entity_catalog()
    source_catalog = build_source_catalog()
    sources_by_doc = {row["source_id"]: row for row in source_catalog}
    chunk_catalog = build_chunk_catalog(
        active_release["chunks_path"],
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
        "inputs": [
            "data/sources/inventory/sources.csv",
            f"{active_release['manifest']['chunks']}/*.jsonl",
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
        ],
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
