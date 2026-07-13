#!/usr/bin/env python3
"""以原子符号链接维护代码与数据制品的当前/上一版本。"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys


STATE_FILE = "deployment-state.json"


def _validate_code_release(path: Path, *, require_manifest: bool = True) -> Path:
    path = path.expanduser().resolve()
    missing = [name for name in ("backend", "frontend") if not (path / name).is_dir()]
    if not (path / "frontend" / "out" / "index.html").is_file():
        missing.append("frontend/out/index.html")
    if require_manifest and not (path / "release-manifest.json").is_file():
        missing.append("release-manifest.json")
    if missing:
        raise ValueError(f"代码 release 不完整：{path}，缺少 {', '.join(missing)}")
    return path


def _validate_artifact_release(path: Path) -> Path:
    path = path.expanduser().resolve()
    if not (path / "data").is_dir():
        raise ValueError(f"制品 release 不完整：{path}，缺少 data/")
    return path


def _read_state(root: Path) -> dict:
    state_path = root / STATE_FILE
    if not state_path.exists():
        return {
            "schema_version": 1,
            "current_code": None,
            "previous_code": None,
            "current_artifact": None,
            "previous_artifact": None,
            "current_legacy": False,
            "previous_legacy": False,
        }
    return json.loads(state_path.read_text(encoding="utf-8"))


def _ensure_replaceable_links(root: Path) -> None:
    for name in (
        "current-generation",
        "current",
        "current-artifact",
        "bgp_knowledge_base",
        "chat_frontend",
        STATE_FILE,
    ):
        path = root / name
        if (path.exists() or path.is_symlink()) and not path.is_symlink():
            raise ValueError(
                f"兼容路径已被真实文件占用：{path}；首次迁移前请先移动到备份目录，脚本不会覆盖。"
            )


def _replace_symlink(link: Path, target: Path) -> None:
    temporary = link.with_name(f".{link.name}.next-{os.getpid()}")
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(target)
    os.replace(temporary, link)


def _ensure_fixed_links(root: Path) -> None:
    fixed = {
        "current": Path("current-generation/code"),
        "current-artifact": Path("current-generation/artifact"),
        "bgp_knowledge_base": Path("current/backend"),
        "chat_frontend": Path("current/frontend"),
        STATE_FILE: Path(f"current-generation/{STATE_FILE}"),
    }
    for name, target in fixed.items():
        link = root / name
        if not link.is_symlink() or link.readlink() != target:
            _replace_symlink(link, target)


def _switch(root: Path, state: dict) -> None:
    code = Path(state["current_code"])
    artifact = Path(state["current_artifact"])
    _ensure_fixed_links(root)
    generations = root / "generations"
    generations.mkdir(exist_ok=True)
    generation_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + f"-{os.getpid()}"
    generation = generations / generation_id
    generation.mkdir()
    try:
        (generation / "code").symlink_to(code)
        (generation / "artifact").symlink_to(artifact)
        (generation / STATE_FILE).write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        _replace_symlink(root / "current-generation", generation)
    except Exception:
        shutil.rmtree(generation, ignore_errors=True)
        raise


def activate(root: Path, code: Path, artifact: Path) -> None:
    root = root.expanduser().resolve()
    code = _validate_code_release(code)
    artifact = _validate_artifact_release(artifact)
    root.mkdir(parents=True, exist_ok=True)
    _ensure_replaceable_links(root)
    current = _read_state(root)
    state = {
        "schema_version": 1,
        "current_code": str(code),
        "previous_code": current.get("current_code"),
        "current_artifact": str(artifact),
        "previous_artifact": current.get("current_artifact"),
        "current_legacy": False,
        "previous_legacy": current.get("current_legacy", False),
        "deployed_at": datetime.now(timezone.utc).isoformat(),
    }
    _switch(root, state)


def bootstrap(root: Path, code: Path, artifact: Path) -> None:
    root = root.expanduser().resolve()
    code = _validate_code_release(code, require_manifest=False)
    artifact = _validate_artifact_release(artifact)
    root.mkdir(parents=True, exist_ok=True)
    _ensure_replaceable_links(root)
    if (root / "current-generation").is_symlink():
        raise ValueError("部署状态已存在，bootstrap 只能用于首次迁移。")
    state = {
        "schema_version": 1,
        "current_code": str(code),
        "previous_code": str(code),
        "current_artifact": str(artifact),
        "previous_artifact": str(artifact),
        "current_legacy": True,
        "previous_legacy": True,
        "deployed_at": datetime.now(timezone.utc).isoformat(),
    }
    _switch(root, state)


def check_rollback(root: Path) -> None:
    root = root.expanduser().resolve()
    state = _read_state(root)
    previous_code = state.get("previous_code")
    previous_artifact = state.get("previous_artifact")
    if not previous_code or not previous_artifact:
        raise ValueError("没有可回滚的上一代码与制品版本；首次部署前必须执行 bootstrap。")
    _validate_code_release(Path(previous_code), require_manifest=not state.get("previous_legacy", False))
    _validate_artifact_release(Path(previous_artifact))


def rollback(root: Path) -> None:
    root = root.expanduser().resolve()
    _ensure_replaceable_links(root)
    current = _read_state(root)
    previous_code = current.get("previous_code")
    previous_artifact = current.get("previous_artifact")
    if not previous_code or not previous_artifact:
        raise ValueError("没有可回滚的上一代码与制品版本。")
    _validate_code_release(Path(previous_code), require_manifest=not current.get("previous_legacy", False))
    _validate_artifact_release(Path(previous_artifact))
    state = {
        "schema_version": 1,
        "current_code": previous_code,
        "previous_code": current.get("current_code"),
        "current_artifact": previous_artifact,
        "previous_artifact": current.get("current_artifact"),
        "current_legacy": current.get("previous_legacy", False),
        "previous_legacy": current.get("current_legacy", False),
        "deployed_at": datetime.now(timezone.utc).isoformat(),
    }
    _switch(root, state)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    activate_parser = subparsers.add_parser("activate")
    activate_parser.add_argument("deploy_root", type=Path)
    activate_parser.add_argument("code_release", type=Path)
    activate_parser.add_argument("artifact_release", type=Path)
    bootstrap_parser = subparsers.add_parser("bootstrap")
    bootstrap_parser.add_argument("deploy_root", type=Path)
    bootstrap_parser.add_argument("code_release", type=Path)
    bootstrap_parser.add_argument("artifact_release", type=Path)
    check_parser = subparsers.add_parser("check-rollback")
    check_parser.add_argument("deploy_root", type=Path)
    rollback_parser = subparsers.add_parser("rollback")
    rollback_parser.add_argument("deploy_root", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "activate":
            activate(args.deploy_root, args.code_release, args.artifact_release)
        elif args.command == "bootstrap":
            bootstrap(args.deploy_root, args.code_release, args.artifact_release)
        elif args.command == "check-rollback":
            check_rollback(args.deploy_root)
        else:
            rollback(args.deploy_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"部署状态切换失败：{exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
