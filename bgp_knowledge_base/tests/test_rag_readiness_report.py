import runpy
import sys
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
SCRIPT = paths.PIPELINE_DIR / "build_rag_readiness_report.py"
REPORT = paths.report_path("rag_readiness_report")


def test_rag_readiness_report_records_framework_boundaries_and_api_entries():
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(SCRIPT)]
        runpy.run_path(str(SCRIPT), run_name="__main__")
    finally:
        sys.argv = old_argv

    text = REPORT.read_text(encoding="utf-8")
    assert "# RAG 就绪框架报告" in text
    assert "## Provider 与运行边界" in text
    assert "当前设备不运行模型" in text
    assert "DeepSeek" in text
    assert "Qwen/vLLM" in text
    assert "BGE-M3" in text
    assert "## API 入口" in text
    assert "/api/v1/retrieval/context-pack" in text
