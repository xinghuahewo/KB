import importlib.util
import os
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "deploy/retrieval-models/cleanup_release.py"


def load_module():
    spec = importlib.util.spec_from_file_location("cleanup_release", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_deletes_valid_non_live_release(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    release_id = "a" * 64
    candidate = releases / release_id
    candidate.mkdir(parents=True)
    (candidate / "file").write_text("x")

    code = module.cleanup_release(release_id, releases, tmp_path / "live-app", tmp_path / "live-models")

    assert code == 0
    assert not candidate.exists()


def test_rejects_empty_short_and_symlink_escape_without_deleting(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    releases.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    release_id = "b" * 64
    (releases / release_id).symlink_to(outside)

    assert module.cleanup_release("", releases, tmp_path / "a", tmp_path / "m") != 0
    assert module.cleanup_release("abc", releases, tmp_path / "a", tmp_path / "m") != 0
    assert module.cleanup_release(release_id, releases, tmp_path / "a", tmp_path / "m") != 0
    assert outside.exists()
    assert os.path.lexists(releases / release_id)


def test_rejects_release_containing_live_app_or_models(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    app_id = "c" * 64
    models_id = "d" * 64
    app_release = releases / app_id
    models_release = releases / models_id
    (app_release / "app").mkdir(parents=True)
    (app_release / "models").mkdir()
    (models_release / "app").mkdir(parents=True)
    (models_release / "models").mkdir()
    live_app = tmp_path / "live-app"
    live_models = tmp_path / "live-models"
    live_app.symlink_to(app_release / "app")
    live_models.symlink_to(models_release / "models")

    assert module.cleanup_release(app_id, releases, live_app, live_models) != 0
    assert module.cleanup_release(models_id, releases, live_app, live_models) != 0
    assert app_release.exists()
    assert models_release.exists()
