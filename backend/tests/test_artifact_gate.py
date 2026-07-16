from pathlib import Path
from types import SimpleNamespace

import pytest

from bgpkb import paths
from bgpkb import artifact_gate


def test_artifact_gate_fails_before_running_tests_without_data_root(monkeypatch):
    monkeypatch.delenv("BGPKB_DATA_DIR", raising=False)
    called = False

    def runner(*args, **kwargs):
        nonlocal called
        called = True

    with pytest.raises(paths.RuntimeDataUnavailable, match="BGPKB_DATA_DIR"):
        artifact_gate.run_artifact_tests(runner=runner)
    assert called is False


def test_artifact_gate_rejects_running_tests_in_immutable_source_release(monkeypatch, tmp_path):
    data_dir = tmp_path / "release" / "data"
    data_dir.mkdir(parents=True)
    monkeypatch.setenv("BGPKB_DATA_DIR", str(data_dir))
    monkeypatch.delenv("BGPKB_ARTIFACT_TEST_DIR", raising=False)

    with pytest.raises(artifact_gate.ArtifactTestWorkspaceError, match="BGPKB_ARTIFACT_TEST_DIR"):
        artifact_gate.run_artifact_tests(runner=lambda *args, **kwargs: None)


def test_artifact_gate_requires_explicit_release_id(monkeypatch, tmp_path):
    data_dir = tmp_path / "release" / "data"
    test_dir = tmp_path / "artifact-test-overlay" / "data"
    data_dir.mkdir(parents=True)
    test_dir.mkdir(parents=True)
    monkeypatch.setenv("BGPKB_DATA_DIR", str(data_dir))
    monkeypatch.setenv("BGPKB_ARTIFACT_TEST_DIR", str(test_dir))
    monkeypatch.delenv("BGPKB_RELEASE_ID", raising=False)

    with pytest.raises(artifact_gate.ArtifactTestWorkspaceError, match="BGPKB_RELEASE_ID"):
        artifact_gate.run_artifact_tests(runner=lambda *args, **kwargs: None)


def test_artifact_gate_rejects_any_workspace_overlapping_source_release(monkeypatch, tmp_path):
    data_dir = tmp_path / "release" / "data"
    nested_test_dir = data_dir / "artifact-test"
    nested_test_dir.mkdir(parents=True)
    monkeypatch.setenv("BGPKB_DATA_DIR", str(data_dir))
    monkeypatch.setenv("BGPKB_ARTIFACT_TEST_DIR", str(nested_test_dir))
    monkeypatch.setenv("BGPKB_RELEASE_ID", "2026-07-10-93a4c97")

    with pytest.raises(artifact_gate.ArtifactTestWorkspaceError, match="重叠"):
        artifact_gate.run_artifact_tests(runner=lambda *args, **kwargs: None)


def test_artifact_gate_verifies_release_then_runs_tests_in_isolated_workspace(monkeypatch, tmp_path):
    data_dir = tmp_path / "release" / "data"
    test_dir = tmp_path / "artifact-test-overlay" / "data"
    data_dir.mkdir(parents=True)
    test_dir.mkdir(parents=True)
    monkeypatch.setenv("BGPKB_DATA_DIR", str(data_dir))
    monkeypatch.setenv("BGPKB_ARTIFACT_TEST_DIR", str(test_dir))
    monkeypatch.setenv("BGPKB_RELEASE_ID", "2026-07-10-93a4c97")
    events = []

    monkeypatch.setattr(
        artifact_gate,
        "verify_registered_artifact_release",
        lambda candidate, release_id: events.append(("verify", Path(candidate), release_id))
        or {"release_id": "2026-07-10-93a4c97"},
    )
    monkeypatch.setattr(
        artifact_gate,
        "verify_artifact_workspace",
        lambda source, workspace: events.append(("workspace", Path(source), Path(workspace))),
    )

    def runner(command, **kwargs):
        events.append(("run", command, kwargs))
        return SimpleNamespace(returncode=0)

    result = artifact_gate.run_artifact_tests(runner=runner)

    assert result == {"release_id": "2026-07-10-93a4c97"}
    assert events[0] == ("verify", data_dir.resolve(), "2026-07-10-93a4c97")
    assert events[1] == ("workspace", data_dir.resolve(), test_dir.resolve())
    assert events[2][1][-3:] == ["-m", "artifact", "-q"]
    assert events[2][2]["cwd"] == paths.PROJECT_ROOT
    assert events[2][2]["env"]["BGPKB_DATA_DIR"] == str(test_dir.resolve())
    assert events[3] == ("verify", data_dir.resolve(), "2026-07-10-93a4c97")


def test_artifact_gate_selects_serving_bundle_tests_for_v2_release(monkeypatch, tmp_path):
    data_dir = tmp_path / "release" / "data"
    test_dir = tmp_path / "artifact-test-overlay" / "data"
    data_dir.mkdir(parents=True)
    test_dir.mkdir(parents=True)
    monkeypatch.setenv("BGPKB_DATA_DIR", str(data_dir))
    monkeypatch.setenv("BGPKB_ARTIFACT_TEST_DIR", str(test_dir))
    monkeypatch.setenv("BGPKB_RELEASE_ID", "rag-evidence-pipeline-v2-11.1-20260715T073006Z")
    commands = []

    monkeypatch.setattr(
        artifact_gate,
        "verify_registered_artifact_release",
        lambda *_: {
            "release_id": "rag-evidence-pipeline-v2-11.1-20260715T073006Z",
            "serving_schema_version": "serving_sqlite_v1",
        },
    )
    monkeypatch.setattr(artifact_gate, "verify_artifact_workspace", lambda *_: None)

    def runner(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0)

    artifact_gate.run_artifact_tests(runner=runner)

    assert commands == [[
        artifact_gate.sys.executable,
        "-m",
        "pytest",
        "-m",
        "serving_artifact",
        "-q",
    ]]
