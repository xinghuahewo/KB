from pathlib import Path
import sys

from bgpkb import paths
import json
import pytest
import runpy


ROOT = paths.PROJECT_ROOT
SCRIPT = paths.PIPELINE_DIR / "run_rag_answer_eval.py"


class EvalFakeClient:
    model = "deepseek-chat"

    def generate_grounded_answer(self, query, evidence, context_groups, repair=None):
        if "forbidden" in query:
            content = "这个回答包含 forbidden-claim。"
        else:
            content = f"基于证据回答 {query}。BGP route leak RPKI ROA ASPA hijack flap。"
        evidence_ids = [item["evidence_id"] for item in evidence]
        return {
            "ok": True,
            "provider": "deepseek",
            "model": self.model,
            "content": json.dumps({
                "schema_version": "grounded_answer_v1",
                "answer": content,
                "claims": [{
                    "schema_version": "grounded_claim_v1",
                    "claim_type": "factual",
                    "text": content,
                    "evidence_ids": evidence_ids,
                    "confidence": 0.9,
                }],
                "evidence_ids": evidence_ids,
                "confidence": 0.9,
                "insufficient_evidence": False,
            }, ensure_ascii=False),
            "raw_usage": {"total_tokens": 8},
        }


def test_eval_script_scores_answers_and_renders_report_without_key_leak():
    namespace = runpy.run_path(str(SCRIPT))
    questions = [
        {
            "question_id": "eval_pass",
            "query": "route leak",
            "expected_status": "answered",
            "must_have_terms": ["route leak"],
            "forbidden_terms": ["forbidden-claim"],
            "expected_source_refs": [],
            "notes": "有证据问题。",
        },
        {
            "question_id": "eval_no_evidence",
            "query": "xyxyxyxyxyxyxyxyxyxy",
            "expected_status": "no_evidence",
            "must_have_terms": [],
            "forbidden_terms": [],
            "expected_source_refs": [],
            "notes": "无证据问题。",
        },
        {
            "question_id": "eval_forbidden",
            "query": "route leak forbidden",
            "expected_status": "answered",
            "must_have_terms": ["route leak"],
            "forbidden_terms": ["forbidden-claim"],
            "expected_source_refs": [],
            "notes": "禁用声明检测。",
        },
    ]

    results = namespace["run_evaluation"](questions=questions, client=EvalFakeClient(), limit=3)
    report = namespace["render_report"](results, api_key_configured=True)
    serialized = json.dumps(results, ensure_ascii=False) + report

    assert results[0]["decision"] == "pass"
    assert results[1]["decision"] == "pass"
    assert results[2]["decision"] == "fail"
    assert "forbidden_terms_hit" in results[2]["failed_checks"]
    assert "阶段 4.3 RAG 答案评测报告" in report
    assert "引用覆盖率" in report
    assert "sk-" not in serialized


def test_eval_script_accepts_common_chinese_equivalents_for_must_have_terms():
    namespace = runpy.run_path(str(SCRIPT))

    assert namespace["text_contains"]("ARTEMIS 能够检测 BGP 劫持事件。", "hijack") is True
    assert namespace["text_contains"]("该事件属于路由泄露。", "route leak") is True


def test_eval_cli_reports_outputs_outside_source_tree(monkeypatch, capsys, tmp_path):
    namespace = runpy.run_path(str(SCRIPT))
    script_globals = namespace["main"].__globals__
    artifact_data = tmp_path / "artifact-data"
    results_path = artifact_data / "derived" / "datasets" / "results.jsonl"
    report_path = artifact_data / "generated" / "reports" / "report.md"
    monkeypatch.setattr(script_globals["paths"], "DATA_DIR", artifact_data)
    monkeypatch.setitem(script_globals, "RESULTS_PATH", results_path)
    monkeypatch.setitem(script_globals, "REPORT_PATH", report_path)
    monkeypatch.setitem(script_globals, "run_evaluation", lambda limit: [])
    monkeypatch.setattr(sys, "argv", [str(SCRIPT)])

    namespace["main"]()

    output = capsys.readouterr().out
    assert "data/derived/datasets/results.jsonl" in output
    assert "data/generated/reports/report.md" in output


def test_structure_only_eval_is_development_only_and_rejected_for_release():
    namespace = runpy.run_path(str(SCRIPT))
    structure_client = namespace["StructureOnlyClient"]()

    assert structure_client.evaluation_mode == "development_structure_only"
    assert structure_client.release_eligible is False
    with pytest.raises(ValueError, match="结构检查.*发布评测"):
        namespace["run_evaluation"](
            questions=[],
            client=structure_client,
            release_mode=True,
            required_model="deepseek-chat",
            required_model_revision="deepseek-chat@release-rev-a",
        )

    report = namespace["render_report"](
        [],
        api_key_configured=False,
        evaluation_mode="development_structure_only",
    )
    assert "仅用于开发" in report
    assert "不能替代真实 reranker/DeepSeek 发布评测" in report


def test_release_answer_eval_requires_exact_deepseek_model_revision():
    namespace = runpy.run_path(str(SCRIPT))

    class UnpinnedDeepSeekClient:
        provider = "deepseek"
        model = "deepseek-chat"
        model_revision = None
        release_eligible = True

    with pytest.raises(ValueError, match="model revision"):
        namespace["run_evaluation"](
            questions=[],
            client=UnpinnedDeepSeekClient(),
            release_mode=True,
            required_model="deepseek-chat",
            required_model_revision="deepseek-chat@release-rev-a",
        )


def test_answer_eval_cli_preserves_failure_report_and_returns_nonzero(
    monkeypatch, tmp_path
):
    namespace = runpy.run_path(str(SCRIPT))
    script_globals = namespace["main"].__globals__
    results_path = tmp_path / "answer-results.jsonl"
    report_path = tmp_path / "answer-report.md"
    failed_rows = [
        {
            "question_id": "failed-answer",
            "query": "route leak",
            "expected_status": "answered",
            "answer_status": "llm_unavailable",
            "decision": "fail",
            "failed_checks": ["answer_status_mismatch"],
            "generated": False,
            "citation_count": 0,
            "citations_from_context_pack": True,
            "must_have_terms_missing": [],
            "forbidden_terms_hit": [],
            "expected_source_refs": ["rfc7908"],
            "matched_expected_source_refs": [],
            "model_provider": "deepseek",
            "model": "deepseek-chat",
            "answer_preview": "",
            "guardrails": {},
        }
    ]
    monkeypatch.setitem(script_globals, "RESULTS_PATH", results_path)
    monkeypatch.setitem(script_globals, "REPORT_PATH", report_path)
    monkeypatch.setitem(script_globals, "run_evaluation", lambda limit: failed_rows)
    monkeypatch.setattr(script_globals["paths"], "DATA_DIR", tmp_path)
    monkeypatch.setattr(sys, "argv", [str(SCRIPT)])

    exit_code = namespace["main"]()

    assert exit_code == 1
    assert results_path.exists()
    assert report_path.exists()
    assert "失败数：1" in report_path.read_text(encoding="utf-8")
