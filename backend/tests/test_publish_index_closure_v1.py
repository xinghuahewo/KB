from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _retrieval_document() -> dict:
    text = "RFC 7908 > Route Leak\n完整检索正文用于 publish-index 闭包测试。"
    chunk_id = "semantic_chunk_v3_" + "a" * 64
    return {
        "schema_version": "retrieval_document_v1",
        "retrieval_doc_id": "retrieval_doc_v1_" + "b" * 64,
        "chunk_id": chunk_id,
        "doc_id": "rfc7908",
        "source_id": "rfc7908",
        "title": "RFC 7908 Route Leak",
        "document_profile": "rfc",
        "section_path": ["2. Route Leak Definition"],
        "semantic_unit": "paragraph",
        "source_ref": "raw/standards/rfc7908.txt#section-2",
        "source_refs": ["raw/standards/rfc7908.txt#section-2"],
        "retrieval_text": text,
        "retrieval_text_hash": "sha256:" + hashlib.sha256(text.encode()).hexdigest(),
        "retrieval_text_version": "retrieval_text_v1",
        "content_preview": text,
        "governance": {
            "parse_status": "parsed",
            "content_quality_status": "approved",
            "source_trust_status": "trusted",
            "semantic_review_status": "approved",
        },
        "eligibility": {
            "status": "eligible",
            "policy_version": "retrieval_eligibility_v1",
            "rule_id": "retrieval.eligible_reviewed_source",
            "reason": "test",
            "audit": {},
        },
    }


def _build_candidate(tmp_path: Path, *, release_id: str = "release-a") -> Path:
    from bgpkb.indexing.retrieval_documents import build_retrieval_input_manifest
    from bgpkb.infrastructure import serving_bundle

    data_dir = tmp_path / release_id / "data"
    published = data_dir / "published"
    datasets = data_dir / "derived" / "datasets"
    published.mkdir(parents=True)
    document = _retrieval_document()
    retrieval_manifest = build_retrieval_input_manifest([document])
    input_hash = retrieval_manifest["input_manifest_hash"]

    _write_jsonl(published / "source_catalog.jsonl", [{"source_id": "rfc7908"}])
    _write_jsonl(
        published / "chunk_catalog.jsonl",
        [{"chunk_id": document["chunk_id"], "source_id": "rfc7908"}],
    )
    _write_jsonl(
        published / "section_catalog.jsonl",
        [{"section_id": "section-1", "child_chunk_ids": [document["chunk_id"]]}],
    )
    _write_jsonl(published / "retrieval_documents_v1.jsonl", [document])
    serving_bundle.build_serving_database(
        published / "serving.sqlite",
        release_id=release_id,
        retrieval_documents=[document],
    )
    serving_bundle.build_governance_database(
        published / "governance.sqlite",
        release_id=release_id,
        datasets={"human_review_workbook": []},
    )
    _write_jsonl(
        published / "bge_m3_vector_index.jsonl",
        [{
            "kind": "chunk",
            "doc_id": document["retrieval_doc_id"],
            "metadata": {"chunk_id": document["chunk_id"]},
            "retrieval_input_manifest_hash": input_hash,
            "vector": [1.0, 0.0],
        }],
    )
    (published / "bge_m3_embedding_manifest.json").write_text(
        json.dumps({
            "status": "complete",
            "record_count": 1,
            "input_count": 1,
            "dimension": 2,
            "model": "BAAI/bge-m3",
            "model_revision": "revision-20260715",
            "retrieval_input_manifest_hash": input_hash,
            "retrieval_text_version": "retrieval_text_v1",
        }) + "\n",
        encoding="utf-8",
    )
    (published / "bge_m3_vector_matrix.npy").write_bytes(b"synthetic matrix")
    _write_jsonl(
        published / "bge_m3_vector_metadata.jsonl",
        [{"chunk_id": document["chunk_id"], "retrieval_doc_id": document["retrieval_doc_id"]}],
    )
    vector_hash = _sha256(published / "bge_m3_vector_index.jsonl")
    (published / "bge_m3_vector_fast_manifest.json").write_text(
        json.dumps({
            "status": "complete",
            "record_count": 1,
            "dimension": 2,
            "source_index_sha256": vector_hash,
            "retrieval_input_manifest_hash": input_hash,
        }) + "\n",
        encoding="utf-8",
    )

    artifact_paths = [
        path
        for path in sorted(data_dir.rglob("*"))
        if path.is_file() and path.name != "artifact_manifest.jsonl"
    ]
    _write_jsonl(
        datasets / "artifact_manifest.jsonl",
        [
            {
                "artifact_path": "data/" + path.relative_to(data_dir).as_posix(),
                "sha256": _sha256(path).removeprefix("sha256:"),
            }
            for path in artifact_paths
        ],
    )
    return data_dir


