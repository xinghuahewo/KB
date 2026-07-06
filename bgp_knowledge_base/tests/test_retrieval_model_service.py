import importlib.util
from pathlib import Path

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
