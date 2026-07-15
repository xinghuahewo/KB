from pathlib import Path
import json

from bgpkb import paths
import sys


ROOT = paths.PROJECT_ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgpkb.infrastructure import llm_client  # noqa: E402


def test_deepseek_client_binds_explicit_release_model_revision(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_MODEL_REVISION", "deepseek-chat@release-rev-a")

    client = llm_client.DeepSeekClient.from_env()

    assert client.provider == "deepseek"
    assert client.release_eligible is True
    assert client.model_revision == "deepseek-chat@release-rev-a"


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


def test_deepseek_client_builds_dedicated_structured_mapping_prompt():
    client = llm_client.DeepSeekClient(api_key="test-key")
    items = [{
        "candidate_type": "relation",
        "local_value": "secures",
        "source_refs": ["rfc8205"],
        "evidence_summary": "BGPsec 关系证据。",
        "examples": [{"src_id": "bgpsec", "dst_id": "as_path"}],
    }]

    payload = client.build_standard_mapping_payload(items, "standard_mapping_v1")

    assert payload["response_format"] == {"type": "json_object"}
    assert payload["temperature"] == 0
    assert "pending_review" in payload["messages"][0]["content"]
    assert "问答助手" not in payload["messages"][0]["content"]
    assert "standard_mapping_v1" in payload["messages"][1]["content"]
    assert "rfc8205" in payload["messages"][1]["content"]
    user_payload = json.loads(payload["messages"][1]["content"])
    assert "candidate_id" not in user_payload["required_fields"]
    assert "input_fingerprint" not in user_payload["required_fields"]
    assert "status" not in user_payload["required_fields"]


def test_deepseek_client_builds_query_type_classification_prompt():
    client = llm_client.DeepSeekClient(api_key="test-key")

    payload = client.build_query_type_classification_payload(
        "如何排查 route leak？", "query_type_classification_v1",
    )

    assert payload["response_format"] == {"type": "json_object"}
    assert payload["temperature"] == 0
    assert "fact / procedure / policy / global" in payload["messages"][0]["content"]
    assert "auto" in payload["messages"][0]["content"]
    user_payload = json.loads(payload["messages"][1]["content"])
    assert user_payload["prompt_version"] == "query_type_classification_v1"
    assert user_payload["allowed_output_values"] == ["fact", "procedure", "policy", "global"]
    assert user_payload["query"] == "如何排查 route leak？"


def test_deepseek_client_builds_global_summary_prompt_without_adding_citations():
    client = llm_client.DeepSeekClient(api_key="test-key")

    payload = client.build_global_summary_payload(
        query="总结 route leak 规范",
        context="chunk-a: MUST NOT leak routes",
        max_tokens=400,
        prompt_version="global_section_summary_v1",
    )

    assert payload["temperature"] == 0
    assert payload["response_format"] == {"type": "json_object"}
    assert "不得新增引用" in payload["messages"][0]["content"]
    user_payload = json.loads(payload["messages"][1]["content"])
    assert user_payload["max_tokens"] == 400
    assert user_payload["prompt_version"] == "global_section_summary_v1"


def test_deepseek_classify_and_summarize_report_missing_key_without_network():
    client = llm_client.DeepSeekClient(api_key="")

    classified = client.classify_query_type("什么是 route leak?", "query_type_classification_v1")
    summarized = client.summarize_context("总结", "证据", 400, "global_section_summary_v1")

    assert classified["ok"] is False
    assert classified["error_code"] == "missing_api_key"
    assert summarized["ok"] is False
    assert summarized["error_code"] == "missing_api_key"
