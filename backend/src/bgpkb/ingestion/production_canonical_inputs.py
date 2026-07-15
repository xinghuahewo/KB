"""新生产下游读取 Canonical Document 的唯一入口。"""

from __future__ import annotations

import json
from pathlib import Path

from bgpkb.ingestion.canonical_contract import CanonicalContractError, require_production_canonical


def iter_production_canonical(
    root: Path,
    *,
    known_snapshot_ids: set[str] | None = None,
):
    """按稳定路径顺序产生已校验文档；任一坏输入立即终止整个构建。"""

    for path in sorted(Path(root).glob("*.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            yield require_production_canonical(
                document,
                known_snapshot_ids=known_snapshot_ids,
            )
        except (OSError, UnicodeError, json.JSONDecodeError, CanonicalContractError) as exc:
            raise CanonicalContractError(f"Canonical 生产输入 {path.name} 无效：{exc}") from exc
