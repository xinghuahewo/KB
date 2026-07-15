import hashlib
import json
import sqlite3

import pytest


def _sha256(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _retrieval_document(*, suffix="1", text=None):
    chunk_id = "semantic_chunk_v3_" + suffix * 64
    retrieval_text = text or (
        "RFC 7908 > Route Leak\n"
        "A route leak propagates routing announcements beyond their intended scope. "
        "The complete retrieval text keeps the tail marker bgp_tail_signal."
    )
    return {
        "schema_version": "retrieval_document_v1",
        "retrieval_doc_id": "retrieval_doc_v1_" + suffix * 64,
        "chunk_id": chunk_id,
        "doc_id": f"rfc7908-{suffix}",
        "source_id": "rfc7908",
        "title": "RFC 7908 Route Leak",
        "document_profile": "rfc",
        "section_path": ["2. Route Leak Definition"],
        "semantic_unit": "paragraph",
        "source_ref": "raw/standards/rfc7908.txt#section-2",
        "retrieval_text": retrieval_text,
        "retrieval_text_hash": "sha256:" + hashlib.sha256(
            retrieval_text.encode("utf-8")
        ).hexdigest(),
        "retrieval_text_version": "retrieval_text_v1",
        "content_preview": retrieval_text[:80],
        "governance": {
            "schema_version": "evidence_governance_state_v1",
            "object_id": chunk_id,
            "object_type": "semantic_chunk",
            "parse_status": "parsed",
            "content_quality_status": "approved",
            "source_trust_status": "trusted",
            "semantic_review_status": "approved",
            "retrieval_eligibility": {},
            "status_provenance": {},
            "migration_audit": [],
        },
        "eligibility": {
            "status": "eligible",
            "policy_version": "retrieval_eligibility_v1",
            "rule_id": "retrieval.eligible_reviewed_source",
            "reason": "来源和内容满足检索条件",
            "audit": {
                "actor": "system:retrieval_eligibility_policy",
                "decision_method": "deterministic_policy",
                "input_fingerprint": "sha256:" + "a" * 64,
                "policy_fingerprint": "sha256:" + "b" * 64,
            },
        },
    }


def test_serving_sqlite_is_minimal_versioned_and_indexes_full_retrieval_text(tmp_path):
    from bgpkb.infrastructure import serving_bundle

    output = tmp_path / "serving.sqlite"
    result = serving_bundle.build_serving_database(
        output,
        release_id="release-a",
        retrieval_documents=[_retrieval_document()],
    )

    with sqlite3.connect(output) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
            )
        }
        metadata = dict(conn.execute("SELECT key, value FROM meta"))
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert conn.execute(
            "SELECT chunk_id FROM chunk_fts WHERE chunk_fts MATCH 'bgp_tail_signal'"
        ).fetchone() == (_retrieval_document()["chunk_id"],)

    assert {"sources", "entities", "chunks", "retrieval_documents", "relationships", "meta"} <= tables
    assert not (serving_bundle.GOVERNANCE_ONLY_TABLES & tables)
    assert metadata["schema_version"] == serving_bundle.SERVING_SCHEMA_VERSION
    assert metadata["minimum_reader_version"] == serving_bundle.MINIMUM_READER_VERSION
    assert metadata["release_id"] == "release-a"
    assert result["retrieval_document_count"] == 1
    assert result["database_sha256"] == _sha256(output)


