from bgpkb.retrieval.retrieval_framework import assess_query_scope


def test_query_scope_policy_rejects_unsupported_intents_in_both_languages():
    cases = {
        "明天北京逐小时天气如何？": "unsupported_weather_or_climate",
        "Can this knowledge base provide every network engineer's private phone number?": "unsupported_private_contact_data",
        "如何用 BGP 命令重置一台未知厂商设备的 root 密码？": "unsupported_root_password_reset",
        "How can today's best stock purchase be selected from a BGP routing table?": "unsupported_financial_recommendation",
        "公司的员工休假审批政策是什么？": "unsupported_employee_policy",
        "Provide the full private-data deletion policy for undisclosed customers.": "unsupported_private_customer_policy",
        "全球海洋温度变化与 BGP 收敛时间的精确因果系数是多少？": "unsupported_weather_or_climate",
        "Predict the next World Cup champion and prove it with BGP evidence.": "unsupported_sports_prediction",
    }

    for query, rule_id in cases.items():
        decision = assess_query_scope(query)
        assert decision["status"] == "unsupported"
        assert decision["rule_id"] == rule_id
        assert decision["policy_version"] == "query_scope_v1"


def test_query_scope_policy_keeps_supported_bgp_operations_queries():
    decision = assess_query_scope(
        "How should an operator configure BGP TCP authentication and route filtering?"
    )

    assert decision == {
        "policy_version": "query_scope_v1",
        "status": "supported",
        "rule_id": "supported_bgp_knowledge_query",
        "reason": "查询属于 BGP 知识库可检索范围",
    }
