import copy
import hashlib
import json


def _chunk(chunk_id: str, content: str = "A sufficiently complete semantic chunk for quality gate validation.") -> dict:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return {
        "schema_version": "semantic_chunk_v3",
        "chunk_id": "semantic_chunk_v3_" + chunk_id * 64,
        "doc_id": "quality-fixture",
        "source_id": "quality-fixture",
        "source_snapshot_id": "snapshot_" + "1" * 64,
        "source_object_digest": "sha256:" + "2" * 64,
        "document_profile": "rfc",
        "chunker": {
            "name": "rfc_semantic",
            "version": "3.0.0",
            "config_version": "quality-fixture-v1",
            "config_fingerprint": "sha256:" + "3" * 64,
        },
        "title": "Quality fixture",
        "section_path": ["Quality"],
        "semantic_unit": "paragraph",
        "content": content,
        "content_hash": "sha256:" + digest,
        "exact_content_hash": "sha256:" + digest,
        "source_block_ids": ["block_v2_" + chunk_id * 64],
        "source_block_hashes": ["sha256:" + chunk_id * 64],
        "source_refs": [f"fixtures/quality#{chunk_id}"],
        "page_numbers": [],
        "language": "en",
        "estimated_tokens": max(1, len(content) // 4),
        "short_content_rule_id": None,
    }


def test_v3_quality_profile_blocks_empty_short_and_excess_same_source_exact_duplicates():
    from bgpkb.ingestion.semantic_chunk_quality import profile_semantic_chunks

    valid = _chunk("a")
    empty = _chunk("b", "")
    short = _chunk("c", "()")
    duplicate = copy.deepcopy(valid)
    duplicate["chunk_id"] = "semantic_chunk_v3_" + "d" * 64
    duplicate["source_block_ids"] = ["block_v2_" + "d" * 64]
    duplicate["source_block_hashes"] = ["sha256:" + "d" * 64]

    report = profile_semantic_chunks([valid, empty, short, duplicate], excluded_blocks=[])

    assert report["status"] == "failed"
    assert report["metrics"]["empty_content_count"] == 1
    assert report["metrics"]["short_unallowlisted_count"] == 2
    assert report["metrics"]["same_source_exact_duplicate_count"] == 1
    assert report["metrics"]["same_source_exact_duplicate_rate"] == 0.25
    assert {issue["code"] for issue in report["blocking_issues"]} >= {
        "empty_semantic_chunk",
        "short_unallowlisted_semantic_chunk",
        "same_source_exact_duplicate_rate_exceeded",
    }
    assert report["samples"]["empty_content"] == [empty["chunk_id"]]
    assert short["chunk_id"] in report["samples"]["short_unallowlisted"]


def test_v3_quality_cli_preserves_failure_report_and_returns_nonzero(tmp_path):
    from bgpkb.ingestion.semantic_chunk_quality import main

    chunks_path = tmp_path / "semantic_chunks_v3.jsonl"
    output = tmp_path / "reports" / "semantic_chunk_quality_v3.json"
    chunks_path.write_text(json.dumps(_chunk("e", "!")) + "\n", encoding="utf-8")

    status = main(["--chunks", str(chunks_path), "--output", str(output)])

    assert status == 1
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "failed"
    assert report["metrics"]["short_unallowlisted_count"] == 1
    assert not list(output.parent.glob("*.tmp"))


def test_v3_quality_profile_accepts_schema_valid_nonduplicate_chunks_and_allowlisted_terms():
    from bgpkb.ingestion.semantic_chunk_quality import profile_semantic_chunks

    valid = _chunk("f")
    term = _chunk("9", "BGP")
    term["semantic_unit"] = "term"
    term["short_content_rule_id"] = "protocol-term-bgp-v1"
    term["exact_content_hash"] = "sha256:" + "9" * 64

    report = profile_semantic_chunks([valid, term], excluded_blocks=[{
        "block_id": "block_v2_" + "8" * 64,
        "reason": "short_unmeaningful_content",
    }])

    assert report["status"] == "passed"
    assert report["blocking_issues"] == []
    assert report["metrics"]["short_allowlisted_count"] == 1
    assert report["metrics"]["excluded_count"] == 1


def test_v3_quality_profile_reports_atomic_over_target_tail_as_nonblocking_warning():
    from bgpkb.ingestion.semantic_chunk_quality import profile_semantic_chunks

    code = _chunk("7", "A complete atomic code example that must remain intact for semantic fidelity.")
    code["semantic_unit"] = "code"
    code["estimated_tokens"] = 801

    report = profile_semantic_chunks([code], excluded_blocks=[])

    assert report["status"] == "passed"
    assert report["metrics"]["over_target_max_tokens_count"] == 1
    assert report["warnings"] == [{
        "code": "semantic_chunk_over_target_max_tokens",
        "actual": 1,
    }]
    assert report["samples"]["over_target_max_tokens"] == [code["chunk_id"]]
