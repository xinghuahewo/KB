"""把 Docling lossless JSON 映射为项目 Canonical Document v2。"""

import hashlib

from bgpkb.ingestion.cleaning_v2.contracts import build_block_id, sort_blocks


GENERATED_BY = "src/bgpkb/cleaning_v2/docling_adapter.py"
LABEL_TO_BLOCK_TYPE = {
    "title": "title",
    "section_header": "heading",
    "text": "paragraph",
    "paragraph": "paragraph",
    "list_item": "list_item",
    "code": "code",
    "formula": "formula",
    "picture": "picture",
    "table": "table",
    "caption": "caption",
    "footnote": "footnote",
    "page_header": "page_header",
    "page_footer": "page_footer",
}


class DoclingParseError(RuntimeError):
    """Docling 受控解析失败。"""


def _index_payload(payload):
    index = {}
    for collection in payload.values():
        if not isinstance(collection, list):
            continue
        for item in collection:
            if isinstance(item, dict) and item.get("self_ref"):
                index[item["self_ref"]] = item
    return index


def _reading_items(payload, index):
    def expand(reference):
        item = index.get(reference)
        if item is None:
            return [{"self_ref": reference, "label": "missing_reference"}]
        if reference.startswith("#/groups/"):
            expanded = []
            for child in item.get("children", []):
                expanded.extend(expand(child.get("$ref", "")))
            return expanded
        return [item]

    mounted_items = []
    for child in payload.get("body", {}).get("children", []):
        mounted_items.extend(expand(child.get("$ref", "")))

    items = [
        item
        for item in mounted_items
        if item.get("content_layer") != "furniture"
    ]
    seen = {item.get("self_ref") for item in items if item.get("self_ref")}
    recovered = []
    for collection_name, collection in payload.items():
        if collection_name == "groups" or not isinstance(collection, list):
            continue
        for item in collection:
            if not isinstance(item, dict):
                continue
            source_anchor = item.get("self_ref")
            if (
                item.get("content_layer") == "body"
                and source_anchor
                and source_anchor not in seen
            ):
                items.append(item)
                recovered.append(source_anchor)
                seen.add(source_anchor)
    return items, recovered


def _page_and_bbox(item):
    provenance = item.get("prov") or []
    if not provenance:
        return None, None
    first = provenance[0]
    raw_bbox = first.get("bbox")
    bbox = None
    if raw_bbox:
        bbox = {
            "left": float(raw_bbox["l"]),
            "top": float(raw_bbox["t"]),
            "right": float(raw_bbox["r"]),
            "bottom": float(raw_bbox["b"]),
            "coord_origin": str(raw_bbox.get("coord_origin", "TOPLEFT")).lower().replace("bottomleft", "bottom_left").replace("topleft", "top_left"),
        }
    return first.get("page_no"), bbox


def _caption(item, index):
    captions = item.get("captions") or []
    if not captions:
        return None
    caption = index.get(captions[0].get("$ref", ""), {})
    return caption.get("text") or caption.get("orig")


def _table(item, block_id, page_number, index):
    data = item.get("data") or {}
    cells = []
    for cell in data.get("table_cells", []):
        start_row = cell.get("start_row_offset_idx", 0)
        end_row = cell.get("end_row_offset_idx", start_row + 1)
        start_col = cell.get("start_col_offset_idx", 0)
        end_col = cell.get("end_col_offset_idx", start_col + 1)
        cells.append(
            {
                "text": cell.get("text", ""),
                "row": start_row,
                "column": start_col,
                "row_span": max(1, end_row - start_row),
                "column_span": max(1, end_col - start_col),
                "column_header": bool(cell.get("column_header")),
                "row_header": bool(cell.get("row_header")),
            }
        )
    return {
        "table_id": f"table_{block_id.removeprefix('block_v2_')}",
        "rows": data.get("num_rows", 0),
        "columns": data.get("num_cols", 0),
        "cells": cells,
        "source_pages": [page_number] if page_number is not None else [],
        "caption": _caption(item, index),
    }


