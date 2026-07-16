from pathlib import Path

from bgpkb import paths
import json
import runpy
import sys


ROOT = paths.PROJECT_ROOT
RUNNER = paths.PIPELINE_DIR / "run_deepseek_rag_answer_eval.py"
ANALYSIS = paths.PIPELINE_DIR / "build_rag_answer_failure_analysis.py"


class FakeDeepSeekClient:
    model = "deepseek-chat"
    model_revision = "deepseek-chat@release-rev-a"
    provider = "deepseek"
    release_eligible = True

    def generate_grounded_answer(self, query, evidence, context_groups, repair=None):
        answer = f"真实评测模拟回答：{query} BGP route leak RPKI ROA ASPA hijack flap semantics。"
        evidence_ids = [item["evidence_id"] for item in evidence]
        return {
            "ok": True,
            "provider": "deepseek",
            "model": self.model,
            "content": json.dumps({
                "schema_version": "grounded_answer_v1",
                "answer": answer,
                "claims": [{
                    "schema_version": "grounded_claim_v1",
                    "claim_type": "factual",
                    "text": answer,
                    "evidence_ids": evidence_ids,
                    "confidence": 0.9,
                }],
                "evidence_ids": evidence_ids,
                "confidence": 0.9,
                "insufficient_evidence": False,
            }, ensure_ascii=False),
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
        required_model="deepseek-chat",
        required_model_revision="deepseek-chat@release-rev-a",
    )
    serialized = json.dumps(results, ensure_ascii=False) + report_path.read_text(encoding="utf-8")

    assert results_path.exists()
    assert report_path.exists()
    assert results[0]["model_provider"] == "deepseek"
    assert results[0]["model_revision"] == "deepseek-chat@release-rev-a"
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


def test_deepseek_cli_preserves_failed_report_and_returns_nonzero(monkeypatch, tmp_path):
    namespace = runpy.run_path(str(RUNNER))
    script_globals = namespace["main"].__globals__
    results_path = tmp_path / "deepseek-results.jsonl"
    report_path = tmp_path / "deepseek-report.md"

    def fake_eval(limit):
        rows = [{"question_id": "failed", "decision": "fail"}]
        results_path.write_text(json.dumps(rows[0]) + "\n", encoding="utf-8")
        report_path.write_text("# DeepSeek\n\n- 失败数：1\n", encoding="utf-8")
        return rows

    monkeypatch.setitem(script_globals, "RESULTS_PATH", results_path)
    monkeypatch.setitem(script_globals, "REPORT_PATH", report_path)
    monkeypatch.setitem(script_globals, "run_real_eval", fake_eval)
    monkeypatch.setattr(script_globals["paths"], "DATA_DIR", tmp_path)
    monkeypatch.setattr(sys, "argv", [str(RUNNER)])

    exit_code = namespace["main"]()

    assert exit_code == 1
    assert results_path.exists()
    assert report_path.exists()


def test_deepseek_cli_writes_blocking_skip_report_when_model_is_unavailable(
    monkeypatch, tmp_path
):
    namespace = runpy.run_path(str(RUNNER))
    script_globals = namespace["main"].__globals__
    results_path = tmp_path / "deepseek-results.jsonl"
    report_path = tmp_path / "deepseek-report.md"
    monkeypatch.setitem(script_globals, "RESULTS_PATH", results_path)
    monkeypatch.setitem(script_globals, "REPORT_PATH", report_path)
    monkeypatch.setattr(script_globals["paths"], "DATA_DIR", tmp_path)
    monkeypatch.setitem(
        script_globals,
        "run_real_eval",
        lambda limit: (_ for _ in ()).throw(
            SystemExit("DEEPSEEK_API_KEY is required for real DeepSeek evaluation.")
        ),
    )
    monkeypatch.setattr(sys, "argv", [str(RUNNER)])

    exit_code = namespace["main"]()

    assert exit_code == 1
    blocking = json.loads(results_path.read_text(encoding="utf-8"))
    assert blocking["status"] == "skipped_blocking"
    assert "skipped_blocking" in report_path.read_text(encoding="utf-8")


def test_real_deepseek_eval_requires_exact_model_and_revision(monkeypatch, tmp_path):
    namespace = runpy.run_path(str(RUNNER))
    observed = {}

    def fake_run_evaluation(**kwargs):
        observed.update(kwargs)
        return []

    monkeypatch.setattr(
        namespace["run_rag_answer_eval"], "run_evaluation", fake_run_evaluation
    )

    namespace["run_real_eval"](
        questions=[],
        client=FakeDeepSeekClient(),
        results_path=tmp_path / "results.jsonl",
        report_path=tmp_path / "report.md",
        required_model="deepseek-chat",
        required_model_revision="deepseek-chat@release-rev-a",
    )

    assert observed["release_mode"] is True
    assert observed["required_model"] == "deepseek-chat"
    assert observed["required_model_revision"] == "deepseek-chat@release-rev-a"


def test_real_deepseek_eval_rejects_missing_release_revision(tmp_path):
    namespace = runpy.run_path(str(RUNNER))

    try:
        namespace["run_real_eval"](
            questions=[],
            client=FakeDeepSeekClient(),
            results_path=tmp_path / "results.jsonl",
            report_path=tmp_path / "report.md",
            required_model="deepseek-chat",
            required_model_revision="",
        )
    except ValueError as exc:
        assert "revision" in str(exc)
    else:
        raise AssertionError("缺失 DeepSeek revision 时必须阻断真实发布评测")
