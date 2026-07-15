from pathlib import Path

from bgpkb import paths
from bgpkb.domain.grounded_answering import build_evidence
import json
import sys


ROOT = paths.PROJECT_ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgpkb.retrieval import rag_answer  # noqa: E402


class SuccessfulClient:
    model = "deepseek-v4-pro"
    model_revision = "DeepSeek-V4-Pro@2026-04-24"

    def generate_grounded_answer(self, query, evidence, context_groups, repair=None):
        answer = f"基于 {len(evidence)} 条证据回答：{query}"
        return {
            "ok": True,
            "provider": "deepseek",
            "model": self.model,
            "content": json.dumps({
                "schema_version": "grounded_answer_v1",
                "answer": answer,
                "claims": [{
                    "schema_version": "grounded_claim_v1",
                    "claim_type": "factual",
                    "text": answer,
                    "evidence_ids": [evidence[0]["evidence_id"]],
                    "confidence": 0.9,
                }],
                "evidence_ids": [evidence[0]["evidence_id"]],
                "confidence": 0.9,
                "insufficient_evidence": False,
            }, ensure_ascii=False),
            "raw_usage": {"total_tokens": 42},
        }


class UnavailableClient:
    model = "deepseek-chat"

    def generate_grounded_answer(self, query, evidence, context_groups, repair=None):
        return {
            "ok": False,
            "provider": "deepseek",
            "model": self.model,
            "error_code": "missing_api_key",
            "error": "DEEPSEEK_API_KEY is not configured.",
        }


class CapturingClient:
    model = "deepseek-chat"

    def __init__(self):
        self.evidence = None
        self.context_groups = None

    def generate_grounded_answer(self, query, evidence, context_groups, repair=None):
        self.evidence = evidence
        self.context_groups = context_groups
        return SuccessfulClient().generate_grounded_answer(query, evidence, context_groups, repair)


def _structured_pack(content="assembled context"):
    group_id = "context_group_v1_" + "a" * 64
    evidence = build_evidence(
        chunk_id="c1",
        doc_id="doc-a",
        source_ref="s1",
        title="u1",
        section_path=["Root"],
        content=content,
        governance={
            "parse_status": "parsed",
            "content_quality_status": "approved",
            "source_trust_status": "trusted",
            "semantic_review_status": "approved",
            "retrieval_eligibility": "eligible",
        },
        retrieval_scores={"score": 0.8, "fusion_score": 0.85, "rerank_score": 0.9},
        context_group_id=group_id,
        member_index=0,
        start_char=0,
        end_char=len(content),
    )
    return {
        "results": [{"chunk_id": "c1", "content_preview": content, "trusted": True}],
        "context_units": [{
            "context_id": "u1",
            "content": content,
            "included_chunk_ids": ["c1"],
            "evidence_ids": [evidence["evidence_id"]],
            "citations": [{"chunk_id": "c1", "source_ref": "s1"}],
        }],
        "evidence": [evidence],
        "context_groups": [{
            "schema_version": "context_group_v1",
            "context_group_id": group_id,
            "context_id": "u1",
            "mode": "matched_chunk",
            "doc_id": "doc-a",
            "section_path": ["Root"],
            "content": content,
            "member_evidence_ids": [evidence["evidence_id"]],
            "members": [{
                "evidence_id": evidence["evidence_id"],
                "chunk_id": "c1",
                "source_ref": "s1",
                "member_index": 0,
                "start_char": 0,
                "end_char": len(content),
            }],
        }],
        "citations": [{"chunk_id": "c1", "source_ref": "s1"}],
        "generated_by": "src/bgpkb/service/hybrid_retrieval.py",
        "trusted_chunk_policy": "approved_entity_evidence_or_processed_source_with_traceability",
    }


