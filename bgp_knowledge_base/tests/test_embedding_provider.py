from pathlib import Path

from bgpkb import paths
import sys


ROOT = paths.PROJECT_ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgpkb.service import embedding_provider  # noqa: E402


def test_default_embedding_provider_is_remote_and_never_runs_local_model(monkeypatch):
    monkeypatch.delenv("SILICONFLOW_API_KEY", raising=False)
    settings = embedding_provider.load_settings()

    assert settings["default_provider"] == "siliconflow_bge_m3"
    assert settings["offline_fallback_provider"] == "deterministic_mock"
    assert settings["local_model_enabled"] is False
    assert settings["active_provider"]["downloads_model"] is False
    assert settings["active_provider"]["requires_network"] is True
    assert settings["active_provider"]["runs_on_current_device"] is False
    assert settings["active_provider_status"]["available"] is False
    assert settings["active_provider_status"]["missing_environment"] == ["SILICONFLOW_API_KEY"]


def test_qwen_embedding_provider_is_reserved_but_disabled():
    settings = embedding_provider.load_settings()
    provider = settings["providers"]["qwen_embedding"]

    assert provider["enabled"] is False
    assert provider["reserved_for"] == "future_remote_or_deployment_stage"
    assert provider["runs_on_current_device"] is False


def test_remote_embedding_providers_only_read_credentials_from_environment(monkeypatch):
    monkeypatch.setenv("SILICONFLOW_API_KEY", "test-siliconflow-key")
    monkeypatch.setenv("ALIYUN_BGE_M3_ENDPOINT", "https://example.invalid/embed")
    monkeypatch.setenv("ALIYUN_BGE_M3_API_KEY", "test-aliyun-key")

    siliconflow = embedding_provider.provider_status("siliconflow_bge_m3")
    aliyun = embedding_provider.provider_status("aliyun_eas_bge_m3")

    assert siliconflow["available"] is True
    assert siliconflow["model"] == "BAAI/bge-m3"
    assert siliconflow["credential_source"] == "environment"
    assert aliyun["available"] is True
    assert aliyun["credential_source"] == "environment"
    assert "test-siliconflow-key" not in repr(siliconflow)
    assert "test-aliyun-key" not in repr(aliyun)
