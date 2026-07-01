"""版本化语料发布指针、失败关闭切换与 v1 回滚。"""

from datetime import datetime, timezone
import json
from pathlib import Path

from .contracts import atomic_write_json


class ReleaseGateError(RuntimeError):
    """发布门禁未通过。"""


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _validate_manifest(manifest):
    required = {"version", "authority", "markdown", "chunks", "input_snapshot"}
    missing = sorted(required - set(manifest))
    if missing:
        raise ValueError("发布 manifest 缺少字段: " + ", ".join(missing))
    if manifest["version"] not in {"v1", "v2"}:
        raise ValueError("不支持的语料版本")


def load_pointer(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_pointer(path, manifest, *, reason):
    _validate_manifest(manifest)
    path = Path(path)
    history = load_pointer(path).get("history", []) if path.is_file() else []
    event = {"version": manifest["version"], "at": _now(), "reason": reason}
    payload = {
        "schema_version": "corpus_release_pointer_v1",
        "active": dict(manifest),
        "updated_at": event["at"],
        "history": history + [event],
    }
    atomic_write_json(path, payload)
    return payload


def switch_release(pointer_path, target_manifest, *, gate_result, reason):
    if not gate_result.get("passed"):
        issues = gate_result.get("blocking_issues", [])
        raise ReleaseGateError("发布门禁未通过: " + ", ".join(issues))
    if target_manifest.get("version") != "v2":
        raise ValueError("switch_release 只接受 v2 目标")
    return write_pointer(pointer_path, target_manifest, reason=reason)


def rollback_to_v1(pointer_path, v1_manifest, *, reason):
    if v1_manifest.get("version") != "v1":
        raise ValueError("回滚 manifest 必须为 v1")
    return write_pointer(pointer_path, v1_manifest, reason=reason)


def resolve_release(pointer_path):
    pointer = load_pointer(pointer_path)
    manifest = pointer.get("active", {})
    _validate_manifest(manifest)
    return manifest
