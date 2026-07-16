import os
import time
from typing import Any

from bgpkb.domain.grounded_answering import (
    GroundingValidationError,
    validate_grounded_answer,
)
from bgpkb.infrastructure import llm_client

from . import hybrid_retrieval
from .inline_citations import IncrementalCitationParser, enrich_citations, parse_answer


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


def answer_question(query, limit=8, client=None, progress=None, stream=False, stop_requested=None):
    if stream:
        return _answer_question_streaming(
            query,
            limit=limit,
            client=client,
            progress=progress,
            stop_requested=stop_requested,
        )
    return _answer_question_buffered(query, limit=limit, client=client, progress=progress)


def _answer_question_buffered(query, limit=8, client=None, progress=None):
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


def _answer_question_streaming(query, limit=8, client=None, progress=None, stop_requested=None):
    total_started = time.perf_counter_ns()
    timings: dict[str, float | None] = {
        "retrieval_ms": None,
        "rerank_ms": None,
        "context_pack_ms": None,
        "generation_ms": None,
        "persistence_ms": 0.0,
        "model_ttft_ms": None,
        "time_to_first_answer_ms": None,
        "total_ms": None,
    }
    require_model = os.environ.get("BGP_RAG_REQUIRE_RERANKER", "").lower() in {"1", "true", "yes"}
    _stream_stage(progress, "retrieval", "started", "正在进行混合检索", elapsed_ms=0.0)
    context_started: int | None = None

    def forward(event):
        nonlocal context_started
        stage = str(event.get("stage") or "retrieval")
        forwarded = {"type": "stage", **event, "elapsed_ms": _elapsed_ms(total_started)}
        if stage == "retrieval" and event.get("status") == "complete":
            timings["retrieval_ms"] = _number(event.get("retrieval_latency_ms"), None)
            forwarded["duration_ms"] = timings["retrieval_ms"]
            _stream_event(progress, forwarded)
            _stream_stage(progress, "rerank", "started", "正在精排证据", elapsed_ms=_elapsed_ms(total_started))
            return
        if stage == "rerank" and event.get("status") == "complete":
            timings["rerank_ms"] = _number(event.get("latency_ms"), None)
            forwarded["duration_ms"] = timings["rerank_ms"]
            _stream_event(progress, forwarded)
            context_started = time.perf_counter_ns()
            _stream_stage(progress, "context_pack", "started", "正在组装引用上下文", elapsed_ms=_elapsed_ms(total_started))
            return
        _stream_event(progress, forwarded)

    pack = hybrid_retrieval.context_pack(
        query,
        limit=limit,
        require_model=require_model,
        progress=forward,
    )
    if timings["retrieval_ms"] is None:
        timings["retrieval_ms"] = _number(pack.get("retrieval_latency_ms"), 0.0)
        _stream_stage(
            progress,
            "retrieval",
            "complete",
            "候选证据召回完成",
            duration_ms=timings["retrieval_ms"],
            elapsed_ms=_elapsed_ms(total_started),
        )
    if context_started is None:
        context_started = time.perf_counter_ns()
        _stream_stage(progress, "context_pack", "started", "正在组装引用上下文", elapsed_ms=_elapsed_ms(total_started))
    timings["context_pack_ms"] = _number(
        pack.get("context_assembly_latency_ms"),
        _elapsed_ms(context_started),
    )
    citations = enrich_citations(pack)
    _stream_stage(
        progress,
        "context_pack",
        "complete",
        "证据上下文已组装",
        duration_ms=timings["context_pack_ms"],
        elapsed_ms=_elapsed_ms(total_started),
        citation_count=len(citations),
        evidence_count=len(pack.get("evidence", [])),
        result_count=len(pack.get("results", [])),
        context_unit_count=len(pack.get("context_units", [])),
        degraded=bool(pack.get("degraded", False)),
    )
    if not citations:
        timings["total_ms"] = _elapsed_ms(total_started)
        _stream_stage(progress, "done", "no_evidence", "没有找到足够证据", elapsed_ms=timings["total_ms"])
        return {
            "query": query,
            "answer": "",
            "answer_parts": [],
            "answer_status": "no_evidence",
            "inline_citation_status": "not_applicable",
            "generated": False,
            "stream_mode": "streaming",
            "model_provider": "none",
            "model": "",
            "model_revision": "",
            "claims": [],
            "evidence": [],
            "citations": [],
            "context_pack": pack,
            "grounding_status": "no_context_evidence",
            "timings": timings,
            "guardrails": _guardrails("no_citations"),
        }

    active_client = client or llm_client.DeepSeekClient.from_env()
    _stream_stage(
        progress,
        "generation",
        "started",
        "正在生成回答",
        model=getattr(active_client, "model", ""),
        elapsed_ms=_elapsed_ms(total_started),
    )
    generation_started = time.perf_counter_ns()
    result = _generate_streaming_answer(
        query,
        pack,
        citations,
        active_client,
        progress,
        total_started,
        generation_started,
        timings,
        stop_requested,
    )
    timings["generation_ms"] = _elapsed_ms(generation_started)
    timings["total_ms"] = _elapsed_ms(total_started)
    _stream_stage(
        progress,
        "generation",
        "complete" if result.get("ok") else "failed",
        "回答生成完成" if result.get("ok") else "生成中断",
        duration_ms=timings["generation_ms"],
        elapsed_ms=timings["total_ms"],
        stream_mode=result.get("stream_mode", "buffered"),
    )
    if not result.get("ok"):
        answer_status = (
            "stopped"
            if result.get("error_code") == "stopped"
            else "interrupted" if result.get("content") else "llm_unavailable"
        )
        return {
            "query": query,
            "answer": result.get("content", ""),
            "answer_parts": result.get("answer_parts", []),
            "answer_status": answer_status,
            "inline_citation_status": result.get("inline_citation_status", "missing"),
            "generated": bool(result.get("content")),
            "stream_mode": result.get("stream_mode", "buffered"),
            "model_provider": result.get("provider", "deepseek"),
            "model": result.get("model", getattr(active_client, "model", "")),
            "model_revision": getattr(active_client, "model_revision", ""),
            "error_code": result.get("error_code", "llm_error"),
            "error": result.get("error", ""),
            "claims": [],
            "evidence": [],
            "citations": citations if result.get("content") else [],
            "context_pack": pack,
            "grounding_status": "stream_interrupted",
            "timings": timings,
            "guardrails": _guardrails(),
        }
    _stream_stage(progress, "done", "answered", "回答生成完成", elapsed_ms=timings["total_ms"])
    return {
        "query": query,
        "answer": result.get("content", ""),
        "answer_parts": result.get("answer_parts", []),
        "answer_status": "answered",
        "inline_citation_status": result.get("inline_citation_status", "missing"),
        "generated": True,
        "stream_mode": result.get("stream_mode", "buffered"),
        "model_provider": result.get("provider", "deepseek"),
        "model": result.get("model", getattr(active_client, "model", "")),
        "model_revision": getattr(active_client, "model_revision", ""),
        "usage": result.get("raw_usage", {}),
        "claims": [],
        "evidence": pack.get("evidence", []),
        "citations": citations,
        "context_pack": pack,
        "grounding_status": "stream_citation_allowlist",
        "timings": timings,
        "guardrails": _guardrails(),
    }


