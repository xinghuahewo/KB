"""从 SemanticChunk v3 派生唯一、完整的检索输入。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unicodedata
from typing import Any, Iterable

import yaml

from bgpkb import paths


SCHEMA_VERSION = "retrieval_document_v1"
RETRIEVAL_TEXT_VERSION = "retrieval_text_v1"
CONFIG_PATH = paths.CONFIG_DIR / "retrieval_text_v1.yaml"
SUPPORTED_COMPONENTS = frozenset({"fts", "embedding", "reranker"})


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_retrieval_text_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != "retrieval_text_config_v1":
        raise ValueError("retrieval text 配置 schema_version 非法")
    if config.get("retrieval_text_version") != RETRIEVAL_TEXT_VERSION:
        raise ValueError("retrieval_text_version 与当前实现不一致")
    config["config_fingerprint"] = _sha256_text(_canonical_json(config))
    return config


def _normalized_metadata(value: Any) -> str:
    return " ".join(unicodedata.normalize("NFC", str(value or "")).split())


def render_retrieval_text(chunk: dict[str, Any], config: dict[str, Any] | None = None) -> str:
    config = config or load_retrieval_text_config()
    labels = config["template"]["labels"]
    section = " > ".join(_normalized_metadata(item) for item in chunk.get("section_path", []))
    content = unicodedata.normalize("NFC", str(chunk.get("content", ""))).strip()
    if not content:
        raise ValueError("SemanticChunk v3 content 不能为空")
    lines = [
        f"{labels['title']}: {_normalized_metadata(chunk.get('title'))}",
        f"{labels['section_path']}: {section}",
        f"{labels['document_profile']}: {_normalized_metadata(chunk.get('document_profile'))}",
        f"{labels['semantic_unit']}: {_normalized_metadata(chunk.get('semantic_unit'))}",
        f"{labels['content']}: {content}",
    ]
    return "\n".join(lines)


def derive_retrieval_document(
    chunk: dict[str, Any],
    *,
    eligibility: dict[str, Any],
    governance: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if chunk.get("schema_version") != "semantic_chunk_v3":
        raise ValueError("只允许从 SemanticChunk v3 派生 Retrieval Document")
    if eligibility.get("status") not in {"eligible", "eligible_with_caution"}:
        raise ValueError("只有 eligible 或 eligible_with_caution chunk 可以派生 Retrieval Document")
    if governance.get("schema_version") != "evidence_governance_state_v1":
        raise ValueError("Retrieval Document 必须携带 Evidence Governance State v1")
    if governance.get("object_id") != chunk.get("chunk_id"):
        raise ValueError("治理状态 object_id 必须与 SemanticChunk chunk_id 一致")
    if governance.get("retrieval_eligibility") != eligibility:
        raise ValueError("治理状态中的 retrieval_eligibility 与派生输入不一致")
    required_governance = {
        "parse_status", "content_quality_status", "source_trust_status",
        "semantic_review_status", "status_provenance", "migration_audit",
    }
    missing_governance = sorted(required_governance - set(governance))
    if missing_governance:
        raise ValueError(f"治理状态缺少字段：{', '.join(missing_governance)}")
    required_eligibility = {"status", "rule_id", "policy_version", "reason", "audit"}
    missing_eligibility = sorted(required_eligibility - set(eligibility))
    if missing_eligibility:
        raise ValueError(f"检索资格缺少审计字段：{', '.join(missing_eligibility)}")
    config = config or load_retrieval_text_config()
    retrieval_text = render_retrieval_text(chunk, config)
    retrieval_text_hash = _sha256_text(retrieval_text)
    identity = _canonical_json({
        "chunk_id": chunk["chunk_id"],
        "retrieval_text_hash": retrieval_text_hash,
        "retrieval_text_version": config["retrieval_text_version"],
        "template_fingerprint": config["config_fingerprint"],
        "eligibility_policy_version": eligibility.get("policy_version"),
        "eligibility_rule_id": eligibility.get("rule_id"),
        "eligibility_status": eligibility.get("status"),
        "eligibility_input_fingerprint": eligibility.get("audit", {}).get("input_fingerprint"),
    })
    source_refs = list(dict.fromkeys(str(item) for item in chunk.get("source_refs", []) if item))
    if not source_refs:
        raise ValueError("Retrieval Document 必须保留 source_ref")
    preview_limit = int(config["preview"]["max_characters"])
    return {
        "schema_version": SCHEMA_VERSION,
        "retrieval_doc_id": f"{SCHEMA_VERSION}_{hashlib.sha256(identity.encode('utf-8')).hexdigest()}",
        "chunk_id": chunk["chunk_id"],
        "doc_id": chunk["doc_id"],
        "source_id": chunk["source_id"],
        "source_snapshot_id": chunk["source_snapshot_id"],
        "document_profile": chunk["document_profile"],
        "title": _normalized_metadata(chunk["title"]),
        "section_path": [_normalized_metadata(item) for item in chunk.get("section_path", [])],
        "semantic_unit": chunk["semantic_unit"],
        "retrieval_text": retrieval_text,
        "retrieval_text_hash": retrieval_text_hash,
        "retrieval_text_version": config["retrieval_text_version"],
        "template_version": config["config_version"],
        "template_fingerprint": config["config_fingerprint"],
        "content_preview": unicodedata.normalize("NFC", str(chunk["content"]))[:preview_limit],
        "content_hash": chunk["content_hash"],
        "source_ref": source_refs[0],
        "source_refs": source_refs,
        "governance": json.loads(_canonical_json(governance)),
        "eligibility": {
            "status": eligibility["status"],
            "rule_id": str(eligibility["rule_id"]),
            "policy_version": str(eligibility["policy_version"]),
            "reason": str(eligibility["reason"]),
            "audit": json.loads(_canonical_json(eligibility["audit"])),
        },
    }


def derive_retrieval_documents(
    chunks: Iterable[dict[str, Any]],
    eligibility_by_chunk_id: dict[str, dict[str, Any]],
    governance_by_chunk_id: dict[str, dict[str, Any]],
    *,
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    resolved_config = config or load_retrieval_text_config()
    documents = []
    for chunk in chunks:
        eligibility = eligibility_by_chunk_id.get(chunk.get("chunk_id", ""), {})
        if eligibility.get("status") not in {"eligible", "eligible_with_caution"}:
            continue
        documents.append(
            derive_retrieval_document(
                chunk,
                eligibility=eligibility,
                governance=governance_by_chunk_id.get(chunk.get("chunk_id", ""), {}),
                config=resolved_config,
            )
        )
    return sorted(documents, key=lambda item: item["retrieval_doc_id"])


def build_retrieval_input_manifest(documents: Iterable[dict[str, Any]]) -> dict[str, Any]:
    entries = [
        {
            "retrieval_doc_id": item["retrieval_doc_id"],
            "retrieval_text_hash": item["retrieval_text_hash"],
            "retrieval_text_version": item["retrieval_text_version"],
        }
        for item in documents
    ]
    entries.sort(key=lambda item: item["retrieval_doc_id"])
    versions = sorted({item["retrieval_text_version"] for item in entries})
    if versions not in ([], [RETRIEVAL_TEXT_VERSION]):
        raise ValueError(f"Retrieval Document version 混用：{versions}")
    return {
        "schema_version": "retrieval_input_manifest_v1",
        "retrieval_text_version": RETRIEVAL_TEXT_VERSION,
        "document_count": len(entries),
        "input_manifest_hash": _sha256_text(_canonical_json(entries)),
        "entries": entries,
    }


def retrieval_input_for(
    document: dict[str, Any],
    component: str,
    *,
    manifest: dict[str, Any],
) -> dict[str, str]:
    if component not in SUPPORTED_COMPONENTS:
        raise ValueError(f"未知检索组件：{component}")
    if document.get("retrieval_text_version") != manifest.get("retrieval_text_version"):
        raise ValueError(f"{component} retrieval_text_version 与输入 manifest 不一致")
    text = document.get("retrieval_text")
    if not isinstance(text, str) or _sha256_text(text) != document.get("retrieval_text_hash"):
        raise ValueError(f"{component} retrieval_text 或 hash 非法")
    return {
        "component": component,
        "retrieval_doc_id": document["retrieval_doc_id"],
        "text": text,
        "retrieval_text_hash": document["retrieval_text_hash"],
        "retrieval_text_version": document["retrieval_text_version"],
        "input_manifest_hash": manifest["input_manifest_hash"],
    }


def embedding_cache_key(
    *,
    document: dict[str, Any],
    model: str,
    model_revision: str,
    normalization: str,
    provider_contract: str,
) -> str:
    payload = {
        "retrieval_text_hash": document["retrieval_text_hash"],
        "model": model,
        "model_revision": model_revision,
        "normalization": normalization,
        "provider_contract": provider_contract,
    }
    return _sha256_text(_canonical_json(payload))


def verify_component_input_manifests(component_hashes: dict[str, str]) -> str:
    missing = sorted(SUPPORTED_COMPONENTS - set(component_hashes))
    if missing:
        raise ValueError(f"缺少检索输入 manifest：{', '.join(missing)}")
    values = {component_hashes[name] for name in SUPPORTED_COMPONENTS}
    if len(values) != 1:
        details = ", ".join(f"{name}={component_hashes[name]}" for name in sorted(SUPPORTED_COMPONENTS))
        raise ValueError(f"检索输入 manifest 不一致：{details}")
    return values.pop()
