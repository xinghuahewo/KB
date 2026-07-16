from fastapi.testclient import TestClient
import json
import pytest

from bgpkb.api.app import app


CLIENT_A = "client-a-12345678901234567890123456789012"
CLIENT_B = "client-b-12345678901234567890123456789012"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("BGP_CHAT_DB_PATH", str(tmp_path / "chat" / "history.sqlite3"))
    monkeypatch.setenv("BGP_CHAT_CLIENT_SALT", "test-salt")
    return TestClient(app)


def _headers(client_id=CLIENT_A):
    return {"X-BGP-Client-ID": client_id}


def _events(response):
    return [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]


def test_conversation_crud_is_paginated_and_client_scoped(client):
    first = client.post("/api/v1/conversations", headers=_headers(), json={"title": "第一条会话"})
    second = client.post("/api/v1/conversations", headers=_headers(), json={"title": "第二条会话"})

    assert first.status_code == 201
    assert second.status_code == 201
    page = client.get("/api/v1/conversations", headers=_headers(), params={"limit": 1})
    assert page.status_code == 200
    assert len(page.json()["items"]) == 1
    assert page.json()["next_cursor"]
    next_page = client.get(
        "/api/v1/conversations",
        headers=_headers(),
        params={"limit": 1, "cursor": page.json()["next_cursor"]},
    )
    assert next_page.status_code == 200
    assert next_page.json()["items"][0]["conversation_id"] != page.json()["items"][0]["conversation_id"]

    conversation_id = first.json()["conversation_id"]
    assert client.get(f"/api/v1/conversations/{conversation_id}", headers=_headers()).status_code == 200
    assert client.get(f"/api/v1/conversations/{conversation_id}", headers=_headers(CLIENT_B)).status_code == 404
    assert client.delete(f"/api/v1/conversations/{conversation_id}", headers=_headers(CLIENT_B)).status_code == 404
    assert client.delete(f"/api/v1/conversations/{conversation_id}", headers=_headers()).status_code == 204
    assert client.get(f"/api/v1/conversations/{conversation_id}", headers=_headers()).status_code == 404


def test_conversation_api_validates_client_header_and_cursor(client):
    assert client.get("/api/v1/conversations").status_code == 422
    assert client.get("/api/v1/conversations", headers=_headers("too-short")).status_code == 422
    assert client.get("/api/v1/conversations", headers=_headers(), params={"cursor": "bad"}).status_code == 422


def test_legacy_v2_import_is_idempotent_and_preserves_evidence(client):
    legacy = {
        "version": 2,
        "id": "legacy-local-id",
        "updatedAt": "2026-07-01T00:00:00.000Z",
        "messages": [
            {"id": "u1", "role": "user", "content": "RPKI 如何工作？"},
            {
                "id": "a1",
                "role": "assistant",
                "content": "RPKI 使用 ROA。",
                "answerStatus": "answered",
                "evidence": {
                    "citations": [
                        {
                            "citation_id": "ev_1",
                            "chunk_id": "chunk-rpki",
                            "source_id": "rfc6811",
                            "content_preview": "Route Origin Authorization (ROA) binds a prefix to an AS.",
                        }
                    ]
                },
            },
        ],
    }

    first = client.post("/api/v1/conversations/import", headers=_headers(), json=legacy)
    second = client.post("/api/v1/conversations/import", headers=_headers(), json=legacy)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["conversation_id"] == second.json()["conversation_id"]
    assert len(second.json()["messages"]) == 2
    assert second.json()["messages"][1]["citations"][0]["citation_id"] == "ev_1"


def test_chat_database_failure_does_not_mask_published_database_health(tmp_path, monkeypatch):
    bad_path = tmp_path / "directory"
    bad_path.mkdir()
    monkeypatch.setenv("BGP_CHAT_DB_PATH", str(bad_path))
    monkeypatch.setattr(
        "bgpkb.api.app.database.health_status",
        lambda: {"service": "bgp-knowledge-base-service", "integrity_check": "ok"},
    )

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["integrity_check"] == "ok"
    assert payload["chat_history"]["writable"] is False


