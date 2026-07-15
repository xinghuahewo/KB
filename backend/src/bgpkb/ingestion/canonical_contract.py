"""Canonical Document v2 的生产契约与身份闭包校验。"""

from __future__ import annotations

import hashlib
import json

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from bgpkb import paths


DOCUMENT_SCHEMA_ID = "https://w3id.org/bgpkb/schema/canonical-document-v2.json"


class CanonicalContractError(ValueError):
    """生产输入不是闭合且严格的 Canonical Document v2。"""


def _schema_registry() -> tuple[dict, Registry]:
    registry = Registry()
    document_schema = None
    for schema_path in sorted(paths.SCHEMAS_DIR.glob("*.schema.json")):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        schema_id = schema.get("$id")
        if not schema_id:
            continue
        registry = registry.with_resource(schema_id, Resource.from_contents(schema))
        if schema_id == DOCUMENT_SCHEMA_ID:
            document_schema = schema
    if document_schema is None:
        raise CanonicalContractError(f"缺少 Canonical Document v2 Schema：{DOCUMENT_SCHEMA_ID}")
    return document_schema, registry


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_processing_fingerprint(source: dict, runtime: dict, config_fingerprint: str) -> str:
    """用内容快照、运行时和配置生成稳定处理指纹。"""

    identity = {
        "source": {
            "snapshot_id": source.get("snapshot_id"),
            "source_id": source.get("source_id"),
            "object_digest": source.get("object_digest"),
        },
        "runtime": runtime,
        "config_fingerprint": config_fingerprint,
    }
    return "sha256:" + hashlib.sha256(_canonical_json(identity)).hexdigest()


def _location(error) -> str:
    return "/" + "/".join(str(item) for item in error.absolute_path)


def validate_canonical_document(
    document: dict,
    *,
    known_snapshot_ids: set[str] | None = None,
) -> list[str]:
    """返回 Schema 与跨对象身份闭包错误；空列表表示可作生产输入。"""

    schema, registry = _schema_registry()
    validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
    errors = [
        f"schema:{_location(error)}:{error.message}"
        for error in sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
    ]
    source = document.get("source") if isinstance(document.get("source"), dict) else {}
    snapshot_id = source.get("snapshot_id")
    object_digest = source.get("object_digest")
    if known_snapshot_ids is not None and snapshot_id not in known_snapshot_ids:
        errors.append(f"source_snapshot_not_registered:{snapshot_id}")

    blocks = document.get("blocks") if isinstance(document.get("blocks"), list) else []
    assets = document.get("assets") if isinstance(document.get("assets"), list) else []
    block_ids = {row.get("block_id") for row in blocks if isinstance(row, dict)}
    asset_ids = {row.get("asset_id") for row in assets if isinstance(row, dict)}
    doc_id = document.get("doc_id")
    if source.get("source_id") != doc_id:
        errors.append(f"source_doc_id_mismatch:{doc_id}:{source.get('source_id')}")
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_id = block.get("block_id")
        if block.get("doc_id") != doc_id:
            errors.append(f"block_doc_id_mismatch:{block_id}")
        parent_id = block.get("parent_block_id")
        if parent_id is not None and parent_id not in block_ids:
            errors.append(f"orphan_parent:{block_id}:{parent_id}")
        for asset_id in block.get("asset_refs", []):
            if asset_id not in asset_ids:
                errors.append(f"asset_ref_not_found:{block_id}:{asset_id}")
        provenance = block.get("provenance") if isinstance(block.get("provenance"), dict) else {}
        if provenance.get("source_snapshot_id") != snapshot_id:
            errors.append(f"block_snapshot_mismatch:{block_id}")
        if provenance.get("source_object_digest") != object_digest:
            errors.append(f"block_source_digest_mismatch:{block_id}")
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        asset_id = asset.get("asset_id")
        if asset.get("doc_id") != doc_id:
            errors.append(f"asset_doc_id_mismatch:{asset_id}")
        provenance = asset.get("provenance") if isinstance(asset.get("provenance"), dict) else {}
        if provenance.get("source_snapshot_id") != snapshot_id:
            errors.append(f"asset_snapshot_mismatch:{asset_id}")
        if provenance.get("source_object_digest") != object_digest:
            errors.append(f"asset_source_digest_mismatch:{asset_id}")

    config_fingerprint = document.get("config_fingerprint")
    runtime = document.get("runtime")
    if source and isinstance(runtime, dict) and isinstance(config_fingerprint, str):
        expected = canonical_processing_fingerprint(source, runtime, config_fingerprint)
        if document.get("processing_fingerprint") != expected:
            errors.append("processing_fingerprint_mismatch")
    return errors


def is_canonical_stale(document: dict, source_snapshot: dict) -> bool:
    """来源身份或内容变更时，不复用旧 Canonical 结果。"""

    current = document.get("source", {})
    if current.get("snapshot_id") != source_snapshot.get("snapshot_id"):
        return True
    if current.get("object_digest") != source_snapshot.get("object_digest"):
        return True
    expected = canonical_processing_fingerprint(
        source_snapshot,
        document.get("runtime", {}),
        document.get("config_fingerprint", ""),
    )
    return document.get("processing_fingerprint") != expected


def require_production_canonical(
    document: dict,
    *,
    known_snapshot_ids: set[str] | None = None,
) -> dict:
    """拒绝 legacy 或未闭合文档，并返回原对象供下游只读使用。"""

    if document.get("schema_version") != "canonical_document_v2":
        raise CanonicalContractError("生产链路只接受 Canonical Document v2")
    errors = validate_canonical_document(document, known_snapshot_ids=known_snapshot_ids)
    if errors:
        raise CanonicalContractError("Canonical Document v2 校验失败：" + "; ".join(errors))
    return document