def _asset(item, doc_id, bbox, index):
    image = item.get("image") or {}
    if not image.get("path") or not image.get("sha256"):
        return None
    payload = f"{doc_id}|{item.get('self_ref', '')}|{image['path']}"
    asset_id = f"asset_v2_{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"
    return {
        "asset_id": asset_id,
        "doc_id": doc_id,
        "asset_type": "picture",
        "path": image["path"],
        "sha256": image["sha256"],
        "bbox": bbox,
        "caption": _caption(item, index),
        "provenance": {"source_anchor": item.get("self_ref", "")},
    }


def adapt_docling_document(docling_payload, source_meta, runtime_meta, config):
    del config
    doc_id = source_meta["doc_id"]
    index = _index_payload(docling_payload)
    items, recovered_body_items = _reading_items(docling_payload, index)
    blocks = []
    assets = []
    diagnostics = []
    if recovered_body_items:
        diagnostics.append(
            {
                "code": "unmounted_body_items_recovered",
                "count": len(recovered_body_items),
                "source_anchors": recovered_body_items,
            }
        )
    heading_stack = []

    for reading_order, item in enumerate(items):
        source_anchor = item.get("self_ref", "")
        label = item.get("label", "")
        block_type = LABEL_TO_BLOCK_TYPE.get(label, "unsupported")
        page_number, bbox = _page_and_bbox(item)
        block_id = build_block_id(doc_id, page_number, reading_order, block_type, source_anchor)
        heading_level = item.get("level") if block_type in {"title", "heading"} else None

        if block_type in {"title", "heading"}:
            heading_level = heading_level or (1 if block_type == "title" else 2)
            while heading_stack and heading_stack[-1][0] >= heading_level:
                heading_stack.pop()
            parent_block_id = heading_stack[-1][1] if heading_stack else None
            heading_stack.append((heading_level, block_id))
        else:
            parent_block_id = heading_stack[-1][1] if heading_stack else None

        raw_text = item.get("orig", item.get("text", "")) or ""
        cleaned_text = item.get("text", raw_text) or ""
        review_status = "auto_approved"
        quality_issues = []
        if block_type == "unsupported":
            review_status = "quarantined"
            quality_issues.append("unsupported_block_type")
            diagnostics.append(
                {
                    "code": "unsupported_block_type",
                    "source_anchor": source_anchor,
                    "label": label,
                    "block_id": block_id,
                }
            )

        block = {
            "block_id": block_id,
            "doc_id": doc_id,
            "page_id": f"{doc_id}_page_{page_number}" if page_number is not None else None,
            "page_number": page_number,
            "parent_block_id": parent_block_id,
            "block_type": block_type,
            "heading_level": heading_level,
            "reading_order": reading_order,
            "bbox": bbox,
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "language": item.get("language"),
            "quality": {
                "confidence": float(item.get("confidence", 1.0)),
                "ocr_used": bool(item.get("ocr_used", False)),
                "issues": quality_issues,
            },
            "provenance": {
                "source_path": source_meta["source_path"],
                "source_sha256": source_meta["source_sha256"],
                "parser": {"name": runtime_meta.get("parser", "docling"), "version": runtime_meta.get("docling_version", "")},
                "runtime": dict(runtime_meta),
                "source_anchor": source_anchor,
                "native_text": item.get("native_text"),
                "ocr_text": item.get("ocr_text"),
            },
            "review_status": review_status,
            "asset_refs": [],
            "generated_by": GENERATED_BY,
        }

        if block_type == "table":
            block["table"] = _table(item, block_id, page_number, index)
        if block_type == "picture":
            asset = _asset(item, doc_id, bbox, index)
            if asset:
                assets.append(asset)
                block["asset_refs"] = [asset["asset_id"]]
            else:
                block["review_status"] = "pending_review"
                block["quality"]["issues"].append("picture_asset_missing")
        blocks.append(block)

    return {
        "schema_version": "canonical_document_v2",
        "doc_id": doc_id,
        "source": dict(source_meta),
        "runtime": dict(runtime_meta),
        "blocks": sort_blocks(blocks),
        "assets": sorted(assets, key=lambda asset: asset["asset_id"]),
        "diagnostics": sorted(
            diagnostics,
            key=lambda row: (row.get("source_anchor", ""), row["code"]),
        ),
        "parser_mode": "docling",
        "fallback_reason": None,
        "fallback_review_status": "not_applicable",
        "document_status": "parsed",
    }


