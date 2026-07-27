#!/usr/bin/env python3
"""以只读方式检查 DB 仓库发布前置条件。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from typing import Any, Callable


DEFAULT_SERVER = "root@10.99.8.28"
SSH_OPTIONS = (
    "-F",
    "/dev/null",
    "-o",
    "ProxyCommand=none",
    "-o",
    "ProxyJump=none",
)


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git(repo: Path, *arguments: str) -> str:
    completed = run(["git", *arguments], cwd=repo)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"git {' '.join(arguments)} 失败：{detail}")
    return completed.stdout.strip()


def inspect_local(repo: Path, phase: str) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    try:
        repository_root = Path(git(repo, "rev-parse", "--show-toplevel")).resolve()
        branch = git(repository_root, "branch", "--show-current")
        head = git(repository_root, "rev-parse", "HEAD")
        status = git(repository_root, "status", "--porcelain", "--untracked-files=normal")
        origin_url = git(repository_root, "remote", "get-url", "origin")
        origin_main = git(repository_root, "rev-parse", "origin/main")
        ahead_text, behind_text = git(
            repository_root, "rev-list", "--left-right", "--count", "HEAD...origin/main"
        ).split()
    except (RuntimeError, ValueError) as exc:
        return {"repository": str(repo.resolve())}, [str(exc)]

    local = {
        "repository": str(repository_root),
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "origin_url": origin_url,
        "ahead_of_origin_main": int(ahead_text),
        "behind_origin_main": int(behind_text),
        "worktree_clean": not status,
        "github_cli_authenticated": False,
    }

    if phase in {"publish", "deploy"} and status:
        errors.append("工作树不干净；先提交当前作用域修改，并保留无关修改。")

    if phase == "publish":
        if branch == "main" or not branch.startswith("codex/"):
            errors.append("推送阶段必须位于 codex/** 功能分支，禁止直接推送 main。")
    elif phase == "deploy":
        if branch != "main":
            errors.append("构建生产 release 前必须切回 main。")
        if head != origin_main:
            errors.append("本地 HEAD 与 origin/main 不一致；只能使用 --ff-only 同步后再部署。")

    if shutil.which("gh"):
        auth = run(["gh", "auth", "status", "--hostname", "github.com"], cwd=repository_root)
        local["github_cli_authenticated"] = auth.returncode == 0
    if phase in {"publish", "deploy"} and not local["github_cli_authenticated"]:
        errors.append("GitHub CLI 未通过 github.com 认证。")

    return local, errors


REMOTE_INSPECTION = r"""
set -u
current_code="$(readlink -f /home/wbt/DB/current 2>/dev/null || true)"
current_artifact="$(readlink -f /home/wbt/DB/current-artifact 2>/dev/null || true)"
runtime_env="missing"
if test -r /etc/bgpkb/runtime.env; then runtime_env="readable"; fi
chat_db=""
if test -r /etc/bgpkb/runtime.env; then
  chat_db="$(awk -F= '$1 == "BGP_CHAT_DB_PATH" {print substr($0, index($0, "=") + 1); exit}' /etc/bgpkb/runtime.env)"
fi
screen_count="$(screen -ls 2>/dev/null | grep -cE 'bgpkb_(frontend|fastapi)_wbt' || true)"
port_count="$(ss -ltn 2>/dev/null | grep -cE ':(39280|39281|8011|8012)[[:space:]]' || true)"
rollback="failed"
if test -n "$current_code" && python3 "$current_code/scripts/deployment.py" check-rollback /home/wbt/DB >/dev/null 2>&1; then
  rollback="ok"
