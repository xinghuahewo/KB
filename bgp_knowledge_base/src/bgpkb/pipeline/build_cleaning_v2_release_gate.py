#!/usr/bin/env python3
"""汇总清洗 v2 迁移与人工验收发布门禁。"""

import argparse
import json
from pathlib import Path

from bgpkb import paths
from bgpkb.cleaning_v2.contracts import atomic_write_json


DEFAULT_MIGRATION = paths.DATASETS_DIR / "cleaning_v2_migration_diff.jsonl"
DEFAULT_ACCEPTANCE = paths.DATASETS_DIR / "cleaning_v2_human_acceptance.json"
DEFAULT_OUTPUT = paths.DATASETS_DIR / "cleaning_v2_release_gate.json"


def _load_jsonl(path):
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def build_gate(*, migration_path, acceptance_path, output_path, expected_document_count=54):
    migration = _load_jsonl(migration_path)
    acceptance = json.loads(Path(acceptance_path).read_text(encoding="utf-8"))
    blocking = []
    if len(migration) != expected_document_count:
        blocking.append("migration_document_count_mismatch")
    if any(not row.get("gate_passed") for row in migration):
        blocking.append("migration_diff_gates_failed")
    if any(row.get("state") == "quarantined" for row in migration):
        blocking.append("quarantined_document_present")
    if not acceptance.get("passed"):
        blocking.append("human_acceptance_failed")
    metrics = acceptance.get("metrics", {})
    result = {
        "schema_version": "cleaning_v2_release_gate_v1",
        "passed": not blocking,
        "blocking_issues": blocking,
        "details": {
            "migration_total": len(migration),
            "migration_gate_passed": sum(bool(row.get("gate_passed")) for row in migration),
            "quarantined_count": sum(row.get("state") == "quarantined" for row in migration),
            "human_acceptance_passed": bool(acceptance.get("passed")),
            "heading_hierarchy_f1": metrics.get("heading_hierarchy_f1"),
            "reading_order_accuracy": metrics.get("reading_order_accuracy"),
            "table_structure_accuracy": metrics.get("table_structure_accuracy"),
            "ocr_character_error_rate": metrics.get("ocr_character_error_rate"),
        },
    }
    atomic_write_json(output_path, result, indent=2)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="生成清洗 v2 发布门禁")
    parser.add_argument("--migration-path", type=Path, default=DEFAULT_MIGRATION)
    parser.add_argument("--acceptance-path", type=Path, default=DEFAULT_ACCEPTANCE)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--expected-document-count", type=int, default=54)
    args = parser.parse_args(argv)
    result = build_gate(**vars(args))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
