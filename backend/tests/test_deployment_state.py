import json
import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPOSITORY_ROOT / "scripts" / "deployment.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _make_code_release(root: Path, release_id: str) -> Path:
    release = root / "code-releases" / release_id
    (release / "backend").mkdir(parents=True)
    (release / "frontend" / "out").mkdir(parents=True)
    (release / "frontend" / "out" / "index.html").write_text("ok", encoding="utf-8")
    (release / "release-manifest.json").write_text("{}\n", encoding="utf-8")
    return release


def _make_artifact_release(root: Path, release_id: str) -> Path:
    release = root / "artifact-releases" / release_id
    (release / "data").mkdir(parents=True)
    return release


def test_activate_records_independent_code_and_artifact_versions_and_legacy_links(tmp_path):
    code = _make_code_release(tmp_path, "code-a")
    artifact = _make_artifact_release(tmp_path, "data-a")
    deploy_root = tmp_path / "deploy"

    result = _run("activate", str(deploy_root), str(code), str(artifact))

    assert result.returncode == 0, result.stderr
    state = json.loads((deploy_root / "deployment-state.json").read_text(encoding="utf-8"))
    assert state["current_code"] == str(code.resolve())
    assert state["current_artifact"] == str(artifact.resolve())
    assert state["previous_code"] is None
    assert state["previous_artifact"] is None
    assert (deploy_root / "current").resolve() == code.resolve()
    assert (deploy_root / "current-artifact").resolve() == artifact.resolve()
    assert (deploy_root / "bgp_knowledge_base").resolve() == (code / "backend").resolve()
    assert (deploy_root / "chat_frontend").resolve() == (code / "frontend").resolve()


def test_rollback_restores_previous_code_and_artifact_without_rebuilding(tmp_path):
    code_a = _make_code_release(tmp_path, "code-a")
    code_b = _make_code_release(tmp_path, "code-b")
    data_a = _make_artifact_release(tmp_path, "data-a")
    data_b = _make_artifact_release(tmp_path, "data-b")
    deploy_root = tmp_path / "deploy"
    assert _run("activate", str(deploy_root), str(code_a), str(data_a)).returncode == 0
    assert _run("activate", str(deploy_root), str(code_b), str(data_b)).returncode == 0

    result = _run("rollback", str(deploy_root))

    assert result.returncode == 0, result.stderr
    state = json.loads((deploy_root / "deployment-state.json").read_text(encoding="utf-8"))
    assert state["current_code"] == str(code_a.resolve())
    assert state["current_artifact"] == str(data_a.resolve())
    assert (deploy_root / "current").resolve() == code_a.resolve()
    assert (deploy_root / "current-artifact").resolve() == data_a.resolve()


def test_invalid_candidate_leaves_current_links_and_state_unchanged(tmp_path):
    code = _make_code_release(tmp_path, "code-a")
    artifact = _make_artifact_release(tmp_path, "data-a")
    deploy_root = tmp_path / "deploy"
    assert _run("activate", str(deploy_root), str(code), str(artifact)).returncode == 0
    state_before = (deploy_root / "deployment-state.json").read_bytes()

    result = _run("activate", str(deploy_root), str(tmp_path / "missing-code"), str(artifact))

    assert result.returncode != 0
    assert (deploy_root / "deployment-state.json").read_bytes() == state_before
    assert (deploy_root / "current").resolve() == code.resolve()


def test_bootstrap_seeds_a_safe_first_migration_rollback_point(tmp_path):
    code = _make_code_release(tmp_path, "legacy-code")
    artifact = _make_artifact_release(tmp_path, "legacy-data")
    deploy_root = tmp_path / "deploy"

    seeded = _run("bootstrap", str(deploy_root), str(code), str(artifact))
    check = _run("check-rollback", str(deploy_root))

    assert seeded.returncode == 0, seeded.stderr
    assert check.returncode == 0, check.stderr
    state = json.loads((deploy_root / "deployment-state.json").read_text(encoding="utf-8"))
    assert state["previous_code"] == state["current_code"] == str(code.resolve())
    assert state["previous_artifact"] == state["current_artifact"] == str(artifact.resolve())


def test_all_runtime_links_follow_one_atomic_generation_pointer(tmp_path):
    code = _make_code_release(tmp_path, "code-a")
    artifact = _make_artifact_release(tmp_path, "data-a")
    deploy_root = tmp_path / "deploy"
    assert _run("activate", str(deploy_root), str(code), str(artifact)).returncode == 0

    assert (deploy_root / "current-generation").is_symlink()
    assert (deploy_root / "current").readlink() == Path("current-generation/code")
    assert (deploy_root / "current-artifact").readlink() == Path("current-generation/artifact")
    assert (deploy_root / "deployment-state.json").readlink() == Path(
        "current-generation/deployment-state.json"
    )


def test_relative_deploy_root_resolves_to_a_valid_generation_pointer(tmp_path):
    code = _make_code_release(tmp_path, "code-a")
    artifact = _make_artifact_release(tmp_path, "data-a")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "activate", "deploy", str(code), str(artifact)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "deploy" / "current").resolve() == code.resolve()


def test_candidate_without_manifest_or_static_index_is_rejected(tmp_path):
    code = tmp_path / "incomplete-code"
    (code / "backend").mkdir(parents=True)
    (code / "frontend").mkdir()
    artifact = _make_artifact_release(tmp_path, "data-a")

    result = _run("activate", str(tmp_path / "deploy"), str(code), str(artifact))

    assert result.returncode != 0
    assert "release-manifest.json" in result.stderr or "index.html" in result.stderr
