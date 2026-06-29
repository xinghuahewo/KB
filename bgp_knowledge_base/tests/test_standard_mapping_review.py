import csv
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path


AUDIT_MODULE = "bgpkb.pipeline.build_standard_mapping_decision_audit"
APPLY_MODULE = "bgpkb.pipeline.apply_standard_mapping_decisions"


def load_modules():
    assert importlib.util.find_spec(AUDIT_MODULE) is not None, "标准映射审核模块尚未实现"
    assert importlib.util.find_spec(APPLY_MODULE) is not None, "标准映射应用模块尚未实现"
    return importlib.import_module(AUDIT_MODULE), importlib.import_module(APPLY_MODULE)


def candidate(candidate_id="candidate-1", mapping="bgpkb:secures", fingerprint="a" * 64):
    return {
        "candidate_id": candidate_id,
        "candidate_type": "relation",
        "local_value": "secures",
        "suggested_mapping": mapping,
        "source_refs": ["rfc8205"],
        "input_fingerprint": fingerprint,
        "confidence": 0.9,
        "reason": "候选理由",
        "provider": "mock",
        "model": "deterministic-mock-v1",
        "prompt_version": "standard_mapping_v1",
        "status": "pending_review",
    }


def decision(candidate_id="candidate-1", value="approved", fingerprint="a" * 64, **overrides):
    row = {
        "candidate_id": candidate_id,
        "input_fingerprint": fingerprint,
        "decision": value,
        "reviewer": "reviewer@example.com",
        "reviewed_at": "2026-06-29T12:00:00+08:00",
        "decision_note": "已核对来源。",
        "row_number": 2,
    }
    row.update(overrides)
    return row


def test_audit_decision_status_matrix():
    audit, _ = load_modules()
    candidates = [candidate(f"candidate-{index}") for index in range(1, 5)]
    decisions = [
        decision("candidate-1", "approved"),
        decision("candidate-2", "rejected"),
        decision("candidate-3", "needs_evidence"),
        decision("candidate-4", "unreviewed"),
    ]

    result = audit.audit_mapping_decisions(candidates, decisions)
    by_id = {row["candidate_id"]: row for row in result["records"]}

    assert by_id["candidate-1"]["audit_status"] == "ready_to_apply"
    assert by_id["candidate-1"]["write_eligible"] is True
    assert by_id["candidate-2"]["audit_status"] == "rejected"
    assert by_id["candidate-3"]["audit_status"] == "needs_evidence"
    assert by_id["candidate-4"]["audit_status"] == "no_op"
    assert result["has_blockers"] is False


def test_approved_requires_reviewer_timezone_and_current_fingerprint():
    audit, _ = load_modules()
    invalid_rows = [
        decision(reviewer=""),
        decision(reviewed_at="2026-06-29T12:00:00"),
        decision(reviewed_at="2026-06-29T12:00:00+0800"),
        decision(reviewed_at="2026-06-29T12:00:00+08"),
        decision(reviewed_at="2026-06-31T12:00:00+08:00"),
        decision(fingerprint="b" * 64),
    ]

    for row in invalid_rows:
        result = audit.audit_mapping_decisions([candidate()], [row])
        record = result["records"][0]
        assert record["audit_status"] == "blocked_invalid_input"
        assert record["write_eligible"] is False
        assert result["has_blockers"] is True


def test_unknown_and_duplicate_decisions_are_blocked():
    audit, _ = load_modules()

    unknown = audit.audit_mapping_decisions([candidate()], [decision("missing")])
    assert unknown["records"][0]["audit_status"] == "blocked_invalid_candidate"

    duplicate = audit.audit_mapping_decisions(
        [candidate()], [decision(row_number=2), decision(row_number=3)]
    )
    assert len(duplicate["records"]) == 2
    assert {row["audit_status"] for row in duplicate["records"]} == {"blocked_invalid_input"}


def test_conflicting_approved_mappings_are_blocked_as_a_group():
    audit, _ = load_modules()
    candidates = [
        candidate("candidate-a", "bgpkb:secures"),
        candidate("candidate-b", "dcterms:relation"),
    ]
    decisions = [decision("candidate-a"), decision("candidate-b")]

    result = audit.audit_mapping_decisions(candidates, decisions)

    assert {row["audit_status"] for row in result["records"]} == {"blocked_conflict"}
    assert all(row["write_eligible"] is False for row in result["records"])


