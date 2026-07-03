"""从 Canonical Block v2 纯派生稳定 section tree 与层级 chunk。"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import unicodedata

from .transformations import publishable_blocks


SPLITTABLE_BLOCK_TYPES = {"paragraph", "list_item"}
ATOMIC_BLOCK_TYPES = {"code", "formula", "table"}
NON_RETRIEVABLE_BLOCK_TYPES = {
    "picture", "caption", "footnote", "page_header", "page_footer", "unsupported"
}
STRUCTURAL_BLOCK_TYPES = {"title", "heading"}
KNOWN_BLOCK_TYPES = SPLITTABLE_BLOCK_TYPES | ATOMIC_BLOCK_TYPES | NON_RETRIEVABLE_BLOCK_TYPES | STRUCTURAL_BLOCK_TYPES


@dataclass(frozen=True)
class HierarchyResult:
    sections: list[dict]
    chunks: list[dict]
    excluded_blocks: list[dict]


def _normalized_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(" ".join(line.split()) for line in text.split("\n")).strip()


def build_section_id(doc_id: str, section_path: list[str], occurrence: int) -> str:
    """以文档、完整标题路径及同路径序号生成稳定身份。"""
    if not doc_id or occurrence < 1:
        raise ValueError("doc_id 不能为空且 occurrence 必须大于零")
    payload = json.dumps(
        [doc_id, [_normalized_text(item) for item in section_path], occurrence],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return "section_v2_" + hashlib.sha256(payload).hexdigest()


def _canonical_block_content(block: dict) -> dict:
    table = block.get("table")
    normalized_table = None
    if isinstance(table, dict):
        normalized_table = {
            "rows": int(table.get("rows", 0)),
            "columns": int(table.get("columns", 0)),
            "cells": [
                {
                    "row": int(cell.get("row", 0)),
                    "column": int(cell.get("column", 0)),
                    "row_span": int(cell.get("row_span", 1)),
                    "column_span": int(cell.get("column_span", 1)),
                    "text": _normalized_text(cell.get("text", "")),
                }
                for cell in table.get("cells", [])
            ],
        }
    return {
        "block_type": str(block.get("block_type", "")),
        "heading_level": block.get("heading_level"),
        "cleaned_text": _normalized_text(block.get("cleaned_text", "")),
        "table": normalized_table,
        "asset_refs": [str(item) for item in block.get("asset_refs", [])],
    }


def build_content_hash(blocks: list[dict]) -> str:
    """对 section 直属、有序、规范化块内容计算 hash。"""
    payload = json.dumps(
        [_canonical_block_content(block) for block in blocks],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _source_ref(block: dict) -> str:
    provenance = block.get("provenance", {})
    path = str(provenance.get("source_path", ""))
    anchor = str(provenance.get("source_anchor", ""))
    if not anchor:
        return path
    return path + (anchor if anchor.startswith("#") else "#" + anchor)


def _table_markdown(table: dict) -> str:
    rows = int(table.get("rows", 0))
    columns = int(table.get("columns", 0))
    if rows <= 0 or columns <= 0:
        return ""
    grid = [["" for _ in range(columns)] for _ in range(rows)]
    for cell in table.get("cells", []):
        row = int(cell.get("row", 0))
        column = int(cell.get("column", 0))
        if 0 <= row < rows and 0 <= column < columns:
            grid[row][column] = str(cell.get("text", "")).replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(row) + " |" for row in grid]
    lines.insert(1, "| " + " | ".join("---" for _ in range(columns)) + " |")
    return "\n".join(lines)


def _split_text(text: str, maximum_chars: int) -> list[str]:
    if maximum_chars < 1:
        raise ValueError("maximum_chunk_chars 必须大于零")
    if not text:
        return []
    parts = []
    remaining = text.strip()
    while len(remaining) > maximum_chars:
        boundary = remaining.rfind(" ", 0, maximum_chars + 1)
        if boundary <= 0:
            boundary = maximum_chars
        parts.append(remaining[:boundary].strip())
        remaining = remaining[boundary:].strip()
    if remaining:
        parts.append(remaining)
    return parts


def _chunk_id(doc_id: str, block_id: str, part_index: int, content: str) -> str:
    payload = f"{doc_id}|{block_id}|{part_index}|{content}".encode("utf-8")
    return "chunk_v2_" + hashlib.sha256(payload).hexdigest()


def _chunk_contents(block: dict, maximum_chunk_chars: int) -> list[str]:
    block_type = block.get("block_type")
    if block_type == "table":
        content = _table_markdown(block.get("table") or {})
    else:
        content = str(block.get("cleaned_text", "")).strip()
    if block_type in SPLITTABLE_BLOCK_TYPES:
        return _split_text(content, maximum_chunk_chars)
    return [content] if content else []


def build_hierarchy(document: dict, maximum_chunk_chars: int = 1200) -> HierarchyResult:
    """构建 section tree；输入文档保持不变。"""
    if maximum_chunk_chars < 1:
        raise ValueError("maximum_chunk_chars 必须大于零")
    doc_id = document.get("doc_id")
    if not doc_id:
        raise ValueError("document.doc_id 不能为空")
    approved = publishable_blocks(document.get("blocks", []))
    for block in approved:
        if not block.get("block_id") or block.get("doc_id") != doc_id:
            raise ValueError("publishable block 必须具有同文档的 block_id/doc_id")

    source_path = str(document.get("source", {}).get("source_path", ""))
    root_id = build_section_id(doc_id, [], 1)
    sections = [
        {
            "schema_version": "section_catalog_v1",
            "section_id": root_id,
            "content_hash": "",
            "doc_id": doc_id,
            "heading": "",
            "section_path": [],
            "section_order": 0,
            "parent_section_id": None,
            "child_section_ids": [],
            "previous_section_id": None,
            "next_section_id": None,
            "source_ref": source_path,
            "child_chunk_ids": [],
            "block_ids": [],
            "content_chars": 0,
            "estimated_tokens": 0,
        }
    ]
    direct_blocks: dict[str, list[dict]] = {root_id: []}
    direct_chunks: dict[str, list[dict]] = {root_id: []}
    current_section = sections[0]
    heading_stack: list[tuple[int, dict]] = []
    path_occurrences: Counter[tuple[str, ...]] = Counter()
    chunks = []
    excluded_blocks = []
    document_title = ""
    source_type = str(document.get("source", {}).get("source_type", "document"))

    for block in approved:
        block_type = block.get("block_type")
        heading = _normalized_text(block.get("cleaned_text", ""))
        if block_type in {"title", "heading"} and heading:
            level = int(block.get("heading_level") or (1 if block_type == "title" else 2))
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            parent = heading_stack[-1][1] if heading_stack else sections[0]
            section_path = [*parent["section_path"], heading]
            path_key = tuple(section_path)
            path_occurrences[path_key] += 1
            section_id = build_section_id(doc_id, section_path, path_occurrences[path_key])
            current_section = {
                "schema_version": "section_catalog_v1",
                "section_id": section_id,
                "content_hash": "",
                "doc_id": doc_id,
                "heading": heading,
                "section_path": section_path,
                "section_order": len(sections),
                "parent_section_id": parent["section_id"],
                "child_section_ids": [],
                "previous_section_id": None,
                "next_section_id": None,
                "source_ref": _source_ref(block) or source_path,
                "child_chunk_ids": [],
                "block_ids": [],
                "content_chars": 0,
                "estimated_tokens": 0,
            }
            parent["child_section_ids"].append(section_id)
            sections.append(current_section)
            direct_blocks[section_id] = []
            direct_chunks[section_id] = []
            heading_stack.append((level, current_section))
            if not document_title:
                document_title = heading
        current_section["block_ids"].append(block["block_id"])
        direct_blocks[current_section["section_id"]].append(block)

        if block_type in SPLITTABLE_BLOCK_TYPES | ATOMIC_BLOCK_TYPES:
            contents = _chunk_contents(block, maximum_chunk_chars)
            if not contents:
                excluded_blocks.append(
                    {"block_id": block["block_id"], "block_type": block_type, "reason": "empty_content"}
                )
            for part_index, content in enumerate(contents, start=1):
                sibling_chunks = direct_chunks[current_section["section_id"]]
                chunk = {
                    "schema_version": "chunk_v2_hierarchical",
                    "chunk_id": _chunk_id(doc_id, block["block_id"], part_index, content),
                    "doc_id": doc_id,
                    "source_type": source_type,
                    "title": document_title,
                    "section_path": list(current_section["section_path"]),
                    "chunk_type": f"canonical_{block_type}",
                    "topics": list(block.get("topics", [])),
                    "content": content,
                    "source_ref": _source_ref(block),
                    "source_block_ids": [block["block_id"]],
                    "language": block.get("language") or "und",
                    "review_status": "approved",
                    "parent_section_id": current_section["section_id"],
                    "chunk_order": len(sibling_chunks),
                    "previous_chunk_id": sibling_chunks[-1]["chunk_id"] if sibling_chunks else None,
                    "next_chunk_id": None,
                    "hierarchy_status": "resolved",
                }
                if sibling_chunks:
                    sibling_chunks[-1]["next_chunk_id"] = chunk["chunk_id"]
                sibling_chunks.append(chunk)
                chunks.append(chunk)
        elif block_type in NON_RETRIEVABLE_BLOCK_TYPES:
            excluded_blocks.append(
                {
                    "block_id": block["block_id"],
                    "block_type": block_type,
                    "reason": "asset_reference_only" if block_type == "picture" else "non_retrievable_block_type",
                }
            )
        elif block_type not in KNOWN_BLOCK_TYPES:
            excluded_blocks.append(
                {"block_id": block["block_id"], "block_type": block_type, "reason": "unknown_block_type"}
            )

    for index, section in enumerate(sections):
        section["previous_section_id"] = sections[index - 1]["section_id"] if index else None
        section["next_section_id"] = sections[index + 1]["section_id"] if index + 1 < len(sections) else None
        section["content_hash"] = build_content_hash(direct_blocks[section["section_id"]])
        section_chunks = direct_chunks[section["section_id"]]
        section["child_chunk_ids"] = [chunk["chunk_id"] for chunk in section_chunks]
        section["content_chars"] = sum(len(chunk["content"]) for chunk in section_chunks)
        section["estimated_tokens"] = (section["content_chars"] + 1) // 2
        if not section["source_ref"] and direct_blocks[section["section_id"]]:
            section["source_ref"] = _source_ref(direct_blocks[section["section_id"]][0])
        if not section["source_ref"]:
            raise ValueError("section source_ref 不能为空")

    return HierarchyResult(sections=sections, chunks=chunks, excluded_blocks=excluded_blocks)
