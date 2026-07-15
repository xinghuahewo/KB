import hashlib
import json
from pathlib import Path
import subprocess

import pytest
from jsonschema import Draft202012Validator

from bgpkb import paths
from bgpkb.ingestion import collect_raw_sources
from bgpkb.ingestion.source_ingest import import_legacy_sources, run_source_ingest
from bgpkb.ingestion.source_registry import SourceRegistryError, load_source_registry
from bgpkb.ingestion.source_store import (
    SourceStore,
    build_source_snapshot,
    conditional_request_headers,
    sanitize_http_metadata,
)


SCHEMAS = paths.SCHEMAS_DIR
REGISTRY = paths.METADATA_DIR / "sources" / "source_registry.yaml"


def _registry(*sources):
    return {
        "schema_version": "source_registry_v1",
        "registry_version": "fixture-v1",
        "sources": list(sources),
    }


def _source(source_id, legacy_path, *, required=True, license_status="unknown"):
    return {
        "source_id": source_id,
        "acquisition": {"method": "local_import", "origin_locator": legacy_path},
        "source_type": "standard",
        "document_profile": "rfc",
        "authority_org": "Fixture Authority",
        "language": "en",
        "license": {"status": license_status, "identifier": None, "notes": "fixture"},
        "expected_content_types": ["text/plain"],
        "legacy_path": legacy_path,
        "required": required,
    }


def test_source_registry_and_snapshot_schemas_reject_missing_license_and_unknown_fields():
    registry_schema = json.loads((SCHEMAS / "source_registry.schema.json").read_text(encoding="utf-8"))
    snapshot_schema = json.loads((SCHEMAS / "source_snapshot.schema.json").read_text(encoding="utf-8"))
    source = _source("rfc4271", "standards/rfc4271.txt")
    registry = _registry(source)

    Draft202012Validator(registry_schema).validate(registry)
    invalid = json.loads(json.dumps(registry))
    del invalid["sources"][0]["license"]
    assert any("license" in error.message for error in Draft202012Validator(registry_schema).iter_errors(invalid))

    snapshot = {
        "schema_version": "source_snapshot_v1",
        "snapshot_id": "snapshot_" + "1" * 64,
        "source_id": "rfc4271",
        "registry_version": "fixture-v1",
        "object_digest": "sha256:" + "2" * 64,
        "object_path": "objects/sha256/" + "2" * 64,
        "byte_size": 12,
        "mime_type": "text/plain",
        "acquired_at": "2026-07-14T00:00:00Z",
        "acquisition_status": "imported",
        "origin_locator": "standards/rfc4271.txt",
        "license": {"status": "unknown", "identifier": None, "notes": "fixture"},
        "http": {"status_code": None, "etag": None, "last_modified": None},
    }
    Draft202012Validator(snapshot_schema).validate(snapshot)
    missing_license = dict(snapshot)
    del missing_license["license"]
    assert any(
        "license" in error.message
        for error in Draft202012Validator(snapshot_schema).iter_errors(missing_license)
    )
    snapshot["authorization"] = "secret"
    assert any("was unexpected" in error.message for error in Draft202012Validator(snapshot_schema).iter_errors(snapshot))


def test_versioned_registry_is_the_only_collector_authority():
    payload = load_source_registry(REGISTRY)

    assert payload["registry_version"] == "2026-07-14-v1"
    assert len(payload["sources"]) == 54
    assert len({source["source_id"] for source in payload["sources"]}) == 54
    assert not hasattr(collect_raw_sources, "SOURCES")
    assert collect_raw_sources.load_sources(REGISTRY) == payload["sources"]


def test_registry_loader_rejects_duplicate_source_ids(tmp_path):
    registry_path = tmp_path / "registry.yaml"
    source = _source("duplicate", "standards/duplicate.txt")
    registry_path.write_text(
        json.dumps(_registry(source, source), ensure_ascii=False), encoding="utf-8"
    )

    with pytest.raises(SourceRegistryError, match="source_id 重复"):
        load_source_registry(registry_path)


