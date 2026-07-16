from bgpkb.retrieval import rag_answer
import json
import time


FAKE_PACK = {
    "results": [{"chunk_id": "c1", "content_preview": "evidence", "title": "RFC"}],
    "context_units": [{
        "context_id": "unit-1",
        "content": "full evidence",
        "included_chunk_ids": ["c1"],
        "citations": [{"chunk_id": "c1", "source_ref": "rfc1#s1"}],
        "parent_section_id": "s1",
        "parent_section_heading": "Section 1",
    }],
    "citations": [{"chunk_id": "c1", "source_ref": "rfc1#s1"}],
    "retrieval_latency_ms": 4.0,
    "context_assembly_latency_ms": 2.0,
}


class SlowStreamingClient:
    model = "slow-test-model"

    def stream_answer(self, query, context_items):
        assert context_items[0]["citation_id"] == "ev_1"
        yield {"type": "delta", "delta": "路由泄露"}
        yield {"type": "delta", "delta": "超出预期范围"}
        yield {"type": "delta", "delta": "[[cite:"}
        yield {"type": "delta", "delta": "ev_1]]。"}
        yield {"type": "usage", "usage": {"total_tokens": 20}}


class BufferedClient:
    model = "buffered-test-model"

    def generate_answer(self, query, context_items):
        return {"ok": True, "provider": "test", "model": self.model, "content": "完整回答", "raw_usage": {}}


def _fake_context_pack(*args, **kwargs):
    progress = kwargs.get("progress")
    if progress:
        progress({"stage": "retrieval", "status": "complete", "message": "检索完成", "retrieval_latency_ms": 4.0})
        progress({"stage": "rerank", "status": "complete", "message": "精排完成", "latency_ms": 3.0})
    return FAKE_PACK


def test_streaming_answer_emits_multiple_deltas_before_done_and_records_timings(monkeypatch):
    monkeypatch.setattr(rag_answer.hybrid_retrieval, "context_pack", _fake_context_pack)
    events = []

    payload = rag_answer.answer_question(
        "区别是什么？", client=SlowStreamingClient(), stream=True, progress=events.append
    )

    types = [event["type"] for event in events]
    assert types.count("answer_delta") >= 2
    assert types.index("answer_delta") < len(types) - 1
    assert any(event["type"] == "citation_delta" for event in events)
    assert payload["answer"] == "路由泄露超出预期范围[1]。"
    assert payload["stream_mode"] == "streaming"
    assert payload["timings"]["model_ttft_ms"] <= payload["timings"]["total_ms"]
    assert payload["timings"]["time_to_first_answer_ms"] <= payload["timings"]["total_ms"]
    stage_pairs = {(event.get("stage"), event.get("status")) for event in events if event["type"] == "stage"}
    assert {("retrieval", "started"), ("retrieval", "complete"), ("rerank", "started"), ("rerank", "complete")} <= stage_pairs


def test_non_stream_provider_is_explicitly_buffered(monkeypatch):
    monkeypatch.setattr(rag_answer.hybrid_retrieval, "context_pack", _fake_context_pack)
    events = []

    payload = rag_answer.answer_question("问题", client=BufferedClient(), stream=True, progress=events.append)

    assert payload["stream_mode"] == "buffered"
    assert any(event["type"] == "answer_snapshot" for event in events)
    assert not any(event["type"] == "answer_delta" for event in events)


def test_stop_preserves_partial_answer(monkeypatch):
    monkeypatch.setattr(rag_answer.hybrid_retrieval, "context_pack", _fake_context_pack)
    checks = iter([False, True])

    payload = rag_answer.answer_question(
        "问题",
        client=SlowStreamingClient(),
        stream=True,
        stop_requested=lambda: next(checks, True),
    )

    assert payload["answer_status"] == "stopped"
    assert payload["answer"] == "路由泄露"


def test_sse_channel_sends_heartbeat_during_slow_provider(monkeypatch):
    from bgpkb.api import app as api_app

    monkeypatch.setattr(api_app, "_SSE_HEARTBEAT_SECONDS", 0.005)

    def slow_work(emit):
        time.sleep(0.018)
        emit({"type": "done", "payload": {}})

    frames = list(api_app._event_stream(slow_work))
    events = [json.loads(frame.removeprefix("data: ")) for frame in frames]

    assert any(event["type"] == "heartbeat" for event in events)
    assert events[-1]["type"] == "done"
    assert [event["sequence"] for event in events] == list(range(1, len(events) + 1))
