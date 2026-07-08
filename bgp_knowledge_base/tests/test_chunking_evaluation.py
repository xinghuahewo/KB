from bgpkb.pipeline.evaluate_chunking import (
    compare_answer_quality,
    evaluate_structure,
    render_report,
)


def test_evaluate_structure_computes_stage_b_gate_rates():
    chunks = [
        {
            "chunk_id": "c1",
            "hierarchy_status": "resolved",
            "parent_section_id": "s1",
            "previous_chunk_id": None,
            "next_chunk_id": "c2",
        },
        {
            "chunk_id": "c2",
            "hierarchy_status": "resolved",
            "parent_section_id": "s1",
            "previous_chunk_id": "c1",
            "next_chunk_id": None,
        },
        {
            "chunk_id": "c3",
            "hierarchy_status": "unresolved",
            "parent_section_id": None,
            "previous_chunk_id": None,
            "next_chunk_id": None,
        },
    ]
    context_packs = [{
        "question_id": "q1",
        "candidate_chunk_count": 20,
        "reranked_chunk_count": 5,
        "context_units": [{
            "included_chunk_ids": ["c1", "c2"],
            "citations": [
                {"chunk_id": "c1", "source_ref": "s#1"},
                {"chunk_id": "c2", "source_ref": "s#2"},
            ],
        }],
    }]

    summary = evaluate_structure(chunks, context_packs)

    assert summary["resolved_coverage_rate"] == 2 / 3
    assert summary["parent_traceability_rate"] == 1.0
    assert summary["adjacent_context_correctness_rate"] == 1.0
    assert summary["citation_completeness_rate"] == 1.0
    assert summary["candidate_chunk_count_values"] == [20]
    assert summary["reranked_chunk_count_values"] == [5]


def test_compare_answer_quality_uses_only_is_critical_true_for_critical_gate():
    baseline = [
        {"question_id": "a", "quality_score": 0.9, "is_critical": True},
        {"question_id": "b", "quality_score": 0.8, "is_critical": False},
        {"question_id": "c", "quality_score": 0.7, "is_critical": True},
    ]
    current = [
        {"question_id": "a", "quality_score": 0.86, "is_critical": True},
        {"question_id": "b", "quality_score": 0.5, "is_critical": False},
        {"question_id": "c", "quality_score": 0.66, "is_critical": True},
    ]

    comparison = compare_answer_quality(current, baseline)

    assert round(comparison["average_degradation_points"], 4) == 0.1267
    assert round(comparison["critical_degradation_points"], 4) == 0.04
    assert comparison["critical_question_ids"] == ["a", "c"]
    assert comparison["passes_average_gate"] is False
    assert comparison["passes_critical_gate"] is True


def test_compare_answer_quality_without_baseline_marks_structure_only_mode():
    comparison = compare_answer_quality([{"question_id": "a", "quality_score": 0.8}], baseline=None)

    assert comparison["baseline_available"] is False
    assert comparison["structure_only_mode"] is True


def test_render_report_is_chinese_and_mentions_structure_only_mode():
    report = render_report(
        {
            "resolved_coverage_rate": 1.0,
            "parent_traceability_rate": 1.0,
            "adjacent_context_correctness_rate": 1.0,
            "citation_completeness_rate": 1.0,
        },
        {"baseline_available": False, "structure_only_mode": True},
    )

    assert "# 阶段 B Chunking / Retrieval 评测报告" in report
    assert "无成熟答案基线" in report
