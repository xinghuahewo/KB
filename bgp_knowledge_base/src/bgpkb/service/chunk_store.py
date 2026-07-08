"""按发布 catalog 安全懒加载完整 chunk 与 section 子树。"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass
class ChunkStoreError(RuntimeError):
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ChunkStoreError("invalid_jsonl", f"{path} 第 {line_number} 行 JSON 非法：{exc}") from exc
    return rows


class ChunkStore:
    def __init__(self, project_root: Path | str, chunk_catalog_path: Path | str, section_catalog_path: Path | str):
        self.project_root = Path(project_root).resolve()
        self.chunk_catalog_path = self._resolve_path(chunk_catalog_path)
        self.section_catalog_path = self._resolve_path(section_catalog_path)
        self._chunk_catalog = {row.get("chunk_id"): row for row in _load_jsonl(self.chunk_catalog_path) if row.get("chunk_id")}
        self._sections = {row.get("section_id"): row for row in _load_jsonl(self.section_catalog_path) if row.get("section_id")}
        self._file_cache: dict[Path, dict[str, dict[str, Any]]] = {}

    def cache_stats(self) -> dict[str, int]:
        return {"loaded_chunk_files": len(self._file_cache)}

    def get_chunk(self, chunk_id: str) -> dict[str, Any]:
        catalog_row = self._chunk_catalog.get(chunk_id)
        if not catalog_row:
            raise ChunkStoreError("chunk_not_found", f"找不到 chunk：{chunk_id}")
        chunk_file = catalog_row.get("chunk_file")
        if not chunk_file:
            if catalog_row.get("content") is not None:
                return dict(catalog_row)
            raise ChunkStoreError("chunk_file_missing", f"chunk 缺少 chunk_file：{chunk_id}")
        path = self._resolve_path(chunk_file)
        file_rows = self._load_chunk_file(path)
        full_row = file_rows.get(chunk_id)
        if not full_row:
            raise ChunkStoreError("chunk_not_found", f"{path} 中找不到 chunk：{chunk_id}")
        return {**catalog_row, **full_row, "chunk_file": chunk_file}

    def get_section_direct_chunks(self, section_id: str) -> list[dict[str, Any]]:
        section = self._section(section_id)
        return self._chunks_for_ids(section.get("child_chunk_ids", []))

    def get_section_subtree_chunks(self, section_id: str) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []
        self._collect_section_chunks(section_id, chunks, seen_sections=set())
        return chunks

    def _section(self, section_id: str) -> dict[str, Any]:
        section = self._sections.get(section_id)
        if not section:
            raise ChunkStoreError("section_not_found", f"找不到 section：{section_id}")
        return section

    def _collect_section_chunks(self, section_id: str, chunks: list[dict[str, Any]], seen_sections: set[str]) -> None:
        if section_id in seen_sections:
            raise ChunkStoreError("section_cycle", f"section 子树存在环：{section_id}")
        seen_sections.add(section_id)
        section = self._section(section_id)
        chunks.extend(self._chunks_for_ids(section.get("child_chunk_ids", [])))
        for child_section_id in section.get("child_section_ids", []):
            self._collect_section_chunks(child_section_id, chunks, seen_sections)

    def _chunks_for_ids(self, chunk_ids: list[str]) -> list[dict[str, Any]]:
        chunks = [self.get_chunk(chunk_id) for chunk_id in chunk_ids]
        chunks.sort(key=lambda item: (int(item.get("chunk_order", 0)), item.get("chunk_id", "")))
        return chunks

    def _load_chunk_file(self, path: Path) -> dict[str, dict[str, Any]]:
        if path not in self._file_cache:
            self._file_cache[path] = {row.get("chunk_id"): row for row in _load_jsonl(path) if row.get("chunk_id")}
        return self._file_cache[path]

    def _resolve_path(self, path: Path | str) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.project_root / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.project_root)
        except ValueError as exc:
            raise ChunkStoreError("path_escape", f"路径越界：{path}") from exc
        return resolved
