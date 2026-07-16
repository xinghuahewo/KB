"""仅供迁移、审计使用的旧 Canonical 只读适配器。"""

from __future__ import annotations

import json
from pathlib import Path


class LegacyCanonicalAccessError(PermissionError):
    """旧数据未通过显式只读模式访问。"""


def read_legacy_read_only(path: Path, *, allow_legacy: bool = False) -> dict:
    source = Path(path)
    if not allow_legacy:
        raise LegacyCanonicalAccessError("读取 legacy 输入必须显式设置 allow_legacy=True")
    if source.suffix.casefold() not in {".json", ".jsonl", ".md", ".markdown"}:
        raise LegacyCanonicalAccessError(f"不支持的 legacy 只读格式：{source.suffix}")
    raw = source.read_text(encoding="utf-8")
    if source.suffix.casefold() == ".json":
        content: object = json.loads(raw)
    elif source.suffix.casefold() == ".jsonl":
        content = [json.loads(line) for line in raw.splitlines() if line.strip()]
    else:
        content = raw
    return {
        "mode": "legacy_read_only",
        "read_only": True,
        "source_path": str(source),
        "diagnostic": {
            "code": "deprecated_legacy_canonical_input",
            "severity": "warning",
            "message": "该输入仅用于历史迁移或审计，禁止进入新生产制品。",
        },
        "content": content,
    }
