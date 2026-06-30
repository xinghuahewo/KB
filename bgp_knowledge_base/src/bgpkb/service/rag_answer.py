from . import hybrid_retrieval, llm_client


def _guardrails(blocked_reason=""):
    payload = {
        "requires_citations": True,
        "read_only": True,
        "local_model_enabled": False,
        "allows_knowledge_base_writes": False,
    }
    if blocked_reason:
        payload["blocked_reason"] = blocked_reason
    return payload


def answer_question(query, limit=8, client=None):
    pack = hybrid_retrieval.context_pack(query, limit=limit)
    citations = pack.get("citations", [])
    if not citations:
        return {
            "query": query,
            "answer": "",
            "answer_status": "no_evidence",
            "generated": False,
            "model_provider": "none",
            "model": "",
            "citations": [],
            "context_pack": pack,
            "guardrails": _guardrails("no_citations"),
        }

    active_client = client or llm_client.DeepSeekClient.from_env()
    result = active_client.generate_answer(query, pack.get("results", []))
    if not result.get("ok"):
        return {
            "query": query,
            "answer": "",
            "answer_status": "llm_unavailable",
            "generated": False,
            "model_provider": result.get("provider", "deepseek"),
            "model": result.get("model", getattr(active_client, "model", "")),
            "error_code": result.get("error_code", "llm_error"),
            "error": result.get("error", ""),
            "citations": citations,
            "context_pack": pack,
            "guardrails": _guardrails(),
        }

    return {
        "query": query,
        "answer": result.get("content", ""),
        "answer_status": "answered",
        "generated": True,
        "model_provider": result.get("provider", "deepseek"),
        "model": result.get("model", getattr(active_client, "model", "")),
        "usage": result.get("raw_usage", {}),
        "citations": citations,
        "context_pack": pack,
        "guardrails": _guardrails(),
    }
