from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_repository_uses_canonical_application_directories():
    assert (REPOSITORY_ROOT / "backend" / "pyproject.toml").is_file()
    assert (REPOSITORY_ROOT / "frontend" / "package.json").is_file()
    assert (REPOSITORY_ROOT / "infra").is_dir()
    assert not (REPOSITORY_ROOT / "bgp_knowledge_base").exists()
    assert not (REPOSITORY_ROOT / "chat_frontend").exists()


def test_root_workflow_targets_only_canonical_directories():
    workflow = (REPOSITORY_ROOT / "scripts" / "project-workflow").read_text(encoding="utf-8")

    assert 'BACKEND_DIR="$REPOSITORY_ROOT/backend"' in workflow
    assert 'FRONTEND_DIR="$REPOSITORY_ROOT/frontend"' in workflow
    assert "bgp_knowledge_base" not in workflow
    assert "chat_frontend" not in workflow
