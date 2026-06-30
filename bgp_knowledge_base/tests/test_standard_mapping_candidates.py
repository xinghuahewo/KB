import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from bgpkb import paths
from bgpkb.pipeline.build_standard_mapping_candidates import (
    build_candidate_id,
    build_input_fingerprint,
    build_mock_candidates,
    collect_unmapped_relations,
    parse_structured_response,
    run_generation,
    validate_candidate,
)


ROOT = paths.PROJECT_ROOT


@pytest.fixture
def config():
    return {
        "outputs": {
            "candidates": "data/derived/datasets/standard_mapping_candidates.jsonl",
            "candidate_errors": "data/derived/datasets/standard_mapping_candidate_errors.jsonl",
        },
        "namespaces": {
            "bgpkb": "https://w3id.org/bgpkb/vocab#",
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "prov": "http://www.w3.org/ns/prov#",
        },
        "relation_mappings": {"supports": "bgpkb:supports"},
        "model_policy": {
            "allowed_providers": ["mock", "deepseek"],
            "allowed_target_prefixes": ["bgpkb", "skos", "prov"],
            "default_candidate_status": "pending_review",
            "minimum_confidence": 0.5,
            "prompt_version": "standard_mapping_v1",
        },
    }


def relationship(relation="secures", source_refs=None):
    return {
        "src_id": "mechanism_bgpsec",
        "src_type": "RoutingMechanism",
        "relation": relation,
        "dst_id": "concept_as_path",
        "dst_type": "BGPConcept",
        "source_refs": source_refs if source_refs is not None else ["rfc8205"],
        "confidence": 0.8,
    }


def test_collect_unmapped_relations_only_returns_real_unconfigured_values():
    relationships = [
        {"relation": "supports", "source_refs": ["rfc4271"]},
        {"relation": "secures", "source_refs": ["rfc8205"]},
    ]

    items = collect_unmapped_relations(relationships, {"supports": "bgpkb:supports"})

    assert [item["local_value"] for item in items] == ["secures"]


def test_real_mock_candidates_are_stable_sorted_and_traceable(config):
    relationships_path = ROOT / "data/knowledge/relationships/relationships.jsonl"
    relationships = [json.loads(line) for line in relationships_path.read_text(encoding="utf-8").splitlines()]
    production_config = yaml.safe_load(
        (ROOT / "metadata/config/standard_exports.yaml").read_text(encoding="utf-8")
    )

    items = collect_unmapped_relations(relationships, production_config["relation_mappings"])
    first = build_mock_candidates(items, production_config, generated_at="2026-06-29T00:00:00Z")
    second = build_mock_candidates(list(reversed(items)), production_config, generated_at="2026-06-30T00:00:00Z")

    assert [item["local_value"] for item in items] == [
        "affects_interpretation_of",
        "limits_interpretation_of",
        "secures",
    ]
    assert [row["local_value"] for row in first] == sorted(row["local_value"] for row in first)
    assert [(row["candidate_id"], row["input_fingerprint"]) for row in first] == [
        (row["candidate_id"], row["input_fingerprint"]) for row in second
    ]
    assert all(row["status"] == "pending_review" for row in first)
    assert all(row["source_refs"] and row["input_fingerprint"] in row["candidate_id"] for row in first)
    assert all(row["provider"] == "mock" and row["model"] and row["reason"] for row in first)


def test_evidence_or_prompt_changes_invalidate_fingerprint_and_candidate_id(config):
    base_item = collect_unmapped_relations([relationship()], {})[0]
    changed_item = collect_unmapped_relations([relationship(source_refs=["rfc8205", "rfc9999"])], {})[0]
    base = build_mock_candidates([base_item], config, generated_at="2026-06-29T00:00:00Z")[0]
    changed = build_mock_candidates([changed_item], config, generated_at="2026-06-29T00:00:00Z")[0]
    prompt_config = copy.deepcopy(config)
    prompt_config["model_policy"]["prompt_version"] = "standard_mapping_v2"
    prompt_changed = build_mock_candidates([base_item], prompt_config, generated_at="2026-06-29T00:00:00Z")[0]

    assert base["input_fingerprint"] != changed["input_fingerprint"]
    assert base["candidate_id"] != changed["candidate_id"]
    assert base["input_fingerprint"] != prompt_changed["input_fingerprint"]
    assert base["candidate_id"] != prompt_changed["candidate_id"]


