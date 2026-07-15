"""运行期 dense 检索使用的 NumPy 快速向量索引。"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np


SCHEMA_VERSION = "fast_vector_index_v2"


@dataclass(frozen=True)
class FastVectorIndexArtifacts:
    source_path: Path
    matrix_path: Path
    metadata_path: Path
    manifest_path: Path

    @classmethod
    def from_index_path(cls, index_path: Path | str) -> "FastVectorIndexArtifacts":
        source_path = Path(index_path)
        stem = source_path.stem
        if stem.endswith("_index"):
            stem = stem.removesuffix("_index")
        return cls(
            source_path=source_path,
            matrix_path=source_path.with_name(f"{stem}_matrix.npy"),
            metadata_path=source_path.with_name(f"{stem}_metadata.jsonl"),
            manifest_path=source_path.with_name(f"{stem}_fast_manifest.json"),
        )

    def exists(self) -> bool:
        return self.matrix_path.exists() and self.metadata_path.exists() and self.manifest_path.exists()

    def cache_signature(self) -> tuple[tuple[str, int, int], ...] | None:
        if not self.exists():
            return None
        return tuple(_file_signature(path) for path in (self.matrix_path, self.metadata_path, self.manifest_path))


class FastVectorIndexError(RuntimeError):
    """快索引构建或读取失败。"""


class FastVectorIndex:
    def __init__(self, artifacts: FastVectorIndexArtifacts, matrix: Any, metadata: list[dict[str, Any]]):
        self.artifacts = artifacts
        self.matrix = matrix
        self.metadata = metadata

    @property
    def record_count(self) -> int:
        return int(self.matrix.shape[0])

    @property
    def dimension(self) -> int:
        return int(self.matrix.shape[1])

    @classmethod
    def load(
        cls,
        index_path: Path | str,
        *,
        validate_source_hash: bool = True,
    ) -> "FastVectorIndex | None":
        artifacts = FastVectorIndexArtifacts.from_index_path(index_path)
        if not artifacts.exists():
            return None
        manifest = _read_json(artifacts.manifest_path)
        if manifest.get("schema_version") != SCHEMA_VERSION:
            return None
        if validate_source_hash and not _source_matches_manifest(artifacts.source_path, manifest):
            return None

        matrix = np.load(artifacts.matrix_path, mmap_mode="r")
        if matrix.ndim != 2:
            raise FastVectorIndexError(f"{artifacts.matrix_path} 必须是二维矩阵")
        metadata = _load_jsonl(artifacts.metadata_path)
        if len(metadata) != int(matrix.shape[0]):
            raise FastVectorIndexError("快索引 metadata 行数与矩阵行数不一致")
        expected_dimension = manifest.get("dimension")
        if isinstance(expected_dimension, int) and expected_dimension != int(matrix.shape[1]):
            raise FastVectorIndexError("快索引 manifest 维度与矩阵维度不一致")
        return cls(artifacts, matrix, metadata)

    def search(self, query_vector: list[float], top_k: int, min_similarity: float) -> list[dict[str, Any]]:
        query = np.asarray(query_vector, dtype=np.float32)
        if query.ndim != 1 or query.shape[0] != self.dimension:
            raise ValueError(f"查询向量维度 {query.shape[0] if query.ndim == 1 else 'invalid'} 与索引维度 {self.dimension} 不一致")
        if not np.isfinite(query).all():
            raise ValueError("查询向量包含非 finite 数值")
        norm = float(np.linalg.norm(query))
        if not math.isfinite(norm) or norm == 0.0:
            raise ValueError("查询向量范数不能为零")
        query = query / norm

        scores = np.asarray(self.matrix @ query)
        if scores.size == 0:
            return []
        candidate_count = min(top_k, scores.size)
        if candidate_count == scores.size:
            candidate_indices = np.arange(scores.size)
        else:
            candidate_indices = np.argpartition(scores, -candidate_count)[-candidate_count:]

        candidates = []
        for index in candidate_indices.tolist():
            score = float(scores[index])
            if score < min_similarity:
                continue
            item = dict(self.metadata[index])
            item.update({"raw_score": score, "score": score, "channel": "vector"})
            candidates.append(item)
        candidates.sort(key=lambda item: (-float(item["raw_score"]), item.get("chunk_id", "")))
        for rank, item in enumerate(candidates[:top_k], start=1):
            item["raw_rank"] = rank
        return candidates[:top_k]


_FAST_INDEX_CACHE: dict[str, tuple[tuple[tuple[str, int, int], ...], FastVectorIndex]] = {}


def clear_fast_vector_index_cache() -> None:
    _FAST_INDEX_CACHE.clear()


def load_cached_fast_vector_index(index_path: Path | str) -> FastVectorIndex | None:
    artifacts = FastVectorIndexArtifacts.from_index_path(index_path)
    signature = artifacts.cache_signature()
    if signature is None:
        return None
    key = str(artifacts.source_path.resolve())
    cached = _FAST_INDEX_CACHE.get(key)
    if cached and cached[0] == signature:
        return cached[1]
    # 线上 release 在激活前已执行源 hash 门禁，运行期只加载不可变 mmap，
    # 避免冷启动重新顺序读取大型 JSONL。直接 load/发布验证仍默认校验源 hash。
    loaded = FastVectorIndex.load(artifacts.source_path, validate_source_hash=False)
    if loaded is None:
        return None
    _FAST_INDEX_CACHE[key] = (signature, loaded)
    return loaded


def build_fast_vector_index(index_path: Path | str) -> FastVectorIndexArtifacts:
    index_path = Path(index_path)
    artifacts = FastVectorIndexArtifacts.from_index_path(index_path)
    if not index_path.exists():
        raise FileNotFoundError(index_path)

    dimension: int | None = None
    total_rows = 0
    skipped_non_chunk = 0
    record_count = 0
    eligible_chunk_ids: list[str] = []
    retrieval_input_manifest_hashes: set[str] = set()

    with index_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            total_rows += 1
            record = json.loads(line)
            if record.get("kind", "chunk") != "chunk":
                skipped_non_chunk += 1
                continue
            vector = _validated_vector(record.get("vector"), line_number)
            if dimension is None:
                dimension = len(vector)
            elif len(vector) != dimension:
                raise FastVectorIndexError(f"索引第 {line_number} 行向量维度不一致")
            metadata = _metadata_row(record, line_number)
            eligible_chunk_ids.append(metadata["chunk_id"])
            if record.get("retrieval_input_manifest_hash"):
                retrieval_input_manifest_hashes.add(record["retrieval_input_manifest_hash"])
            record_count += 1

    if not record_count or dimension is None:
        raise FastVectorIndexError("Dense JSONL 索引没有可用 chunk 向量")
    if len(set(eligible_chunk_ids)) != len(eligible_chunk_ids):
        raise FastVectorIndexError("Dense JSONL 索引包含重复 chunk_id")
    if len(retrieval_input_manifest_hashes) > 1:
        raise FastVectorIndexError("Dense JSONL 索引混用了 retrieval input manifest")

    artifacts.matrix_path.parent.mkdir(parents=True, exist_ok=True)
    matrix_tmp = artifacts.matrix_path.with_name(f".{artifacts.matrix_path.name}.tmp")
    metadata_tmp = artifacts.metadata_path.with_name(f".{artifacts.metadata_path.name}.tmp")
    for temporary in (matrix_tmp, metadata_tmp):
        if temporary.exists():
            temporary.unlink()
    matrix = np.lib.format.open_memmap(
        matrix_tmp,
        mode="w+",
        dtype=np.float32,
        shape=(record_count, dimension),
    )
    row_index = 0
    try:
        with index_path.open(encoding="utf-8") as source, metadata_tmp.open("w", encoding="utf-8") as metadata_handle:
            for line_number, line in enumerate(source, start=1):
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("kind", "chunk") != "chunk":
                    continue
                vector = np.asarray(_validated_vector(record.get("vector"), line_number), dtype=np.float32)
                if vector.shape != (dimension,):
                    raise FastVectorIndexError(f"索引第 {line_number} 行向量维度不一致")
                norm = float(np.linalg.norm(vector))
                if not math.isfinite(norm) or norm == 0.0:
                    raise FastVectorIndexError("Dense JSONL 索引包含零范数或非 finite 向量")
                matrix[row_index] = vector / norm
                metadata_handle.write(
                    json.dumps(_metadata_row(record, line_number), ensure_ascii=False, separators=(",", ":")) + "\n"
                )
                row_index += 1
            metadata_handle.flush()
            os.fsync(metadata_handle.fileno())
        matrix.flush()
        if row_index != record_count:
            raise FastVectorIndexError("快索引两阶段读取的记录数不一致")
        del matrix
        matrix = None
        matrix_tmp.replace(artifacts.matrix_path)
        metadata_tmp.replace(artifacts.metadata_path)
    except Exception:
        if matrix is not None:
            del matrix
        for temporary in (matrix_tmp, metadata_tmp):
            if temporary.exists():
                temporary.unlink()
        raise

    stat = index_path.stat()
    _atomic_write_json(
        artifacts.manifest_path,
        {
            "schema_version": SCHEMA_VERSION,
            "source_path": str(index_path),
            "source_index_sha256": _sha256_file(index_path),
            "source_size_bytes": stat.st_size,
            "source_mtime_ns": stat.st_mtime_ns,
            "matrix_file": artifacts.matrix_path.name,
            "metadata_file": artifacts.metadata_path.name,
            "dtype": "float32",
            "normalized": True,
            "dimension": dimension,
            "record_count": record_count,
            "source_row_count": total_rows,
            "skipped_non_chunk_count": skipped_non_chunk,
            "eligible_chunk_ids_hash": _string_set_hash(eligible_chunk_ids),
            "retrieval_input_manifest_hash": next(iter(retrieval_input_manifest_hashes), None),
            "build_strategy": "two_pass_preallocated_memmap_v1",
            "matrix_sha256": _sha256_file(artifacts.matrix_path),
            "metadata_sha256": _sha256_file(artifacts.metadata_path),
        },
    )
    clear_fast_vector_index_cache()
    return artifacts


def _metadata_row(record: dict[str, Any], line_number: int) -> dict[str, Any]:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    chunk_id = metadata.get("chunk_id") or record.get("chunk_id")
    if not chunk_id and str(record.get("doc_id", "")).startswith("chunk:"):
        chunk_id = str(record["doc_id"]).split(":", 1)[1]
    if not chunk_id:
        raise FastVectorIndexError(f"索引第 {line_number} 行缺少 chunk_id")
    row = {key: value for key, value in record.items() if key != "vector"}
    row.update(metadata)
    row["chunk_id"] = chunk_id
    return row


def _validated_vector(vector: Any, line_number: int) -> list[float]:
    if not isinstance(vector, list) or not vector:
        raise FastVectorIndexError(f"索引第 {line_number} 行向量必须是非空数组")
    values = []
    for value in vector:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise FastVectorIndexError(f"索引第 {line_number} 行向量包含非 finite 数值")
        values.append(float(value))
    return values


def _source_matches_manifest(source_path: Path, manifest: dict[str, Any]) -> bool:
    if not source_path.exists():
        return True
    return manifest.get("source_index_sha256") == _sha256_file(source_path)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _string_set_hash(values: Any) -> str:
    encoded = json.dumps(sorted(set(values)), ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def verify_fast_vector_artifacts(
    index_path: Path | str,
    *,
    eligible_chunk_ids: set[str],
) -> dict[str, Any]:
    artifacts = FastVectorIndexArtifacts.from_index_path(index_path)
    required = {
        "matrix": artifacts.matrix_path,
        "metadata": artifacts.metadata_path,
        "manifest": artifacts.manifest_path,
    }
    for name, path in required.items():
        if not path.is_file():
            raise FastVectorIndexError(f"缺少 fast {name} artifact：{path}")
    if not artifacts.source_path.is_file():
        raise FastVectorIndexError(f"缺少 fast source index：{artifacts.source_path}")
    manifest = _read_json(artifacts.manifest_path)
    if manifest.get("source_index_sha256") != _sha256_file(artifacts.source_path):
        raise FastVectorIndexError("fast manifest source index hash 已过期")
    loaded = FastVectorIndex.load(artifacts.source_path, validate_source_hash=False)
    if loaded is None:
        raise FastVectorIndexError("fast index 无法按当前 schema 与源 hash 加载")
    actual_ids = {str(item.get("chunk_id", "")) for item in loaded.metadata}
    if actual_ids != set(eligible_chunk_ids):
        raise FastVectorIndexError(
            "fast index eligibility 集合不一致："
            f"missing={sorted(set(eligible_chunk_ids) - actual_ids)[:5]}, "
            f"extra={sorted(actual_ids - set(eligible_chunk_ids))[:5]}"
        )
    expected_hash = _string_set_hash(eligible_chunk_ids)
    if manifest.get("eligible_chunk_ids_hash") != expected_hash:
        raise FastVectorIndexError("fast manifest eligibility hash 不一致")
    if manifest.get("matrix_sha256") != _sha256_file(artifacts.matrix_path):
        raise FastVectorIndexError("fast matrix hash 不一致")
    if manifest.get("metadata_sha256") != _sha256_file(artifacts.metadata_path):
        raise FastVectorIndexError("fast metadata hash 不一致")
    return manifest


def _file_signature(path: Path) -> tuple[str, int, int]:
    stat = path.stat()
    return (str(path.resolve()), stat.st_size, stat.st_mtime_ns)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise FastVectorIndexError(f"{path} 第 {line_number} 行 JSON 非法：{exc}") from exc
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FastVectorIndexError(f"{path} JSON 非法：{exc}") from exc


def _atomic_save_npy(path: Path, matrix: Any) -> None:
    tmp_path = path.with_name(f".{path.name}.tmp")
    with tmp_path.open("wb") as handle:
        np.save(handle, matrix)
    tmp_path.replace(path)


def _atomic_write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    tmp_path = path.with_name(f".{path.name}.tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    tmp_path.replace(path)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)