def project_config():
    return {
        "outputs": {
            "candidates": "data/derived/datasets/standard_mapping_candidates.jsonl",
            "decision_audit": "data/derived/datasets/standard_mapping_decision_audit.jsonl",
            "apply_preview": "data/derived/datasets/standard_mapping_apply_preview.jsonl",
            "approved_mappings": "data/derived/datasets/approved_standard_mappings.jsonl",
            "decisions": "data/review_inputs/standard_mapping_decisions.csv",
            "decision_audit_report": "data/generated/reports/review/standard_mapping_decision_audit_report.md",
            "decision_apply_report": "data/generated/reports/review/standard_mapping_decision_apply_report.md",
        },
        "review_policy": {
            "allowed_decisions": ["unreviewed", "approved", "rejected", "needs_evidence"],
            "write_requires_explicit_flag": True,
        },
    }


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_decisions(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["candidate_id", "input_fingerprint", "decision", "reviewer", "reviewed_at", "decision_note"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in writer.fieldnames})


def prepare_project(root, candidates, decisions, audits):
    config = project_config()
    outputs = config["outputs"]
    write_jsonl(root / outputs["candidates"], candidates)
    write_jsonl(root / outputs["decision_audit"], audits)
    write_decisions(root / outputs["decisions"], decisions)
    return config


def test_dry_run_writes_preview_without_touching_approved_file(tmp_path):
    _, apply = load_modules()
    valid_candidate = candidate()
    audit_record = {
        "candidate_id": "candidate-1",
        "submitted_input_fingerprint": "a" * 64,
        "current_input_fingerprint": "a" * 64,
        "decision": "approved",
        "reviewer": "reviewer@example.com",
        "reviewed_at": "2026-06-29T12:00:00+08:00",
        "decision_note": "已核对来源。",
        "audit_status": "ready_to_apply",
        "write_eligible": True,
        "reason": "审核通过。",
    }
    config = prepare_project(tmp_path, [valid_candidate], [decision()], [audit_record])
    approved_path = tmp_path / config["outputs"]["approved_mappings"]
    approved_path.parent.mkdir(parents=True, exist_ok=True)
    approved_path.write_text("canary\n", encoding="utf-8")

    result = apply.apply_standard_mapping_decisions(tmp_path, config, write=False)

    assert result["ready_count"] == 1
    assert approved_path.read_text(encoding="utf-8") == "canary\n"
    assert (tmp_path / config["outputs"]["apply_preview"]).exists()


def test_explicit_write_only_publishes_current_ready_mappings(tmp_path):
    _, apply = load_modules()
    good = candidate("candidate-good")
    blocked = candidate("candidate-blocked", fingerprint="b" * 64)
    audits = [
        {
            "candidate_id": "candidate-good",
            "submitted_input_fingerprint": "a" * 64,
            "current_input_fingerprint": "a" * 64,
            "decision": "approved",
            "reviewer": "reviewer@example.com",
            "reviewed_at": "2026-06-29T12:00:00Z",
            "decision_note": "通过",
            "audit_status": "ready_to_apply",
            "write_eligible": True,
            "reason": "审核通过。",
        },
        {
            "candidate_id": "candidate-blocked",
            "submitted_input_fingerprint": "a" * 64,
            "current_input_fingerprint": "b" * 64,
            "decision": "approved",
            "audit_status": "blocked_invalid_input",
            "write_eligible": False,
            "reason": "指纹不匹配。",
        },
    ]
    config = prepare_project(tmp_path, [good, blocked], [], audits)

    result = apply.apply_standard_mapping_decisions(tmp_path, config, write=True)
    rows = [
        json.loads(line)
        for line in (tmp_path / config["outputs"]["approved_mappings"]).read_text(encoding="utf-8").splitlines()
        if line
    ]

    assert result["written"] is True
    assert [row["candidate_id"] for row in rows] == ["candidate-good"]
    assert rows[0]["input_fingerprint"] == "a" * 64


def test_review_workflow_does_not_modify_primary_entities_or_relationships(tmp_path):
    audit, _ = load_modules()
    entity_path = tmp_path / "data/knowledge/entities/concepts.jsonl"
    relationship_path = tmp_path / "data/knowledge/relationships/relationships.jsonl"
    write_jsonl(entity_path, [{"id": "concept_rpki"}])
    write_jsonl(relationship_path, [{"relation": "secures"}])
    before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (entity_path, relationship_path)
    }

    audit.audit_mapping_decisions([candidate()], [decision()])

    after = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (entity_path, relationship_path)
    }
    assert after == before


def test_atomic_write_failure_preserves_existing_file_and_cleans_temporary_file(tmp_path, monkeypatch):
    _, apply = load_modules()
    target = tmp_path / "approved.jsonl"
    target.write_text("canary\n", encoding="utf-8")

    def fail_replace(source, destination):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", fail_replace)
    try:
        apply.atomic_write_jsonl(target, [{"candidate_id": "new"}])
    except OSError as exc:
        assert "simulated" in str(exc)
    else:
        raise AssertionError("atomic_write_jsonl 应传播替换失败")

    assert target.read_text(encoding="utf-8") == "canary\n"
    assert list(tmp_path.glob(".approved.jsonl.*")) == []
