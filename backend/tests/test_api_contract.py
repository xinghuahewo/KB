from bgpkb.api.app import app


EXPECTED_OPERATIONS = {
    ("/", "get"),
    ("/health", "get"),
    ("/search", "get"),
    ("/entities/{entity_id}", "get"),
    ("/sources/{source_id}", "get"),
    ("/api/v1/stats", "get"),
    ("/api/v1/terms/{term}", "get"),
    ("/api/v1/entities/{entity_id}", "get"),
    ("/api/v1/entities/{entity_id}/evidence", "get"),
    ("/api/v1/entities/{entity_id}/neighbors", "get"),
    ("/api/v1/sources/{source_id}", "get"),
    ("/api/v1/search/entities", "get"),
    ("/api/v1/search/chunks", "get"),
    ("/api/v1/actions", "get"),
    ("/api/v1/retrieval/search", "get"),
    ("/api/v1/retrieval/evidence", "get"),
    ("/api/v1/retrieval/context-pack", "get"),
    ("/api/v1/hybrid/search", "get"),
    ("/api/v1/hybrid/context-pack", "get"),
    ("/api/v1/rag/answer", "post"),
    ("/api/v1/rag/answer/stream", "post"),
    ("/api/v1/progress", "get"),
    ("/api/v1/conversations", "post"),
    ("/api/v1/conversations", "get"),
    ("/api/v1/conversations/import", "post"),
    ("/api/v1/conversations/{conversation_id}", "get"),
    ("/api/v1/conversations/{conversation_id}", "delete"),
    ("/api/v1/conversations/{conversation_id}/turns/stream", "post"),
    ("/api/v1/conversations/{conversation_id}/turns/{request_id}/stop", "post"),
    ("/api/v1/conversations/{conversation_id}/messages/{message_id}/evidence/{citation_id}", "get"),
}


def test_openapi_operations_remain_available_without_runtime_artifacts(monkeypatch):
    monkeypatch.delenv("BGPKB_DATA_DIR", raising=False)

    schema = app.openapi()
    operations = {
        (path, method)
        for path, methods in schema["paths"].items()
        for method in methods
        if method in {"get", "post", "put", "patch", "delete"}
    }

    assert schema["info"]["title"] == "BGP 知识库服务"
    assert schema["info"]["version"] == "0.1.0"
    assert operations == EXPECTED_OPERATIONS
