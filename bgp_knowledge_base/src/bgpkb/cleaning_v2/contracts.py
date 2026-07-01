"""Canonical Block v2 的稳定身份和轻量契约校验。"""

import hashlib
import json
import os
from pathlib import Path
import tempfile


REQUIRED_BLOCK_FIELDS = {
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


def build_block_id(doc_id, page_number, reading_order, block_type, source_anchor):
    payload = f"{doc_id}|{page_number}|{reading_order}|{block_type}|{source_anchor}"
    return f"block_v2_{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def valid_bbox(bbox):
    if bbox is None:
        return True
    required = {"left", "top", "right", "bottom", "coord_origin"}
    if not isinstance(bbox, dict) or not required <= set(bbox):
        return False
    coordinates = [bbox[key] for key in ("left", "top", "right", "bottom")]
    if any(not isinstance(value, (int, float)) for value in coordinates):
        return False
    left, top, right, bottom = coordinates
    return left <= right and top <= bottom and bbox["coord_origin"] in {"top_left", "bottom_left"}


def validate_blocks(blocks):
    errors = []
    seen = set()
    block_ids = {block.get("block_id") for block in blocks if block.get("block_id")}
    for block in blocks:
        missing = sorted(REQUIRED_BLOCK_FIELDS - set(block))
        if missing:
            errors.append("missing_fields:" + ",".join(missing))
        block_id = block.get("block_id", "")
        if block_id in seen:
            errors.append(f"duplicate_block_id:{block_id}")
        seen.add(block_id)
        if not valid_bbox(block.get("bbox")):
            errors.append(f"invalid_bbox:{block_id}")
        parent_id = block.get("parent_block_id")
        if parent_id and parent_id not in block_ids:
            errors.append(f"orphan_parent:{block_id}")
    return errors


def sort_blocks(blocks):
    return sorted(
        blocks,
        key=lambda block: (
            block.get("page_number") if block.get("page_number") is not None else 0,
            block.get("reading_order", 0),
            block.get("block_id", ""),
        ),
    )


def atomic_write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise
