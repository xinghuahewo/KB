from pathlib import Path
import json
import runpy


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_rag_answer_eval.py"


class EvalFakeClient:
    model = "deepseek-chat"

    def generate_answer(self, query, context_items):
        if "forbidden" in query:
            content = "这个回答包含 forbidden-claim。"
        else:
            content = f"基于证据回答 {query}。BGP route leak RPKI ROA ASPA hijack flap。"
        return {
            "ok": True,
            "provider": "deepseek",
            "model": self.model,
            "content": content,
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
            "query": "zzzzqqqxxxx",
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

