from pathlib import Path

from bgpkb import paths
import sys


ROOT = paths.PROJECT_ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgpkb.service import rag_answer  # noqa: E402


class SuccessfulClient:
    model = "deepseek-chat"

    def generate_answer(self, query, context_items):
        return {
            "ok": True,
            "provider": "deepseek",
            "model": self.model,
            "content": f"基于 {len(context_items)} 条证据回答：{query}",
            "raw_usage": {"total_tokens": 42},
        }


class UnavailableClient:
    model = "deepseek-chat"

    def generate_answer(self, query, context_items):
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
        self.context_items = None

    def generate_answer(self, query, context_items):
        self.context_items = context_items
        return {
            "ok": True,
            "provider": "deepseek",
            "model": self.model,
            "content": "ok",
            "raw_usage": {},
        }


def test_answer_question_generates_traceable_answer_when_evidence_exists():
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
    assert payload["guardrails"]["requires_citations"] is True


def test_answer_question_falls_back_to_evidence_when_llm_is_unavailable():
    payload = rag_answer.answer_question("route leak", limit=3, client=UnavailableClient())

    assert payload["answer_status"] == "llm_unavailable"
    assert payload["generated"] is False
    assert payload["answer"] == ""
    assert payload["citations"]
    assert payload["error_code"] == "missing_api_key"


def test_answer_question_refuses_generation_without_evidence():
    payload = rag_answer.answer_question("zzzzqqqxxxx", limit=3, client=SuccessfulClient())

    assert payload["answer_status"] == "no_evidence"
    assert payload["generated"] is False
    assert payload["answer"] == ""
    assert payload["citations"] == []
    assert payload["guardrails"]["blocked_reason"] == "no_citations"


def test_answer_question_sends_context_unit_content_to_llm(monkeypatch):
    fake_pack = {
        "results": [{"chunk_id": "raw", "content_preview": "raw retrieval"}],
        "context_units": [{
            "context_id": "u1",
            "content": "assembled context",
            "included_chunk_ids": ["c1"],
            "citations": [{"chunk_id": "c1", "source_ref": "s1"}],
        }],
        "citations": [{"chunk_id": "c1", "source_ref": "s1"}],
    }
    monkeypatch.setattr(rag_answer.hybrid_retrieval, "context_pack", lambda *args, **kwargs: fake_pack)
    client = CapturingClient()

    payload = rag_answer.answer_question("q", limit=5, client=client)

    assert payload["answer_status"] == "answered"
    assert client.context_items == [{
        "chunk_id": "c1",
        "title": "u1",
        "source_ref": "s1",
        "content_preview": "assembled context",
    }]
