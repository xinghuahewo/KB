"""基于编号体系和文档顺序推断确定性标题层级。"""

from __future__ import annotations

import re


_METADATA_PREFIXES = (
    "Network Working Group",
    "Request for Comments:",
    "Obsoletes:",
    "Updates:",
    "Category:",
    "ISSN:",
)
_RFC_UNNUMBERED = {
    "Abstract",
    "Acknowledgements",
    "Copyright Notice",
    "IANA Considerations",
    "Introduction",
    "References",
    "Security Considerations",
    "Status of This Memo",
}
_CONTEXT_LEAF = {
    "Discussion:",
    "References:",
    "Joining requirements:",
    "Ongoing requirements:",
}


def _text(block):
    return " ".join(str(block.get("cleaned_text", "")).split())


def _docling_levels_are_reliable(blocks):
    headings = [block for block in blocks if block.get("block_type") in {"title", "heading"}]
    levels = [block.get("heading_level") for block in headings]
    if not levels or any(not isinstance(level, int) or not 1 <= level <= 6 for level in levels):
        return False
    if len(headings) > 1 and len(set(levels)) == 1:
        return False
    return all(right <= left + 1 for left, right in zip(levels, levels[1:]))


def _numbered_level(text):
    if re.match(r"^APPENDIX(?:\s+[A-Z0-9]+)?(?:\s|$)", text, flags=re.IGNORECASE):
        return 2, "appendix"
    match = re.match(r"^([IVXLCDM]+)[.)]\s+", text, flags=re.IGNORECASE)
    if match:
        return 2, "roman_section"
    match = re.match(r"^(\d+(?:\.\d+)*)(?:[.)])?\s+", text)
    if match:
        return min(6, 1 + len(match.group(1).split("."))), "arabic_section"
    if re.match(r"^[A-Z][.)]\s+", text):
        return 3, "letter_section"
    if re.match(r"^Action\s+\d+:\s+", text, flags=re.IGNORECASE):
        return 3, "named_action"
    if text in _CONTEXT_LEAF:
        return 4, "named_leaf"
    return None, None


def _fallback_candidates(blocks, source_format):
    if source_format == "txt":
        candidates = []
        title_found = False
        for block in blocks:
            text = _text(block)
            if not text:
                continue
            if (
                not title_found
                and 20 <= len(text) <= 120
                and not text.startswith(_METADATA_PREFIXES)
                and not re.match(r"^\d+(?:\.\d+)*[.)]?\s+", text)
            ):
                candidates.append((block, text, 1, "rfc_title"))
                title_found = True
                continue
            level, source = _numbered_level(text)
            if level is not None and len(text) <= 160 and "..." not in text:
                candidates.append((block, text, level, source))
            elif text in _RFC_UNNUMBERED:
                candidates.append((block, text, 2, "rfc_unnumbered"))
        return candidates
    if source_format in {"yaml", "yml"}:
        candidates = []
        for block in blocks:
            raw = str(block.get("cleaned_text", ""))
            title = re.search(r"^\s*title:\s*(.+)$", raw, flags=re.MULTILINE)
            if title and not any(row[2] == 1 for row in candidates):
                candidates.append(
                    (block, title.group(1).strip().strip("\"'"), 1, "yaml_title")
                )
            key = re.match(r"^([A-Za-z0-9_-]+):", raw)
            if key:
                candidates.append((block, key.group(1), 2, "yaml_key"))
        return candidates
    return []


def infer_heading_hierarchy(blocks, *, source_format):
    """返回标题候选，不修改输入 Block。"""
    reliable = _docling_levels_are_reliable(blocks)
    raw_candidates = []
    existing_headings = [
        block for block in blocks
        if block.get("block_type") in {"title", "heading"} and _text(block)
    ]
    if existing_headings:
        for index, block in enumerate(existing_headings):
            text = _text(block)
            inferred_level, inferred_source = _numbered_level(text)
            if reliable:
                level = int(block["heading_level"])
                source = "docling_level"
            elif index == 0:
                level, source = 1, "document_title"
            elif inferred_level is not None:
                level, source = inferred_level, inferred_source
            else:
                level, source = 2, "unnumbered_section"
            raw_candidates.append((block, text, level, source))
        existing_ids = {block["block_id"] for block in existing_headings}
        for block in blocks:
            if block.get("block_id") in existing_ids:
                continue
            text = _text(block)
            level, source = _numbered_level(text)
            if source in {"named_action", "named_leaf"}:
                raw_candidates.append((block, text, level, source))
        raw_candidates.sort(key=lambda row: row[0].get("reading_order", 0))
    else:
        raw_candidates = _fallback_candidates(blocks, source_format)

    stack = []
    result = []
    used_ids = set()
    for block, text, level, source in raw_candidates:
        level = max(1, min(6, int(level)))
        while stack and stack[-1][0] >= level:
            stack.pop()
        if level > 1 and not stack:
            level = 1
        elif stack and level > stack[-1][0] + 1:
            level = stack[-1][0] + 1
        base_id = str(block.get("block_id", ""))
        block_id = base_id
        if block_id in used_ids:
            block_id = f"{base_id}::{source}"
        used_ids.add(block_id)
        parent_block_id = stack[-1][1] if stack else None
        promoted = block.get("block_type") not in {"title", "heading"} or text != _text(block)
        candidate = {
            "block_id": block_id,
            "source_block_id": base_id,
            "text": text,
            "level": level,
            "parent_block_id": parent_block_id,
            "promoted": promoted,
            "confidence": 1.0 if source in {"docling_level", "arabic_section", "roman_section", "letter_section", "appendix"} else 0.95,
            "evidence": {
                "source": source,
                "docling_level": block.get("heading_level"),
                "docling_level_degenerated": bool(existing_headings and not reliable),
            },
        }
        result.append(candidate)
        stack.append((level, block_id))
    return result
