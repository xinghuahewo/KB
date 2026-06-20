import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "quality_report.md"


def test_quality_check_accepts_cleaned_markdown_with_frontmatter():
    manifest_result = subprocess.run(
        [sys.executable, "scripts/build_artifact_manifest.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert manifest_result.returncode == 0, manifest_result.stdout + manifest_result.stderr

    result = subprocess.run(
        [sys.executable, "scripts/quality_check.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    report = REPORT.read_text(encoding="utf-8")
    assert "Cleaned 文档缺失标题数：0" in report
    assert "cleaned/notes/context_summary.md" not in report
