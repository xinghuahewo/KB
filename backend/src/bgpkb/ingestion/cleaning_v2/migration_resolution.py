"""构建经过显式审核的 legacy-preservation 文档与迁移决策。"""

from __future__ import annotations

import hashlib
import json
import re

from .contracts import build_block_id


GENERATED_BY = "src/bgpkb/cleaning_v2/migration_resolution.py"


def _stable_id(prefix, payload):
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return prefix + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _markdown_items(markdown):
    items = []
    paragraph = []
    paragraph_start = None

    def flush():
        nonlocal paragraph, paragraph_start
        text = "\n".join(paragraph).strip()
        if text:
            items.append((paragraph_start, "paragraph", None, text))
        paragraph = []
        paragraph_start = None

    for line_number, line in enumerate(markdown.splitlines(), start=1):
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        list_item = re.match(r"^\s*[-*+]\s+(.+?)\s*$", line)
        if heading:
            flush()
            level = len(heading.group(1))
            items.append((line_number, "title" if level == 1 and not items else "heading", level, heading.group(2)))
        elif list_item:
            flush()
            items.append((line_number, "list_item", None, list_item.group(1)))
        elif line.strip():
            if paragraph_start is None:
                paragraph_start = line_number
            paragraph.append(line)
        else:
            flush()
    flush()
    return items


def build_legacy_preservation_document(
    *, doc_id, markdown, source_meta, runtime_meta, reviewer, reviewed_at
):
    """把历史 cleaned Markdown 转成可追溯、已审核的 Canonical Block。"""
    blocks = []
    decisions = []
    heading_stack = []
    source_sha = str(source_meta.get("source_sha256", ""))
    fingerprint = source_sha if re.fullmatch(r"[0-9a-f]{64}", source_sha) else hashlib.sha256(source_sha.encode()).hexdigest()
    for reading_order, (line_number, block_type, level, text) in enumerate(_markdown_items(markdown)):
        source_anchor = f"#legacy-cleaned-L{line_number}"
        block_id = build_block_id(doc_id, None, reading_order, block_type, source_anchor)
        if block_type in {"title", "heading"}:
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            parent_block_id = heading_stack[-1][1] if heading_stack else None
            heading_stack.append((level, block_id))
        else:
            parent_block_id = heading_stack[-1][1] if heading_stack else None
        block = {
            "block_id": block_id,
            "doc_id": doc_id,
            "page_id": None,
            "page_number": None,
            "parent_block_id": parent_block_id,
            "block_type": block_type,
            "heading_level": level,
            "reading_order": reading_order,
            "bbox": None,
            "raw_text": text,
            "cleaned_text": text,
            "language": None,
            "quality": {
                "confidence": 1.0,
                "ocr_used": False,
                "issues": ["fallback_parser"],
                "fallback_reviewed": True,
            },
            "provenance": {
                "source_path": source_meta["source_path"],
                "source_sha256": source_sha,
                "parser": {"name": "deterministic_v1_import", "version": "v1"},
                "runtime": dict(runtime_meta),
                "source_anchor": source_anchor,
                "native_text": text,
                "ocr_text": None,
            },
            "review_status": "approved",
            "asset_refs": [],
            "generated_by": GENERATED_BY,
        }
        blocks.append(block)
        decisions.append(
            {
                "decision_id": _stable_id(
                    "decision_v2_", [doc_id, block_id, "approved", reviewer, reviewed_at, fingerprint]
                ),
                "block_id": block_id,
                "decision": "approved",
                "reviewer": reviewer,
                "reviewed_at": reviewed_at,
                "input_fingerprint": fingerprint,
                "note": "用户批准 legacy-preservation 迁移策略。",
            }
        )
    document = {
        "schema_version": "canonical_document_v2",
        "doc_id": doc_id,
        "source": dict(source_meta),
        "runtime": dict(runtime_meta),
        "blocks": blocks,
        "assets": [],
        "diagnostics": [
            {
                "code": "legacy_preservation_fallback",
                "reason": "Docling 正文覆盖不足，使用已审核 v1 cleaned Markdown 保全正文。",
            }
        ],
        "parser_mode": "fallback",
        "fallback_reason": "docling_body_coverage_below_threshold",
        "fallback_review_status": "approved",
        "document_status": "approved",
        "transformations": [],
        "review_items": [],
    }
    return document, decisions


def build_migration_decision(
    *, doc_id, strategy, reason_code, v1_digest, v2_digest, reviewer, reviewed_at
):
    payload = [doc_id, strategy, reason_code, v1_digest, v2_digest, reviewer, reviewed_at]
    return {
        "decision_id": _stable_id("migration_decision_v2_", payload),
        "doc_id": doc_id,
        "strategy": strategy,
        "decision": "approved",
        "reason_code": reason_code,
        "reviewer": reviewer,
        "reviewed_at": reviewed_at,
        "evidence": {"v1_digest": v1_digest, "v2_digest": v2_digest},
        "generated_by": GENERATED_BY,
    }
