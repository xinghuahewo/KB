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
import time
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
    expected_paths = {entry["path"] for entry in files}
    actual_paths = set()
    for path in app.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(app).as_posix()
        if relative not in {"release_manifest.json", ".env", "model_manifest.lock.json"}:
            actual_paths.add(relative)
    if actual_paths != expected_paths:
        raise ValueError(
            f"app 文件集合不匹配: 缺失={sorted(expected_paths - actual_paths)}, "
            f"未登记={sorted(actual_paths - expected_paths)}"
        )
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


def verify_preloaded_image(runner, tag, expected_digest, cwd, env):
    output = runner(["docker", "image", "inspect", tag], cwd=cwd, env=env)
    inspected = json.loads(output)
    record = inspected[0] if isinstance(inspected, list) else inspected
    identifiers = {record.get("Id", "")}
    identifiers.update(item.rsplit("@", 1)[-1] for item in record.get("RepoDigests", []))
    if expected_digest not in identifiers:
        raise RuntimeError(f"预载镜像与 manifest 不匹配: expected={expected_digest}, actual={sorted(identifiers)}")


def validated_release_path(releases_root, release_id):
    root = Path(releases_root).resolve()
    candidate = root / release_id
    if candidate.is_symlink() or not candidate.is_dir():
        raise ValueError("release 必须是 releases_root 下的真实目录")
    resolved = candidate.resolve()
    if resolved != candidate or resolved.parent != root:
        raise ValueError("release 路径逃逸或不是直接子目录")
    return resolved


def validated_release_internal(release, name):
    candidate = release / name
    if candidate.is_symlink() or not candidate.is_dir():
        raise ValueError(f"release 内部 {name} 必须是真实目录")
    resolved = candidate.resolve()
    if resolved != candidate or release not in resolved.parents:
        raise ValueError(f"release 内部 {name} 路径逃逸")
    return resolved


def _default_runner(command, cwd=None, env=None):
    return subprocess.run(command, cwd=cwd, env=env, check=True, text=True, capture_output=True).stdout


def _default_health(
    port,
    deadline_seconds=30,
    interval_seconds=1,
    request_timeout_seconds=10,
    clock=time.monotonic,
    sleeper=time.sleep,
):
    expected = {
        8011: ("embedding", "BAAI/bge-m3"),
        8012: ("reranker", "BAAI/bge-reranker-v2-m3"),
    }
    role, model = expected[port]
    deadline = clock() + deadline_seconds
    while True:
        remaining = deadline - clock()
        if remaining <= 0:
            return False
        try:
            address = os.environ.get("RETRIEVAL_BIND_ADDRESS", "10.99.8.28")
            with urllib.request.urlopen(
                f"http://{address}:{port}/health",
                timeout=min(request_timeout_seconds, remaining),
            ) as response:
                payload = json.loads(response.read())
                if (
                    200 <= response.status < 300
                    and payload.get("loaded") is True
                    and payload.get("role") == role
                    and payload.get("model") == model
                ):
                    return True
        except Exception:
            pass
        sleeper(interval_seconds)


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


def _project_container_ids(runner, app, env):
    output = runner([
        "docker", "ps", "-aq", "--filter",
        f"label=com.docker.compose.project={PROJECT_NAME}",
    ], cwd=app, env=env)
    return [line.strip() for line in output.splitlines() if line.strip()]


