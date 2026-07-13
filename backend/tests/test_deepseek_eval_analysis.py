from pathlib import Path

from bgpkb import paths
import json
import runpy


ROOT = paths.PROJECT_ROOT
RUNNER = paths.PIPELINE_DIR / "run_deepseek_rag_answer_eval.py"
ANALYSIS = paths.PIPELINE_DIR / "build_rag_answer_failure_analysis.py"


class FakeDeepSeekClient:
    model = "deepseek-chat"

    def generate_answer(self, query, context_items):
        return {
            "ok": True,
            "provider": "deepseek",
            "model": self.model,
            "content": f"真实评测模拟回答：{query} BGP route leak RPKI ROA ASPA hijack flap semantics。",
            "raw_usage": {"total_tokens": 16},
        }


def test_deepseek_runner_writes_separate_real_eval_outputs_without_key_leak(tmp_path):
    namespace = runpy.run_path(str(RUNNER))
    results_path = tmp_path / "deepseek_results.jsonl"
    report_path = tmp_path / "deepseek_report.md"
    questions = [
        {
            "question_id": "real_eval_pass",
            "query": "route leak",
            "expected_status": "answered",
            "must_have_terms": ["route leak"],
            "forbidden_terms": ["secret-token"],
            "expected_source_refs": [],
            "notes": "真实评测模拟。",
        }
    ]

    results = namespace["run_real_eval"](
        questions=questions,
        client=FakeDeepSeekClient(),
        results_path=results_path,
        report_path=report_path,
        limit=3,
    )
    serialized = json.dumps(results, ensure_ascii=False) + report_path.read_text(encoding="utf-8")

    assert results_path.exists()
    assert report_path.exists()
    assert results[0]["model_provider"] == "deepseek"
    assert "阶段 4.4 DeepSeek 真实批量评测报告" in report_path.read_text(encoding="utf-8")
    assert "sk-" not in serialized


def test_failure_analysis_groups_failed_checks_and_renders_chinese_report(tmp_path):
    namespace = runpy.run_path(str(ANALYSIS))
    rows = [
        {
            "question_id": "ok",
            "query": "route leak",
            "decision": "pass",
            "failed_checks": [],
            "answer_status": "answered",
            "expected_status": "answered",
            "citation_count": 3,
        },
        {
            "question_id": "bad",
            "query": "fictional",
            "decision": "fail",
            "failed_checks": ["answer_status_mismatch", "unexpected_generation"],
            "answer_status": "answered",
            "expected_status": "no_evidence",
            "citation_count": 2,
        },
    ]

    summary = namespace["summarize_failures"](rows)
    report = namespace["render_report"](rows, summary, source_path="data/derived/datasets/deepseek_rag_answer_eval_results.jsonl")

    assert summary["total"] == 2
    assert summary["failed"] == 1
    assert summary["failed_check_counts"]["answer_status_mismatch"] == 1
    assert "阶段 4.4 RAG 答案失败样本分析报告" in report
    assert "answer_status_mismatch" in report
