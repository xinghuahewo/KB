"""SemanticChunk v3 生产画像与阻断门禁。"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from bgpkb import paths
from bgpkb.ingestion.semantic_chunking_v3 import (
    SemanticChunkingConfig,
    load_semantic_chunking_config,
    resolve_profile,
)


def _validator() -> Draft202012Validator:
    schema = json.loads(
        (paths.SCHEMAS_DIR / "semantic_chunk_v3.schema.json").read_text(encoding="utf-8")
    )
    return Draft202012Validator(schema)


def _sample(values: list[str], limit: int = 20) -> list[str]:
    return values[:limit]


def profile_semantic_chunks(
    chunks: list[dict],
    *,
    excluded_blocks: list[dict],
    config: SemanticChunkingConfig | None = None,
) -> dict:
    active_config = config or load_semantic_chunking_config()
    validator = _validator()
    schema_error_ids: list[str] = []
    empty_ids: list[str] = []
    short_ids: list[str] = []
    allowed_short_ids: list[str] = []
    missing_trace_ids: list[str] = []
    over_target_ids: list[str] = []
    exact_counts: Counter[tuple[str, str, str]] = Counter()
    exact_ids: dict[tuple[str, str, str], list[str]] = {}

    for chunk in chunks:
        chunk_id = str(chunk.get("chunk_id") or "<missing>")
        if list(validator.iter_errors(chunk)):
            schema_error_ids.append(chunk_id)
        content = str(chunk.get("content") or "").strip()
        if not content:
            empty_ids.append(chunk_id)
        if len(content) < active_config.minimum_chars:
            if chunk.get("short_content_rule_id"):
                allowed_short_ids.append(chunk_id)
            else:
                short_ids.append(chunk_id)
        if not chunk.get("source_snapshot_id") or not chunk.get("source_block_ids") or not chunk.get("source_refs"):
            missing_trace_ids.append(chunk_id)
        profile = resolve_profile(str(chunk.get("document_profile")), active_config)
        if int(chunk.get("estimated_tokens") or 0) > profile.target_max_tokens:
            over_target_ids.append(chunk_id)
        exact_key = (
            str(chunk.get("source_id") or ""),
            str(chunk.get("source_snapshot_id") or ""),
            str(chunk.get("exact_content_hash") or ""),
        )
        exact_counts[exact_key] += 1
        exact_ids.setdefault(exact_key, []).append(chunk_id)

    duplicate_count = sum(max(0, count - 1) for count in exact_counts.values())
    duplicate_rate = duplicate_count / len(chunks) if chunks else 0.0
    duplicate_samples = [
        chunk_id
        for key, ids in exact_ids.items()
        if exact_counts[key] > 1
        for chunk_id in ids
    ]
    blocking_issues: list[dict] = []
    if schema_error_ids:
        blocking_issues.append({
            "code": "semantic_chunk_schema_error",
            "actual": len(schema_error_ids),
            "threshold": 0,
        })
    if empty_ids:
        blocking_issues.append({
            "code": "empty_semantic_chunk",
            "actual": len(empty_ids),
            "threshold": 0,
        })
    if short_ids:
        blocking_issues.append({
            "code": "short_unallowlisted_semantic_chunk",
            "actual": len(short_ids),
            "threshold": 0,
        })
    if missing_trace_ids:
        blocking_issues.append({
            "code": "semantic_chunk_traceability_missing",
            "actual": len(missing_trace_ids),
            "threshold": 0,
        })
    if duplicate_rate > active_config.max_same_source_exact_duplicate_rate:
        blocking_issues.append({
            "code": "same_source_exact_duplicate_rate_exceeded",
            "actual": round(duplicate_rate, 6),
            "threshold": active_config.max_same_source_exact_duplicate_rate,
        })

    excluded_reasons = Counter(str(row.get("reason") or "unknown") for row in excluded_blocks)
    warnings = []
    if over_target_ids:
        warnings.append({
            "code": "semantic_chunk_over_target_max_tokens",
            "actual": len(over_target_ids),
        })
    return {
        "schema_version": "semantic_chunk_quality_report_v1",
        "status": "failed" if blocking_issues else "passed",
        "config_version": active_config.config_version,
        "config_fingerprint": active_config.config_fingerprint,
        "metrics": {
            "chunk_count": len(chunks),
            "excluded_count": len(excluded_blocks),
            "schema_error_count": len(schema_error_ids),
            "empty_content_count": len(empty_ids),
            "short_unallowlisted_count": len(short_ids),
            "short_allowlisted_count": len(allowed_short_ids),
            "missing_traceability_count": len(missing_trace_ids),
            "over_target_max_tokens_count": len(over_target_ids),
            "same_source_exact_duplicate_count": duplicate_count,
            "same_source_exact_duplicate_rate": round(duplicate_rate, 6),
        },
        "thresholds": {
            "minimum_semantic_chars": active_config.minimum_chars,
            "max_same_source_exact_duplicate_rate": active_config.max_same_source_exact_duplicate_rate,
        },
        "excluded_reasons": dict(sorted(excluded_reasons.items())),
        "blocking_issues": blocking_issues,
        "warnings": warnings,
        "samples": {
            "schema_errors": _sample(schema_error_ids),
            "empty_content": _sample(empty_ids),
            "short_unallowlisted": _sample(short_ids),
            "missing_traceability": _sample(missing_trace_ids),
            "over_target_max_tokens": _sample(over_target_ids),
            "same_source_exact_duplicates": _sample(duplicate_samples),
        },
    }


def _read_jsonl(path: Path) -> list[dict]:
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError(f"{path}:{line_number} 必须是 JSON object")
        records.append(record)
    return records


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成 SemanticChunk v3 画像并执行生产门禁")
    parser.add_argument("--chunks", type=Path, required=True)
    parser.add_argument("--excluded", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=paths.CONFIG_DIR / "semantic_chunking_v3.yaml")
    args = parser.parse_args(argv)
    chunks = _read_jsonl(args.chunks)
    excluded = _read_jsonl(args.excluded) if args.excluded else []
    report = profile_semantic_chunks(
        chunks,
        excluded_blocks=excluded,
        config=load_semantic_chunking_config(args.config),
    )
    _write_json(args.output, report)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