def test_governance_sqlite_owns_review_audit_history_and_offline_workflows(tmp_path):
    from bgpkb.infrastructure import serving_bundle

    serving_path = tmp_path / "serving.sqlite"
    governance_path = tmp_path / "governance.sqlite"
    serving_bundle.build_serving_database(
        serving_path,
        release_id="release-a",
        retrieval_documents=[_retrieval_document()],
    )
    result = serving_bundle.build_governance_database(
        governance_path,
        release_id="release-a",
        datasets={
            "human_review_workbook": [{"workbook_id": "workbook-1", "decision": "pending"}],
            "human_review_decision_audit": [{"audit_id": "audit-1", "status": "recorded"}],
            "historical_v1_evidence": [{"evidence_id": "legacy-1", "chunk_id": "chunk-v1"}],
            "offline_workflow": [{"task_id": "task-1", "status": "waiting"}],
        },
    )

    with sqlite3.connect(serving_path) as conn:
        serving_tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    with sqlite3.connect(governance_path) as conn:
        governance_tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        dataset_counts = dict(
            conn.execute(
                "SELECT dataset_name, COUNT(*) FROM governance_records GROUP BY dataset_name"
            )
        )

    assert "governance_records" not in serving_tables
    assert "governance_records" in governance_tables
    assert dataset_counts == {
        "historical_v1_evidence": 1,
        "human_review_decision_audit": 1,
        "human_review_workbook": 1,
        "offline_workflow": 1,
    }
    assert result["record_count"] == 4


def test_online_retrieval_starts_without_governance_and_opens_serving_read_only(tmp_path):
    from bgpkb.infrastructure import serving_bundle
    from bgpkb.retrieval import repository
    from bgpkb.retrieval.retrieval_data import PublishedArtifactRetrievalData
    from bgpkb.retrieval.retrievers import Bm25Retriever

    data_dir = tmp_path / "release-a" / "data"
    published_dir = data_dir / "published"
    published_dir.mkdir(parents=True)
    serving_path = published_dir / "serving.sqlite"
    serving_bundle.build_serving_database(
        serving_path,
        release_id="release-a",
        retrieval_documents=[_retrieval_document()],
    )
    assert not (published_dir / "governance.sqlite").exists()

    retrieval_data = PublishedArtifactRetrievalData(data_dir)
    result = Bm25Retriever(retrieval_data=retrieval_data).search("bgp_tail_signal", 5)
    diagnostics = serving_bundle.inspect_serving_database(serving_path)
    with serving_bundle.connect_serving_database(serving_path) as conn:
        stats = repository.stats(conn)
        assert stats["human_review_progress"] == 0
        assert stats["entity_evidence"] == 0
        assert repository.actions(conn) == []
        assert repository.progress(conn) == []
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("INSERT INTO meta VALUES ('forbidden', 'write')")

    assert retrieval_data.database_path() == serving_path
    assert [item["chunk_id"] for item in result.items] == [_retrieval_document()["chunk_id"]]
    assert diagnostics["mode"] == "current"
    assert diagnostics["degraded"] is False


def test_serving_database_insert_failure_preserves_previous_file_and_removes_temp(tmp_path):
    from bgpkb.infrastructure import serving_bundle

    output = tmp_path / "serving.sqlite"
    serving_bundle.build_serving_database(
        output,
        release_id="release-a",
        retrieval_documents=[_retrieval_document()],
    )
    previous_hash = _sha256(output)
    duplicate = _retrieval_document(suffix="2")

    with pytest.raises(serving_bundle.ServingBundleBuildError, match="构建失败"):
        serving_bundle.build_serving_database(
            output,
            release_id="release-b",
            retrieval_documents=[duplicate, duplicate],
        )

    assert _sha256(output) == previous_hash
    assert list(tmp_path.glob(".serving.sqlite.*.tmp")) == []


