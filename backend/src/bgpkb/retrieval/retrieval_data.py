"""Published-artifact access boundary for retrieval and context assembly."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Protocol

from bgpkb import paths


class RetrievalData(Protocol):
    def database_path(self) -> Path: ...

    def vector_index_path(self) -> Path: ...

    def chunk_catalog_path(self) -> Path: ...

    def section_catalog_path(self) -> Path: ...

    def trusted_chunk_ids(self) -> set[str]: ...

    def eligible_doc_ids(self) -> set[str]: ...

    def excluded_by_policy(self) -> list[dict]: ...


def _load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"发布制品缺少必需数据文件：{path}")
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


@dataclass(frozen=True)
class PublishedArtifactRetrievalData:
    data_dir: Path

    @classmethod
    def from_environment(cls) -> "PublishedArtifactRetrievalData":
        return cls(paths.require_runtime_data_dir())

    def published_path(self, filename: str) -> Path:
        return self.data_dir / "published" / filename

    def dataset_path(self, filename: str) -> Path:
        return self.data_dir / "derived" / "datasets" / filename

    def _required(self, path: Path) -> Path:
        if not path.is_file():
            raise FileNotFoundError(f"发布制品缺少必需数据文件：{path}")
        return path

    def database_path(self) -> Path:
        return self._required(self.published_path("bgp_knowledge_base.sqlite"))

    def vector_index_path(self) -> Path:
        return self._required(self.published_path("bge_m3_vector_index.jsonl"))

    def chunk_catalog_path(self) -> Path:
        return self._required(self.published_path("chunk_catalog.jsonl"))

    def section_catalog_path(self) -> Path:
        dataset_path = self.dataset_path("section_catalog.jsonl")
        if dataset_path.is_file():
            return dataset_path
        return self._required(self.published_path("section_catalog.jsonl"))

    def trusted_chunk_ids(self) -> set[str]:
        trusted: set[str] = set()
        for item in _load_jsonl(self.dataset_path("entity_source_evidence.jsonl")):
            if item.get("entity_review_status") == "approved":
                trusted.update(item.get("chunk_sample_ids", []))
        return trusted

    def eligible_doc_ids(self) -> set[str]:
        return {
            item.get("source_id", "")
            for item in _load_jsonl(self.published_path("source_catalog.jsonl"))
            if item.get("processing_status") == "complete_deterministic"
            and item.get("trust_level") in {"high", "medium"}
        }

    def excluded_by_policy(self) -> list[dict]:
        excluded = []
        for entity in _load_jsonl(self.published_path("entity_catalog.jsonl")):
            status = entity.get("review_status", "")
            if status != "approved":
                excluded.append({
                    "entity_id": entity.get("entity_id", ""),
                    "reason": "not_approved",
                    "review_status": status,
                })
        return excluded
