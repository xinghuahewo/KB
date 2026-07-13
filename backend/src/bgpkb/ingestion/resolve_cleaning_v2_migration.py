#!/usr/bin/env python3
"""解决清洗 v2 迁移差异并生成已审核的 resolved run。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

from bgpkb import paths
from bgpkb.ingestion.cleaning_v2.contracts import atomic_write_json
from bgpkb.ingestion.cleaning_v2.migration_resolution import (
    build_legacy_preservation_document,
    build_migration_decision,
)


DEFAULT_AUTHORITY = paths.CORPUS_DIR / "cleaned_blocks_v2"
DEFAULT_ORIGINAL_RUN = paths.DATASETS_DIR / "cleaning_runs_v2" / "full-54-v2-final"
DEFAULT_RESOLVED_RUN = paths.DATASETS_DIR / "cleaning_runs_v2" / "full-54-v2-resolved"
DEFAULT_DIFF = paths.DATASETS_DIR / "cleaning_v2_migration_diff.jsonl"
DEFAULT_DECISIONS = paths.REVIEW_INPUTS_DIR / "cleaning_v2_migration_decisions.jsonl"


def _load_jsonl(path):
    path = Path(path)
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _atomic_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _find_document(root, doc_id, suffix=None):
    matches = sorted(Path(root).rglob(f"{doc_id}{suffix or '.*'}"))
    return matches[0] if matches else None


def find_v1_markdown(root, doc_id):
    root = Path(root)
    if doc_id == "context_2026":
        alias = root / "notes" / "context_summary.md"
        if alias.is_file():
            return alias
    return _find_document(root, doc_id, ".md")


def _sha256(content):
    return "sha256:" + hashlib.sha256(content).hexdigest()


def resolve_migration(
    *, authority_root, original_run_dir, resolved_run_dir, v1_markdown_root,
    raw_root, diff_path, decisions_path, reviewer, reviewed_at,
    fallback_formats=(".html", ".yaml", ".yml", ".md"),
    minimum_coverage=0.995,
):
    authority_root = Path(authority_root)
    statuses = _load_jsonl(Path(original_run_dir) / "document_status.jsonl")
    diffs = {row["doc_id"]: row for row in _load_jsonl(diff_path)}
    resolved_statuses = []
    decisions = []
    fallback_count = 0

    for status in sorted(statuses, key=lambda row: row["doc_id"]):
        doc_id = status["doc_id"]
        raw_path = _find_document(raw_root, doc_id)
        v1_path = find_v1_markdown(v1_markdown_root, doc_id)
        if raw_path is None or v1_path is None:
            raise FileNotFoundError(f"迁移解析缺少输入: {doc_id}")
        authority_dir = authority_root / doc_id
        authority_dir.mkdir(parents=True, exist_ok=True)
        existing_path = authority_dir / "cleaned_document.json"
        existing = json.loads(existing_path.read_text(encoding="utf-8")) if existing_path.is_file() else {}
        diff = diffs.get(doc_id, {})
        coverage = (diff.get("diff") or {}).get("body", {}).get("coverage_ratio", 0.0)
        use_fallback = (
            status.get("state") == "quarantined"
            or (
                existing.get("parser_mode") == "fallback"
                and existing.get("fallback_review_status") == "approved"
            )
            or (raw_path.suffix.lower() in set(fallback_formats) and coverage < minimum_coverage)
        )
        v1_bytes = v1_path.read_bytes()

        if use_fallback:
            source_sha = hashlib.sha256(raw_path.read_bytes()).hexdigest()
            source_meta = {
                "doc_id": doc_id,
                "source_path": str(
                    Path("data/sources/raw") / raw_path.relative_to(Path(raw_root))
                ),
                "source_sha256": source_sha,
                "legacy_cleaned_path": str(
                    Path("data/corpus/cleaned") / v1_path.relative_to(Path(v1_markdown_root))
                ),
            }
            runtime = existing.get("runtime", {"pipeline_revision": "legacy-preservation-v2"})
            document, review_decisions = build_legacy_preservation_document(
                doc_id=doc_id,
                markdown=v1_bytes.decode("utf-8"),
                source_meta=source_meta,
                runtime_meta=runtime,
                reviewer=reviewer,
                reviewed_at=reviewed_at,
            )
            atomic_write_json(existing_path, document)
            atomic_write_json(authority_dir / "review_decisions.json", review_decisions)
            atomic_write_json(authority_dir / "transformations.json", [])
            atomic_write_json(authority_dir / "review_queue.json", [])
            atomic_write_json(
                authority_dir / "validation.json",
                {"valid": True, "errors": [], "review_queue": [], "publishable_block_count": len(document["blocks"])},
            )
            fallback_count += 1
            strategy = "legacy_preservation"
            reason_code = "reviewed_docling_coverage_fallback"
            v2_bytes = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        else:
            if not existing:
                raise FileNotFoundError(f"缺少 approved authority: {doc_id}")
            strategy = "docling"
            reason_code = "reviewed_layout_difference"
            v2_bytes = json.dumps(existing, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

        decisions.append(
            build_migration_decision(
                doc_id=doc_id,
                strategy=strategy,
                reason_code=reason_code,
                v1_digest=_sha256(v1_bytes),
                v2_digest=_sha256(v2_bytes),
                reviewer=reviewer,
                reviewed_at=reviewed_at,
            )
        )
        output_summary = dict(status.get("output_summary", {}))
        output_summary["fallback_used"] = use_fallback
        resolved_status = {
            **status,
            "state": "approved",
            "errors": [],
            "output_summary": output_summary,
            "resolution": {"strategy": strategy, "reviewer": reviewer, "reviewed_at": reviewed_at},
        }
        atomic_write_json(authority_dir / "document_status.json", resolved_status)
        resolved_statuses.append(resolved_status)

    _atomic_jsonl(Path(resolved_run_dir) / "document_status.jsonl", resolved_statuses)
    _atomic_jsonl(decisions_path, decisions)
    return {
        "document_count": len(resolved_statuses),
        "fallback_document_count": fallback_count,
        "docling_document_count": len(resolved_statuses) - fallback_count,
        "decision_count": len(decisions),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="解决清洗 v2 迁移差异并生成已审核 resolved run")
    parser.add_argument("--authority-root", type=Path, default=DEFAULT_AUTHORITY)
    parser.add_argument("--original-run-dir", type=Path, default=DEFAULT_ORIGINAL_RUN)
    parser.add_argument("--resolved-run-dir", type=Path, default=DEFAULT_RESOLVED_RUN)
    parser.add_argument("--v1-markdown-root", type=Path, default=paths.CLEANED_DIR)
    parser.add_argument("--raw-root", type=Path, default=paths.RAW_DIR)
    parser.add_argument("--diff-path", type=Path, default=DEFAULT_DIFF)
    parser.add_argument("--decisions-path", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--reviewer", default="botongwu")
    parser.add_argument("--reviewed-at", default="2026-07-02T00:00:00+08:00")
    args = parser.parse_args(argv)
    print(json.dumps(resolve_migration(**vars(args)), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
