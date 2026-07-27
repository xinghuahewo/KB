from concurrent.futures import ThreadPoolExecutor
import threading
import time

import pytest
from fastapi.testclient import TestClient


def test_readiness_is_not_successful_until_preload_finishes(tmp_path):
    from bgpkb.infrastructure.retrieval_runtime import RetrievalRuntimeReadiness

    started = threading.Event()
    release = threading.Event()

    def loader(_index_path):
        started.set()
        assert release.wait(timeout=2)
        return {
            "ready": True,
            "index_mode": "fast_numpy",
            "record_count": 2,
            "dimension": 2,
        }

    readiness = RetrievalRuntimeReadiness(loader=loader)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(readiness.preload, tmp_path / "index.jsonl")
        assert started.wait(timeout=2)
        assert readiness.status() == {
            "ready": False,
            "status": "loading",
            "index_mode": None,
        }
        release.set()
        result = future.result(timeout=2)

    assert result["ready"] is True
    assert readiness.status()["status"] == "ready"
    assert readiness.status()["index_mode"] == "fast_numpy"


def test_readiness_preload_is_single_flight_for_concurrent_callers(tmp_path):
    from bgpkb.infrastructure.retrieval_runtime import RetrievalRuntimeReadiness

    call_count = 0
    count_lock = threading.Lock()

    def loader(_index_path):
        nonlocal call_count
        with count_lock:
            call_count += 1
        time.sleep(0.05)
        return {
            "ready": True,
            "index_mode": "fast_numpy",
            "record_count": 2,
            "dimension": 2,
        }

    readiness = RetrievalRuntimeReadiness(loader=loader)
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(
            executor.map(
                lambda _index: readiness.preload(tmp_path / "index.jsonl"),
                range(4),
            )
        )

    assert call_count == 1
    assert all(result["index_mode"] == "fast_numpy" for result in results)


def test_preload_failure_is_unhealthy_and_never_silently_degrades(tmp_path):
    from bgpkb.infrastructure.retrieval_runtime import (
        RetrievalRuntimeError,
        RetrievalRuntimeReadiness,
    )

    readiness = RetrievalRuntimeReadiness(
        loader=lambda _path: (_ for _ in ()).throw(RuntimeError("broken index"))
    )

    with pytest.raises(RetrievalRuntimeError, match="broken index"):
        readiness.preload(tmp_path / "index.jsonl")

    assert readiness.status() == {
        "ready": False,
        "status": "failed",
        "index_mode": None,
        "error": "fast index preload failed",
    }


def test_health_returns_503_before_retrieval_runtime_is_ready(monkeypatch):
    from bgpkb.api import app as api_app

    monkeypatch.setattr(
        api_app,
        "retrieval_runtime_status",
        lambda: {"ready": False, "status": "loading", "index_mode": None},
    )
    monkeypatch.setattr(
        api_app.database,
        "health_status",
        lambda: {"integrity_check": "ok", "degraded": False},
    )
    monkeypatch.setattr(
        api_app.ChatRepository,
        "health",
        lambda self: {"writable": True},
    )

    response = TestClient(api_app.app).get("/health")

    assert response.status_code == 503
    assert response.json()["retrieval_runtime"]["ready"] is False