def test_release_manifest_rejects_cross_release_and_hash_mixed_artifacts(tmp_path):
    from bgpkb import artifact_verification
    from bgpkb.infrastructure import serving_bundle

    data_dir = tmp_path / "release-a" / "data"
    published_dir = data_dir / "published"
    published_dir.mkdir(parents=True)
    serving_path = published_dir / "serving.sqlite"
    serving_bundle.build_serving_database(
        serving_path,
        release_id="release-b",
        retrieval_documents=[_retrieval_document()],
    )
    governance_path = published_dir / "governance.sqlite"
    serving_bundle.build_governance_database(
        governance_path,
        release_id="release-a",
        datasets={"human_review_workbook": []},
    )
    chunk_id = _retrieval_document()["chunk_id"]
    retrieval_doc_id = _retrieval_document()["retrieval_doc_id"]
    files = {
        "source_snapshot_manifest": ("source_snapshot_manifest.json", {"release_id": "release-a"}),
        "canonical_manifest": ("canonical_manifest.json", {"release_id": "release-a"}),
        "semantic_chunk_manifest": (
            "semantic_chunk_manifest.json",
            {"release_id": "release-a", "chunk_ids": [chunk_id]},
        ),
        "retrieval_document_manifest": (
            "retrieval_document_manifest.json",
            {
                "release_id": "release-a",
                "chunk_ids": [chunk_id],
                "retrieval_doc_ids": [retrieval_doc_id],
            },
        ),
        "evaluation_evidence": ("evaluation_evidence.json", {"release_id": "release-a"}),
    }
    artifacts = {
        "serving_sqlite": serving_path,
        "governance_sqlite": governance_path,
    }
    for role, (filename, payload) in files.items():
        path = published_dir / filename
        path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        artifacts[role] = path
    vector_path = published_dir / "bge_m3_vector_index.jsonl"
    vector_path.write_text(
        json.dumps({"kind": "chunk", "metadata": {"chunk_id": chunk_id}, "vector": [1.0]})
        + "\n",
        encoding="utf-8",
    )
    fast_metadata_path = published_dir / "bge_m3_vector_metadata.jsonl"
    fast_metadata_path.write_text(json.dumps({"chunk_id": chunk_id}) + "\n", encoding="utf-8")
    fast_matrix_path = published_dir / "bge_m3_vector_matrix.npy"
    fast_matrix_path.write_bytes(b"matrix")
    fast_manifest_path = published_dir / "bge_m3_vector_fast_manifest.json"
    fast_manifest_path.write_text(
        json.dumps(
            {
                "release_id": "release-a",
                "source_index_sha256": _sha256(vector_path),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    artifacts.update(
        {
            "vector_jsonl": vector_path,
            "fast_matrix": fast_matrix_path,
            "fast_metadata": fast_metadata_path,
            "fast_manifest": fast_manifest_path,
        }
    )

    with pytest.raises(serving_bundle.ReleaseManifestError, match="release_id"):
        serving_bundle.write_release_manifest(
            data_dir,
            release_id="release-a",
            artifacts=artifacts,
        )

    serving_bundle.build_serving_database(
        serving_path,
        release_id="release-a",
        retrieval_documents=[_retrieval_document()],
    )
    manifest_path = serving_bundle.write_release_manifest(
        data_dir,
        release_id="release-a",
        artifacts=artifacts,
    )
    artifact_verification.verify_release_manifest_closure(data_dir, manifest_path)
    artifacts["vector_jsonl"].write_text("mixed release bytes\n", encoding="utf-8")

    with pytest.raises(artifact_verification.ArtifactVerificationError, match="hash"):
        artifact_verification.verify_release_manifest_closure(data_dir, manifest_path)


def test_reader_rejects_incompatible_minimum_version_and_legacy_requires_opt_in(tmp_path):
    from bgpkb.infrastructure import serving_bundle

    current = tmp_path / "serving.sqlite"
    serving_bundle.build_serving_database(
        current,
        release_id="release-a",
        retrieval_documents=[_retrieval_document()],
        minimum_reader_version="99.0.0",
    )
    with pytest.raises(serving_bundle.ServingBundleCompatibilityError, match="minimum_reader_version"):
        serving_bundle.inspect_serving_database(current, reader_version="1.0.0")

    legacy = tmp_path / "bgp_knowledge_base.sqlite"
    with sqlite3.connect(legacy) as conn:
        conn.execute("CREATE TABLE chunks (chunk_id TEXT PRIMARY KEY)")
    with pytest.raises(serving_bundle.ServingBundleCompatibilityError, match="legacy"):
        serving_bundle.inspect_serving_database(legacy)

    diagnostics = serving_bundle.inspect_serving_database(legacy, allow_legacy=True)
    assert diagnostics == {
        "mode": "legacy",
        "degraded": True,
        "schema_version": "legacy_v0",
        "minimum_reader_version": None,
        "reader_version": serving_bundle.CURRENT_READER_VERSION,
        "release_id": None,
        "reason": "explicit_legacy_reader",
    }
