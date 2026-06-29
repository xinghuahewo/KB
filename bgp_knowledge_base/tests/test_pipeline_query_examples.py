import subprocess
import sys
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT


def test_query_examples_script_matches_current_published_database():
    result = subprocess.run(
        [sys.executable, "-m", "bgpkb.pipeline.build_query_examples"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
