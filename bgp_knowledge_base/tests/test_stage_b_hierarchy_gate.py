import pytest

from bgpkb.pipeline import quality_check


def _fixture(count=100, unresolved=1):
    chunks = []
    resolved_count = count - unresolved
    for index in range(count):
        resolved = index < resolved_count
        chunks.append({
            "chunk_id": f"chunk-{index}", "doc_id": "doc-a",
            "hierarchy_status": "resolved" if resolved else "unresolved",
            "parent_section_id": "section-a" if resolved else None,
            "chunk_order": index if resolved else None,
            "previous_chunk_id": f"chunk-{index - 1}" if resolved and index else None,
            "next_chunk_id": f"chunk-{index + 1}" if resolved and index + 1 < resolved_count else None,
            "source_ref": "raw.pdf#p1", "source_block_ids": [f"block-{index}"],
        })
    section = {
        "schema_version": "section_catalog_v1", "section_id": "section-a", "content_hash": "sha256:x",
        "doc_id": "doc-a", "heading": "A", "section_path": ["A"], "section_order": 0,
        "parent_section_id": None, "child_section_ids": [], "previous_section_id": None,
        "next_section_id": None, "source_ref": "raw.pdf#p1",
        "child_chunk_ids": [row["chunk_id"] for row in chunks if row["hierarchy_status"] == "resolved"],
        "block_ids": [f"block-{index}" for index in range(count)], "content_chars": 1, "estimated_tokens": 1,
    }
    return chunks, [section]


def test_quality_loader_includes_section_catalog_schema():
    assert quality_check.load_schemas()["section_catalog"]["title"] == "SectionCatalog"


def test_generated_resolution_boundary_accepts_99_percent_and_published_100_percent():
    generated, sections = _fixture(unresolved=1)
    result = quality_check.validate_stage_b_hierarchy(
        corpus_version="v2", generated_chunks=generated,
        published_chunks=generated[:99], sections=sections,
    )

    assert result["passed"] is True
    assert result["resolution_rate"] == 0.99
    assert result["unresolved_count"] == 1
    assert result["published_traceability_rate"] == 1.0
    assert result["errors"] == []


def test_generated_resolution_below_99_percent_is_blocked():
    generated, sections = _fixture(unresolved=2)
    result = quality_check.validate_stage_b_hierarchy(
        corpus_version="v2", generated_chunks=generated,
        published_chunks=generated[:98], sections=sections,
    )

    assert result["passed"] is False
    assert result["resolution_rate"] == 0.98
    assert any("99%" in error for error in result["errors"])


def test_v2_empty_hierarchy_samples_are_blocked():
    result = quality_check.validate_stage_b_hierarchy(
        corpus_version="v2", generated_chunks=[], published_chunks=[], sections=[],
    )

    assert result["passed"] is False
    assert any("为空" in error for error in result["errors"])


def test_generated_hierarchy_status_rejects_unknown_value():
    generated, sections = _fixture(count=100, unresolved=1)
    generated[-1]["hierarchy_status"] = "resovled"

    result = quality_check.validate_stage_b_hierarchy(
        corpus_version="v2",
        generated_chunks=generated,
        published_chunks=generated[:-1],
        sections=sections,
    )

    assert result["passed"] is False
    assert any("hierarchy_status" in error for error in result["errors"])


def test_published_chunk_ids_must_cover_all_resolved_chunks():
    generated, sections = _fixture(count=1, unresolved=0)

    result = quality_check.validate_stage_b_hierarchy(
        corpus_version="v2",
        generated_chunks=generated,
        published_chunks=[],
        sections=sections,
    )

    assert result["passed"] is False
    assert any("published" in error and "chunk_id" in error for error in result["errors"])


@pytest.mark.parametrize(
    ("wrong_link_count", "expected_accuracy", "expected_passed"),
    [(1, 0.99, True), (2, 0.98, True), (3, 0.97, False)],
)
def test_generated_adjacency_uses_98_percent_accuracy_gate(
    wrong_link_count, expected_accuracy, expected_passed,
):
    generated, sections = _fixture(count=50, unresolved=0)
    for index in range(1, wrong_link_count + 1):
        generated[index]["previous_chunk_id"] = "wrong-neighbor"

    result = quality_check.validate_stage_b_hierarchy(
        corpus_version="v2",
        generated_chunks=generated,
        published_chunks=generated,
        sections=sections,
    )

    assert result["adjacent_context_eligible_count"] == 100
    assert result["adjacent_context_correct_count"] == 100 - wrong_link_count
    assert result["adjacent_context_accuracy"] == expected_accuracy
    assert result["passed"] is expected_passed


def test_published_requires_100_percent_and_v1_skips_gate():
    generated, sections = _fixture(count=2, unresolved=1)
    published = [generated[0], generated[1]]

    blocked = quality_check.validate_stage_b_hierarchy(
        corpus_version="v2", generated_chunks=generated, published_chunks=published, sections=sections,
    )
    skipped = quality_check.validate_stage_b_hierarchy(
        corpus_version="v1", generated_chunks=[{"chunk_id": "legacy"}],
        published_chunks=[{"chunk_id": "legacy"}], sections=[],
    )

    assert blocked["passed"] is False
    assert any("published" in error for error in blocked["errors"])
    assert skipped == {"passed": True, "skipped": True, "reason": "v1 不适用阶段 B 层级门禁"}


def test_section_schema_and_cross_document_links_are_blocking():
    generated, sections = _fixture(count=1, unresolved=0)
    sections[0]["schema_version"] = "bad"
    sections[0]["doc_id"] = "doc-b"

    result = quality_check.validate_stage_b_hierarchy(
        corpus_version="v2", generated_chunks=generated, published_chunks=generated, sections=sections,
    )

    assert result["passed"] is False
    assert any("schema" in error for error in result["errors"])
    assert any("跨文档" in error for error in result["errors"])