def test_answer_question_generates_traceable_answer_when_evidence_exists(monkeypatch):
    monkeypatch.setattr(
        rag_answer.hybrid_retrieval,
        "context_pack",
        lambda *args, **kwargs: _structured_pack(),
    )
    payload = rag_answer.answer_question("route leak", limit=3, client=SuccessfulClient())

    assert payload["answer_status"] == "answered"
    assert payload["generated"] is True
    assert payload["answer"].startswith("基于")
    assert payload["citations"]
    assert payload["context_pack"]["results"]
    assert payload["context_pack"]["generated_by"] == "src/bgpkb/service/hybrid_retrieval.py"
    assert payload["context_pack"]["trusted_chunk_policy"] == "approved_entity_evidence_or_processed_source_with_traceability"
    assert all(item["trusted"] is True for item in payload["context_pack"]["results"])
    assert payload["model_provider"] == "deepseek"
    assert payload["model"] == "deepseek-v4-pro"
    assert payload["model_revision"] == "DeepSeek-V4-Pro@2026-04-24"
    assert payload["guardrails"]["requires_citations"] is True


def test_answer_question_falls_back_to_evidence_when_llm_is_unavailable():
    payload = rag_answer.answer_question("route leak", limit=3, client=UnavailableClient())

    assert payload["answer_status"] == "llm_unavailable"
    assert payload["generated"] is False
    assert payload["answer"] == ""
    assert payload["citations"] == []
    assert payload["context_pack"]["evidence"]
    assert payload["error_code"] == "missing_api_key"


def test_answer_question_refuses_generation_without_evidence(monkeypatch):
    empty_pack = {
        "query": "zzzzqqqxxxx",
        "results": [],
        "citations": [],
        "context_units": [],
        "generated_by": "src/bgpkb/service/hybrid_retrieval.py",
        "trusted_chunk_policy": "approved_entity_evidence_or_processed_source_with_traceability",
    }
    monkeypatch.setattr(rag_answer.hybrid_retrieval, "context_pack", lambda query, limit=None, **kwargs: empty_pack)
    payload = rag_answer.answer_question("zzzzqqqxxxx", limit=3, client=SuccessfulClient())

    assert payload["answer_status"] == "no_evidence"
    assert payload["generated"] is False
    assert payload["answer"] == ""
    assert payload["citations"] == []
    assert payload["guardrails"]["blocked_reason"] == "no_citations"


def test_answer_question_sends_context_unit_content_to_llm(monkeypatch):
    fake_pack = _structured_pack()
    monkeypatch.setattr(rag_answer.hybrid_retrieval, "context_pack", lambda *args, **kwargs: fake_pack)
    client = CapturingClient()

    payload = rag_answer.answer_question("q", limit=5, client=client)

    assert payload["answer_status"] == "answered"
    assert client.evidence == fake_pack["evidence"]
    assert client.context_groups == fake_pack["context_groups"]


def test_answer_question_can_require_real_reranker_with_env(monkeypatch):
    captured = {}
    fake_pack = _structured_pack()

    def fake_context_pack(*args, **kwargs):
        captured.update(kwargs)
        return fake_pack

    monkeypatch.setenv("BGP_RAG_REQUIRE_RERANKER", "1")
    monkeypatch.setattr(rag_answer.hybrid_retrieval, "context_pack", fake_context_pack)

    payload = rag_answer.answer_question("q", limit=8, client=SuccessfulClient())

    assert payload["answer_status"] == "answered"
    assert captured["require_model"] is True


def test_answer_question_reports_progress_stages(monkeypatch):
    fake_pack = _structured_pack()
    events = []

    def fake_context_pack(*args, **kwargs):
        kwargs["progress"]({
            "stage": "rerank",
            "status": "complete",
            "message": "精排完成",
        })
        return fake_pack

    monkeypatch.setattr(rag_answer.hybrid_retrieval, "context_pack", fake_context_pack)

    payload = rag_answer.answer_question("q", limit=8, client=SuccessfulClient(), progress=events.append)

    assert payload["answer_status"] == "answered"
    assert [event["stage"] for event in events] == [
        "retrieval",
        "rerank",
        "context_pack",
        "generation",
        "done",
    ]
    assert events[-1]["answer_status"] == "answered"
