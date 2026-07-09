import importlib.util
import hashlib
import json
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "deploy/retrieval-models/build_release_manifest.py"


def load_module():
    spec = importlib.util.spec_from_file_location("release_manifest", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_tree(tmp_path):
    app = tmp_path / "app"
    app.mkdir()
    (app / "service.py").write_text("service")
    (app / "compose.yaml").write_text("compose")
    (app / ".env").write_text("SECRET=x")
    lock = tmp_path / "model_manifest.lock.json"
    lock.write_text('{"models":[]}')
    return app, lock


def test_manifest_is_canonical_deterministic_and_excludes_special_files(tmp_path):
    module = load_module()
    app, lock = make_tree(tmp_path)
    output = app / "release_manifest.json"
    digest = "sha256:" + "a" * 64

    first = module.build_manifest(app, lock, digest, output)
    second = module.build_manifest(app, lock, digest, output)

    assert first == second
    parsed = json.loads(first)
    assert [entry["path"] for entry in parsed["app_files"]] == ["compose.yaml", "service.py"]
    assert "release_id" not in parsed
    assert output.read_bytes() == first
    assert b" " not in first and not first.endswith(b"\n")
    assert len(module.release_id(first)) == 64


def test_manifest_only_excludes_root_runtime_files(tmp_path):
    module = load_module()
    app, lock = make_tree(tmp_path)
    (app / "nested").mkdir()
    (app / "nested/.env").write_text("tracked")

    parsed = json.loads(module.build_manifest(
        app, lock, "sha256:" + "a" * 64, app / "release_manifest.json"
    ))

    assert "nested/.env" in [entry["path"] for entry in parsed["app_files"]]


def test_release_id_changes_with_app_lock_or_image_digest(tmp_path):
    module = load_module()
    app, lock = make_tree(tmp_path)
    output = app / "release_manifest.json"
    initial = module.release_id(module.build_manifest(app, lock, "sha256:" + "a" * 64, output))

    (app / "service.py").write_text("changed")
    app_changed = module.release_id(module.build_manifest(app, lock, "sha256:" + "a" * 64, output))
    lock.write_text('{"models":[1]}')
    lock_changed = module.release_id(module.build_manifest(app, lock, "sha256:" + "a" * 64, output))
    image_changed = module.release_id(module.build_manifest(app, lock, "sha256:" + "b" * 64, output))

    assert len({initial, app_changed, lock_changed, image_changed}) == 4


def test_rejects_mutable_image_identifier(tmp_path):
    module = load_module()
    app, lock = make_tree(tmp_path)

    try:
        module.build_manifest(app, lock, "bgpkb-retrieval-models:latest", app / "release.json")
    except ValueError as exc:
        assert "digest" in str(exc)
    else:
        raise AssertionError("必须拒绝可变镜像标签")


def test_prepare_models_downloads_exact_revisions_and_reuses_only_verified_lock(tmp_path):
    root = SCRIPT.parent
    prepare_path = root / "prepare_models.py"
    spec = importlib.util.spec_from_file_location("prepare_models", prepare_path)
    prepare = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prepare)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"models": [{"model": "org/model", "revision": "abc123"}]}))
    models = tmp_path / "models"
    lock = tmp_path / "model_manifest.lock.json"
    calls = []

    def downloader(repo_id, revision, local_dir, **kwargs):
        calls.append((repo_id, revision))
        destination = Path(local_dir)
        destination.mkdir(parents=True)
        (destination / "weights.bin").write_bytes(b"weights")

    prepare.prepare_models(manifest, models, lock, downloader=downloader)
    first = lock.read_bytes()
    prepare.prepare_models(manifest, models, lock, downloader=downloader)

    assert calls == [("org/model", "abc123")]
    assert lock.read_bytes() == first
    assert json.loads(first)["models"][0]["files"] == [{
        "path": "weights.bin",
        "sha256": hashlib.sha256(b"weights").hexdigest(),
    }]

    (models / "org/model/weights.bin").write_bytes(b"tampered")
    prepare.prepare_models(manifest, models, lock, downloader=downloader)
    assert calls == [("org/model", "abc123"), ("org/model", "abc123")]
