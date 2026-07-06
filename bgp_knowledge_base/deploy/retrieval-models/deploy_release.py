#!/usr/bin/env python3
"""部署不可变检索模型 release，并在运行态失败时恢复旧 release。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request


RELEASE_PATTERN = re.compile(r"^[0-9a-f]{64}$")
PROJECT_NAME = "bgpkb-retrieval-models"


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _canonical(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def verify_manifest(release_id, app, models):
    manifest_path = app / "release_manifest.json"
    content = manifest_path.read_bytes()
    if hashlib.sha256(content).hexdigest() != release_id:
        raise ValueError("release ID 与 manifest 不匹配")
    manifest = json.loads(content)
    files = manifest["app_files"]
    for entry in files:
        path = (app / entry["path"]).resolve()
        if app.resolve() not in path.parents or _sha256(path) != entry["sha256"]:
            raise ValueError(f"app 文件哈希不匹配: {entry['path']}")
    if hashlib.sha256(_canonical(files)).hexdigest() != manifest["app_tree_sha256"]:
        raise ValueError("app tree 哈希不匹配")
    lock = models / "model_manifest.lock.json"
    if _sha256(lock) != manifest["model_lock_sha256"]:
        raise ValueError("模型 lock 哈希不匹配")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", manifest["image_digest"]):
        raise ValueError("镜像 digest 不是不可变引用")
    return manifest


def _default_runner(command, cwd=None, env=None):
    return subprocess.run(command, cwd=cwd, env=env, check=True, text=True, capture_output=True).stdout


def _default_health(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=10) as response:
            payload = json.loads(response.read())
            return response.status == 200 and isinstance(payload.get("loaded"), bool)
    except Exception:
        return False


def _replace_link(link, target):
    link = Path(link)
    target = Path(target).resolve()
    temporary = link.with_name(f".{link.name}.{os.getpid()}.tmp")
    if os.path.lexists(temporary):
        temporary.unlink()
    temporary.symlink_to(target)
    os.replace(temporary, link)


def _remove_link(link):
    if os.path.lexists(link):
        Path(link).unlink()


def _compose_up(runner, app, env, force=False):
    command = ["docker", "compose", "up"]
    if force:
        command.append("--force-recreate")
    command.extend(["--pull", "never", "-d"])
    runner(command, cwd=app, env=env)


def deploy_release(
    release_id,
    releases_root=Path("/srv/bgpkb/retrieval-releases"),
    live_app=Path("/srv/bgpkb/retrieval-models"),
    live_models=Path("/srv/bgpkb/retrieval-models-models"),
    command_runner=None,
    health_checker=None,
    prestart_checker=None,
):
    if not RELEASE_PATTERN.fullmatch(release_id):
        return 2
    runner = command_runner or _default_runner
    health = health_checker or _default_health
    release = Path(releases_root) / release_id
    app = release / "app"
    models = release / "models"
    try:
        manifest = verify_manifest(release_id, app, models)
        env_path = app / ".env"
        if prestart_checker is None:
            runner([
                sys.executable, str(app / "select_gpu_devices.py"),
                "--policy", str(app / "gpu_policy.json"), "--env", str(env_path),
            ], cwd=app, env=os.environ.copy())
        prior_env = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
        retained = "\n".join(
            line for line in prior_env.splitlines()
            if line.startswith(("EMBEDDING_GPU_", "RERANKER_GPU_"))
        )
        env_path.write_text(
            (retained + "\n" if retained else "")
            + f"RETRIEVAL_IMAGE=bgpkb-retrieval-models:{release_id}\n"
            + f"COMPOSE_PROJECT_NAME={PROJECT_NAME}\n",
            encoding="utf-8",
        )
        runtime_env = os.environ.copy()
        runtime_env.update({
            "RETRIEVAL_IMAGE": f"bgpkb-retrieval-models:{release_id}",
            "COMPOSE_PROJECT_NAME": PROJECT_NAME,
        })
        if prestart_checker:
            prestart_checker(app, models, runtime_env)
        else:
            runner([
                sys.executable, str(app / "verify_runtime.py"), "prestart",
                "--models-root", str(models),
                "--lock", str(models / "model_manifest.lock.json"),
                "--env", str(env_path),
                "--policy", str(app / "gpu_policy.json"),
            ], cwd=app, env=runtime_env)
        try:
            existing = runner(["docker", "image", "inspect", f"bgpkb-retrieval-models:{release_id}"], cwd=app, env=runtime_env)
        except Exception:
            existing = None
        if existing:
            raise RuntimeError("release 镜像 tag 已存在，禁止覆盖")
        runner(["docker", "image", "tag", manifest["image_digest"], f"bgpkb-retrieval-models:{release_id}"], cwd=app, env=runtime_env)
    except Exception:
        return 2

    old_app = Path(live_app).resolve() if os.path.lexists(live_app) else None
    old_models = Path(live_models).resolve() if os.path.lexists(live_models) else None
    try:
        _replace_link(live_app, app)
        _replace_link(live_models, models)
        _compose_up(runner, app, runtime_env)
        if not health(8011) or not health(8012):
            raise RuntimeError("新 release health 检查失败")
        return 0
    except Exception:
        try:
            runner(["docker", "compose", "down"], cwd=app, env=runtime_env)
        except Exception:
            pass
        if old_app is None or old_models is None:
            _remove_link(live_app)
            _remove_link(live_models)
            return 2
        try:
            _replace_link(live_app, old_app)
            _replace_link(live_models, old_models)
            _compose_up(runner, old_app, os.environ.copy(), force=True)
            if not health(8011) or not health(8012):
                raise RuntimeError("旧 release health 恢复失败")
        except Exception:
            return 4
        return 3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("release_id")
    args = parser.parse_args()
    raise SystemExit(deploy_release(args.release_id))


if __name__ == "__main__":
    main()
