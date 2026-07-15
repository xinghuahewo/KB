import json
from pathlib import Path

from bgpkb.ingestion.dedup_strategy_evaluation import evaluate_strategies, initial_policy


GOLD = Path(__file__).parent / "fixtures" / "rag_evidence_pipeline_v2" / "dedup_gold.json"


def test_dedup_strategy_comparison_reports_false_collapse_and_missed_duplicate_rates():
    pairs = json.loads(GOLD.read_text(encoding="utf-8"))["pairs"]

    report = evaluate_strategies(pairs)

    assert set(report["strategies"]) == {"exact_hash", "token_shingles", "minhash", "simhash"}
    for metrics in report["strategies"].values():
        assert metrics["pair_count"] == len(pairs)
        assert 0 <= metrics["false_collapse_rate"] <= 1
        assert 0 <= metrics["missed_duplicate_rate"] <= 1
        assert set(metrics["decisions"]) == {pair["id"] for pair in pairs}
    assert report["strategies"]["exact_hash"]["false_collapse_count"] == 0


def test_unapproved_near_duplicate_strategy_keeps_exact_only_as_hard_gate():
    pairs = json.loads(GOLD.read_text(encoding="utf-8"))["pairs"]
    report = evaluate_strategies(pairs)

    assert initial_policy(report, near_duplicate_approved=False) == {
        "hard_gate": "exact_hash",
        "near_duplicate_mode": "diagnostic_only",
        "cross_source_collapse": False,
    }
