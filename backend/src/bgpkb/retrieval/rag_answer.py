import os

from bgpkb.infrastructure import llm_client

from . import hybrid_retrieval


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


def _emit(progress, stage, status, message, **metadata):
    if progress is None:
        return
    progress({
        "stage": stage,
        "status": status,
        "message": message,
        **metadata,
    })


def answer_question(query, limit=8, client=None, progress=None):
    require_reranker_model = os.environ.get("BGP_RAG_REQUIRE_RERANKER", "").lower() in {"1", "true", "yes"}
    _emit(progress, "retrieval", "started", "正在进行混合检索")
    pack = hybrid_retrieval.context_pack(
        query,
        limit=limit,
        require_model=require_reranker_model,
        progress=progress,
    )
    citations = pack.get("citations", [])
    _emit(
        progress,
        "context_pack",
        "complete",
        "证据上下文已组装",
        citation_count=len(citations),
        result_count=len(pack.get("results", [])),
        context_unit_count=len(pack.get("context_units", [])),
        retrieval_latency_ms=pack.get("retrieval_latency_ms"),
        context_assembly_latency_ms=pack.get("context_assembly_latency_ms"),
        degraded=bool(pack.get("degraded", False)),
    )
    if not citations:
        _emit(progress, "done", "no_evidence", "没有找到足够证据", answer_status="no_evidence")
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
    _emit(progress, "generation", "started", "正在生成回答", model=getattr(active_client, "model", ""))
    result = active_client.generate_answer(query, _llm_context_items(pack))
    if not result.get("ok"):
        _emit(
            progress,
            "done",
            "llm_unavailable",
            "模型暂时不可用",
            answer_status="llm_unavailable",
            error_code=result.get("error_code", "llm_error"),
        )
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

    _emit(progress, "done", "answered", "回答生成完成", answer_status="answered")
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


def _llm_context_items(pack):
    units = pack.get("context_units") or []
    if not units:
        return pack.get("results", [])
    items = []
    for unit in units:
        first_citation = (unit.get("citations") or [{}])[0]
        items.append({
            "chunk_id": ",".join(unit.get("included_chunk_ids", [])),
            "title": unit.get("context_id", ""),
            "source_ref": first_citation.get("source_ref", ""),
            "content_preview": unit.get("content", ""),
        })
    return items
