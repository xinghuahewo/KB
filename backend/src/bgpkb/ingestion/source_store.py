"""外置、不可变、按 SHA-256 内容寻址的来源对象库。"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import tempfile


@dataclass(frozen=True)
class StoredObject:
    digest: str
    path: Path
    byte_size: int
    created: bool

    @property
    def relative_path(self) -> str:
        return f"objects/sha256/{self.digest.removeprefix('sha256:')}"


def _digest_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    byte_size = 0
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
            byte_size += len(block)
    return digest.hexdigest(), byte_size


class SourceStore:
    def __init__(self, root: Path):
        self.root = Path(root)

    def object_path(self, hexdigest: str) -> Path:
        return self.root / "objects" / "sha256" / hexdigest

    def put_bytes(self, content: bytes) -> StoredObject:
        hexdigest = hashlib.sha256(content).hexdigest()
        destination = self.object_path(hexdigest)
        return self._install(destination, hexdigest, len(content), lambda handle: handle.write(content))

    def put_file(self, source: Path) -> StoredObject:
        source = Path(source)
        hexdigest, byte_size = _digest_file(source)
        destination = self.object_path(hexdigest)

        def copy(handle):
            with source.open("rb") as input_handle:
                for block in iter(lambda: input_handle.read(1024 * 1024), b""):
                    handle.write(block)

        return self._install(destination, hexdigest, byte_size, copy)

    def _install(self, destination, hexdigest, byte_size, writer) -> StoredObject:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            actual_digest, actual_size = _digest_file(destination)
            if actual_digest != hexdigest or actual_size != byte_size:
                raise RuntimeError(f"内容寻址对象损坏：{destination}")
            return StoredObject(f"sha256:{hexdigest}", destination, byte_size, False)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".object-", delete=False) as handle:
                temporary = Path(handle.name)
                writer(handle)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary, destination)
                created = True
            except FileExistsError:
                created = False
            actual_digest, actual_size = _digest_file(destination)
            if actual_digest != hexdigest or actual_size != byte_size:
                raise RuntimeError(f"内容寻址对象写入校验失败：{destination}")
            return StoredObject(f"sha256:{hexdigest}", destination, byte_size, created)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def hash_source_file(path: Path) -> tuple[str, int]:
    hexdigest, byte_size = _digest_file(Path(path))
    return f"sha256:{hexdigest}", byte_size


def sanitize_http_metadata(headers, *, status_code: int | None) -> dict:
    normalized = {str(key).casefold(): str(value) for key, value in dict(headers).items()}
    return {
        "mime_type": normalized.get("content-type", "application/octet-stream").split(";", 1)[0].strip(),
        "http": {
            "status_code": status_code,
            "etag": normalized.get("etag"),
            "last_modified": normalized.get("last-modified"),
        },
    }


def conditional_request_headers(previous_snapshot: dict | None) -> dict:
    http = (previous_snapshot or {}).get("http", {})
    headers = {}
    if http.get("etag"):
        headers["If-None-Match"] = http["etag"]
    if http.get("last_modified"):
        headers["If-Modified-Since"] = http["last_modified"]
    return headers


def build_source_snapshot(
    *, source: dict, registry_version: str, stored_object: StoredObject,
    acquired_at: str, mime_type: str, acquisition_status: str, http: dict,
) -> dict:
    identity = "\0".join([
        source["source_id"], stored_object.digest, source["acquisition"]["origin_locator"]
    ])
    snapshot_id = "snapshot_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return {
        "schema_version": "source_snapshot_v1",
        "snapshot_id": snapshot_id,
        "source_id": source["source_id"],
        "registry_version": registry_version,
        "object_digest": stored_object.digest,
        "object_path": stored_object.relative_path,
        "byte_size": stored_object.byte_size,
        "mime_type": mime_type or "application/octet-stream",
        "acquired_at": acquired_at,
        "acquisition_status": acquisition_status,
        "origin_locator": source["acquisition"]["origin_locator"],
        "license": dict(source["license"]),
        "http": {
            "status_code": http.get("status_code"),
            "etag": http.get("etag"),
            "last_modified": http.get("last_modified"),
        },
    }