def test_content_addressed_store_reuses_identical_bytes_without_overwrite(tmp_path):
    store = SourceStore(tmp_path / "source-store")
    first = store.put_bytes(b"immutable source\n")
    before = first.path.stat()
    second = store.put_bytes(b"immutable source\n")

    assert first.created is True
    assert second.created is False
    assert first.path == second.path
    assert first.digest == "sha256:" + hashlib.sha256(b"immutable source\n").hexdigest()
    assert second.path.read_bytes() == b"immutable source\n"
    assert second.path.stat().st_mtime_ns == before.st_mtime_ns


def test_snapshot_filters_sensitive_headers_and_records_conditional_metadata(tmp_path):
    stored = SourceStore(tmp_path).put_bytes(b"payload")
    http = sanitize_http_metadata({
        "ETag": '"v1"',
        "Last-Modified": "Tue, 14 Jul 2026 00:00:00 GMT",
        "Content-Type": "text/plain",
        "Authorization": "Bearer secret",
        "Cookie": "session=secret",
    }, status_code=200)
    snapshot = build_source_snapshot(
        source=_source("rfc4271", "standards/rfc4271.txt"),
        registry_version="fixture-v1",
        stored_object=stored,
        acquired_at="2026-07-14T00:00:00Z",
        mime_type=http["mime_type"],
        acquisition_status="downloaded",
        http=http["http"],
    )

    serialized = json.dumps(snapshot, ensure_ascii=False).casefold()
    assert snapshot["http"] == {
        "status_code": 200,
        "etag": '"v1"',
        "last_modified": "Tue, 14 Jul 2026 00:00:00 GMT",
    }
    assert "authorization" not in serialized
    assert "cookie" not in serialized
    assert "secret" not in serialized


def test_conditional_request_uses_only_previous_etag_and_last_modified():
    headers = conditional_request_headers({
        "http": {
            "etag": '"v1"',
            "last_modified": "Tue, 14 Jul 2026 00:00:00 GMT",
            "authorization": "secret",
        }
    })

    assert headers == {
        "If-None-Match": '"v1"',
        "If-Modified-Since": "Tue, 14 Jul 2026 00:00:00 GMT",
    }


def test_legacy_import_is_read_only_and_reuses_objects(tmp_path):
    raw = tmp_path / "legacy"
    (raw / "standards").mkdir(parents=True)
    first_path = raw / "standards" / "a.txt"
    second_path = raw / "standards" / "b.txt"
    first_path.write_bytes(b"same bytes")
    second_path.write_bytes(b"same bytes")
    before = {path: (path.stat().st_mtime_ns, path.read_bytes()) for path in (first_path, second_path)}
    registry = _registry(
        _source("source_a", "standards/a.txt"),
        _source("source_b", "standards/b.txt"),
    )

    result = import_legacy_sources(registry, legacy_root=raw, store_root=tmp_path / "store")

    assert result["summary"] == {"imported": 2, "failed": 0, "object_created": 1, "object_reused": 1}
    assert len({row["snapshot"]["object_digest"] for row in result["sources"]}) == 1
    assert len({row["snapshot"]["snapshot_id"] for row in result["sources"]}) == 2
    for path, state in before.items():
        assert (path.stat().st_mtime_ns, path.read_bytes()) == state


def test_source_ingest_isolates_failures_and_writes_atomic_terminal_manifest(tmp_path):
    raw = tmp_path / "legacy"
    (raw / "standards").mkdir(parents=True)
    (raw / "standards" / "ok.txt").write_text("ok", encoding="utf-8")
    registry = _registry(
        _source("ok", "standards/ok.txt"),
        _source("missing_optional", "standards/missing-optional.txt", required=False),
        _source("missing_required", "standards/missing-required.txt", required=True),
    )
    manifest = tmp_path / "candidate" / "source-ingest-manifest.json"

    result = run_source_ingest(
        registry,
        legacy_root=raw,
        store_root=tmp_path / "store",
        manifest_path=manifest,
    )

    assert result["exit_code"] == 1
    assert [row["status"] for row in result["sources"]] == ["imported", "missing", "failed"]
    assert result["summary"] == {"imported": 1, "missing": 1, "failed": 1}
    assert json.loads(manifest.read_text(encoding="utf-8")) == result["manifest"]
    assert not list(manifest.parent.glob("*.tmp"))