def test_conversation_turn_stream_persists_before_done_and_retry_is_idempotent(client, monkeypatch):
    conversation = client.post("/api/v1/conversations", headers=_headers(), json={}).json()

    def fake_stream(query, limit=8, progress=None, **kwargs):
        progress({"type": "stage", "stage": "retrieval", "status": "started", "message": "检索"})
        progress({"type": "answer_delta", "delta": "增量一"})
        progress({"type": "answer_delta", "delta": "增量二"})
        return {
            "query": query,
            "answer": "增量一增量二[1]",
            "answer_parts": [
                {"type": "text", "text": "增量一增量二"},
                {"type": "citation", "citation_ids": ["ev_1"], "label": "1"},
            ],
            "answer_status": "answered",
            "stream_mode": "streaming",
            "citations": [{
                "citation_id": "ev_1",
                "chunk_id": "chunk-1",
                "source_id": "rfc6811",
                "content_preview": "Route Origin Authorization (ROA) binds a prefix to an AS.",
                "context_snapshot": "完整证据",
                "release_id": "release-1",
            }],
            "context_pack": {},
            "timings": {"total_ms": 10},
        }

    monkeypatch.setattr("bgpkb.api.app.repository.rag_answer_stream_payload", fake_stream)
    body = {"request_id": "request-00000001", "query": "什么是 ROA？", "limit": 8}
    first = client.post(
        f"/api/v1/conversations/{conversation['conversation_id']}/turns/stream",
        headers=_headers(),
        json=body,
    )
    first_events = _events(first)

    assert [event["sequence"] for event in first_events] == list(range(1, len(first_events) + 1))
    assert [event["delta"] for event in first_events if event["type"] == "answer_delta"] == ["增量一", "增量二"]
    assert first_events[-1]["type"] == "done"
    detail = client.get(
        f"/api/v1/conversations/{conversation['conversation_id']}", headers=_headers()
    ).json()
    assert len(detail["messages"]) == 2
    assert detail["messages"][1]["content"] == "增量一增量二[1]"
    assert detail["messages"][1]["timings"]["persistence_ms"] >= 0

    retry = client.post(
        f"/api/v1/conversations/{conversation['conversation_id']}/turns/stream",
        headers=_headers(),
        json=body,
    )
    assert _events(retry)[-1]["type"] == "done"
    detail_after_retry = client.get(
        f"/api/v1/conversations/{conversation['conversation_id']}", headers=_headers()
    ).json()
    assert len(detail_after_retry["messages"]) == 2


def test_conversation_stream_error_preserves_partial_answer(client, monkeypatch):
    conversation = client.post("/api/v1/conversations", headers=_headers(), json={}).json()

    def failing_stream(query, limit=8, progress=None, **kwargs):
        progress({"type": "answer_delta", "delta": "已经生成的部分"})
        raise RuntimeError("provider failed")

    monkeypatch.setattr("bgpkb.api.app.repository.rag_answer_stream_payload", failing_stream)
    response = client.post(
        f"/api/v1/conversations/{conversation['conversation_id']}/turns/stream",
        headers=_headers(),
        json={"request_id": "request-00000002", "query": "问题"},
    )

    events = _events(response)
    assert events[-1]["type"] == "error"
    assert events[-1]["partial_answer"] == "已经生成的部分"
    detail = client.get(
        f"/api/v1/conversations/{conversation['conversation_id']}", headers=_headers()
    ).json()
    assert detail["messages"][1]["content"] == "已经生成的部分"
    assert detail["messages"][1]["answer_status"] == "error"


