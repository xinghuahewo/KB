"""版本化检索与回答黄金集的严格加载边界。"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


def load_versioned_jsonl(
    path: Path,
    *,
    schema_path: Path,
    schema_version: str,
    dataset_version: str,
) -> list[dict]:
    selected = Path(path)
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    rows: list[dict] = []
    for line_number, raw_line in enumerate(
        selected.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        try:
            row = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{selected}:{line_number} 不是合法 JSON：{exc.msg}") from exc
        errors = sorted(
            validator.iter_errors(row), key=lambda item: list(item.absolute_path)
        )
        if errors:
            detail = "; ".join(error.message for error in errors)
            raise ValueError(f"{selected}:{line_number} 不符合黄金集 Schema：{detail}")
        if row.get("schema_version") != schema_version:
            raise ValueError(f"{selected}:{line_number} schema_version 不匹配")
        if row.get("dataset_version") != dataset_version:
            raise ValueError(f"{selected}:{line_number} dataset_version 不匹配")
        rows.append(row)
    if not rows:
        raise ValueError(f"黄金集不能为空：{selected}")
    return rows
