import pytest

from bgpkb.retrieval.query_type_resolver import QueryTypeResolver, resolve_query_type


class FakeClassifier:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def classify_query_type(self, query, prompt_version):
        self.calls.append((query, prompt_version))
        return self.response


def test_explicit_query_type_wins_without_deepseek_call():
    client = FakeClassifier({"ok": True, "query_type": "global"})

    result = resolve_query_type("什么是 route leak", requested_query_type="policy", client=client)

    assert result["requested_query_type"] == "policy"
    assert result["resolved_query_type"] == "policy"
    assert result["provider"] == "explicit"
    assert result["degraded"] is False
    assert client.calls == []


def test_invalid_requested_query_type_is_rejected():
    with pytest.raises(ValueError, match="query_type"):
        resolve_query_type("q", requested_query_type="other")


def test_auto_rejects_deepseek_auto_and_falls_back_to_auditable_rules():
    client = FakeClassifier({
        "ok": True,
        "provider": "deepseek",
        "model": "deepseek-chat",
        "query_type": "auto",
        "reason": "ambiguous",
    })

    result = resolve_query_type("如何按步骤排查 route leak？", requested_query_type="auto", client=client)

    assert client.calls == [("如何按步骤排查 route leak？", "query_type_classification_v1")]
    assert result["requested_query_type"] == "auto"
    assert result["resolved_query_type"] == "procedure"
    assert result["provider"] == "rule_based"
    assert result["degraded"] is True
    assert result["degraded_reason"] == "deepseek_invalid_query_type"
    assert "步骤" in result["reason"]


def test_auto_uses_deepseek_valid_structured_result():
    client = FakeClassifier({
        "ok": True,
        "provider": "deepseek",
        "model": "deepseek-chat",
        "query_type": "global",
        "reason": "跨章节总结",
    })

    result = QueryTypeResolver(client=client).resolve("总结这些 RFC 对 route leak 的共同约束", "auto")

    assert result["resolved_query_type"] == "global"
    assert result["provider"] == "deepseek"
    assert result["prompt_version"] == "query_type_classification_v1"
    assert result["reason"] == "跨章节总结"
    assert result["degraded"] is False


def test_auto_falls_back_to_policy_then_fact_when_deepseek_unavailable():
    failed = FakeClassifier({
        "ok": False,
        "provider": "deepseek",
        "error_code": "missing_api_key",
        "error": "DEEPSEEK_API_KEY is not configured.",
    })

    policy = resolve_query_type("RFC 7908 中 MUST NOT 约束是什么？", "auto", client=failed)
    fact = resolve_query_type("AS_PATH 是什么？", "auto", client=failed)

    assert policy["resolved_query_type"] == "policy"
    assert policy["degraded_reason"] == "missing_api_key"
    assert fact["resolved_query_type"] == "fact"


def test_auto_rule_fallback_treats_cross_section_summary_as_global_even_with_rfc_terms():
    failed = FakeClassifier({
        "ok": False,
        "provider": "deepseek",
        "error_code": "timeout",
        "error": "request timeout",
    })

    result = resolve_query_type("总结这些 RFC 对 route leak 的共同约束", "auto", client=failed)

    assert result["resolved_query_type"] == "global"
