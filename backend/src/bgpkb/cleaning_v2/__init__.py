"""旧清洗模块兼容入口；实现已迁移到 ``bgpkb.ingestion.cleaning_v2``。"""

from pathlib import Path


_CANONICAL_PACKAGE = Path(__file__).resolve().parents[1] / "ingestion" / "cleaning_v2"
__path__.append(str(_CANONICAL_PACKAGE))
