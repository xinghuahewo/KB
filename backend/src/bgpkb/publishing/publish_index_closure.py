"""publish-index 候选制品的 release、hash、模型与 ID 闭包。"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Mapping
import uuid

from bgpkb.indexing.retrieval_documents import build_retrieval_input_manifest
from bgpkb.infrastructure import serving_bundle


PUBLISH_INDEX_MANIFEST_FILENAME = "publish_index_manifest_v1.json"
PUBLISH_ARTIFACT_PATHS = {
    "source_catalog": "published/source_catalog.jsonl",
    "chunk_catalog": "published/chunk_catalog.jsonl",
    "section_catalog": "published/section_catalog.jsonl",
    "retrieval_documents": "published/retrieval_documents_v1.jsonl",
    "serving_sqlite": "published/serving.sqlite",
    "fts": "published/serving.sqlite",
    "governance_sqlite": "published/governance.sqlite",
    "embedding_jsonl": "published/bge_m3_vector_index.jsonl",
    "embedding_manifest": "published/bge_m3_embedding_manifest.json",
    "fast_matrix": "published/bge_m3_vector_matrix.npy",
    "fast_metadata": "published/bge_m3_vector_metadata.jsonl",
    "fast_manifest": "published/bge_m3_vector_fast_manifest.json",
    "artifact_manifest": "derived/datasets/artifact_manifest.jsonl",
}
REQUIRED_PUBLISH_ARTIFACT_ROLES = frozenset(PUBLISH_ARTIFACT_PATHS)
RETRIEVAL_BOUND_ROLES = {
    "retrieval_documents",
    "serving_sqlite",
    "fts",
    "embedding_jsonl",
    "embedding_manifest",
    "fast_matrix",
    "fast_metadata",
    "fast_manifest",
}
MODEL_BOUND_ROLES = {
    "embedding_jsonl",
    "embedding_manifest",
    "fast_matrix",
    "fast_metadata",
    "fast_manifest",
}


class PublishIndexClosureError(RuntimeError):
    """publish-index 尚未形成完整、同 release 的服务制品。"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _load_json(path: Path, label: str) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PublishIndexClosureError(f"{label} JSON 不可读：{exc}") from exc
    if not isinstance(payload, dict):
        raise PublishIndexClosureError(f"{label} 必须是 JSON 对象")
    return payload


def _load_jsonl(path: Path, label: str) -> list[dict]:
    rows = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise PublishIndexClosureError(
                        f"{label} 第 {line_number} 行必须是 JSON 对象"
                    )
                rows.append(row)
    except (OSError, json.JSONDecodeError) as exc:
        raise PublishIndexClosureError(f"{label} JSONL 不可读：{exc}") from exc
    return rows


def _require_unique(rows: list[dict], key: str, label: str) -> set[str]:
    values = [str(row.get(key, "")) for row in rows]
    if any(not value for value in values):
        raise PublishIndexClosureError(f"{label} 缺少 {key}")
    if len(values) != len(set(values)):
        raise PublishIndexClosureError(f"{label} {key} 重复")
    return set(values)


def _database_metadata(path: Path) -> dict[str, str]:
    try:
        with sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True) as connection:
            return dict(connection.execute("SELECT key, value FROM meta"))
    except sqlite3.Error as exc:
        raise PublishIndexClosureError(f"SQLite meta 不可读：{path.name}: {exc}") from exc


def _artifact_manifest_map(path: Path) -> dict[str, dict]:
    rows = _load_jsonl(path, "artifact_manifest")
    result = {}
    for row in rows:
        artifact_path = row.get("artifact_path")
        if isinstance(artifact_path, str) and artifact_path:
            result[artifact_path] = row
    return result


def _normalize_recorded_sha(value: object) -> str:
    text = str(value or "")
    return text if text.startswith("sha256:") else "sha256:" + text


