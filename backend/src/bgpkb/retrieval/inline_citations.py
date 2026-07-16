"""结构化行内引用的 allowlist、完整句摘录与增量解析。"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
from typing import Any

from bgpkb import paths

from .chunk_store import ChunkStore, ChunkStoreError
from .retrieval_data import PublishedArtifactRetrievalData


MARKER_PREFIX = "[[cite:"
MARKER_SUFFIX = "]]"
MAX_MARKER_LENGTH = 160
SENTENCE_BOUNDARY = re.compile(r"(?<=[。！？!?\.])(?:\s+|(?=[A-Z\u4e00-\u9fff]))")


def current_release_id() -> str:
    configured = os.environ.get("BGPKB_RELEASE_ID")
    if configured:
        return configured
    try:
        manifest_path = paths.require_runtime_data_dir() / "published" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return str(manifest.get("release_id") or manifest.get("corpus_version") or "unknown")
    except Exception:
        return "unknown"


def published_chunk_store() -> ChunkStore:
    data = PublishedArtifactRetrievalData.from_environment()
    return ChunkStore(data.data_dir.parent, data.chunk_catalog_path(), data.section_catalog_path())


def enrich_citations(pack: dict[str, Any], store: ChunkStore | None = None) -> list[dict[str, Any]]:
    results = {str(item.get("chunk_id")): item for item in pack.get("results", []) if item.get("chunk_id")}
    unit_by_chunk: dict[str, dict[str, Any]] = {}
    for unit in pack.get("context_units", []) or []:
        for chunk_id in unit.get("included_chunk_ids", []) or []:
            unit_by_chunk[str(chunk_id)] = unit
    if store is None:
        try:
            store = published_chunk_store()
        except Exception:
            store = None

    enriched: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for raw in pack.get("citations", []) or []:
        chunk_id = str(raw.get("chunk_id") or raw.get("chunkId") or "")
        source_ref = str(raw.get("source_ref") or "")
        key = (chunk_id, source_ref)
        if not chunk_id or key in seen:
            continue
        seen.add(key)
        result = results.get(chunk_id, {})
        unit = unit_by_chunk.get(chunk_id, {})
        full_chunk: dict[str, Any] = {}
        if store is not None:
            try:
                full_chunk = store.get_chunk(chunk_id)
            except ChunkStoreError:
                pass
        source_id = str(
            raw.get("source_id")
            or result.get("source_id")
            or full_chunk.get("doc_id")
            or source_ref.split("#", 1)[0]
        )
        section_id = str(
            raw.get("section_id")
            or full_chunk.get("parent_section_id")
            or unit.get("parent_section_id")
            or ""
        )
        section_heading = str(
            raw.get("section_heading")
            or full_chunk.get("parent_section_heading")
            or unit.get("parent_section_heading")
            or ""
        )
        full_text = str(full_chunk.get("content") or unit.get("content") or "")
        preview = str(
            raw.get("content_preview")
            or result.get("content_preview")
            or full_chunk.get("content_preview")
            or full_text
        )
        enriched.append({
            **result,
            **raw,
            "citation_id": f"ev_{len(enriched) + 1}",
            "chunk_id": chunk_id,
            "source_id": source_id,
            "source_ref": source_ref,
            "title": raw.get("title") or result.get("title") or full_chunk.get("title") or source_id,
            "source_type": raw.get("source_type") or result.get("source_type") or full_chunk.get("source_type"),
            "section_id": section_id,
            "section_heading": section_heading,
            "content_preview": complete_sentence(full_text, preview),
            "context_snapshot": full_text or preview,
            "release_id": current_release_id(),
        })
    return enriched


def complete_sentence(full_text: str, preview: str) -> str:
    text = " ".join(str(full_text or "").split())
    hint = " ".join(str(preview or "").replace("…", "").split())
    if not text:
        return " ".join(str(preview or "").split())
    sentences = [sentence.strip() for sentence in SENTENCE_BOUNDARY.split(text) if sentence.strip()]
    if not sentences:
        return text
    needle = hint[:48].strip()
    if needle:
        for sentence in sentences:
            if needle in sentence or sentence[:32] in hint:
                return sentence
    return sentences[0]


def parse_answer(content: str, citations: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]], str]:
    parser = IncrementalCitationParser({citation["citation_id"] for citation in citations})
    tokens = parser.feed(content)
    tokens.extend(parser.finish())
    parts: list[dict[str, Any]] = []
    visible: list[str] = []
    labels = {citation["citation_id"]: str(index) for index, citation in enumerate(citations, start=1)}
    for token in tokens:
        if token["type"] == "text":
            if token["text"]:
                parts.append(token)
                visible.append(token["text"])
            continue
        citation_ids = token["citation_ids"]
        label = ",".join(labels[citation_id] for citation_id in citation_ids)
        part = {"type": "citation", "citation_ids": citation_ids, "label": label}
        parts.append(part)
        visible.append(f"[{label}]")
    status = parser.status
    if not any(part["type"] == "citation" for part in parts) and citations and status == "complete":
        status = "missing"
    return "".join(visible), parts, status


class IncrementalCitationParser:
    """在任意上游分片边界上安全解析 ``[[cite:ev_1]]``。"""

    def __init__(self, allowed_ids: set[str]):
        self.allowed_ids = allowed_ids
        self.buffer = ""
        self.invalid = False
        self.incomplete = False

    @property
    def status(self) -> str:
        if self.incomplete:
            return "incomplete"
        if self.invalid:
            return "invalid"
        return "complete"

    def feed(self, delta: str) -> list[dict[str, Any]]:
        self.buffer += delta
        output: list[dict[str, Any]] = []
        while self.buffer:
            start = self.buffer.find(MARKER_PREFIX)
            if start < 0:
                keep = self._prefix_suffix_length(self.buffer)
                emit_text = self.buffer[:-keep] if keep else self.buffer
                if emit_text:
                    output.append({"type": "text", "text": emit_text})
                self.buffer = self.buffer[-keep:] if keep else ""
                break
            if start > 0:
                output.append({"type": "text", "text": self.buffer[:start]})
                self.buffer = self.buffer[start:]
            end = self.buffer.find(MARKER_SUFFIX, len(MARKER_PREFIX))
            if end < 0:
                if len(self.buffer) > MAX_MARKER_LENGTH:
                    self.invalid = True
                    self.buffer = self.buffer[len(MARKER_PREFIX):]
                    continue
                break
            raw_ids = self.buffer[len(MARKER_PREFIX):end]
            self.buffer = self.buffer[end + len(MARKER_SUFFIX):]
            citation_ids = [item.strip() for item in raw_ids.split(",") if item.strip()]
            if citation_ids and all(item in self.allowed_ids for item in citation_ids):
                output.append({"type": "citation", "citation_ids": citation_ids})
            else:
                self.invalid = True
        return _merge_text_tokens(output)

    def finish(self) -> list[dict[str, Any]]:
        if not self.buffer:
            return []
        if self.buffer.startswith(MARKER_PREFIX) or self._prefix_suffix_length(self.buffer) == len(self.buffer):
            self.incomplete = True
            self.buffer = ""
            return []
        text = self.buffer
        self.buffer = ""
        return [{"type": "text", "text": text}]

    @staticmethod
    def _prefix_suffix_length(value: str) -> int:
        maximum = min(len(value), len(MARKER_PREFIX) - 1)
        for length in range(maximum, 0, -1):
            if value.endswith(MARKER_PREFIX[:length]):
                return length
        return 0


def _merge_text_tokens(tokens: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for token in tokens:
        if token["type"] == "text" and merged and merged[-1]["type"] == "text":
            merged[-1]["text"] += token["text"]
        else:
            merged.append(token)
    return merged
