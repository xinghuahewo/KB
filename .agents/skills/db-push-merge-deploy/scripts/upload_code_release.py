#!/usr/bin/env python3
"""校验并原子上传不可变代码 release；默认只输出演练计划。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import os
import re
import shlex
import subprocess
import sys
from typing import Any


DEFAULT_SERVER = "root@10.99.8.28"
DEFAULT_REMOTE_ROOT = PurePosixPath("/home/wbt/DB-code-releases")
RELEASE_ID_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
SSH_OPTIONS = (
    "-F",
    "/dev/null",
    "-o",
    "ProxyCommand=none",
    "-o",
    "ProxyJump=none",
)


def run(
    command: list[str], *, check: bool = True, input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        text=True,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"命令失败：{shlex.join(command)}\n{detail}")
    return completed


def frontend_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix().encode()
        if path.is_symlink():
            digest.update(b"L\0" + relative + b"\0" + os.readlink(path).encode())
        elif path.is_file():
            digest.update(b"F\0" + relative + b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


def validate_release(release: Path) -> tuple[dict[str, Any], str]:
    release = release.resolve()
    manifest_path = release / "release-manifest.json"
    required = (
        release / "backend",
        release / "frontend",
        release / "frontend" / "out" / "index.html",
        manifest_path,
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise ValueError(f"代码 release 不完整，缺少：{', '.join(missing)}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    release_id = manifest.get("release_id")
    commit = manifest.get("git_commit")
    expected_frontend = manifest.get("frontend_sha256")
    if not isinstance(release_id, str) or not RELEASE_ID_PATTERN.fullmatch(release_id):
        raise ValueError("release-manifest.json 的 release_id 非法。")
    if release.name != release_id:
        raise ValueError("本地目录名必须与 release-manifest.json 的 release_id 一致。")
    if not isinstance(commit, str) or not COMMIT_PATTERN.fullmatch(commit):
        raise ValueError("release-manifest.json 的 git_commit 不是完整 Git SHA。")
    if not isinstance(expected_frontend, str) or not HASH_PATTERN.fullmatch(expected_frontend):
        raise ValueError("release-manifest.json 的 frontend_sha256 非法。")
    actual_frontend = frontend_digest(release / "frontend" / "out")
    if actual_frontend != expected_frontend:
        raise ValueError("本地前端 SHA-256 与 release manifest 不一致。")
    return manifest, tree_digest(release)


REMOTE_TREE_DIGEST = r"""
import hashlib
import os
from pathlib import Path
import sys

root = Path(sys.argv[1])
digest = hashlib.sha256()
for path in sorted(root.rglob("*")):
    relative = path.relative_to(root).as_posix().encode()
    if path.is_symlink():
        digest.update(b"L\0" + relative + b"\0" + os.readlink(path).encode())
    elif path.is_file():
        digest.update(b"F\0" + relative + b"\0")
        digest.update(path.read_bytes())
print(digest.hexdigest())
"""


def remote_command(server: str, command: str, *, check: bool = True) -> str:
    completed = run(["ssh", *SSH_OPTIONS, server, command], check=check)
    return completed.stdout.strip()


def upload(
    release: Path,
    manifest: dict[str, Any],
    expected_tree_digest: str,
    *,
    server: str,
    remote_root: PurePosixPath,
) -> dict[str, Any]:
    release_id = manifest["release_id"]
    final = remote_root / release_id
    incoming = remote_root / f".incoming-{release_id}-{os.getpid()}"
    quoted_root = shlex.quote(str(remote_root))
    quoted_final = shlex.quote(str(final))
    quoted_incoming = shlex.quote(str(incoming))

    prepare = (
        f"set -eu; test -d {quoted_root}; test ! -e {quoted_final}; "
        f"test ! -e {quoted_incoming}; mkdir -m 755 {quoted_incoming}"
    )
    remote_command(server, prepare)
    try:
        ssh_transport = "ssh " + " ".join(shlex.quote(item) for item in SSH_OPTIONS)
        run(
            [
                "rsync",
                "--archive",
                "--checksum",
                "-e",
                ssh_transport,
                f"{release}/",
                f"{server}:{incoming}/",
            ]
        )
        digest_command = (
            f"test -f {quoted_incoming}/release-manifest.json && "
            f"test -f {quoted_incoming}/frontend/out/index.html && "
            f"python3 -c {shlex.quote(REMOTE_TREE_DIGEST)} {quoted_incoming}"
        )
        remote_digest = remote_command(server, digest_command)
        if remote_digest != expected_tree_digest:
            raise RuntimeError(
                f"远端全树 SHA-256 不一致：expected={expected_tree_digest} actual={remote_digest}"
            )
        activate = f"set -eu; test ! -e {quoted_final}; mv {quoted_incoming} {quoted_final}"
        remote_command(server, activate)
    except Exception:
        cleanup = f"test ! -e {quoted_final} && rm -rf -- {quoted_incoming} || true"
        remote_command(server, cleanup, check=False)
        raise

    return {
        "server": server,
        "remote_release": str(final),
        "release_id": release_id,
        "git_commit": manifest["git_commit"],
        "frontend_sha256": manifest["frontend_sha256"],
        "tree_sha256": expected_tree_digest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release", type=Path)
    parser.add_argument("--server", default=DEFAULT_SERVER)
    parser.add_argument("--remote-root", type=PurePosixPath, default=DEFAULT_REMOTE_ROOT)
    parser.add_argument("--execute", action="store_true", help="执行远端上传；省略时只演练。")
    args = parser.parse_args()

    try:
        manifest, digest = validate_release(args.release)
        final = args.remote_root / manifest["release_id"]
        if not args.execute:
            result = {
                "mode": "dry-run",
                "server": args.server,
                "local_release": str(args.release.resolve()),
                "remote_release": str(final),
                "release_id": manifest["release_id"],
                "git_commit": manifest["git_commit"],
                "frontend_sha256": manifest["frontend_sha256"],
                "tree_sha256": digest,
                "remote_writes": False,
            }
        else:
            result = upload(
                args.release.resolve(),
                manifest,
                digest,
                server=args.server,
                remote_root=args.remote_root,
            )
            result["mode"] = "executed"
            result["remote_writes"] = True
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"代码 release 上传失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
