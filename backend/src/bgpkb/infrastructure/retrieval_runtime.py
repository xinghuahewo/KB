"""FastAPI 检索运行时的启动 readiness 与 single-flight 预载。"""

from __future__ import annotations

from pathlib import Path
import threading
from typing import Callable

from bgpkb import paths
from bgpkb.infrastructure.fast_vector_index import preload_fast_vector_index


class RetrievalRuntimeError(RuntimeError):
    """检索运行时无法在服务 ready 前完成预载。"""


class RetrievalRuntimeReadiness:
    def __init__(
        self,
        *,
        loader: Callable[[Path], dict] = preload_fast_vector_index,
    ):
        self._loader = loader
        self._condition = threading.Condition()
        self._status = "uninitialized"
        self._index_path: Path | None = None
        self._result: dict | None = None

    def status(self) -> dict:
        with self._condition:
            payload = {
                "ready": self._status == "ready",
                "status": self._status,
                "index_mode": (
                    self._result.get("index_mode")
                    if self._result is not None
                    else None
                ),
            }
            if self._status == "ready" and self._result is not None:
                payload.update({
                    "record_count": self._result.get("record_count"),
                    "dimension": self._result.get("dimension"),
                })
            if self._status == "failed":
                payload["error"] = "fast index preload failed"
            return payload

    def preload(self, index_path: Path) -> dict:
        resolved = Path(index_path).expanduser().resolve()
        with self._condition:
            while self._status == "loading":
                self._condition.wait()
            if self._status == "ready" and self._index_path == resolved:
                return dict(self._result or {})
            if self._status == "failed" and self._index_path == resolved:
                raise RetrievalRuntimeError("fast index preload failed")
            self._status = "loading"
            self._index_path = resolved
            self._result = None
        try:
            result = dict(self._loader(resolved))
            if (
                result.get("ready") is not True
                or result.get("index_mode") != "fast_numpy"
            ):
                raise RetrievalRuntimeError(
                    "fast index preload 未进入 fast_numpy ready 状态"
                )
        except Exception as exc:
            with self._condition:
                self._status = "failed"
                self._condition.notify_all()
            raise RetrievalRuntimeError(
                f"fast index preload failed: {exc}"
            ) from exc
        with self._condition:
            self._status = "ready"
            self._result = result
            self._condition.notify_all()
            return dict(result)


_READINESS = RetrievalRuntimeReadiness()


def preload_retrieval_runtime(data_dir: Path | None = None) -> dict:
    active_data_dir = Path(data_dir or paths.require_runtime_data_dir())
    return _READINESS.preload(
        active_data_dir / "published" / "bge_m3_vector_index.jsonl"
    )


def retrieval_runtime_status() -> dict:
    return _READINESS.status()


def reset_retrieval_runtime_for_tests() -> None:
    global _READINESS
    _READINESS = RetrievalRuntimeReadiness()
