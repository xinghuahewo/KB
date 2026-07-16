"""RAG 证据链五阶段候选构建编排器。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Callable, Mapping, Sequence

import yaml

from bgpkb import paths


STAGE_ORDER = (
    "source-ingest",
    "canonicalize",
    "semantic-build",
    "publish-index",
    "verify-release",
)
PIPELINE_CONFIG_PATH = paths.CONFIG_DIR / "converged_pipeline_v2.yaml"
FAST_INDEX_ARTIFACTS = (
    "data/published/bge_m3_vector_matrix.npy",
    "data/published/bge_m3_vector_metadata.jsonl",
    "data/published/bge_m3_vector_fast_manifest.json",
)


class PipelineDefinitionError(ValueError):
    """五阶段配置不满足固定产品契约。"""


class CandidateIsolationError(ValueError):
    """候选路径与受保护 release 路径重叠。"""


@dataclass(frozen=True)
class SubtaskDefinition:
    subtask_id: str
    module: str
    args: tuple[str, ...]
    write_paths: tuple[str, ...]
    failure_policy: str
    code_dependencies: tuple[str, ...]
    fingerprint_files: tuple[str, ...]


@dataclass(frozen=True)
class StageDefinition:
    name: str
    depends_on: tuple[str, ...]
    input_manifests: tuple[str, ...]
    required_outputs: tuple[str, ...]
    closure_artifacts: tuple[str, ...]
    success_criteria: tuple[str, ...]
    subtasks: tuple[SubtaskDefinition, ...]


@dataclass(frozen=True)
class PipelineDefinition:
    schema_version: str
    pipeline_version: str
    config_path: Path
    stages: Mapping[str, StageDefinition]


@dataclass(frozen=True)
class SubtaskContext:
    definition: PipelineDefinition
    stage: StageDefinition
    subtask: SubtaskDefinition
    candidate_dir: Path
    data_dir: Path
    source_store_dir: Path
    environment: Mapping[str, str]
    command: tuple[str, ...]
    write_paths: tuple[Path, ...]


TaskExecutor = Callable[[SubtaskContext], Mapping[str, object] | int]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _fingerprint_json(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _fingerprint_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _fingerprint_file_or_missing(path: Path) -> str:
    return _fingerprint_file(path) if Path(path).is_file() else "missing"


def _fingerprint_tree(root: Path) -> str:
    root = Path(root).resolve()
    if not root.is_dir():
        return "missing"
    entries = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": _fingerprint_file(path),
            "size": path.stat().st_size,
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]
    return _fingerprint_json(entries)


def _normalize_stage(raw: Mapping[str, object]) -> StageDefinition:
    subtasks = tuple(
        SubtaskDefinition(
            subtask_id=str(item["id"]),
            module=str(item["module"]),
            args=tuple(str(arg) for arg in item.get("args", [])),
            write_paths=tuple(str(path) for path in item.get("write_paths", [])),
            failure_policy=str(item.get("failure_policy", "stop")),
            code_dependencies=tuple(str(module) for module in item.get("code_dependencies", [])),
            fingerprint_files=tuple(str(path) for path in item.get("fingerprint_files", [])),
        )
        for item in raw.get("subtasks", [])
    )
    return StageDefinition(
        name=str(raw["name"]),
        depends_on=tuple(str(item) for item in raw.get("depends_on", [])),
        input_manifests=tuple(str(item) for item in raw.get("input_manifests", [])),
        required_outputs=tuple(str(item) for item in raw.get("required_outputs", [])),
        closure_artifacts=tuple(str(item) for item in raw.get("closure_artifacts", [])),
        success_criteria=tuple(str(item) for item in raw.get("success_criteria", [])),
        subtasks=subtasks,
    )


def load_pipeline_definition(config_path: Path = PIPELINE_CONFIG_PATH) -> PipelineDefinition:
    config_path = Path(config_path).resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != "converged_pipeline_v2":
        raise PipelineDefinitionError("五阶段配置 schema_version 非法")
    stage_rows = raw.get("stages")
    if not isinstance(stage_rows, list):
        raise PipelineDefinitionError("五阶段配置缺少 stages")
    stages = {stage.name: stage for stage in (_normalize_stage(item) for item in stage_rows)}
    if tuple(stages) != STAGE_ORDER:
        raise PipelineDefinitionError(f"五阶段名称或顺序必须固定为：{STAGE_ORDER}")
    expected_dependencies = {
        STAGE_ORDER[index]: (() if index == 0 else (STAGE_ORDER[index - 1],))
        for index in range(len(STAGE_ORDER))
    }
    for name, stage in stages.items():
        if stage.depends_on != expected_dependencies[name]:
            raise PipelineDefinitionError(f"阶段 {name} 依赖必须为 {expected_dependencies[name]}")
        if not stage.subtasks:
            raise PipelineDefinitionError(f"阶段 {name} 至少需要一个内部子任务")
        for subtask in stage.subtasks:
            if not subtask.write_paths:
                raise PipelineDefinitionError(
                    f"子任务 {name}/{subtask.subtask_id} 必须声明候选写入路径"
                )
            if subtask.failure_policy not in {"stop", "collect_for_gate"}:
                raise PipelineDefinitionError(
                    f"子任务 {name}/{subtask.subtask_id} failure_policy 非法"
                )
            if subtask.failure_policy == "collect_for_gate" and name != "verify-release":
                raise PipelineDefinitionError(
                    "collect_for_gate 只允许 verify-release 内部报告子任务使用"
                )
    return PipelineDefinition(
        schema_version=str(raw["schema_version"]),
        pipeline_version=str(raw["pipeline_version"]),
        config_path=config_path,
        stages=stages,
    )


def stage_manifest_path(candidate_dir: Path, stage_name: str) -> Path:
    return Path(candidate_dir).resolve() / ".pipeline" / "manifests" / f"{stage_name}.json"


def checkpoint_path(candidate_dir: Path, stage_name: str) -> Path:
    return Path(candidate_dir).resolve() / ".pipeline" / "checkpoints" / f"{stage_name}.json"


def invalidation_log_path(candidate_dir: Path) -> Path:
    return Path(candidate_dir).resolve() / ".pipeline" / "invalidations.json"


def candidate_state_path(candidate_dir: Path) -> Path:
    return Path(candidate_dir).resolve() / ".pipeline" / "candidate.json"


def _default_protected_paths() -> tuple[Path, ...]:
    configured = [paths.DATA_DIR]
    for name in ("BGPKB_CURRENT_RELEASE_DIR", "BGPKB_PREVIOUS_RELEASE_DIR"):
        if os.environ.get(name):
            configured.append(Path(os.environ[name]))
    return tuple(configured)


def assert_candidate_isolated(
    candidate_dir: Path,
    *,
    protected_paths: Sequence[Path] | None = None,
) -> Path:
    candidate = Path(candidate_dir).expanduser()
    if candidate.exists() and candidate.is_symlink():
        raise CandidateIsolationError(f"候选目录不得是符号链接：{candidate}")
    candidate = candidate.resolve()
    if candidate.name in {"current", "previous"}:
        raise CandidateIsolationError(f"候选目录不得使用 release 指针名称：{candidate}")
    protected = _default_protected_paths() if protected_paths is None else tuple(protected_paths)
    for raw_path in protected:
        path = Path(raw_path).expanduser().resolve()
        if candidate == path or candidate.is_relative_to(path) or path.is_relative_to(candidate):
            raise CandidateIsolationError(f"候选目录与受保护路径重叠：candidate={candidate}; protected={path}")
    return candidate


def _render_subtask_command(
    subtask: SubtaskDefinition,
    *,
    candidate_dir: Path,
    frozen_source_root: Path,
    frozen_canonical_root: Path,
    frozen_assets_root: Path,
    frozen_legacy_chunks_root: Path,
    frozen_source_catalog_path: Path,
    frozen_entity_evidence_path: Path,
) -> tuple[str, ...]:
    substitutions = _candidate_substitutions(
        candidate_dir,
        frozen_source_root=frozen_source_root,
        frozen_canonical_root=frozen_canonical_root,
        frozen_assets_root=frozen_assets_root,
        frozen_legacy_chunks_root=frozen_legacy_chunks_root,
        frozen_source_catalog_path=frozen_source_catalog_path,
        frozen_entity_evidence_path=frozen_entity_evidence_path,
    )
    return (
        sys.executable,
        "-m",
        subtask.module,
        *(argument.format(**substitutions) for argument in subtask.args),
    )


def _candidate_substitutions(
    candidate_dir: Path,
    *,
    frozen_source_root: Path | None = None,
    frozen_canonical_root: Path | None = None,
    frozen_assets_root: Path | None = None,
    frozen_legacy_chunks_root: Path | None = None,
    frozen_source_catalog_path: Path | None = None,
    frozen_entity_evidence_path: Path | None = None,
) -> dict[str, str]:
    selected_frozen_root = Path(frozen_source_root or paths.RAW_DIR).expanduser().resolve()
    selected_canonical_root = Path(
        frozen_canonical_root or paths.DATA_DIR / "corpus" / "parsed_v2"
    ).expanduser().resolve()
    selected_assets_root = Path(
        frozen_assets_root or paths.DATA_DIR / "corpus" / "assets_v2"
    ).expanduser().resolve()
    selected_legacy_chunks_root = Path(
        frozen_legacy_chunks_root or paths.CORPUS_DIR / "chunks_v2"
    ).expanduser().resolve()
    selected_source_catalog_path = Path(
        frozen_source_catalog_path or paths.PUBLISHED_DIR / "source_catalog.jsonl"
    ).expanduser().resolve()
    selected_entity_evidence_path = Path(
        frozen_entity_evidence_path
        or paths.DATASETS_DIR / "entity_source_evidence.jsonl"
    ).expanduser().resolve()
    return {
        "candidate_dir": str(candidate_dir),
        "data_dir": str(candidate_dir / "data"),
        "source_store_dir": str(candidate_dir / "source-store"),
        "frozen_source_root": str(selected_frozen_root),
        "frozen_canonical_root": str(selected_canonical_root),
        "frozen_assets_root": str(selected_assets_root),
        "frozen_legacy_chunks_root": str(selected_legacy_chunks_root),
        "frozen_source_catalog_path": str(selected_source_catalog_path),
        "frozen_entity_evidence_path": str(selected_entity_evidence_path),
        "release_id": candidate_dir.name,
        "backend_root": str(paths.PROJECT_ROOT),
        "repository_root": str(paths.REPOSITORY_ROOT),
    }


def _render_subtask_write_paths(
    subtask: SubtaskDefinition,
    *,
    candidate_dir: Path,
) -> tuple[Path, ...]:
    write_paths = tuple(
        Path(value.format(**_candidate_substitutions(candidate_dir))).resolve()
        for value in subtask.write_paths
    )
    for write_path in write_paths:
        if write_path != candidate_dir and not write_path.is_relative_to(candidate_dir):
            raise CandidateIsolationError(
                f"子任务写入路径必须位于候选目录：{subtask.subtask_id}={write_path}"
            )
    return write_paths


def _protected_path_state(raw_path: Path) -> dict[str, object]:
    """记录指针及 release 树的轻量不可变证据，避免重复读取大型向量本体。"""

    path = Path(raw_path).expanduser().absolute()
    if path.is_symlink():
        target = path.resolve()
        return {
            "kind": "symlink",
            "target": os.readlink(path),
            "resolved_target": str(target),
            "target_state": _protected_path_state(target),
        }
    if not path.exists():
        return {"kind": "missing"}
    if path.is_file():
        stat = path.stat()
        return {
            "kind": "file",
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "sha256": _fingerprint_file(path),
        }
    entries = []
    for item in sorted(path.rglob("*")):
        relative = item.relative_to(path).as_posix()
        if item.is_symlink():
            entries.append({"path": relative, "kind": "symlink", "target": os.readlink(item)})
            continue
        if not item.is_file():
            continue
        stat = item.stat()
        row: dict[str, object] = {
            "path": relative,
            "kind": "file",
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        }
        if stat.st_size <= 1024 * 1024 or item.name in {
            "SHA256SUMS",
            "release_manifest_v2.json",
            "publish_index_manifest_v1.json",
        }:
            row["sha256"] = _fingerprint_file(item)
        entries.append(row)
    return {"kind": "directory", "entries": entries}


def _protected_state(protected_paths: Sequence[Path]) -> dict[str, object]:
    state = {
        str(Path(path).expanduser().absolute()): _protected_path_state(path)
        for path in protected_paths
    }
    return {"fingerprint": _fingerprint_json(state), "paths": state}


def _write_candidate_state(
    candidate_dir: Path,
    *,
    status: str,
    reader_selectable: bool,
    protected_state: Mapping[str, object],
    failed_stage: str | None = None,
) -> None:
    _atomic_json(
        candidate_state_path(candidate_dir),
        {
            "schema_version": "pipeline_candidate_state_v1",
            "status": status,
            "reader_selectable": reader_selectable,
            "failed_stage": failed_stage,
            "protected_state_fingerprint": protected_state["fingerprint"],
            "updated_at": _utc_now(),
        },
    )


def _default_task_executor(context: SubtaskContext) -> Mapping[str, object]:
    result = subprocess.run(
        context.command,
        cwd=paths.PROJECT_ROOT,
        env=dict(context.environment),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "diagnostics": {},
    }


def _normalize_task_result(result: Mapping[str, object] | int) -> dict:
    if isinstance(result, int):
        return {"returncode": result, "stdout": "", "stderr": "", "diagnostics": {}}
    return {
        "returncode": int(result.get("returncode", 1)),
        "stdout": str(result.get("stdout", "")),
        "stderr": str(result.get("stderr", "")),
        "diagnostics": dict(result.get("diagnostics", {})),
    }


def _write_subtask_logs(
    candidate_dir: Path,
    stage_name: str,
    subtask_id: str,
    result: Mapping[str, object],
) -> tuple[str, str]:
    log_root = candidate_dir / ".pipeline" / "logs" / stage_name
    stdout_path = log_root / f"{subtask_id}.stdout.log"
    stderr_path = log_root / f"{subtask_id}.stderr.log"
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(str(result["stdout"]), encoding="utf-8")
    stderr_path.write_text(str(result["stderr"]), encoding="utf-8")
    return (
        stdout_path.relative_to(candidate_dir).as_posix(),
        stderr_path.relative_to(candidate_dir).as_posix(),
    )


def _stage_manifest(
    *,
    definition: PipelineDefinition,
    stage: StageDefinition,
    candidate_dir: Path,
    status: str,
    started_at: str,
    subtasks: list[dict],
    diagnostics: list[dict],
    fingerprint: str,
    fingerprint_components: Mapping[str, object],
) -> dict:
    return {
        "schema_version": "pipeline_stage_manifest_v1",
        "pipeline_version": definition.pipeline_version,
        "stage": stage.name,
        "status": status,
        "candidate_dir": str(candidate_dir),
        "started_at": started_at,
        "completed_at": _utc_now(),
        "depends_on": list(stage.depends_on),
        "input_manifests": list(stage.input_manifests),
        "required_outputs": list(stage.required_outputs),
        "closure_artifacts": list(stage.closure_artifacts),
        "success_criteria": list(stage.success_criteria),
        "fingerprint": fingerprint,
        "fingerprint_components": fingerprint_components,
        "subtasks": subtasks,
        "diagnostics": diagnostics,
    }


def _stage_names_through(target_stage: str) -> tuple[str, ...]:
    try:
        index = STAGE_ORDER.index(target_stage)
    except ValueError as exc:
        raise PipelineDefinitionError(f"未知目标阶段：{target_stage}") from exc
    return STAGE_ORDER[: index + 1]


def _candidate_input_path(candidate_dir: Path, logical_path: str) -> Path:
    path = Path(logical_path)
    if path.is_absolute() or ".." in path.parts:
        raise PipelineDefinitionError(f"阶段输入必须是受控相对路径：{logical_path}")
    if path.parts and path.parts[0] == "data":
        return candidate_dir / path
    return paths.PROJECT_ROOT / path


def _input_fingerprints(
    stage: StageDefinition,
    *,
    candidate_dir: Path,
    external_inputs: Mapping[str, str],
) -> dict:
    declared = {}
    for logical_path in stage.input_manifests:
        path = _candidate_input_path(candidate_dir, logical_path)
        declared[logical_path] = _fingerprint_file(path) if path.is_file() else "missing"
    return {
        "declared": dict(sorted(declared.items())),
        "external": dict(sorted(external_inputs.items())),
    }


def _stage_configuration_fingerprint(
    definition: PipelineDefinition,
    stage: StageDefinition,
    override: str,
) -> str:
    stage_payload = asdict(stage)
    for subtask in stage_payload["subtasks"]:
        if not subtask["code_dependencies"]:
            subtask.pop("code_dependencies")
        if not subtask["fingerprint_files"]:
            subtask.pop("fingerprint_files")
    return _fingerprint_json({
        "schema_version": definition.schema_version,
        "pipeline_version": definition.pipeline_version,
        "stage": stage_payload,
        "override": override,
    })


def _stage_code_fingerprint(
    code_fingerprint: str | Mapping[str, str],
    stage_name: str,
) -> str:
    if isinstance(code_fingerprint, str):
        return code_fingerprint
    try:
        return str(code_fingerprint[stage_name])
    except KeyError as exc:
        raise PipelineDefinitionError(f"缺少阶段代码指纹：{stage_name}") from exc


def _upstream_manifest_fingerprints(
    candidate_dir: Path,
    stage: StageDefinition,
) -> dict[str, str]:
    fingerprints = {}
    for dependency in stage.depends_on:
        manifest_path = stage_manifest_path(candidate_dir, dependency)
        fingerprints[dependency] = (
            _fingerprint_file(manifest_path) if manifest_path.is_file() else "missing"
        )
    return fingerprints


def _fingerprint_components(
    *,
    definition: PipelineDefinition,
    stage: StageDefinition,
    candidate_dir: Path,
    external_inputs: Mapping[str, str],
    config_override: str,
    code_fingerprint: str | Mapping[str, str],
) -> dict:
    return {
        "inputs": _input_fingerprints(
            stage,
            candidate_dir=candidate_dir,
            external_inputs=external_inputs,
        ),
        "config": _stage_configuration_fingerprint(definition, stage, config_override),
        "code": _stage_code_fingerprint(code_fingerprint, stage.name),
        "upstream_manifests": _upstream_manifest_fingerprints(candidate_dir, stage),
    }


def _checkpoint_reuse_status(
    candidate_dir: Path,
    stage: StageDefinition,
    *,
    expected_fingerprint: str,
) -> tuple[bool, str, dict]:
    path = checkpoint_path(candidate_dir, stage.name)
    if not path.is_file():
        return False, "checkpoint_missing", {}
    try:
        checkpoint = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, "checkpoint_invalid", {}
    if checkpoint.get("schema_version") != "pipeline_stage_checkpoint_v1":
        return False, "checkpoint_schema_mismatch", checkpoint
    if checkpoint.get("status") != "complete":
        return False, "checkpoint_not_complete", checkpoint
    if checkpoint.get("fingerprint") != expected_fingerprint:
        return False, "fingerprint_changed", checkpoint
    manifest_path = stage_manifest_path(candidate_dir, stage.name)
    if not manifest_path.is_file():
        return False, "output_manifest_missing", checkpoint
    if _fingerprint_file(manifest_path) != checkpoint.get("output_manifest_hash"):
        return False, "output_manifest_changed", checkpoint
    recorded_outputs = checkpoint.get("required_output_hashes")
    if not isinstance(recorded_outputs, dict):
        return False, "required_output_hashes_missing", checkpoint
    for relative in stage.required_outputs:
        output_path = candidate_dir / relative
        if not output_path.is_file():
            return False, f"required_output_missing:{relative}", checkpoint
        if _fingerprint_file(output_path) != recorded_outputs.get(relative):
            return False, f"required_output_changed:{relative}", checkpoint
    return True, "checkpoint_reused", checkpoint


def _write_checkpoint(
    *,
    definition: PipelineDefinition,
    stage: StageDefinition,
    candidate_dir: Path,
    fingerprint: str,
    fingerprint_components: Mapping[str, object],
) -> None:
    manifest_path = stage_manifest_path(candidate_dir, stage.name)
    payload = {
        "schema_version": "pipeline_stage_checkpoint_v1",
        "pipeline_version": definition.pipeline_version,
        "stage": stage.name,
        "status": "complete",
        "fingerprint": fingerprint,
        "fingerprint_components": fingerprint_components,
        "output_manifest": manifest_path.relative_to(candidate_dir).as_posix(),
        "output_manifest_hash": _fingerprint_file(manifest_path),
        "required_output_hashes": {
            relative: _fingerprint_file(candidate_dir / relative)
            for relative in stage.required_outputs
        },
        "completed_at": _utc_now(),
    }
    _atomic_json(checkpoint_path(candidate_dir, stage.name), payload)


def _record_invalidation(
    candidate_dir: Path,
    *,
    first_stage: str,
    invalidated_stages: Sequence[str],
    reason: str,
    previous_fingerprint: str,
    expected_fingerprint: str,
) -> None:
    path = invalidation_log_path(candidate_dir)
    if path.is_file():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {"schema_version": "pipeline_invalidation_log_v1", "events": []}
    else:
        payload = {"schema_version": "pipeline_invalidation_log_v1", "events": []}
    payload.setdefault("events", []).append({
        "recorded_at": _utc_now(),
        "first_affected_stage": first_stage,
        "invalidated_stages": list(invalidated_stages),
        "reason": reason,
        "previous_fingerprint": previous_fingerprint,
        "expected_fingerprint": expected_fingerprint,
    })
    _atomic_json(path, payload)


def _invalidate_from(
    candidate_dir: Path,
    *,
    first_stage: str,
    target_stage: str,
    reason: str,
    previous_fingerprint: str,
    expected_fingerprint: str,
) -> None:
    target_names = _stage_names_through(target_stage)
    first_index = target_names.index(first_stage)
    invalidated = target_names[first_index:]
    _record_invalidation(
        candidate_dir,
        first_stage=first_stage,
        invalidated_stages=invalidated,
        reason=reason,
        previous_fingerprint=previous_fingerprint,
        expected_fingerprint=expected_fingerprint,
    )
    for stage_name in invalidated:
        checkpoint_path(candidate_dir, stage_name).unlink(missing_ok=True)
        stage_manifest_path(candidate_dir, stage_name).unlink(missing_ok=True)


def run_pipeline(
    *,
    candidate_dir: Path,
    target_stage: str,
    definition: PipelineDefinition | None = None,
    task_executor: TaskExecutor | None = None,
    external_input_fingerprints: Mapping[str, Mapping[str, str]] | None = None,
    stage_config_fingerprints: Mapping[str, str] | None = None,
    code_fingerprint: str | Mapping[str, str] = "",
    protected_paths: Sequence[Path] | None = None,
    frozen_source_root: Path | None = None,
    frozen_canonical_root: Path | None = None,
    frozen_assets_root: Path | None = None,
    frozen_legacy_chunks_root: Path | None = None,
    frozen_source_catalog_path: Path | None = None,
    frozen_entity_evidence_path: Path | None = None,
) -> dict:
    definition = definition or load_pipeline_definition()
    if not code_fingerprint:
        code_fingerprint = _default_code_fingerprints(definition)
    frozen_source_root = Path(frozen_source_root or paths.RAW_DIR).expanduser().resolve()
    frozen_canonical_root = Path(
        frozen_canonical_root or paths.DATA_DIR / "corpus" / "parsed_v2"
    ).expanduser().resolve()
    frozen_assets_root = Path(
        frozen_assets_root or paths.DATA_DIR / "corpus" / "assets_v2"
    ).expanduser().resolve()
    frozen_legacy_chunks_root = Path(
        frozen_legacy_chunks_root or paths.CORPUS_DIR / "chunks_v2"
    ).expanduser().resolve()
    frozen_source_catalog_path = Path(
        frozen_source_catalog_path or paths.PUBLISHED_DIR / "source_catalog.jsonl"
    ).expanduser().resolve()
    frozen_entity_evidence_path = Path(
        frozen_entity_evidence_path
        or paths.DATASETS_DIR / "entity_source_evidence.jsonl"
    ).expanduser().resolve()
    protected = _default_protected_paths() if protected_paths is None else tuple(protected_paths)
    resolved_protected = tuple(Path(path).expanduser().resolve() for path in protected)
    for frozen_input in (
        frozen_source_root,
        frozen_canonical_root,
        frozen_assets_root,
        frozen_legacy_chunks_root,
        frozen_source_catalog_path,
        frozen_entity_evidence_path,
    ):
        if not any(
            frozen_input == path or frozen_input.is_relative_to(path)
            for path in resolved_protected
        ):
            protected = (*protected, frozen_input)
            resolved_protected = (*resolved_protected, frozen_input)
    candidate = assert_candidate_isolated(candidate_dir, protected_paths=protected)
    protected_before = _protected_state(protected)
    candidate.mkdir(parents=True, exist_ok=True)
    (candidate / "data").mkdir(exist_ok=True)
    (candidate / "source-store").mkdir(exist_ok=True)
    runtime_temp = candidate / ".pipeline" / "tmp"
    runtime_cache = candidate / ".pipeline" / "cache"
    runtime_temp.mkdir(parents=True, exist_ok=True)
    runtime_cache.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    for name in ("BGPKB_CURRENT_RELEASE_DIR", "BGPKB_PREVIOUS_RELEASE_DIR"):
        environment.pop(name, None)
    environment.update({
        "BGPKB_CANDIDATE_DIR": str(candidate),
        "BGPKB_RELEASE_ID": candidate.name,
        "BGPKB_DATA_DIR": str(candidate / "data"),
        "BGPKB_SOURCE_STORE_DIR": str(candidate / "source-store"),
        "BGPKB_FROZEN_SOURCE_ROOT": str(frozen_source_root),
        "BGPKB_FROZEN_CANONICAL_ROOT": str(frozen_canonical_root),
        "BGPKB_FROZEN_ASSETS_ROOT": str(frozen_assets_root),
        "BGPKB_FROZEN_LEGACY_CHUNKS_ROOT": str(frozen_legacy_chunks_root),
        "BGPKB_FROZEN_SOURCE_CATALOG_PATH": str(frozen_source_catalog_path),
        "BGPKB_FROZEN_ENTITY_EVIDENCE_PATH": str(frozen_entity_evidence_path),
        "BGPKB_PIPELINE_WRITE_ROOT": str(candidate),
        "TMPDIR": str(runtime_temp),
        "TMP": str(runtime_temp),
        "TEMP": str(runtime_temp),
        "XDG_CACHE_HOME": str(runtime_cache),
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    _write_candidate_state(
        candidate,
        status="building",
        reader_selectable=False,
        protected_state=protected_before,
    )
    executor = task_executor or _default_task_executor
    external_input_fingerprints = {
        stage_name: dict(values)
        for stage_name, values in (external_input_fingerprints or {}).items()
    }
    external_input_fingerprints.setdefault("source-ingest", {}).setdefault(
        "frozen_source_root",
        _fingerprint_tree(frozen_source_root),
    )
    external_input_fingerprints.setdefault("canonicalize", {}).setdefault(
        "frozen_canonical_root",
        _fingerprint_tree(frozen_canonical_root),
    )
    external_input_fingerprints.setdefault("canonicalize", {}).setdefault(
        "frozen_assets_root",
        _fingerprint_tree(frozen_assets_root),
    )
    external_input_fingerprints.setdefault("semantic-build", {}).setdefault(
        "frozen_legacy_chunks_root",
        _fingerprint_tree(frozen_legacy_chunks_root),
    )
    external_input_fingerprints.setdefault("semantic-build", {}).setdefault(
        "frozen_source_catalog_path",
        _fingerprint_file_or_missing(frozen_source_catalog_path),
    )
    external_input_fingerprints.setdefault("semantic-build", {}).setdefault(
        "frozen_entity_evidence_path",
        _fingerprint_file_or_missing(frozen_entity_evidence_path),
    )
    stage_config_fingerprints = stage_config_fingerprints or {}
    executed_stages: list[str] = []
    reused_stages: list[str] = []
    force_execute = False

    for stage_name in _stage_names_through(target_stage):
        stage = definition.stages[stage_name]
        components = _fingerprint_components(
            definition=definition,
            stage=stage,
            candidate_dir=candidate,
            external_inputs=external_input_fingerprints.get(stage_name, {}),
            config_override=stage_config_fingerprints.get(stage_name, ""),
            code_fingerprint=code_fingerprint,
        )
        fingerprint = _fingerprint_json(components)
        if not force_execute:
            reusable, invalidation_reason, previous_checkpoint = _checkpoint_reuse_status(
                candidate,
                stage,
                expected_fingerprint=fingerprint,
            )
            if reusable:
                reused_stages.append(stage_name)
                continue
            _invalidate_from(
                candidate,
                first_stage=stage_name,
                target_stage=target_stage,
                reason=invalidation_reason,
                previous_fingerprint=str(previous_checkpoint.get("fingerprint", "")),
                expected_fingerprint=fingerprint,
            )
            force_execute = True

        started_at = _utc_now()
        subtask_rows: list[dict] = []
        failure_code = 0
        collected_failure_codes: list[int] = []
        for subtask in stage.subtasks:
            command = _render_subtask_command(
                subtask,
                candidate_dir=candidate,
                frozen_source_root=frozen_source_root,
                frozen_canonical_root=frozen_canonical_root,
                frozen_assets_root=frozen_assets_root,
                frozen_legacy_chunks_root=frozen_legacy_chunks_root,
                frozen_source_catalog_path=frozen_source_catalog_path,
                frozen_entity_evidence_path=frozen_entity_evidence_path,
            )
            write_paths = _render_subtask_write_paths(subtask, candidate_dir=candidate)
            context = SubtaskContext(
                definition=definition,
                stage=stage,
                subtask=subtask,
                candidate_dir=candidate,
                data_dir=candidate / "data",
                source_store_dir=candidate / "source-store",
                environment=environment,
                command=command,
                write_paths=write_paths,
            )
            start = time.monotonic()
            result = _normalize_task_result(executor(context))
            duration_ms = round((time.monotonic() - start) * 1000, 3)
            stdout_log, stderr_log = _write_subtask_logs(
                candidate, stage_name, subtask.subtask_id, result
            )
            subtask_rows.append({
                "subtask_id": subtask.subtask_id,
                "module": subtask.module,
                "command": list(command),
                "write_paths": [str(path) for path in write_paths],
                "failure_policy": subtask.failure_policy,
                "returncode": result["returncode"],
                "duration_ms": duration_ms,
                "stdout_log": stdout_log,
                "stderr_log": stderr_log,
                "diagnostics": result["diagnostics"],
            })
            if _protected_state(protected) != protected_before:
                result["diagnostics"]["error_code"] = "protected_release_modified"
                failure_code = 70
                break
            if result["returncode"] != 0:
                if subtask.failure_policy == "collect_for_gate":
                    collected_failure_codes.append(int(result["returncode"]))
                    continue
                failure_code = int(result["returncode"])
                break

        diagnostics: list[dict] = [
            {
                "error_code": "collected_gate_subtask_failure",
                "returncode": code,
            }
            for code in collected_failure_codes
        ]
        if failure_code == 0:
            closure_paths = tuple(dict.fromkeys(
                (*stage.required_outputs, *stage.closure_artifacts)
            ))
            diagnostics.extend(
                [
                {"error_code": "missing_required_output", "path": relative}
                for relative in closure_paths
                if not (candidate / relative).is_file()
                ]
            )
            missing_outputs = any(
                row["error_code"] == "missing_required_output" for row in diagnostics
            )
            if missing_outputs:
                failure_code = 1
            elif collected_failure_codes:
                failure_code = collected_failure_codes[0]

        status = "failed" if failure_code else "complete"
        manifest = _stage_manifest(
            definition=definition,
            stage=stage,
            candidate_dir=candidate,
            status=status,
            started_at=started_at,
            subtasks=subtask_rows,
            diagnostics=diagnostics,
            fingerprint=fingerprint,
            fingerprint_components=components,
        )
        _atomic_json(stage_manifest_path(candidate, stage_name), manifest)
        executed_stages.append(stage_name)
        if failure_code:
            _write_candidate_state(
                candidate,
                status="failed",
                reader_selectable=False,
                protected_state=protected_before,
                failed_stage=stage_name,
            )
            return {
                "status": "failed",
                "exit_code": failure_code,
                "failed_stage": stage_name,
                "executed_stages": executed_stages,
                "reused_stages": reused_stages,
                "candidate_dir": str(candidate),
            }
        _write_checkpoint(
            definition=definition,
            stage=stage,
            candidate_dir=candidate,
            fingerprint=fingerprint,
            fingerprint_components=components,
        )

    verified = target_stage == "verify-release"
    _write_candidate_state(
        candidate,
        status="verified" if verified else "candidate",
        reader_selectable=verified,
        protected_state=protected_before,
    )
    return {
        "status": "complete",
        "exit_code": 0,
        "failed_stage": None,
        "executed_stages": executed_stages,
        "reused_stages": reused_stages,
        "candidate_dir": str(candidate),
    }


def _default_code_fingerprints(definition: PipelineDefinition) -> dict[str, str]:
    orchestrator_path = Path(__file__).resolve()
    fingerprints = {}
    for stage_name, stage in definition.stages.items():
        digest = hashlib.sha256()
        sources_to_hash = {"bgpkb.workflows.converged_pipeline": orchestrator_path}
        for subtask in stage.subtasks:
            for module in (subtask.module, *subtask.code_dependencies):
                spec = importlib.util.find_spec(module)
                if spec is None or spec.origin is None:
                    raise PipelineDefinitionError(f"无法定位子任务模块：{module}")
                sources_to_hash[module] = Path(spec.origin).resolve()
            for relative in subtask.fingerprint_files:
                path = (paths.PROJECT_ROOT / relative).resolve()
                if not path.is_file() or not path.is_relative_to(paths.PROJECT_ROOT.resolve()):
                    raise PipelineDefinitionError(f"无法定位阶段指纹文件：{relative}")
                sources_to_hash[f"file:{relative}"] = path
        for module, path in sorted(sources_to_hash.items()):
            digest.update(module.encode("utf-8"))
            digest.update(path.read_bytes())
        fingerprints[stage_name] = "sha256:" + digest.hexdigest()
    return fingerprints


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行 RAG 证据链五阶段候选构建")
    parser.add_argument("stage", choices=STAGE_ORDER)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=PIPELINE_CONFIG_PATH)
    parser.add_argument("--frozen-source-root", type=Path, default=paths.RAW_DIR)
    parser.add_argument(
        "--frozen-canonical-root",
        type=Path,
        default=paths.DATA_DIR / "corpus" / "parsed_v2",
    )
    parser.add_argument(
        "--frozen-assets-root",
        type=Path,
        default=paths.DATA_DIR / "corpus" / "assets_v2",
    )
    parser.add_argument(
        "--frozen-legacy-chunks-root",
        type=Path,
        default=paths.CORPUS_DIR / "chunks_v2",
    )
    parser.add_argument(
        "--frozen-source-catalog-path",
        type=Path,
        default=paths.PUBLISHED_DIR / "source_catalog.jsonl",
    )
    parser.add_argument(
        "--frozen-entity-evidence-path",
        type=Path,
        default=paths.DATASETS_DIR / "entity_source_evidence.jsonl",
    )
    parser.add_argument("--plan-only", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    definition = load_pipeline_definition(args.config)
    if args.plan_only:
        print(json.dumps({
            "pipeline_version": definition.pipeline_version,
            "candidate_dir": str(args.candidate_dir.expanduser().resolve()),
            "frozen_source_root": str(args.frozen_source_root.expanduser().resolve()),
            "frozen_canonical_root": str(args.frozen_canonical_root.expanduser().resolve()),
            "frozen_assets_root": str(args.frozen_assets_root.expanduser().resolve()),
            "frozen_legacy_chunks_root": str(args.frozen_legacy_chunks_root.expanduser().resolve()),
            "frozen_source_catalog_path": str(args.frozen_source_catalog_path.expanduser().resolve()),
            "frozen_entity_evidence_path": str(args.frozen_entity_evidence_path.expanduser().resolve()),
            "target_stage": args.stage,
            "stages": list(_stage_names_through(args.stage)),
            "mode": "plan_only",
        }, ensure_ascii=False, indent=2))
        return 0
    try:
        result = run_pipeline(
            candidate_dir=args.candidate_dir,
            target_stage=args.stage,
            definition=definition,
            code_fingerprint=_default_code_fingerprints(definition),
            frozen_source_root=args.frozen_source_root,
            frozen_canonical_root=args.frozen_canonical_root,
            frozen_assets_root=args.frozen_assets_root,
            frozen_legacy_chunks_root=args.frozen_legacy_chunks_root,
            frozen_source_catalog_path=args.frozen_source_catalog_path,
            frozen_entity_evidence_path=args.frozen_entity_evidence_path,
        )
    except (CandidateIsolationError, PipelineDefinitionError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
