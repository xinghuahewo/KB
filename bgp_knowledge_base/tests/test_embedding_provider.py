from pathlib import Path

from bgpkb import paths
import sys


ROOT = paths.PROJECT_ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgpkb.service import embedding_provider  # noqa: E402


def test_default_embedding_provider_never_runs_local_model():
    settings = embedding_provider.load_settings()

    assert settings["default_provider"] == "deterministic_mock"
    assert settings["local_model_enabled"] is False
    assert settings["active_provider"]["downloads_model"] is False
    assert settings["active_provider"]["requires_network"] is False


def test_qwen_embedding_provider_is_reserved_but_disabled():
    settings = embedding_provider.load_settings()
    provider = settings["providers"]["qwen_embedding"]

    assert provider["enabled"] is False
    assert provider["reserved_for"] == "future_remote_or_deployment_stage"
    assert provider["runs_on_current_device"] is False
