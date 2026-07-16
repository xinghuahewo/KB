import json

from bgpkb.workflows.replay_governance_migration import replay_governance_migration


def _chunk(index, *, source_id, source_ref=True, snapshot=True, review_status="approved"):
    return {
        "schema_version": "semantic_chunk_v3",
        "chunk_id": "semantic_chunk_v3_" + str(index) * 64,
        "doc_id": source_id,
        "source_id": source_id,
        "source_snapshot_id": "snapshot_" + str(index) * 64 if snapshot else "",
        "source_refs": [f"raw/{source_id}.txt#section-1"] if source_ref else [],
        "review_status": review_status,
        "parse_status": "parsed",
    }


def test_replay_is_conservative_auditable_and_writes_only_governance_reports(tmp_path):
    chunks = [
        _chunk(1, source_id="rfc4271"),
        _chunk(2, source_id="pending-source"),
        _chunk(3, source_id="missing-source", source_ref=False, snapshot=False),
    ]
    sources = [
        {
            "source_id": "rfc4271",
            "source_type": "standard",
            "trust_level": "high",
            "review_status": "approved",
        },
        {
            "source_id": "pending-source",
            "source_type": "research",
            "trust_level": "high",
            "review_status": "pending",
        },
    ]
    entity_evidence = [{
        "entity_id": "bgp",
        "entity_review_status": "approved",
        "chunk_sample_ids": [chunks[0]["chunk_id"]],
    }]

    report = replay_governance_migration(
        chunks,
        source_records=sources,
        entity_evidence_records=entity_evidence,
        output_root=tmp_path,
    )

    records = [
        json.loads(line)
        for line in (tmp_path / "evidence_governance_migration_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    by_id = {row["chunk_id"]: row for row in records}
    first = by_id[chunks[0]["chunk_id"]]["governance"]
    pending = by_id[chunks[1]["chunk_id"]]["governance"]
    missing = by_id[chunks[2]["chunk_id"]]["governance"]

    assert first["content_quality_status"] == "approved"
    assert first["source_trust_status"] == "trusted"
    assert first["semantic_review_status"] == "approved"
    assert first["retrieval_eligibility"]["status"] == "eligible"
    assert pending["source_trust_status"] == "pending"
    assert pending["semantic_review_status"] == "unknown"
    assert pending["retrieval_eligibility"]["status"] == "eligible_with_caution"
    assert missing["source_trust_status"] == "unknown"
    assert missing["semantic_review_status"] == "unknown"
    assert missing["retrieval_eligibility"]["status"] == "ineligible"
    assert missing["retrieval_eligibility"]["rule_id"] == "retrieval.missing_source_trace"

    assert report["statistics"]["record_count"] == 3
    assert report["statistics"]["retrieval_eligibility"] == {
        "eligible": 1,
        "eligible_with_caution": 1,
        "ineligible": 1,
    }
    assert {row["dimension"] for row in report["status_promotions"]} == {
        "source_trust_status",
        "semantic_review_status",
    }
    assert {row["chunk_id"] for row in report["retrieval_downgrades"]} == {
        chunks[1]["chunk_id"],
        chunks[2]["chunk_id"],
    }
    assert [row["chunk_id"] for row in report["ineligible_records"]] == [
        chunks[2]["chunk_id"]
    ]
    assert report["blockers"] == [{
        "code": "missing_source_record",
        "count": 1,
        "chunk_ids": [chunks[2]["chunk_id"]],
    }, {
        "code": "missing_source_trace",
        "count": 1,
        "chunk_ids": [chunks[2]["chunk_id"]],
    }]
    assert (tmp_path / "evidence_governance_migration_diff_v1.json").is_file()
    assert "# 证据治理状态迁移重放报告" in (
        tmp_path / "evidence_governance_migration_report_v1.md"
    ).read_text(encoding="utf-8")
    assert not any("retrieval_document" in path.name for path in tmp_path.iterdir())
    assert not any("sqlite" in path.name or "vector" in path.name for path in tmp_path.iterdir())


def test_replay_is_deterministic_and_missing_reviews_never_promote_status(tmp_path):
    chunks = [_chunk(4, source_id="unknown-source")]
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"

    first = replay_governance_migration(
        chunks,
        source_records=[],
        entity_evidence_records=[],
        output_root=first_root,
    )
    second = replay_governance_migration(
        chunks,
        source_records=[],
        entity_evidence_records=[],
        output_root=second_root,
    )

    assert first == second
    assert (first_root / "evidence_governance_migration_v1.jsonl").read_bytes() == (
        second_root / "evidence_governance_migration_v1.jsonl"
    ).read_bytes()
    record = json.loads(
        (first_root / "evidence_governance_migration_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    governance = record["governance"]
    assert governance["content_quality_status"] == "approved"
    assert governance["source_trust_status"] == "unknown"
    assert governance["semantic_review_status"] == "unknown"
    assert first["status_promotions"] == []
