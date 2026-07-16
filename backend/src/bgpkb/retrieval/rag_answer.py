import os

from bgpkb.domain.grounded_answering import (
    GroundingValidationError,
    validate_grounded_answer,
)
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
    context_citations = pack.get("citations", [])
    evidence = pack.get("evidence", [])
    context_groups = pack.get("context_groups", [])
    _emit(
        progress,
        "context_pack",
        "complete",
        "证据上下文已组装",
        citation_count=len(context_citations),
        evidence_count=len(evidence),
        result_count=len(pack.get("results", [])),
        context_unit_count=len(pack.get("context_units", [])),
        retrieval_latency_ms=pack.get("retrieval_latency_ms"),
        context_assembly_latency_ms=pack.get("context_assembly_latency_ms"),
        degraded=bool(pack.get("degraded", False)),
    )
    if not evidence:
        _emit(
            progress,
            "done",
            "no_evidence",
            "没有找到足够证据",
            answer_status="no_evidence",
            grounding_status="no_context_evidence",
        )
        return {
            "query": query,
            "answer": "",
            "answer_status": "no_evidence",
            "generated": False,
            "model_provider": "none",
            "model": "",
            "model_revision": "",
            "claims": [],
            "evidence": [],
            "citations": [],
            "context_pack": pack,
            "grounding_status": "no_context_evidence",
            "guardrails": _guardrails("no_citations"),
        }

    active_client = client or llm_client.DeepSeekClient.from_env()
    _emit(progress, "generation", "started", "正在生成回答", model=getattr(active_client, "model", ""))
    result = _generate_grounded(active_client, query, evidence, context_groups)
    if not result.get("ok"):
        _emit(
            progress,
            "done",
            "llm_unavailable",
            "模型暂时不可用",
            answer_status="llm_unavailable",
            grounding_status="llm_unavailable",
            error_code=result.get("error_code", "llm_error"),
        )
        return {
            "query": query,
            "answer": "",
            "answer_status": "llm_unavailable",
            "generated": False,
            "model_provider": result.get("provider", "deepseek"),
            "model": result.get("model", getattr(active_client, "model", "")),
            "model_revision": getattr(active_client, "model_revision", ""),
            "error_code": result.get("error_code", "llm_error"),
            "error": result.get("error", ""),
            "claims": [],
            "evidence": [],
            "citations": [],
            "context_pack": pack,
            "grounding_status": "llm_unavailable",
            "guardrails": _guardrails(),
        }

    repaired = False
    try:
        grounded = validate_grounded_answer(result.get("content"), evidence)
    except GroundingValidationError as first_error:
        repaired = True
        repair = {
            "attempt": 1,
            "validation_code": first_error.code,
            "allowed_evidence_ids": [item["evidence_id"] for item in evidence],
            "instruction": "仅修复结构和引用范围；不得添加外部事实或新的 evidence_id。",
        }
        result = _generate_grounded(
            active_client, query, evidence, context_groups, repair=repair
        )
        if not result.get("ok"):
            _emit(
                progress,
                "done",
                "llm_unavailable",
                "模型修复请求不可用",
                answer_status="llm_unavailable",
                grounding_status="llm_unavailable",
                error_code=result.get("error_code", "llm_error"),
            )
            return {
                "query": query,
                "answer": "",
                "answer_status": "llm_unavailable",
                "generated": False,
                "model_provider": result.get("provider", "deepseek"),
                "model": result.get("model", getattr(active_client, "model", "")),
                "model_revision": getattr(active_client, "model_revision", ""),
                "error_code": result.get("error_code", "llm_error"),
                "error": result.get("error", ""),
                "claims": [],
                "evidence": [],
                "citations": [],
                "context_pack": pack,
                "grounding_status": "llm_unavailable",
                "guardrails": _guardrails("repair_unavailable"),
            }
        try:
            grounded = validate_grounded_answer(result.get("content"), evidence)
        except GroundingValidationError as repair_error:
            _emit(
                progress,
                "done",
                "no_evidence",
                "回答未通过证据校验",
                answer_status="no_evidence",
                grounding_status="failed_after_repair",
                error_code="grounding_validation_failed",
            )
            return {
                "query": query,
                "answer": "",
                "answer_status": "no_evidence",
                "generated": False,
                "model_provider": result.get("provider", "deepseek"),
                "model": result.get("model", getattr(active_client, "model", "")),
                "model_revision": getattr(active_client, "model_revision", ""),
                "error_code": "grounding_validation_failed",
                "error": str(repair_error),
                "claims": [],
                "evidence": [],
                "citations": [],
                "context_pack": pack,
                "grounding_status": "failed_after_repair",
                "guardrails": _guardrails("grounding_validation_failed"),
            }

    if grounded["insufficient_evidence"]:
        _emit(
            progress,
            "done",
            "no_evidence",
            "模型判定证据不足",
            answer_status="no_evidence",
            grounding_status="insufficient_evidence",
        )
        return {
            "query": query,
            "answer": "",
            "answer_status": "no_evidence",
            "generated": False,
            "model_provider": result.get("provider", "deepseek"),
            "model": result.get("model", getattr(active_client, "model", "")),
            "model_revision": getattr(active_client, "model_revision", ""),
            "usage": result.get("raw_usage", {}),
            "claims": [],
            "evidence": [],
            "citations": [],
            "context_pack": pack,
            "grounding_status": "insufficient_evidence",
            "guardrails": _guardrails("insufficient_evidence"),
        }

    grounding_status = "repaired" if repaired else "validated"
    used_evidence, citations = _grounded_projection(grounded, evidence)
    _emit(
        progress,
        "done",
        "answered",
        "回答生成完成",
        answer_status="answered",
        grounding_status=grounding_status,
    )
    return {
        "query": query,
        "answer": grounded["answer"],
        "answer_status": "answered",
        "generated": True,
        "model_provider": result.get("provider", "deepseek"),
        "model": result.get("model", getattr(active_client, "model", "")),
        "model_revision": getattr(active_client, "model_revision", ""),
        "usage": result.get("raw_usage", {}),
        "claims": grounded["claims"],
        "evidence": used_evidence,
        "citations": citations,
        "context_pack": pack,
        "grounding_status": grounding_status,
        "guardrails": _guardrails(),
    }


