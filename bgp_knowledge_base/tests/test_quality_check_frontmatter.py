import subprocess
import sys
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
REPORT = paths.report_path("quality_report")


def test_quality_check_accepts_cleaned_markdown_with_frontmatter():
    manifest_result = subprocess.run(
        [sys.executable, "-m", "bgpkb.pipeline.build_artifact_manifest"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert manifest_result.returncode == 0, manifest_result.stdout + manifest_result.stderr

    result = subprocess.run(
        [sys.executable, "-m", "bgpkb.pipeline.quality_check"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    report = REPORT.read_text(encoding="utf-8")
    assert "Cleaned 文档缺失标题数：0" in report
    assert "data/corpus/cleaned/notes/context_summary.md" not in report
