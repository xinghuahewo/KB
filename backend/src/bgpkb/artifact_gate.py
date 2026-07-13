"""Verify an external release and run the real-artifact pytest gate."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from bgpkb import paths
from bgpkb.artifact_verification import verify_artifact_workspace, verify_registered_artifact_release


class ArtifactTestFailure(RuntimeError):
    pass


class ArtifactTestWorkspaceError(RuntimeError):
    pass


def run_artifact_tests(runner=subprocess.run) -> dict:
    source_data_dir = paths.require_runtime_data_dir()
    configured_test_dir = os.environ.get("BGPKB_ARTIFACT_TEST_DIR")
    if not configured_test_dir:
        raise ArtifactTestWorkspaceError(
            "未配置 BGPKB_ARTIFACT_TEST_DIR；artifact 测试必须在临时副本或 overlay 中运行。"
        )
    test_data_dir = Path(configured_test_dir).expanduser().resolve()
    if not test_data_dir.is_dir():
        raise ArtifactTestWorkspaceError(f"BGPKB_ARTIFACT_TEST_DIR 不是可用目录：{test_data_dir}")
    if test_data_dir.is_relative_to(source_data_dir) or source_data_dir.is_relative_to(test_data_dir):
        raise ArtifactTestWorkspaceError("BGPKB_ARTIFACT_TEST_DIR 不得与不可变源 release 重叠")
    release_id = os.environ.get("BGPKB_RELEASE_ID")
    if not release_id:
        raise ArtifactTestWorkspaceError(
            "未配置 BGPKB_RELEASE_ID；artifact gate 必须显式指定已登记 release id。"
        )

    verification = verify_registered_artifact_release(source_data_dir, release_id)
    verify_artifact_workspace(source_data_dir, test_data_dir)
    try:
        completed = runner(
            [sys.executable, "-m", "pytest", "-m", "artifact", "-q"],
            cwd=paths.PROJECT_ROOT,
            env={**os.environ, "BGPKB_DATA_DIR": str(test_data_dir)},
            check=False,
        )
    finally:
        verify_registered_artifact_release(source_data_dir, release_id)
    if completed.returncode != 0:
        raise ArtifactTestFailure(f"artifact/integration gate 失败，退出码 {completed.returncode}")
    return verification


def main() -> int:
    try:
        result = run_artifact_tests()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
