import importlib.util
from pathlib import Path
import threading
import time

from fastapi.testclient import TestClient


SERVICE_PATH = Path(__file__).resolve().parents[1] / "deploy/retrieval-models/service.py"


def load_service():
    spec = importlib.util.spec_from_file_location("retrieval_model_service", SERVICE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeEmbeddingModel:
    def encode(self, texts):
        return {"dense_vecs": [[float(index), 1.0] for index, _ in enumerate(texts)]}


class FakeReranker:
    def compute_score(self, pairs, normalize=True):
        return [float(len(document)) for _, document in pairs]


def test_embedding_service_contract_and_health_redacts_paths():
    service = load_service()
    app = service.create_app(
        role="embedding",
        model=FakeEmbeddingModel(),
        revision="fixed-revision",
        device="cuda:0",
    )
    client = TestClient(app)

    response = client.post(
        "/v1/embeddings",
        json={"model": "BAAI/bge-m3", "input": ["BGP", "RPKI"]},
    )

    assert response.status_code == 200
    assert response.json()["data"] == [
        {"index": 0, "embedding": [0.0, 1.0]},
        {"index": 1, "embedding": [1.0, 1.0]},
    ]
    health = client.get("/health").json()
    assert health == {
        "role": "embedding",
        "model": "BAAI/bge-m3",
        "revision": "fixed-revision",
        "device": "cuda:0",
        "loaded": True,
    }


def test_reranker_service_sorts_and_applies_top_n():
    service = load_service()
    client = TestClient(service.create_app(role="reranker", model=FakeReranker()))
    documents = ["x" * size for size in range(1, 9)]

    response = client.post(
        "/v1/rerank",
        json={
            "model": "BAAI/bge-reranker-v2-m3",
            "query": "route leak",
            "documents": documents,
            "top_n": 5,
        },
    )

    assert response.status_code == 200
    assert [item["index"] for item in response.json()["results"]] == [7, 6, 5, 4, 3]


def test_service_rejects_empty_inputs_wrong_models_roles_and_invalid_top_n():
    service = load_service()
    embedding = TestClient(service.create_app(role="embedding", model=FakeEmbeddingModel()))
    reranker = TestClient(service.create_app(role="reranker", model=FakeReranker()))
    valid_documents = ["doc"] * 8

    assert embedding.post("/v1/embeddings", json={"model": "BAAI/bge-m3", "input": []}).status_code == 422
    assert embedding.post("/v1/embeddings", json={"model": "wrong", "input": ["x"]}).status_code == 422
    assert reranker.post("/v1/embeddings", json={"model": "BAAI/bge-m3", "input": ["x"]}).status_code == 409
    assert embedding.post(
        "/v1/rerank",
        json={"model": "BAAI/bge-reranker-v2-m3", "query": "q", "documents": valid_documents, "top_n": 5},
    ).status_code == 409
    assert reranker.post(
        "/v1/rerank",
        json={"model": "BAAI/bge-reranker-v2-m3", "query": "q", "documents": [], "top_n": 5},
    ).status_code == 422
    assert reranker.post(
        "/v1/rerank",
        json={"model": "BAAI/bge-reranker-v2-m3", "query": "q", "documents": valid_documents, "top_n": 4},
    ).status_code == 422
    assert reranker.post(
        "/v1/rerank",
        json={"model": "BAAI/bge-reranker-v2-m3", "query": "q", "documents": ["x"] * 5, "top_n": 6},
    ).status_code == 422


def test_model_manifest_and_runtime_deployment_contracts():
    root = Path(__file__).resolve().parents[1] / "deploy/retrieval-models"
    manifest = __import__("json").loads((root / "model_manifest.json").read_text())
    assert manifest == {
        "models": [
            {"model": "BAAI/bge-m3", "revision": "5617a9f61b028005a4858fdac845db406aefb181"},
            {"model": "BAAI/bge-reranker-v2-m3", "revision": "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"},
        ]
    }
    compose = (root / "compose.yaml").read_text()
    assert "${RETRIEVAL_BIND_ADDRESS:-10.99.8.28}:8011:8011" in compose
    assert "${RETRIEVAL_BIND_ADDRESS:-10.99.8.28}:8012:8012" in compose
    assert "0.0.0.0:8011" not in compose and "0.0.0.0:8012" not in compose
    assert "pull_policy: never" in compose
    assert "restart: unless-stopped" in compose
    assert "${EMBEDDING_GPU_CDI}" in compose
    assert "${RERANKER_GPU_CDI}" in compose
    assert "${RETRIEVAL_IMAGE}" in compose
    assert "--gpus all" not in compose
    assert "stage-b-v1" not in compose
    assert not (root / "model_manifest.lock.json").exists()


def test_runtime_preflight_checks_model_hashes_gpu_policy_and_health(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1] / "deploy/retrieval-models"
    spec = importlib.util.spec_from_file_location("verify_runtime", root / "verify_runtime.py")
    verify = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verify)
    models = tmp_path / "models"
    model_dir = models / "BAAI/bge-m3"
    model_dir.mkdir(parents=True)
    (model_dir / "weights.bin").write_bytes(b"weights")
    import hashlib
    import json
    lock = models / "model_manifest.lock.json"
    lock.write_text(json.dumps({"models": [{
        "model": "BAAI/bge-m3",
        "revision": "r",
        "files": [{"path": "weights.bin", "sha256": hashlib.sha256(b"weights").hexdigest()}],
    }]}))
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({
        "allowed_indices": [2, 3],
        "embedding": {"min_free_mib": 8192},
        "reranker": {"min_free_mib": 8192},
    }))
    env = tmp_path / ".env"
    env.write_text(
        "EMBEDDING_GPU_CDI=nvidia.com/gpu=2\nRERANKER_GPU_CDI=nvidia.com/gpu=3\n"
        "EMBEDDING_GPU_INDEX=2\nRERANKER_GPU_INDEX=3\n"
    )

    verify.verify_prestart(
        models, lock, env, policy,
        command_runner=lambda command: "2, 11264, 1000\n3, 11264, 1000\n",
    )
    verify.verify_health(lambda port: {
        "role": "embedding" if port == 8011 else "reranker",
        "model": "BAAI/bge-m3" if port == 8011 else "BAAI/bge-reranker-v2-m3",
        "revision": "r",
        "device": "cuda:0",
        "loaded": port == 8011,
    })

    captured = {}
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return b'{"loaded":false}'
    monkeypatch.setenv("RETRIEVAL_BIND_ADDRESS", "10.99.8.28")
    monkeypatch.setattr(verify.urllib.request, "urlopen", lambda url, timeout: captured.setdefault("url", url) and Response())
    verify._fetch_health(8011)
    assert captured["url"] == "http://10.99.8.28:8011/health"


