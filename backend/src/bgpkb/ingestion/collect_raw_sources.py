"""旧命令兼容入口；来源权威已迁移到版本化 source registry。"""

from pathlib import Path

from bgpkb import paths
from bgpkb.ingestion.source_ingest import main
from bgpkb.ingestion.source_registry import load_source_registry


def load_sources(registry_path: Path = paths.SOURCE_REGISTRY_PATH) -> list[dict]:
    return load_source_registry(registry_path)["sources"]


if __name__ == "__main__":
    raise SystemExit(main())
