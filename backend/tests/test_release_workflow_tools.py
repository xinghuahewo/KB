from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT_SCRIPT = (
    REPOSITORY_ROOT
    / ".agents"
    / "skills"
    / "db-push-merge-deploy"
    / "scripts"
    / "preflight.py"
)
CHAT_DATABASE_TOOL = REPOSITORY_ROOT / "scripts" / "chat-database-maintenance"
REQUIRED_CHAT_TABLES = {
    "conversations",
    "messages",
    "message_evidence",
    "turn_requests",
}


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _create_chat_database(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA wal_autocheckpoint = 0")
    connection.executescript(
        """
        CREATE TABLE conversations (
            conversation_id TEXT PRIMARY KEY,
            title TEXT NOT NULL
        );
        CREATE TABLE messages (
            message_id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL
        );
        CREATE TABLE message_evidence (
            evidence_id INTEGER PRIMARY KEY,
            assistant_message_id TEXT NOT NULL
        );
        CREATE TABLE turn_requests (
            conversation_id TEXT NOT NULL,
            request_id TEXT NOT NULL,
            PRIMARY KEY(conversation_id, request_id)
        );
        PRAGMA user_version = 1;
        """
    )
    connection.commit()
    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    connection.execute(
        "INSERT INTO conversations(conversation_id, title) VALUES (?, ?)",
        ("conversation-in-wal", "WAL 中的会话"),
    )
    connection.commit()
    return connection


def _run_chat_database_tool(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHAT_DATABASE_TOOL), *arguments],
        cwd=REPOSITORY_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_preflight_uses_direct_sqlite_inspection_as_the_chat_database_gate(tmp_path):
    preflight = _load_module("release_preflight", PREFLIGHT_SCRIPT)
    database = tmp_path / "chat.sqlite3"
    connection = _create_chat_database(database)
    connection.close()
    inspection_calls: list[str] = []

    remote = {
        "chat_db": str(database),
        "fastapi_health": json.dumps(
            {"degraded": False, "integrity_check": "ok", "release_id": "artifact-v1"}
        ),
        "frontend_health": json.dumps(
            {"degraded": False, "integrity_check": "ok", "release_id": "artifact-v1"}
        ),
    }

    errors = preflight.validate_remote_health(
        remote,
        lambda path: (
            inspection_calls.append(path)
            or {
                "ok": True,
                "database_path": path,
                "database_exists": True,
                "writable": True,
                "integrity_check": "ok",
                "schema_version": 1,
                "required_tables_present": True,
            }
        ),
    )

    assert errors == []
    assert inspection_calls == [str(database)]
    assert remote["chat_history_source"] == "direct_sqlite_inspect"
    assert remote["chat_history_summary"]["integrity_check"] == "ok"


@pytest.mark.parametrize(
    "fallback",
    [
        {
            "ok": False,
            "database_exists": True,
            "writable": True,
            "integrity_check": "database disk image is malformed",
            "schema_version": 1,
            "required_tables_present": True,
        },
        {
            "ok": False,
            "database_exists": True,
            "writable": False,
            "integrity_check": "ok",
            "schema_version": 1,
            "required_tables_present": True,
        },
    ],
)
def test_preflight_fails_closed_when_direct_sqlite_inspection_is_unhealthy(fallback):
    preflight = _load_module("release_preflight_unhealthy", PREFLIGHT_SCRIPT)
    remote = {
        "chat_db": "/runtime/chat.sqlite3",
        "fastapi_health": json.dumps({"degraded": False, "integrity_check": "ok"}),
        "frontend_health": json.dumps({"degraded": False, "integrity_check": "ok"}),
    }

    errors = preflight.validate_remote_health(remote, lambda _path: fallback)

    assert errors
    assert remote["chat_history_source"] == "direct_sqlite_inspect"


