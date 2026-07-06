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


def stage_release(root, marker="new", image_digest=None):
    app = root / "pending" / "app"
    models = root / "pending" / "models"
    app.mkdir(parents=True)
    models.mkdir(parents=True)
    (app / "compose.yaml").write_text(marker)
    (app / ".env").write_text(
        "EMBEDDING_GPU_CDI=nvidia.com/gpu=2\n"
        "RERANKER_GPU_CDI=nvidia.com/gpu=3\n"
        "EMBEDDING_GPU_INDEX=2\n"
        "RERANKER_GPU_INDEX=3\n"
    )
    (models / "model_manifest.lock.json").write_text('{"models":[]}')
    file_hash = hashlib.sha256((app / "compose.yaml").read_bytes()).hexdigest()
    files = [{"path": "compose.yaml", "sha256": file_hash}]
    manifest = {
        "app_files": files,
        "app_tree_sha256": hashlib.sha256(canonical(files)).hexdigest(),
        "image_digest": image_digest or "sha256:" + "a" * 64,
        "model_lock_sha256": hashlib.sha256((models / "model_manifest.lock.json").read_bytes()).hexdigest(),
    }
    content = canonical(manifest)
    release_id = hashlib.sha256(content).hexdigest()
    final = root / release_id
    (root / "pending").rename(final)
    (final / "app/release_manifest.json").write_bytes(content)
    return release_id, final


class Recorder:
    def __init__(self, images=None, fail_old=False):
        self.calls = []
        self.fail_old = fail_old
        self.images = images or {}

    def __call__(self, command, cwd=None, env=None):
        self.calls.append((tuple(command), Path(cwd) if cwd else None, dict(env or {})))
        if self.fail_old and "--force-recreate" in command:
            raise RuntimeError("old compose failed")
        if command[:3] == ["docker", "image", "inspect"]:
            tag = command[3]
            if tag not in self.images:
                raise RuntimeError("image missing")
            return json.dumps([{"Id": self.images[tag], "RepoDigests": []}])
        if command[:3] == ["docker", "ps", "-aq"]:
            return ""


def image_map(release_id, digest="sha256:" + "a" * 64):
    return {f"bgpkb-retrieval-models:{release_id}": digest}


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
        command_runner=Recorder(image_map(release_id)), health_checker=lambda port: True,
        prestart_checker=lambda app, models, env: (_ for _ in ()).throw(RuntimeError("prestart")),
    )

    assert code != 0
    assert live_app.resolve() == old_app.resolve()
    assert live_models.resolve() == old_models.resolve()


