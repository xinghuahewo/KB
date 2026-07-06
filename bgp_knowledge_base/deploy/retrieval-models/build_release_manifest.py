#!/usr/bin/env python3
"""构建不可变检索模型 release manifest。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def release_id(canonical_manifest):
    return hashlib.sha256(canonical_manifest).hexdigest()


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


def build_manifest(app_dir, model_lock, image_digest, output_path):
    app_dir = Path(app_dir).resolve()
    model_lock = Path(model_lock).resolve()
    output_path = Path(output_path).resolve()
    if not DIGEST_PATTERN.fullmatch(image_digest):
        raise ValueError("image_digest 必须是不可变 sha256 digest")
    files = []
    for path in app_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.resolve() in {model_lock, output_path} or path.name == ".env" or path.name == "model_manifest.lock.json":
            continue
        relative = path.relative_to(app_dir).as_posix()
        files.append({"path": relative, "sha256": sha256_file(path)})
    files.sort(key=lambda entry: entry["path"])
    app_tree_sha256 = hashlib.sha256(canonical_json(files)).hexdigest()
    payload = {
        "app_files": files,
        "app_tree_sha256": app_tree_sha256,
        "image_digest": image_digest,
        "model_lock_sha256": sha256_file(model_lock),
    }
    content = canonical_json(payload)
    _atomic_write(output_path, content)
    return content


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-dir", type=Path, required=True)
    parser.add_argument("--model-lock", type=Path, required=True)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    content = build_manifest(args.app_dir, args.model_lock, args.image_digest, args.output)
    print(release_id(content))


if __name__ == "__main__":
    main()
