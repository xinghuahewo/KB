"""在隔离候选中显式执行远端 Docling 并物化严格 Canonical。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
from typing import Callable, Literal

from bgpkb import paths
from bgpkb.ingestion.canonicalize_candidate import (
    _load_source_manifest,
    load_reprocess_policy,
)
from bgpkb.ingestion.cleaning_v2.contracts import atomic_write_json
from bgpkb.ingestion.docling_reprocess_materializer import (
    materialize_docling_reprocess,
)


class CandidateDoclingReprocessError(RuntimeError):
    """候选 Docling 远端执行或闭包不满足发布约束。"""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _safe_relative(value: str, *, field: str) -> Path:
    path = Path(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise CandidateDoclingReprocessError(f"{field} 路径越界：{value}")
    return path


def _within_candidate(candidate_dir: Path, value: Path, *, field: str) -> Path:
    candidate = Path(candidate_dir).resolve()
    resolved = Path(value).resolve()
    if resolved != candidate and not resolved.is_relative_to(candidate):
        raise CandidateDoclingReprocessError(f"{field} 路径越界：{resolved}")
    return resolved


def _runtime_identity(policy: dict) -> dict:
    route = policy["docling"]
    return {
        "pipeline_revision": route["pipeline_revision"],
        "parser_version": "2.107.0",
        "image": route["image"],
        "image_digest": route["image_digest"],
        "gpu_index": route["gpu_index"],
        "device": route["device"],
        "network": route["network"],
    }


def _read_plan(
    *,
    plan_path: Path,
    source_manifest_path: Path,
    source_store_root: Path,
    policy_path: Path,
    release_id: str,
    policy: dict,
) -> tuple[dict, dict[str, dict]]:
    try:
        plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CandidateDoclingReprocessError(f"Docling 重处理计划不可读：{exc}") from exc
    if (
        plan.get("schema_version") != "docling_reprocess_plan_v1"
        or plan.get("release_id") != release_id
        or plan.get("status") not in {"ready", "not_required"}
    ):
        raise CandidateDoclingReprocessError("Docling 重处理计划身份或状态非法")
    if plan.get("source_ingest_manifest_sha256") != _sha256(source_manifest_path):
        raise CandidateDoclingReprocessError("Docling 重处理计划 source hash 不匹配")
    policy_binding = plan.get("reprocess_policy")
    if (
        not isinstance(policy_binding, dict)
        or policy_binding.get("policy_version") != policy["policy_version"]
        or policy_binding.get("sha256") != _sha256(policy_path)
        or policy_binding.get("affected_source_ids")
        != list(policy["affected_source_ids"])
    ):
        raise CandidateDoclingReprocessError("Docling 重处理计划 policy hash 不匹配")
    rows = plan.get("sources")
    if not isinstance(rows, list):
        raise CandidateDoclingReprocessError("Docling 重处理计划 sources 非法")
    _source_manifest, snapshots = _load_source_manifest(
        source_manifest_path, Path(source_store_root).resolve()
    )
    affected = set(policy["affected_source_ids"])
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("source_id"), str):
            raise CandidateDoclingReprocessError("Docling 重处理计划来源记录非法")
        source_id = row["source_id"]
        if source_id in seen:
            raise CandidateDoclingReprocessError(f"Docling 重处理计划来源重复：{source_id}")
        seen.add(source_id)
        if source_id not in affected:
            raise CandidateDoclingReprocessError(f"Docling 重处理计划包含未授权来源：{source_id}")
        snapshot = snapshots.get(source_id)
        if snapshot is None or row.get("object_digest") != snapshot["object_digest"]:
            raise CandidateDoclingReprocessError(
                f"Docling 重处理计划 source hash 不匹配：{source_id}"
            )
        if (
            row.get("snapshot_id") != snapshot["snapshot_id"]
            or row.get("object_path") != snapshot["object_path"]
            or row.get("byte_size") != snapshot["byte_size"]
        ):
            raise CandidateDoclingReprocessError(
                f"Docling 重处理计划 snapshot 身份不闭合：{source_id}"
            )
    if plan.get("summary", {}).get("requested") != len(rows):
        raise CandidateDoclingReprocessError("Docling 重处理计划计数不一致")
    return plan, snapshots


def _validate_receipt(
    *,
    receipt: dict,
    plan: dict,
    snapshots: dict[str, dict],
    payload_root: Path,
    release_id: str,
    runtime_identity: dict,
) -> None:
    if (
        receipt.get("schema_version") != "docling_payload_manifest_v1"
        or receipt.get("release_id") != release_id
    ):
        raise CandidateDoclingReprocessError("Docling payload 回执身份非法")
    if receipt.get("runtime") != runtime_identity:
        raise CandidateDoclingReprocessError("Docling payload runtime 与锁定策略不一致")
    model_evidence = receipt.get("model_evidence")
    if (
        not isinstance(model_evidence, list)
        or len(model_evidence) != 5
        or any(
            not isinstance(row, dict)
            or not row.get("name")
            or not row.get("actual_sha256")
            or row.get("actual_sha256") != row.get("expected_sha256")
            for row in model_evidence
        )
    ):
        raise CandidateDoclingReprocessError("Docling payload 5 模型 revision 证据非法")
    rows = receipt.get("documents")
    if not isinstance(rows, list):
        raise CandidateDoclingReprocessError("Docling payload 回执 documents 非法")
    expected = [row["source_id"] for row in plan["sources"]]
    actual = [row.get("source_id") for row in rows if isinstance(row, dict)]
    if actual != expected:
        raise CandidateDoclingReprocessError("Docling payload 回执来源集合或顺序不一致")
    failed = [row for row in rows if row.get("status") != "complete"]
    if receipt.get("status") != "complete" or failed:
        failed_ids = [str(row.get("source_id")) for row in failed]
        raise CandidateDoclingReprocessError(
            "Docling payload 部分失败：" + ", ".join(failed_ids)
        )
    payload_root = Path(payload_root).resolve()
    for row in rows:
        source_id = row["source_id"]
        if row.get("source_sha256") != snapshots[source_id]["object_digest"]:
            raise CandidateDoclingReprocessError(
                f"Docling payload source hash 不匹配：{source_id}"
            )
        relative = _safe_relative(
            str(row.get("payload_path") or ""), field="Docling payload"
        )
        payload_path = (payload_root / relative).resolve()
        if payload_path != payload_root and not payload_path.is_relative_to(payload_root):
            raise CandidateDoclingReprocessError(
                f"Docling payload 路径越界：{source_id}"
            )
        if not payload_path.is_file():
            raise CandidateDoclingReprocessError(f"Docling payload 缺失：{source_id}")
        if row.get("payload_sha256") != _sha256(payload_path):
            raise CandidateDoclingReprocessError(
                f"Docling payload 输出 hash 不匹配：{source_id}"
            )
        if (
            row.get("parser_version") != runtime_identity["parser_version"]
            or row.get("pipeline_revision") != runtime_identity["pipeline_revision"]
        ):
            raise CandidateDoclingReprocessError(
                f"Docling payload parser revision 不匹配：{source_id}"
            )


def _resolve_local_addresses(target_host: str) -> set[str]:
    """解析本机地址；UDP 只选路由源地址，不发送任何数据。"""

    addresses = {"127.0.0.1", "::1"}
    for hostname in {socket.gethostname(), socket.getfqdn()}:
        try:
            addresses.update(
                row[4][0] for row in socket.getaddrinfo(hostname, None)
            )
        except OSError:
            continue
    try:
        target_rows = socket.getaddrinfo(target_host, 9, type=socket.SOCK_DGRAM)
    except OSError:
        target_rows = []
    for family, socktype, protocol, _canonname, sockaddr in target_rows:
        probe = socket.socket(family, socktype, protocol)
        try:
            probe.connect(sockaddr)
            addresses.add(str(probe.getsockname()[0]))
        except OSError:
            continue
        finally:
            probe.close()
    return addresses


class SSHDoclingRunner:
    """在目标本机直跑，否则通过固定无代理 SSH 执行锁定 Docling worker。"""

    def __init__(
        self,
        *,
        command_runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
        local_address_resolver: Callable[[str], set[str]] = _resolve_local_addresses,
        transport_override: Literal["local", "remote"] | None = None,
    ):
        self.command_runner = command_runner
        self.local_address_resolver = local_address_resolver
        self.transport_override = transport_override
        self._transport: Literal["local", "remote"] | None = None

    @staticmethod
    def _ssh_prefix(target: str) -> list[str]:
        return [
            "ssh",
            "-F",
            "/dev/null",
            "-o",
            "ProxyCommand=none",
            "-o",
            "ProxyJump=none",
            target,
        ]

    @staticmethod
    def _target_host(target: str) -> str:
        host = target.rsplit("@", 1)[-1].strip()
        if not host:
            raise CandidateDoclingReprocessError("Docling 目标主机为空")
        return host

    def _select_transport(self, target: str) -> Literal["local", "remote"]:
        host = self._target_host(target)
        try:
            target_addresses = {
                row[4][0] for row in socket.getaddrinfo(host, None)
            }
            local_addresses = set(self.local_address_resolver(host))
        except OSError as exc:
            raise CandidateDoclingReprocessError(
                f"Docling 执行面主机判定失败：{exc}"
            ) from exc
        is_local = bool(target_addresses & local_addresses)
        if self.transport_override == "local" and not is_local:
            raise CandidateDoclingReprocessError(
                "显式 local 执行面与本机地址不匹配，拒绝运行"
            )
        if self.transport_override is not None:
            return self.transport_override
        return "local" if is_local else "remote"

    def _run_target(
        self,
        target: str,
        command: list[str],
        *,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        if self._transport is None:
            self._transport = self._select_transport(target)
        routed_command = (
            command
            if self._transport == "local"
            else [*self._ssh_prefix(target), shlex.join(command)]
        )
        completed = self.command_runner(
            routed_command,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and completed.returncode:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise CandidateDoclingReprocessError(
                f"Docling {self._transport} 命令失败（{completed.returncode}）：{detail}"
            )
        return completed

    def _preflight(self, *, policy: dict) -> dict:
        route = policy["docling"]
        target = route["ssh_target"]
        self._transport = self._select_transport(target)
        gpu_rows = self._run_target(
            target,
            [
                "nvidia-smi",
                "--query-gpu=index,uuid,memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
        ).stdout.splitlines()
        selected = None
        for row in gpu_rows:
            values = [value.strip() for value in row.split(",")]
            if values and values[0] == str(route["gpu_index"]):
                selected = values
                break
        if selected is None:
            raise CandidateDoclingReprocessError("未找到锁定 GPU 1")
        app_result = self._run_target(
            target,
            [
                "nvidia-smi",
                "--query-compute-apps=gpu_uuid,pid,process_name,used_memory",
                "--format=csv,noheader,nounits",
            ],
            check=False,
        )
        active = [
            row
            for row in app_result.stdout.splitlines()
            if row.strip() and row.split(",", 1)[0].strip() == selected[1]
        ]
        if active:
            raise CandidateDoclingReprocessError("锁定 GPU 1 当前有计算任务")
        image_id = self._run_target(
            target,
            ["docker", "image", "inspect", "--format", "{{.Id}}", route["image"]],
        ).stdout.strip()
        if image_id != route["image_digest"]:
            raise CandidateDoclingReprocessError(
                f"Docling 镜像 digest 不匹配：{image_id}"
            )
        runtime_result = self._run_target(
            target,
            [
                "docker",
                "run",
                "--rm",
                "--device",
                route["device"],
                "--network",
                route["network"],
                "--env",
                f"BGPKB_IMAGE_DIGEST={route['image_digest']}",
                route["image"],
                "--expected-image-digest",
                route["image_digest"],
            ],
        )
        try:
            preflight = json.loads(runtime_result.stdout)
        except json.JSONDecodeError as exc:
            raise CandidateDoclingReprocessError(
                f"Docling 离线预检回执不可读：{exc}"
            ) from exc
        models = preflight.get("models")
        if (
            not preflight.get("ok")
            or not isinstance(models, list)
            or len(models) != 5
            or any(row.get("actual_sha256") != row.get("expected_sha256") for row in models)
            or not preflight.get("gpu", {}).get("cuda_available")
        ):
            raise CandidateDoclingReprocessError("Docling GPU/模型/offline 预检未通过")
        return {
            "execution_transport": self._transport,
            "target_host": self._target_host(target),
            "gpu": {
                "index": int(selected[0]),
                "uuid": selected[1],
                "memory_used_mib": int(selected[2]),
                "memory_total_mib": int(selected[3]),
                "utilization_percent": int(selected[4]),
                "active_compute_processes": 0,
            },
            "image_id": image_id,
            "preflight": preflight,
        }

    def __call__(self, **kwargs) -> dict:
        candidate_dir = Path(kwargs["candidate_dir"]).resolve()
        source_manifest_path = Path(kwargs["source_manifest_path"]).resolve()
        source_store_root = Path(kwargs["source_store_root"]).resolve()
        plan_path = Path(kwargs["plan_path"]).resolve()
        payload_root = Path(kwargs["payload_root"]).resolve()
        code_root = Path(kwargs["code_root"]).resolve()
        release_id = kwargs["release_id"]
        runtime_identity = kwargs["runtime_identity"]
        policy = kwargs["policy"]
        evidence = self._preflight(policy=policy)
        runtime_evidence_path = (
            candidate_dir / "data" / "manifests" / "docling_runtime_evidence_v1.json"
        )
        runtime_evidence = {
            "schema_version": "docling_runtime_evidence_v1",
            "release_id": release_id,
            "status": "complete",
            "ssh_target": policy["docling"]["ssh_target"],
            "runtime": runtime_identity,
            **evidence,
        }
        atomic_write_json(runtime_evidence_path, runtime_evidence, indent=2)
        payload_root.mkdir(parents=True, exist_ok=True)
        runtime_tmp = candidate_dir / ".pipeline" / "tmp" / "docling"
        runtime_cache = candidate_dir / ".pipeline" / "cache" / "docling"
        runtime_tmp.mkdir(parents=True, exist_ok=True)
        runtime_cache.mkdir(parents=True, exist_ok=True)
        for directory in (payload_root, runtime_tmp, runtime_cache):
            directory.chmod(0o777)
        receipt_path = payload_root / "docling_payload_manifest_v1.json"
        route = policy["docling"]
        def mount(source: Path, *, readonly: bool = False) -> str:
            value = f"type=bind,src={source},dst={source}"
            return value + ",readonly" if readonly else value

        input_work_root = runtime_tmp / "inputs"
        command = [
            "docker",
            "run",
            "--rm",
            "--device",
            route["device"],
            "--network",
            route["network"],
            "--env",
            f"PYTHONPATH={code_root / 'backend' / 'src'}",
            "--env",
            "HF_HUB_OFFLINE=1",
            "--env",
            "TRANSFORMERS_OFFLINE=1",
            "--env",
            "DOCLING_ARTIFACTS_PATH=/opt/docling/models",
            "--env",
            f"TMPDIR={runtime_tmp}",
            "--env",
            f"XDG_CACHE_HOME={runtime_cache}",
            "--mount",
            mount(candidate_dir),
            "--mount",
            mount(source_store_root, readonly=True),
            "--mount",
            mount(source_manifest_path, readonly=True),
            "--mount",
            mount(plan_path, readonly=True),
            "--mount",
            mount(runtime_evidence_path, readonly=True),
            "--mount",
            mount(code_root, readonly=True),
            "--workdir",
            str(code_root / "backend"),
            "--entrypoint",
            "python",
            route["image"],
            "-m",
            "bgpkb.ingestion.docling_payload_worker",
            "--plan",
            str(plan_path),
            "--source-manifest",
            str(source_manifest_path),
            "--source-store",
            str(source_store_root),
            "--output-root",
            str(payload_root),
            "--input-work-root",
            str(input_work_root),
            "--receipt",
            str(receipt_path),
            "--runtime-evidence",
            str(runtime_evidence_path),
            "--release-id",
            release_id,
        ]
        try:
            self._run_target(route["ssh_target"], command)
        finally:
            for directory in (payload_root, runtime_tmp, runtime_cache):
                if directory.exists():
                    directory.chmod(0o750)
        try:
            return json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CandidateDoclingReprocessError(
                f"Docling payload 回执不可读：{exc}"
            ) from exc


def run_candidate_docling_reprocess(
    *,
    candidate_dir: Path,
    plan_path: Path,
    source_manifest_path: Path,
    source_store_root: Path,
    payload_root: Path,
    output_root: Path,
    manifest_path: Path,
    policy_path: Path,
    release_id: str,
    execution_mode: str,
    code_root: Path | None = None,
    remote_runner=None,
) -> dict:
    candidate_dir = Path(candidate_dir).resolve()
    for field, value in (
        ("plan", plan_path),
        ("source manifest", source_manifest_path),
        ("source store", source_store_root),
        ("payload root", payload_root),
        ("Canonical output root", output_root),
        ("Docling manifest", manifest_path),
    ):
        _within_candidate(candidate_dir, Path(value), field=field)
    policy = load_reprocess_policy(policy_path)
    plan, snapshots = _read_plan(
        plan_path=plan_path,
        source_manifest_path=source_manifest_path,
        source_store_root=source_store_root,
        policy_path=policy_path,
        release_id=release_id,
        policy=policy,
    )
    if not plan["sources"]:
        return {
            "status": "not_required",
            "summary": {"requested": 0, "materialized": 0, "failed": 0},
            "documents": [],
        }
    if execution_mode != "remote":
        raise CandidateDoclingReprocessError(
            "存在 Docling 重处理任务，但未通过参数显式启用远端执行"
        )
    runtime_identity = _runtime_identity(policy)
    runner = remote_runner or SSHDoclingRunner()
    receipt = runner(
        candidate_dir=candidate_dir,
        plan=plan,
        plan_path=Path(plan_path).resolve(),
        source_manifest_path=Path(source_manifest_path).resolve(),
        source_store_root=Path(source_store_root).resolve(),
        payload_root=Path(payload_root).resolve(),
        code_root=Path(code_root or paths.REPOSITORY_ROOT).resolve(),
        release_id=release_id,
        runtime_identity=runtime_identity,
        policy=policy,
    )
    _validate_receipt(
        receipt=receipt,
        plan=plan,
        snapshots=snapshots,
        payload_root=payload_root,
        release_id=release_id,
        runtime_identity=runtime_identity,
    )
    result = materialize_docling_reprocess(
        source_manifest_path=source_manifest_path,
        source_store_root=source_store_root,
        payload_root=payload_root,
        output_root=output_root,
        manifest_path=manifest_path,
        source_ids=[row["source_id"] for row in plan["sources"]],
        release_id=release_id,
        runtime_identity=runtime_identity,
        model_evidence=receipt["model_evidence"],
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-store", type=Path, required=True)
    parser.add_argument("--payload-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument(
        "--execution-mode", choices=("disabled", "remote"), default="disabled"
    )
    parser.add_argument("--code-root", type=Path, default=paths.REPOSITORY_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_candidate_docling_reprocess(
            candidate_dir=args.candidate_dir,
            plan_path=args.plan,
            source_manifest_path=args.source_manifest,
            source_store_root=args.source_store,
            payload_root=args.payload_root,
            output_root=args.output_root,
            manifest_path=args.manifest,
            policy_path=args.policy,
            release_id=args.release_id,
            execution_mode=args.execution_mode,
            code_root=args.code_root,
        )
    except (
        CandidateDoclingReprocessError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(str(exc))
        return 2
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