def test_different_suggested_mappings_have_different_candidate_ids(config):
    item = collect_unmapped_relations([relationship()], {})[0]
    fingerprint = build_input_fingerprint(item, config["model_policy"]["prompt_version"])

    first = build_candidate_id("relation", "secures", "bgpkb:secures", fingerprint)
    second = build_candidate_id("relation", "secures", "dcterms:relation", fingerprint)

    assert first != second
    assert fingerprint in first and fingerprint in second


def valid_candidate_and_items(config):
    items = collect_unmapped_relations([relationship()], {})
    return build_mock_candidates(items, config, generated_at="2026-06-29T00:00:00Z")[0], items


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda row: row.update(suggested_mapping="evil:predicate"), "unknown_prefix"),
        (lambda row: row.update(source_refs=[]), "source_refs"),
        (lambda row: row.update(confidence=0.49), "minimum_confidence"),
        (lambda row: row.update(confidence=True), "confidence_type"),
        (lambda row: row.update(status="approved"), "status"),
        (lambda row: row.update(unexpected="value"), "additional_property"),
        (lambda row: row.update(evidence_summary=42), "evidence_summary"),
        (lambda row: row.update(generated_at=42), "generated_at"),
        (lambda row: row.update(local_value="invented_relation"), "local_value"),
        (lambda row: row.update(input_fingerprint="0" * 64), "input_fingerprint"),
        (lambda row: row.update(candidate_id="candidate-without-fingerprint"), "candidate_id"),
    ],
)
def test_validate_candidate_rejects_model_safety_boundary_violations(config, mutate, expected):
    candidate, items = valid_candidate_and_items(config)
    mutate(candidate)

    errors = validate_candidate(candidate, config, items)

    assert expected in errors


def test_parse_structured_response_rejects_invalid_json_and_envelope(config):
    items = collect_unmapped_relations([relationship()], {})

    candidates, errors = parse_structured_response("not-json", config, items)
    assert candidates == [] and errors[0]["error_code"] == "invalid_json"

    candidates, errors = parse_structured_response(
        json.dumps({"candidates": [], "raw_response": "forbidden"}), config, items
    )
    assert candidates == [] and errors[0]["error_code"] == "invalid_envelope"
    assert "raw_response" not in json.dumps(errors)


def test_mixed_response_keeps_only_valid_candidates_without_raw_response(config):
    items = collect_unmapped_relations([relationship()], {})
    valid = {
        "candidate_type": "relation",
        "local_value": "secures",
        "suggested_mapping": "bgpkb:secures",
        "source_refs": ["rfc8205"],
        "confidence": 0.9,
        "reason": "保留项目受控谓词。",
    }
    invalid = dict(valid, status="approved")
    content = json.dumps({"candidates": [valid, invalid]}, ensure_ascii=False)

    candidates, errors = parse_structured_response(content, config, items)

    assert len(candidates) == 1
    assert candidates[0]["provider"] == "deepseek"
    assert candidates[0]["status"] == "pending_review"
    assert errors and errors[0]["error_code"] == "invalid_candidate"
    assert "raw_response" not in json.dumps(errors)


class CountingClient:
    model = "deepseek-chat"

    def __init__(self, content=""):
        self.content = content
        self.calls = 0

    def generate_standard_mapping_candidates(self, items, prompt_version):
        self.calls += 1
        return {
            "ok": True,
            "provider": "deepseek",
            "model": self.model,
            "content": self.content,
            "raw_usage": {"total_tokens": 12},
        }


