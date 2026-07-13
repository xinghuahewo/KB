import os
import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_makefile_exposes_stable_project_workflow_targets():
    makefile = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")

    for target in (
        "bootstrap",
        "test",
        "test-artifacts",
        "build",
        "verify-artifacts",
        "release",
        "deploy",
        "rollback",
    ):
        assert f"{target}:" in makefile
        assert f"bash scripts/project-workflow {target}" in makefile


def test_project_workflow_keeps_uv_and_corepack_yarn_boundaries():
    workflow = (REPOSITORY_ROOT / "scripts" / "project-workflow").read_text(encoding="utf-8")

    assert "uv sync --frozen --all-groups" in workflow
    assert "uv run pytest -q -m 'not artifact and not legacy_documentation'" in workflow
    assert "scripts/artifact-test-overlay" in workflow
    assert "uv run python -m bgpkb.artifact_verification" in workflow
    assert "corepack yarn install --immutable" in workflow
    assert "corepack yarn test" in workflow
    assert "corepack yarn build" in workflow
    assert 'bash "$REPOSITORY_ROOT/scripts/release"' in workflow
    assert 'bash "$REPOSITORY_ROOT/scripts/deploy"' in workflow
    assert 'bash "$REPOSITORY_ROOT/scripts/rollback"' in workflow


def test_deployment_scripts_and_state_manager_exist():
    for path in (
        "scripts/release",
        "scripts/deploy",
        "scripts/rollback",
        "scripts/deployment.py",
        "scripts/check-service-health",
        "scripts/check-workflow-paths",
        "scripts/restart-active-services",
    ):
        assert (REPOSITORY_ROOT / path).is_file(), path


def test_code_release_is_verified_atomic_and_keeps_static_frontend_output():
    release = (REPOSITORY_ROOT / "scripts" / "release").read_text(encoding="utf-8")
    deploy = (REPOSITORY_ROOT / "scripts" / "deploy").read_text(encoding="utf-8")

    assert "make test" in release
    assert "make build" in release
    assert ".next-$$" in release
    assert "--exclude 'frontend/out/'" not in release
    assert "git status --porcelain" in release
    assert "git archive" in release
    assert "uv sync --frozen --all-groups" in deploy
    assert "check-rollback" in deploy


def test_health_check_is_bounded_and_checks_static_frontend():
    health = (REPOSITORY_ROOT / "scripts" / "check-service-health").read_text(encoding="utf-8")
    restart = (REPOSITORY_ROOT / "scripts" / "restart-active-services").read_text(encoding="utf-8")

    assert "--connect-timeout" in health
    assert "--max-time" in health
    assert "BGPKB_HEALTH_ATTEMPTS" in health
    assert "http://127.0.0.1:39280/index.html" in health
    assert "BGPKB_ENV_FILE" in restart
    assert "/etc/bgpkb/runtime.env" in restart
    assert "DEEPSEEK_API_KEY" in restart


def test_health_check_loads_external_runtime_urls(tmp_path):
    env_file = tmp_path / "runtime.env"
    env_file.write_text(
        "\n".join(
            (
                "BGPKB_FRONTEND_URL=http://frontend.example/index.html",
                "BGPKB_FASTAPI_HEALTH_URL=http://fastapi.example/health",
                "BGPKB_EMBEDDING_HEALTH_URL=http://embedding.example/health",
                "BGPKB_RERANKER_HEALTH_URL=http://reranker.example/health",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    curl_log = tmp_path / "curl.log"
    fake_curl = fake_bin / "curl"
    fake_curl.write_text(
        '#!/usr/bin/env bash\nprintf "%s\\n" "${@: -1}" >> "$CURL_LOG"\n',
        encoding="utf-8",
    )
    fake_curl.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "CURL_LOG": str(curl_log),
        "BGPKB_ENV_FILE": str(env_file),
        "BGPKB_HEALTH_ATTEMPTS": "1",
        "BGPKB_HEALTH_INTERVAL_SECONDS": "0",
    }

    subprocess.run(
        ["bash", str(REPOSITORY_ROOT / "scripts" / "check-service-health")],
        check=True,
        env=env,
        text=True,
        capture_output=True,
    )

    assert curl_log.read_text(encoding="utf-8").splitlines() == [
        "http://frontend.example/index.html",
        "http://fastapi.example/health",
        "http://embedding.example/health",
        "http://reranker.example/health",
    ]


def test_artifact_overlay_keeps_source_release_read_only_and_reverifies_it():
    overlay = (REPOSITORY_ROOT / "scripts" / "artifact-test-overlay").read_text(encoding="utf-8")

    assert "lowerdir=" in overlay
    assert "upperdir=" in overlay
    assert "workdir=" in overlay
    assert "BGPKB_ARTIFACT_TEST_DIR" in overlay
    assert "BGPKB_RELEASE_ID" in overlay
    assert "uv run python -m bgpkb.artifact_gate" in overlay
    assert "uv run python -m bgpkb.artifact_verification" in overlay
    assert "umount" in overlay


def test_ci_uses_only_existing_unified_workflow_entries():
    workflow = (REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "make test" in workflow
    assert "make build" in workflow
    assert "bash scripts/check-repository-hygiene" in workflow
    assert "python3 scripts/check-doc-links" in workflow
    assert "python3 scripts/check-workflow-paths" in workflow
    assert "openspec validate --all --strict --no-interactive" in workflow
    for retired_path in (
        "requirements-service.txt",
        "scripts/run_pipeline.py",
        "scripts/run_stage_acceptance.py",
        "scripts/build_artifact_manifest.py",
        "scripts/quality_check.py",
    ):
        assert retired_path not in workflow


def test_repository_hygiene_gate_rejects_tracked_runtime_artifact_patterns():
    gate = (REPOSITORY_ROOT / "scripts" / "check-repository-hygiene").read_text(encoding="utf-8")

    for pattern in ("*.sqlite", "*.db", "*.parquet", "*.faiss", "*.index"):
        assert pattern in gate
    assert "1048576" in gate
    assert "git ls-files -ci --exclude-standard" in gate


def test_root_gitignore_blocks_runtime_artifacts_but_keeps_release_registry():
    gitignore = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8")

    for pattern in ("*.sqlite", "*.db", "*.parquet", "*.faiss", "*.index"):
        assert pattern in gitignore
    assert "artifacts/*" in gitignore
    assert "!artifacts/releases.yaml" in gitignore
    assert "backend/dist/" in gitignore
