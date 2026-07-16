"""Canonical 语料迁移分类：元数据升级与 Docling 重处理分流。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from bgpkb.ingestion.canonical_contract import (
    canonical_processing_fingerprint,
    validate_canonical_document,
)
from bgpkb.ingestion.cleaning_v2.contracts import atomic_write_json


_LEGACY_BLOCK_FIELDS = {
    "block_id",
    "doc_id",
    "page_id",
    "parent_block_id",
    "block_type",
    "heading_level",
    "reading_order",
    "bbox",
    "raw_text",
    "cleaned_text",
    "language",
    "quality",
    "provenance",
    "review_status",
    "generated_by",
}


def _sha256_json(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _content_quality_status(review_status: object) -> str:
    if review_status in {"approved", "auto_approved"}:
        return "approved"
    if review_status in {"rejected", "quarantined"}:
        return str(review_status)
    return "pending_review"


def _strict_provenance(snapshot: dict, legacy: dict) -> dict:
    return {
        "source_snapshot_id": snapshot["snapshot_id"],
        "source_object_digest": snapshot["object_digest"],
        "source_anchor": str(legacy.get("source_anchor") or "#/unknown"),
    }


def _upgrade_diagnostic(diagnostic: dict) -> dict:
    message = diagnostic.get("message") or diagnostic.get("reason")
    if not message:
        message = json.dumps(diagnostic, ensure_ascii=False, sort_keys=True)
    severity = diagnostic.get("severity")
    if severity not in {"info", "warning", "error"}:
        severity = "warning"
    return {
        "code": str(diagnostic.get("code") or "legacy_diagnostic"),
        "severity": severity,
        "message": str(message),
        "source_anchor": diagnostic.get("source_anchor"),
        "block_id": diagnostic.get("block_id"),
    }


def upgrade_legacy_canonical_metadata(document: dict, source_snapshot: dict) -> dict:
    """只升级闭包元数据，保持旧 Block/asset 身份和内容不变。"""

    safe, reason = _legacy_metadata_upgrade_safe(document)
    if not safe:
        raise ValueError(f"Canonical 文档不能安全执行 metadata upgrade：{reason}")
    legacy_digest = str(document["source"]["source_sha256"])
    if source_snapshot.get("object_digest") != "sha256:" + legacy_digest:
        raise ValueError("source snapshot digest 与旧 Canonical source_sha256 不一致")
    if source_snapshot.get("source_id") != document["doc_id"]:
        raise ValueError("source snapshot source_id 与 Canonical doc_id 不一致")

    parser_mode = str(document.get("parser_mode") or "docling")
    legacy_runtime = document.get("runtime") if isinstance(document.get("runtime"), dict) else {}
    parser_name = "fallback" if parser_mode == "fallback" else "docling"
    parser_version = str(legacy_runtime.get("docling") or "unknown")
    runtime = {
        "schema_version": "canonical_runtime_v1",
        "pipeline_revision": str(legacy_runtime.get("pipeline_revision") or "legacy-metadata-upgrade-v1"),
        "parser": {"name": parser_name, "version": parser_version},
        "environment_fingerprint": _sha256_json(legacy_runtime),
    }
    config_fingerprint = _sha256_json({"migration": "canonical-metadata-upgrade-v1"})

    blocks = []
    for block in document["blocks"]:
        blocks.append({
            "block_id": block["block_id"],
            "doc_id": block["doc_id"],
            "page_id": block.get("page_id"),
            "page_number": block.get("page_number"),
            "parent_block_id": block.get("parent_block_id"),
            "block_type": block["block_type"],
            "heading_level": block.get("heading_level"),
            "reading_order": block["reading_order"],
            "bbox": block.get("bbox"),
            "raw_text": str(block.get("raw_text") or ""),
            "cleaned_text": str(block.get("cleaned_text") or ""),
            "language": block.get("language"),
            "quality": {
                "confidence": float(block.get("quality", {}).get("confidence", 0.0)),
                "ocr_used": bool(block.get("quality", {}).get("ocr_used", False)),
                "issues": [str(issue) for issue in block.get("quality", {}).get("issues", [])],
            },
            "provenance": _strict_provenance(source_snapshot, block.get("provenance", {})),
            "parse_status": "parsed",
            "content_quality_status": _content_quality_status(block.get("review_status")),
            "table": block.get("table"),
            "asset_refs": list(block.get("asset_refs", [])),
            "generated_by": str(block.get("generated_by") or "legacy-metadata-upgrade-v1"),
        })

    assets = []
    for asset in document.get("assets", []):
        assets.append({
            "asset_id": asset["asset_id"],
            "doc_id": asset["doc_id"],
            "asset_type": asset["asset_type"],
            "path": asset["path"],
            "sha256": asset["sha256"],
            "bbox": asset.get("bbox"),
            "caption": asset.get("caption"),
            "provenance": _strict_provenance(source_snapshot, asset.get("provenance", {})),
        })

    content_quality_status = (
        "pending_review"
        if document.get("document_status") == "pending_review"
        or any(block["content_quality_status"] != "approved" for block in blocks)
        else "approved"
    )
    upgraded = {
        "schema_version": "canonical_document_v2",
        "doc_id": document["doc_id"],
        "source": dict(source_snapshot),
        "runtime": runtime,
        "config_fingerprint": config_fingerprint,
        "processing_fingerprint": "",
        "parse_status": "parsed",
        "content_quality_status": content_quality_status,
        "blocks": blocks,
        "assets": assets,
        "diagnostics": [_upgrade_diagnostic(row) for row in document.get("diagnostics", [])],
        "parser_mode": parser_mode,
    }
    upgraded["processing_fingerprint"] = canonical_processing_fingerprint(
        upgraded["source"], upgraded["runtime"], upgraded["config_fingerprint"]
    )
    errors = validate_canonical_document(
        upgraded,
        known_snapshot_ids={source_snapshot["snapshot_id"]},
    )
    if errors:
        raise ValueError("metadata upgrade 后 Canonical 契约失败：" + "; ".join(errors))
    return upgraded


def _legacy_metadata_upgrade_safe(document: dict) -> tuple[bool, str]:
    if document.get("schema_version") != "canonical_document_v2":
        return False, "legacy_schema_version"
    doc_id = document.get("doc_id")
    source = document.get("source")
    blocks = document.get("blocks")
    if not isinstance(doc_id, str) or not doc_id:
        return False, "missing_doc_id"
    if not isinstance(source, dict) or source.get("doc_id") != doc_id:
        return False, "legacy_source_identity_invalid"
    digest = source.get("source_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        return False, "legacy_source_digest_invalid"
    if not isinstance(source.get("source_path"), str) or not source["source_path"]:
        return False, "legacy_source_path_invalid"
    if not isinstance(blocks, list):
        return False, "legacy_blocks_invalid"
    seen = set()
    for block in blocks:
        if not isinstance(block, dict) or not _LEGACY_BLOCK_FIELDS <= set(block):
            return False, "legacy_block_structure_invalid"
        block_id = block.get("block_id")
        if (
            not isinstance(block_id, str)
            or not block_id.startswith("block_v2_")
            or len(block_id) != len("block_v2_") + 64
            or block_id in seen
            or block.get("doc_id") != doc_id
        ):
            return False, "legacy_block_identity_invalid"
        seen.add(block_id)
    if any(block.get("parent_block_id") not in seen for block in blocks if block.get("parent_block_id")):
        return False, "legacy_block_parent_invalid"
    return True, "strict_metadata_upgrade_required"


def scan_canonical_corpus(root: Path, *, known_snapshot_ids: set[str] | None = None) -> dict:
    root = Path(root)
    valid = []
    metadata_upgrade = []
    docling_reprocess = []
    for path in sorted(root.glob("*.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            docling_reprocess.append({"doc_id": path.stem, "path": str(path), "reason": f"unreadable:{exc}"})
            continue
        doc_id = document.get("doc_id") or path.stem
        strict_errors = validate_canonical_document(document, known_snapshot_ids=known_snapshot_ids)
        if not strict_errors:
            valid.append({"doc_id": doc_id, "path": str(path)})
            continue
        safe, reason = _legacy_metadata_upgrade_safe(document)
        row = {"doc_id": doc_id, "path": str(path), "reason": reason, "strict_errors": strict_errors}
        if safe:
            metadata_upgrade.append(row)
        else:
            docling_reprocess.append(row)
    return {
        "schema_version": "canonical_migration_scan_v1",
        "root": str(root),
        "summary": {
            "documents": len(valid) + len(metadata_upgrade) + len(docling_reprocess),
            "valid": len(valid),
            "metadata_upgrade": len(metadata_upgrade),
            "docling_reprocess": len(docling_reprocess),
        },
        "valid_documents": valid,
        "metadata_upgrade_queue": metadata_upgrade,
        "docling_reprocess_queue": docling_reprocess,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="扫描 Canonical v2 并生成迁移分流报告")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fail-on-reprocess", action="store_true")
    args = parser.parse_args(argv)
    report = scan_canonical_corpus(args.root)
    atomic_write_json(args.output, report, indent=2)
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))
    return 1 if args.fail_on_reprocess and report["summary"]["docling_reprocess"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
