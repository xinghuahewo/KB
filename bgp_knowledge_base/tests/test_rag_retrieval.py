import json
import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_SCRIPT = ROOT / "scripts" / "build_rag_indexes.py"
QUERY_SCRIPT = ROOT / "scripts" / "query_rag.py"


def run_script(path, *args):
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(path), *args]
        return runpy.run_path(str(path), run_name="__main__")
    finally:
        sys.argv = old_argv


def test_search_route_leak_returns_traceable_offline_results():
    run_script(INDEX_SCRIPT)
    namespace = runpy.run_path(str(QUERY_SCRIPT))
    results = namespace["search"]("route leak", limit=5)

    assert results
    assert any("route" in result["title"].lower() or "route" in result["content_preview"].lower() for result in results)
    for result in results:
        assert result["@id"].startswith("https://")
        assert result["chunk_id"]
        assert result["source_ref"]
        assert result["review_status"]
        assert result["retrieval_method"] in {"sqlite_fts5", "mock_hybrid"}
        assert isinstance(result["score"], float)


def test_chinese_route_leak_query_uses_term_expansion_and_context_pack_excludes_policy_items():
    run_script(INDEX_SCRIPT)
    namespace = runpy.run_path(str(QUERY_SCRIPT))
    results = namespace["search"]("路由泄露", limit=5)
    pack = namespace["context_pack"]("路由泄露", limit=5)

    assert results
    assert pack["query"] == "路由泄露"
    assert "route leak" in pack["normalized_query"]
    assert pack["results"]
    assert pack["citations"]
    assert "answer" not in pack
    assert all(result["review_status"] != "archived" for result in pack["results"])
    assert isinstance(pack["excluded_by_policy"], list)


def test_cli_context_pack_outputs_json(capsys):
    run_script(INDEX_SCRIPT)
    capsys.readouterr()
    run_script(QUERY_SCRIPT, "context-pack", "route leak", "--limit", "2")
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert payload["query"] == "route leak"
    assert len(payload["results"]) <= 2
