"""仅用于本地端到端验收的慢速流式 Provider。"""

from __future__ import annotations

import time

from bgpkb.api import app as app_module


def slow_rag_payload(query, limit=8, progress=None, **kwargs):
    stages = [
        ("retrieval", "started", "正在召回候选证据", 0),
        ("retrieval", "complete", "候选证据召回完成", 120),
        ("rerank", "started", "正在精排证据", 0),
        ("rerank", "complete", "证据精排完成", 140),
        ("context_pack", "started", "正在组装引用上下文", 0),
        ("context_pack", "complete", "证据上下文已组装", 80),
        ("generation", "started", "正在生成回答", 0),
    ]
    for stage, status, message, duration in stages:
        time.sleep(0.08)
        event = {"type": "stage", "stage": stage, "status": status, "message": message}
        if duration:
            event["duration_ms"] = duration
        progress(event)

    answer_deltas = [
        "RPKI 通过签名的路由起源授权",
        "把 IP 前缀与获准起源 AS 绑定",
    ]
    for delta in answer_deltas:
        time.sleep(0.16)
        progress({"type": "answer_delta", "delta": delta})
    progress({"type": "citation_delta", "citation_ids": ["ev_1"], "label": "1"})
    time.sleep(0.12)
    progress({"type": "answer_delta", "delta": "，网络可据此执行起源验证并拒绝不匹配公告。"})
    answer = "".join(answer_deltas) + "[1]，网络可据此执行起源验证并拒绝不匹配公告。"
    citation = {
        "citation_id": "ev_1",
        "chunk_id": "chunk-rpki-roa",
        "source_id": "rfc6811",
        "source_ref": "rfc6811#introduction",
        "title": "RFC 6811 — BGP Prefix Origin Validation",
        "source_type": "standard",
        "section_id": "section-introduction",
        "section_heading": "Introduction",
        "content_preview": (
            "The RPKI stores cryptographically verifiable objects called Route Origin "
            "Authorizations (ROAs), which bind IP prefixes to authorized origin ASes."
        ),
        "context_snapshot": (
            "The RPKI stores cryptographically verifiable objects called Route Origin "
            "Authorizations (ROAs), which bind IP prefixes to authorized origin ASes."
        ),
        "release_id": "e2e-release",
    }
    return {
        "query": query,
        "answer": answer,
        "answer_parts": [
            {"type": "text", "text": "".join(answer_deltas)},
            {"type": "citation", "citation_ids": ["ev_1"], "label": "1"},
            {"type": "text", "text": "，网络可据此执行起源验证并拒绝不匹配公告。"},
        ],
        "answer_status": "answered",
        "inline_citation_status": "complete",
        "generated": True,
        "stream_mode": "streaming",
        "citations": [citation],
        "context_pack": {
            "schema_version": "context_pack_v2",
            "results": [{"chunk_id": "chunk-rpki-roa", "source_id": "rfc6811", "retrieval_method": "hybrid"}],
            "context_units": [{"parent_section_id": "section-introduction", "parent_section_heading": "Introduction"}],
        },
        "timings": {
            "retrieval_ms": 120,
            "rerank_ms": 140,
            "context_pack_ms": 80,
            "model_ttft_ms": 160,
            "time_to_first_answer_ms": 660,
            "generation_ms": 440,
            "persistence_ms": 0,
            "total_ms": 1100,
        },
    }


def fake_evidence_detail(citation, **kwargs):
    scope = kwargs.get("scope", "section")
    return {
        "citation": citation,
        "available": True,
        "complete_sentence": citation["content_preview"],
        "highlight_chunk_id": citation["chunk_id"],
        "source_id": citation["source_id"],
        "snapshot_release_id": "e2e-release",
        "current_release_id": "e2e-release",
        "release_mismatch": False,
        "scope": scope,
        "cursor": kwargs.get("cursor", 0),
        "sections": [{
            "section_id": "section-introduction",
            "heading": "Introduction",
            "chunks": [{
                "chunk_id": "chunk-rpki-roa",
                "content": citation["context_snapshot"],
                "is_highlight": True,
            }],
        }],
        "next_cursor": None,
    }


app_module.repository.rag_answer_stream_payload = slow_rag_payload
app_module.evidence_detail = fake_evidence_detail
app = app_module.app
