import json

from fastapi.testclient import TestClient

from bgpkb.api.app import app


client = TestClient(app)


def _payload(query="route leak"):
    evidence = [
        {
            "schema_version": "evidence_v1",
            "evidence_id": "evidence_v1_" + token * 64,
            "chunk_id": f"chunk-{token}",
            "source_ref": f"source-{token}#section",
            "content_hash": "sha256:" + token * 64,
        }
        for token in ("a", "b")
    ]
    claims = [
        {
            "schema_version": "grounded_claim_v1",
            "claim_type": "factual",
            "text": "路由泄露会违反预期传播策略。",
            "evidence_ids": [item["evidence_id"] for item in evidence],
            "confidence": 0.9,
        }
    ]
    return {
        "query": query,
        "answer": "路由泄露会违反预期传播策略。",
        "answer_status": "answered",
        "generated": True,
        "claims": claims,
        "evidence": evidence,
        "grounding_status": "validated",
        "model": "deepseek-v4-pro",
        "model_revision": "DeepSeek-V4-Pro@2026-04-24",
        "citations": [
            {
                "evidence_id": item["evidence_id"],
                "chunk_id": item["chunk_id"],
                "source_ref": item["source_ref"],
            }
            for item in evidence
        ],
        "context_pack": {
            "schema_version": "context_pack_v2",
            "results": [{"chunk_id": "chunk-a"}, {"chunk_id": "chunk-b"}],
            "citations": [],
            "evidence": evidence,
            "context_groups": [],
        },
        "guardrails": {"requires_citations": True},
    }


def test_fastapi_openapi_documents_grounded_fields_as_compatible_extension():
    schema = app.openapi()
    operation = schema["paths"]["/api/v1/rag/answer"]["post"]
    response_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    model_name = response_schema["$ref"].rsplit("/", 1)[-1]
    properties = schema["components"]["schemas"][model_name]["properties"]

    assert {"answer", "citations", "context_pack"} <= set(properties)
    assert {"claims", "evidence", "grounding_status", "model", "model_revision"} <= set(properties)


def test_fastapi_answer_keeps_old_fields_and_returns_multiple_grounded_references(monkeypatch):
    monkeypatch.setattr(
        "bgpkb.api.app.repository.rag_answer_payload",
        lambda query, limit=8, progress=None: _payload(query),
    )

    response = client.post("/api/v1/rag/answer", json={"query": "route leak", "limit": 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"]
    assert len(payload["citations"]) == 2
    assert payload["context_pack"]["results"]
    assert payload["grounding_status"] == "validated"
    assert payload["model_revision"] == "DeepSeek-V4-Pro@2026-04-24"
    assert len(payload["claims"][0]["evidence_ids"]) == 2
    assert len(payload["evidence"]) == 2


def test_fastapi_sse_keeps_stage_order_and_done_payload_extensions(monkeypatch):
    def fake_payload(query, limit=8, progress=None, **_kwargs):
        for stage in ("retrieval", "rerank", "context_pack", "generation"):
            progress({"type": "stage", "stage": stage, "status": "complete", "message": stage})
        return _payload(query)

    monkeypatch.setattr("bgpkb.api.app.repository.rag_answer_stream_payload", fake_payload)

    response = client.post("/api/v1/rag/answer/stream", json={"query": "route leak", "limit": 3})
    events = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]

    assert [event.get("stage", event["type"]) for event in events] == [
        "accepted",
        "retrieval",
        "rerank",
        "context_pack",
        "generation",
        "done",
    ]
    assert events[-1]["type"] == "done"
    assert events[-1]["payload"]["grounding_status"] == "validated"
    assert len(events[-1]["payload"]["citations"]) == 2
    assert len(events[-1]["payload"]["claims"]) == 1