def _generate_streaming_answer(
    query, pack, citations, client, progress, total_started, generation_started, timings, stop_requested=None
):
    if not hasattr(client, "stream_answer"):
        result = client.generate_answer(query, _llm_context_items(pack, citations))
        if not result.get("ok"):
            return {**result, "stream_mode": "buffered", "content": "", "answer_parts": []}
        content, parts, status = parse_answer(result.get("content", ""), citations)
        result = {
            **result,
            "content": content,
            "answer_parts": parts,
            "inline_citation_status": status,
            "stream_mode": "buffered",
        }
        _stream_event(progress, {
            "type": "answer_snapshot",
            "answer": content,
            "answer_parts": parts,
            "stream_mode": "buffered",
            "elapsed_ms": _elapsed_ms(total_started),
        })
        return result

    parser = IncrementalCitationParser({citation["citation_id"] for citation in citations})
    labels = {citation["citation_id"]: str(index) for index, citation in enumerate(citations, start=1)}
    content_parts: list[str] = []
    answer_parts: list[dict[str, Any]] = []
    usage: dict[str, Any] = {}
    error: dict[str, Any] | None = None
    first_visible = False
    for frame in client.stream_answer(query, _llm_context_items(pack, citations)):
        if stop_requested is not None and stop_requested():
            error = {"error_code": "stopped", "error": "用户停止生成"}
            break
        if frame.get("type") == "error":
            error = frame
            break
        if frame.get("type") == "usage":
            usage = frame.get("usage") or {}
            continue
        if frame.get("type") != "delta":
            continue
        for token in parser.feed(str(frame.get("delta") or "")):
            if token["type"] == "text":
                delta = token["text"]
                if not delta:
                    continue
                if not first_visible:
                    first_visible = True
                    timings["model_ttft_ms"] = _elapsed_ms(generation_started)
                    timings["time_to_first_answer_ms"] = _elapsed_ms(total_started)
                content_parts.append(delta)
                _append_text_part(answer_parts, delta)
                _stream_event(progress, {"type": "answer_delta", "delta": delta, "elapsed_ms": _elapsed_ms(total_started)})
            else:
                citation_ids = token["citation_ids"]
                label = ",".join(labels[citation_id] for citation_id in citation_ids)
                content_parts.append(f"[{label}]")
                answer_parts.append({"type": "citation", "citation_ids": citation_ids, "label": label})
                _stream_event(progress, {
                    "type": "citation_delta",
                    "citation_ids": citation_ids,
                    "label": label,
                    "elapsed_ms": _elapsed_ms(total_started),
                })
    for token in parser.finish():
        delta = token.get("text", "")
        if delta:
            if not first_visible:
                timings["model_ttft_ms"] = _elapsed_ms(generation_started)
                timings["time_to_first_answer_ms"] = _elapsed_ms(total_started)
            content_parts.append(delta)
            _append_text_part(answer_parts, delta)
            _stream_event(progress, {"type": "answer_delta", "delta": delta, "elapsed_ms": _elapsed_ms(total_started)})

    content = "".join(content_parts)
    status = parser.status
    if not any(part["type"] == "citation" for part in answer_parts) and status == "complete":
        status = "missing"
    base = {
        "content": content,
        "answer_parts": answer_parts,
        "inline_citation_status": status,
        "stream_mode": "streaming",
        "provider": getattr(client, "provider", "deepseek"),
        "model": getattr(client, "model", ""),
        "raw_usage": usage,
    }
    return {**base, **(error or {}), "ok": not error and bool(content)}


