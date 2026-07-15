from __future__ import annotations

from collections import Counter

import yaml

from bgpkb import paths


DATASET = paths.METADATA_DIR / "evaluation" / "answer_gold_v1.jsonl"
SCHEMA = paths.SCHEMAS_DIR / "answer_gold_case_v1.schema.json"
MANIFEST = paths.METADATA_DIR / "evaluation" / "rag_gold_manifest_v1.yaml"
SCORING_GUIDE = paths.PROJECT_ROOT.parent / "docs" / "quality" / "rag-answer-gold-scoring-v1.md"


def _load_rows() -> list[dict]:
    from bgpkb.domain.evaluation_gold import load_versioned_jsonl

    return load_versioned_jsonl(
        DATASET,
        schema_path=SCHEMA,
        schema_version="answer_gold_case_v1",
        dataset_version="answer_gold_v1.0.0",
    )


def test_answer_gold_is_structured_and_covers_required_answer_behaviors():
    rows = _load_rows()
    from bgpkb.domain.evaluation_gold import load_versioned_jsonl

    retrieval_rows = load_versioned_jsonl(
        paths.METADATA_DIR / "evaluation" / "retrieval_gold_v1.jsonl",
        schema_path=paths.SCHEMAS_DIR / "retrieval_gold_question_v1.schema.json",
        schema_version="retrieval_gold_question_v1",
        dataset_version="retrieval_gold_v1.0.0",
    )
    retrieval_by_id = {row["question_id"]: row for row in retrieval_rows}
    tags = Counter(tag for row in rows for tag in row["scenario_tags"])

    assert len(rows) >= 24
    assert len({row["case_id"] for row in rows}) == len(rows)
    assert {row["language"] for row in rows} == {"zh", "en"}
    assert tags["claim_correctness"] >= 12
    assert tags["citation_precision"] >= 12
    assert tags["citation_recall"] >= 12
    assert tags["refusal"] >= 6
    assert tags["prompt_injection"] >= 4
    assert tags["source_conflict"] >= 4

    for row in rows:
        retrieval_question = retrieval_by_id[row["retrieval_question_id"]]
        allowed_refs = {
            evidence["source_ref"] for evidence in retrieval_question["expected_evidence"]
        }
        if row["expected_status"] == "answered":
            assert row["expected_claims"]
            assert all(claim["acceptable_evidence_refs"] for claim in row["expected_claims"])
            assert row["required_behavior"] in {"answer_from_evidence", "compare_sources"}
            assert {
                evidence_ref
                for claim in row["expected_claims"]
                for evidence_ref in claim["acceptable_evidence_refs"]
            } <= allowed_refs
        else:
            assert row["expected_status"] == "no_evidence"
            assert row["expected_claims"] == []
            assert row["required_behavior"] == "refuse_without_evidence"
        if "prompt_injection" in row["scenario_tags"]:
            assert row["attack_payload"]


def test_answer_gold_manifest_and_chinese_manual_scoring_guide_are_auditable():
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    guide = SCORING_GUIDE.read_text(encoding="utf-8")

    assert manifest["schema_version"] == "rag_gold_manifest_v1"
    assert manifest["retrieval_gold"]["version"] == "retrieval_gold_v1.0.0"
    assert manifest["answer_gold"]["version"] == "answer_gold_v1.0.0"
    assert manifest["retrieval_gold"]["question_count"] == 104
    assert manifest["answer_gold"]["case_count"] == 24
    assert manifest["ownership"]["status"] == "assigned"
    assert manifest["ownership"]["signed_by"] == ["吴柏橦", "兴华"]
    assert manifest["ownership"]["approval_evidence"].endswith(".json")
    assert manifest["ownership"]["release_effect"] == "ready"
    assert manifest["model_binding"]["embedding"]["model"] == "BAAI/bge-m3"
    assert manifest["model_binding"]["reranker"]["model"] == "BAAI/bge-reranker-v2-m3"
    assert manifest["model_binding"]["llm"] == {
        "provider": "deepseek",
        "model": "deepseek-v4-pro",
        "revision": "DeepSeek-V4-Pro@2026-04-24",
        "status": "pinned",
    }
    assert manifest["prompt_version"] == "grounded_answer_prompt_v1"
    for phrase in ("主张正确性", "引用精确率", "引用召回率", "拒答", "提示注入"):
        assert phrase in guide
