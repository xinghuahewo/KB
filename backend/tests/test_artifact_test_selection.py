from artifact_tests import marker_for


def test_real_retrieval_checks_are_selected_for_the_artifact_gate():
    assert marker_for(
        "tests/test_hybrid_retrieval.py::test_chinese_route_leak_query_expands_and_returns_trusted_results"
    ) == "artifact"


def test_cli_that_builds_real_rag_indexes_is_selected_for_the_artifact_gate():
    assert marker_for(
        "tests/test_rag_retrieval.py::test_cli_context_pack_outputs_json"
    ) == "artifact"


def test_pure_runtime_path_contract_is_not_selected_for_the_artifact_gate():
    assert marker_for(
        "tests/test_runtime_data_paths.py::test_runtime_data_dir_uses_configured_directory"
    ) is None


def test_v2_read_only_runtime_checks_use_serving_artifact_gate():
    assert marker_for(
        "tests/test_serving_artifact_runtime.py::test_serving_artifact_health_and_database_are_read_only"
    ) == "serving_artifact"


def test_stale_historical_document_checks_are_separated_from_the_pr_baseline():
    assert marker_for(
        "tests/test_stage_b_server_routing.py::test_stage_b_design_documents_new_server_and_gpu_safety_boundaries"
    ) == "legacy_documentation"