def _stream_stage(progress, stage, status, message, **metadata):
    _stream_event(progress, {"type": "stage", "stage": stage, "status": status, "message": message, **metadata})


def _stream_event(progress, payload):
    if progress is not None:
        progress(payload)


def _elapsed_ms(start_ns):
    return round((time.perf_counter_ns() - start_ns) / 1_000_000, 3)


def _number(value, fallback):
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return fallback


def _append_text_part(parts, delta):
    if parts and parts[-1]["type"] == "text":
        parts[-1]["text"] += delta
    else:
        parts.append({"type": "text", "text": delta})


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


def _llm_context_items(pack, citations=None):
    citations = citations or enrich_citations(pack)
    citation_by_chunk = {str(item["chunk_id"]): item["citation_id"] for item in citations}
    units = pack.get("context_units") or []
    if not units:
        return [
            {
                **item,
                "citation_id": citation_by_chunk.get(str(item.get("chunk_id")), ""),
            }
            for item in pack.get("results", [])
        ]
    items = []
    for unit in units:
        chunk_ids = [str(chunk_id) for chunk_id in unit.get("included_chunk_ids", [])]
        first_citation = (unit.get("citations") or [{}])[0]
        items.append({
            "citation_id": ",".join(citation_by_chunk[chunk_id] for chunk_id in chunk_ids if chunk_id in citation_by_chunk),
            "chunk_id": ",".join(chunk_ids),
            "title": unit.get("parent_section_heading") or unit.get("context_id", ""),
            "source_ref": first_citation.get("source_ref", ""),
            "content_preview": unit.get("content", ""),
        })
    return items