def _adapt_fallback_document(parsed_document, source_meta, runtime_meta, reason):
    doc_id = source_meta["doc_id"]
    blocks = []
    for reading_order, section in enumerate(parsed_document.get("sections", [])):
        source_anchor = f"#/sections/{section.get('section_id', reading_order)}"
        block_id = build_block_id(doc_id, None, reading_order, "paragraph", source_anchor)
        text = section.get("content", "")
        blocks.append(
            {
                "block_id": block_id,
                "doc_id": doc_id,
                "page_id": None,
                "page_number": None,
                "parent_block_id": None,
                "block_type": "paragraph",
                "heading_level": None,
                "reading_order": reading_order,
                "bbox": None,
                "raw_text": text,
                "cleaned_text": text,
                "language": None,
                "quality": {"confidence": 0.0, "ocr_used": False, "issues": ["fallback_parser"]},
                "provenance": {
                    "source_path": source_meta["source_path"],
                    "source_sha256": source_meta["source_sha256"],
                    "parser": {"name": "deterministic_v1", "version": "v1"},
                    "runtime": dict(runtime_meta),
                    "source_anchor": source_anchor,
                    "native_text": text,
                    "ocr_text": None,
                },
                "review_status": "pending_review",
                "asset_refs": [],
                "generated_by": GENERATED_BY,
            }
        )
    return {
        "schema_version": "canonical_document_v2",
        "doc_id": doc_id,
        "source": dict(source_meta),
        "runtime": dict(runtime_meta),
        "blocks": blocks,
        "assets": [],
        "diagnostics": [{"code": "fallback_parser", "reason": reason}],
        "parser_mode": "fallback",
        "fallback_reason": reason,
        "fallback_review_status": "pending_review",
        "document_status": "pending_review",
    }


def parse_with_explicit_fallback(
    source,
    source_meta,
    runtime_meta,
    config,
    docling_parser,
    fallback_parser,
    *,
    allow_fallback=False,
    payload_preprocessor=None,
):
    try:
        payload = docling_parser(source)
    except DoclingParseError as exc:
        fallback_enabled = bool(config.get("fallback", {}).get("enabled"))
        if not allow_fallback or not fallback_enabled:
            return {
                "schema_version": "canonical_document_v2",
                "doc_id": source_meta["doc_id"],
                "source": dict(source_meta),
                "runtime": dict(runtime_meta),
                "blocks": [],
                "assets": [],
                "diagnostics": [{"code": "docling_parse_failed", "reason": str(exc)}],
                "parser_mode": "docling_failed",
                "fallback_reason": str(exc),
                "fallback_review_status": "not_applicable",
                "document_status": "quarantined",
            }
        parsed_document, _text = fallback_parser(source, source_meta["doc_id"])
        return _adapt_fallback_document(parsed_document, source_meta, runtime_meta, str(exc))
    if payload_preprocessor is not None:
        payload_preprocessor(payload)
    return adapt_docling_document(payload, source_meta, runtime_meta, config)


def publishable_blocks(document):
    if document.get("parser_mode") == "fallback" and document.get("fallback_review_status") != "approved":
        return []
    return [
        block
        for block in document.get("blocks", [])
        if block.get("review_status") in {"auto_approved", "approved"}
    ]
