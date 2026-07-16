"""Explicit inventory of tests that require a published artifact or stale history."""

ARTIFACT_TEST_NODEIDS = frozenset({
    "tests/test_cleaning_v2_batch.py::test_batch_cli_legacy_fallback_preserves_explicit_yaml_evidence",
    "tests/test_deepseek_eval_analysis.py::test_deepseek_runner_writes_separate_real_eval_outputs_without_key_leak",
    "tests/test_hybrid_retrieval.py::test_chinese_route_leak_query_expands_and_returns_trusted_results",
    "tests/test_hybrid_retrieval.py::test_processed_source_is_retrieval_eligible_without_changing_review_status",
    "tests/test_hybrid_retrieval.py::test_named_tool_query_surfaces_matching_documentation",
    "tests/test_hybrid_retrieval.py::test_hybrid_query_cli_outputs_json",
    "tests/test_hybrid_retrieval.py::test_v1_retrieval_framework_search_remains_available",
    "tests/test_hybrid_retrieval_eval.py::test_hybrid_retrieval_eval_dataset_has_required_shape_and_coverage",
    "tests/test_lifecycle_metadata.py::test_lifecycle_script_generates_inventory_and_report",
    "tests/test_llm_candidate_enrichment.py::test_mock_candidate_generation_is_offline_traceable_and_does_not_edit_entities",
    "tests/test_pipeline_query_examples.py::test_query_examples_script_matches_current_published_database",
    "tests/test_quality_check_frontmatter.py::test_quality_check_accepts_cleaned_markdown_with_frontmatter",
    "tests/test_rag_answer.py::test_answer_question_generates_traceable_answer_when_evidence_exists",
    "tests/test_rag_answer.py::test_answer_question_falls_back_to_evidence_when_llm_is_unavailable",
    "tests/test_rag_answer_eval_dataset.py::test_rag_answer_eval_dataset_has_required_shape_and_coverage",
    "tests/test_rag_answer_eval_script.py::test_eval_script_scores_answers_and_renders_report_without_key_leak",
    "tests/test_rag_answer_smoke_script.py::test_smoke_script_builds_report_without_leaking_api_key",
    "tests/test_rag_indexes.py::test_mock_embedding_index_is_offline_and_preserves_chunk_catalog",
    "tests/test_rag_readiness_report.py::test_rag_readiness_report_records_framework_boundaries_and_api_entries",
    "tests/test_rag_retrieval.py::test_search_route_leak_returns_traceable_offline_results",
    "tests/test_rag_retrieval.py::test_chinese_route_leak_query_uses_term_expansion_and_context_pack_excludes_policy_items",
    "tests/test_rag_retrieval.py::test_cli_context_pack_outputs_json",
    "tests/test_rag_retrieval_ranking.py::test_definition_query_prefers_standard_sources",
    "tests/test_rag_retrieval_ranking.py::test_incident_query_prefers_case_sources",
    "tests/test_rag_retrieval_ranking.py::test_chinese_route_leak_expansion_surfaces_route_leak_results",
    "tests/test_semantic_identity.py::test_semantic_identity_script_generates_context_id_map_and_report",
    "tests/test_semantic_quality.py::test_semantic_quality_script_generates_findings_and_report",
    "tests/test_service_api.py::test_health_reports_existing_sqlite_database",
    "tests/test_service_api.py::test_stats_returns_core_counts_and_review_statuses",
    "tests/test_service_api.py::test_entity_detail_includes_sources_evidence_relationships_and_actions",
    "tests/test_service_api.py::test_missing_entity_returns_404",
    "tests/test_service_api.py::test_source_detail_includes_entities_and_chunks",
    "tests/test_service_api.py::test_entity_and_chunk_search_return_results",
    "tests/test_service_api.py::test_actions_can_filter_needs_llm",
    "tests/test_service_api.py::test_retrieval_api_returns_traceable_search_evidence_and_context_pack",
    "tests/test_service_api.py::test_hybrid_api_returns_fused_search_and_context_pack",
    "tests/test_service_api.py::test_hybrid_context_pack_accepts_stage_b_parameters_and_rejects_invalid_values",
    "tests/test_service_api.py::test_rag_answer_api_returns_evidence_when_llm_key_is_missing",
    "tests/test_service_api.py::test_html_pages_render_search_and_entity_detail",
    "tests/test_stage_acceptance.py::test_stage_acceptance_agent_outputs_effect_oriented_report",
    "tests/test_stage_b_retrieval_contracts.py::test_chunk_schema_keeps_v1_compatible_and_gates_v2_hierarchy_fields",
    "tests/test_standard_exports.py::test_cli_generates_deterministic_standard_exports_without_changing_primary_inputs",
    "tests/test_standard_mapping_candidates.py::test_real_mock_candidates_are_stable_sorted_and_traceable",
})

SERVING_ARTIFACT_TEST_NODEIDS = frozenset({
    "tests/test_serving_artifact_runtime.py::test_serving_artifact_health_and_database_are_read_only",
    "tests/test_serving_artifact_runtime.py::test_serving_artifact_keeps_traceable_retrieval_api",
})

LEGACY_DOCUMENTATION_TEST_NODEIDS = frozenset({
    "tests/test_stage_b_server_routing.py::test_current_server_routing_documents_do_not_retain_retired_server_assumptions",
    "tests/test_stage_b_server_routing.py::test_stage_b_design_documents_new_server_and_gpu_safety_boundaries",
    "tests/test_stage_b_server_routing.py::test_stage_b_plan_requires_selector_generated_distinct_cdi_devices",
})


def marker_for(nodeid: str) -> str | None:
    if nodeid in ARTIFACT_TEST_NODEIDS:
        return "artifact"
    if nodeid in SERVING_ARTIFACT_TEST_NODEIDS:
        return "serving_artifact"
    if nodeid in LEGACY_DOCUMENTATION_TEST_NODEIDS:
        return "legacy_documentation"
    return None
