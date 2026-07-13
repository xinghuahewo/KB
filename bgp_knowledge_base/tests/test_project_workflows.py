from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_makefile_exposes_stable_first_phase_workflow_targets():
    makefile = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")

    for target in ("bootstrap", "test", "test-artifacts", "build", "verify-artifacts"):
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
