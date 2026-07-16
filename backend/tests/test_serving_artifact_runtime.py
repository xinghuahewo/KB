import os
import sqlite3

from fastapi.testclient import TestClient
import pytest

from bgpkb.api.app import app
from bgpkb.infrastructure import database


def test_serving_artifact_health_and_database_are_read_only(monkeypatch, tmp_path):
    monkeypatch.setenv("BGP_CHAT_DB_PATH", str(tmp_path / "chat.sqlite3"))

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["release_id"] == os.environ["BGPKB_RELEASE_ID"]
    assert payload["schema_version"] == "serving_sqlite_v1"
    assert payload["integrity_check"] == "ok"
    assert payload["degraded"] is False
    with database.connect() as connection:
        assert connection.execute("PRAGMA query_only").fetchone()[0] == 1
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            connection.execute("CREATE TABLE deployment_probe(value INTEGER)")


def test_serving_artifact_keeps_traceable_retrieval_api(monkeypatch, tmp_path):
    monkeypatch.setenv("BGP_CHAT_DB_PATH", str(tmp_path / "chat.sqlite3"))

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/retrieval/search",
            params={"q": "route leak", "limit": 3},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "route leak"
    assert payload["results"]
    assert all(
        item["chunk_id"]
        and item["source_ref"]
        and item["content_preview"]
        and item["retrieval_method"]
        for item in payload["results"]
    )
