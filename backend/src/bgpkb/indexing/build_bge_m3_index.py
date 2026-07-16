#!/usr/bin/env python3
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile

from bgpkb import paths
from bgpkb.infrastructure.retrieval_model_client import EmbeddingProviderChain
from bgpkb.indexing.retrieval_documents import build_retrieval_input_manifest, embedding_cache_key


RETRIEVAL_DOCUMENTS_PATH = paths.PUBLISHED_DIR / "retrieval_documents_v1.jsonl"
INDEX_PATH = paths.PUBLISHED_DIR / "bge_m3_vector_index.jsonl"
MANIFEST_PATH = paths.PUBLISHED_DIR / "bge_m3_embedding_manifest.json"
REPORT_PATH = paths.GENERATED_REPORTS_DIR / "rag" / "bge_m3_embedding_report.md"
CHECKPOINT_PATH = paths.GENERATED_DIR / "checkpoints" / "bge_m3_embedding_checkpoint.json"


def load_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_embedding_documents(
    *,
    retrieval_documents,
    input_manifest,
):
    documents = []
    expected_version = input_manifest.get("retrieval_text_version")
    expected_hash = input_manifest.get("input_manifest_hash")
    for item in retrieval_documents:
        if item.get("schema_version") != "retrieval_document_v1":
            raise ValueError("Embedding 只接受 Retrieval Document v1，禁止 content_preview 输入")
        if item.get("retrieval_text_version") != expected_version:
            raise ValueError("Retrieval Document 与 embedding input manifest 版本不一致")
        text = item.get("retrieval_text")
        text_hash = item.get("retrieval_text_hash")
        if not isinstance(text, str) or "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest() != text_hash:
            raise ValueError("Retrieval Document retrieval_text hash 非法")
        governance = item.get("governance")
        eligibility = item.get("eligibility")
        if not isinstance(governance, dict) or not isinstance(eligibility, dict):
            raise ValueError("Retrieval Document 缺少独立治理状态或资格审计")
        documents.append({
            "doc_id": item["retrieval_doc_id"],
            "kind": "chunk",
            "text": text,
            "retrieval_text_hash": text_hash,
            "retrieval_text_version": item["retrieval_text_version"],
            "retrieval_input_manifest_hash": expected_hash,
            "source_ref": item["source_ref"],
            "source_refs": item["source_refs"],
            "source_type": item["document_profile"],
            "review_status": "",
            "lifecycle_status": eligibility["status"],
            "trusted": (
                eligibility["status"] == "eligible"
                and governance.get("source_trust_status") == "trusted"
            ),
            "trust_basis": eligibility["rule_id"],
            "governance": governance,
            "eligibility": eligibility,
            "metadata": item,
        })
    return documents


def load_documents():
    retrieval_documents = load_jsonl(RETRIEVAL_DOCUMENTS_PATH)
    if not retrieval_documents:
        raise ValueError(f"缺少 Retrieval Document v1：{RETRIEVAL_DOCUMENTS_PATH}")
    input_manifest = build_retrieval_input_manifest(retrieval_documents)
    return build_embedding_documents(
        retrieval_documents=retrieval_documents,
        input_manifest=input_manifest,
    )


def normalize_vector(vector):
    magnitude = math.sqrt(sum(float(value) ** 2 for value in vector))
    if magnitude == 0:
        return [0.0 for _ in vector]
    return [float(value) / magnitude for value in vector]


def input_hash(documents):
    digest = hashlib.sha256()
    for item in documents:
        digest.update(item["doc_id"].encode("utf-8"))
        digest.update(item["text"].encode("utf-8"))
    return digest.hexdigest()


def _fingerprint(payload):
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def render_report(manifest):
    status = manifest["status"]
    lines = [
        "# BGE-M3 Embedding 构建报告",
        "",
        "## 摘要",
        "",
        f"- 状态：{status}",
        f"- Provider：`{manifest['provider']}`",
        f"- 模型：`{manifest['model']}`",
        f"- 输入数量：{manifest['input_count']}",
        f"- 向量维度：{manifest.get('dimension', 0)}",
        f"- 真实远程模型调用：{'是' if manifest.get('real_model_execution') else '否'}",
        "- 当前设备未运行本地模型。",
        "- 未修改实体、关系、chunk、术语表或复核状态。",
        "",
        "## 输入数据",
        "",
    ]
    for kind, count in manifest["source_counts"].items():
        lines.append(f"- {kind}：{count}")
    lines.extend(["", "## 运行说明", ""])
    if manifest.get("error_code") in {"missing_api_key", "missing_endpoint"}:
        lines.append("- 未配置远程 API key，已跳过真实 embedding 构建；离线测试仍可使用 fake client。")
    elif status == "failed":
        lines.append(f"- 构建失败：{manifest.get('error', manifest.get('error_code', '未知错误'))}。")
    else:
        lines.append("- 向量已进行 L2 归一化并写入文件化 JSONL 索引。")
    return "\n".join(lines).rstrip() + "\n"


