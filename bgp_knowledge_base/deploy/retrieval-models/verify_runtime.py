#!/usr/bin/env python3
"""启动前后检索模型运行态预检（仅标准库与 nvidia-smi）。"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request


GPU_COMMAND = ["nvidia-smi", "--query-gpu=index,memory.total,memory.used", "--format=csv,noheader,nounits"]


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_model_lock(models_root, lock_path):
    models_root = Path(models_root)
    lock = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    for model in lock["models"]:
        directory = models_root / model["model"]
        expected = {item["path"]: item["sha256"] for item in model["files"]}
        actual_paths = {path.relative_to(directory).as_posix() for path in directory.rglob("*") if path.is_file()}
        if actual_paths != set(expected):
            raise RuntimeError(f"模型文件集合与 lock 不一致: {model['model']}")
        for relative, digest in expected.items():
            if _sha256(directory / relative) != digest:
                raise RuntimeError(f"模型文件哈希不一致: {model['model']}/{relative}")


def _parse_env(path):
    values = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def verify_gpu_selection(env_path, policy_path, command_runner=None):
    env = _parse_env(env_path)
    policy = json.loads(Path(policy_path).read_text(encoding="utf-8"))
    embedding = int(env["EMBEDDING_GPU_INDEX"])
    reranker = int(env["RERANKER_GPU_INDEX"])
    if embedding == reranker or embedding not in policy["allowed_indices"] or reranker not in policy["allowed_indices"]:
        raise RuntimeError("GPU 选择不符合 allowed_indices 或设备不互异")
    if env["EMBEDDING_GPU_CDI"] != f"nvidia.com/gpu={embedding}" or env["RERANKER_GPU_CDI"] != f"nvidia.com/gpu={reranker}":
        raise RuntimeError("GPU CDI 与 index 不一致")
    runner = command_runner or (lambda command: subprocess.check_output(command, text=True))
    gpus = {}
    for line in runner(GPU_COMMAND).splitlines():
        index, total, used = (int(part.strip()) for part in line.split(","))
        gpus[index] = total - used
    if gpus.get(embedding, -1) < policy["embedding"]["min_free_mib"]:
        raise RuntimeError("embedding GPU 实时空闲显存不足")
    if gpus.get(reranker, -1) < policy["reranker"]["min_free_mib"]:
        raise RuntimeError("reranker GPU 实时空闲显存不足")


def verify_prestart(models_root, lock_path, env_path, policy_path, command_runner=None):
    verify_model_lock(models_root, lock_path)
    verify_gpu_selection(env_path, policy_path, command_runner)


def _fetch_health(port):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def verify_health(fetcher=None):
    fetcher = fetcher or _fetch_health
    expected = {8011: ("embedding", "BAAI/bge-m3"), 8012: ("reranker", "BAAI/bge-reranker-v2-m3")}
    for port, (role, model) in expected.items():
        payload = fetcher(port)
        if payload.get("role") != role or payload.get("model") != model:
            raise RuntimeError(f"端口 {port} health 角色或模型错误")
        if not isinstance(payload.get("loaded"), bool) or not all(payload.get(key) for key in ("revision", "device")):
            raise RuntimeError(f"端口 {port} health 元数据不完整")
        if any(key in payload for key in ("path", "model_root", "api_key", "token")):
            raise RuntimeError(f"端口 {port} health 暴露敏感字段")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="phase", required=True)
    prestart = subparsers.add_parser("prestart")
    prestart.add_argument("--models-root", type=Path, required=True)
    prestart.add_argument("--lock", type=Path, required=True)
    prestart.add_argument("--env", type=Path, required=True)
    prestart.add_argument("--policy", type=Path, required=True)
    subparsers.add_parser("health")
    args = parser.parse_args()
    if args.phase == "prestart":
        verify_prestart(args.models_root, args.lock, args.env, args.policy)
    else:
        verify_health()


if __name__ == "__main__":
    main()
