from pathlib import Path

from bgpkb import paths
import sys


ROOT = paths.PROJECT_ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgpkb.retrieval import retrieval_framework  # noqa: E402


def test_definition_query_prefers_standard_sources():
    results = retrieval_framework.search("what is RPKI RFC validation", limit=5)

    assert results
    assert results[0]["source_type"] == "standard"


def test_incident_query_prefers_case_sources():
    results = retrieval_framework.search("YouTube hijack incident", limit=5)

    assert results
    assert results[0]["source_type"] == "case_report"
    assert "youtube_hijack_google_2008" in results[0]["doc_id"]


def test_chinese_route_leak_expansion_surfaces_route_leak_results():
    normalized = retrieval_framework.normalize_query("路由泄露")
    results = retrieval_framework.search("路由泄露", limit=5)

    assert "route leak" in normalized
    assert results
    assert any("route" in item["content_preview"].lower() or "route" in item["title"].lower() for item in results)


def test_query_expansions_do_not_inject_gold_source_names_for_broad_concepts():
    observability = retrieval_framework.normalize_query(
        "Which data sources jointly provide global BGP observability?"
    )
    incidents = retrieval_framework.normalize_query(
        "Which common operational risks are reflected by major routing incident cases?"
    )
    research = retrieval_framework.normalize_query(
        "近年来的 BGP 安全研究有哪些主要方向？"
    )

    assert not {"ROUTEVIEWS", "RIPE", "RIS", "BGPSTREAM"} & set(observability.split())
    assert not {"YOUTUBE", "VERIZON", "FACEBOOK"} & set(incidents.split())
    assert not {"BGP2VEC", "OSCILLOSCOPE", "BGPSHIELD"} & set(research.split())


def test_ascii_acronym_expansion_requires_a_complete_query_token():
    assert "RFC6811" not in retrieval_framework.normalize_query(
        "Which sources provide global observability?"
    )
    assert "route origin authorization" not in retrieval_framework.normalize_query(
        "What road policy applies here?"
    )
