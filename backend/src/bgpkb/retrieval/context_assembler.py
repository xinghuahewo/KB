"""按 query_type 组装阶段 B 层级 context pack。"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from bgpkb.domain.token_budget import TokenCounter, parent_budget


QUERY_POLICIES = {
    "fact": {"window": 1, "promotion": False},
    "procedure": {"window": 2, "promotion": True},
    "policy": {"window": 2, "promotion": True},
    "global": {"window": 1, "promotion": True},
}


@dataclass
class ContextAssembler:
    store: Any
    token_counter: Any | None = None
    summarizer: Any | None = None

    def __post_init__(self):
        if self.token_counter is None:
            self.token_counter = TokenCounter()

    def build(self, query: str, reranked_chunks: list[dict[str, Any]], query_type: str, token_budget: int = 6000) -> dict[str, Any]:
        if query_type not in QUERY_POLICIES:
            raise ValueError("query_type 必须是 fact/procedure/policy/global")
        hits, trim_events = self._load_and_dedupe_hits(reranked_chunks)
        grouped: dict[str, list[dict[str, Any]]] = {}
        for hit in hits:
            grouped.setdefault(hit["parent_section_id"], []).append(hit)

        units = []
        for section_id, section_hits in grouped.items():
            units.append(self._build_section_unit(query, query_type, section_id, section_hits, token_budget))
        units.sort(key=lambda unit: (-float(unit["max_rerank_score"] or 0.0), unit["doc_id"], unit["parent_section_id"]))

        units = self._apply_budget(query, units, token_budget, trim_events)
        return {
            "schema_version": "context_pack_v2",
            "query": query,
            "requested_query_type": query_type,
            "resolved_query_type": query_type,
            "token_budget": token_budget,
            "context_units": units,
            "trim_events": trim_events,
        }

    def _load_and_dedupe_hits(self, reranked_chunks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        trim_events: list[dict[str, Any]] = []
        by_chunk: dict[str, dict[str, Any]] = {}
        for index, hit in enumerate(reranked_chunks):
            chunk_id = hit.get("chunk_id")
            if not chunk_id:
                continue
            chunk = {**self.store.get_chunk(chunk_id), **hit}
            chunk["_hit_order"] = index
            chunk["_hit_score"] = _score(chunk)
            previous = by_chunk.get(chunk_id)
            if previous is None or chunk["_hit_score"] > previous["_hit_score"]:
                by_chunk[chunk_id] = chunk
        by_blocks: dict[tuple[str, ...], dict[str, Any]] = {}
        for chunk in by_chunk.values():
            block_key = tuple(sorted(chunk.get("source_block_ids") or []))
            if not block_key:
                by_blocks[(chunk["chunk_id"],)] = chunk
                continue
            previous = by_blocks.get(block_key)
            if previous is None or chunk["_hit_score"] > previous["_hit_score"]:
                if previous is not None:
                    trim_events.append({
                        "event": "dedupe_by_block_set",
                        "removed_chunk_id": previous["chunk_id"],
                        "kept_chunk_id": chunk["chunk_id"],
                    })
                by_blocks[block_key] = chunk
            else:
                trim_events.append({
                    "event": "dedupe_by_block_set",
                    "removed_chunk_id": chunk["chunk_id"],
                    "kept_chunk_id": previous["chunk_id"],
                })
        return sorted(by_blocks.values(), key=lambda item: item.get("rerank_rank") or item["_hit_order"]), trim_events

    def _build_section_unit(self, query: str, query_type: str, section_id: str, hits: list[dict[str, Any]], token_budget: int) -> dict[str, Any]:
        policy = QUERY_POLICIES[query_type]
        section = self.store.get_section(section_id)
        mode = "matched_chunk"
        chunks = self._window_chunks(section_id, hits, policy["window"])

        if query_type in {"policy", "global"} and self._can_use_full_section(query_type, section_id, token_budget):
            mode = "full_section"
            chunks = self.store.get_section_subtree_chunks(section_id)
        elif policy["promotion"] and len(hits) >= 2:
            mode = "parent_span"

        unit = self._unit_from_chunks(mode, section, chunks, hits)
        if query_type == "global" and unit["estimated_tokens"] > token_budget and self.summarizer is not None:
            return self._summarize_unit(query, unit)
        return unit

    def _window_chunks(self, section_id: str, hits: list[dict[str, Any]], sibling_window: int) -> list[dict[str, Any]]:
        direct = self.store.get_section_direct_chunks(section_id)
        by_id = {chunk["chunk_id"]: chunk for chunk in direct}
        selected: dict[str, dict[str, Any]] = {}
        hit_orders = [by_id[hit["chunk_id"]]["chunk_order"] for hit in hits if hit["chunk_id"] in by_id]
        for chunk in direct:
            order = int(chunk.get("chunk_order", 0))
            if any(abs(order - int(hit_order)) <= sibling_window for hit_order in hit_orders):
                selected[chunk["chunk_id"]] = chunk
        if not selected:
            selected = {hit["chunk_id"]: self.store.get_chunk(hit["chunk_id"]) for hit in hits}
        chunks = sorted(selected.values(), key=lambda item: (int(item.get("chunk_order", 0)), item.get("chunk_id", "")))
        return self._dedupe_chunks_by_blocks(chunks, hits)

    def _dedupe_chunks_by_blocks(self, chunks: list[dict[str, Any]], hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        hit_score = {hit["chunk_id"]: hit["_hit_score"] for hit in hits}
        by_blocks: dict[tuple[str, ...], dict[str, Any]] = {}
        for chunk in chunks:
            block_key = tuple(sorted(chunk.get("source_block_ids") or [])) or (chunk["chunk_id"],)
            current_score = hit_score.get(chunk["chunk_id"], -1.0)
            previous = by_blocks.get(block_key)
            previous_score = hit_score.get(previous["chunk_id"], -1.0) if previous else -1.0
            if previous is None or current_score > previous_score:
                by_blocks[block_key] = chunk
        return sorted(by_blocks.values(), key=lambda item: (int(item.get("chunk_order", 0)), item.get("chunk_id", "")))

    def _can_use_full_section(self, query_type: str, section_id: str, token_budget: int) -> bool:
        budget = parent_budget(query_type, token_budget)
        chunks = self.store.get_section_subtree_chunks(section_id)
        return self._chunks_tokens(chunks) <= budget.per_parent

    def _chunks_tokens(self, chunks: list[dict[str, Any]]) -> int:
        return self.token_counter.count(_content(chunks)).tokens

    def _unit_from_chunks(self, mode: str, section: dict[str, Any], chunks: list[dict[str, Any]], hits: list[dict[str, Any]]) -> dict[str, Any]:
        content = _content(chunks)
        count = self.token_counter.count(content)
        included_chunk_ids = [chunk["chunk_id"] for chunk in chunks]
        citations = [
            {"chunk_id": chunk["chunk_id"], "source_ref": chunk.get("source_ref", "")}
            for chunk in chunks if chunk.get("source_ref")
        ]
        if len(citations) != len(chunks):
            raise ValueError("context unit 缺少完整 chunk 引用")
        block_ids = []
        for chunk in chunks:
            block_ids.extend(chunk.get("source_block_ids") or [])
        max_score = max((_score(hit) for hit in hits), default=None)
        return {
            "schema_version": "context_unit_v1",
            "context_id": _context_id(section["section_id"], included_chunk_ids),
            "mode": mode,
            "doc_id": section.get("doc_id") or (chunks[0].get("doc_id") if chunks else ""),
            "section_path": section.get("section_path") or (chunks[0].get("section_path") if chunks else []),
            "parent_section_id": section["section_id"],
            "parent_section_heading": section.get("heading", ""),
            "included_chunk_ids": included_chunk_ids,
            "included_block_ids": sorted(set(block_ids)),
            "content": content,
            "estimated_tokens": count.tokens,
            "actual_tokens": None if count.estimated else count.tokens,
            "max_rerank_score": max_score,
            "trim_events": [],
            "citations": citations,
        }

    def _summarize_unit(self, query: str, unit: dict[str, Any]) -> dict[str, Any]:
        response = self.summarizer.summarize_context(
            query, unit["content"], 400, "global_section_summary_v1",
        )
        if not response.get("ok"):
            unit["trim_events"].append({"event": "summary_failed", "reason": response.get("error", "unknown")})
            return unit
        summarized = dict(unit)
        summarized["mode"] = "summary"
        summarized["content"] = response["summary"]
        count = self.token_counter.count(summarized["content"])
        summarized["estimated_tokens"] = count.tokens
        summarized["actual_tokens"] = None if count.estimated else count.tokens
        summarized["trim_events"] = [*unit["trim_events"], {"event": "summarized", "provider": response.get("provider", "")}]
        return summarized

    def _apply_budget(self, query: str, units: list[dict[str, Any]], token_budget: int, trim_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        while sum(unit["estimated_tokens"] for unit in units) > token_budget and len(units) > 1:
            removed = units.pop()
            trim_events.append({
                "event": "drop_low_score_unit",
                "parent_section_id": removed["parent_section_id"],
            })
        return units


def _score(item: dict[str, Any]) -> float:
    value = item.get("rerank_score", item.get("score", item.get("fusion_score", 0.0)))
    return float(value or 0.0)


def _content(chunks: list[dict[str, Any]]) -> str:
    return "\n\n".join(str(chunk.get("content", chunk.get("content_preview", ""))) for chunk in chunks).strip()


def _context_id(section_id: str, included_chunk_ids: list[str]) -> str:
    payload = json.dumps(
        {"section_id": section_id, "included_chunk_ids": included_chunk_ids},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"context_unit_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"
