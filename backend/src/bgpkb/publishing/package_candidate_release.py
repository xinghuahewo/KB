"""把已验证候选原子封装为不可变 artifact release。"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import tempfile
import uuid

from bgpkb.publishing.publish_index_closure import verify_publish_index_manifest


class CandidateReleasePackagingError(RuntimeError):
    """候选身份、门禁或封装闭包不满足发布要求。"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _load_json(path: Path, label: str) -> dict:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CandidateReleasePackagingError(f"{label} 不可读：{exc}") from exc
    if not isinstance(payload, dict):
        raise CandidateReleasePackagingError(f"{label} 必须是 JSON 对象")
    return payload


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path, *, prefixed: bool = False) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    value = digest.hexdigest()
    return f"sha256:{value}" if prefixed else value


def _validated_code_release(path: Path) -> tuple[Path, dict]:
    path = Path(path).expanduser().resolve()
    manifest = _load_json(path / "release-manifest.json", "代码 release manifest")
    commit = str(manifest.get("git_commit", ""))
    frontend_hash = str(manifest.get("frontend_sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise CandidateReleasePackagingError("代码 release 缺少完整 Git commit")
    if not re.fullmatch(r"[0-9a-f]{64}", frontend_hash):
        raise CandidateReleasePackagingError("代码 release 缺少前端构建 SHA-256")
    return path, manifest


def _write_checksums(release_root: Path) -> tuple[int, str]:
    data_dir = release_root / "data"
    files = sorted(path for path in data_dir.rglob("*") if path.is_file())
    if not files:
        raise CandidateReleasePackagingError("候选 data/ 不能为空")
    lines = [
        f"{_sha256(path)}  {path.relative_to(release_root).as_posix()}"
        for path in files
    ]
    checksum_path = release_root / "SHA256SUMS"
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(files), _sha256(checksum_path)


def _verify_checksums(release_root: Path) -> None:
    lines = (release_root / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    registered: dict[str, str] = {}
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  (data/.+)", line)
        if match is None or match.group(2) in registered:
            raise CandidateReleasePackagingError("SHA256SUMS 格式或路径闭包非法")
        registered[match.group(2)] = match.group(1)
    actual = {
        path.relative_to(release_root).as_posix()
        for path in (release_root / "data").rglob("*")
        if path.is_file()
    }
    if set(registered) != actual:
        raise CandidateReleasePackagingError("SHA256SUMS 文件集合不闭合")
    for relative, expected in registered.items():
        if _sha256(release_root / relative) != expected:
            raise CandidateReleasePackagingError(f"SHA-256 不匹配：{relative}")


def _compatibility_report(
    *, release_id: str, code_manifest: dict, publish_manifest: dict,
    verification_report: dict,
) -> dict:
    return {
        "schema_version": "candidate_compatibility_report_v1",
        "release_id": release_id,
        "status": "passed",
        "generated_at": _utc_now(),
        "api_contract": "向后兼容扩展",
        "serving_boundary": "serving.sqlite 仅含在线读取数据，治理数据位于 governance.sqlite",
        "legacy_reader": "仅保留受控只读兼容入口，不进入新生产链路",
        "code": {
            "release_id": code_manifest.get("release_id"),
            "git_commit": code_manifest["git_commit"],
            "frontend_sha256": code_manifest["frontend_sha256"],
        },
        "artifact": {
            "publish_index_schema": publish_manifest.get("schema_version"),
            "artifact_count": publish_manifest.get("artifact_count"),
            "identity_closure": publish_manifest.get("identity_closure", {}),
        },
        "verification": {
            "schema_version": verification_report.get("schema_version"),
            "status": verification_report.get("status"),
            "gate_count": len(verification_report.get("gates", [])),
        },
    }


def _migration_summary(published: Path, release_id: str) -> dict:
    chunk_path = published / "chunk_id_migration_report_v1.json"
    governance_path = published / "evidence_governance_migration_diff_v1.json"
    chunk = _load_json(chunk_path, "chunk migration 报告")
    governance = _load_json(governance_path, "治理迁移报告")
    if chunk.get("status") not in {"passed", "complete"}:
        raise CandidateReleasePackagingError("chunk migration 未通过")
    governance_status = governance.get("status")
    governance_complete = governance_status in {"passed", "complete"} or (
        governance_status is None
        and governance.get("schema_version")
        == "evidence_governance_migration_diff_v1"
        and governance.get("blockers") == []
        and isinstance(governance.get("statistics"), dict)
        and isinstance(governance["statistics"].get("record_count"), int)
    )
    if not governance_complete:
        raise CandidateReleasePackagingError("治理迁移未完成")
    return {
        "schema_version": "candidate_migration_summary_v1",
        "release_id": release_id,
        "status": "passed",
        "generated_at": _utc_now(),
        "chunk_migration": chunk,
        "governance_migration": governance,
        "source_reports": {
            "chunk": {
                "path": "published/chunk_id_migration_report_v1.json",
                "sha256": _sha256(chunk_path, prefixed=True),
            },
            "governance": {
                "path": "published/evidence_governance_migration_diff_v1.json",
                "sha256": _sha256(governance_path, prefixed=True),
            },
        },
    }


def _rollback_plan(
    *, release_id: str, code_release: Path, artifact_release: Path,
    previous_code_release: Path, previous_artifact_release: Path,
    deploy_root: Path,
) -> dict:
    deploy_script = code_release / "scripts" / "deployment.py"
    deploy_command = " ".join(
        shlex.quote(str(value))
        for value in (
            "python3", deploy_script, "activate", deploy_root,
            code_release, artifact_release,
        )
    )
    rollback_command = " ".join(
        shlex.quote(str(value))
        for value in (
            "python3", deploy_script, "rollback", deploy_root,
        )
    )
    return {
        "schema_version": "paired_rollback_plan_v1",
        "release_id": release_id,
        "generated_at": _utc_now(),
        "automatic_switch": False,
        "candidate_pair": {
            "code_release": str(code_release),
            "artifact_release": str(artifact_release),
        },
        "previous_pair": {
            "code_release": str(previous_code_release),
            "artifact_release": str(previous_artifact_release),
        },
        "commands": {
            "activate_after_human_approval": deploy_command,
            "rollback": rollback_command,
        },
        "instructions": "仅在人工批准并通过 canary 后执行成对切换；回滚不得重建历史 release。",
    }


def package_candidate_release(
    *, candidate_dir: Path, output_root: Path, code_release_dir: Path,
    previous_code_release: Path, previous_artifact_release: Path,
    deploy_root: Path,
) -> dict:
    """把 verified 候选复制到同文件系统临时目录，校验后原子公开。"""

    candidate = Path(candidate_dir).expanduser().resolve()
    output_root = Path(output_root).expanduser().resolve()
    code_release, code_manifest = _validated_code_release(code_release_dir)
    previous_code = Path(previous_code_release).expanduser().resolve()
    previous_artifact = Path(previous_artifact_release).expanduser().resolve()
    deploy_root = Path(deploy_root).expanduser()
    state = _load_json(candidate / ".pipeline" / "candidate.json", "候选状态")
    if state.get("status") != "verified" or state.get("reader_selectable") is not True:
        raise CandidateReleasePackagingError("候选必须处于 verified 且 reader_selectable 状态")

    source_data = candidate / "data"
    publish_path = source_data / "published" / "publish_index_manifest_v1.json"
    publish_manifest = _load_json(publish_path, "publish-index manifest")
    release_id = str(publish_manifest.get("release_id", ""))
    if (
        publish_manifest.get("status") != "complete"
        or not release_id
        or release_id != candidate.name
    ):
        raise CandidateReleasePackagingError("publish-index release 身份或状态非法")
    destination = output_root / release_id
    if destination.exists() or destination.is_symlink():
        raise CandidateReleasePackagingError(f"artifact release 已存在且不可覆盖：{destination}")
    if output_root == candidate or output_root.is_relative_to(candidate):
        raise CandidateReleasePackagingError("artifact release 输出不得位于候选目录内部")
    if not previous_code.is_dir() or not previous_artifact.is_dir():
        raise CandidateReleasePackagingError("上一代码/制品对不存在，无法生成回滚计划")

    verification_path = source_data / "published" / "release_verification_report_v1.json"
    verification = _load_json(verification_path, "verify-release 报告")
    if (
        verification.get("status") != "passed"
        or verification.get("exit_code") != 0
        or verification.get("candidate", {}).get("release_id") != release_id
    ):
        raise CandidateReleasePackagingError("verify-release 未通过或未绑定当前候选")
    try:
        verify_publish_index_manifest(source_data, publish_path)
    except Exception as exc:
        raise CandidateReleasePackagingError(f"publish-index 闭包失败：{exc}") from exc

    output_root.mkdir(parents=True, exist_ok=True)
    temporary = output_root / f".{release_id}.next-{uuid.uuid4().hex}"
    try:
        shutil.copytree(source_data, temporary / "data")
        copied_published = temporary / "data" / "published"
        _write_json(
            copied_published / "compatibility_report_v1.json",
            _compatibility_report(
                release_id=release_id,
                code_manifest=code_manifest,
                publish_manifest=publish_manifest,
                verification_report=verification,
            ),
        )
        _write_json(
            copied_published / "migration_summary_v1.json",
            _migration_summary(copied_published, release_id),
        )
        _write_json(
            copied_published / "paired_rollback_plan_v1.json",
            _rollback_plan(
                release_id=release_id,
                code_release=code_release,
                artifact_release=destination,
                previous_code_release=previous_code,
                previous_artifact_release=previous_artifact,
                deploy_root=deploy_root,
            ),
        )
        copied_publish_path = copied_published / "publish_index_manifest_v1.json"
        verify_publish_index_manifest(temporary / "data", copied_publish_path)
        file_count, checksum_hash = _write_checksums(temporary)
        _verify_checksums(temporary)
        package_manifest = {
            "schema_version": "candidate_release_package_v1",
            "release_id": release_id,
            "generated_at": _utc_now(),
            "code_release_id": code_manifest.get("release_id"),
            "code_commit": code_manifest["git_commit"],
            "frontend_sha256": code_manifest["frontend_sha256"],
            "artifact_file_count": file_count,
            "sha256sums_sha256": checksum_hash,
            "publish_index_manifest_sha256": _sha256(
                copied_publish_path, prefixed=True
            ),
            "automatic_switch": False,
        }
        _write_json(temporary / "release-package-manifest.json", package_manifest)
        os.replace(temporary, destination)
        try:
            directory_fd = os.open(output_root, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            pass
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    return {
        "release_id": release_id,
        "release_root": str(destination.resolve()),
        "code_commit": code_manifest["git_commit"],
        "file_count": file_count,
        "sha256sums_sha256": checksum_hash,
        "automatic_switch": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="封装已验证的候选 artifact release")
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--code-release-dir", type=Path, required=True)
    parser.add_argument("--previous-code-release", type=Path, required=True)
    parser.add_argument("--previous-artifact-release", type=Path, required=True)
    parser.add_argument("--deploy-root", type=Path, default=Path("/home/wbt/DB"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = package_candidate_release(
            candidate_dir=args.candidate_dir,
            output_root=args.output_root,
            code_release_dir=args.code_release_dir,
            previous_code_release=args.previous_code_release,
            previous_artifact_release=args.previous_artifact_release,
            deploy_root=args.deploy_root,
        )
    except CandidateReleasePackagingError as exc:
        print(str(exc))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
