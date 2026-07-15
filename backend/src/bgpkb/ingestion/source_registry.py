"""版本化来源注册表加载与严格校验。"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
import yaml

from bgpkb import paths


class SourceRegistryError(ValueError):
    pass


def _format_error(error) -> str:
    location = ".".join(str(part) for part in error.absolute_path) or "$"
    return f"{location}: {error.message}"


def validate_source_registry(payload: dict, schema_path: Path | None = None) -> None:
    schema_path = schema_path or paths.SCHEMAS_DIR / "source_registry.schema.json"
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda item: list(item.absolute_path))
    if errors:
        raise SourceRegistryError("来源注册表 Schema 校验失败：" + "; ".join(_format_error(error) for error in errors))
    source_ids = [source["source_id"] for source in payload["sources"]]
    duplicates = sorted({source_id for source_id in source_ids if source_ids.count(source_id) > 1})
    if duplicates:
        raise SourceRegistryError(f"source_id 重复：{', '.join(duplicates)}")


def load_source_registry(path: Path | None = None) -> dict:
    selected = Path(path or paths.SOURCE_REGISTRY_PATH)
    try:
        payload = yaml.safe_load(selected.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SourceRegistryError(f"来源注册表不可读：{selected}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SourceRegistryError("来源注册表根节点必须是对象")
    validate_source_registry(payload)
    return payload
