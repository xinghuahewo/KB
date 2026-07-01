"""Docling 清洗 v2 的文档级幂等批处理编排。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import time
from typing import Callable, Mapping
import uuid

from .contracts import atomic_write_json


SUCCESS_STATES = ("discovered", "preflighted", "parsed", "normalized", "validated", "approved")
PROCESSING_STAGES = SUCCESS_STATES[1:]
ALL_STATES = SUCCESS_STATES + ("quarantined",)
RETRYABLE_ERROR_TYPES = {"gpu_oom", "timeout", "transient_model_error"}
DIRECT_QUARANTINE_ERROR_TYPES = {"invalid_content", "schema_error", "governance_error"}


class InvalidStateTransition(ValueError):
    """状态机发生非法跃迁。"""


class RunInterrupted(RuntimeError):
    """非内容类故障中断批次，允许使用同一 run_id 续跑。"""


class BatchFailure(RuntimeError):
    """携带批处理治理语义的受控错误。"""

    def __init__(self, error_type: str, message: str, *, retryable: bool = False, quarantine: bool = True):
        super().__init__(message)
        self.error_type = error_type
        self.retryable = retryable
        self.quarantine = quarantine


@dataclass(frozen=True)
class StageContext:
    run_id: str
    doc_id: str
    source_path: Path
    stage: str
    attempt: int
    temporary_dir: Path
    status: dict
    config: dict
    runtime_identity: dict


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _canonical_hash(payload) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def processing_fingerprint(source_path, runtime_identity, config) -> str:
    """用输入内容、镜像/模型身份和完整配置构造稳定处理指纹。"""
    source = Path(source_path)
    return _canonical_hash(
        {
            "source_sha256": _file_sha256(source),
            "runtime_identity": runtime_identity,
            "config": config,
        }
    )


def new_document_status(run_id, doc_id, source_path, fingerprint, *, now=None) -> dict:
    timestamp = now or _utc_now()
    return {
        "schema_version": "cleaning_document_status_v2",
        "run_id": run_id,
        "doc_id": doc_id,
        "source_path": str(source_path),
        "processing_fingerprint": fingerprint,
        "state": "discovered",
        "transitions": [],
        "errors": [],
        "retries": [],
        "performance": {
            "duration_seconds": 0.0,
            "page_count": 0,
            "ocr_page_count": 0,
            "gpu_peak_memory_mb": 0.0,
            "stage_durations_seconds": {},
        },
        "output_summary": {"fallback_used": False, "counts": {}},
        "skip_reason": None,
        "updated_at": timestamp,
    }


def transition(status: dict, target_state: str, *, reason: str, now=None) -> None:
    current = status["state"]
    valid_target = None
    if current in SUCCESS_STATES[:-1]:
        valid_target = SUCCESS_STATES[SUCCESS_STATES.index(current) + 1]
    if target_state != valid_target and not (target_state == "quarantined" and current not in {"approved", "quarantined"}):
        raise InvalidStateTransition(f"非法状态迁移: {current} -> {target_state}")
    timestamp = now or _utc_now()
    status["transitions"].append(
        {"from": current, "to": target_state, "run_id": status["run_id"], "at": timestamp, "reason": reason}
    )
    status["state"] = target_state
    status["updated_at"] = timestamp


def _document_id(source: Path) -> str:
    stem = re.sub(r"[^0-9A-Za-z._-]+", "-", source.stem).strip("-") or "document"
    identity = hashlib.sha256(str(source.resolve()).encode("utf-8")).hexdigest()[:12]
    return f"{stem}-{identity}"


def _percentile(values, percentile):
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _merge_metrics(status: dict, metrics: dict) -> None:
    performance = status["performance"]
    performance["page_count"] = max(performance["page_count"], int(metrics.get("page_count", 0)))
    performance["ocr_page_count"] += int(metrics.get("ocr_page_count", 0))
    performance["gpu_peak_memory_mb"] = max(
        performance["gpu_peak_memory_mb"], float(metrics.get("gpu_peak_memory_mb", 0))
    )
    status["output_summary"]["fallback_used"] |= bool(metrics.get("fallback_used", False))
    for key, value in metrics.get("output_counts", {}).items():
        status["output_summary"]["counts"][key] = int(value)


def _as_batch_failure(error: Exception) -> BatchFailure:
    if isinstance(error, BatchFailure):
        return error
    if isinstance(error, MemoryError):
        return BatchFailure("gpu_oom", str(error) or "GPU 显存不足", retryable=True)
    if isinstance(error, TimeoutError):
        return BatchFailure("timeout", str(error) or "处理超时", retryable=True)
    return BatchFailure("unexpected_error", str(error), retryable=False, quarantine=False)


class BatchRunner:
    """以文档为事务边界运行、恢复并发布清洗结果。"""

    def __init__(
        self,
        *,
        output_root,
        run_root,
        config: dict,
        runtime_identity: dict,
        handlers: Mapping[str, Callable[[StageContext], dict]],
    ):
        self.output_root = Path(output_root)
        self.run_root = Path(run_root)
        self.config = config
        self.runtime_identity = runtime_identity
        self.handlers = handlers
        missing = set(PROCESSING_STAGES) - set(handlers)
        if missing:
            raise ValueError("缺少阶段处理器: " + ", ".join(sorted(missing)))

    def run(self, sources, *, run_id=None, resume=False) -> dict:
        run_id = run_id or f"cleaning-v2-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
        run_dir = self.run_root / run_id
        status_dir = run_dir / "document_status"
        work_root = run_dir / "work"
        status_dir.mkdir(parents=True, exist_ok=True)
        work_root.mkdir(parents=True, exist_ok=True)
        self.output_root.mkdir(parents=True, exist_ok=True)
        started_at = _utc_now()
        started_clock = time.monotonic()
        documents = []

        for source_value in sources:
            source = Path(source_value)
            doc_id = _document_id(source)
            fingerprint = processing_fingerprint(source, self.runtime_identity, self.config)
            authority_status_path = self.output_root / doc_id / "document_status.json"
            if authority_status_path.is_file():
                prior = json.loads(authority_status_path.read_text(encoding="utf-8"))
                if prior.get("state") == "approved" and prior.get("processing_fingerprint") == fingerprint:
                    skipped = dict(prior)
                    skipped["run_id"] = run_id
                    skipped["skip_reason"] = "identical_approved_fingerprint"
                    skipped["updated_at"] = _utc_now()
                    documents.append(skipped)
                    atomic_write_json(status_dir / f"{doc_id}.json", skipped)
                    continue

            status_path = status_dir / f"{doc_id}.json"
            if resume and status_path.is_file():
                status = json.loads(status_path.read_text(encoding="utf-8"))
                if status["processing_fingerprint"] != fingerprint:
                    status = new_document_status(run_id, doc_id, source, fingerprint)
            else:
                status = new_document_status(run_id, doc_id, source, fingerprint)
            work_dir = work_root / doc_id
            work_dir.mkdir(parents=True, exist_ok=True)
            document_started = time.monotonic()
            try:
                self._run_document(source, status, status_path, work_dir)
            except RunInterrupted:
                status["performance"]["duration_seconds"] += time.monotonic() - document_started
                atomic_write_json(status_path, status)
                raise
            status["performance"]["duration_seconds"] += time.monotonic() - document_started
            atomic_write_json(status_path, status)
            if status["state"] == "approved":
                self._publish(work_dir, self.output_root / doc_id, status)
            documents.append(status)

        elapsed = time.monotonic() - started_clock
        result = {
            "schema_version": "cleaning_run_v2",
            "run_id": run_id,
            "started_at": started_at,
            "finished_at": _utc_now(),
            "runtime": self.runtime_identity,
            "config_fingerprint": _canonical_hash(self.config),
            "summary": self._summarize(documents, elapsed),
            "documents": documents,
        }
        atomic_write_json(run_dir / "cleaning_run.json", result)
        self._write_jsonl(run_dir / "document_status.jsonl", documents)
        (run_dir / "cleaning_run_report.md").write_text(self._render_report(result), encoding="utf-8")
        return result

    def _run_document(self, source, status, status_path, work_dir):
        if status["state"] in {"approved", "quarantined"}:
            return
        start_index = SUCCESS_STATES.index(status["state"])
        maximum_attempts = max(1, int(self.config.get("retry", {}).get("maximum_attempts", 2)))
        configured_retryable = set(
            self.config.get("retry", {}).get("retryable_errors", RETRYABLE_ERROR_TYPES)
        )
        for stage in PROCESSING_STAGES[start_index:]:
            for attempt in range(1, maximum_attempts + 1):
                stage_started = time.monotonic()
                context = StageContext(
                    run_id=status["run_id"], doc_id=status["doc_id"], source_path=source,
                    stage=stage, attempt=attempt, temporary_dir=work_dir, status=status,
                    config=self.config, runtime_identity=self.runtime_identity,
                )
                try:
                    metrics = self.handlers[stage](context) or {}
                    duration = time.monotonic() - stage_started
                    status["performance"]["stage_durations_seconds"][stage] = (
                        status["performance"]["stage_durations_seconds"].get(stage, 0.0) + duration
                    )
                    _merge_metrics(status, metrics)
                    transition(status, stage, reason=f"{stage} 阶段完成")
                    atomic_write_json(status_path, status)
                    break
                except Exception as error:
                    failure = _as_batch_failure(error)
                    timestamp = _utc_now()
                    status["errors"].append(
                        {"stage": stage, "error_type": failure.error_type, "message": str(failure),
                         "retryable": failure.retryable, "attempt": attempt, "at": timestamp}
                    )
                    can_retry = (
                        failure.retryable and failure.error_type in configured_retryable and attempt < maximum_attempts
                    )
                    if can_retry:
                        status["retries"].append(
                            {"stage": stage, "error_type": failure.error_type, "attempt": attempt,
                             "next_attempt": attempt + 1, "at": timestamp}
                        )
                        atomic_write_json(status_path, status)
                        continue
                    if failure.quarantine or failure.error_type in DIRECT_QUARANTINE_ERROR_TYPES or failure.retryable:
                        transition(status, "quarantined", reason=f"{stage} 失败: {failure.error_type}")
                        atomic_write_json(status_path, status)
                        return
                    atomic_write_json(status_path, status)
                    raise RunInterrupted(f"{status['doc_id']} 在 {stage} 中断: {failure}") from error

    def _publish(self, work_dir: Path, target: Path, status: dict) -> None:
        atomic_write_json(work_dir / "document_status.json", status)
        staging = self.output_root / f".{target.name}.tmp-{uuid.uuid4().hex}"
        backup = self.output_root / f".{target.name}.backup-{uuid.uuid4().hex}"
        if staging.exists():
            shutil.rmtree(staging)
        os.replace(work_dir, staging)
        replaced = False
        try:
            if target.exists():
                os.replace(target, backup)
                replaced = True
            os.replace(staging, target)
            if backup.exists():
                shutil.rmtree(backup)
        except Exception:
            if target.exists() and replaced:
                shutil.rmtree(target)
            if backup.exists():
                os.replace(backup, target)
            if staging.exists():
                work_dir.parent.mkdir(parents=True, exist_ok=True)
                os.replace(staging, work_dir)
            raise

    @staticmethod
    def _write_jsonl(path: Path, documents) -> None:
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            for document in documents:
                handle.write(json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)

    @staticmethod
    def _summarize(documents, elapsed):
        count = len(documents)
        durations = [row["performance"]["duration_seconds"] for row in documents]
        approved = sum(row["state"] == "approved" for row in documents)
        quarantined = sum(row["state"] == "quarantined" for row in documents)
        skipped = sum(bool(row.get("skip_reason")) for row in documents)
        return {
            "document_count": count,
            "approved_count": approved,
            "quarantined_count": quarantined,
            "skipped_count": skipped,
            "failure_rate": quarantined / count if count else 0.0,
            "throughput_documents_per_hour": count * 3600 / elapsed if elapsed > 0 else 0.0,
            "duration_p50_seconds": _percentile(durations, 0.50),
            "duration_p95_seconds": _percentile(durations, 0.95),
            "gpu_peak_memory_mb": max((row["performance"]["gpu_peak_memory_mb"] for row in documents), default=0.0),
            "ocr_page_count": sum(row["performance"]["ocr_page_count"] for row in documents),
            "fallback_count": sum(row["output_summary"]["fallback_used"] for row in documents),
            "retry_count": sum(len(row["retries"]) for row in documents),
        }

    @staticmethod
    def _render_report(run):
        summary = run["summary"]
        return "\n".join(
            [
                "# Docling 清洗批次报告", "", f"- 批次 ID：`{run['run_id']}`",
                f"- 文档数：{summary['document_count']}", f"- 通过数：{summary['approved_count']}",
                f"- 隔离数：{summary['quarantined_count']}", f"- 幂等跳过数：{summary['skipped_count']}",
                f"- 吞吐量：{summary['throughput_documents_per_hour']:.2f} 篇/小时",
                f"- p50 时延：{summary['duration_p50_seconds']:.3f} 秒",
                f"- p95 时延：{summary['duration_p95_seconds']:.3f} 秒",
                f"- 失败率：{summary['failure_rate']:.2%}",
                f"- GPU 峰值显存：{summary['gpu_peak_memory_mb']:.1f} MiB",
                f"- OCR 页数：{summary['ocr_page_count']}",
                f"- fallback 文档数：{summary['fallback_count']}",
                f"- 重试次数：{summary['retry_count']}", "",
                "## 文档终态", "",
                *[f"- `{row['doc_id']}`：{row['state']}" for row in run["documents"]], "",
            ]
        )