def write_minimal_project(root, config, rows):
    config_path = root / "metadata/config/standard_exports.yaml"
    relationships_path = root / "data/knowledge/relationships/relationships.jsonl"
    config_path.parent.mkdir(parents=True)
    relationships_path.parent.mkdir(parents=True)
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    relationships_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )


def test_missing_deepseek_key_skips_without_calling_or_overwriting(tmp_path, config, monkeypatch):
    write_minimal_project(tmp_path, config, [relationship()])
    candidates_path = tmp_path / config["outputs"]["candidates"]
    errors_path = tmp_path / config["outputs"]["candidate_errors"]
    candidates_path.parent.mkdir(parents=True)
    candidates_path.write_text("old candidates\n", encoding="utf-8")
    errors_path.write_text("old errors\n", encoding="utf-8")
    client = CountingClient()
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    result = run_generation(tmp_path, config, provider="deepseek", client=client)

    assert result["status"] == "skipped"
    assert client.calls == 0
    assert candidates_path.read_text(encoding="utf-8") == "old candidates\n"
    assert errors_path.read_text(encoding="utf-8") == "old errors\n"


def test_fake_deepseek_client_writes_valid_structured_result_without_key_or_raw_response(
    tmp_path, config, monkeypatch
):
    write_minimal_project(tmp_path, config, [relationship()])
    semantic_suggestion = {
        "candidate_type": "relation",
        "local_value": "secures",
        "suggested_mapping": "bgpkb:secures",
        "source_refs": ["rfc8205"],
        "evidence_summary": "本地关系证据。",
        "confidence": 0.9,
        "reason": "保留项目受控谓词。",
    }
    client = CountingClient(json.dumps({"candidates": [semantic_suggestion]}, ensure_ascii=False))
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret-test-key")

    result = run_generation(
        tmp_path, config, provider="deepseek", client=client, generated_at="2026-06-29T00:00:00Z"
    )

    assert result["status"] == "generated" and client.calls == 1
    serialized = "".join(
        (tmp_path / config["outputs"][key]).read_text(encoding="utf-8")
        for key in ("candidates", "candidate_errors")
    )
    assert "secret-test-key" not in serialized
    assert "raw_response" not in serialized and "raw_usage" not in serialized
    written = json.loads((tmp_path / config["outputs"]["candidates"]).read_text(encoding="utf-8"))
    assert written["provider"] == "deepseek"
    assert written["model"] == "deepseek-chat"
    assert written["status"] == "pending_review"
    assert written["input_fingerprint"] in written["candidate_id"]


def test_unknown_provider_fails_instead_of_falling_back(tmp_path, config):
    write_minimal_project(tmp_path, config, [relationship()])

    with pytest.raises(ValueError, match="Unknown provider"):
        run_generation(tmp_path, config, provider="other")


def test_cli_generates_jsonl_and_chinese_report(tmp_path, config):
    write_minimal_project(tmp_path, config, [relationship()])
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "bgpkb.pipeline.build_standard_mapping_candidates",
            "--root",
            str(tmp_path),
            "--provider",
            "mock",
            "--generated-at",
            "2026-06-29T00:00:00Z",
        ],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    candidates = (tmp_path / config["outputs"]["candidates"]).read_text(encoding="utf-8")
    errors = (tmp_path / config["outputs"]["candidate_errors"]).read_text(encoding="utf-8")
    report = (tmp_path / "data/generated/reports/review/standard_mapping_candidate_report.md").read_text(
        encoding="utf-8"
    )
    assert candidates and errors == ""
    assert report.startswith("# 标准映射候选生成报告\n")
    assert "待人工审核" in report and "mock" in report


def test_report_policy_registers_candidate_report():
    policy = yaml.safe_load((ROOT / "metadata/config/report_policy.yaml").read_text(encoding="utf-8"))

    assert policy["reports"]["standard_mapping_candidate_report"] == {
        "path": "data/generated/reports/review/standard_mapping_candidate_report.md",
        "category": "review",
        "retention": "generated",
        "human_entry": False,
    }