def test_preflight_does_not_treat_current_health_chat_node_as_the_database_gate():
    preflight = _load_module("release_preflight_direct_inspection", PREFLIGHT_SCRIPT)
    calls: list[str] = []
    remote = {
        "chat_db": "/runtime/chat.sqlite3",
        "fastapi_health": json.dumps(
            {
                "degraded": False,
                "integrity_check": "ok",
                "chat_history": {
                    "writable": False,
                    "integrity_check": "failed",
                    "schema_version": 1,
                },
            }
        ),
        "frontend_health": json.dumps(
            {
                "degraded": False,
                "integrity_check": "ok",
                "chat_history": {
                    "writable": False,
                    "integrity_check": "failed",
                    "schema_version": 1,
                },
            }
        ),
    }

    errors = preflight.validate_remote_health(
        remote,
        lambda path: (
            calls.append(path)
            or {
                "ok": True,
                "database_path": path,
                "database_exists": True,
                "writable": True,
                "integrity_check": "ok",
                "schema_version": 1,
                "schema_compatible": True,
                "required_tables_present": True,
            }
        ),
    )

    assert errors == []
    assert calls == ["/runtime/chat.sqlite3"]
    assert remote["chat_history_source"] == "direct_sqlite_inspect"


def test_backup_captures_committed_wal_data_and_emits_verified_receipt(tmp_path):
    database = tmp_path / "chat.sqlite3"
    writer = _create_chat_database(database)
    backup_dir = tmp_path / "backups"

    completed = _run_chat_database_tool(
        "backup",
        "--database",
        str(database),
        "--backup-dir",
        str(backup_dir),
        "--timestamp",
        "20260727T010203Z",
    )
    writer.close()

    assert completed.returncode == 0, completed.stderr
    receipt = json.loads(completed.stdout)
    backup_path = Path(receipt["backup_path"])
    assert backup_path.exists()
    assert receipt["integrity_check"] == "ok"
    assert receipt["schema_version"] == 1
    assert receipt["required_tables_present"] is True
    assert len(receipt["sha256"]) == 64
    assert receipt["size_bytes"] == backup_path.stat().st_size
    assert backup_dir.stat().st_mode & 0o777 == 0o700
    assert backup_path.stat().st_mode & 0o777 == 0o600
    with sqlite3.connect(backup_path) as backup:
        assert backup.execute(
            "SELECT title FROM conversations WHERE conversation_id = ?",
            ("conversation-in-wal",),
        ).fetchone() == ("WAL 中的会话",)


def test_backup_refuses_to_overwrite_existing_target(tmp_path):
    database = tmp_path / "chat.sqlite3"
    connection = _create_chat_database(database)
    connection.close()
    target = tmp_path / "existing.sqlite3"
    target.write_bytes(b"keep-me")

    completed = _run_chat_database_tool(
        "backup",
        "--database",
        str(database),
        "--output",
        str(target),
    )

    assert completed.returncode != 0
    assert target.read_bytes() == b"keep-me"


def test_corrupt_source_never_leaves_a_formal_or_temporary_backup(tmp_path):
    database = tmp_path / "corrupt.sqlite3"
    database.write_bytes(b"not a sqlite database")
    backup_dir = tmp_path / "backups"

    completed = _run_chat_database_tool(
        "backup",
        "--database",
        str(database),
        "--backup-dir",
        str(backup_dir),
        "--timestamp",
        "20260727T010203Z",
    )

    assert completed.returncode != 0
    assert not list(backup_dir.glob("chat_history-*.sqlite3"))
    assert not list(backup_dir.glob(".*.tmp-*"))


def test_inspect_rejects_incompatible_or_incomplete_chat_database(tmp_path):
    database = tmp_path / "incomplete.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE conversations(conversation_id TEXT PRIMARY KEY)")
        connection.execute("PRAGMA user_version = 2")

    completed = _run_chat_database_tool("inspect", "--database", str(database))

    assert completed.returncode != 0
    payload = json.loads(completed.stdout)
    assert payload["integrity_check"] == "ok"
    assert payload["schema_version"] == 2
    assert payload["required_tables_present"] is False
    assert payload["schema_compatible"] is False


def test_inspect_fails_closed_when_chat_database_is_not_writable(tmp_path):
    database = tmp_path / "readonly.sqlite3"
    connection = _create_chat_database(database)
    connection.close()
    database.chmod(0o400)

    completed = _run_chat_database_tool("inspect", "--database", str(database))

    assert completed.returncode != 0
    payload = json.loads(completed.stdout)
    assert payload["integrity_check"] == "ok"
    assert payload["writable"] is False
    assert payload["ok"] is False
