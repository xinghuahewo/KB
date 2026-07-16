"""版本化 serving/governance SQLite 制品及受控只读 reader。"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sqlite3
from typing import Iterable, Mapping, Sequence
from urllib.parse import quote
import uuid


SERVING_DB_FILENAME = "serving.sqlite"
GOVERNANCE_DB_FILENAME = "governance.sqlite"
SERVING_SCHEMA_VERSION = "serving_sqlite_v1"
GOVERNANCE_SCHEMA_VERSION = "governance_sqlite_v1"
MINIMUM_READER_VERSION = "1.0.0"
CURRENT_READER_VERSION = "1.0.0"
LEGACY_SCHEMA_VERSION = "legacy_v0"

GOVERNANCE_ONLY_TABLES = {
    "entity_evidence",
    "review_packets",
    "next_actions",
    "case_observations",
    "human_review_workbook",
    "human_review_decision_audit",
    "human_review_decision_apply_preview",
    "human_review_input_validation",
    "human_review_progress",
    "historical_evidence_chunks",
    "human_review_evidence_extracts",
    "human_review_session_queue",
    "human_review_session_status",
    "human_review_field_checklist",
    "human_review_source_matrix",
    "human_review_task_board",
    "human_review_handoff",
}

REQUIRED_RELEASE_ARTIFACT_ROLES = {
    "source_snapshot_manifest",
    "canonical_manifest",
    "semantic_chunk_manifest",
    "retrieval_document_manifest",
    "serving_sqlite",
    "governance_sqlite",
    "vector_jsonl",
    "fast_matrix",
    "fast_metadata",
    "fast_manifest",
    "evaluation_evidence",
}


class ServingBundleError(RuntimeError):
    """serving bundle 基础错误。"""


class ServingBundleBuildError(ServingBundleError):
    """候选数据库没有通过原子构建。"""


class ServingBundleCompatibilityError(ServingBundleError):
    """reader 与数据库契约不兼容。"""


class ReleaseManifestError(ServingBundleError):
    """release manifest 不闭合或存在跨 release 混用。"""


SERVING_SCHEMA = """
CREATE TABLE meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE sources (
  source_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  source_type TEXT NOT NULL,
  domain TEXT NOT NULL,
  authority TEXT NOT NULL,
  organization TEXT NOT NULL,
  publish_date TEXT NOT NULL,
  language TEXT NOT NULL,
  path TEXT NOT NULL,
  url TEXT NOT NULL,
  trust_level TEXT NOT NULL,
  review_status TEXT NOT NULL,
  processing_status TEXT NOT NULL,
  parsed_status TEXT NOT NULL,
  cleaned_status TEXT NOT NULL,
  chunk_count INTEGER NOT NULL,
  case_observation_count INTEGER NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE TABLE entities (
  entity_id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  review_status TEXT NOT NULL,
  source_ref_count INTEGER NOT NULL,
  evidence_record_count INTEGER NOT NULL,
  chunk_count INTEGER NOT NULL,
  case_observation_count INTEGER NOT NULL,
  review_bucket TEXT NOT NULL,
  entity_file TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE TABLE entity_sources (
  entity_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  PRIMARY KEY (entity_id, source_id),
  FOREIGN KEY (entity_id) REFERENCES entities(entity_id),
  FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE chunks (
  chunk_id TEXT PRIMARY KEY,
  doc_id TEXT NOT NULL,
  title TEXT NOT NULL,
  source_type TEXT NOT NULL,
  chunk_type TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  language TEXT NOT NULL,
  review_status TEXT NOT NULL,
  content_chars INTEGER NOT NULL,
  content_preview TEXT NOT NULL,
  chunk_file TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  section_path_json TEXT NOT NULL,
  parent_section_id TEXT,
  chunk_order INTEGER,
  previous_chunk_id TEXT,
  next_chunk_id TEXT,
  hierarchy_status TEXT NOT NULL,
  source_block_ids_json TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE TABLE retrieval_documents (
  retrieval_doc_id TEXT PRIMARY KEY,
  chunk_id TEXT NOT NULL UNIQUE,
  doc_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  title TEXT NOT NULL,
  document_profile TEXT NOT NULL,
  semantic_unit TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  retrieval_text TEXT NOT NULL CHECK(length(trim(retrieval_text)) > 0),
  retrieval_text_hash TEXT NOT NULL,
  retrieval_text_version TEXT NOT NULL,
  content_preview TEXT NOT NULL,
  parse_status TEXT NOT NULL,
  content_quality_status TEXT NOT NULL,
  source_trust_status TEXT NOT NULL,
  semantic_review_status TEXT NOT NULL,
  eligibility_status TEXT NOT NULL,
  eligibility_policy_version TEXT NOT NULL,
  eligibility_rule_id TEXT NOT NULL,
  eligibility_reason TEXT NOT NULL,
  eligibility_audit_json TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id)
);

CREATE TABLE chunk_topics (
  chunk_id TEXT NOT NULL,
  topic TEXT NOT NULL,
  PRIMARY KEY (chunk_id, topic),
  FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id)
);

CREATE TABLE relationships (
  relationship_id TEXT PRIMARY KEY,
  src_id TEXT NOT NULL,
  src_type TEXT NOT NULL,
  relation TEXT NOT NULL,
  dst_id TEXT NOT NULL,
  dst_type TEXT NOT NULL,
  confidence REAL,
  source_refs_json TEXT NOT NULL
);

CREATE TABLE lexical_terms (term TEXT PRIMARY KEY);
CREATE TABLE lexical_entity_refs (
  term TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  PRIMARY KEY (term, entity_id),
  FOREIGN KEY (term) REFERENCES lexical_terms(term),
  FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);
CREATE TABLE lexical_source_refs (
  term TEXT NOT NULL,
  source_id TEXT NOT NULL,
  PRIMARY KEY (term, source_id),
  FOREIGN KEY (term) REFERENCES lexical_terms(term),
  FOREIGN KEY (source_id) REFERENCES sources(source_id)
);
CREATE TABLE lexical_chunk_refs (
  term TEXT NOT NULL,
  chunk_id TEXT NOT NULL,
  PRIMARY KEY (term, chunk_id),
  FOREIGN KEY (term) REFERENCES lexical_terms(term),
  FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id)
);

CREATE TABLE glossary (
  term_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  term TEXT NOT NULL,
  category TEXT NOT NULL,
  definition TEXT NOT NULL,
  aliases_json TEXT NOT NULL,
  source_refs_json TEXT NOT NULL,
  review_status TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_review_status ON entities(review_status);
CREATE INDEX idx_chunks_doc_id ON chunks(doc_id);
CREATE INDEX idx_retrieval_documents_doc_id ON retrieval_documents(doc_id);
CREATE INDEX idx_retrieval_documents_source_id ON retrieval_documents(source_id);
CREATE INDEX idx_retrieval_documents_text_hash ON retrieval_documents(retrieval_text_hash);
CREATE INDEX idx_relationships_src ON relationships(src_id, relation);
CREATE INDEX idx_relationships_dst ON relationships(dst_id, relation);
"""


FTS_SCHEMA = """
CREATE VIRTUAL TABLE entity_fts USING fts5(
  entity_id UNINDEXED,
  name,
  entity_type,
  category,
  payload_json
);
CREATE VIRTUAL TABLE chunk_fts USING fts5(
  retrieval_doc_id UNINDEXED,
  chunk_id UNINDEXED,
  retrieval_text
);
"""


GOVERNANCE_SCHEMA = """
CREATE TABLE meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE governance_records (
  dataset_name TEXT NOT NULL,
  record_id TEXT NOT NULL,
  record_type TEXT NOT NULL,
  payload_sha256 TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  PRIMARY KEY (dataset_name, record_id)
);

CREATE TABLE governance_dataset_manifest (
  dataset_name TEXT PRIMARY KEY,
  record_count INTEGER NOT NULL,
  content_sha256 TEXT NOT NULL
);

CREATE INDEX idx_governance_records_type
  ON governance_records(record_type, dataset_name);
"""


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _documents_manifest_hash(documents: Sequence[Mapping[str, object]]) -> str:
    payload = [
        {
            "retrieval_doc_id": item.get("retrieval_doc_id"),
            "retrieval_text_hash": item.get("retrieval_text_hash"),
            "retrieval_text_version": item.get("retrieval_text_version"),
        }
        for item in sorted(documents, key=lambda row: str(row.get("retrieval_doc_id", "")))
    ]
    return "sha256:" + hashlib.sha256(_json(payload).encode("utf-8")).hexdigest()


def _temp_path(output_path: Path) -> Path:
    return output_path.parent / f".{output_path.name}.{uuid.uuid4().hex}.tmp"


def _remove_sqlite_sidecars(path: Path) -> None:
    for candidate in (path, Path(str(path) + "-shm"), Path(str(path) + "-wal")):
        try:
            candidate.unlink()
        except FileNotFoundError:
            pass


def _sync_file_and_parent(path: Path) -> None:
    file_descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(file_descriptor)
    finally:
        os.close(file_descriptor)
    directory_descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)


def _source_row(record: Mapping[str, object]) -> dict[str, object]:
    return {
        "source_id": str(record["source_id"]),
        "title": str(record.get("title", record["source_id"])),
        "source_type": str(record.get("source_type", "unknown")),
        "domain": str(record.get("domain", "")),
        "authority": str(record.get("authority", "")),
        "organization": str(record.get("organization", "")),
        "publish_date": str(record.get("publish_date", "")),
        "language": str(record.get("language", "")),
        "path": str(record.get("path", "")),
        "url": str(record.get("url", "")),
        "trust_level": str(record.get("trust_level", "unknown")),
        "review_status": str(record.get("review_status", "pending")),
        "processing_status": str(record.get("processing_status", "")),
        "parsed_status": str(record.get("parsed_status", "")),
        "cleaned_status": str(record.get("cleaned_status", "")),
        "chunk_count": int(record.get("chunk_count", 0)),
        "case_observation_count": int(record.get("case_observation_count", 0)),
        "payload_json": _json(record),
    }


def _entity_row(record: Mapping[str, object]) -> dict[str, object]:
    return {
        "entity_id": str(record["entity_id"]),
        "entity_type": str(record.get("entity_type", "unknown")),
        "name": str(record.get("name", record["entity_id"])),
        "category": str(record.get("category", "")),
        "review_status": str(record.get("review_status", "pending")),
        "source_ref_count": int(record.get("source_ref_count", 0)),
        "evidence_record_count": int(record.get("evidence_record_count", 0)),
        "chunk_count": int(record.get("chunk_count", 0)),
        "case_observation_count": int(record.get("case_observation_count", 0)),
        "review_bucket": str(record.get("review_bucket", "")),
        "entity_file": str(record.get("entity_file", "")),
        "payload_json": _json(record),
    }


def _insert_serving_rows(
    conn: sqlite3.Connection,
    *,
    release_id: str,
    minimum_reader_version: str,
    retrieval_documents: Sequence[Mapping[str, object]],
    sources: Sequence[Mapping[str, object]],
    entities: Sequence[Mapping[str, object]],
    entity_sources: Sequence[Mapping[str, object]],
    relationships: Sequence[Mapping[str, object]],
) -> None:
    source_rows = [_source_row(record) for record in sources]
    conn.executemany(
        """
        INSERT INTO sources VALUES (
          :source_id, :title, :source_type, :domain, :authority, :organization,
          :publish_date, :language, :path, :url, :trust_level, :review_status,
          :processing_status, :parsed_status, :cleaned_status, :chunk_count,
          :case_observation_count, :payload_json
        )
        """,
        source_rows,
    )
    entity_rows = [_entity_row(record) for record in entities]
    conn.executemany(
        """
        INSERT INTO entities VALUES (
          :entity_id, :entity_type, :name, :category, :review_status,
          :source_ref_count, :evidence_record_count, :chunk_count,
          :case_observation_count, :review_bucket, :entity_file, :payload_json
        )
        """,
        entity_rows,
    )
    conn.executemany(
        "INSERT INTO entity_sources VALUES (:entity_id, :source_id)",
        entity_sources,
    )
    if entity_rows:
        conn.executemany(
            "INSERT INTO entity_fts VALUES (:entity_id, :name, :entity_type, :category, :payload_json)",
            entity_rows,
        )

    chunk_rows = []
    retrieval_rows = []
    fts_rows = []
    for document in retrieval_documents:
        retrieval_text = str(document.get("retrieval_text", ""))
        if not retrieval_text.strip():
            raise ValueError("Retrieval Document retrieval_text 不能为空")
        governance = document.get("governance")
        eligibility = document.get("eligibility")
        if not isinstance(governance, Mapping) or not isinstance(eligibility, Mapping):
            raise ValueError("Retrieval Document 缺少治理或资格对象")
        chunk_id = str(document["chunk_id"])
        section_path = document.get("section_path", [])
        payload_json = _json(document)
        chunk_rows.append(
            {
                "chunk_id": chunk_id,
                "doc_id": str(document["doc_id"]),
                "title": str(document.get("title", "")),
                "source_type": str(document.get("document_profile", "")),
                "chunk_type": str(document.get("semantic_unit", "")),
                "source_ref": str(document["source_ref"]),
                "language": str(document.get("language", "")),
                "review_status": str(governance.get("semantic_review_status", "unknown")),
                "content_chars": len(retrieval_text),
                "content_preview": str(document.get("content_preview", "")),
                "chunk_file": "",
                "schema_version": "semantic_chunk_v3",
                "section_path_json": _json(section_path),
                "parent_section_id": None,
                "chunk_order": None,
                "previous_chunk_id": None,
                "next_chunk_id": None,
                "hierarchy_status": "derived_from_retrieval_document",
                "source_block_ids_json": "[]",
                "payload_json": payload_json,
            }
        )
        retrieval_rows.append(
            {
                "retrieval_doc_id": str(document["retrieval_doc_id"]),
                "chunk_id": chunk_id,
                "doc_id": str(document["doc_id"]),
                "source_id": str(document["source_id"]),
                "title": str(document.get("title", "")),
                "document_profile": str(document.get("document_profile", "")),
                "semantic_unit": str(document.get("semantic_unit", "")),
                "source_ref": str(document["source_ref"]),
                "retrieval_text": retrieval_text,
                "retrieval_text_hash": str(document["retrieval_text_hash"]),
                "retrieval_text_version": str(document["retrieval_text_version"]),
                "content_preview": str(document.get("content_preview", "")),
                "parse_status": str(governance.get("parse_status", "unknown")),
                "content_quality_status": str(
                    governance.get("content_quality_status", "unknown")
                ),
                "source_trust_status": str(governance.get("source_trust_status", "unknown")),
                "semantic_review_status": str(
                    governance.get("semantic_review_status", "unknown")
                ),
                "eligibility_status": str(eligibility.get("status", "ineligible")),
                "eligibility_policy_version": str(eligibility.get("policy_version", "")),
                "eligibility_rule_id": str(eligibility.get("rule_id", "")),
                "eligibility_reason": str(eligibility.get("reason", "")),
                "eligibility_audit_json": _json(eligibility.get("audit", {})),
                "payload_json": payload_json,
            }
        )
        fts_rows.append((str(document["retrieval_doc_id"]), chunk_id, retrieval_text))

    conn.executemany(
        """
        INSERT INTO chunks VALUES (
          :chunk_id, :doc_id, :title, :source_type, :chunk_type, :source_ref,
          :language, :review_status, :content_chars, :content_preview, :chunk_file,
          :schema_version, :section_path_json, :parent_section_id, :chunk_order,
          :previous_chunk_id, :next_chunk_id, :hierarchy_status,
          :source_block_ids_json, :payload_json
        )
        """,
        chunk_rows,
    )
    conn.executemany(
        """
        INSERT INTO retrieval_documents VALUES (
          :retrieval_doc_id, :chunk_id, :doc_id, :source_id, :title,
          :document_profile, :semantic_unit, :source_ref, :retrieval_text,
          :retrieval_text_hash, :retrieval_text_version, :content_preview,
          :parse_status, :content_quality_status, :source_trust_status,
          :semantic_review_status, :eligibility_status,
          :eligibility_policy_version, :eligibility_rule_id,
          :eligibility_reason, :eligibility_audit_json, :payload_json
        )
        """,
        retrieval_rows,
    )
    conn.executemany("INSERT INTO chunk_fts VALUES (?, ?, ?)", fts_rows)

    relationship_rows = []
    for record in relationships:
        relationship_rows.append(
            {
                "relationship_id": str(record["relationship_id"]),
                "src_id": str(record["src_id"]),
                "src_type": str(record.get("src_type", "entity")),
                "relation": str(record["relation"]),
                "dst_id": str(record["dst_id"]),
                "dst_type": str(record.get("dst_type", "entity")),
                "confidence": record.get("confidence"),
                "source_refs_json": _json(record.get("source_refs", [])),
            }
        )
    conn.executemany(
        """
        INSERT INTO relationships VALUES (
          :relationship_id, :src_id, :src_type, :relation, :dst_id,
          :dst_type, :confidence, :source_refs_json
        )
        """,
        relationship_rows,
    )

    retrieval_manifest_hash = _documents_manifest_hash(retrieval_documents)
    metadata = {
        "schema_version": SERVING_SCHEMA_VERSION,
        "minimum_reader_version": minimum_reader_version,
        "release_id": release_id,
        "retrieval_document_manifest_hash": retrieval_manifest_hash,
        "fts_input_manifest_hash": retrieval_manifest_hash,
        "retrieval_document_count": str(len(retrieval_documents)),
        "fts_retrieval_text_version": (
            str(retrieval_documents[0].get("retrieval_text_version", ""))
            if retrieval_documents
            else ""
        ),
        "database_role": "online_serving_only",
    }
    conn.executemany("INSERT INTO meta VALUES (?, ?)", sorted(metadata.items()))


def _validate_serving_candidate(
    conn: sqlite3.Connection,
    *,
    expected_document_count: int,
    release_id: str,
) -> dict[str, object]:
    foreign_key_issues = conn.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_key_issues:
        raise ValueError(f"foreign_key_check 失败：{foreign_key_issues[:3]}")
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise ValueError(f"integrity_check 失败：{integrity}")
    metadata = dict(conn.execute("SELECT key, value FROM meta"))
    if metadata.get("schema_version") != SERVING_SCHEMA_VERSION:
        raise ValueError("serving schema_version 不匹配")
    if metadata.get("release_id") != release_id:
        raise ValueError("serving release_id 不匹配")
    retrieval_count = conn.execute("SELECT COUNT(*) FROM retrieval_documents").fetchone()[0]
    chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    fts_count = conn.execute("SELECT COUNT(*) FROM chunk_fts").fetchone()[0]
    if {retrieval_count, chunk_count, fts_count} != {expected_document_count}:
        raise ValueError(
            "serving 记录数闭包失败："
            f"retrieval={retrieval_count}, chunks={chunk_count}, fts={fts_count}, "
            f"expected={expected_document_count}"
        )
    missing_ids = conn.execute(
        """
        SELECT d.chunk_id FROM retrieval_documents d
        LEFT JOIN chunks c ON c.chunk_id = d.chunk_id
        WHERE c.chunk_id IS NULL
        """
    ).fetchall()
    if missing_ids:
        raise ValueError(f"serving chunk ID 闭包失败：{missing_ids[:3]}")
    return {
        "integrity_check": integrity,
        "foreign_key_issue_count": 0,
        "retrieval_document_count": retrieval_count,
        "chunk_count": chunk_count,
        "fts_document_count": fts_count,
    }


def build_serving_database(
    output_path: Path,
    *,
    release_id: str,
    retrieval_documents: Sequence[Mapping[str, object]],
    sources: Sequence[Mapping[str, object]] = (),
    entities: Sequence[Mapping[str, object]] = (),
    entity_sources: Sequence[Mapping[str, object]] = (),
    relationships: Sequence[Mapping[str, object]] = (),
    minimum_reader_version: str = MINIMUM_READER_VERSION,
) -> dict[str, object]:
    """在同目录候选文件中构建并校验最小在线数据库，再原子替换。"""

    output_path = Path(output_path)
    if not release_id.strip():
        raise ServingBundleBuildError("serving.sqlite 构建失败：release_id 不能为空")
    _parse_version(minimum_reader_version)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    candidate = _temp_path(output_path)
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(candidate)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = DELETE")
        connection.execute("PRAGMA synchronous = FULL")
        connection.executescript(SERVING_SCHEMA)
        connection.executescript(FTS_SCHEMA)
        _insert_serving_rows(
            connection,
            release_id=release_id,
            minimum_reader_version=minimum_reader_version,
            retrieval_documents=list(retrieval_documents),
            sources=list(sources),
            entities=list(entities),
            entity_sources=list(entity_sources),
            relationships=list(relationships),
        )
        connection.commit()
        result = _validate_serving_candidate(
            connection,
            expected_document_count=len(retrieval_documents),
            release_id=release_id,
        )
        connection.close()
        connection = None
        _sync_file_and_parent(candidate)
        os.replace(candidate, output_path)
        _sync_file_and_parent(output_path)
    except Exception as exc:
        if connection is not None:
            connection.close()
        _remove_sqlite_sidecars(candidate)
        if isinstance(exc, ServingBundleBuildError):
            raise
        raise ServingBundleBuildError(f"serving.sqlite 构建失败：{exc}") from exc
    return {
        **result,
        "path": str(output_path),
        "schema_version": SERVING_SCHEMA_VERSION,
        "minimum_reader_version": minimum_reader_version,
        "release_id": release_id,
        "database_sha256": _sha256(output_path),
    }


def _parse_version(version: str) -> tuple[int, ...]:
    try:
        parts = tuple(int(part) for part in version.split("."))
    except (AttributeError, ValueError) as exc:
        raise ServingBundleCompatibilityError(f"reader version 非法：{version}") from exc
    if not parts or any(part < 0 for part in parts):
        raise ServingBundleCompatibilityError(f"reader version 非法：{version}")
    return parts


def _readonly_connection(path: Path) -> sqlite3.Connection:
    uri = f"file:{quote(str(Path(path).resolve()), safe='/')}?mode=ro&immutable=1"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def inspect_serving_database(
    path: Path,
    *,
    allow_legacy: bool = False,
    reader_version: str = CURRENT_READER_VERSION,
) -> dict[str, object]:
    """读取版本协商元数据；legacy 必须显式允许且总是 degraded。"""

    path = Path(path)
    _parse_version(reader_version)
    try:
        with _readonly_connection(path) as connection:
            has_meta = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='meta'"
            ).fetchone()
            metadata = dict(connection.execute("SELECT key, value FROM meta")) if has_meta else {}
    except sqlite3.Error as exc:
        raise ServingBundleCompatibilityError(f"serving.sqlite 不可读：{exc}") from exc

    schema_version = metadata.get("schema_version")
    if schema_version is None:
        if not allow_legacy:
            raise ServingBundleCompatibilityError(
                "legacy serving database 需要显式 allow_legacy 开关"
            )
        return {
            "mode": "legacy",
            "degraded": True,
            "schema_version": LEGACY_SCHEMA_VERSION,
            "minimum_reader_version": None,
            "reader_version": reader_version,
            "release_id": None,
            "reason": "explicit_legacy_reader",
        }
    if schema_version != SERVING_SCHEMA_VERSION:
        raise ServingBundleCompatibilityError(
            f"不支持的 serving schema_version：{schema_version}"
        )
    minimum = metadata.get("minimum_reader_version")
    if minimum is None or _parse_version(reader_version) < _parse_version(minimum):
        raise ServingBundleCompatibilityError(
            "reader 版本低于 serving minimum_reader_version："
            f"reader={reader_version}, minimum_reader_version={minimum}"
        )
    return {
        "mode": "current",
        "degraded": False,
        "schema_version": schema_version,
        "minimum_reader_version": minimum,
        "reader_version": reader_version,
        "release_id": metadata.get("release_id"),
        "reason": None,
    }


def connect_serving_database(
    path: Path,
    *,
    allow_legacy: bool = False,
    reader_version: str = CURRENT_READER_VERSION,
) -> sqlite3.Connection:
    inspect_serving_database(
        path,
        allow_legacy=allow_legacy,
        reader_version=reader_version,
    )
    return _readonly_connection(Path(path))


def legacy_reader_enabled() -> bool:
    return os.environ.get("BGPKB_ALLOW_LEGACY_READER", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def resolve_serving_database_path(
    data_dir: Path,
    *,
    allow_legacy: bool | None = None,
) -> Path:
    """优先选择新 serving.sqlite；旧单库只能通过显式开关选择。"""

    data_dir = Path(data_dir).resolve()
    candidate_state_path = data_dir.parent / ".pipeline" / "candidate.json"
    if candidate_state_path.is_file():
        try:
            candidate_state = json.loads(candidate_state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ServingBundleCompatibilityError(f"候选状态不可读：{exc}") from exc
        if candidate_state.get("reader_selectable") is not True:
            raise ServingBundleCompatibilityError(
                f"候选 release 尚不可读取：status={candidate_state.get('status', 'unknown')}"
            )
    published_dir = data_dir / "published"
    current = published_dir / SERVING_DB_FILENAME
    if current.is_file():
        return current
    legacy = published_dir / "bgp_knowledge_base.sqlite"
    legacy_allowed = legacy_reader_enabled() if allow_legacy is None else allow_legacy
    if legacy_allowed and legacy.is_file():
        return legacy
    if legacy.is_file():
        raise ServingBundleCompatibilityError(
            "release 只包含 legacy bgp_knowledge_base.sqlite；"
            "需要显式设置 BGPKB_ALLOW_LEGACY_READER=1 才能 degraded 读取"
        )
    raise FileNotFoundError(f"发布制品缺少必需数据文件：{current}")


def _governance_record_id(dataset_name: str, record: Mapping[str, object]) -> str:
    for key in (
        "audit_id",
        "workbook_id",
        "evidence_id",
        "extract_id",
        "candidate_id",
        "task_id",
        "handoff_id",
        "validation_id",
        "progress_id",
        "session_item_id",
        "session_status_id",
        "field_check_id",
        "source_matrix_id",
        "preview_id",
        "action_id",
        "packet_id",
        "id",
    ):
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    digest = hashlib.sha256(_json(record).encode("utf-8")).hexdigest()
    return f"{dataset_name}_{digest}"


def _governance_rows(
    datasets: Mapping[str, Sequence[Mapping[str, object]]],
) -> tuple[list[dict[str, object]], list[tuple[str, int, str]]]:
    rows: list[dict[str, object]] = []
    manifests: list[tuple[str, int, str]] = []
    for dataset_name in sorted(datasets):
        if not dataset_name or not dataset_name.replace("_", "").isalnum():
            raise ValueError(f"governance dataset_name 非法：{dataset_name}")
        dataset_rows = []
        for record in datasets[dataset_name]:
            if not isinstance(record, Mapping):
                raise ValueError(f"governance 数据集 {dataset_name} 包含非对象记录")
            payload_json = _json(record)
            dataset_rows.append(
                {
                    "dataset_name": dataset_name,
                    "record_id": _governance_record_id(dataset_name, record),
                    "record_type": str(
                        record.get("schema_version")
                        or record.get("record_type")
                        or record.get("type")
                        or dataset_name
                    ),
                    "payload_sha256": "sha256:"
                    + hashlib.sha256(payload_json.encode("utf-8")).hexdigest(),
                    "payload_json": payload_json,
                }
            )
        dataset_rows.sort(key=lambda row: str(row["record_id"]))
        rows.extend(dataset_rows)
        manifest_payload = [
            {"record_id": row["record_id"], "payload_sha256": row["payload_sha256"]}
            for row in dataset_rows
        ]
        manifests.append(
            (
                dataset_name,
                len(dataset_rows),
                "sha256:"
                + hashlib.sha256(_json(manifest_payload).encode("utf-8")).hexdigest(),
            )
        )
    return rows, manifests


def build_governance_database(
    output_path: Path,
    *,
    release_id: str,
    datasets: Mapping[str, Sequence[Mapping[str, object]]],
) -> dict[str, object]:
    """把复核、审计、历史证据和离线工作流写入独立原子制品。"""

    output_path = Path(output_path)
    if not release_id.strip():
        raise ServingBundleBuildError("governance.sqlite 构建失败：release_id 不能为空")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    candidate = _temp_path(output_path)
    connection: sqlite3.Connection | None = None
    try:
        rows, manifests = _governance_rows(datasets)
        connection = sqlite3.connect(candidate)
        connection.execute("PRAGMA journal_mode = DELETE")
        connection.execute("PRAGMA synchronous = FULL")
        connection.executescript(GOVERNANCE_SCHEMA)
        connection.executemany(
            """
            INSERT INTO governance_records (
              dataset_name, record_id, record_type, payload_sha256, payload_json
            ) VALUES (
              :dataset_name, :record_id, :record_type, :payload_sha256, :payload_json
            )
            """,
            rows,
        )
        connection.executemany(
            "INSERT INTO governance_dataset_manifest VALUES (?, ?, ?)", manifests
        )
        metadata = {
            "schema_version": GOVERNANCE_SCHEMA_VERSION,
            "release_id": release_id,
            "database_role": "offline_governance_and_audit_only",
            "dataset_count": str(len(manifests)),
            "record_count": str(len(rows)),
        }
        connection.executemany("INSERT INTO meta VALUES (?, ?)", sorted(metadata.items()))
        connection.commit()
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError(f"integrity_check 失败：{integrity}")
        stored_count = connection.execute(
            "SELECT COUNT(*) FROM governance_records"
        ).fetchone()[0]
        manifest_count = connection.execute(
            "SELECT COALESCE(SUM(record_count), 0) FROM governance_dataset_manifest"
        ).fetchone()[0]
        if stored_count != len(rows) or manifest_count != len(rows):
            raise ValueError(
                "governance 记录数闭包失败："
                f"stored={stored_count}, manifests={manifest_count}, expected={len(rows)}"
            )
        connection.close()
        connection = None
        _sync_file_and_parent(candidate)
        os.replace(candidate, output_path)
        _sync_file_and_parent(output_path)
    except Exception as exc:
        if connection is not None:
            connection.close()
        _remove_sqlite_sidecars(candidate)
        raise ServingBundleBuildError(f"governance.sqlite 构建失败：{exc}") from exc
    return {
        "path": str(output_path),
        "schema_version": GOVERNANCE_SCHEMA_VERSION,
        "release_id": release_id,
        "dataset_count": len(manifests),
        "record_count": len(rows),
        "integrity_check": "ok",
        "database_sha256": _sha256(output_path),
    }


def _resolve_manifest_artifact(data_dir: Path, relative_path: str) -> Path:
    if not relative_path or Path(relative_path).is_absolute():
        raise ReleaseManifestError(f"artifact path 非法：{relative_path}")
    candidate = (data_dir / relative_path).resolve()
    try:
        candidate.relative_to(data_dir.resolve())
    except ValueError as exc:
        raise ReleaseManifestError(f"artifact path 越界：{relative_path}") from exc
    return candidate


def _load_json_object(path: Path, role: str) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseManifestError(f"{role} JSON 不可读：{exc}") from exc
    if not isinstance(payload, dict):
        raise ReleaseManifestError(f"{role} 必须是 JSON 对象")
    return payload


def _database_metadata(path: Path) -> dict[str, str]:
    try:
        with _readonly_connection(path) as connection:
            return dict(connection.execute("SELECT key, value FROM meta"))
    except sqlite3.Error as exc:
        raise ReleaseManifestError(f"SQLite meta 不可读：{path.name}: {exc}") from exc


def _jsonl_chunk_ids(path: Path, role: str) -> set[str]:
    chunk_ids: set[str] = set()
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                record = json.loads(line)
                metadata = record.get("metadata") if isinstance(record, dict) else None
                chunk_id = (
                    metadata.get("chunk_id")
                    if isinstance(metadata, dict)
                    else record.get("chunk_id") if isinstance(record, dict) else None
                )
                if record.get("kind", "chunk") == "chunk" and not chunk_id:
                    raise ReleaseManifestError(
                        f"{role} 第 {line_number} 行缺少 chunk_id"
                    )
                if chunk_id:
                    chunk_ids.add(str(chunk_id))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseManifestError(f"{role} JSONL 不可读：{exc}") from exc
    return chunk_ids


def _verify_release_manifest_payload(
    data_dir: Path,
    payload: Mapping[str, object],
) -> dict[str, object]:
    if payload.get("schema_version") != "rag_release_manifest_v2":
        raise ReleaseManifestError("release manifest schema_version 非法")
    release_id = payload.get("release_id")
    if not isinstance(release_id, str) or not release_id:
        raise ReleaseManifestError("release manifest release_id 非法")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise ReleaseManifestError("release manifest artifacts 非法")
    missing_roles = REQUIRED_RELEASE_ARTIFACT_ROLES - set(artifacts)
    if missing_roles:
        raise ReleaseManifestError(f"release manifest 缺少 roles：{sorted(missing_roles)}")

    resolved: dict[str, Path] = {}
    for role in sorted(REQUIRED_RELEASE_ARTIFACT_ROLES):
        entry = artifacts.get(role)
        if not isinstance(entry, Mapping):
            raise ReleaseManifestError(f"artifact entry 非法：{role}")
        if entry.get("release_id") != release_id:
            raise ReleaseManifestError(
                f"artifact release_id 不一致：{role}={entry.get('release_id')} != {release_id}"
            )
        relative_path = entry.get("path")
        if not isinstance(relative_path, str):
            raise ReleaseManifestError(f"artifact path 非法：{role}")
        path = _resolve_manifest_artifact(data_dir, relative_path)
        if not path.is_file():
            raise ReleaseManifestError(f"artifact 不存在：{role}={relative_path}")
        actual_hash = _sha256(path)
        if entry.get("sha256") != actual_hash:
            raise ReleaseManifestError(
                f"artifact hash 不一致：{role}={entry.get('sha256')} != {actual_hash}"
            )
        resolved[role] = path

    serving_diagnostics = inspect_serving_database(resolved["serving_sqlite"])
    if serving_diagnostics.get("release_id") != release_id:
        raise ReleaseManifestError(
            "serving.sqlite release_id 与 release manifest 不一致："
            f"{serving_diagnostics.get('release_id')} != {release_id}"
        )
    governance_metadata = _database_metadata(resolved["governance_sqlite"])
    if governance_metadata.get("schema_version") != GOVERNANCE_SCHEMA_VERSION:
        raise ReleaseManifestError("governance.sqlite schema_version 不匹配")
    if governance_metadata.get("release_id") != release_id:
        raise ReleaseManifestError(
            "governance.sqlite release_id 与 release manifest 不一致："
            f"{governance_metadata.get('release_id')} != {release_id}"
        )

    json_roles = {
        "source_snapshot_manifest",
        "canonical_manifest",
        "semantic_chunk_manifest",
        "retrieval_document_manifest",
        "fast_manifest",
        "evaluation_evidence",
    }
    inner_payloads = {
        role: _load_json_object(resolved[role], role) for role in json_roles
    }
    for role, inner in inner_payloads.items():
        inner_release_id = inner.get("release_id")
        if inner_release_id != release_id:
            raise ReleaseManifestError(
                f"{role} 内部 release_id 不一致：{inner_release_id} != {release_id}"
            )

    semantic_chunk_ids = set(inner_payloads["semantic_chunk_manifest"].get("chunk_ids", []))
    retrieval_chunk_ids = set(
        inner_payloads["retrieval_document_manifest"].get("chunk_ids", [])
    )
    retrieval_doc_ids = set(
        inner_payloads["retrieval_document_manifest"].get("retrieval_doc_ids", [])
    )
    with _readonly_connection(resolved["serving_sqlite"]) as connection:
        serving_rows = connection.execute(
            "SELECT retrieval_doc_id, chunk_id FROM retrieval_documents"
        ).fetchall()
    serving_chunk_ids = {str(row[1]) for row in serving_rows}
    serving_retrieval_doc_ids = {str(row[0]) for row in serving_rows}
    vector_chunk_ids = _jsonl_chunk_ids(resolved["vector_jsonl"], "vector_jsonl")
    fast_chunk_ids = _jsonl_chunk_ids(resolved["fast_metadata"], "fast_metadata")
    chunk_id_sets = {
        "semantic_chunk_manifest": semantic_chunk_ids,
        "retrieval_document_manifest": retrieval_chunk_ids,
        "serving_sqlite": serving_chunk_ids,
        "vector_jsonl": vector_chunk_ids,
        "fast_metadata": fast_chunk_ids,
    }
    if any(ids != serving_chunk_ids for ids in chunk_id_sets.values()):
        counts = {name: len(ids) for name, ids in chunk_id_sets.items()}
        raise ReleaseManifestError(f"跨制品 chunk ID 闭包失败：{counts}")
    if retrieval_doc_ids != serving_retrieval_doc_ids:
        raise ReleaseManifestError(
            "retrieval document ID 闭包失败："
            f"manifest={len(retrieval_doc_ids)}, serving={len(serving_retrieval_doc_ids)}"
        )
    vector_hash = _sha256(resolved["vector_jsonl"])
    if inner_payloads["fast_manifest"].get("source_index_sha256") != vector_hash:
        raise ReleaseManifestError("fast_manifest source_index_sha256 与 vector_jsonl hash 不一致")

    return {
        "schema_version": "rag_release_manifest_v2",
        "release_id": release_id,
        "artifact_count": len(REQUIRED_RELEASE_ARTIFACT_ROLES),
        "chunk_id_count": len(serving_chunk_ids),
        "retrieval_document_count": len(serving_retrieval_doc_ids),
        "serving_schema_version": serving_diagnostics["schema_version"],
        "governance_schema_version": governance_metadata["schema_version"],
    }


def verify_release_manifest(
    data_dir: Path,
    manifest_path: Path | None = None,
) -> dict[str, object]:
    data_dir = Path(data_dir).resolve()
    path = Path(manifest_path or data_dir / "published" / "release_manifest_v2.json")
    payload = _load_json_object(path, "release_manifest")
    return _verify_release_manifest_payload(data_dir, payload)


def write_release_manifest(
    data_dir: Path,
    *,
    release_id: str,
    artifacts: Mapping[str, Path],
    output_path: Path | None = None,
) -> Path:
    """写出绑定全链路 hash/release identity 的原子 manifest。"""

    data_dir = Path(data_dir).resolve()
    missing_roles = REQUIRED_RELEASE_ARTIFACT_ROLES - set(artifacts)
    if missing_roles:
        raise ReleaseManifestError(f"release manifest 缺少 roles：{sorted(missing_roles)}")
    entries: dict[str, dict[str, str]] = {}
    for role in sorted(REQUIRED_RELEASE_ARTIFACT_ROLES):
        path = Path(artifacts[role]).resolve()
        try:
            relative_path = path.relative_to(data_dir).as_posix()
        except ValueError as exc:
            raise ReleaseManifestError(f"artifact path 越界：{role}={path}") from exc
        if not path.is_file():
            raise ReleaseManifestError(f"artifact 不存在：{role}={path}")
        entries[role] = {
            "path": relative_path,
            "sha256": _sha256(path),
            "release_id": release_id,
        }
    payload = {
        "schema_version": "rag_release_manifest_v2",
        "release_id": release_id,
        "artifacts": entries,
    }
    verification = _verify_release_manifest_payload(data_dir, payload)
    payload["identity_closure"] = {
        "chunk_id_count": verification["chunk_id_count"],
        "retrieval_document_count": verification["retrieval_document_count"],
    }
    target = Path(output_path or data_dir / "published" / "release_manifest_v2.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    candidate = target.parent / f".{target.name}.{uuid.uuid4().hex}.tmp"
    try:
        candidate.write_text(_json(payload) + "\n", encoding="utf-8")
        _sync_file_and_parent(candidate)
        os.replace(candidate, target)
        _sync_file_and_parent(target)
    except Exception:
        try:
            candidate.unlink()
        except FileNotFoundError:
            pass
        raise
    return target
