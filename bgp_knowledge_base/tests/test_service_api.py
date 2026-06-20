from pathlib import Path
import sys

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from service.app import app  # noqa: E402


client = TestClient(app)


def test_health_reports_existing_sqlite_database():
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["database_exists"] is True
    assert payload["integrity_check"] == "ok"
    assert payload["service"] == "bgp-knowledge-base-service"


def test_stats_returns_core_counts_and_review_statuses():
    response = client.get("/api/v1/stats")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sources"] == 54
    assert payload["entities"] == 112
    assert payload["chunks"] == 2037
    assert payload["relationships"] == 106
    assert payload["review_statuses"]["approved"] == 107
    assert payload["review_statuses"]["pending"] == 5


def test_entity_detail_includes_sources_evidence_relationships_and_actions():
    response = client.get("/api/v1/entities/anomaly_route_leak")

    assert response.status_code == 200
    payload = response.json()
    assert payload["entity_id"] == "anomaly_route_leak"
    assert payload["name"] == "Route Leak"
    assert payload["sources"]
    assert payload["evidence"]
    assert "incoming_relationships" in payload
    assert "outgoing_relationships" in payload
    assert payload["actions"]


def test_missing_entity_returns_404():
    response = client.get("/api/v1/entities/not_exists")

    assert response.status_code == 404
    assert response.json() == {"detail": "entity not found"}


def test_source_detail_includes_entities_and_chunks():
    response = client.get("/api/v1/sources/rfc4271")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_id"] == "rfc4271"
    assert payload["entities"]
    assert payload["chunks"]


def test_entity_and_chunk_search_return_results():
    entity_response = client.get("/api/v1/search/entities", params={"q": "RPKI"})
    chunk_response = client.get("/api/v1/search/chunks", params={"q": "route leak"})

    assert entity_response.status_code == 200
    assert chunk_response.status_code == 200
    assert entity_response.json()
    assert chunk_response.json()


def test_actions_can_filter_needs_llm():
    response = client.get("/api/v1/actions", params={"needs_llm": "true"})

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert all(item["needs_llm"] == 1 for item in payload)


def test_retrieval_api_returns_traceable_search_evidence_and_context_pack():
    search = client.get("/api/v1/retrieval/search", params={"q": "route leak", "limit": 3})
    evidence = client.get("/api/v1/retrieval/evidence", params={"entity_id": "anomaly_route_leak"})
    pack = client.get("/api/v1/retrieval/context-pack", params={"q": "路由泄露", "limit": 3})

    assert search.status_code == 200
    search_payload = search.json()
    assert search_payload["query"] == "route leak"
    assert search_payload["results"]
    assert {"@id", "chunk_id", "source_ref", "review_status", "retrieval_method", "score"} <= set(search_payload["results"][0])

    assert evidence.status_code == 200
    evidence_payload = evidence.json()
    assert evidence_payload["entity_id"] == "anomaly_route_leak"
    assert evidence_payload["records"]

    assert pack.status_code == 200
    pack_payload = pack.json()
    assert pack_payload["query"] == "路由泄露"
    assert "route leak" in pack_payload["normalized_query"]
    assert pack_payload["citations"]
    assert "answer" not in pack_payload


def test_html_pages_render_search_and_entity_detail():
    home = client.get("/")
    search = client.get("/search", params={"q": "route leak"})
    entity = client.get("/entities/anomaly_route_leak")

    assert home.status_code == 200
    assert "搜索" in home.text
    assert search.status_code == 200
    assert "Route Leak" in search.text or "route leak" in search.text.lower()
    assert entity.status_code == 200
    assert "review_status" in entity.text
    assert "来源" in entity.text
    assert "证据" in entity.text
