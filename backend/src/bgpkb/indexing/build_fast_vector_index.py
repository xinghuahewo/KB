"""为在线 dense 检索构建 NumPy 快速向量索引。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bgpkb import paths
from bgpkb.infrastructure.fast_vector_index import (
    FastVectorIndex,
    build_fast_vector_index,
    verify_fast_vector_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="构建 BGE-M3 dense 检索快索引")
    parser.add_argument(
        "--index-path",
        type=Path,
        default=paths.PUBLISHED_DIR / "bge_m3_vector_index.jsonl",
        help="源 JSONL 向量索引路径",
    )
    args = parser.parse_args(argv)

    artifacts = build_fast_vector_index(args.index_path)
    loaded = FastVectorIndex.load(args.index_path, validate_source_hash=False)
    if loaded is None:
        raise RuntimeError("快索引构建后无法重新加载")
    eligible_chunk_ids = {str(item["chunk_id"]) for item in loaded.metadata}
    verify_fast_vector_artifacts(args.index_path, eligible_chunk_ids=eligible_chunk_ids)
    manifest = json.loads(artifacts.manifest_path.read_text(encoding="utf-8"))
    print(json.dumps({
        "ok": True,
        "matrix_path": str(artifacts.matrix_path),
        "metadata_path": str(artifacts.metadata_path),
        "manifest_path": str(artifacts.manifest_path),
        "record_count": manifest["record_count"],
        "dimension": manifest["dimension"],
        "source_row_count": manifest["source_row_count"],
        "skipped_non_chunk_count": manifest["skipped_non_chunk_count"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
