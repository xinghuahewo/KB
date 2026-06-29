from pathlib import Path

from bgpkb import paths
import sys


ROOT = paths.PROJECT_ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgpkb.service import llm_client  # noqa: E402


def test_deepseek_client_reports_unavailable_without_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    client = llm_client.DeepSeekClient.from_env()
    result = client.generate_answer("问题", [{"content_preview": "证据"}])

    assert result["ok"] is False
    assert result["error_code"] == "missing_api_key"
    assert result["provider"] == "deepseek"


def test_deepseek_client_builds_traceable_openai_compatible_payload(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    client = llm_client.DeepSeekClient.from_env()

    payload = client.build_payload(
        query="什么是 route leak?",
        context_items=[
            {
                "chunk_id": "chunk_001",
                "title": "Route Leak",
                "source_ref": "rfc7908",
                "content_preview": "A route leak is the propagation of routing announcements beyond their intended scope.",
            }
        ],
    )

    assert payload["model"] == "deepseek-chat"
    assert payload["temperature"] == 0.2
    assert "必须基于引用证据回答" in payload["messages"][0]["content"]
    assert "chunk_001" in payload["messages"][1]["content"]
    assert "rfc7908" in payload["messages"][1]["content"]