def test_stop_endpoint_marks_turn_terminal_without_disclosing_other_clients(client):
    conversation = client.post("/api/v1/conversations", headers=_headers(), json={}).json()
    from bgpkb.infrastructure.chat_store import ChatRepository, hash_client_id

    repository = ChatRepository()
    repository.begin_turn(
        hash_client_id(CLIENT_A), conversation["conversation_id"], "request-00000003", "问题"
    )

    hidden = client.post(
        f"/api/v1/conversations/{conversation['conversation_id']}/turns/request-00000003/stop",
        headers=_headers(CLIENT_B),
    )
    stopped = client.post(
        f"/api/v1/conversations/{conversation['conversation_id']}/turns/request-00000003/stop",
        headers=_headers(),
    )

    assert hidden.status_code == 404
    assert stopped.status_code == 200
    assert stopped.json()["status"] == "stopped"


def test_message_scoped_evidence_loads_full_sentence_and_rejects_cross_turn(client, monkeypatch, tmp_path):
    data_dir = tmp_path / "release" / "data"
    published = data_dir / "published"
    datasets = data_dir / "derived" / "datasets"
    chunks_dir = data_dir / "corpus" / "chunks"
    published.mkdir(parents=True)
    datasets.mkdir(parents=True)
    chunks_dir.mkdir(parents=True)
    (published / "manifest.json").write_text('{"release_id":"release-1"}', encoding="utf-8")
    (published / "chunk_catalog.jsonl").write_text(
        json.dumps({
            "chunk_id": "chunk-roa",
            "chunk_file": "data/corpus/chunks/rpki.jsonl",
            "doc_id": "rfc6811",
        }) + "\n",
        encoding="utf-8",
    )
    (datasets / "section_catalog.jsonl").write_text(
        json.dumps({
            "section_id": "section-rpki",
            "doc_id": "rfc6811",
            "heading": "Introduction",
            "section_order": 1,
            "child_chunk_ids": ["chunk-roa"],
            "child_section_ids": [],
        }) + "\n",
        encoding="utf-8",
    )
    (chunks_dir / "rpki.jsonl").write_text(
        json.dumps({
            "chunk_id": "chunk-roa",
            "doc_id": "rfc6811",
            "parent_section_id": "section-rpki",
            "chunk_order": 1,
            "content": (
                "The repository binds prefixes to owning ASes, called Route Origin Authorization (ROA). "
                "Routers then validate announcements."
            ),
        }) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("BGPKB_DATA_DIR", str(data_dir))
    monkeypatch.setenv("BGPKB_RELEASE_ID", "release-1")
    conversation = client.post("/api/v1/conversations", headers=_headers(), json={}).json()
    from bgpkb.infrastructure.chat_store import ChatRepository, hash_client_id

    repository = ChatRepository()
    handle = repository.begin_turn(
        hash_client_id(CLIENT_A), conversation["conversation_id"], "request-00000004", "问题"
    )
    repository.finalize_turn(
        conversation["conversation_id"],
        "request-00000004",
        content="回答[1]",
        answer_status="answered",
        timings={},
        stream_mode="streaming",
        answer_parts=[],
        citations=[{
            "citation_id": "ev_1",
            "chunk_id": "chunk-roa",
            "source_id": "rfc6811",
            "section_id": "section-rpki",
            "content_preview": "The repository binds prefixes to owning ASes, called Route Origin Authorization (ROA).",
            "release_id": "release-0",
        }],
        last_sequence=1,
    )
    url = (
        f"/api/v1/conversations/{conversation['conversation_id']}/messages/"
        f"{handle.assistant_message_id}/evidence/ev_1"
    )

    detail = client.get(url, headers=_headers())
    cross_client = client.get(url, headers=_headers(CLIENT_B))
    cross_message = client.get(url.replace(handle.assistant_message_id, "message-other"), headers=_headers())
    traversal = client.get(url.replace("ev_1", "..%2F..%2Fsecret"), headers=_headers())

    assert detail.status_code == 200
    assert detail.json()["available"] is True
    assert detail.json()["release_mismatch"] is True
    assert detail.json()["snapshot_release_id"] == "release-0"
    assert "Route Origin Authorization (ROA)" in detail.json()["complete_sentence"]
    assert detail.json()["sections"][0]["chunks"][0]["is_highlight"] is True
    assert cross_client.status_code == 404
    assert cross_message.status_code == 404
    assert traversal.status_code in {404, 422}
