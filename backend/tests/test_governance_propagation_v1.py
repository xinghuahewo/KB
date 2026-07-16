import json
import sqlite3

import jsonschema

from bgpkb import paths
from bgpkb.indexing.build_bge_m3_index import _index_record, build_embedding_documents
from bgpkb.indexing.retrieval_documents import (
    build_retrieval_input_manifest,
    derive_retrieval_document,
)
from bgpkb.publishing import build_published_knowledge_base as catalog_builder
from bgpkb.publishing import build_sqlite_knowledge_base as sqlite_builder
from bgpkb.retrieval import hybrid_retrieval
from bgpkb.retrieval.retrievers import Bm25Retriever, RetrievalChannelResult

from test_retrieval_document_v1_gold import _eligibility, _governance, _semantic_chunk


def _document(*, cautious=False):
    chunk = _semantic_chunk(content="governance propagation marker " + "BGP evidence " * 30)
    eligibility = _eligibility()
    if cautious:
        eligibility = {
            **eligibility,
            "status": "eligible_with_caution",
            "rule_id": "retrieval.pending_governance_caution",
            "reason": "来源审核仍待完成",
        }
    governance = _governance(chunk, eligibility)
    if cautious:
        governance["source_trust_status"] = "pending"
        governance["semantic_review_status"] = "unknown"
    return derive_retrieval_document(
        chunk,
        eligibility=eligibility,
        governance=governance,
    )


def test_retrieval_document_propagates_all_states_and_cautious_eligibility():
    document = _document(cautious=True)
    schema = json.loads(
        (paths.SCHEMAS_DIR / "retrieval_document_v1.schema.json").read_text(encoding="utf-8")
    )

    jsonschema.Draft202012Validator(schema).validate(document)
    assert document["governance"]["parse_status"] == "parsed"
    assert document["governance"]["content_quality_status"] == "approved"
    assert document["governance"]["source_trust_status"] == "pending"
    assert document["governance"]["semantic_review_status"] == "unknown"
    assert document["eligibility"]["status"] == "eligible_with_caution"
    assert document["eligibility"]["audit"]["decision_method"] == "deterministic_policy"


def test_chunk_catalog_preserves_governance_instead_of_only_trusted_boolean(tmp_path):
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir()
    governance = _governance(_semantic_chunk())
    chunk = {
        "chunk_id": "legacy-chunk",
        "doc_id": "doc-a",
        "title": "BGP",
        "source_type": "standard",
        "chunk_type": "paragraph",
        "topics": ["BGP"],
        "source_ref": "raw/rfc4271.txt",
        "language": "en",
        "review_status": "approved",
        "content": "BGP governance catalog propagation",
        "governance": governance,
    }
    (chunk_dir / "doc-a.jsonl").write_text(json.dumps(chunk) + "\n", encoding="utf-8")

    record = catalog_builder.build_chunk_catalog(
        chunk_dir,
        corpus_version="v1",
        project_root=tmp_path,
    )[0]

    assert record["governance"] == governance
    assert "trusted" not in record


def test_sqlite_and_bm25_expose_governance_dimensions_and_policy_audit(tmp_path):
    document = _document()
    manifest = build_retrieval_input_manifest([document])
    db_path = tmp_path / "governed.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(sqlite_builder.SCHEMA)
        fts_enabled = sqlite_builder.create_fts_tables(conn)
        sqlite_builder.insert_retrieval_documents(conn, [document], manifest, fts_enabled)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(retrieval_documents)")}
        assert {
            "parse_status",
            "content_quality_status",
            "source_trust_status",
            "semantic_review_status",
            "eligibility_status",
            "eligibility_policy_version",
            "eligibility_rule_id",
            "eligibility_reason",
            "eligibility_audit_json",
        } <= columns
        persisted = conn.execute(
            "SELECT parse_status, content_quality_status, source_trust_status, "
            "semantic_review_status, eligibility_policy_version, eligibility_rule_id, "
            "eligibility_audit_json FROM retrieval_documents"
        ).fetchone()
        conn.commit()

    assert persisted[:4] == ("parsed", "approved", "trusted", "approved")
    assert persisted[4:6] == (
        document["eligibility"]["policy_version"],
        document["eligibility"]["rule_id"],
    )
    assert json.loads(persisted[6]) == document["eligibility"]["audit"]
    if fts_enabled:
        result = Bm25Retriever(db_path).search("governance", 5)
        assert result.error is None
        assert result.items[0]["governance"] == document["governance"]
        assert result.items[0]["eligibility"] == document["eligibility"]


def test_embedding_and_vector_metadata_preserve_governance_object():
    document = _document()
    manifest = build_retrieval_input_manifest([document])
    embedding_document = build_embedding_documents(
        retrieval_documents=[document], input_manifest=manifest
    )[0]
    vector_record = _index_record(embedding_document, [1.0, 0.0])

    assert embedding_document["governance"] == document["governance"]
    assert vector_record["governance"] == document["governance"]
    assert vector_record["eligibility"] == document["eligibility"]
    assert vector_record["metadata"]["governance"] == document["governance"]


def test_hybrid_api_diagnostics_summarize_all_governance_dimensions():
    document = _document(cautious=True)

    class LexicalRetriever:
        def search(self, query, top_k):
            return RetrievalChannelResult(
                channel="lexical",
                items=[{
                    "chunk_id": document["chunk_id"],
                    "doc_id": document["doc_id"],
                    "source_ref": document["source_ref"],
                    "raw_rank": 1,
                    "raw_score": -1.0,
                    "governance": document["governance"],
                    "eligibility": document["eligibility"],
                }],
                metadata={},
            )

    payload = hybrid_retrieval.search(
        "BGP governance",
        vector_enabled=False,
        lexical_retriever=LexicalRetriever(),
        trusted_chunk_ids=set(),
        eligible_doc_ids=set(),
    )

    assert payload["governance_diagnostics"] == {
        "state_dimensions": [
            "parse_status",
            "content_quality_status",
            "source_trust_status",
            "semantic_review_status",
            "retrieval_eligibility",
        ],
        "retrieval_eligibility_counts": {"eligible_with_caution": 1},
        "policy_versions": ["retrieval_eligibility_v1"],
        "missing_governance_count": 0,
    }
    assert payload["results"][0]["governance"] == document["governance"]
