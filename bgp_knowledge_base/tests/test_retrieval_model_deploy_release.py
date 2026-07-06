import hashlib
import importlib.util
import json
import os
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "deploy/retrieval-models/deploy_release.py"


def load_module():
    spec = importlib.util.spec_from_file_location("deploy_release", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def stage_release(root, marker="new"):
    app = root / "pending" / "app"
    models = root / "pending" / "models"
    app.mkdir(parents=True)
    models.mkdir(parents=True)
    (app / "compose.yaml").write_text(marker)
    (models / "model_manifest.lock.json").write_text('{"models":[]}')
    file_hash = hashlib.sha256((app / "compose.yaml").read_bytes()).hexdigest()
    files = [{"path": "compose.yaml", "sha256": file_hash}]
    manifest = {
        "app_files": files,
        "app_tree_sha256": hashlib.sha256(canonical(files)).hexdigest(),
        "image_digest": "sha256:" + "a" * 64,
        "model_lock_sha256": hashlib.sha256((models / "model_manifest.lock.json").read_bytes()).hexdigest(),
    }
    content = canonical(manifest)
    release_id = hashlib.sha256(content).hexdigest()
    final = root / release_id
    (root / "pending").rename(final)
    (final / "app/release_manifest.json").write_bytes(content)
    return release_id, final


class Recorder:
    def __init__(self, fail_old=False):
        self.calls = []
        self.fail_old = fail_old

    def __call__(self, command, cwd=None, env=None):
        self.calls.append((tuple(command), Path(cwd) if cwd else None, dict(env or {})))
        if self.fail_old and cwd and Path(cwd).name == "app" and "old" in Path(cwd).parts and "--force-recreate" in command:
            raise RuntimeError("old compose failed")


def test_prestart_failure_does_not_touch_live_links(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    release_id, _ = stage_release(releases)
    old_app = tmp_path / "old/app"
    old_models = tmp_path / "old/models"
    old_app.mkdir(parents=True)
    old_models.mkdir(parents=True)
    live_app = tmp_path / "live-app"
    live_models = tmp_path / "live-models"
    live_app.symlink_to(old_app)
    live_models.symlink_to(old_models)

    code = module.deploy_release(
        release_id, releases, live_app, live_models,
        command_runner=Recorder(), health_checker=lambda port: True,
        prestart_checker=lambda app, models, env: (_ for _ in ()).throw(RuntimeError("prestart")),
    )

    assert code != 0
    assert live_app.resolve() == old_app.resolve()
    assert live_models.resolve() == old_models.resolve()


def test_success_switches_both_links_and_exports_immutable_image(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    release_id, release = stage_release(releases)
    runner = Recorder()
    live_app = tmp_path / "live-app"
    live_models = tmp_path / "live-models"

    code = module.deploy_release(
        release_id, releases, live_app, live_models,
        command_runner=runner, health_checker=lambda port: True,
        prestart_checker=lambda app, models, env: None,
    )

    assert code == 0
    assert live_app.resolve() == (release / "app").resolve()
    assert live_models.resolve() == (release / "models").resolve()
    env = (release / "app/.env").read_text()
    assert f"RETRIEVAL_IMAGE=bgpkb-retrieval-models:{release_id}\n" in env
    assert "COMPOSE_PROJECT_NAME=bgpkb-retrieval-models\n" in env
    assert any(call[0][-3:] == ("--pull", "never", "-d") for call in runner.calls)


def test_runtime_failure_restarts_old_compose_and_verifies_old_health(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    release_id, _ = stage_release(releases)
    old = tmp_path / "old"
    (old / "app").mkdir(parents=True)
    (old / "models").mkdir()
    live_app = tmp_path / "live-app"
    live_models = tmp_path / "live-models"
    live_app.symlink_to(old / "app")
    live_models.symlink_to(old / "models")
    runner = Recorder()
    health_calls = []

    def health(port):
        health_calls.append(port)
        return len(health_calls) > 1

    code = module.deploy_release(
        release_id, releases, live_app, live_models,
        command_runner=runner, health_checker=health,
        prestart_checker=lambda app, models, env: None,
    )

    assert code == 3
    assert live_app.resolve() == (old / "app").resolve()
    assert live_models.resolve() == (old / "models").resolve()
    assert any(call[1] == old / "app" and "--force-recreate" in call[0] for call in runner.calls)
    assert health_calls[-2:] == [8011, 8012]


def test_rollback_failure_returns_four(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    release_id, _ = stage_release(releases)
    old = tmp_path / "old"
    (old / "app").mkdir(parents=True)
    (old / "models").mkdir()
    live_app = tmp_path / "live-app"
    live_models = tmp_path / "live-models"
    live_app.symlink_to(old / "app")
    live_models.symlink_to(old / "models")

    code = module.deploy_release(
        release_id, releases, live_app, live_models,
        command_runner=Recorder(fail_old=True), health_checker=lambda port: False,
        prestart_checker=lambda app, models, env: None,
    )

    assert code == 4


def test_first_deploy_runtime_failure_leaves_no_live_links(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    release_id, _ = stage_release(releases)
    live_app = tmp_path / "live-app"
    live_models = tmp_path / "live-models"

    code = module.deploy_release(
        release_id, releases, live_app, live_models,
        command_runner=Recorder(), health_checker=lambda port: False,
        prestart_checker=lambda app, models, env: None,
    )

    assert code != 0
    assert not os.path.lexists(live_app)
    assert not os.path.lexists(live_models)


def test_default_prestart_runs_gpu_selection_and_runtime_verification(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    release_id, _ = stage_release(releases)
    runner = Recorder()

    code = module.deploy_release(
        release_id, releases, tmp_path / "live-app", tmp_path / "live-models",
        command_runner=runner, health_checker=lambda port: True,
    )

    assert code == 0
    flattened = [" ".join(call[0]) for call in runner.calls]
    assert any("select_gpu_devices.py" in command for command in flattened)
    assert any("verify_runtime.py prestart" in command for command in flattened)
