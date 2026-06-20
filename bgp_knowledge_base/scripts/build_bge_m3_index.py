#!/usr/bin/env python3
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from service.bge_m3_remote_client import BgeM3RemoteClient  # noqa: E402


CHUNKS_PATH = ROOT / "published" / "chunk_catalog.jsonl"
ENTITIES_PATH = ROOT / "published" / "entity_catalog.jsonl"
GLOSSARY_PATH = ROOT / "datasets" / "glossary.jsonl"
EVIDENCE_TEMPLATES_PATH = ROOT / "entities" / "evidence_templates.jsonl"
ENTITY_EVIDENCE_PATH = ROOT / "datasets" / "entity_source_evidence.jsonl"
INDEX_PATH = ROOT / "published" / "bge_m3_vector_index.jsonl"
MANIFEST_PATH = ROOT / "published" / "bge_m3_embedding_manifest.json"
REPORT_PATH = ROOT / "reports" / "bge_m3_embedding_report.md"


def load_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _join(values):
    return ", ".join(str(value) for value in values or [] if value)


def _document(doc_id, kind, text, record, source_refs=None, trusted=False):
    refs = source_refs or []
    return {
        "doc_id": doc_id,
        "kind": kind,
        "text": text.strip(),
        "source_ref": refs[0] if refs else record.get("source_ref", ""),
        "source_refs": refs,
        "source_type": record.get("source_type", kind),
        "review_status": record.get("review_status", ""),
        "lifecycle_status": record.get("lifecycle_status", "approved" if trusted else "candidate"),
        "trusted": trusted,
        "metadata": record,
    }


def build_embedding_documents(chunks, entities, glossary, evidence_templates, trusted_chunk_ids=None):
    trusted_chunk_ids = set(trusted_chunk_ids or [])
    documents = []
    for item in chunks:
        chunk_id = item.get("chunk_id", "")
        text = "\n".join([
            f"title: {item.get('title', '')}",
            f"kind: chunk",
            f"source_type: {item.get('source_type', '')}",
            f"topics: {_join(item.get('topics', []))}",
            f"section: {_join(item.get('section_path', []))}",
            f"content: {item.get('content_preview', '')}",
        ])
        trusted = item.get("review_status") == "approved" or chunk_id in trusted_chunk_ids
        documents.append(_document(
            f"chunk:{chunk_id}",
            "chunk",
            text,
            item,
            source_refs=[item.get("source_ref", "")] if item.get("source_ref") else [],
            trusted=trusted,
        ))

    for item in entities:
        payload = item.get("entity_payload", {})
        aliases = item.get("aliases") or payload.get("aliases", [])
        refs = item.get("source_refs") or payload.get("source_refs", [])
        text = "\n".join([
            f"name: {item.get('name', '')}",
            f"kind: entity",
            f"entity_type: {item.get('entity_type', '')}",
            f"category: {item.get('category', '')}",
            f"aliases: {_join(aliases)}",
            f"definition: {payload.get('definition', '')}",
            f"related_concepts: {_join(payload.get('related_concepts', []))}",
        ])
        documents.append(_document(
            f"entity:{item.get('entity_id', '')}",
            "entity",
            text,
            item,
            source_refs=refs,
            trusted=item.get("review_status") == "approved",
        ))

    for item in glossary:
        refs = item.get("source_refs", [])
        text = "\n".join([
            f"term: {item.get('term', '')}",
            f"kind: glossary",
            f"entity_type: {item.get('entity_type', '')}",
            f"aliases: {_join(item.get('aliases', []))}",
            f"definition: {item.get('definition', '')}",
        ])
        documents.append(_document(
            f"glossary:{item.get('term_id', '')}",
            "glossary",
            text,
            item,
            source_refs=refs,
            trusted=item.get("review_status") == "approved",
        ))

    for item in evidence_templates:
        refs = item.get("source_refs", [])
        text = "\n".join([
            f"name: {item.get('id', '')}",
            f"kind: evidence_template",
            f"applies_to: {item.get('applies_to', '')}",
            f"required_evidence: {_join(item.get('required_evidence', []))}",
            f"optional_evidence: {_join(item.get('optional_evidence', []))}",
            f"false_positive_checks: {_join(item.get('false_positive_checks', []))}",
        ])
        documents.append(_document(
            f"evidence_template:{item.get('id', '')}",
            "evidence_template",
            text,
            item,
            source_refs=refs,
            trusted=item.get("review_status") == "approved",
        ))
    return documents