def _atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _complete_artifacts(index_path, manifest_path, report_path):
    if not all(path.exists() for path in (index_path, manifest_path, report_path)):
        return False
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8")).get("status") == "complete"
    except (OSError, json.JSONDecodeError):
        return False


def _provider_chain(result, fallback):
    names = [item.get("provider") for item in result.get("attempts", []) if item.get("provider")]
    provider = result.get("provider") or fallback
    if provider and provider not in names:
        names.append(provider)
    return names


def _load_checkpoint(path):
    if not path.exists():
        return {"schema_version": "embedding_checkpoint_v1", "entries": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": "embedding_checkpoint_v1", "entries": {}}
    if payload.get("schema_version") != "embedding_checkpoint_v1" or not isinstance(payload.get("entries"), dict):
        return {"schema_version": "embedding_checkpoint_v1", "entries": {}}
    return payload


def _write_checkpoint(path, checkpoint, completed_count):
    checkpoint["completed_count"] = completed_count
    _atomic_write(path, json.dumps(checkpoint, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _vector_error(vectors, expected_count, expected_dimension=0):
    if not isinstance(vectors, list) or len(vectors) != expected_count:
        return "Embedding 数量与输入不一致"
    dimension = len(vectors[0]) if vectors and isinstance(vectors[0], list) else 0
    if expected_dimension and dimension != expected_dimension:
        return "不同批次的向量维度不一致"
    if not dimension or any(
        not isinstance(vector, list) or len(vector) != dimension
        or any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in vector)
        or not any(float(value) != 0.0 for value in vector)
        for vector in vectors
    ):
        return "Embedding 向量维度、数值或范数无效"
    return ""


def _failed_build(manifest, result, index_path, manifest_path, report_path):
    manifest.update({
        "status": "failed",
        "error_code": result.get("error_code", "embedding_failed"),
        "error": result.get("error", "Embedding provider 不可用"),
        "real_model_execution": False,
        "preserved_previous_artifacts": _complete_artifacts(index_path, manifest_path, report_path),
    })
    if not manifest["preserved_previous_artifacts"]:
        _atomic_write(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        _atomic_write(report_path, render_report(manifest))
    return manifest


def _index_record(document, vector):
    return {
        "doc_id": document["doc_id"],
        "kind": document["kind"],
        "source_ref": document["source_ref"],
        "source_refs": document["source_refs"],
        "source_type": document["source_type"],
        "review_status": document["review_status"],
        "lifecycle_status": document["lifecycle_status"],
        "trusted": document["trusted"],
        "trust_basis": document["trust_basis"],
        "governance": document["governance"],
        "eligibility": document["eligibility"],
        "text": document["text"],
        "text_hash": hashlib.sha256(document["text"].encode("utf-8")).hexdigest(),
        "retrieval_text_hash": document["retrieval_text_hash"],
        "retrieval_text_version": document["retrieval_text_version"],
        "retrieval_input_manifest_hash": document["retrieval_input_manifest_hash"],
        "metadata": document["metadata"],
        "vector": vector,
        "generated_by": "src/bgpkb/pipeline/build_bge_m3_index.py",
    }


def build_index(
    documents,
    client,
    index_path=INDEX_PATH,
    manifest_path=MANIFEST_PATH,
    report_path=REPORT_PATH,
    batch_size=32,
    checkpoint_path=None,
    model_revision=None,
):
    versions = {item.get("retrieval_text_version") for item in documents}
    input_manifest_hashes = {item.get("retrieval_input_manifest_hash") for item in documents}
    if versions != {"retrieval_text_v1"} or len(input_manifest_hashes) != 1 or None in input_manifest_hashes:
        raise ValueError("Embedding 输入必须来自同一份 Retrieval Document v1 manifest")
    if not documents:
        raise ValueError("Embedding 输入不能为空")
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    counts = dict(sorted(Counter(item["kind"] for item in documents).items()))
    model = getattr(client, "model", "BAAI/bge-m3")
    resolved_revision = model_revision or getattr(client, "model_revision", "") or getattr(client, "revision", "")
    if not resolved_revision:
        raise ValueError("Embedding 构建必须固定 model revision")
    normalization = "l2_v1"
    provider_contract = getattr(
        client,
        "provider_contract",
        f"embedding_provider_chain_v1:{getattr(client, 'provider', 'provider_chain')}",
    )
    provider_contract_fingerprint = _fingerprint({"provider_contract": provider_contract})
    if checkpoint_path:
        checkpoint_path = Path(checkpoint_path)
    elif Path(index_path).resolve() == INDEX_PATH.resolve():
        checkpoint_path = CHECKPOINT_PATH
    else:
        checkpoint_path = Path(index_path).with_name("bge_m3_embedding_checkpoint.json")
    checkpoint = _load_checkpoint(checkpoint_path)
    cache_entries = checkpoint["entries"]
    completed_cache_keys = set()
    manifest = {
        "status": "complete",
        "generated_at": generated_at,
        "generated_by": "src/bgpkb/pipeline/build_bge_m3_index.py",
        "provider": getattr(client, "provider", "provider_chain"),
        "model": model,
        "model_revision": resolved_revision,
        "model_hash": "",
        "provider_chain": [],
        "degraded_reason": None,
        "dimension": 0,
        "input_count": len(documents),
        "input_hash": input_hash(documents),
        "retrieval_text_version": versions.pop(),
        "retrieval_input_manifest_hash": input_manifest_hashes.pop(),
        "normalization": normalization,
        "normalization_fingerprint": _fingerprint({"algorithm": "l2", "version": "v1"}),
        "provider_contract": provider_contract,
        "provider_contract_fingerprint": provider_contract_fingerprint,
        "checkpoint_schema_version": "embedding_checkpoint_v1",
        "cache_hit_count": 0,
        "embedded_count": 0,
        "source_counts": counts,
        "real_model_execution": not bool(getattr(client, "is_fake", False)),
        "local_model_enabled": True,
    }
    records = []
    for offset in range(0, len(documents), batch_size):
        batch = documents[offset:offset + batch_size]
        keyed = []
        missing = []
        for document in batch:
            key = embedding_cache_key(
                document=document,
                model=model,
                model_revision=resolved_revision,
                normalization=normalization,
                provider_contract=provider_contract,
            )
            cached = cache_entries.get(key)
            vector = cached.get("vector") if isinstance(cached, dict) else None
            if _vector_error([vector], 1, manifest["dimension"]):
                missing.append((document, key))
                keyed.append((document, key, None))
            else:
                manifest["cache_hit_count"] += 1
                manifest["dimension"] = manifest["dimension"] or len(vector)
                completed_cache_keys.add(key)
                keyed.append((document, key, vector))

        if missing:
            result = client.embed_texts([document["text"] for document, _ in missing])
            if not result.get("ok"):
                return _failed_build(manifest, result, index_path, manifest_path, report_path)
            if result.get("revision") and result["revision"] != resolved_revision:
                return _failed_build(manifest, {
                    "error_code": "model_revision_mismatch",
                    "error": f"Embedding revision 不一致：{result['revision']} != {resolved_revision}",
                }, index_path, manifest_path, report_path)
            vectors = result.get("vectors")
            error = _vector_error(vectors, len(missing), manifest["dimension"])
            if error:
                return _failed_build(manifest, {
                    "error_code": "dimension_mismatch" if "不同批次" in error else "invalid_embeddings",
                    "error": error,
                }, index_path, manifest_path, report_path)
            dimension = len(vectors[0])
            manifest.update({
                "provider": result.get("provider", manifest["provider"]),
                "model": result.get("model", manifest["model"]),
                "model_hash": result.get("model_hash", result.get("model_sha256", manifest["model_hash"])),
                "provider_chain": _provider_chain(result, manifest["provider"]),
                "degraded_reason": result.get("degraded_reason") or manifest["degraded_reason"],
                "dimension": dimension,
                "embedded_count": manifest["embedded_count"] + len(missing),
            })
            embedded = {}
            for (document, key), vector in zip(missing, vectors):
                normalized = normalize_vector(vector)
                embedded[key] = normalized
                cache_entries[key] = {
                    "retrieval_doc_id": document["doc_id"],
                    "retrieval_text_hash": document["retrieval_text_hash"],
                    "model": model,
                    "model_revision": resolved_revision,
                    "normalization": normalization,
                    "provider_contract": provider_contract,
                    "vector": normalized,
                }
                completed_cache_keys.add(key)
            keyed = [
                (document, key, embedded.get(key, vector))
                for document, key, vector in keyed
            ]
            _write_checkpoint(checkpoint_path, checkpoint, len(completed_cache_keys))

        records.extend(_index_record(document, vector) for document, _, vector in keyed)
    index_content = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    _atomic_write(index_path, index_content)
    _atomic_write(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    _atomic_write(report_path, render_report(manifest))
    return manifest


def main():
    parser = argparse.ArgumentParser(description="使用本地优先 BGE-M3 provider chain 构建文件化向量索引。")
    parser.add_argument("--provider", choices=["siliconflow_bge_m3", "aliyun_eas_bge_m3"], default="siliconflow_bge_m3")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--model-revision",
        default=os.environ.get("BGP_EMBEDDING_MODEL_REVISION", ""),
        help="固定的 embedding 模型 revision；也可通过 BGP_EMBEDDING_MODEL_REVISION 设置",
    )
    parser.add_argument("--checkpoint-path", type=Path, default=None)
    args = parser.parse_args()
    if not args.model_revision:
        parser.error("必须通过 --model-revision 或 BGP_EMBEDDING_MODEL_REVISION 固定模型 revision")

    documents = load_documents()
    if args.limit > 0:
        documents = documents[:args.limit]
    manifest = build_index(
        documents=documents,
        client=EmbeddingProviderChain.from_env(),
        batch_size=args.batch_size,
        checkpoint_path=args.checkpoint_path,
        model_revision=args.model_revision,
    )
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
