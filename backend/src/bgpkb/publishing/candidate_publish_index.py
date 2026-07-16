"""从隔离候选的 v3 权威输入生成 publish-index 基础 catalog。"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile

from bgpkb import paths
from bgpkb.ingestion.source_registry import load_source_registry


class CandidatePublishIndexError(RuntimeError):
    """候选 catalog 无法形成同 release 身份闭包。"""


def _load_json(path: Path, label: str) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidatePublishIndexError(f"{label} 不可读：{exc}") from exc
    if not isinstance(payload, dict):
        raise CandidatePublishIndexError(f"{label} 必须是 JSON 对象")
    return payload


def _load_jsonl(path: Path, label: str) -> list[dict]:
    rows: list[dict] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise CandidatePublishIndexError(
                        f"{label} 第 {line_number} 行必须是 JSON 对象"
                    )
                rows.append(row)
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidatePublishIndexError(f"{label} 不可读：{exc}") from exc
    return rows


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _write_json(path: Path, payload: object) -> None:
    _atomic_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def _write_jsonl(path: Path, records: list[dict]) -> None:
    _atomic_text(
        path,
        "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            for record in records
        ),
    )


def _unique_by(rows: list[dict], key: str, label: str) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for row in rows:
        value = row.get(key)
        if not isinstance(value, str) or not value:
            raise CandidatePublishIndexError(f"{label} 缺少 {key}")
        if value in result:
            raise CandidatePublishIndexError(f"{label} {key} 重复：{value}")
        result[value] = row
    return result


def build_candidate_catalogs(
    *,
    data_dir: Path,
    registry_path: Path,
    release_id: str,
) -> dict[str, object]:
    """只从候选 source snapshot、SemanticChunk v3 与 Retrieval Document 派生。"""

    if not release_id.strip():
        raise CandidatePublishIndexError("release_id 不能为空")
    data_dir = Path(data_dir).resolve()
    published_dir = data_dir / "published"
    source_manifest = _load_json(
        data_dir / "manifests" / "source_ingest.json", "source-ingest manifest"
    )
    registry = load_source_registry(Path(registry_path))
    chunks = _load_jsonl(
        published_dir / "semantic_chunks_v3.jsonl", "SemanticChunk v3"
    )
    retrieval_documents = _load_jsonl(
        published_dir / "retrieval_documents_v1.jsonl", "Retrieval Document v1"
    )
    if not chunks or not retrieval_documents:
        raise CandidatePublishIndexError("SemanticChunk/Retrieval Document 不能为空")

    chunk_by_id = _unique_by(chunks, "chunk_id", "SemanticChunk v3")
    retrieval_by_chunk = _unique_by(
        retrieval_documents, "chunk_id", "Retrieval Document v1"
    )
    if set(chunk_by_id) != set(retrieval_by_chunk):
        raise CandidatePublishIndexError("SemanticChunk 与 Retrieval Document chunk ID 集不闭合")

    registry_by_id = _unique_by(registry["sources"], "source_id", "来源注册表")
    snapshots = {}
    for row in source_manifest.get("sources", []):
        source_id = row.get("source_id")
        snapshot = row.get("snapshot")
        if row.get("status") != "imported" or not isinstance(snapshot, dict):
            raise CandidatePublishIndexError(f"来源没有可发布 snapshot：{source_id}")
        if snapshot.get("source_id") != source_id:
            raise CandidatePublishIndexError(f"snapshot source_id 不闭合：{source_id}")
        snapshots[str(source_id)] = snapshot
    if set(snapshots) != set(registry_by_id):
        raise CandidatePublishIndexError("来源注册表与 snapshot source ID 集不闭合")

    chunk_counts = Counter(str(row["source_id"]) for row in chunks)
    source_catalog = []
    for source_id, source in sorted(registry_by_id.items()):
        snapshot = snapshots[source_id]
        acquisition = source.get("acquisition", {})
        license_payload = snapshot.get("license", {})
        source_catalog.append(
            {
                "schema_version": "source_catalog_v3",
                "release_id": release_id,
                "source_id": source_id,
                "title": source.get("title", source_id),
                "source_type": source.get("source_type", "unknown"),
                "document_profile": source.get("document_profile", "plain_text"),
                "authority": source.get("authority_org", ""),
                "organization": source.get("authority_org", ""),
                "language": source.get("language", "und"),
                "url": acquisition.get("origin_locator", ""),
                "path": source.get("legacy_path", ""),
                "snapshot_id": snapshot.get("snapshot_id", ""),
                "object_digest": snapshot.get("object_digest", ""),
                "license_status": license_payload.get("status", "unknown"),
                "trust_level": "unknown",
                "review_status": "pending",
                "processing_status": "complete",
                "parsed_status": "parsed",
                "cleaned_status": "approved",
                "chunk_count": chunk_counts[source_id],
                "case_observation_count": 0,
            }
        )

    section_groups: dict[tuple[str, tuple[str, ...]], list[str]] = {}
    for chunk in chunks:
        key = (
            str(chunk.get("doc_id", "")),
            tuple(str(item) for item in chunk.get("section_path", [])),
        )
        section_groups.setdefault(key, []).append(str(chunk["chunk_id"]))
    section_ids = {
        key: "semantic_section_v1_"
        + hashlib.sha256(
            json.dumps(
                {"doc_id": key[0], "section_path": key[1]},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        for key in section_groups
    }
    chunk_positions = {
        chunk_id: (section_ids[key], index, child_ids)
        for key, child_ids in section_groups.items()
        for index, chunk_id in enumerate(child_ids)
    }

    chunk_catalog = []
    for chunk in chunks:
        chunk_id = str(chunk["chunk_id"])
        retrieval = retrieval_by_chunk[chunk_id]
        if chunk.get("source_id") != retrieval.get("source_id"):
            raise CandidatePublishIndexError(f"chunk/source ID 不闭合：{chunk_id}")
        section_id, chunk_order, siblings = chunk_positions[chunk_id]
        chunk_catalog.append(
            {
                **chunk,
                "release_id": release_id,
                "retrieval_doc_id": retrieval["retrieval_doc_id"],
                "retrieval_text_hash": retrieval["retrieval_text_hash"],
                "retrieval_text_version": retrieval["retrieval_text_version"],
                "content_preview": retrieval.get("content_preview", ""),
                "source_ref": retrieval["source_ref"],
                "governance": retrieval["governance"],
                "eligibility": retrieval["eligibility"],
                "content_chars": len(str(chunk.get("content", ""))),
                "chunk_file": "data/published/semantic_chunks_v3.jsonl",
                "parent_section_id": section_id,
                "chunk_order": chunk_order,
                "previous_chunk_id": siblings[chunk_order - 1] if chunk_order else None,
                "next_chunk_id": (
                    siblings[chunk_order + 1]
                    if chunk_order + 1 < len(siblings)
                    else None
                ),
                "hierarchy_status": "resolved",
            }
        )

    section_catalog = []
    sections_by_doc: dict[str, list[tuple[tuple[str, tuple[str, ...]], list[str]]]] = {}
    for key, child_ids in section_groups.items():
        sections_by_doc.setdefault(key[0], []).append((key, child_ids))
    for doc_id, grouped_sections in sorted(sections_by_doc.items()):
        for section_order, (key, child_ids) in enumerate(grouped_sections):
            section_path = list(key[1])
            section_catalog.append(
                {
                    "schema_version": "semantic_section_v1",
                    "release_id": release_id,
                    "section_id": section_ids[key],
                    "doc_id": doc_id,
                    "section_path": section_path,
                    "heading": section_path[-1] if section_path else "",
                    "section_order": section_order,
                    "parent_section_id": None,
                    "child_section_ids": [],
                    "child_chunk_ids": child_ids,
                    "previous_section_id": (
                        section_ids[grouped_sections[section_order - 1][0]]
                        if section_order
                        else None
                    ),
                    "next_section_id": (
                        section_ids[grouped_sections[section_order + 1][0]]
                        if section_order + 1 < len(grouped_sections)
                        else None
                    ),
                }
            )

    manifest = {
        "schema_version": "candidate_published_manifest_v1",
        "release_id": release_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        ),
        "generated_by": "bgpkb.publishing.candidate_publish_index",
        "corpus_version": "semantic_chunk_v3",
        "retrieval_text_version": "retrieval_text_v1",
        "historical_review_evidence_corpus_version": "v1",
        "legacy_inputs": [],
        "counts": {
            "sources": len(source_catalog),
            "chunks": len(chunk_catalog),
            "sections": len(section_catalog),
            "retrieval_documents": len(retrieval_documents),
        },
        "inputs": [
            "data/manifests/source_ingest.json",
            "data/published/semantic_chunks_v3.jsonl",
            "data/published/retrieval_documents_v1.jsonl",
        ],
    }
    _write_jsonl(published_dir / "source_catalog.jsonl", source_catalog)
    _write_jsonl(published_dir / "chunk_catalog.jsonl", chunk_catalog)
    _write_jsonl(published_dir / "section_catalog.jsonl", section_catalog)
    _write_jsonl(published_dir / "entity_catalog.jsonl", [])
    _write_json(
        published_dir / "relationship_adjacency.json",
        {
            "release_id": release_id,
            "node_count": 0,
            "relationship_count": 0,
            "nodes": {},
        },
    )
    _write_json(published_dir / "lexical_index.json", {})
    _write_json(published_dir / "manifest.json", manifest)
    _atomic_text(
        published_dir / "README.md",
        "# 候选发布索引\n\n本目录只从本 release 的 v3 候选数据派生，未读取 legacy chunk。\n",
    )
    return {
        "status": "complete",
        "release_id": release_id,
        "source_count": len(source_catalog),
        "chunk_count": len(chunk_catalog),
        "section_count": len(section_catalog),
        "retrieval_document_count": len(retrieval_documents),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="构建 v3 候选 publish-index catalog")
    parser.add_argument("--data-dir", type=Path, default=paths.DATA_DIR)
    parser.add_argument("--registry", type=Path, default=paths.SOURCE_REGISTRY_PATH)
    parser.add_argument("--release-id", default=os.environ.get("BGPKB_RELEASE_ID", ""))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_candidate_catalogs(
        data_dir=args.data_dir,
        registry_path=args.registry,
        release_id=args.release_id or args.data_dir.resolve().parent.name,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
