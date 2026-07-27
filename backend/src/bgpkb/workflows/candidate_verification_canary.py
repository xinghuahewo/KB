"""在本机回环地址启动严格限定的候选真实评测服务。"""

from __future__ import annotations

import argparse
import atexit
from contextlib import contextmanager
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import threading
from typing import Iterator, Mapping

from bgpkb.infrastructure.serving_bundle import (
    CODE_RELEASE_MANIFEST_PATH,
    VERIFICATION_CANDIDATE_BINDING_ENV,
)


class CandidateVerificationCanaryError(RuntimeError):
    """候选真实评测服务启动条件不成立。"""


def is_loopback_host(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def validate_candidate(
    candidate_dir: Path,
    *,
    release_id: str,
    publish_manifest_hash: str,
    publish_checkpoint_hash: str,
    code_commit: str,
    prompt_version: str,
    model_revisions: Mapping[str, str],
    llm_model: str = "deepseek-v4-pro",
) -> tuple[Path, dict]:
    candidate_root = candidate_dir.expanduser().resolve()
    state_path = candidate_root / ".pipeline" / "candidate.json"
    stage_path = candidate_root / ".pipeline" / "manifests" / "publish-index.json"
    checkpoint_path = candidate_root / ".pipeline" / "checkpoints" / "publish-index.json"
    publish_path = candidate_root / "data" / "published" / "publish_index_manifest_v1.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        stage = json.loads(stage_path.read_text(encoding="utf-8"))
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        publish = json.loads(publish_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateVerificationCanaryError(f"候选验证证据不可读：{exc}") from exc
    if state.get("reader_selectable") is True:
        raise CandidateVerificationCanaryError("已验证候选不需要未验证候选评测入口")
    if state.get("status") not in {"candidate", "failed"}:
        raise CandidateVerificationCanaryError("候选状态不允许进入真实评测")
    if state.get("failed_stage") not in {None, "verify-release"}:
        raise CandidateVerificationCanaryError("候选必须已完成 publish-index 且只允许在 verify-release 恢复")
    if stage.get("stage") != "publish-index" or stage.get("status") != "complete":
        raise CandidateVerificationCanaryError("publish-index 阶段未完整通过")
    if (
        publish.get("status") != "complete"
        or publish.get("release_id") != candidate_root.name
        or release_id != candidate_root.name
    ):
        raise CandidateVerificationCanaryError("publish-index manifest 与候选身份不闭合")
    actual_manifest_hash = "sha256:" + hashlib.sha256(publish_path.read_bytes()).hexdigest()
    if publish_manifest_hash != actual_manifest_hash:
        raise CandidateVerificationCanaryError("publish-index manifest hash 与显式绑定不匹配")
    actual_checkpoint_hash = "sha256:" + hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
    if (
        checkpoint.get("stage") != "publish-index"
        or checkpoint.get("status") != "complete"
        or publish_checkpoint_hash != actual_checkpoint_hash
    ):
        raise CandidateVerificationCanaryError("publish-index checkpoint 与显式绑定不匹配")
    try:
        code_release_manifest = json.loads(
            CODE_RELEASE_MANIFEST_PATH.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateVerificationCanaryError(f"代码 release manifest 不可读：{exc}") from exc
    if (
        not re.fullmatch(r"[0-9a-f]{40}", code_commit)
        or code_release_manifest.get("git_commit") != code_commit
    ):
        raise CandidateVerificationCanaryError("代码提交与当前不可变代码 release 不匹配")
    if not prompt_version.strip() or not llm_model.strip():
        raise CandidateVerificationCanaryError("prompt version 与 LLM model 不得为空")
    if any(not str(model_revisions.get(role, "")).strip() for role in ("embedding", "reranker", "llm")):
        raise CandidateVerificationCanaryError("embedding、reranker、LLM revision 必须完整绑定")
    if publish.get("model_revisions", {}).get("embedding") != model_revisions["embedding"]:
        raise CandidateVerificationCanaryError("embedding revision 与候选 manifest 不匹配")
    return candidate_root, publish


def validate_chat_db_path(
    candidate_root: Path,
    chat_db_path: Path,
    pipeline_run_id: str,
) -> Path:
    isolated_root = (
        candidate_root / ".pipeline" / "tmp" / "canary-chat" / pipeline_run_id
    ).resolve()
    resolved = chat_db_path.expanduser().resolve()
    production_path = os.environ.get("BGP_CHAT_DB_PATH", "").strip()
    if production_path and resolved == Path(production_path).expanduser().resolve():
        raise CandidateVerificationCanaryError("候选评测不得读取或写入生产会话库")
    if resolved.parent != isolated_root or resolved.suffix != ".sqlite3":
        raise CandidateVerificationCanaryError("候选评测会话库必须位于候选 canary-chat 隔离目录")
    return resolved


@contextmanager
def verification_environment(
    *,
    binding: Mapping[str, object],
    chat_db_path: Path,
) -> Iterator[None]:
    model_revisions = binding["model_revisions"]
    updates = {
        "BGPKB_DATA_DIR": str(Path(str(binding["candidate_root"])) / "data"),
        "BGP_CHAT_DB_PATH": str(chat_db_path),
        VERIFICATION_CANDIDATE_BINDING_ENV: json.dumps(
            dict(binding), ensure_ascii=False, sort_keys=True
        ),
        "BGPKB_CODE_COMMIT": str(binding["code_commit"]),
        "BGPKB_PIPELINE_RUN_ID": str(binding["pipeline_run_id"]),
        "BGP_RAG_REQUIRE_RERANKER": "1",
        "BGP_GROUNDED_PROMPT_VERSION": str(binding["prompt_version"]),
        "BGP_LLM_MODEL": str(binding["llm_model"]),
        "BGP_EMBEDDING_MODEL_REVISION": str(model_revisions["embedding"]),
        "BGP_RERANKER_MODEL_REVISION": str(model_revisions["reranker"]),
        "BGP_LLM_MODEL_REVISION": str(model_revisions["llm"]),
        "DEEPSEEK_MODEL": str(binding["llm_model"]),
        "DEEPSEEK_MODEL_REVISION": str(model_revisions["llm"]),
    }
    previous = {name: os.environ.get(name) for name in updates}
    chat_db_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_root = Path(str(binding["candidate_root"]))
    cleanup_chat_database(candidate_root, chat_db_path, str(binding["pipeline_run_id"]))
    try:
        os.environ.update(updates)
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        cleanup_chat_database(candidate_root, chat_db_path, str(binding["pipeline_run_id"]))


def cleanup_chat_database(
    candidate_root: Path,
    chat_db_path: Path,
    pipeline_run_id: str,
) -> None:
    resolved_candidate = candidate_root.expanduser().resolve()
    resolved_chat_db = chat_db_path.expanduser().resolve()
    if not re.fullmatch(r"run-[0-9a-f]{32}", pipeline_run_id):
        raise CandidateVerificationCanaryError("拒绝使用无效 pipeline run id 清理")
    isolated_root = (
        resolved_candidate / ".pipeline" / "tmp" / "canary-chat" / pipeline_run_id
    ).resolve()
    if resolved_chat_db.parent != isolated_root or resolved_chat_db.suffix != ".sqlite3":
        raise CandidateVerificationCanaryError("拒绝清理候选 canary-chat 隔离目录之外的路径")
    for suffix in ("", "-wal", "-shm"):
        cleanup_path = Path(str(resolved_chat_db) + suffix)
        if cleanup_path.is_file():
            cleanup_path.unlink()


def run_server_with_timeout(server: object, max_runtime_seconds: int) -> None:
    timer = threading.Timer(
        max_runtime_seconds,
        lambda: setattr(server, "should_exit", True),
    )
    timer.daemon = True
    timer.start()
    try:
        server.run()
    finally:
        timer.cancel()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="启动仅绑定回环地址的候选真实评测服务")
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--publish-manifest-hash", required=True)
    parser.add_argument("--publish-checkpoint-hash", required=True)
    parser.add_argument("--pipeline-run-id", required=True)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--prompt-version", required=True)
    parser.add_argument("--embedding-revision", required=True)
    parser.add_argument("--reranker-revision", required=True)
    parser.add_argument("--llm-model", required=True)
    parser.add_argument("--llm-revision", required=True)
    parser.add_argument("--chat-db-path", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--max-runtime-seconds", type=int, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not is_loopback_host(args.host):
        raise SystemExit("候选真实评测服务只能绑定本机回环地址")
    if not 1 <= args.port <= 65535:
        raise SystemExit("端口必须位于 1..65535")
    if not 1 <= args.max_runtime_seconds <= 3600:
        raise SystemExit("最长运行时间必须位于 1..3600 秒")
    if not re.fullmatch(r"run-[0-9a-f]{32}", args.pipeline_run_id):
        raise SystemExit("pipeline run id 必须使用 run- 加 32 位小写十六进制")
    model_revisions = {
        "embedding": args.embedding_revision,
        "reranker": args.reranker_revision,
        "llm": args.llm_revision,
    }
    candidate_root, _ = validate_candidate(
        args.candidate_dir,
        release_id=args.release_id,
        publish_manifest_hash=args.publish_manifest_hash,
        publish_checkpoint_hash=args.publish_checkpoint_hash,
        code_commit=args.code_commit,
        prompt_version=args.prompt_version,
        model_revisions=model_revisions,
        llm_model=args.llm_model,
    )
    chat_db_path = validate_chat_db_path(
        candidate_root,
        args.chat_db_path,
        args.pipeline_run_id,
    )
    binding = {
        "candidate_root": str(candidate_root),
        "release_id": args.release_id,
        "publish_manifest_hash": args.publish_manifest_hash,
        "publish_checkpoint_hash": args.publish_checkpoint_hash,
        "pipeline_run_id": args.pipeline_run_id,
        "code_commit": args.code_commit,
        "prompt_version": args.prompt_version,
        "llm_model": args.llm_model,
        "model_revisions": model_revisions,
        "chat_db_path": str(chat_db_path),
    }

    import uvicorn

    server = uvicorn.Server(
        uvicorn.Config("bgpkb.api.app:app", host=args.host, port=args.port)
    )
    atexit.register(
        cleanup_chat_database,
        candidate_root,
        chat_db_path,
        args.pipeline_run_id,
    )
    try:
        with verification_environment(binding=binding, chat_db_path=chat_db_path):
            run_server_with_timeout(server, args.max_runtime_seconds)
    finally:
        atexit.unregister(cleanup_chat_database)
        cleanup_chat_database(candidate_root, chat_db_path, args.pipeline_run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