def _build_payload(data_dir: Path, *, release_id: str) -> dict:
    if not release_id.strip():
        raise PublishIndexClosureError("publish-index release_id 不能为空")
    data_dir = Path(data_dir).resolve()
    paths_by_role = {
        role: data_dir / relative for role, relative in PUBLISH_ARTIFACT_PATHS.items()
    }
    missing = sorted(
        role for role, path in paths_by_role.items() if not path.is_file()
    )
    if missing:
        raise PublishIndexClosureError(f"缺少 publish-index 制品：{missing}")

    source_rows = _load_jsonl(paths_by_role["source_catalog"], "source_catalog")
    chunk_rows = _load_jsonl(paths_by_role["chunk_catalog"], "chunk_catalog")
    section_rows = _load_jsonl(paths_by_role["section_catalog"], "section_catalog")
    retrieval_rows = _load_jsonl(
        paths_by_role["retrieval_documents"], "retrieval_documents"
    )
    artifact_rows = _load_jsonl(
        paths_by_role["artifact_manifest"], "artifact_manifest"
    )
    if not retrieval_rows:
        raise PublishIndexClosureError("Retrieval Document 不能为空")
    _require_unique(source_rows, "source_id", "source_catalog")
    retrieval_manifest = build_retrieval_input_manifest(retrieval_rows)
    retrieval_input_hash = retrieval_manifest["input_manifest_hash"]
    retrieval_chunk_ids = _require_unique(
        retrieval_rows, "chunk_id", "retrieval_documents"
    )
    retrieval_doc_ids = _require_unique(
        retrieval_rows, "retrieval_doc_id", "retrieval_documents"
    )
    catalog_chunk_ids = _require_unique(chunk_rows, "chunk_id", "chunk_catalog")
    _require_unique(section_rows, "section_id", "section_catalog")
    section_chunk_ids = {
        str(chunk_id)
        for section in section_rows
        for chunk_id in section.get("child_chunk_ids", [])
    }
    if section_chunk_ids != catalog_chunk_ids:
        raise PublishIndexClosureError("section catalog 与 chunk catalog ID 集不闭合")
    if not retrieval_chunk_ids <= catalog_chunk_ids:
        raise PublishIndexClosureError("catalog 与 Retrieval Document chunk ID 集不闭合")

    try:
        serving_diagnostics = serving_bundle.inspect_serving_database(
            paths_by_role["serving_sqlite"]
        )
        with serving_bundle.connect_serving_database(
            paths_by_role["serving_sqlite"]
        ) as connection:
            serving_rows = connection.execute(
                "SELECT retrieval_doc_id, chunk_id FROM retrieval_documents"
            ).fetchall()
            fts_rows = connection.execute(
                "SELECT retrieval_doc_id, chunk_id FROM chunk_fts"
            ).fetchall()
            serving_meta = dict(connection.execute("SELECT key, value FROM meta"))
    except (sqlite3.Error, serving_bundle.ServingBundleError) as exc:
        raise PublishIndexClosureError(f"serving.sqlite/FTS 不可验证：{exc}") from exc
    if serving_diagnostics.get("release_id") != release_id:
        raise PublishIndexClosureError(
            "serving.sqlite 跨 release："
            f"{serving_diagnostics.get('release_id')} != {release_id}"
        )
    serving_ids = {(str(row[0]), str(row[1])) for row in serving_rows}
    expected_ids = {
        (str(row["retrieval_doc_id"]), str(row["chunk_id"]))
        for row in retrieval_rows
    }
    if serving_ids != expected_ids:
        raise PublishIndexClosureError("serving.sqlite Retrieval Document ID 集不闭合")
    fts_ids = {(str(row[0]), str(row[1])) for row in fts_rows}
    if fts_ids != serving_ids:
        raise PublishIndexClosureError("FTS Retrieval Document ID 集不闭合")
    if serving_meta.get("retrieval_document_manifest_hash") != retrieval_input_hash:
        raise PublishIndexClosureError("FTS retrieval input manifest 不一致")

    governance_meta = _database_metadata(paths_by_role["governance_sqlite"])
    if governance_meta.get("release_id") != release_id:
        raise PublishIndexClosureError(
            f"governance.sqlite 跨 release：{governance_meta.get('release_id')} != {release_id}"
        )

    embedding_manifest = _load_json(
        paths_by_role["embedding_manifest"], "embedding_manifest"
    )
    model_revision = embedding_manifest.get("model_revision")
    if not isinstance(model_revision, str) or not model_revision.strip():
        raise PublishIndexClosureError("embedding manifest 缺少 model_revision")
    if embedding_manifest.get("status") != "complete":
        raise PublishIndexClosureError("embedding manifest 未完成")
    if embedding_manifest.get("retrieval_input_manifest_hash") != retrieval_input_hash:
        raise PublishIndexClosureError("embedding retrieval input manifest 不一致")

    vector_rows = _load_jsonl(paths_by_role["embedding_jsonl"], "embedding_jsonl")
    vector_chunk_ids = set()
    vector_doc_ids = set()
    vector_input_hashes = set()
    for row in vector_rows:
        if row.get("kind", "chunk") != "chunk":
            continue
        metadata = row.get("metadata") if isinstance(row.get("metadata"), Mapping) else {}
        chunk_id = metadata.get("chunk_id") or row.get("chunk_id")
        if not chunk_id:
            raise PublishIndexClosureError("embedding JSONL 缺少 chunk_id")
        vector_chunk_ids.add(str(chunk_id))
        vector_doc_ids.add(str(row.get("doc_id", "")))
        vector_input_hashes.add(row.get("retrieval_input_manifest_hash"))
    if vector_chunk_ids != retrieval_chunk_ids or vector_doc_ids != retrieval_doc_ids:
        raise PublishIndexClosureError("embedding JSONL 与 Retrieval Document ID 集不闭合")
    if vector_input_hashes != {retrieval_input_hash}:
        raise PublishIndexClosureError("embedding JSONL retrieval input manifest 不一致")
    expected_embedding_count = embedding_manifest.get(
        "record_count", embedding_manifest.get("input_count")
    )
    if expected_embedding_count != len(vector_rows):
        raise PublishIndexClosureError("embedding manifest 记录数不一致")

    fast_rows = _load_jsonl(paths_by_role["fast_metadata"], "fast_metadata")
    fast_chunk_ids = _require_unique(fast_rows, "chunk_id", "fast_metadata")
    if fast_chunk_ids != retrieval_chunk_ids:
        raise PublishIndexClosureError("fast metadata chunk ID 闭包失败")
    fast_manifest = _load_json(paths_by_role["fast_manifest"], "fast_manifest")
    if fast_manifest.get("status", "complete") != "complete":
        raise PublishIndexClosureError("fast manifest 未完成")
    if fast_manifest.get("source_index_sha256") != _sha256(
        paths_by_role["embedding_jsonl"]
    ):
        raise PublishIndexClosureError(
            "fast manifest source_index_sha256 与 embedding JSONL 不一致"
        )
    if fast_manifest.get("retrieval_input_manifest_hash") != retrieval_input_hash:
        raise PublishIndexClosureError("fast index retrieval input manifest 不一致")
    if fast_manifest.get("record_count") != len(fast_rows):
        raise PublishIndexClosureError("fast manifest 记录数不一致")

    artifact_manifest = _artifact_manifest_map(paths_by_role["artifact_manifest"])
    expected_artifacts = {
        "data/" + path.relative_to(data_dir).as_posix(): path
        for role, path in paths_by_role.items()
        if role not in {"fts", "artifact_manifest"}
    }
    for relative, path in expected_artifacts.items():
        row = artifact_manifest.get(relative)
        if row is None:
            raise PublishIndexClosureError(f"artifact manifest 缺少制品：{relative}")
        if _normalize_recorded_sha(row.get("sha256")) != _sha256(path):
            raise PublishIndexClosureError(f"artifact manifest hash 不一致：{relative}")

    counts = {
        "source_catalog": len(source_rows),
        "chunk_catalog": len(chunk_rows),
        "section_catalog": len(section_rows),
        "retrieval_documents": len(retrieval_rows),
        "serving_sqlite": len(serving_rows),
        "fts": len(fts_rows),
        "governance_sqlite": int(governance_meta.get("record_count", "0")),
        "embedding_jsonl": len(vector_rows),
        "embedding_manifest": int(expected_embedding_count),
        "fast_matrix": len(fast_rows),
        "fast_metadata": len(fast_rows),
        "fast_manifest": int(fast_manifest["record_count"]),
        "artifact_manifest": len(artifact_rows),
    }
    artifacts = {}
    for role, path in sorted(paths_by_role.items()):
        artifacts[role] = {
            "release_id": release_id,
            "path": path.relative_to(data_dir).as_posix(),
            "sha256": _sha256(path),
            "record_count": counts[role],
            "model_revision": model_revision if role in MODEL_BOUND_ROLES else None,
            "retrieval_input_manifest_hash": (
                retrieval_input_hash if role in RETRIEVAL_BOUND_ROLES else None
            ),
        }
    return {
        "schema_version": "publish_index_manifest_v1",
        "status": "complete",
        "release_id": release_id,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "model_revisions": {"embedding": model_revision},
        "retrieval_input_manifest": {
            "schema_version": retrieval_manifest["schema_version"],
            "retrieval_text_version": retrieval_manifest["retrieval_text_version"],
            "document_count": retrieval_manifest["document_count"],
            "input_manifest_hash": retrieval_input_hash,
        },
        "identity_closure": {
            "retrieval_document_count": len(retrieval_rows),
            "chunk_id_count": len(retrieval_chunk_ids),
            "fts_document_count": len(fts_rows),
            "vector_record_count": len(vector_rows),
            "fast_record_count": len(fast_rows),
        },
    }


