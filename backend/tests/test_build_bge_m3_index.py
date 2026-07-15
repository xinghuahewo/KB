import json
from pathlib import Path
import runpy

import pytest

from bgpkb.indexing.retrieval_documents import (
    build_retrieval_input_manifest,
    derive_retrieval_document,
)

from test_retrieval_document_v1_gold import _eligibility, _governance, _semantic_chunk


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "bgpkb" / "pipeline" / "build_bge_m3_index.py"


class FakeEmbeddingClient:
    provider = "fake_bge_m3"
    model = "BAAI/bge-m3"
    is_fake = True
    model_revision = "rev-test"
    provider_contract = "fake_embedding_v1"

    def embed_texts(self, texts):
        vectors = []
        for index, _text in enumerate(texts, start=1):
            vectors.append([float(index), float(index + 1), 0.0])
        return {
            "ok": True,
            "provider": self.provider,
            "model": self.model,
            "vectors": vectors,
            "dimension": 3,
            "input_count": len(texts),
            "revision": "rev-test",
            "model_hash": "sha256:model-test",
            "degraded": True,
            "degraded_reason": "本地服务超时，已使用 API",
            "attempts": [
                {"provider": "local_http", "ok": False},
                {"provider": self.provider, "ok": True},
            ],
        }


class MissingKeyClient:
    provider = "siliconflow_bge_m3"
    model = "BAAI/bge-m3"
    is_fake = False
    model_revision = "rev-test"
    provider_contract = "fake_embedding_v1"

    def embed_texts(self, texts):
        return {
            "ok": False,
            "provider": self.provider,
            "model": self.model,
            "error_code": "missing_api_key",
            "error": "BGE-M3 API key is not configured.",
        }


def sample_inputs():
    return {
        "chunks": [{
            "chunk_id": "chunk_route_leak",
            "doc_id": "rfc7908",
            "title": "Route Leak",
            "content_preview": "A route leak propagates routes beyond their intended scope.",
            "topics": ["Route Leak", "BGP"],
            "source_ref": "raw/standards/rfc7908.txt",
            "source_type": "standard",
            "review_status": "pending",
        }],
        "entities": [{
            "entity_id": "anomaly_route_leak",
            "entity_type": "AnomalyType",
            "name": "Route Leak",
            "aliases": ["路由泄露"],
            "category": "Policy Violation",
            "review_status": "approved",
            "source_refs": ["rfc7908"],
            "entity_payload": {"definition": "A BGP route leak."},
        }],
        "glossary": [{
            "term_id": "glossary_route_leak",
            "term": "Route Leak",
            "aliases": ["路由泄露"],
            "definition": "A routing announcement beyond intended scope.",
            "entity_type": "AnomalyType",
            "review_status": "approved",
            "source_refs": ["rfc7908"],
        }],
        "evidence_templates": [{
            "id": "evidence_route_leak",
            "entity_type": "EvidenceTemplate",
            "applies_to": "anomaly_route_leak",
            "required_evidence": ["as_path", "suspected_leaker_as"],
            "optional_evidence": ["operator_statement"],
            "false_positive_checks": ["legitimate_policy_change"],
            "review_status": "approved",
            "source_refs": ["rfc7908"],
        }],
    }


def sample_retrieval_documents(count=1):
    documents = []
    for index in range(count):
        digit = format(index + 1, "x")
        chunk = _semantic_chunk(content=f"完整检索正文 {index} " + "route leak evidence " * 20)
        chunk["chunk_id"] = "semantic_chunk_v3_" + digit * 64
        chunk["content_hash"] = "sha256:" + digit * 64
        documents.append(
            derive_retrieval_document(
                chunk, eligibility=_eligibility(), governance=_governance(chunk)
            )
        )
    return documents


