from pathlib import Path
import json

from bgpkb import paths
import sys

from fastapi.testclient import TestClient


ROOT = paths.PROJECT_ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgpkb.service.app import app  # noqa: E402


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
    manifest = json.loads((paths.PUBLISHED_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert payload["chunks"] == manifest["counts"]["chunks"]
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


def test_hybrid_api_returns_fused_search_and_context_pack():
    search = client.get("/api/v1/hybrid/search", params={"q": "route leak", "limit": 3})
    pack = client.get("/api/v1/hybrid/context-pack", params={"q": "路由泄露", "limit": 3})

    assert search.status_code == 200
    search_payload = search.json()
    assert search_payload["results"]
    assert search_payload["vector_status"] in {"complete", "failed"}
    if search_payload["vector_status"] == "failed":
        assert search_payload["degraded"] is True
        assert search_payload["channel_errors"]["vector"]["code"] in {
            "embedding_unavailable", "index_unavailable"
        }
    assert {"rrf_score", "fusion_score", "match_channels"} <= set(search_payload["results"][0])
    first = search_payload["results"][0]
    for channel in first["match_channels"]:
        assert {f"{channel}_raw_score", f"{channel}_raw_rank"} <= set(first)

    assert pack.status_code == 200
    pack_payload = pack.json()
    assert pack_payload["citations"]
    assert all(item["trusted"] is True for item in pack_payload["results"])
    assert pack_payload["trusted_chunk_policy"] == "approved_entity_evidence_or_processed_source_with_traceability"


def test_hybrid_context_pack_accepts_stage_b_parameters_and_rejects_invalid_values():
    ok = client.get("/api/v1/hybrid/context-pack", params={
        "q": "路由泄露",
        "top_n": 5,
        "query_type": "fact",
        "token_budget": 6000,
        "require_model": "false",
    })
    old_limit = client.get("/api/v1/hybrid/context-pack", params={"q": "路由泄露", "limit": 3})
    bad_top_n = client.get("/api/v1/hybrid/context-pack", params={"q": "路由泄露", "top_n": 4})
    bad_query_type = client.get("/api/v1/hybrid/context-pack", params={"q": "路由泄露", "query_type": "other"})
    bad_budget = client.get("/api/v1/hybrid/context-pack", params={"q": "路由泄露", "token_budget": 9000})

    assert ok.status_code == 200
    payload = ok.json()
    assert payload["schema_version"] == "context_pack_v2"
    assert payload["requested_query_type"] == "fact"
    assert payload["resolved_query_type"] == "fact"
    assert payload["token_budget"] == 6000
    assert payload["reranked_chunk_count"] <= 5

    assert old_limit.status_code == 200
    assert old_limit.json()["deprecated_parameters"]["limit"] == "use top_n"
    assert bad_top_n.status_code == 422
    assert bad_query_type.status_code == 422
    assert bad_budget.status_code == 422


def test_rag_answer_api_returns_evidence_when_llm_key_is_missing(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    response = client.post("/api/v1/rag/answer", json={"query": "route leak", "limit": 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "route leak"
    assert payload["answer_status"] == "llm_unavailable"
    assert payload["generated"] is False
    assert payload["citations"]
    assert payload["context_pack"]["results"]
    assert payload["guardrails"]["local_model_enabled"] is False


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