def test_success_switches_both_links_and_exports_immutable_image(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    release_id, release = stage_release(releases)
    runner = Recorder(image_map(release_id))
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
    assert (release / "app/.env").read_text().count("\n") == 4
    compose_call = next(call for call in runner.calls if call[0][:3] == ("docker", "compose", "up"))
    assert compose_call[2]["RETRIEVAL_IMAGE"] == f"bgpkb-retrieval-models:{release_id}"
    assert compose_call[2]["COMPOSE_PROJECT_NAME"] == "bgpkb-retrieval-models"
    assert any(call[0][-3:] == ("--pull", "never", "-d") for call in runner.calls)
    assert not any(call[0][:3] in {("docker", "image", "tag"), ("docker", "image", "rm")} for call in runner.calls)


def test_runtime_failure_restarts_old_compose_and_verifies_old_health(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    release_id, _ = stage_release(releases)
    old_id, old = stage_release(releases, "old", "sha256:" + "b" * 64)
    live_app = tmp_path / "live-app"
    live_models = tmp_path / "live-models"
    live_app.symlink_to(old / "app")
    live_models.symlink_to(old / "models")
    images = image_map(release_id)
    images.update(image_map(old_id, "sha256:" + "b" * 64))
    runner = Recorder(images)
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


def test_rollback_failure_returns_four(tmp_path, capsys):
    module = load_module()
    releases = tmp_path / "releases"
    release_id, _ = stage_release(releases)
    old_id, old = stage_release(releases, "old", "sha256:" + "b" * 64)
    live_app = tmp_path / "live-app"
    live_models = tmp_path / "live-models"
    live_app.symlink_to(old / "app")
    live_models.symlink_to(old / "models")

    code = module.deploy_release(
        release_id, releases, live_app, live_models,
        command_runner=Recorder({**image_map(release_id), **image_map(old_id, "sha256:" + "b" * 64)}, fail_old=True), health_checker=lambda port: False,
        prestart_checker=lambda app, models, env: None,
    )

    assert code == 4
    diagnostic = json.loads(capsys.readouterr().err.splitlines()[-1])
    assert diagnostic["诊断码"] == "rollback_failed"


def test_first_deploy_runtime_failure_leaves_no_live_links(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    release_id, _ = stage_release(releases)
    live_app = tmp_path / "live-app"
    live_models = tmp_path / "live-models"

    code = module.deploy_release(
        release_id, releases, live_app, live_models,
        command_runner=Recorder(image_map(release_id)), health_checker=lambda port: False,
        prestart_checker=lambda app, models, env: None,
    )

    assert code != 0
    assert not os.path.lexists(live_app)
    assert not os.path.lexists(live_models)


def test_default_prestart_runs_gpu_selection_and_runtime_verification(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    release_id, _ = stage_release(releases)
    runner = Recorder(image_map(release_id))

    code = module.deploy_release(
        release_id, releases, tmp_path / "live-app", tmp_path / "live-models",
        command_runner=runner, health_checker=lambda port: True,
    )

    assert code == 0
    flattened = [" ".join(call[0]) for call in runner.calls]
    assert any("select_gpu_devices.py" in command for command in flattened)
    assert any("verify_runtime.py prestart" in command for command in flattened)
    assert any("--output" in command for command in flattened)


def test_missing_or_mismatched_preloaded_image_fails_before_switch(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    release_id, _ = stage_release(releases)
    old_app = tmp_path / "old/app"
    old_models = tmp_path / "old/models"
    old_app.mkdir(parents=True)
    old_models.mkdir(parents=True)
    for images in ({}, image_map(release_id, "sha256:" + "f" * 64)):
        live_app = tmp_path / f"live-app-{len(images)}"
        live_models = tmp_path / f"live-models-{len(images)}"
        live_app.symlink_to(old_app)
        live_models.symlink_to(old_models)
        code = module.deploy_release(
            release_id, releases, live_app, live_models,
            command_runner=Recorder(images), health_checker=lambda port: True,
            prestart_checker=lambda app, models, env: None,
        )
        assert code == 2
        assert live_app.resolve() == old_app.resolve()
        assert live_models.resolve() == old_models.resolve()


def test_first_runtime_failure_can_retry_same_preloaded_release(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    release_id, release = stage_release(releases)
    runner = Recorder(image_map(release_id))
    live_app, live_models = tmp_path / "live-app", tmp_path / "live-models"

    first = module.deploy_release(
        release_id, releases, live_app, live_models, runner, lambda port: False,
        lambda app, models, env: None,
    )
    second = module.deploy_release(
        release_id, releases, live_app, live_models, runner, lambda port: True,
        lambda app, models, env: None,
    )

    assert first == 2 and second == 0
    assert live_app.resolve() == (release / "app").resolve()
    assert not any(call[0][:3] in {("docker", "image", "tag"), ("docker", "image", "rm")} for call in runner.calls)


def test_manifest_rejects_unregistered_app_file(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    release_id, release = stage_release(releases)
    (release / "app/compose.override.yaml").write_text("services: {}")

    try:
        module.verify_manifest(release_id, release / "app", release / "models")
    except ValueError as exc:
        assert "文件集合" in str(exc)
    else:
        raise AssertionError("未登记 app 文件必须导致 manifest 校验失败")

    (release / "app/compose.override.yaml").unlink()
    (release / "app/nested").mkdir()
    (release / "app/nested/.env").write_text("UNREGISTERED=x")
    try:
        module.verify_manifest(release_id, release / "app", release / "models")
    except ValueError as exc:
        assert "nested/.env" in str(exc)
    else:
        raise AssertionError("只有 app 根目录 .env 可作为运行时文件排除")


def test_default_health_uses_private_bind_address(monkeypatch):
    module = load_module()
    captured = {}

    class Response:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return b'{"loaded":false}'

    def urlopen(url, timeout):
        captured["url"] = url
        return Response()

    monkeypatch.setenv("RETRIEVAL_BIND_ADDRESS", "10.99.8.28")
    monkeypatch.setattr(module.urllib.request, "urlopen", urlopen)

    assert module._default_health(8011) is True
    assert captured["url"] == "http://10.99.8.28:8011/health"


class FirstDeployCleanupRunner(Recorder):
    def __init__(self, release_id, failure=None):
        super().__init__(image_map(release_id))
        self.failure = failure
        self.removed = False

    def __call__(self, command, cwd=None, env=None):
        if command[:3] == ["docker", "compose", "down"]:
            self.calls.append((tuple(command), Path(cwd), dict(env or {})))
            raise RuntimeError("compose down exploded")
        if command[:3] == ["docker", "ps", "-aq"]:
            self.calls.append((tuple(command), Path(cwd) if cwd else None, dict(env or {})))
            if self.failure == "verify":
                return "container-1\n"
            return "" if self.removed else "container-1\n"
        if command[:3] == ["docker", "rm", "-f"]:
            self.calls.append((tuple(command), Path(cwd) if cwd else None, dict(env or {})))
            if self.failure == "remove":
                raise RuntimeError("force rm exploded")
            self.removed = True
            return ""
        return super().__call__(command, cwd, env)


def test_first_deploy_down_failure_forces_project_cleanup_and_returns_two(tmp_path):
    module = load_module()
    releases = tmp_path / "releases"
    release_id, _ = stage_release(releases)
    runner = FirstDeployCleanupRunner(release_id)
    live_app, live_models = tmp_path / "live-app", tmp_path / "live-models"

    code = module.deploy_release(
        release_id, releases, live_app, live_models,
        runner, lambda port: False, lambda app, models, env: None,
    )

    assert code == 2
    assert not os.path.lexists(live_app) and not os.path.lexists(live_models)
    assert any(call[0][:3] == ("docker", "rm", "-f") for call in runner.calls)
    ps_calls = [call for call in runner.calls if call[0][:3] == ("docker", "ps", "-aq")]
    assert len(ps_calls) == 2
    assert all("label=com.docker.compose.project=bgpkb-retrieval-models" in call[0] for call in ps_calls)


def test_first_deploy_force_cleanup_or_verification_failure_returns_four(tmp_path, capsys):
    module = load_module()
    for failure in ("remove", "verify"):
        releases = tmp_path / failure / "releases"
        release_id, _ = stage_release(releases)
        runner = FirstDeployCleanupRunner(release_id, failure)
        live_app = tmp_path / failure / "live-app"
        live_models = tmp_path / failure / "live-models"

        code = module.deploy_release(
            release_id, releases, live_app, live_models,
            runner, lambda port: False, lambda app, models, env: None,
        )

        assert code == 4
        assert not os.path.lexists(live_app) and not os.path.lexists(live_models)
        diagnostic = json.loads(capsys.readouterr().err.splitlines()[-1])
        assert diagnostic["诊断码"] == "first_deploy_cleanup_failed"
        assert "原因" in diagnostic and diagnostic["原因"]