def test_runtime_lock_is_fully_pinned_for_linux_amd64_python_311():
    root = Path(__file__).resolve().parents[1] / "deploy/retrieval-models"
    lines = [
        line.strip() for line in (root / "requirements.lock").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#") and not line.startswith((" ", "-"))
    ]
    assert all("==" in line.split(";", 1)[0] for line in lines)
    names = {line.split("==", 1)[0].lower() for line in lines}
    for required in (
        "fastapi", "starlette", "pydantic", "uvicorn", "flagembedding", "torch",
        "transformers", "sentence-transformers", "huggingface-hub",
    ):
        assert required in names
    dockerfile = (root / "Dockerfile").read_text()
    assert "python:3.11." in dockerfile.splitlines()[0]
    assert "--requirement /app/requirements.lock" in dockerfile


def test_health_warmup_success_and_model_failure_is_not_ready():
    service = load_service()
    ready = TestClient(service.create_app(role="embedding", model=FakeEmbeddingModel()))

    class Broken:
        def encode(self, texts):
            raise RuntimeError("secret model path /models/private")

    broken = TestClient(service.create_app(role="embedding", model=Broken()))

    assert ready.get("/health").status_code == 200
    assert ready.get("/health").json()["loaded"] is True
    assert broken.get("/health").status_code == 503


