import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from service import bge_m3_remote_client  # noqa: E402


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_siliconflow_client_builds_openai_compatible_payload():
    client = bge_m3_remote_client.BgeM3RemoteClient(
        provider="siliconflow_bge_m3",
        api_key="test-key",
    )

    payload = client.build_payload(["route leak", "路由泄露"])

    assert payload == {
        "model": "BAAI/bge-m3",
        "input": ["route leak", "路由泄露"],
        "encoding_format": "float",
    }


def test_aliyun_client_builds_eas_dense_payload():
    client = bge_m3_remote_client.BgeM3RemoteClient(
        provider="aliyun_eas_bge_m3",
        api_key="test-key",
        base_url="https://example.invalid/embed",
    )

    assert client.build_payload(["route leak"]) == {
        "input": ["route leak"],
        "embedding_type": "dense",
    }


def test_remote_client_parses_vectors_without_leaking_key(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse({
            "data": [
                {"index": 1, "embedding": [0.0, 1.0]},
                {"index": 0, "embedding": [1.0, 0.0]},
            ]
        })

    monkeypatch.setattr(bge_m3_remote_client.urllib.request, "urlopen", fake_urlopen)
    client = bge_m3_remote_client.BgeM3RemoteClient(
        provider="siliconflow_bge_m3",
        api_key="secret-test-key",
        timeout=12,
    )

    result = client.embed_texts(["route leak", "RPKI"])

    assert result["ok"] is True
    assert result["vectors"] == [[1.0, 0.0], [0.0, 1.0]]
    assert result["dimension"] == 2
    assert result["provider"] == "siliconflow_bge_m3"
    assert captured["timeout"] == 12
    assert "secret-test-key" not in repr(client)
    assert "secret-test-key" not in json.dumps(result)


def test_remote_client_reports_unavailable_without_api_key():
    client = bge_m3_remote_client.BgeM3RemoteClient(
        provider="siliconflow_bge_m3",
        api_key="",
    )

    result = client.embed_texts(["route leak"])

    assert result["ok"] is False
    assert result["error_code"] == "missing_api_key"