def current_embedding_documents(namespace, count=1):
    retrieval_documents = sample_retrieval_documents(count)
    return namespace["build_embedding_documents"](
        retrieval_documents=retrieval_documents,
        input_manifest=build_retrieval_input_manifest(retrieval_documents),
    )


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_fake_client_builds_index_manifest_and_chinese_report(tmp_path):
    namespace = runpy.run_path(str(SCRIPT))
    documents = current_embedding_documents(namespace)
    index_path = tmp_path / "bge_m3_vector_index.jsonl"
    manifest_path = tmp_path / "bge_m3_embedding_manifest.json"
    report_path = tmp_path / "bge_m3_embedding_report.md"

    result = namespace["build_index"](
        documents=documents,
        client=FakeEmbeddingClient(),
        index_path=index_path,
        manifest_path=manifest_path,
        report_path=report_path,
        batch_size=2,
    )

    records = load_jsonl(index_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")

    assert result["status"] == "complete"
    assert {item["kind"] for item in records} == {"chunk"}
    assert all(abs(sum(value * value for value in item["vector"]) - 1.0) < 1e-6 for item in records)
    assert manifest["provider"] == "fake_bge_m3"
    assert manifest["model"] == "BAAI/bge-m3"
    assert manifest["dimension"] == 3
    assert manifest["input_count"] == 1
    assert len(manifest["input_hash"]) == 64
    assert manifest["source_counts"] == {"chunk": 1}
    assert manifest["real_model_execution"] is False
    assert manifest["model_revision"] == "rev-test"
    assert manifest["model_hash"] == "sha256:model-test"
    assert manifest["provider_chain"] == ["local_http", "fake_bge_m3"]
    assert manifest["degraded_reason"] == "本地服务超时，已使用 API"
    assert "# BGE-M3 Embedding 构建报告" in report
    assert "当前设备未运行本地模型" in report


def test_missing_key_writes_failed_manifest_without_vector_index(tmp_path):
    namespace = runpy.run_path(str(SCRIPT))
    documents = current_embedding_documents(namespace)
    index_path = tmp_path / "bge_m3_vector_index.jsonl"
    manifest_path = tmp_path / "bge_m3_embedding_manifest.json"
    report_path = tmp_path / "bge_m3_embedding_report.md"

    result = namespace["build_index"](
        documents=documents,
        client=MissingKeyClient(),
        index_path=index_path,
        manifest_path=manifest_path,
        report_path=report_path,
        batch_size=2,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert result["status"] == "failed"
    assert manifest["status"] == "failed"
    assert manifest["error_code"] == "missing_api_key"
    assert index_path.exists() is False
    assert "未配置远程 API key" in report_path.read_text(encoding="utf-8")


def test_failed_rebuild_atomically_preserves_complete_artifacts(tmp_path):
    namespace = runpy.run_path(str(SCRIPT))
    documents = current_embedding_documents(namespace, count=3)
    index_path = tmp_path / "bge_m3_vector_index.jsonl"
    manifest_path = tmp_path / "bge_m3_embedding_manifest.json"
    report_path = tmp_path / "bge_m3_embedding_report.md"
    old = {
        index_path: b'{"old":"index"}\n',
        manifest_path: b'{"status":"complete","old":true}\n',
        report_path: "# 旧报告\n".encode(),
    }
    for path, content in old.items():
        path.write_bytes(content)

    class FailsSecondBatch(FakeEmbeddingClient):
        def __init__(self):
            self.calls = 0

        def embed_texts(self, texts):
            self.calls += 1
            if self.calls == 2:
                return {"ok": False, "error_code": "offline", "error": "模型不可用"}
            return super().embed_texts(texts)

    result = namespace["build_index"](
        documents=documents,
        client=FailsSecondBatch(),
        index_path=index_path,
        manifest_path=manifest_path,
        report_path=report_path,
        batch_size=2,
    )

    assert result["status"] == "failed"
    assert result["preserved_previous_artifacts"] is True
    assert {path: path.read_bytes() for path in old} == old


def test_eligibility_policy_is_propagated_without_legacy_approval_aliases():
    namespace = runpy.run_path(str(SCRIPT))
    chunk = current_embedding_documents(namespace)[0]

    assert chunk["trusted"] is True
    assert chunk["trust_basis"] == _eligibility()["rule_id"]
    assert chunk["review_status"] == ""


def test_embedding_builder_accepts_only_current_retrieval_documents_and_fingerprints_input(tmp_path):
    namespace = runpy.run_path(str(SCRIPT))
    semantic_chunk = _semantic_chunk(
        content="preview start " + "full retrieval body " * 30 + "tail-marker"
    )
    retrieval_document = derive_retrieval_document(
        semantic_chunk,
        eligibility=_eligibility(),
        governance=_governance(semantic_chunk),
    )
    input_manifest = build_retrieval_input_manifest([retrieval_document])
    documents = namespace["build_embedding_documents"](
        retrieval_documents=[retrieval_document],
        input_manifest=input_manifest,
    )

    assert [item["text"] for item in documents] == [retrieval_document["retrieval_text"]]
    with pytest.raises(ValueError, match="Retrieval Document"):
        namespace["build_embedding_documents"](
            retrieval_documents=[{
                "chunk_id": retrieval_document["chunk_id"],
                "content_preview": retrieval_document["content_preview"],
            }],
            input_manifest=input_manifest,
        )

    index_path = tmp_path / "bge_m3_vector_index.jsonl"
    manifest_path = tmp_path / "bge_m3_embedding_manifest.json"
    report_path = tmp_path / "bge_m3_embedding_report.md"
    result = namespace["build_index"](
        documents=documents,
        client=FakeEmbeddingClient(),
        index_path=index_path,
        manifest_path=manifest_path,
        report_path=report_path,
    )

    assert result["retrieval_text_version"] == "retrieval_text_v1"
    assert result["retrieval_input_manifest_hash"] == input_manifest["input_manifest_hash"]
    assert result["normalization_fingerprint"]
    assert result["provider_contract_fingerprint"]
    assert load_jsonl(index_path)[0]["retrieval_text_hash"] == retrieval_document["retrieval_text_hash"]


def test_embedding_checkpoint_resumes_completed_batches_and_revision_invalidates_cache(tmp_path):
    namespace = runpy.run_path(str(SCRIPT))
    documents = current_embedding_documents(namespace, count=3)
    index_path = tmp_path / "bge_m3_vector_index.jsonl"
    manifest_path = tmp_path / "bge_m3_embedding_manifest.json"
    report_path = tmp_path / "bge_m3_embedding_report.md"
    checkpoint_path = tmp_path / "embedding.checkpoint.json"

    class InterruptsAfterFirstBatch(FakeEmbeddingClient):
        def __init__(self):
            self.calls = 0

        def embed_texts(self, texts):
            self.calls += 1
            if self.calls == 2:
                return {"ok": False, "error_code": "offline", "error": "模型中断"}
            return super().embed_texts(texts)

    interrupted = InterruptsAfterFirstBatch()
    failed = namespace["build_index"](
        documents=documents,
        client=interrupted,
        index_path=index_path,
        manifest_path=manifest_path,
        report_path=report_path,
        checkpoint_path=checkpoint_path,
        batch_size=2,
    )
    assert failed["status"] == "failed"
    assert interrupted.calls == 2
    assert json.loads(checkpoint_path.read_text(encoding="utf-8"))["completed_count"] == 2

    class CountingClient(FakeEmbeddingClient):
        def __init__(self, revision="rev-test"):
            self.calls = []
            self.model_revision = revision

        def embed_texts(self, texts):
            self.calls.append(list(texts))
            result = super().embed_texts(texts)
            result["revision"] = self.model_revision
            return result

    resumed = CountingClient()
    complete = namespace["build_index"](
        documents=documents,
        client=resumed,
        index_path=index_path,
        manifest_path=manifest_path,
        report_path=report_path,
        checkpoint_path=checkpoint_path,
        batch_size=2,
    )
    assert complete["status"] == "complete"
    assert sum(map(len, resumed.calls)) == 1
    assert complete["cache_hit_count"] == 2

    same_revision = CountingClient()
    namespace["build_index"](
        documents=documents,
        client=same_revision,
        index_path=index_path,
        manifest_path=manifest_path,
        report_path=report_path,
        checkpoint_path=checkpoint_path,
        batch_size=2,
    )
    assert same_revision.calls == []

    changed_revision = CountingClient("rev-next")
    changed = namespace["build_index"](
        documents=documents,
        client=changed_revision,
        index_path=index_path,
        manifest_path=manifest_path,
        report_path=report_path,
        checkpoint_path=checkpoint_path,
        batch_size=2,
    )
    assert sum(map(len, changed_revision.calls)) == 3
    assert changed["cache_hit_count"] == 0
