"""独立的运行时会话 SQLite 存储。

该模块只写入 ``BGP_CHAT_DB_PATH``，不得复用发布知识库连接。
匿名客户端标识仅用于命名空间隔离，不构成认证。
"""

from __future__ import annotations

import base64
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Iterator
import uuid

from bgpkb import paths


SCHEMA_VERSION = 1
DEFAULT_RELATIVE_PATH = Path("runtime/chat/chat_history.sqlite3")
DEFAULT_PENDING_TIMEOUT_SECONDS = 300


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    client_key_hash TEXT NOT NULL,
    title TEXT NOT NULL,
    import_key TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(client_key_hash, import_key)
);
CREATE INDEX IF NOT EXISTS idx_conversations_owner_updated
    ON conversations(client_key_hash, updated_at DESC, conversation_id DESC);

CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL DEFAULT '',
    answer_status TEXT,
    timings_json TEXT,
    stream_mode TEXT,
    answer_parts_json TEXT,
    sync_status TEXT NOT NULL DEFAULT 'synced',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(conversation_id, ordinal)
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages(conversation_id, ordinal);

CREATE TABLE IF NOT EXISTS message_evidence (
    evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    assistant_message_id TEXT NOT NULL REFERENCES messages(message_id) ON DELETE CASCADE,
    citation_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_ref TEXT,
    title TEXT,
    source_type TEXT,
    section_id TEXT,
    section_heading TEXT,
    content_preview TEXT NOT NULL DEFAULT '',
    context_snapshot TEXT NOT NULL DEFAULT '',
    release_id TEXT,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(assistant_message_id, citation_id)
);
CREATE INDEX IF NOT EXISTS idx_message_evidence_message
    ON message_evidence(assistant_message_id, citation_id);

