#!/usr/bin/env python3
"""验证 Docling 离线模型、GPU 和运行边界，任一缺口均失败关闭。"""

import argparse
import hashlib
import json
import os
from pathlib import Path


OFFLINE_ENV = {
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
}


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(path):
    """对目录内非缓存文件的路径、大小和内容 hash 形成稳定摘要。"""
    digest = hashlib.sha256()
    files = sorted(
        item
        for item in path.rglob("*")
        if item.is_file() and ".cache" not in item.relative_to(path).parts
    )
    for item in files:
        relative = item.relative_to(path).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(item.stat().st_size).encode("ascii"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(item)))
    return digest.hexdigest()


def collect_gpu_evidence():
    try:
        import torch
    except (ImportError, OSError) as exc:
        return {"cuda_available": False, "error": str(exc)}

    available = torch.cuda.is_available()
    evidence = {
        "cuda_available": available,
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
    }
    if available:
        properties = torch.cuda.get_device_properties(0)
        evidence.update(
            {
                "device_name": properties.name,
                "device_count": torch.cuda.device_count(),
                "total_memory_bytes": properties.total_memory,
            }
        )
    return evidence


def _error(code, **details):
    return {"code": code, **details}


def verify_runtime(
    manifest_path,
    model_root,
    expected_image_digest=None,
    *,
    check_models=True,
    check_gpu=True,
    check_offline=False,
):
    manifest_path = Path(manifest_path)
    model_root = Path(model_root).resolve()
    result = {"ok": True, "errors": [], "models": [], "gpu": {}}

    if check_models:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            result["errors"].append(_error("manifest_invalid", detail=str(exc)))
            manifest = {"models": []}

        for model in manifest.get("models", []):
            relative_path = model.get("path", "")
            artifact = (model_root / relative_path).resolve()
            if artifact != model_root and model_root not in artifact.parents:
                result["errors"].append(
                    _error("model_path_escape", name=model.get("name", ""), path=relative_path)
                )
                continue
            if not artifact.exists():
                result["errors"].append(
                    _error("model_missing", name=model.get("name", ""), path=relative_path)
                )
                continue
            actual_sha256 = sha256_tree(artifact) if artifact.is_dir() else sha256_file(artifact)
            result["models"].append(
                {
                    "name": model.get("name", ""),
                    "path": relative_path,
                    "expected_sha256": model.get("sha256", ""),
                    "actual_sha256": actual_sha256,
                }
            )
            if actual_sha256 != model.get("sha256"):
                result["errors"].append(
                    _error(
                        "model_hash_mismatch",
                        name=model.get("name", ""),
                        expected=model.get("sha256", ""),
                        actual=actual_sha256,
                    )
                )

    if check_gpu:
        result["gpu"] = collect_gpu_evidence()
        if not result["gpu"].get("cuda_available"):
            result["errors"].append(_error("gpu_unavailable"))

    if check_offline:
        invalid = {
            key: os.environ.get(key)
            for key, expected in OFFLINE_ENV.items()
            if os.environ.get(key) != expected
        }
        if invalid:
            result["errors"].append(_error("offline_environment_invalid", values=invalid))
        artifacts_path = os.environ.get("DOCLING_ARTIFACTS_PATH", "")
        if not artifacts_path or Path(artifacts_path).resolve() != model_root:
            result["errors"].append(
                _error("artifacts_path_invalid", value=artifacts_path, expected=str(model_root))
            )

    if expected_image_digest:
        actual_digest = os.environ.get("BGPKB_IMAGE_DIGEST", "")
        if actual_digest != expected_image_digest:
            result["errors"].append(
                _error(
                    "image_digest_mismatch",
                    expected=expected_image_digest,
                    actual=actual_digest,
                )
            )

    result["ok"] = not result["errors"]
    return result


def parse_args():
    parser = argparse.ArgumentParser(description="验证 Docling 离线运行环境")
    parser.add_argument("--manifest", default="/opt/docling/model_manifest.json")
    parser.add_argument("--model-root", default="/opt/docling/models")
    parser.add_argument("--expected-image-digest")
    parser.add_argument("--skip-models", action="store_true")
    parser.add_argument("--skip-gpu", action="store_true")
    parser.add_argument("--skip-offline", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    result = verify_runtime(
        args.manifest,
        args.model_root,
        args.expected_image_digest,
        check_models=not args.skip_models,
        check_gpu=not args.skip_gpu,
        check_offline=not args.skip_offline,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
