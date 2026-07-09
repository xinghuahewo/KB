#!/usr/bin/env python3
"""按固定 revision 准备模型，并在真实文件校验后原子生成 lock。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def model_files(directory):
    return [{"path": path.relative_to(directory).as_posix(), "sha256": sha256_file(path)}
            for path in sorted(directory.rglob("*")) if path.is_file()]


def canonical(payload):
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def lock_is_valid(manifest, models_root, lock_path):
    try:
        lock = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return False
    expected = {(item["model"], item["revision"]) for item in manifest["models"]}
    actual = {(item["model"], item["revision"]) for item in lock.get("models", [])}
    if actual != expected:
        return False
    return all(
        (Path(models_root) / item["model"]).is_dir()
        and model_files(Path(models_root) / item["model"]) == item.get("files")
        for item in lock["models"]
    )


def _atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=path.parent, prefix=f"{path.name}.", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def prepare_models(manifest_path, models_root, lock_path, downloader=None):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    models_root, lock_path = Path(models_root), Path(lock_path)
    if lock_is_valid(manifest, models_root, lock_path):
        return json.loads(lock_path.read_text(encoding="utf-8"))
    if downloader is None:
        from huggingface_hub import snapshot_download
        downloader = snapshot_download
    models_root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".prepare-models-", dir=models_root))
    try:
        prepared = []
        for item in manifest["models"]:
            destination = staging / item["model"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            downloader(repo_id=item["model"], revision=item["revision"], local_dir=destination,
                       local_dir_use_symlinks=False)
            files = model_files(destination)
            if not files:
                raise RuntimeError(f"模型下载结果为空: {item['model']}")
            prepared.append({**item, "files": files})
        for item in prepared:
            source, target = staging / item["model"], models_root / item["model"]
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                shutil.rmtree(target)
            os.replace(source, target)
        lock = {"models": prepared}
        _atomic_write(lock_path, canonical(lock))
        return lock
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("model_manifest.json"))
    parser.add_argument("--models-root", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    args = parser.parse_args()
    prepare_models(args.manifest, args.models_root, args.lock)


if __name__ == "__main__":
    main()