def _generate_grounded(client, query, evidence, context_groups, repair=None):
    generate = getattr(client, "generate_grounded_answer", None)
    if generate is None:
        return {
            "ok": False,
            "provider": "unknown",
            "model": getattr(client, "model", ""),
            "error_code": "grounded_answer_not_supported",
            "error": "LLM client 不支持结构化 grounded answer。",
        }
    return generate(query, evidence, context_groups, repair=repair)


def _grounded_projection(grounded, evidence):
    evidence_by_id = {item["evidence_id"]: item for item in evidence}
    used_ids = []
    for claim in grounded["claims"]:
        for evidence_id in claim["evidence_ids"]:
            if evidence_id not in used_ids:
                used_ids.append(evidence_id)
    used_evidence = [evidence_by_id[evidence_id] for evidence_id in used_ids]
    citations = []
    for item in used_evidence:
        scores = item.get("retrieval_scores", {})
        score = next(
            (
                scores.get(name)
                for name in ("rerank_score", "fusion_score", "score")
                if scores.get(name) is not None
            ),
            None,
        )
        citations.append({
            "evidence_id": item["evidence_id"],
            "chunk_id": item["chunk_id"],
            "source_ref": item["source_ref"],
            "title": item.get("title", ""),
            "section_path": item.get("section_path", []),
            "content_hash": item["content_hash"],
            "governance": item["governance"],
            "score": score,
            "content_preview": item.get("content", "")[:240],
        })
    return used_evidence, citations


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