def test_lazy_model_concurrent_first_load_happens_once():
    service = load_service()
    calls = []
    model = object()
    lazy = service.LazyModel("embedding", "/models", "cuda:0", loader=lambda: (calls.append(1), model)[1])
    results = []
    threads = [threading.Thread(target=lambda: results.append(lazy.get())) for _ in range(8)]

    for thread in threads: thread.start()
    for thread in threads: thread.join()

    assert calls == [1]
    assert results == [model] * 8


def test_inference_is_semaphore_bounded_and_oversized_inputs_rejected():
    service = load_service()

    class BlockingEmbedding:
        def __init__(self):
            self.active = 0
            self.max_active = 0
            self.lock = threading.Lock()
        def encode(self, texts):
            with self.lock:
                self.active += 1
                self.max_active = max(self.max_active, self.active)
            time.sleep(0.02)
            with self.lock:
                self.active -= 1
            return {"dense_vecs": [[1.0] for _ in texts]}

    model = BlockingEmbedding()
    client = TestClient(service.create_app(role="embedding", model=model, max_concurrency=1))
    threads = [threading.Thread(target=lambda: client.post(
        "/v1/embeddings", json={"model": "BAAI/bge-m3", "input": ["x"]}
    )) for _ in range(2)]
    for thread in threads: thread.start()
    for thread in threads: thread.join()
    assert model.max_active == 1

    assert client.post("/v1/embeddings", json={
        "model": "BAAI/bge-m3", "input": ["x"] * 65,
    }).status_code == 422
    assert client.post("/v1/embeddings", json={
        "model": "BAAI/bge-m3", "input": ["x" * 4097],
    }).status_code == 422

    reranker = TestClient(service.create_app(role="reranker", model=FakeReranker()))
    assert reranker.post("/v1/rerank", json={
        "model": "BAAI/bge-reranker-v2-m3", "query": "q",
        "documents": ["d"] * 21, "top_n": 5,
    }).status_code == 422
    assert reranker.post("/v1/rerank", json={
        "model": "BAAI/bge-reranker-v2-m3", "query": "q" * 4097,
        "documents": ["d"] * 5, "top_n": 5,
    }).status_code == 422


def test_compose_has_real_readiness_healthchecks():
    compose = (Path(__file__).resolve().parents[1] / "deploy/retrieval-models/compose.yaml").read_text()
    assert compose.count("healthcheck:") == 2
    for key in ("interval:", "timeout:", "retries:", "start_period:"):
        assert compose.count(key) == 2
    assert "urllib.request" in compose


def test_runtime_lock_rejects_path_traversal_and_symlink_escape(tmp_path):
    root = Path(__file__).resolve().parents[1] / "deploy/retrieval-models"
    spec = importlib.util.spec_from_file_location("verify_runtime_paths", root / "verify_runtime.py")
    verify = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verify)
    models = tmp_path / "models"
    models.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "weights.bin").write_bytes(b"x")
    (models / "escape").symlink_to(outside)
    import hashlib
    import json

    bad_locks = [
        {"models": [{"model": "../outside", "revision": "r", "files": []}]},
        {"models": [{"model": "escape", "revision": "r", "files": [{
            "path": "weights.bin", "sha256": hashlib.sha256(b"x").hexdigest(),
        }]}]},
        {"models": [{"model": "safe", "revision": "r", "files": [{"path": "../x", "sha256": "0" * 64}]}]},
    ]
    for index, payload in enumerate(bad_locks):
        lock = tmp_path / f"bad-{index}.json"
        lock.write_text(json.dumps(payload))
        try:
            verify.verify_model_lock(models, lock)
        except RuntimeError as exc:
            assert "路径" in str(exc) or "逃逸" in str(exc)
        else:
            raise AssertionError("危险 lock 路径必须被拒绝")