def _verify_payload(data_dir: Path, payload: Mapping[str, object]) -> dict:
    if payload.get("schema_version") != "publish_index_manifest_v1":
        raise PublishIndexClosureError("publish-index manifest schema_version 非法")
    release_id = payload.get("release_id")
    if not isinstance(release_id, str) or not release_id:
        raise PublishIndexClosureError("publish-index manifest release_id 非法")
    generated_at = payload.get("generated_at")
    if not isinstance(generated_at, str) or not generated_at.endswith("Z"):
        raise PublishIndexClosureError("publish-index manifest generated_at 非法")
    expected = _build_payload(Path(data_dir), release_id=release_id)
    for field in (
        "status",
        "artifact_count",
        "artifacts",
        "model_revisions",
        "retrieval_input_manifest",
        "identity_closure",
    ):
        if payload.get(field) != expected[field]:
            raise PublishIndexClosureError(f"publish-index manifest {field} 与候选不一致")
    return {
        "status": "complete",
        "release_id": release_id,
        "artifact_count": expected["artifact_count"],
        **expected["identity_closure"],
    }


def verify_publish_index_manifest(
    data_dir: Path,
    manifest_path: Path | None = None,
) -> dict:
    data_dir = Path(data_dir).resolve()
    path = Path(
        manifest_path
        or data_dir / "published" / PUBLISH_INDEX_MANIFEST_FILENAME
    )
    return _verify_payload(data_dir, _load_json(path, "publish-index manifest"))


def write_publish_index_manifest(
    data_dir: Path,
    *,
    release_id: str,
    output_path: Path | None = None,
) -> Path:
    data_dir = Path(data_dir).resolve()
    payload = _build_payload(data_dir, release_id=release_id)
    payload["generated_at"] = _utc_now()
    target = Path(
        output_path
        or data_dir / "published" / PUBLISH_INDEX_MANIFEST_FILENAME
    ).resolve()
    try:
        target.relative_to(data_dir)
    except ValueError as exc:
        raise PublishIndexClosureError(f"publish-index manifest 路径越界：{target}") from exc
    target.parent.mkdir(parents=True, exist_ok=True)
    candidate = target.parent / f".{target.name}.{uuid.uuid4().hex}.tmp"
    try:
        candidate.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with candidate.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(candidate, target)
    finally:
        candidate.unlink(missing_ok=True)
    return target
