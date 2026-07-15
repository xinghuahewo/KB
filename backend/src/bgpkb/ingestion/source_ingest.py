"""source-ingest：隔离采集失败并生成不可变来源快照。"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import mimetypes
import os
from pathlib import Path
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import parse_qsl, urlsplit

from jsonschema import Draft202012Validator

from bgpkb import paths
from bgpkb.ingestion.source_registry import load_source_registry, validate_source_registry
from bgpkb.ingestion.source_store import (
    SourceStore,
    build_source_snapshot,
    conditional_request_headers,
    hash_source_file,
    sanitize_http_metadata,
)


_SUCCESS_STATUSES = frozenset({"imported", "downloaded", "not_modified"})
_SENSITIVE_NAMES = frozenset({
    "authorization",
    "cookie",
    "set_cookie",
    "proxy_authorization",
    "token",
    "access_token",
    "api_key",
    "apikey",
    "password",
    "passwd",
    "secret",
    "credential",
    "credentials",
})


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_legacy_path(root: Path, relative: str) -> Path:
    logical = Path(relative)
    if logical.is_absolute() or ".." in logical.parts:
        raise ValueError(f"legacy_path 越界：{relative}")
    candidate = (Path(root) / logical).resolve()
    candidate.relative_to(Path(root).resolve())
    return candidate


def _atomic_json(path: Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _validate_snapshot(snapshot: dict) -> None:
    schema = json.loads((paths.SCHEMAS_DIR / "source_snapshot.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(snapshot))
    if errors:
        raise ValueError("source snapshot Schema 校验失败：" + "; ".join(error.message for error in errors))


def _write_snapshot(store_root: Path, snapshot: dict) -> dict:
    _validate_snapshot(snapshot)
    path = Path(store_root) / "snapshots" / snapshot["source_id"] / f"{snapshot['snapshot_id']}.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        identity_fields = ("snapshot_id", "source_id", "object_digest", "object_path", "byte_size")
        if any(existing.get(field) != snapshot.get(field) for field in identity_fields):
            raise RuntimeError(f"已有 snapshot 身份冲突：{path}")
        return existing
    _atomic_json(path, snapshot)
    return snapshot


def _legacy_row(source, registry_version, legacy_root, store, store_root, acquired_at, dry_run):
    if source["license"]["status"] == "restricted":
        return {
            "source_id": source["source_id"],
            "status": "license_blocked",
            "required": source["required"],
            "error_code": "license_restricted",
            "error": "来源许可证状态为 restricted，禁止进入候选",
        }
    source_path = _safe_legacy_path(legacy_root, source["legacy_path"])
    if not source_path.is_file():
        return {
            "source_id": source["source_id"],
            "status": "failed" if source["required"] else "missing",
            "required": source["required"],
            "error_code": "legacy_source_missing",
            "error": f"旧 raw 文件不存在：{source['legacy_path']}",
        }
    if dry_run:
        digest, byte_size = hash_source_file(source_path)
        return {
            "source_id": source["source_id"], "status": "dry_run", "required": source["required"],
            "object_digest": digest, "byte_size": byte_size, "legacy_path": source["legacy_path"],
        }
    stored = store.put_file(source_path)
    mime_type = source["expected_content_types"][0] or mimetypes.guess_type(source_path.name)[0]
    snapshot = build_source_snapshot(
        source=source,
        registry_version=registry_version,
        stored_object=stored,
        acquired_at=acquired_at,
        mime_type=mime_type,
        acquisition_status="imported",
        http={"status_code": None, "etag": None, "last_modified": None},
    )
    snapshot = _write_snapshot(store_root, snapshot)
    return {
        "source_id": source["source_id"], "status": "imported", "required": source["required"],
        "object_created": stored.created, "snapshot": snapshot,
    }


def import_legacy_sources(
    registry: dict, *, legacy_root: Path, store_root: Path,
    dry_run: bool = False, acquired_at: str | None = None,
) -> dict:
    validate_source_registry(registry)
    store_root = Path(store_root)
    store = SourceStore(store_root)
    timestamp = acquired_at or _now()
    rows = []
    for source in registry["sources"]:
        try:
            row = _legacy_row(
                source, registry["registry_version"], legacy_root, store,
                store_root, timestamp, dry_run,
            )
        except Exception as exc:
            row = {
                "source_id": source["source_id"], "status": "failed", "required": source["required"],
                "error_code": "legacy_import_failed", "error": str(exc),
            }
        rows.append(row)
    summary = {
        "imported": sum(row["status"] == "imported" for row in rows),
        "failed": sum(row["status"] in {"failed", "missing"} for row in rows),
        "object_created": sum(row.get("object_created") is True for row in rows),
        "object_reused": sum(row.get("object_created") is False for row in rows if row["status"] == "imported"),
    }
    return {"sources": rows, "summary": summary}


def _latest_snapshot(store_root: Path, source_id: str) -> dict | None:
    candidates = []
    for path in (Path(store_root) / "snapshots" / source_id).glob("snapshot_*.json"):
        try:
            candidates.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return max(candidates, key=lambda item: item.get("acquired_at", ""), default=None)


def _http_row(source, registry_version, store, store_root, acquired_at, opener=urlopen):
    if source["license"]["status"] == "restricted":
        return {
            "source_id": source["source_id"],
            "status": "license_blocked",
            "required": source["required"],
            "error_code": "license_restricted",
            "error": "来源许可证状态为 restricted，禁止进入候选",
        }
    previous_snapshot = _latest_snapshot(store_root, source["source_id"])
    request_headers = {
        "User-Agent": "bgpkb-source-ingest/1",
        "Accept": ", ".join(source["expected_content_types"]),
        **conditional_request_headers(previous_snapshot),
    }
    request = Request(
        source["acquisition"]["origin_locator"],
        headers=request_headers,
    )
    try:
        with opener(request, timeout=45) as response:
            content = response.read()
            metadata = sanitize_http_metadata(response.headers, status_code=getattr(response, "status", 200))
    except HTTPError as exc:
        if exc.code == 304 and previous_snapshot is not None:
            return {
                "source_id": source["source_id"], "status": "not_modified",
                "required": source["required"], "snapshot": previous_snapshot,
            }
        raise RuntimeError(f"HTTP {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("远端来源请求失败") from exc
    stored = store.put_bytes(content)
    snapshot = build_source_snapshot(
        source=source, registry_version=registry_version, stored_object=stored,
        acquired_at=acquired_at, mime_type=metadata["mime_type"],
        acquisition_status="downloaded", http=metadata["http"],
    )
    snapshot = _write_snapshot(store_root, snapshot)
    return {
        "source_id": source["source_id"], "status": "downloaded", "required": source["required"],
        "object_created": stored.created, "snapshot": snapshot,
    }


def _frozen_input_paths(root: Path) -> set[str]:
    root = Path(root).resolve()
    if not root.is_dir():
        return set()
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }


def _sensitive_metadata_paths(payload: object, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            child_path = f"{path}.{key}"
            normalized = str(key).casefold().replace("-", "_")
            if normalized in _SENSITIVE_NAMES:
                findings.append(child_path)
            if key == "origin_locator" and isinstance(value, str):
                parsed = urlsplit(value)
                if parsed.username is not None or parsed.password is not None:
                    findings.append(child_path + ".userinfo")
                for query_key, _ in parse_qsl(parsed.query, keep_blank_values=True):
                    if query_key.casefold().replace("-", "_") in _SENSITIVE_NAMES:
                        findings.append(child_path + f".query.{query_key}")
            findings.extend(_sensitive_metadata_paths(value, child_path))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            findings.extend(_sensitive_metadata_paths(value, f"{path}[{index}]"))
    return sorted(set(findings))


def _audit_source_ingest(
    registry: dict,
    rows: list[dict],
    *,
    store_root: Path,
    legacy_root: Path | None,
) -> dict:
    sources = registry["sources"]
    registered_paths = {source["legacy_path"] for source in sources}
    frozen_paths = _frozen_input_paths(legacy_root) if legacy_root is not None else set()
    unregistered = sorted(frozen_paths - registered_paths)
    successful = [row for row in rows if row["status"] in _SUCCESS_STATUSES]
    missing = [row for row in rows if row["status"] == "missing"]
    failed = [row for row in rows if row["status"] == "failed"]
    license_blocked = [row for row in rows if row["status"] == "license_blocked"]
    present_registered = (
        len(registered_paths & frozen_paths)
        if legacy_root is not None
        else len(successful)
    )
    coverage_denominator = len(sources) + len(unregistered)
    coverage_percent = round(
        (present_registered / coverage_denominator * 100) if coverage_denominator else 100.0,
        3,
    )

    dangling_references: list[str] = []
    hash_mismatches: list[str] = []
    object_paths: set[str] = set()
    snapshots: list[dict] = []
    for row in successful:
        snapshot = row.get("snapshot")
        if not isinstance(snapshot, dict):
            dangling_references.append(f"{row['source_id']}:snapshot_missing")
            continue
        try:
            _validate_snapshot(snapshot)
        except ValueError as exc:
            hash_mismatches.append(f"{row['source_id']}:snapshot_schema:{exc}")
            continue
        snapshots.append(snapshot)
        object_path = Path(store_root) / snapshot["object_path"]
        object_paths.add(snapshot["object_path"])
        if not object_path.is_file():
            dangling_references.append(f"{row['source_id']}:{snapshot['object_path']}")
            continue
        actual_digest, actual_size = hash_source_file(object_path)
        expected_object_path = f"objects/sha256/{actual_digest.removeprefix('sha256:')}"
        if (
            actual_digest != snapshot["object_digest"]
            or actual_size != snapshot["byte_size"]
            or snapshot["object_path"] != expected_object_path
        ):
            hash_mismatches.append(row["source_id"])

    sensitive_paths = _sensitive_metadata_paths(rows)
    diagnostics = [
        {
            "error_code": row.get("error_code", "source_missing"),
            "source_id": row["source_id"],
            "status": row["status"],
        }
        for row in (*missing, *failed, *license_blocked)
    ]
    if unregistered:
        diagnostics.append({
            "error_code": "unregistered_frozen_input",
            "paths": unregistered,
        })
    if dangling_references:
        diagnostics.append({
            "error_code": "dangling_object_reference",
            "references": dangling_references,
        })
    if hash_mismatches:
        diagnostics.append({
            "error_code": "object_hash_mismatch",
            "sources": hash_mismatches,
        })
    if sensitive_paths:
        diagnostics.append({
            "error_code": "sensitive_metadata",
            "paths": sensitive_paths,
        })

    license_counts = {
        status: sum(source["license"]["status"] == status for source in sources)
        for status in ("known", "unknown", "restricted")
    }
    closure_complete = (
        not dangling_references
        and not hash_mismatches
        and len(snapshots) == len(successful)
    )
    return {
        "registry": {
            "total": len(sources),
            "enabled": len(sources),
            "successful": len(successful),
            "missing": len(missing),
            "failed": len(failed),
            "license_blocked": len(license_blocked),
            "coverage_percent": coverage_percent,
            "unregistered_inputs": unregistered,
        },
        "licenses": license_counts,
        "objects": {
            "snapshot_count": len(snapshots),
            "object_count": len(object_paths),
            "object_created": sum(row.get("object_created") is True for row in successful),
            "object_reused": sum(row.get("object_created") is False for row in successful),
            "dangling_references": dangling_references,
            "hash_mismatches": hash_mismatches,
            "closure_complete": closure_complete,
        },
        "sensitive_metadata_paths": sensitive_paths,
        "diagnostics": diagnostics,
    }


def run_source_ingest(
    registry: dict, *, store_root: Path, manifest_path: Path,
    legacy_root: Path | None = None, dry_run: bool = False, opener=urlopen,
) -> dict:
    validate_source_registry(registry)
    timestamp = _now()
    if legacy_root is not None:
        imported = import_legacy_sources(
            registry, legacy_root=legacy_root, store_root=store_root,
            dry_run=dry_run, acquired_at=timestamp,
        )
        rows = imported["sources"]
    else:
        store = SourceStore(store_root)
        rows = []
        for source in registry["sources"]:
            try:
                if source["acquisition"]["method"] != "http":
                    raise RuntimeError("local_import 来源必须显式提供 --legacy-root")
                row = _http_row(
                    source, registry["registry_version"], store, Path(store_root), timestamp, opener=opener,
                )
            except Exception as exc:
                row = {
                    "source_id": source["source_id"],
                    "status": "failed" if source["required"] else "missing",
                    "required": source["required"],
                    "error_code": "source_acquisition_failed",
                    "error": str(exc),
                }
            rows.append(row)
    normalized_rows = [dict(row) for row in rows]
    summary = {
        "imported": sum(row["status"] in {"imported", "downloaded", "not_modified", "dry_run"} for row in normalized_rows),
        "missing": sum(row["status"] == "missing" for row in normalized_rows),
        "failed": sum(row["status"] == "failed" for row in normalized_rows),
    }
    audit = _audit_source_ingest(
        registry,
        normalized_rows,
        store_root=Path(store_root),
        legacy_root=Path(legacy_root) if legacy_root is not None else None,
    )
    failed_closed = bool(audit["diagnostics"])
    manifest = {
        "schema_version": "source_ingest_manifest_v1",
        "registry_version": registry["registry_version"],
        "generated_at": timestamp,
        "dry_run": dry_run,
        "summary": summary,
        "audit": audit,
        "sources": normalized_rows,
        "status": "failed" if failed_closed else "complete",
    }
    _atomic_json(manifest_path, manifest)
    return {
        "exit_code": 1 if failed_closed else 0,
        "summary": summary,
        "sources": normalized_rows,
        "manifest": manifest,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="构建不可变来源快照。")
    parser.add_argument("--registry", type=Path, default=paths.SOURCE_REGISTRY_PATH)
    parser.add_argument("--source-store", type=Path, default=os.environ.get("BGPKB_SOURCE_STORE_DIR"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--legacy-root", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.source_store is None:
        parser.error("必须通过 --source-store 或 BGPKB_SOURCE_STORE_DIR 指定外置对象库")
    result = run_source_ingest(
        load_source_registry(args.registry), store_root=args.source_store,
        manifest_path=args.manifest, legacy_root=args.legacy_root, dry_run=args.dry_run,
    )
    print(json.dumps({"summary": result["summary"], "manifest": str(args.manifest)}, ensure_ascii=False))
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
