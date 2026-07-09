import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = ROOT / "deploy" / "docling"
DOCKERFILE = DEPLOY_DIR / "Dockerfile"
LOCKFILE = DEPLOY_DIR / "requirements.lock"
MODEL_MANIFEST = DEPLOY_DIR / "model_manifest.json"
VERIFIER = DEPLOY_DIR / "verify_offline_runtime.py"
OPERATIONS_DOC = ROOT / "docs" / "operations" / "docling_private_runtime_v1.md"


def load_verifier():
    assert VERIFIER.exists(), "离线运行验证器尚未实现"
    spec = importlib.util.spec_from_file_location("verify_offline_runtime", VERIFIER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_manifest(path, file_path, sha256):
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "models": [
                    {
                        "name": "fixture-model",
                        "version": "1.0.0",
                        "path": file_path,
                        "sha256": sha256,
                        "license": "MIT",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_runtime_assets_and_version_matrix_are_locked():
    for path in (DOCKERFILE, LOCKFILE, MODEL_MANIFEST, VERIFIER, OPERATIONS_DOC):
        assert path.exists(), f"缺少运行环境资产：{path.relative_to(ROOT)}"

    lock_text = LOCKFILE.read_text(encoding="utf-8")
    assert "docling==2.107.0" in lock_text
    assert "torch==2.10.0+cu128" in lock_text
    assert "--hash=sha256:" in lock_text

    operations = OPERATIONS_DOC.read_text(encoding="utf-8")
    for expected in (
        "root@10.99.8.28",
        "4 × NVIDIA GeForce RTX 2080 Ti",
        "11264 MiB",
        "545.23.08",
        "Docker 29.1.3",
        "nvidia.com/gpu=1",
        "sha256:273131691988d0b069c158fea9d5ea9aa597d5cc095288c3ee0baed315fc24f2",
        "Python 3.11",
        "Docling 2.107.0",
        "CUDA 12.8",
    ):
        assert expected in operations


def test_model_manifest_is_nonempty_and_has_auditable_fields():
    manifest = json.loads(MODEL_MANIFEST.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == 1
    assert manifest["models"]
    for model in manifest["models"]:
        assert {"name", "version", "path", "sha256", "license"} <= set(model)
        assert len(model["sha256"]) == 64
        int(model["sha256"], 16)
        assert model["sha256"] != "0" * 64


def test_verifier_fails_closed_for_missing_and_mismatched_models(tmp_path):
    verifier = load_verifier()
    manifest_path = tmp_path / "manifest.json"
    model_root = tmp_path / "models"
    model_root.mkdir()

    write_manifest(manifest_path, "missing.bin", "a" * 64)
    missing = verifier.verify_runtime(manifest_path, model_root, check_gpu=False)
    assert missing["ok"] is False
    assert missing["errors"][0]["code"] == "model_missing"

    artifact = model_root / "model.bin"
    artifact.write_bytes(b"unexpected")
    write_manifest(manifest_path, "model.bin", "b" * 64)
    mismatch = verifier.verify_runtime(manifest_path, model_root, check_gpu=False)
    assert mismatch["ok"] is False
    assert mismatch["errors"][0]["code"] == "model_hash_mismatch"


def test_verifier_accepts_complete_offline_fixture_and_reports_hash(tmp_path):
    verifier = load_verifier()
    model_root = tmp_path / "models"
    model_root.mkdir()
    artifact = model_root / "model.bin"
    artifact.write_bytes(b"locked-model")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    manifest_path = tmp_path / "manifest.json"
    write_manifest(manifest_path, "model.bin", digest)

    result = verifier.verify_runtime(manifest_path, model_root, check_gpu=False)

    assert result["ok"] is True
    assert result["models"][0]["actual_sha256"] == digest


def test_gpu_preflight_rejects_missing_cuda(monkeypatch):
    verifier = load_verifier()
    monkeypatch.setattr(verifier, "collect_gpu_evidence", lambda: {"cuda_available": False})

    result = verifier.verify_runtime(MODEL_MANIFEST, DEPLOY_DIR, check_models=False)

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "gpu_unavailable"


def test_production_image_is_offline_non_root_and_has_no_download_entrypoint():
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")

    assert (
        "python:3.11.15-slim-bookworm@sha256:"
        "961f57b66f6aee85ae11272cca9219123a860ab20e2a09a1238f57e0df495825"
    ) in dockerfile
    assert {"libgl1", "libglib2.0-0", "libgomp1"} <= set(dockerfile.split())
    assert "HF_HUB_OFFLINE=1" in dockerfile
    assert "TRANSFORMERS_OFFLINE=1" in dockerfile
    assert "DOCLING_ARTIFACTS_PATH=/opt/docling/models" in dockerfile
    assert "DOCLING_DEVICE=cuda" in dockerfile
    assert "useradd --system --create-home --gid docling --home /home/docling docling" in dockerfile
    assert "USER docling" in dockerfile
    runtime_tail = dockerfile.split("FROM ")[-1]
    assert "models download" not in runtime_tail
    assert "--network=none" in dockerfile


def test_image_build_consumes_prefetched_verified_model_context():
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    operations = OPERATIONS_DOC.read_text(encoding="utf-8")

    assert "COPY --from=model_assets / /opt/docling/models" in dockerfile
    assert "docling-tools models download" not in dockerfile
    assert "--build-context model_assets=" in operations
    assert "verify_offline_runtime.py" in operations


def test_image_build_supports_an_explicit_debian_mirror_without_changing_default():
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")

    assert dockerfile.count("ARG DEBIAN_MIRROR=") == 2
    assert dockerfile.count('if [ -n "$DEBIAN_MIRROR" ]') == 2
    assert "deb.debian.org/debian-security" in dockerfile
    assert "${DEBIAN_MIRROR}/debian-security" in dockerfile

    operations = OPERATIONS_DOC.read_text(encoding="utf-8")
    assert "--build-arg DEBIAN_MIRROR=" in operations