def test_frozen_source_ingest_audits_registry_license_objects_and_hash_closure(tmp_path):
    raw = tmp_path / "frozen"
    (raw / "standards").mkdir(parents=True)
    (raw / "standards" / "a.txt").write_bytes(b"same frozen bytes")
    (raw / "standards" / "b.txt").write_bytes(b"same frozen bytes")
    registry = _registry(
        _source("source_a", "standards/a.txt", license_status="known"),
        _source("source_b", "standards/b.txt"),
    )
    manifest = tmp_path / "candidate" / "data" / "manifests" / "source_ingest.json"

    result = run_source_ingest(
        registry,
        legacy_root=raw,
        store_root=tmp_path / "candidate" / "source-store",
        manifest_path=manifest,
    )

    assert result["exit_code"] == 0
    assert result["manifest"]["status"] == "complete"
    assert result["manifest"]["audit"] == {
        "registry": {
            "total": 2,
            "enabled": 2,
            "successful": 2,
            "missing": 0,
            "failed": 0,
            "license_blocked": 0,
            "coverage_percent": 100.0,
            "unregistered_inputs": [],
        },
        "licenses": {"known": 1, "unknown": 1, "restricted": 0},
        "objects": {
            "snapshot_count": 2,
            "object_count": 1,
            "object_created": 1,
            "object_reused": 1,
            "dangling_references": [],
            "hash_mismatches": [],
            "closure_complete": True,
        },
        "sensitive_metadata_paths": [],
        "diagnostics": [],
    }
    for row in result["sources"]:
        snapshot = row["snapshot"]
        assert snapshot["license"] == next(
            source["license"] for source in registry["sources"]
            if source["source_id"] == row["source_id"]
        )


@pytest.mark.parametrize(
    ("source", "extra_path", "expected_code"),
    [
        (_source("restricted", "standards/restricted.txt", license_status="restricted"), None, "license_restricted"),
        (_source("registered", "standards/registered.txt"), "standards/unregistered.txt", "unregistered_frozen_input"),
        (
            {
                **_source("credentialed", "standards/credentialed.txt"),
                "acquisition": {
                    "method": "local_import",
                    "origin_locator": "https://example.test/source?token=secret",
                },
            },
            None,
            "sensitive_metadata",
        ),
    ],
)
def test_frozen_source_ingest_fails_closed_for_license_coverage_or_sensitive_gaps(
    tmp_path,
    source,
    extra_path,
    expected_code,
):
    raw = tmp_path / "frozen"
    source_path = raw / source["legacy_path"]
    source_path.parent.mkdir(parents=True)
    source_path.write_text("registered bytes", encoding="utf-8")
    if extra_path:
        unmanaged = raw / extra_path
        unmanaged.parent.mkdir(parents=True, exist_ok=True)
        unmanaged.write_text("unregistered bytes", encoding="utf-8")

    result = run_source_ingest(
        _registry(source),
        legacy_root=raw,
        store_root=tmp_path / "candidate" / "source-store",
        manifest_path=tmp_path / "candidate" / "data" / "manifests" / "source_ingest.json",
    )

    assert result["exit_code"] != 0
    assert result["manifest"]["status"] == "failed"
    assert any(
        row["error_code"] == expected_code
        for row in result["manifest"]["audit"]["diagnostics"]
    )


def test_dry_run_hashes_legacy_sources_without_creating_raw_objects(tmp_path):
    raw = tmp_path / "legacy"
    (raw / "standards").mkdir(parents=True)
    (raw / "standards" / "rfc.txt").write_text("RFC fixture", encoding="utf-8")
    result = import_legacy_sources(
        _registry(_source("rfc", "standards/rfc.txt")),
        legacy_root=raw,
        store_root=tmp_path / "store",
        dry_run=True,
    )

    assert result["sources"][0]["status"] == "dry_run"
    assert result["sources"][0]["object_digest"].startswith("sha256:")
    assert not (tmp_path / "store" / "objects").exists()


def test_raw_objects_are_ignored_by_git():
    candidate = "backend/data/sources/raw/objects/sha256/" + "a" * 64
    result = subprocess.run(
        ["git", "check-ignore", "-q", candidate],
        cwd=paths.REPOSITORY_ROOT,
        check=False,
    )

    assert result.returncode == 0
