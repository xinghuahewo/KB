import json
from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "bgpkb" / "pipeline" / "build_bge_m3_index.py"


class FakeEmbeddingClient:
    provider = "fake_bge_m3"
    model = "BAAI/bge-m3"
    is_fake = True

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
        }


class MissingKeyClient:
    provider = "siliconflow_bge_m3"
    model = "BAAI/bge-m3"
    is_fake = False

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


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_fake_client_builds_index_manifest_and_chinese_report(tmp_path):
    namespace = runpy.run_path(str(SCRIPT))
    documents = namespace["build_embedding_documents"](**sample_inputs())
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
    assert {item["kind"] for item in records} == {"chunk", "entity", "glossary", "evidence_template"}
    assert all(abs(sum(value * value for value in item["vector"]) - 1.0) < 1e-6 for item in records)
    assert manifest["provider"] == "fake_bge_m3"
    assert manifest["model"] == "BAAI/bge-m3"
    assert manifest["dimension"] == 3
    assert manifest["input_count"] == 4
    assert len(manifest["input_hash"]) == 64
    assert manifest["source_counts"] == {
        "chunk": 1,
        "entity": 1,
        "evidence_template": 1,
        "glossary": 1,
    }
    assert manifest["real_model_execution"] is False
    assert "# BGE-M3 Embedding 构建报告" in report
    assert "当前设备未运行本地模型" in report


def test_missing_key_writes_skipped_manifest_without_vector_index(tmp_path):
    namespace = runpy.run_path(str(SCRIPT))
    documents = namespace["build_embedding_documents"](**sample_inputs())
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
    assert result["status"] == "skipped"
    assert manifest["status"] == "skipped"
    assert manifest["error_code"] == "missing_api_key"
    assert index_path.exists() is False
    assert "未配置远程 API key" in report_path.read_text(encoding="utf-8")


def test_processed_source_chunk_is_marked_retrieval_eligible_without_approval():
    namespace = runpy.run_path(str(SCRIPT))
    inputs = sample_inputs()

    documents = namespace["build_embedding_documents"](
        **inputs,
        trusted_doc_ids={"rfc7908"},
    )
    chunk = next(item for item in documents if item["kind"] == "chunk")

    assert chunk["trusted"] is True
    assert chunk["trust_basis"] == "processed_source_with_traceability"
    assert chunk["review_status"] == "pending"
