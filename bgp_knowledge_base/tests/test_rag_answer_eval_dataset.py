import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "datasets" / "rag_answer_eval_questions.jsonl"


REQUIRED_FIELDS = {
    "question_id",
    "query",
    "expected_status",
    "must_have_terms",
    "forbidden_terms",
    "expected_source_refs",
    "notes",
}
VALID_STATUSES = {"answered", "no_evidence"}


def load_rows():
    return [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_rag_answer_eval_dataset_has_required_shape_and_coverage():
    rows = load_rows()

    assert len(rows) >= 20
    assert len({row["question_id"] for row in rows}) == len(rows)
    assert sum(1 for row in rows if row["expected_status"] == "no_evidence") >= 3
    assert any("路由泄露" in row["query"] for row in rows)
    assert any("RPKI" in row["query"] for row in rows)

    for row in rows:
        assert REQUIRED_FIELDS <= set(row)
        assert row["expected_status"] in VALID_STATUSES
        assert isinstance(row["must_have_terms"], list)
        assert isinstance(row["forbidden_terms"], list)
        assert isinstance(row["expected_source_refs"], list)