fi
fastapi_health="$(curl -fsS --connect-timeout 2 --max-time 5 http://127.0.0.1:39281/health 2>/dev/null || true)"
frontend_health="$(curl -fsS --connect-timeout 2 --max-time 5 http://127.0.0.1:39280/health 2>/dev/null || true)"
disk_code="$(df -Pk /home/wbt 2>/dev/null | awk 'NR == 2 {print $5}')"
disk_artifact="$(df -Pk /srv/bgpkb 2>/dev/null | awk 'NR == 2 {print $5}')"
printf 'current_code\t%s\n' "$current_code"
printf 'current_artifact\t%s\n' "$current_artifact"
printf 'runtime_env\t%s\n' "$runtime_env"
printf 'chat_db\t%s\n' "$chat_db"
printf 'screen_count\t%s\n' "$screen_count"
printf 'port_count\t%s\n' "$port_count"
printf 'rollback\t%s\n' "$rollback"
printf 'fastapi_health\t%s\n' "$fastapi_health"
printf 'frontend_health\t%s\n' "$frontend_health"
printf 'disk_code\t%s\n' "$disk_code"
printf 'disk_artifact\t%s\n' "$disk_artifact"
"""


def _chat_database_tool() -> Path:
    return Path(__file__).resolve().parents[4] / "scripts" / "chat-database-maintenance"


def inspect_remote_chat_database(server: str, database_path: str) -> dict[str, Any]:
    tool = _chat_database_tool()
    if not tool.is_file():
        return {"ok": False, "error": "local_chat_database_tool_missing"}
    remote_command = (
        "python3 - inspect --database " + shlex.quote(database_path)
    )
    completed = run(
        ["ssh", *SSH_OPTIONS, server, remote_command],
        input_text=tool.read_text(encoding="utf-8"),
    )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": "remote_chat_database_inspection_invalid_json"}
    if not isinstance(result, dict):
        return {"ok": False, "error": "remote_chat_database_inspection_invalid_payload"}
    if completed.returncode != 0:
        result["ok"] = False
    return result


def _chat_summary(chat: dict[str, Any]) -> dict[str, Any]:
    return {
        "database_path": chat.get("database_path"),
        "database_exists": chat.get("database_exists"),
        "writable": chat.get("writable"),
        "integrity_check": chat.get("integrity_check"),
        "schema_version": chat.get("schema_version"),
        "schema_compatible": chat.get("schema_compatible"),
        "required_tables_present": chat.get("required_tables_present"),
    }


def _chat_is_healthy(chat: dict[str, Any]) -> bool:
    schema_version = chat.get("schema_version")
    schema_compatible = chat.get("schema_compatible", schema_version == 1)
    required_tables_present = chat.get("required_tables_present", True)
    return bool(
        chat.get("writable") is True
        and chat.get("integrity_check") == "ok"
        and schema_version == 1
        and schema_compatible is True
        and required_tables_present is True
    )


def validate_remote_health(
    remote: dict[str, Any],
    database_inspector: Callable[[str], dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    health_payloads: dict[str, dict[str, Any]] = {}

    for key in ("fastapi_health", "frontend_health"):
        raw_health = remote.get(key, "")
        try:
            health = json.loads(raw_health)
        except (TypeError, json.JSONDecodeError):
            errors.append(f"{key} 未返回有效 JSON。")
            continue
        if not isinstance(health, dict):
            errors.append(f"{key} 未返回 JSON 对象。")
            continue
        health_payloads[key] = health
        if health.get("degraded") is not False or health.get("integrity_check") != "ok":
            errors.append(f"{key} 显示知识库降级或完整性异常。")

    if remote.get("chat_db"):
        remote["chat_history_source"] = "direct_sqlite_inspect"
        chat = database_inspector(str(remote["chat_db"]))
        remote["chat_history_summary"] = _chat_summary(chat)
        if chat.get("ok") is not True or not _chat_is_healthy(chat):
            errors.append("会话库直接 SQLite 检查失败。")
    else:
        errors.append("未找到会话数据库路径，不能执行直接 SQLite 检查。")

    for key, health in health_payloads.items():
        remote[f"{key}_summary"] = {
            "release_id": health.get("release_id"),
            "degraded": health.get("degraded"),
            "integrity_check": health.get("integrity_check"),
        }
        remote.pop(key, None)

    return errors


def inspect_remote(server: str) -> tuple[dict[str, Any], list[str]]:
    completed = run(["ssh", *SSH_OPTIONS, server, REMOTE_INSPECTION])
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        return {"server": server}, [f"生产只读预检失败：{detail}"]

    remote: dict[str, Any] = {"server": server}
    for line in completed.stdout.splitlines():
        if "\t" in line:
            key, value = line.split("\t", 1)
            remote[key] = value

    errors: list[str] = []
    if not remote.get("current_code"):
        errors.append("服务器 current 代码指针缺失。")
    if not remote.get("current_artifact"):
        errors.append("服务器 current-artifact 指针缺失。")
    if remote.get("runtime_env") != "readable":
        errors.append("服务器外置运行环境文件缺失或不可读。")
    if not remote.get("chat_db"):
        errors.append("未找到 BGP_CHAT_DB_PATH；不会输出环境文件内容。")
    if int(remote.get("screen_count") or 0) < 2:
        errors.append("前端或 FastAPI screen 会话不完整。")
    if int(remote.get("port_count") or 0) < 4:
        errors.append("39280/39281/8011/8012 监听不完整。")
    if remote.get("rollback") != "ok":
        errors.append("previous 代码/制品回滚点无效。")

    errors.extend(
        validate_remote_health(
            remote,
            lambda database_path: inspect_remote_chat_database(server, database_path),
        )
    )

    return remote, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("inspect", "publish", "deploy"), default="inspect")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--server", default=DEFAULT_SERVER)
    parser.add_argument(
        "--remote",
        action="store_true",
        help="inspect 阶段也连接服务器做只读检查；deploy 阶段始终检查服务器。",
    )
    args = parser.parse_args()

    local, errors = inspect_local(args.repo.resolve(), args.phase)
    result: dict[str, Any] = {"phase": args.phase, "local": local}
    if args.phase == "deploy" or args.remote:
        remote, remote_errors = inspect_remote(args.server)
        result["remote"] = remote
        errors.extend(remote_errors)

    result["ok"] = not errors
    result["errors"] = errors
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
