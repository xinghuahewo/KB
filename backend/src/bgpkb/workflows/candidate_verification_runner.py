"""以单一稳定入口启动候选 canary 并执行完整 verify-release。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from typing import Mapping
import urllib.error
import urllib.request
import uuid

from bgpkb import paths
from bgpkb.infrastructure.serving_bundle import CODE_RELEASE_MANIFEST_PATH
from bgpkb.workflows.candidate_verification_canary import (
    cleanup_chat_database,
    validate_candidate,
)


class CandidateVerificationRunnerError(RuntimeError):
    """稳定候选评测入口的身份、readiness 或清理约束不成立。"""


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_runner_binding(binding: Mapping[str, object]) -> dict:
    normalized = dict(binding)
    revisions = normalized.get("model_revisions")
    if (
        not re.fullmatch(r"[0-9a-f]{40}", str(normalized.get("code_commit", "")))
        or not str(normalized.get("prompt_version", "")).strip()
        or not str(normalized.get("llm_model", "")).strip()
        or not isinstance(revisions, Mapping)
        or any(
            not str(revisions.get(role, "")).strip()
            for role in ("embedding", "reranker", "llm")
        )
    ):
        raise CandidateVerificationRunnerError(
            "code commit、prompt、embedding、reranker、LLM revisions 必须完整"
        )
    if not re.fullmatch(
        r"run-[0-9a-f]{32}",
        str(normalized.get("pipeline_run_id", "")),
    ):
        raise CandidateVerificationRunnerError("pipeline run id 非法")
    for key in ("publish_manifest_hash", "publish_checkpoint_hash"):
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(normalized.get(key, ""))):
            raise CandidateVerificationRunnerError(f"{key} 非法")
    candidate_root = Path(str(normalized.get("candidate_root", ""))).resolve()
    if (
        not candidate_root.name
        or normalized.get("release_id") != candidate_root.name
    ):
        raise CandidateVerificationRunnerError("候选路径与 release id 不一致")
    return normalized


def build_verification_environment(binding: Mapping[str, object]) -> dict[str, str]:
    validated = validate_runner_binding(binding)
    revisions = validated["model_revisions"]
    return {
        "BGPKB_CODE_COMMIT": str(validated["code_commit"]),
        "BGPKB_PIPELINE_RUN_ID": str(validated["pipeline_run_id"]),
        "BGP_RAG_REQUIRE_RERANKER": "1",
        "BGP_GROUNDED_PROMPT_VERSION": str(validated["prompt_version"]),
        "BGP_LLM_MODEL": str(validated["llm_model"]),
        "BGP_EMBEDDING_MODEL_REVISION": str(revisions["embedding"]),
        "BGP_RERANKER_MODEL_REVISION": str(revisions["reranker"]),
        "BGP_LLM_MODEL_REVISION": str(revisions["llm"]),
        "DEEPSEEK_MODEL": str(validated["llm_model"]),
        "DEEPSEEK_MODEL_REVISION": str(revisions["llm"]),
    }


def validate_canary_health(
    health: Mapping[str, object],
    binding: Mapping[str, object],
) -> None:
    validated = validate_runner_binding(binding)
    readiness = health.get("retrieval_runtime")
    if (
        health.get("release_id") != validated["release_id"]
        or health.get("degraded") is not False
        or not isinstance(readiness, Mapping)
        or readiness.get("ready") is not True
        or readiness.get("status") != "ready"
        or readiness.get("index_mode") != "fast_numpy"
    ):
        raise CandidateVerificationRunnerError(
            "canary health 未达到候选 fast_numpy readiness"
        )
    if health.get("verification_binding") != validated:
        raise CandidateVerificationRunnerError(
            "canary health verification binding 与本轮候选不一致"
        )


def _read_health(url: str, timeout_seconds: float) -> dict:
    with urllib.request.urlopen(
        url.rstrip("/") + "/health",
        timeout=timeout_seconds,
    ) as response:
        if response.status != 200:
            raise CandidateVerificationRunnerError(
                f"canary health 返回 HTTP {response.status}"
            )
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise CandidateVerificationRunnerError("canary health 必须是 JSON object")
    return payload


def wait_for_canary(
    *,
    target_url: str,
    binding: Mapping[str, object],
    process: subprocess.Popen,
    timeout_seconds: float,
) -> dict:
    deadline = time.monotonic() + timeout_seconds
    last_error = ""
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise CandidateVerificationRunnerError(
                f"canary 在 ready 前退出：returncode={process.returncode}"
            )
        try:
            health = _read_health(target_url, min(2.0, timeout_seconds))
            validate_canary_health(health, binding)
            return health
        except (
            OSError,
            ValueError,
            json.JSONDecodeError,
            urllib.error.URLError,
            CandidateVerificationRunnerError,
        ) as exc:
            last_error = str(exc)
            time.sleep(0.2)
    raise CandidateVerificationRunnerError(
        f"canary readiness 超时：{last_error or 'unavailable'}"
    )


def _stop_canary(process: subprocess.Popen, timeout_seconds: float = 15.0) -> None:
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        raise CandidateVerificationRunnerError(
            "canary 未在 SIGINT 后按期清理退出"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="启动隔离 canary、校验 readiness 并运行完整 verify-release"
    )
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--frozen-release-root", type=Path, required=True)
    parser.add_argument(
        "--prompt-version",
        default="grounded_answer_prompt_v1",
    )
    parser.add_argument("--embedding-revision", required=True)
    parser.add_argument("--reranker-revision", required=True)
    parser.add_argument("--llm-model", default="deepseek-v4-pro")
    parser.add_argument("--llm-revision", required=True)
    parser.add_argument("--pipeline-run-id")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=39282)
    parser.add_argument("--max-runtime-seconds", type=int, default=1800)
    parser.add_argument("--readiness-timeout-seconds", type=float, default=60)
    parser.add_argument(
        "--config",
        type=Path,
        default=paths.PROJECT_ROOT / "metadata/config/converged_pipeline_v2.yaml",
    )
    return parser


def _build_binding(args: argparse.Namespace) -> dict:
    candidate = args.candidate_dir.expanduser().resolve()
    publish_path = (
        candidate / "data/published/publish_index_manifest_v1.json"
    )
    checkpoint_path = candidate / ".pipeline/checkpoints/publish-index.json"
    try:
        code_manifest = json.loads(
            CODE_RELEASE_MANIFEST_PATH.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateVerificationRunnerError(
            f"代码 release manifest 不可读：{exc}"
        ) from exc
    run_id = args.pipeline_run_id or f"run-{uuid.uuid4().hex}"
    binding = {
        "candidate_root": str(candidate),
        "release_id": candidate.name,
        "publish_manifest_hash": _sha256(publish_path),
        "publish_checkpoint_hash": _sha256(checkpoint_path),
        "pipeline_run_id": run_id,
        "code_commit": str(code_manifest.get("git_commit", "")),
        "prompt_version": args.prompt_version,
        "llm_model": args.llm_model,
        "model_revisions": {
            "embedding": args.embedding_revision,
            "reranker": args.reranker_revision,
            "llm": args.llm_revision,
        },
        "chat_db_path": str(
            candidate
            / ".pipeline/tmp/canary-chat"
            / run_id
            / "verification.sqlite3"
        ),
    }
    return validate_runner_binding(binding)


def run(args: argparse.Namespace) -> int:
    binding = _build_binding(args)
    candidate = Path(binding["candidate_root"])
    revisions = binding["model_revisions"]
    validate_candidate(
        candidate,
        release_id=str(binding["release_id"]),
        publish_manifest_hash=str(binding["publish_manifest_hash"]),
        publish_checkpoint_hash=str(binding["publish_checkpoint_hash"]),
        code_commit=str(binding["code_commit"]),
        prompt_version=str(binding["prompt_version"]),
        model_revisions=revisions,
    )
    target_url = f"http://{args.host}:{args.port}"
    canary_command = [
        sys.executable,
        "-m",
        "bgpkb.workflows.candidate_verification_canary",
        "--candidate-dir",
        str(candidate),
        "--release-id",
        str(binding["release_id"]),
        "--publish-manifest-hash",
        str(binding["publish_manifest_hash"]),
        "--publish-checkpoint-hash",
        str(binding["publish_checkpoint_hash"]),
        "--pipeline-run-id",
        str(binding["pipeline_run_id"]),
        "--code-commit",
        str(binding["code_commit"]),
        "--prompt-version",
        str(binding["prompt_version"]),
        "--embedding-revision",
        str(revisions["embedding"]),
        "--reranker-revision",
        str(revisions["reranker"]),
        "--llm-model",
        str(binding["llm_model"]),
        "--llm-revision",
        str(revisions["llm"]),
        "--chat-db-path",
        str(binding["chat_db_path"]),
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--max-runtime-seconds",
        str(args.max_runtime_seconds),
    ]
    environment = {
        **os.environ,
        **build_verification_environment(binding),
        "BGPKB_VERIFY_TARGET_URL": target_url,
    }
    canary = subprocess.Popen(canary_command, env=environment)
    pipeline_result: subprocess.CompletedProcess | None = None
    cleanup_error: Exception | None = None
    try:
        wait_for_canary(
            target_url=target_url,
            binding=binding,
            process=canary,
            timeout_seconds=args.readiness_timeout_seconds,
        )
        frozen = args.frozen_release_root.expanduser().resolve() / "data"
        pipeline_command = [
            sys.executable,
            "-m",
            "bgpkb.workflows.converged_pipeline",
            "verify-release",
            "--candidate-dir",
            str(candidate),
            "--config",
            str(args.config.expanduser().resolve()),
            "--frozen-source-root",
            str(frozen / "sources/raw"),
            "--frozen-canonical-root",
            str(frozen / "corpus/parsed_v2"),
            "--frozen-assets-root",
            str(frozen / "corpus/assets_v2"),
            "--frozen-legacy-chunks-root",
            str(frozen / "corpus/chunks_v2"),
            "--frozen-source-catalog-path",
            str(frozen / "published/source_catalog.jsonl"),
            "--frozen-entity-evidence-path",
            str(frozen / "derived/datasets/entity_source_evidence.jsonl"),
            "--docling-execution-mode",
            "remote",
        ]
        pipeline_result = subprocess.run(
            pipeline_command,
            env=environment,
            check=False,
        )
    finally:
        try:
            _stop_canary(canary)
            cleanup_chat_database(
                candidate,
                Path(str(binding["chat_db_path"])),
                str(binding["pipeline_run_id"]),
            )
        except Exception as exc:
            cleanup_error = exc
    if cleanup_error is not None:
        raise CandidateVerificationRunnerError(str(cleanup_error))
    if pipeline_result is None:
        raise CandidateVerificationRunnerError(
            "verify-release 未启动"
        )
    return int(pipeline_result.returncode)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except CandidateVerificationRunnerError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
