import sqlite3

import pytest

from bgpkb.infrastructure.chat_store import ChatRepository, SCHEMA_VERSION, hash_client_id


def _repository(tmp_path):
    repository = ChatRepository(tmp_path / "runtime" / "chat.sqlite3")
    repository.initialize()
    return repository


def test_chat_schema_migrates_to_current_version_and_enables_runtime_pragmas(tmp_path):
    repository = _repository(tmp_path)

    with repository.connect() as conn:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        foreign_keys = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]

    assert {"conversations", "messages", "message_evidence", "turn_requests"} <= tables
    assert version == SCHEMA_VERSION
    assert foreign_keys == 1
    assert journal_mode == "wal"
    assert repository.health()["writable"] is True


def test_chat_repository_rolls_back_failed_transaction(tmp_path):
    repository = _repository(tmp_path)

    with pytest.raises(RuntimeError):
        with repository.transaction() as conn:
            conn.execute(
                "INSERT INTO conversations VALUES (?, ?, ?, ?, ?, ?)",
                ("c1", "owner", "会话", None, "now", "now"),
            )
            raise RuntimeError("rollback")

    with repository.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0] == 0


def test_chat_repository_isolates_clients_and_cascades_delete(tmp_path):
    repository = _repository(tmp_path)
    owner_a = hash_client_id("client-a-12345678901234567890123456789012")
    owner_b = hash_client_id("client-b-12345678901234567890123456789012")
    conversation = repository.create_conversation(owner_a)
    handle = repository.begin_turn(owner_a, conversation["conversation_id"], "request-1", "什么是 ROA？")
    assert handle is not None
    repository.finalize_turn(
        conversation["conversation_id"],
        "request-1",
        content="ROA 是路由起源授权。",
        answer_status="answered",
        timings={"total_ms": 12},
        stream_mode="streaming",
        answer_parts=[{"type": "text", "text": "ROA 是路由起源授权。"}],
        citations=[{
            "citation_id": "ev_1",
            "chunk_id": "chunk-1",
            "source_id": "rfc6811",
            "content_preview": "Route Origin Authorization (ROA) binds a prefix to an origin AS.",
        }],
        last_sequence=4,
    )

    assert repository.get_conversation(owner_b, conversation["conversation_id"]) is None
    assert repository.delete_conversation(owner_b, conversation["conversation_id"]) is False
    assert repository.delete_conversation(owner_a, conversation["conversation_id"]) is True

    with repository.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM message_evidence").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM turn_requests").fetchone()[0] == 0


def test_chat_repository_converges_stale_pending_and_preserves_partial_answer(tmp_path):
    repository = _repository(tmp_path)
    owner = hash_client_id("client-a-12345678901234567890123456789012")
    conversation = repository.create_conversation(owner)
    handle = repository.begin_turn(owner, conversation["conversation_id"], "request-1", "问题")
    assert handle is not None
    repository.checkpoint_turn(conversation["conversation_id"], "request-1", "部分回答", 9)
    with repository.connect() as conn:
        conn.execute(
            "UPDATE turn_requests SET updated_at = '2000-01-01T00:00:00.000Z' WHERE request_id = 'request-1'"
        )
        conn.commit()

    assert repository.converge_stale_pending(timeout_seconds=1) == 1
    turn = repository.get_turn(owner, conversation["conversation_id"], "request-1")
    assert turn["status"] == "interrupted"
    assert turn["assistant_message"]["content"] == "部分回答"
    assert turn["assistant_message"]["answer_status"] == "interrupted"


def test_chat_repository_keeps_message_and_evidence_transactional(tmp_path, monkeypatch):
    repository = _repository(tmp_path)
    owner = hash_client_id("client-a-12345678901234567890123456789012")
    conversation = repository.create_conversation(owner)
    handle = repository.begin_turn(owner, conversation["conversation_id"], "request-1", "问题")
    assert handle is not None

    original = repository._evidence_payload

    def fail_after_write(*args, **kwargs):
        raise sqlite3.OperationalError("forced")

    monkeypatch.setattr(repository, "get_message", fail_after_write)
    with pytest.raises(sqlite3.OperationalError):
        repository.finalize_turn(
            conversation["conversation_id"],
            "request-1",
            content="回答",
            answer_status="answered",
            timings={},
            stream_mode="streaming",
            answer_parts=[],
            citations=[],
            last_sequence=1,
        )

    monkeypatch.setattr(repository, "get_message", lambda message_id: {"message_id": message_id})
    # finalize_turn 的事务已经完成后才读取返回消息；即使读取失败，持久化终态仍应一致。
    with repository.connect() as conn:
        row = conn.execute("SELECT answer_status, content FROM messages WHERE message_id = ?", (handle.assistant_message_id,)).fetchone()
    assert dict(row) == {"answer_status": "answered", "content": "回答"}
    monkeypatch.setattr(repository, "_evidence_payload", original)