def test_publish_index_manifest_binds_complete_release_model_and_retrieval_closure(tmp_path):
    from bgpkb.publishing import publish_index_closure

    data_dir = _build_candidate(tmp_path)
    manifest_path = publish_index_closure.write_publish_index_manifest(
        data_dir,
        release_id="release-a",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert set(manifest["artifacts"]) == publish_index_closure.REQUIRED_PUBLISH_ARTIFACT_ROLES
    assert "section_catalog" in manifest["artifacts"]
    assert manifest["release_id"] == "release-a"
    assert manifest["model_revisions"] == {"embedding": "revision-20260715"}
    assert manifest["retrieval_input_manifest"]["document_count"] == 1
    assert manifest["retrieval_input_manifest"]["input_manifest_hash"].startswith("sha256:")
    assert manifest["identity_closure"] == {
        "retrieval_document_count": 1,
        "chunk_id_count": 1,
        "fts_document_count": 1,
        "vector_record_count": 1,
        "fast_record_count": 1,
    }
    for entry in manifest["artifacts"].values():
        assert entry["release_id"] == "release-a"
        assert entry["path"]
        assert entry["sha256"].startswith("sha256:")
        assert isinstance(entry["record_count"], int)
        assert "model_revision" in entry
        assert "retrieval_input_manifest_hash" in entry

    verification = publish_index_closure.verify_publish_index_manifest(data_dir)
    assert verification["status"] == "complete"
    assert verification["artifact_count"] == len(
        publish_index_closure.REQUIRED_PUBLISH_ARTIFACT_ROLES
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing_fast_metadata", "缺少 publish-index 制品"),
        ("fast_hash_mismatch", "source_index_sha256"),
        ("fast_id_mismatch", "chunk ID 闭包"),
        ("missing_model_revision", "model_revision"),
        ("retrieval_input_mismatch", "retrieval input manifest"),
    ],
)
def test_publish_index_closure_fails_closed_and_preserves_previous_manifest(
    tmp_path,
    mutation,
    message,
):
    from bgpkb.publishing import publish_index_closure

    data_dir = _build_candidate(tmp_path)
    manifest_path = publish_index_closure.write_publish_index_manifest(
        data_dir,
        release_id="release-a",
    )
    previous = manifest_path.read_bytes()
    published = data_dir / "published"

    if mutation == "missing_fast_metadata":
        (published / "bge_m3_vector_metadata.jsonl").unlink()
    elif mutation == "fast_hash_mismatch":
        payload = json.loads((published / "bge_m3_vector_fast_manifest.json").read_text())
        payload["source_index_sha256"] = "sha256:" + "0" * 64
        (published / "bge_m3_vector_fast_manifest.json").write_text(json.dumps(payload) + "\n")
    elif mutation == "fast_id_mismatch":
        _write_jsonl(published / "bge_m3_vector_metadata.jsonl", [{"chunk_id": "wrong"}])
    elif mutation == "missing_model_revision":
        payload = json.loads((published / "bge_m3_embedding_manifest.json").read_text())
        payload["model_revision"] = ""
        (published / "bge_m3_embedding_manifest.json").write_text(json.dumps(payload) + "\n")
    else:
        payload = json.loads((published / "bge_m3_embedding_manifest.json").read_text())
        payload["retrieval_input_manifest_hash"] = "sha256:" + "f" * 64
        (published / "bge_m3_embedding_manifest.json").write_text(json.dumps(payload) + "\n")

    with pytest.raises(publish_index_closure.PublishIndexClosureError, match=message):
        publish_index_closure.write_publish_index_manifest(
            data_dir,
            release_id="release-a",
        )

    assert manifest_path.read_bytes() == previous
    assert list(manifest_path.parent.glob(".publish_index_manifest_v1.json.*.tmp")) == []
