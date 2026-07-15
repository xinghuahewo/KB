import json
from pathlib import Path
import runpy

from bgpkb import paths


ROOT = Path(__file__).resolve().parents[1]
DATASET = paths.DATASETS_DIR / "hybrid_retrieval_eval_questions.jsonl"
SCRIPT = ROOT / "src" / "bgpkb" / "pipeline" / "run_hybrid_retrieval_eval.py"


REQUIRED_FIELDS = {
    "question_id",
    "query",
    "expected_status",
    "expected_source_refs",
    "expected_source_types",
    "notes",
}


def load_questions():
    return [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_hybrid_retrieval_eval_dataset_has_required_shape_and_coverage():
    questions = load_questions()

    assert len(questions) >= 20
    assert len({item["question_id"] for item in questions}) == len(questions)
    assert sum(item["expected_status"] == "no_evidence" for item in questions) >= 3
    assert any("路由泄露" in item["query"] for item in questions)
    for item in questions:
        assert REQUIRED_FIELDS <= set(item)
        assert item["expected_status"] in {"evidence", "no_evidence"}
        assert isinstance(item["expected_source_refs"], list)
        assert isinstance(item["expected_source_types"], list)


def test_eval_calculates_recall_mrr_and_no_evidence_rejection_without_key_leak():
    namespace = runpy.run_path(str(SCRIPT))
    questions = [
        {
            "question_id": "hit",
            "query": "route leak",
            "expected_status": "evidence",
            "expected_source_refs": ["rfc7908"],
            "expected_source_types": ["standard"],
            "notes": "命中。",
        },
        {
            "question_id": "reject",
            "query": "unknown",
            "expected_status": "no_evidence",
            "expected_source_refs": [],
            "expected_source_types": [],
            "notes": "拒绝。",
        },
    ]

    def fake_search(query, limit):
        if query == "unknown":
            return {"results": [], "vector_status": "disabled", "normalized_query": query}
        return {
            "results": [
                {"source_ref": "other", "source_type": "paper", "chunk_id": "a"},
                {"source_ref": "raw/standards/rfc7908.txt", "source_type": "standard", "chunk_id": "b"},
            ],
            "vector_status": "offline_mock",
            "normalized_query": query,
        }

    results = namespace["evaluate"](questions=questions, search_fn=fake_search)
    summary = namespace["summarize"](results)
    report = namespace["render_report"](results)
    serialized = json.dumps(results, ensure_ascii=False) + report

    assert results[0]["recall_at_5"] == 1.0
    assert results[0]["reciprocal_rank"] == 0.5
    assert results[1]["decision"] == "pass"
    assert summary["recall_at_5"] == 1.0
    assert summary["mrr"] == 0.5
    assert summary["no_evidence_rejection_rate"] == 1.0
    assert summary["source_coverage"] == ["paper", "standard"]
    assert "# 阶段 4.5 混合检索评测报告" in report
    assert "API key" not in serialized


def test_hybrid_eval_cli_preserves_failure_report_and_returns_nonzero(monkeypatch, tmp_path):
    namespace = runpy.run_path(str(SCRIPT))
    script_globals = namespace["main"].__globals__
    results_path = tmp_path / "hybrid-results.jsonl"
    report_path = tmp_path / "hybrid-report.md"
    failed_rows = namespace["evaluate"](
        questions=[
            {
                "question_id": "miss",
                "query": "route leak",
                "expected_status": "evidence",
                "expected_source_refs": ["rfc7908"],
                "expected_source_types": ["standard"],
                "notes": "必须失败。",
            }
        ],
        search_fn=lambda query, limit: {
            "results": [],
            "vector_status": "complete",
            "normalized_query": query,
        },
    )
    monkeypatch.setitem(script_globals, "RESULTS_PATH", results_path)
    monkeypatch.setitem(script_globals, "REPORT_PATH", report_path)
    monkeypatch.setitem(script_globals, "evaluate", lambda: failed_rows)

    exit_code = namespace["main"]()

    assert exit_code == 1
    assert results_path.exists()
    assert report_path.exists()
    assert "失败数：1" in report_path.read_text(encoding="utf-8")


def test_release_retrieval_eval_uses_required_real_reranker_and_records_revision(
    monkeypatch,
):
    namespace = runpy.run_path(str(SCRIPT))
    calls = []

    def fake_context_pack(query, **kwargs):
        calls.append((query, kwargs))
        return {
            "results": [
                {
                    "source_ref": "rfc7908#section-2",
                    "source_type": "standard",
                    "chunk_id": "chunk-rfc7908",
                }
            ],
            "vector_status": "complete",
            "normalized_query": query,
            "provider": "local_http",
            "model": "BAAI/bge-reranker-v2-m3",
            "revision": "bge-reranker-v2-m3@rev-a",
            "rerank_status": "complete",
            "degraded": False,
        }

    monkeypatch.setattr(
        namespace["hybrid_retrieval"],
        "search",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("发布检索评测不得绕过 reranker")
        ),
    )
    monkeypatch.setattr(namespace["hybrid_retrieval"], "context_pack", fake_context_pack)

    rows = namespace["evaluate"](
        questions=[
            {
                "question_id": "real-reranker",
                "query": "route leak",
                "query_type": "fact",
                "expected_status": "evidence",
                "expected_source_refs": ["rfc7908"],
                "expected_source_types": ["standard"],
                "notes": "固定真实 reranker。",
            }
        ]
    )

    assert calls[0][1]["require_model"] is True
    assert calls[0][1]["query_type"] == "fact"
    assert rows[0]["reranker_model"] == "BAAI/bge-reranker-v2-m3"
    assert rows[0]["reranker_revision"] == "bge-reranker-v2-m3@rev-a"
    assert rows[0]["degraded"] is False
