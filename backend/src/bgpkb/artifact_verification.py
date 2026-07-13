"""Fail-closed verification for immutable BGP knowledge-base releases."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import sys

from bgpkb import paths
from bgpkb.artifact_registry import ArtifactRegistryError, load_release_registry
from bgpkb.infrastructure.fast_vector_index import (
    FastVectorIndex,
    FastVectorIndexArtifacts,
    FastVectorIndexError,
)


class ArtifactVerificationError(RuntimeError):
    pass


REQUIRED_FILES = (
    "published/bgp_knowledge_base.sqlite",
    "published/chunk_catalog.jsonl",
    "published/source_catalog.jsonl",
    "published/entity_catalog.jsonl",
    "published/bge_m3_vector_index.jsonl",
    "published/bge_m3_vector_matrix.npy",
    "published/bge_m3_vector_metadata.jsonl",
    "published/bge_m3_vector_fast_manifest.json",
    "published/bge_m3_embedding_manifest.json",
    "derived/datasets/entity_source_evidence.jsonl",
    "derived/datasets/section_catalog.jsonl",
)

DEFAULT_REGISTRY_PATH = paths.PROJECT_ROOT.parent / "artifacts" / "releases.yaml"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_checksums(release_root: Path) -> list[tuple[str, Path, str]]:
    checksum_path = release_root / "SHA256SUMS"
    if not checksum_path.is_file():
        raise ArtifactVerificationError(f"缺少 SHA256SUMS：{checksum_path}")
    entries = []
    seen_paths = set()
    for line_number, line in enumerate(checksum_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            raise ArtifactVerificationError(f"SHA256SUMS 第 {line_number} 行格式非法")
        relative_path = match.group(2)
        if relative_path in seen_paths:
            raise ArtifactVerificationError(f"SHA256SUMS 路径重复：{relative_path}")
        seen_paths.add(relative_path)
        candidate = (release_root / relative_path).resolve()
        try:
            candidate.relative_to(release_root.resolve())
        except ValueError as exc:
            raise ArtifactVerificationError(f"SHA256SUMS 路径越界：{relative_path}") from exc
        if not relative_path.startswith("data/"):
            raise ArtifactVerificationError(f"SHA256SUMS 只能登记 data/ 文件：{relative_path}")
        entries.append((match.group(1), candidate, relative_path))
    if not entries:
        raise ArtifactVerificationError("SHA256SUMS 不能为空")
    return entries


def verify_artifact_release(data_dir: Path) -> dict:
    data_dir = Path(data_dir).resolve()
    if data_dir.name != "data" or not data_dir.is_dir():
        raise ArtifactVerificationError(f"数据根目录必须是存在的 release/data：{data_dir}")
    release_root = data_dir.parent

    for relative_path in REQUIRED_FILES:
        path = data_dir / relative_path
        if not path.is_file():
            raise ArtifactVerificationError(f"缺少必需运行制品：{relative_path}")
        if path.stat().st_size == 0 and relative_path.startswith("published/"):
            raise ArtifactVerificationError(f"必需运行制品为空：{relative_path}")

    entries = _load_checksums(release_root)
    expected_paths = {relative for _, _, relative in entries}
    actual_paths = {
        path.relative_to(release_root).as_posix()
        for path in data_dir.rglob("*")
        if path.is_file()
    }
    if expected_paths != actual_paths:
        missing = sorted(actual_paths - expected_paths)
        extra = sorted(expected_paths - actual_paths)
        raise ArtifactVerificationError(
            f"SHA256SUMS 文件集合不完整：未登记={missing[:5]}，不存在={extra[:5]}"
        )
    for expected, path, _ in entries:
        if not path.is_file() or _sha256(path) != expected:
            raise ArtifactVerificationError(f"SHA-256 校验失败：{path.relative_to(release_root)}")

    database_path = data_dir / "published" / "bgp_knowledge_base.sqlite"
    try:
        uri = f"file:{database_path.as_posix()}?mode=ro&immutable=1"
        with sqlite3.connect(uri, uri=True) as conn:
            sqlite_integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    except sqlite3.Error as exc:
        raise ArtifactVerificationError(f"SQLite 完整性检查失败：{exc}") from exc
    if sqlite_integrity != "ok":
        raise ArtifactVerificationError(f"SQLite 完整性检查失败：{sqlite_integrity}")

    manifest_path = data_dir / "published" / "bge_m3_embedding_manifest.json"
    try:
        vector_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactVerificationError(f"向量索引元数据不可读：{exc}") from exc
    dimension = vector_manifest.get("dimension", vector_manifest.get("dimensions"))
    if vector_manifest.get("status") != "complete" or not isinstance(dimension, int) or dimension <= 0:
        raise ArtifactVerificationError("向量索引元数据未达到 complete 状态或缺少有效维度")

    vector_count = 0
    vector_index_path = data_dir / "published" / "bge_m3_vector_index.jsonl"
    try:
        with vector_index_path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                record = json.loads(line)
                vector = record.get("vector")
                if (
                    not isinstance(vector, list)
                    or len(vector) != dimension
                    or any(
                        isinstance(value, bool)
                        or not isinstance(value, (int, float))
                        or not math.isfinite(value)
                        for value in vector
                    )
                ):
                    raise ArtifactVerificationError(f"向量索引第 {line_number} 行向量维度或数值无效")
                vector_count += 1
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactVerificationError(f"向量索引不可读：{exc}") from exc
    expected_vector_count = vector_manifest.get("record_count", vector_manifest.get("input_count"))
    if not isinstance(expected_vector_count, int) or vector_count != expected_vector_count:
        raise ArtifactVerificationError(
            f"向量索引记录数与元数据不一致：{vector_count} != {expected_vector_count}"
        )

    fast_artifacts = FastVectorIndexArtifacts.from_index_path(vector_index_path)
    try:
        fast_index = FastVectorIndex.load(vector_index_path)
    except (FastVectorIndexError, OSError, ValueError, json.JSONDecodeError) as exc:
        raise ArtifactVerificationError(f"快向量索引不可读：{exc}") from exc
    if fast_index is None:
        raise ArtifactVerificationError(
            f"快向量索引过期或 manifest 无效：{fast_artifacts.manifest_path.relative_to(data_dir)}"
        )
    if fast_index.record_count != vector_count:
        raise ArtifactVerificationError(
            f"快向量索引记录数不一致：{fast_index.record_count} != {vector_count}"
        )
    if fast_index.dimension != dimension:
        raise ArtifactVerificationError(
            f"快向量索引维度不一致：{fast_index.dimension} != {dimension}"
        )

    return {
        "release_id": release_root.name,
        "data_dir": str(data_dir),
        "file_count": len(entries),
        "sha256sums_sha256": _sha256(release_root / "SHA256SUMS"),
        "sqlite_integrity": sqlite_integrity,
        "vector_index_status": vector_manifest["status"],
        "vector_dimension": dimension,
        "vector_record_count": vector_count,
        "vector_index_mode": "fast_numpy",
        "fast_vector_record_count": fast_index.record_count,
    }


def verify_artifact_workspace(source_data_dir: Path, workspace_data_dir: Path) -> None:
    source_data_dir = Path(source_data_dir).resolve()
    workspace_data_dir = Path(workspace_data_dir).resolve()
    entries = _load_checksums(source_data_dir.parent)
    expected_workspace_paths = {
        Path(relative).relative_to("data").as_posix()
        for _, _, relative in entries
    }
    actual_workspace_paths = {
        path.relative_to(workspace_data_dir).as_posix()
        for path in workspace_data_dir.rglob("*")
        if path.is_file()
    }
    if expected_workspace_paths != actual_workspace_paths:
        raise ArtifactVerificationError("测试工作区文件集合与源 release 不一致")
    for expected_hash, _, relative in entries:
        workspace_path = workspace_data_dir / Path(relative).relative_to("data")
        if _sha256(workspace_path) != expected_hash:
            raise ArtifactVerificationError(f"测试工作区哈希不一致：{relative}")


def verify_registered_artifact_release(
    data_dir: Path,
    release_id: str | None = None,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
) -> dict:
    result = verify_artifact_release(data_dir)
    selected_release_id = release_id or result["release_id"]
    if selected_release_id != result["release_id"]:
        raise ArtifactVerificationError(
            f"BGPKB_RELEASE_ID 与数据目录不一致：{selected_release_id} != {result['release_id']}"
        )
    try:
        registry = load_release_registry(Path(registry_path))
    except ArtifactRegistryError as exc:
        raise ArtifactVerificationError(f"制品注册表无效：{exc}") from exc
    release = next(
        (item for item in registry["releases"] if item["release_id"] == selected_release_id),
        None,
    )
    if release is None:
        raise ArtifactVerificationError(f"release 未登记：{selected_release_id}")
    expected = {
        "file_count": release["file_count"],
        "sha256sums_sha256": release["sha256sums_sha256"],
    }
    for field, expected_value in expected.items():
        if result[field] != expected_value:
            raise ArtifactVerificationError(
                f"release {field} 与注册表不一致：{result[field]} != {expected_value}"
            )
    if Path(release["data_path"]).resolve() != Path(data_dir).resolve():
        raise ArtifactVerificationError("release data_path 与注册表不一致")
    return result


def main() -> int:
    try:
        result = verify_registered_artifact_release(paths.require_runtime_data_dir())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