CREATE TABLE IF NOT EXISTS turn_requests (
    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    request_id TEXT NOT NULL,
    user_message_id TEXT NOT NULL REFERENCES messages(message_id) ON DELETE CASCADE,
    assistant_message_id TEXT NOT NULL REFERENCES messages(message_id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    last_sequence INTEGER NOT NULL DEFAULT 0,
    partial_answer TEXT NOT NULL DEFAULT '',
    error_code TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY(conversation_id, request_id)
);
CREATE INDEX IF NOT EXISTS idx_turn_requests_status_updated
    ON turn_requests(status, updated_at);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def runtime_chat_database_path() -> Path:
    configured = os.environ.get("BGP_CHAT_DB_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return (paths.PROJECT_ROOT / DEFAULT_RELATIVE_PATH).resolve()


def hash_client_id(client_id: str) -> str:
    salt = os.environ.get("BGP_CHAT_CLIENT_SALT") or "bgpkb-private-chat-namespace-v1"
    return hashlib.sha256(f"{salt}:{client_id}".encode("utf-8")).hexdigest()


def deterministic_title(question: str, maximum: int = 42) -> str:
    compact = " ".join(question.split()) or "新会话"
    return compact if len(compact) <= maximum else compact[: maximum - 1].rstrip() + "…"


def _json_dump(value: Any) -> str | None:
    return None if value is None else json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _json_load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _encode_cursor(updated_at: str, conversation_id: str) -> str:
    raw = json.dumps([updated_at, conversation_id], separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(cursor: str) -> tuple[str, str]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        value = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        if not isinstance(value, list) or len(value) != 2 or not all(isinstance(item, str) for item in value):
            raise ValueError
        return value[0], value[1]
    except Exception as exc:
        raise ValueError("invalid cursor") from exc


@dataclass(frozen=True)
class TurnHandle:
    conversation_id: str
    request_id: str
    user_message_id: str
    assistant_message_id: str
    status: str
    existing: bool


class ChatRepository:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path or runtime_chat_database_path()).resolve()

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            current_version = conn.execute("PRAGMA user_version").fetchone()[0]
            if current_version > SCHEMA_VERSION:
                raise RuntimeError(
                    f"会话数据库 schema v{current_version} 高于当前支持的 v{SCHEMA_VERSION}"
                )
            conn.executescript(SCHEMA_SQL)
            if current_version < SCHEMA_VERSION:
                conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
            except Exception:
                conn.rollback()
                raise
            else:
                conn.commit()

    def health(self) -> dict[str, Any]:
        status: dict[str, Any] = {
            "database_path": str(self.db_path),
            "database_exists": self.db_path.exists(),
            "schema_version": None,
            "integrity_check": None,
            "writable": False,
        }
        try:
            self.initialize()
            with self.connect() as conn:
                status["schema_version"] = conn.execute("PRAGMA user_version").fetchone()[0]
                status["integrity_check"] = conn.execute("PRAGMA quick_check").fetchone()[0]
                conn.execute("CREATE TEMP TABLE IF NOT EXISTS _chat_health(value INTEGER)")
                status["writable"] = True
                status["database_exists"] = True
        except Exception as exc:
            status["error"] = str(exc)
        return status

    def converge_stale_pending(self, timeout_seconds: int = DEFAULT_PENDING_TIMEOUT_SECONDS) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)).isoformat(
            timespec="milliseconds"
        ).replace("+00:00", "Z")
        now = utc_now()
        with self.transaction() as conn:
            rows = conn.execute(
                "SELECT assistant_message_id FROM turn_requests WHERE status = 'pending' AND updated_at < ?",
                (cutoff,),
            ).fetchall()
            if not rows:
                return 0
            conn.execute(
                "UPDATE turn_requests SET status = 'interrupted', updated_at = ? "
                "WHERE status = 'pending' AND updated_at < ?",
                (now, cutoff),
            )
            conn.executemany(
                "UPDATE messages SET answer_status = 'interrupted', sync_status = 'synced', updated_at = ? "
                "WHERE message_id = ?",
                [(now, row["assistant_message_id"]) for row in rows],
            )
            return len(rows)

    def create_conversation(
        self,
        client_hash: str,
        title: str = "新会话",
        *,
        conversation_id: str | None = None,
        import_key: str | None = None,
    ) -> dict[str, Any]:
        self.initialize()
        now = utc_now()
        conversation_id = conversation_id or f"conversation-{uuid.uuid4()}"
        with self.transaction() as conn:
            if import_key:
                existing = conn.execute(
                    "SELECT * FROM conversations WHERE client_key_hash = ? AND import_key = ?",
                    (client_hash, import_key),
                ).fetchone()
                if existing:
                    return self._conversation_summary(existing)
            conn.execute(
                "INSERT INTO conversations(conversation_id, client_key_hash, title, import_key, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (conversation_id, client_hash, deterministic_title(title), import_key, now, now),
            )
            row = conn.execute("SELECT * FROM conversations WHERE conversation_id = ?", (conversation_id,)).fetchone()
        return self._conversation_summary(row)

    def list_conversations(self, client_hash: str, limit: int = 20, cursor: str | None = None) -> dict[str, Any]:
        self.initialize()
        params: list[Any] = [client_hash]
        where = "client_key_hash = ?"
        if cursor:
            updated_at, conversation_id = _decode_cursor(cursor)
            where += " AND (updated_at < ? OR (updated_at = ? AND conversation_id < ?))"
            params.extend([updated_at, updated_at, conversation_id])
        params.append(limit + 1)
        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM conversations WHERE {where} "
                "ORDER BY updated_at DESC, conversation_id DESC LIMIT ?",
                params,
            ).fetchall()
            items = [self._conversation_summary(row, conn) for row in rows[:limit]]
        next_cursor = None
        if len(rows) > limit and items:
            last = items[-1]
            next_cursor = _encode_cursor(last["updated_at"], last["conversation_id"])
        return {"items": items, "next_cursor": next_cursor}

    def get_conversation(self, client_hash: str, conversation_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE conversation_id = ? AND client_key_hash = ?",
                (conversation_id, client_hash),
            ).fetchone()
            if not row:
                return None
            messages = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY ordinal",
                (conversation_id,),
            ).fetchall()
            evidence_rows = conn.execute(
                "SELECT e.* FROM message_evidence e JOIN messages m ON m.message_id = e.assistant_message_id "
                "WHERE m.conversation_id = ? ORDER BY e.evidence_id",
                (conversation_id,),
            ).fetchall()
        evidence_by_message: dict[str, list[dict[str, Any]]] = {}
        for evidence in evidence_rows:
            evidence_by_message.setdefault(evidence["assistant_message_id"], []).append(
                self._evidence_payload(evidence)
            )
        return {
            **self._conversation_summary(row),
            "messages": [self._message_payload(message, evidence_by_message.get(message["message_id"], [])) for message in messages],
        }

    def delete_conversation(self, client_hash: str, conversation_id: str) -> bool:
        self.initialize()
        with self.transaction() as conn:
            cursor = conn.execute(
                "DELETE FROM conversations WHERE conversation_id = ? AND client_key_hash = ?",
                (conversation_id, client_hash),
            )
            return cursor.rowcount > 0

    def begin_turn(
        self,
        client_hash: str,
        conversation_id: str,
        request_id: str,
        question: str,
        *,
        user_message_id: str | None = None,
        assistant_message_id: str | None = None,
    ) -> TurnHandle | None:
        self.initialize()
        now = utc_now()
        with self.transaction() as conn:
            conversation = conn.execute(
                "SELECT * FROM conversations WHERE conversation_id = ? AND client_key_hash = ?",
                (conversation_id, client_hash),
            ).fetchone()
            if not conversation:
                return None
            existing = conn.execute(
                "SELECT * FROM turn_requests WHERE conversation_id = ? AND request_id = ?",
                (conversation_id, request_id),
            ).fetchone()
            if existing:
                return TurnHandle(
                    conversation_id,
                    request_id,
                    existing["user_message_id"],
                    existing["assistant_message_id"],
                    existing["status"],
                    True,
                )
            next_ordinal = conn.execute(
                "SELECT COALESCE(MAX(ordinal), 0) + 1 FROM messages WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()[0]
            user_message_id = user_message_id or f"message-{uuid.uuid4()}"
            assistant_message_id = assistant_message_id or f"message-{uuid.uuid4()}"
            conn.execute(
                "INSERT INTO messages(message_id, conversation_id, ordinal, role, content, sync_status, created_at, updated_at) "
                "VALUES (?, ?, ?, 'user', ?, 'synced', ?, ?)",
                (user_message_id, conversation_id, next_ordinal, question, now, now),
            )
            conn.execute(
                "INSERT INTO messages(message_id, conversation_id, ordinal, role, content, answer_status, stream_mode, "
                "sync_status, created_at, updated_at) VALUES (?, ?, ?, 'assistant', '', 'pending', 'streaming', 'syncing', ?, ?)",
                (assistant_message_id, conversation_id, next_ordinal + 1, now, now),
            )
            conn.execute(
                "INSERT INTO turn_requests(conversation_id, request_id, user_message_id, assistant_message_id, status, "
                "created_at, updated_at) VALUES (?, ?, ?, ?, 'pending', ?, ?)",
                (conversation_id, request_id, user_message_id, assistant_message_id, now, now),
            )
            title = conversation["title"]
            if title == "新会话":
                title = deterministic_title(question)
            conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE conversation_id = ?",
                (title, now, conversation_id),
            )
        return TurnHandle(conversation_id, request_id, user_message_id, assistant_message_id, "pending", False)

    def checkpoint_turn(
        self,
        conversation_id: str,
        request_id: str,
        content: str,
        last_sequence: int,
        timings: dict[str, Any] | None = None,
    ) -> None:
        now = utc_now()
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT assistant_message_id FROM turn_requests WHERE conversation_id = ? AND request_id = ?",
                (conversation_id, request_id),
            ).fetchone()
            if not row:
                return
            conn.execute(
                "UPDATE turn_requests SET partial_answer = ?, last_sequence = ?, updated_at = ? "
                "WHERE conversation_id = ? AND request_id = ?",
                (content, last_sequence, now, conversation_id, request_id),
            )
            conn.execute(
                "UPDATE messages SET content = ?, timings_json = COALESCE(?, timings_json), updated_at = ? "
                "WHERE message_id = ?",
                (content, _json_dump(timings), now, row["assistant_message_id"]),
            )

    def finalize_turn(
        self,
        conversation_id: str,
        request_id: str,
        *,
        content: str,
        answer_status: str,
        timings: dict[str, Any] | None,
        stream_mode: str,
        answer_parts: list[dict[str, Any]] | None,
        citations: list[dict[str, Any]],
        last_sequence: int,
        error_code: str | None = None,
    ) -> dict[str, Any] | None:
        now = utc_now()
        with self.transaction() as conn:
            request = conn.execute(
                "SELECT * FROM turn_requests WHERE conversation_id = ? AND request_id = ?",
                (conversation_id, request_id),
            ).fetchone()
            if not request:
                return None
            assistant_id = request["assistant_message_id"]
            conn.execute(
                "UPDATE messages SET content = ?, answer_status = ?, timings_json = ?, stream_mode = ?, "
                "answer_parts_json = ?, sync_status = 'synced', updated_at = ? WHERE message_id = ?",
                (
                    content,
                    answer_status,
                    _json_dump(timings),
                    stream_mode,
                    _json_dump(answer_parts or []),
                    now,
                    assistant_id,
                ),
            )
            conn.execute("DELETE FROM message_evidence WHERE assistant_message_id = ?", (assistant_id,))
            for citation in citations:
                citation_id = str(citation.get("citation_id") or "")
                chunk_id = str(citation.get("chunk_id") or citation.get("chunkId") or "")
                source_id = str(citation.get("source_id") or citation.get("sourceId") or citation.get("source_ref") or "")
                if not citation_id or not chunk_id or not source_id:
                    continue
                conn.execute(
                    "INSERT INTO message_evidence(assistant_message_id, citation_id, chunk_id, source_id, source_ref, "
                    "title, source_type, section_id, section_heading, content_preview, context_snapshot, release_id, "
                    "payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        assistant_id,
                        citation_id,
                        chunk_id,
                        source_id,
                        citation.get("source_ref"),
                        citation.get("title"),
                        citation.get("source_type") or citation.get("sourceType"),
                        citation.get("section_id"),
                        citation.get("section_heading") or citation.get("section"),
                        citation.get("content_preview") or citation.get("contentPreview") or "",
                        citation.get("context_snapshot") or "",
                        citation.get("release_id"),
                        _json_dump(citation) or "{}",
                        now,
                    ),
                )
            conn.execute(
                "UPDATE turn_requests SET status = ?, last_sequence = ?, partial_answer = ?, error_code = ?, updated_at = ? "
                "WHERE conversation_id = ? AND request_id = ?",
                (answer_status, last_sequence, content, error_code, now, conversation_id, request_id),
            )
            conn.execute("UPDATE conversations SET updated_at = ? WHERE conversation_id = ?", (now, conversation_id))
        return self.get_message(assistant_id)

    def get_turn(self, client_hash: str, conversation_id: str, request_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self.connect() as conn:
            row = conn.execute(
                "SELECT tr.* FROM turn_requests tr JOIN conversations c ON c.conversation_id = tr.conversation_id "
                "WHERE tr.conversation_id = ? AND tr.request_id = ? AND c.client_key_hash = ?",
                (conversation_id, request_id, client_hash),
            ).fetchone()
            if not row:
                return None
        assistant = self.get_message(row["assistant_message_id"])
        return {**dict(row), "assistant_message": assistant}

    def mark_turn_stopped(self, client_hash: str, conversation_id: str, request_id: str) -> bool:
        self.initialize()
        now = utc_now()
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT tr.assistant_message_id FROM turn_requests tr "
                "JOIN conversations c ON c.conversation_id = tr.conversation_id "
                "WHERE tr.conversation_id = ? AND tr.request_id = ? AND c.client_key_hash = ?",
                (conversation_id, request_id, client_hash),
            ).fetchone()
            if not row:
                return False
            conn.execute(
                "UPDATE turn_requests SET status = 'stopped', updated_at = ? "
                "WHERE conversation_id = ? AND request_id = ?",
                (now, conversation_id, request_id),
            )
            conn.execute(
                "UPDATE messages SET answer_status = 'stopped', sync_status = 'synced', updated_at = ? "
                "WHERE message_id = ?",
                (now, row["assistant_message_id"]),
            )
            return True

    def update_message_timings(self, message_id: str, timings: dict[str, Any]) -> None:
        with self.transaction() as conn:
            conn.execute(
                "UPDATE messages SET timings_json = ?, updated_at = ? WHERE message_id = ?",
                (_json_dump(timings), utc_now(), message_id),
            )

    def get_message(self, message_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM messages WHERE message_id = ?", (message_id,)).fetchone()
            if not row:
                return None
            evidence = conn.execute(
                "SELECT * FROM message_evidence WHERE assistant_message_id = ? ORDER BY evidence_id",
                (message_id,),
            ).fetchall()
        return self._message_payload(row, [self._evidence_payload(item) for item in evidence])

    def get_scoped_evidence(
        self,
        client_hash: str,
        conversation_id: str,
        message_id: str,
        citation_id: str,
    ) -> dict[str, Any] | None:
        self.initialize()
        with self.connect() as conn:
            row = conn.execute(
                "SELECT e.* FROM message_evidence e "
                "JOIN messages m ON m.message_id = e.assistant_message_id "
                "JOIN conversations c ON c.conversation_id = m.conversation_id "
                "WHERE c.client_key_hash = ? AND c.conversation_id = ? AND m.message_id = ? AND e.citation_id = ?",
                (client_hash, conversation_id, message_id, citation_id),
            ).fetchone()
        return self._evidence_payload(row) if row else None

    def import_legacy(
        self,
        client_hash: str,
        import_key: str,
        title: str,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        summary = self.create_conversation(client_hash, title, import_key=import_key)
        existing = self.get_conversation(client_hash, summary["conversation_id"])
        if existing and existing["messages"]:
            return existing
        now = utc_now()
        with self.transaction() as conn:
            for ordinal, message in enumerate(messages, start=1):
                legacy_id = str(message.get("id") or uuid.uuid4())
                message_id = f"{summary['conversation_id']}:{legacy_id}"
                role = message.get("role") if message.get("role") in {"user", "assistant", "system"} else "user"
                conn.execute(
                    "INSERT INTO messages(message_id, conversation_id, ordinal, role, content, answer_status, "
                    "timings_json, stream_mode, answer_parts_json, sync_status, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'synced', ?, ?)",
                    (
                        message_id,
                        summary["conversation_id"],
                        ordinal,
                        role,
                        str(message.get("content") or ""),
                        message.get("answerStatus") or message.get("answer_status"),
                        _json_dump(message.get("timings")),
                        message.get("streamMode") or message.get("stream_mode"),
                        _json_dump(message.get("answerParts") or message.get("answer_parts") or []),
                        message.get("createdAt") or message.get("created_at") or now,
                        now,
                    ),
                )
                for citation in ((message.get("evidence") or {}).get("citations") or []):
                    enriched = dict(citation)
                    enriched.setdefault("citation_id", f"ev_{ordinal}_{len(str(citation)) % 97}")
                    self._insert_evidence(conn, message_id, enriched, now)
            conn.execute("UPDATE conversations SET updated_at = ? WHERE conversation_id = ?", (now, summary["conversation_id"]))
        return self.get_conversation(client_hash, summary["conversation_id"]) or summary

    @staticmethod
    def _insert_evidence(conn: sqlite3.Connection, assistant_id: str, citation: dict[str, Any], now: str) -> None:
        chunk_id = str(citation.get("chunk_id") or citation.get("chunkId") or "legacy")
        source_id = str(citation.get("source_id") or citation.get("sourceId") or citation.get("source_ref") or "legacy")
        conn.execute(
            "INSERT OR IGNORE INTO message_evidence(assistant_message_id, citation_id, chunk_id, source_id, source_ref, "
            "title, source_type, section_id, section_heading, content_preview, context_snapshot, release_id, payload_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                assistant_id,
                citation["citation_id"],
                chunk_id,
                source_id,
                citation.get("source_ref"),
                citation.get("title"),
                citation.get("source_type"),
                citation.get("section_id"),
                citation.get("section_heading"),
                citation.get("content_preview") or citation.get("contentPreview") or "",
                citation.get("context_snapshot") or "",
                citation.get("release_id"),
                _json_dump(citation) or "{}",
                now,
            ),
        )

    @staticmethod
    def _conversation_summary(row: sqlite3.Row, conn: sqlite3.Connection | None = None) -> dict[str, Any]:
        message_count = 0
        if conn is not None:
            message_count = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (row["conversation_id"],)
            ).fetchone()[0]
        return {
            "conversation_id": row["conversation_id"],
            "title": row["title"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "message_count": message_count,
            "sync_status": "synced",
        }

    @staticmethod
    def _message_payload(row: sqlite3.Row, citations: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "message_id": row["message_id"],
            "role": row["role"],
            "content": row["content"],
            "answer_status": row["answer_status"],
            "timings": _json_load(row["timings_json"], None),
            "stream_mode": row["stream_mode"],
            "answer_parts": _json_load(row["answer_parts_json"], []),
            "sync_status": row["sync_status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "citations": citations,
        }

    @staticmethod
    def _evidence_payload(row: sqlite3.Row) -> dict[str, Any]:
        payload = _json_load(row["payload_json"], {})
        payload.update({
            "citation_id": row["citation_id"],
            "chunk_id": row["chunk_id"],
            "source_id": row["source_id"],
            "source_ref": row["source_ref"],
            "title": row["title"],
            "source_type": row["source_type"],
            "section_id": row["section_id"],
            "section_heading": row["section_heading"],
            "content_preview": row["content_preview"],
            "context_snapshot": row["context_snapshot"],
            "release_id": row["release_id"],
        })
        return payload
