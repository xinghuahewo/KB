import os
from pathlib import Path

from bgpkb import paths

import yaml


ROOT = paths.PROJECT_ROOT
RAG_CONFIG = paths.CONFIG_DIR / "rag_retrieval.yaml"


def _payload():
    return yaml.safe_load(RAG_CONFIG.read_text(encoding="utf-8"))


def provider_status(provider_name, environ=None):
    payload = _payload()
    provider = payload.get("embedding", {}).get("providers", {}).get(provider_name, {})
    environment = os.environ if environ is None else environ
    required_environment = [
        provider.get(field)
        for field in ("api_key_env", "endpoint_env")
        if provider.get(field)
    ]
    missing = [name for name in required_environment if not environment.get(name)]
    return {
        "provider": provider_name,
        "model": provider.get("model", ""),
        "enabled": bool(provider.get("enabled", False)),
        "available": bool(provider.get("enabled", False)) and not missing,
        "credential_source": "environment" if required_environment else "none",
        "missing_environment": missing,
        "requires_network": bool(provider.get("requires_network", False)),
        "runs_on_current_device": bool(provider.get("runs_on_current_device", False)),
    }


def load_settings():
    payload = _payload()
    embedding = payload.get("embedding", {})
    providers = embedding.get("providers", {})
    default_provider = embedding.get("default_provider", "deterministic_mock")
    active_provider = providers.get(default_provider, {})
    return {
        "default_provider": default_provider,
        "offline_fallback_provider": embedding.get("offline_fallback_provider", "deterministic_mock"),
        "local_model_enabled": bool(embedding.get("local_model_enabled", False)),
        "active_provider": active_provider,
        "active_provider_status": provider_status(default_provider),
        "providers": providers,
    }
