"""从消息作用域内的已验证 citation 懒加载发布文档内容。"""

from __future__ import annotations

from typing import Any

from .chunk_store import ChunkStoreError
from .inline_citations import complete_sentence, current_release_id, published_chunk_store


MAX_RESPONSE_CHARS = 48_000


def evidence_detail(
    citation: dict[str, Any],
    *,
    scope: str = "section",
    cursor: int = 0,
    section_limit: int = 3,
) -> dict[str, Any]:
    snapshot_release = str(citation.get("release_id") or "unknown")
    active_release = current_release_id()
    base = {
        "citation": citation,
        "highlight_chunk_id": citation.get("chunk_id"),
        "snapshot_release_id": snapshot_release,
        "current_release_id": active_release,
        "release_mismatch": snapshot_release not in {"", "unknown", active_release},
        "scope": scope,
        "cursor": cursor,
        "available": False,
        "sections": [],
        "next_cursor": None,
    }
    try:
        store = published_chunk_store()
        chunk = store.get_chunk(str(citation.get("chunk_id") or ""))
        doc_id = str(chunk.get("doc_id") or citation.get("source_id") or "")
        section_id = str(citation.get("section_id") or chunk.get("parent_section_id") or "")
        if scope == "document":
            all_sections = store.list_sections_for_document(doc_id)
            selected = all_sections[cursor: cursor + section_limit]
            next_cursor = cursor + len(selected) if cursor + len(selected) < len(all_sections) else None
        else:
            selected = [store.get_section(section_id)] if section_id else []
            next_cursor = None
        sections = []
        remaining = MAX_RESPONSE_CHARS
        for section in selected:
            section_chunks = store.get_section_direct_chunks(section["section_id"])
            chunk_payloads = []
            for item in section_chunks:
                content = str(item.get("content") or item.get("content_preview") or "")
                if remaining <= 0:
                    break
                visible = content[:remaining]
                remaining -= len(visible)
                chunk_payloads.append({
                    "chunk_id": item.get("chunk_id"),
                    "content": visible,
                    "is_highlight": item.get("chunk_id") == citation.get("chunk_id"),
                })
            sections.append({
                "section_id": section.get("section_id"),
                "heading": section.get("heading") or citation.get("section_heading") or "相关章节",
                "chunks": chunk_payloads,
            })
            if remaining <= 0:
                break
        full_content = str(chunk.get("content") or chunk.get("content_preview") or "")
        current_sentence = complete_sentence(full_content, str(citation.get("content_preview") or ""))
        return {
            **base,
            "available": True,
            "source_id": doc_id,
            "complete_sentence": (
                citation.get("content_preview") or ""
                if base["release_mismatch"]
                else current_sentence
            ),
            "current_complete_sentence": current_sentence,
            "sections": sections,
            "next_cursor": next_cursor,
            "truncated_by_limit": remaining <= 0,
        }
    except (ChunkStoreError, FileNotFoundError, OSError, ValueError) as exc:
        return {
            **base,
            "error_code": getattr(exc, "code", "published_content_unavailable"),
            "error": str(exc),
            "complete_sentence": citation.get("content_preview") or "",
        }
