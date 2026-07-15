from __future__ import annotations

from collections import Counter, defaultdict

import yaml

from bgpkb import paths


DATASET = paths.METADATA_DIR / "evaluation" / "retrieval_gold_v1.jsonl"
SCHEMA = paths.SCHEMAS_DIR / "retrieval_gold_question_v1.schema.json"


def _load_rows() -> list[dict]:
    from bgpkb.domain.evaluation_gold import load_versioned_jsonl

    return load_versioned_jsonl(
        DATASET,
        schema_path=SCHEMA,
        schema_version="retrieval_gold_question_v1",
        dataset_version="retrieval_gold_v1.0.0",
    )


def test_retrieval_gold_has_100_versioned_unique_traceable_questions():
    rows = _load_rows()
    registry = yaml.safe_load(
        (paths.METADATA_DIR / "sources" / "source_registry.yaml").read_text(encoding="utf-8")
    )
    registered_source_ids = {source["source_id"] for source in registry["sources"]}

    assert len(rows) >= 100
    assert len({row["question_id"] for row in rows}) == len(rows)
    assert {row["language"] for row in rows} == {"zh", "en"}
    assert {row["query_type"] for row in rows} == {"fact", "process", "policy", "global"}
    assert all(row["owner_ref"].endswith("#retrieval_gold") for row in rows)

    for row in rows:
        if row["expected_status"] == "evidence":
            assert row["expected_evidence"]
            assert all(
                {"source_id", "source_ref", "support"} <= set(evidence)
                for evidence in row["expected_evidence"]
            )
            assert {
                evidence["source_id"] for evidence in row["expected_evidence"]
            } <= registered_source_ids
        else:
            assert row["expected_status"] == "no_evidence"
            assert row["expected_evidence"] == []


def test_retrieval_gold_covers_languages_query_types_and_adversarial_features():
    rows = _load_rows()
    by_language = Counter(row["language"] for row in rows)
    by_type = Counter(row["query_type"] for row in rows)
    type_languages: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        type_languages[row["query_type"]].add(row["language"])

    assert min(by_language.values()) >= 40
    assert min(by_type.values()) >= 20
    assert all(languages == {"zh", "en"} for languages in type_languages.values())
    assert sum("synonym" in row["query_features"] for row in rows) >= 12
    assert sum("source_conflict" in row["query_features"] for row in rows) >= 8
    assert sum("hard_negative" in row["query_features"] for row in rows) >= 12
    assert all(
        row["conflict_group"]
        for row in rows
        if "source_conflict" in row["query_features"]
    )
