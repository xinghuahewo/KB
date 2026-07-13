#!/usr/bin/env python3
import argparse
import hashlib
import json
import sys
from pathlib import Path

from bgpkb import paths

import yaml


ROOT = paths.PROJECT_ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgpkb.service import retrieval_framework


CONFIG = paths.CONFIG_DIR / "rag_retrieval.yaml"
CHUNKS = paths.PUBLISHED_DIR / "chunk_catalog.jsonl"
VECTOR_INDEX = paths.PUBLISHED_DIR / "rag_mock_vector_index.jsonl"
MANIFEST = paths.PUBLISHED_DIR / "embedding_manifest.json"
RETRIEVAL_INDEX = paths.PUBLISHED_DIR / "rag_retrieval_index.json"


class BgeM3EmbeddingProvider:
    def __init__(self, enabled=False, model="BAAI/bge-m3"):
        self.enabled = enabled
        self.model = model

    def embed(self, texts):
        if not self.enabled:
            raise RuntimeError("BGE-M3 provider is disabled; enable it explicitly on a model-capable device")
        try:
            from FlagEmbedding import BGEM3FlagModel
        except ImportError as exc:
            raise RuntimeError("BGE-M3 provider requires requirements-rag.txt dependencies") from exc
        model = BGEM3FlagModel(self.model, use_fp16=False)
        return model.encode(texts, return_dense=True, return_sparse=True, return_colbert_vecs=False)


def load_config():
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def input_hash(chunks):
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk.get("chunk_id", "").encode("utf-8"))
        digest.update(chunk.get("content_preview", "").encode("utf-8"))
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Build RAG retrieval indexes without running local models by default.")
    parser.add_argument("--provider", default=None)
    args = parser.parse_args()
    cfg = load_config()
    provider = args.provider or cfg["embedding"]["default_provider"]
    if provider == "bge_m3" and not cfg["embedding"]["providers"]["bge_m3"].get("enabled", False):
        raise SystemExit("bge_m3 provider is disabled; current-device framework uses deterministic_mock")

    chunks = retrieval_framework.load_jsonl(CHUNKS)
    chunk_uris = retrieval_framework.semantic_uri_map("chunk")
    dimensions = int(cfg["embedding"]["providers"]["deterministic_mock"]["dimensions"])
    records = []
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", "")
        text = " ".join([chunk_id, chunk.get("title", ""), chunk.get("content_preview", "")])
        records.append({
            "@id": chunk_uris.get(chunk_id, ""),
            "chunk_id": chunk_id,
            "source_ref": chunk.get("source_ref", ""),
            "review_status": chunk.get("review_status", ""),
            "source_type": chunk.get("source_type", ""),
            "topics": chunk.get("topics", []),
            "vector": retrieval_framework.stable_vector(text, dimensions=dimensions),
            "generated_by": "src/bgpkb/pipeline/build_rag_indexes.py",
        })

    retrieval_framework.write_jsonl(VECTOR_INDEX, records)
    manifest = {
        "generated_by": "src/bgpkb/pipeline/build_rag_indexes.py",
        "provider": "deterministic_mock",
        "model": "deterministic_mock_v1",
        "real_model_execution": False,
        "bge_m3_ready": True,
        "bge_m3_model": cfg["embedding"]["providers"]["bge_m3"]["model"],
        "dense_dimension": dimensions,
        "sparse_enabled": True,
        "colbert_enabled": False,
        "input_count": len(records),
        "input_hash": input_hash(chunks),
    }
    retrieval_framework.write_json(MANIFEST, manifest)
    retrieval_framework.write_json(RETRIEVAL_INDEX, {
        "generated_by": "src/bgpkb/pipeline/build_rag_indexes.py",
        "vector_store": {
            "provider": "mock_jsonl",
            "path": paths.rel(VECTOR_INDEX),
            "real_milvus_execution": False,
            "milvus_lite_ready": True,
        },
        "embedding_manifest": paths.rel(MANIFEST),
        "lexical_fallback": cfg["lexical_fallback"],
        "semantic_identity": "data/published/semantic_id_map.jsonl",
        "trusted_collection": cfg["trusted_collection"],
    })
    print(f"Wrote {paths.rel(VECTOR_INDEX)}")
    print(f"Wrote {paths.rel(MANIFEST)}")
    print(f"Wrote {paths.rel(RETRIEVAL_INDEX)}")


if __name__ == "__main__":
    main()