def trusted_chunk_ids(entity_evidence):
    trusted = set()
    for item in entity_evidence:
        if item.get("entity_review_status") == "approved":
            trusted.update(item.get("chunk_sample_ids", []))
    return trusted


def load_documents():
    evidence = load_jsonl(ENTITY_EVIDENCE_PATH)
    return build_embedding_documents(
        chunks=load_jsonl(CHUNKS_PATH),
        entities=load_jsonl(ENTITIES_PATH),
        glossary=load_jsonl(GLOSSARY_PATH),
        evidence_templates=load_jsonl(EVIDENCE_TEMPLATES_PATH),
        trusted_chunk_ids=trusted_chunk_ids(evidence),
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
    if status == "skipped":
        lines.append("- 未配置远程 API key，已跳过真实 embedding 构建；离线测试仍可使用 fake client。")
    else:
        lines.append("- 向量已进行 L2 归一化并写入文件化 JSONL 索引。")
    return "\n".join(lines).rstrip() + "\n"


def build_index(documents, client, index_path=INDEX_PATH, manifest_path=MANIFEST_PATH, report_path=REPORT_PATH, batch_size=32):
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    counts = dict(sorted(Counter(item["kind"] for item in documents).items()))
    manifest = {
        "status": "complete",
        "generated_at": generated_at,
        "generated_by": "scripts/build_bge_m3_index.py",
        "provider": client.provider,
        "model": client.model,
        "dimension": 0,
        "input_count": len(documents),
        "input_hash": input_hash(documents),
        "source_counts": counts,
        "real_model_execution": not bool(getattr(client, "is_fake", False)),
        "local_model_enabled": False,
    }
    records = []
    for offset in range(0, len(documents), batch_size):
        batch = documents[offset:offset + batch_size]
        result = client.embed_texts([item["text"] for item in batch])
        if not result.get("ok"):
            manifest.update({
                "status": "skipped" if result.get("error_code") in {"missing_api_key", "missing_endpoint"} else "failed",
                "error_code": result.get("error_code", "embedding_failed"),
                "real_model_execution": False,
            })
            write_json(manifest_path, manifest)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(render_report(manifest), encoding="utf-8")
            return manifest
        manifest["dimension"] = result["dimension"]
        for document, vector in zip(batch, result["vectors"]):
            records.append({
                "doc_id": document["doc_id"],
                "kind": document["kind"],
                "source_ref": document["source_ref"],
                "source_refs": document["source_refs"],
                "source_type": document["source_type"],
                "review_status": document["review_status"],
                "lifecycle_status": document["lifecycle_status"],
                "trusted": document["trusted"],
                "text": document["text"],
                "text_hash": hashlib.sha256(document["text"].encode("utf-8")).hexdigest(),
                "metadata": document["metadata"],
                "vector": normalize_vector(vector),
                "generated_by": "scripts/build_bge_m3_index.py",
            })
    write_jsonl(index_path, records)
    write_json(manifest_path, manifest)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(manifest), encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="使用远程 BGE-M3 构建文件化向量索引。")
    parser.add_argument("--provider", choices=["siliconflow_bge_m3", "aliyun_eas_bge_m3"], default="siliconflow_bge_m3")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    documents = load_documents()
    if args.limit > 0:
        documents = documents[:args.limit]
    manifest = build_index(
        documents=documents,
        client=BgeM3RemoteClient.from_env(args.provider),
        batch_size=args.batch_size,
    )
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