def _cleanup_first_deploy(runner, app, env):
    errors = []
    try:
        runner(["docker", "compose", "down"], cwd=app, env=env)
    except Exception as exc:
        errors.append(f"compose down: {exc}")
    try:
        container_ids = _project_container_ids(runner, app, env)
    except Exception as exc:
        container_ids = []
        errors.append(f"枚举容器: {exc}")
    if container_ids:
        try:
            runner(["docker", "rm", "-f", *container_ids], cwd=app, env=env)
        except Exception as exc:
            errors.append(f"强制删除容器: {exc}")
    try:
        remaining = _project_container_ids(runner, app, env)
        if remaining:
            errors.append(f"仍有容器残留: {','.join(remaining)}")
    except Exception as exc:
        errors.append(f"验证容器残留: {exc}")
    # down 失败本身可由后续强制清理与零残留验证弥补。
    blocking = [error for error in errors if not error.startswith("compose down:")]
    return blocking, errors


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
    try:
        release = validated_release_path(releases_root, release_id)
        app = validated_release_internal(release, "app")
        models = validated_release_internal(release, "models")
        manifest = verify_manifest(release_id, app, models)
        env_path = app / ".env"
        if prestart_checker is None:
            runner([
                sys.executable, str(app / "select_gpu_devices.py"),
                "--policy", str(app / "gpu_policy.json"), "--output", str(env_path),
            ], cwd=app, env=os.environ.copy())
        runtime_env = os.environ.copy()
        runtime_env.update({
            "RETRIEVAL_IMAGE": f"bgpkb-retrieval-models:{release_id}",
            "COMPOSE_PROJECT_NAME": PROJECT_NAME,
            "RETRIEVAL_BIND_ADDRESS": os.environ.get("RETRIEVAL_BIND_ADDRESS", "10.99.8.28"),
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
        verify_preloaded_image(
            runner, f"bgpkb-retrieval-models:{release_id}", manifest["image_digest"], app, runtime_env
        )
    except Exception as exc:
        print(json.dumps({"阶段": "切换前预检", "错误": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    old_app = Path(live_app).resolve() if os.path.lexists(live_app) else None
    old_models = Path(live_models).resolve() if os.path.lexists(live_models) else None
    old_release_id = None
    old_manifest = None
    old_runtime_env = None
    if (old_app is None) != (old_models is None):
        print(json.dumps({"阶段": "旧 release 记录", "错误": "两个 live link 状态不一致"}, ensure_ascii=False), file=sys.stderr)
        return 2
    if old_app is not None:
        try:
            if old_app.parent != old_models.parent:
                raise RuntimeError("旧 app/models 不属于同一 release")
            old_release_id = old_app.parent.name
            if not RELEASE_PATTERN.fullmatch(old_release_id):
                raise RuntimeError("旧 release ID 非法")
            old_release = validated_release_path(releases_root, old_release_id)
            expected_old_app = validated_release_internal(old_release, "app")
            expected_old_models = validated_release_internal(old_release, "models")
            if old_app != expected_old_app or old_models != expected_old_models:
                raise RuntimeError("旧 live target 不属于 releases_root 的标准 app/models")
            old_manifest = verify_manifest(old_release_id, old_app, old_models)
            old_runtime_env = os.environ.copy()
            old_runtime_env.update({
                "RETRIEVAL_IMAGE": f"bgpkb-retrieval-models:{old_release_id}",
                "COMPOSE_PROJECT_NAME": PROJECT_NAME,
                "RETRIEVAL_BIND_ADDRESS": os.environ.get("RETRIEVAL_BIND_ADDRESS", "10.99.8.28"),
            })
            verify_preloaded_image(
                runner, old_runtime_env["RETRIEVAL_IMAGE"], old_manifest["image_digest"], old_app, old_runtime_env
            )
        except Exception as exc:
            print(json.dumps({"阶段": "旧 release 记录", "错误": str(exc)}, ensure_ascii=False), file=sys.stderr)
            return 2
    try:
        _replace_link(live_app, app)
        _replace_link(live_models, models)
        _compose_up(runner, app, runtime_env)
        if not health(8011) or not health(8012):
            raise RuntimeError("新 release health 检查失败")
        return 0
    except Exception:
        if old_app is None or old_models is None:
            _remove_link(live_app)
            _remove_link(live_models)
            blocking, errors = _cleanup_first_deploy(runner, app, runtime_env)
            if blocking:
                print(json.dumps({
                    "诊断码": "first_deploy_cleanup_failed",
                    "阶段": "首次部署运行态清理",
                    "原因": errors,
                }, ensure_ascii=False), file=sys.stderr)
                return 4
            return 2
        try:
            runner(["docker", "compose", "down"], cwd=app, env=runtime_env)
        except Exception:
            pass
        try:
            _replace_link(live_app, old_app)
            _replace_link(live_models, old_models)
            verify_preloaded_image(
                runner, old_runtime_env["RETRIEVAL_IMAGE"], old_manifest["image_digest"], old_app, old_runtime_env
            )
            _compose_up(runner, old_app, old_runtime_env, force=True)
            if not health(8011) or not health(8012):
                raise RuntimeError("旧 release health 恢复失败")
        except Exception as exc:
            print(json.dumps({
                "诊断码": "rollback_failed", "阶段": "回滚旧 release", "错误": str(exc)
            }, ensure_ascii=False), file=sys.stderr)
            return 4
        return 3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("release_id")
    args = parser.parse_args()
    raise SystemExit(deploy_release(args.release_id))


if __name__ == "__main__":
    main()
