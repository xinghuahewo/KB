from pathlib import Path

from bgpkb import paths
import json
import runpy


ROOT = paths.PROJECT_ROOT
SCRIPT = paths.PIPELINE_DIR / "run_rag_answer_smoke_test.py"


class FakeClient:
    model = "deepseek-chat"

    def generate_answer(self, query, context_items):
        return {
            "ok": True,
            "provider": "deepseek",
            "model": self.model,
            "content": f"测试回答：{query}，证据数 {len(context_items)}。",
            "raw_usage": {"total_tokens": 12},
        }


def test_smoke_script_builds_report_without_leaking_api_key(tmp_path):
    namespace = runpy.run_path(str(SCRIPT))
    results = namespace["run_smoke_tests"](
        client=FakeClient(),
        queries=["route leak", "zzzzqqqxxxx"],
        limit=2,
    )
    report = namespace["render_report"](results, api_key_configured=True)
    serialized = json.dumps(results, ensure_ascii=False) + report

    assert results[0]["answer_status"] == "answered"
    assert results[1]["answer_status"] == "no_evidence"
    assert "阶段 4.2 DeepSeek 冒烟测试报告" in report
    assert "DEEPSEEK_API_KEY" in report
    assert "test-key" not in serialized
    assert "sk-" not in serialized
