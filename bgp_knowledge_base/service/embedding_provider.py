from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
RAG_CONFIG = ROOT / "config" / "rag_retrieval.yaml"


def load_settings():
    payload = yaml.safe_load(RAG_CONFIG.read_text(encoding="utf-8"))
    embedding = payload.get("embedding", {})
    providers = embedding.get("providers", {})
    default_provider = embedding.get("default_provider", "deterministic_mock")
    active_provider = providers.get(default_provider, {})
    return {
        "default_provider": default_provider,
        "local_model_enabled": bool(embedding.get("local_model_enabled", False)),
        "active_provider": active_provider,
        "providers": providers,
    }
