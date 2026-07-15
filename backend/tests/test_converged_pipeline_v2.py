from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


EXPECTED_STAGES = (
    "source-ingest",
    "canonicalize",
    "semantic-build",
    "publish-index",
    "verify-release",
)


def _pipeline():
    from bgpkb.workflows import converged_pipeline

    return converged_pipeline


def _write_required_outputs(context, *, excluded: set[str] | None = None) -> None:
    excluded = excluded or set()
    for relative in context.stage.required_outputs:
        if relative in excluded:
            continue
        path = context.candidate_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{context.stage.name}:{relative}\n", encoding="utf-8")


def _successful_executor(calls: list[tuple[str, str]], *, excluded: set[str] | None = None):
    def execute(context):
        calls.append((context.stage.name, context.subtask.subtask_id))
        _write_required_outputs(context, excluded=excluded)
        return {
            "returncode": 0,
            "stdout": f"完成 {context.subtask.subtask_id}",
            "stderr": "",
            "diagnostics": {"records": 1},
        }

    return execute


def _run(
    candidate_dir: Path,
    *,
    target_stage: str = "verify-release",
    calls: list[tuple[str, str]] | None = None,
    task_executor=None,
    external_input_fingerprints: dict[str, dict[str, str]] | None = None,
    stage_config_fingerprints: dict[str, str] | None = None,
    code_fingerprint: str = "sha256:code-v1",
):
    pipeline = _pipeline()
    recorded_calls = calls if calls is not None else []
    return pipeline.run_pipeline(
        candidate_dir=candidate_dir,
        target_stage=target_stage,
        task_executor=task_executor or _successful_executor(recorded_calls),
        external_input_fingerprints=external_input_fingerprints or {},
        stage_config_fingerprints=stage_config_fingerprints or {},
        code_fingerprint=code_fingerprint,
        protected_paths=(),
    )


def test_five_stage_dependency_contract_is_fixed_and_linear():
    pipeline = _pipeline()
    definition = pipeline.load_pipeline_definition()

    assert pipeline.STAGE_ORDER == EXPECTED_STAGES
    assert tuple(definition.stages) == EXPECTED_STAGES
    assert {
        name: stage.depends_on
        for name, stage in definition.stages.items()
    } == {
        "source-ingest": (),
        "canonicalize": ("source-ingest",),
        "semantic-build": ("canonicalize",),
        "publish-index": ("semantic-build",),
        "verify-release": ("publish-index",),
    }


def test_stage_failure_stops_downstream_and_preserves_candidate_diagnostics(tmp_path):
    pipeline = _pipeline()
    candidate_dir = tmp_path / "candidate"
    calls: list[tuple[str, str]] = []

    def fail_canonicalize(context):
        calls.append((context.stage.name, context.subtask.subtask_id))
        if context.stage.name == "canonicalize":
            return {
                "returncode": 23,
                "stdout": "",
                "stderr": "canonical schema closure failed",
                "diagnostics": {"error_code": "canonical_closure_failed"},
            }
        _write_required_outputs(context)
        return {"returncode": 0, "stdout": "ok", "stderr": ""}

    result = _run(candidate_dir, calls=calls, task_executor=fail_canonicalize)

    assert result["status"] == "failed"
    assert result["exit_code"] == 23
    assert result["failed_stage"] == "canonicalize"
    assert {stage for stage, _ in calls} == {"source-ingest", "canonicalize"}
    assert not any(stage in {"semantic-build", "publish-index", "verify-release"} for stage, _ in calls)
    failed_manifest = json.loads(
        pipeline.stage_manifest_path(candidate_dir, "canonicalize").read_text(encoding="utf-8")
    )
    assert failed_manifest["status"] == "failed"
    assert failed_manifest["subtasks"][-1]["returncode"] == 23
    assert failed_manifest["subtasks"][-1]["diagnostics"]["error_code"] == "canonical_closure_failed"


def test_verify_release_collects_reports_but_never_masks_nonzero_gate_failure(tmp_path):
    pipeline = _pipeline()
    candidate_dir = tmp_path / "candidate"
    calls: list[tuple[str, str]] = []

    def fail_one_report(context):
        calls.append((context.stage.name, context.subtask.subtask_id))
        _write_required_outputs(context)
        if (
            context.stage.name == "verify-release"
            and context.subtask.subtask_id == "build-release-gate-evidence"
        ):
            return {"returncode": 17, "stderr": "retrieval gold failed"}
        return {"returncode": 0, "stdout": "report retained", "stderr": ""}

    result = _run(candidate_dir, task_executor=fail_one_report)

    verify_subtasks = [
        subtask_id for stage, subtask_id in calls if stage == "verify-release"
    ]
    assert result["status"] == "failed"
    assert result["failed_stage"] == "verify-release"
    assert result["exit_code"] == 17
    assert verify_subtasks[-1] == "verify-candidate-release"
    manifest = json.loads(
        pipeline.stage_manifest_path(candidate_dir, "verify-release").read_text(encoding="utf-8")
    )
    assert any(
        row["error_code"] == "collected_gate_subtask_failure"
        and row["returncode"] == 17
        for row in manifest["diagnostics"]
    )
    failed = next(
        row for row in manifest["subtasks"]
        if row["subtask_id"] == "build-release-gate-evidence"
    )
    assert failed["failure_policy"] == "collect_for_gate"


def test_candidate_directory_is_rejected_when_it_is_current_or_previous(tmp_path):
    pipeline = _pipeline()
    current = tmp_path / "releases" / "current-release"
    previous = tmp_path / "releases" / "previous-release"
    current.mkdir(parents=True)
    previous.mkdir(parents=True)

    for protected in (current, previous):
        with pytest.raises(pipeline.CandidateIsolationError, match="候选目录"):
            pipeline.run_pipeline(
                candidate_dir=protected,
                target_stage="source-ingest",
                task_executor=lambda context: {"returncode": 0},
                code_fingerprint="sha256:code-v1",
                protected_paths=(current, previous),
            )


def test_subtasks_receive_only_candidate_scoped_runtime_paths(tmp_path):
    candidate_dir = tmp_path / "candidate"
    observed = []

    def inspect_environment(context):
        observed.append(context)
        assert Path(context.environment["BGPKB_CANDIDATE_DIR"]) == candidate_dir.resolve()
        assert Path(context.environment["BGPKB_DATA_DIR"]) == candidate_dir.resolve() / "data"
        assert Path(context.environment["BGPKB_SOURCE_STORE_DIR"]) == candidate_dir.resolve() / "source-store"
        _write_required_outputs(context)
        return {"returncode": 0, "stdout": "isolated", "stderr": ""}

    result = _run(
        candidate_dir,
        target_stage="source-ingest",
        task_executor=inspect_environment,
    )

    assert result["status"] == "complete"
    assert observed


def test_all_runtime_write_roots_and_temporary_paths_are_candidate_scoped(tmp_path):
    candidate_dir = (tmp_path / "candidate").resolve()
    observed = []

    def inspect_write_boundary(context):
        observed.append(context)
        assert context.write_paths
        assert all(
            path == candidate_dir or path.is_relative_to(candidate_dir)
            for path in context.write_paths
        )
        for name in ("TMPDIR", "TMP", "TEMP", "XDG_CACHE_HOME"):
            runtime_path = Path(context.environment[name]).resolve()
            assert runtime_path.is_relative_to(candidate_dir)
        assert context.environment["PYTHONDONTWRITEBYTECODE"] == "1"
        assert context.environment["BGPKB_RELEASE_ID"] == candidate_dir.name
        _write_required_outputs(context)
        return {"returncode": 0, "stdout": "isolated", "stderr": ""}

    result = _run(
        candidate_dir,
        target_stage="source-ingest",
        task_executor=inspect_write_boundary,
    )

    assert result["status"] == "complete"
    assert observed


def test_failure_preserves_release_pointers_and_marks_partial_candidate_unreadable(tmp_path):
    from bgpkb.infrastructure import serving_bundle

    pipeline = _pipeline()
    releases = tmp_path / "releases"
    current_release = releases / "release-current"
    previous_release = releases / "release-previous"
    for release, content in (
        (current_release, b"current release bytes\n"),
        (previous_release, b"previous release bytes\n"),
    ):
        (release / "data" / "published").mkdir(parents=True)
        (release / "data" / "published" / "sentinel.bin").write_bytes(content)
    current_pointer = releases / "current"
    previous_pointer = releases / "previous"
    current_pointer.symlink_to(current_release.name)
    previous_pointer.symlink_to(previous_release.name)
    before = {
        "current_target": current_pointer.readlink(),
        "previous_target": previous_pointer.readlink(),
        "current_bytes": (current_release / "data" / "published" / "sentinel.bin").read_bytes(),
        "previous_bytes": (previous_release / "data" / "published" / "sentinel.bin").read_bytes(),
    }
    candidate_dir = tmp_path / "candidate"

    def fail_after_partial_output(context):
        _write_required_outputs(context)
        partial = context.data_dir / "published" / serving_bundle.SERVING_DB_FILENAME
        partial.parent.mkdir(parents=True, exist_ok=True)
        partial.write_bytes(b"partial database")
        if context.stage.name == "canonicalize":
            return {"returncode": 31, "stderr": "candidate build failed"}
        return {"returncode": 0, "stdout": "ok", "stderr": ""}

    result = pipeline.run_pipeline(
        candidate_dir=candidate_dir,
        target_stage="verify-release",
        task_executor=fail_after_partial_output,
        code_fingerprint="sha256:code-v1",
        protected_paths=(current_pointer, previous_pointer),
    )

    assert result["status"] == "failed"
    assert current_pointer.readlink() == before["current_target"]
    assert previous_pointer.readlink() == before["previous_target"]
    assert (current_release / "data" / "published" / "sentinel.bin").read_bytes() == before["current_bytes"]
    assert (previous_release / "data" / "published" / "sentinel.bin").read_bytes() == before["previous_bytes"]
    candidate_state = json.loads(
        pipeline.candidate_state_path(candidate_dir).read_text(encoding="utf-8")
    )
    assert candidate_state["status"] == "failed"
    assert candidate_state["reader_selectable"] is False
    assert candidate_state["failed_stage"] == "canonicalize"
    with pytest.raises(serving_bundle.ServingBundleCompatibilityError, match="候选"):
        serving_bundle.resolve_serving_database_path(candidate_dir / "data")


def test_publish_index_fails_when_any_fast_index_artifact_is_missing(tmp_path):
    pipeline = _pipeline()
    candidate_dir = tmp_path / "candidate"
    calls: list[tuple[str, str]] = []
    missing = {pipeline.FAST_INDEX_ARTIFACTS[1]}

    result = _run(
        candidate_dir,
        target_stage="publish-index",
        calls=calls,
        task_executor=_successful_executor(calls, excluded=missing),
    )

    assert result["status"] == "failed"
    assert result["failed_stage"] == "publish-index"
    assert result["exit_code"] != 0
    manifest = json.loads(
        pipeline.stage_manifest_path(candidate_dir, "publish-index").read_text(encoding="utf-8")
    )
    assert manifest["diagnostics"] == [{
        "error_code": "missing_required_output",
        "path": pipeline.FAST_INDEX_ARTIFACTS[1],
    }]
    assert not pipeline.checkpoint_path(candidate_dir, "publish-index").exists()


def test_stable_cli_make_entries_and_stage_manifests_are_public(tmp_path):
    pipeline = _pipeline()
    definition = pipeline.load_pipeline_definition()
    parser = pipeline.build_parser()
    candidate_dir = tmp_path / "candidate"

    for stage_name in EXPECTED_STAGES:
        args = parser.parse_args([stage_name, "--candidate-dir", str(candidate_dir), "--plan-only"])
        assert args.stage == stage_name

    repository_root = Path(__file__).resolve().parents[2]
    makefile = (repository_root / "Makefile").read_text(encoding="utf-8")
    pyproject = (repository_root / "backend" / "pyproject.toml").read_text(encoding="utf-8")
    for stage_name in EXPECTED_STAGES:
        assert f"{stage_name}:" in makefile
    assert "bgpkb-pipeline" in makefile
    assert 'bgpkb-pipeline = "bgpkb.workflows.converged_pipeline:main"' in pyproject

    calls: list[tuple[str, str]] = []
    result = _run(candidate_dir, target_stage="source-ingest", calls=calls)
    manifest = json.loads(
        pipeline.stage_manifest_path(candidate_dir, "source-ingest").read_text(encoding="utf-8")
    )
    assert result["status"] == "complete"
    assert manifest["schema_version"] == "pipeline_stage_manifest_v1"
    assert manifest["pipeline_version"] == definition.pipeline_version
    assert manifest["stage"] == "source-ingest"
    assert manifest["status"] == "complete"


def test_source_ingest_cli_uses_frozen_input_and_binds_it_to_checkpoint_fingerprint(tmp_path):
    pipeline = _pipeline()
    candidate_dir = tmp_path / "candidate"
    frozen_root = tmp_path / "frozen"
    frozen_root.mkdir()
    (frozen_root / "source.txt").write_text("frozen source", encoding="utf-8")
    observed = []

    def inspect_frozen_input(context):
        observed.append(context)
        assert "--legacy-root" in context.command
        assert str(frozen_root.resolve()) in context.command
        _write_required_outputs(context)
        return {"returncode": 0, "stdout": "offline", "stderr": ""}

    result = pipeline.run_pipeline(
        candidate_dir=candidate_dir,
        target_stage="source-ingest",
        task_executor=inspect_frozen_input,
        code_fingerprint="sha256:code-v1",
        protected_paths=(),
        frozen_source_root=frozen_root,
    )

    assert result["status"] == "complete"
    assert observed
    checkpoint = json.loads(
        pipeline.checkpoint_path(candidate_dir, "source-ingest").read_text(encoding="utf-8")
    )
    frozen_fingerprint = checkpoint["fingerprint_components"]["inputs"]["external"][
        "frozen_source_root"
    ]
    assert frozen_fingerprint.startswith("sha256:")

    parsed = pipeline.build_parser().parse_args([
        "source-ingest",
        "--candidate-dir",
        str(candidate_dir),
        "--frozen-source-root",
        str(frozen_root),
        "--plan-only",
    ])
    assert parsed.frozen_source_root == frozen_root


def test_source_ingest_rejects_mutation_of_frozen_input(tmp_path):
    pipeline = _pipeline()
    candidate_dir = tmp_path / "candidate"
    frozen_root = tmp_path / "frozen"
    frozen_root.mkdir()
    frozen_file = frozen_root / "source.txt"
    frozen_file.write_text("immutable source", encoding="utf-8")

    def mutate_frozen_input(context):
        frozen_file.write_text("mutated source", encoding="utf-8")
        _write_required_outputs(context)
        return {"returncode": 0, "stdout": "mutated", "stderr": ""}

    result = pipeline.run_pipeline(
        candidate_dir=candidate_dir,
        target_stage="source-ingest",
        task_executor=mutate_frozen_input,
        code_fingerprint="sha256:code-v1",
        protected_paths=(),
        frozen_source_root=frozen_root,
    )

    assert result["status"] == "failed"
    assert result["exit_code"] == 70
    assert result["failed_stage"] == "source-ingest"
    candidate_state = json.loads(
        pipeline.candidate_state_path(candidate_dir).read_text(encoding="utf-8")
    )
    assert candidate_state["reader_selectable"] is False


def test_canonicalize_cli_binds_frozen_canonical_inputs_to_checkpoint(tmp_path):
    pipeline = _pipeline()
    candidate_dir = tmp_path / "candidate"
    frozen_canonical = tmp_path / "frozen-canonical"
    frozen_assets = tmp_path / "frozen-assets"
    frozen_canonical.mkdir()
    frozen_assets.mkdir()
    (frozen_canonical / "doc.json").write_text('{"doc_id":"doc"}', encoding="utf-8")
    (frozen_assets / "figure.bin").write_bytes(b"figure")
    observed = []

    def inspect_canonical_input(context):
        observed.append(context)
        _write_required_outputs(context)
        if context.stage.name == "canonicalize":
            assert "--frozen-canonical-root" in context.command
            assert str(frozen_canonical.resolve()) in context.command
            assert "--frozen-assets-root" in context.command
            assert str(frozen_assets.resolve()) in context.command
        return {"returncode": 0, "stdout": "offline", "stderr": ""}

    result = pipeline.run_pipeline(
        candidate_dir=candidate_dir,
        target_stage="canonicalize",
        task_executor=inspect_canonical_input,
        code_fingerprint="sha256:code-v1",
        protected_paths=(),
        frozen_canonical_root=frozen_canonical,
        frozen_assets_root=frozen_assets,
    )

    assert result["status"] == "complete"
    checkpoint = json.loads(
        pipeline.checkpoint_path(candidate_dir, "canonicalize").read_text(encoding="utf-8")
    )
    external = checkpoint["fingerprint_components"]["inputs"]["external"]
    assert external["frozen_canonical_root"].startswith("sha256:")
    assert external["frozen_assets_root"].startswith("sha256:")

    parsed = pipeline.build_parser().parse_args([
        "canonicalize",
        "--candidate-dir",
        str(candidate_dir),
        "--frozen-canonical-root",
        str(frozen_canonical),
        "--frozen-assets-root",
        str(frozen_assets),
        "--plan-only",
    ])
    assert parsed.frozen_canonical_root == frozen_canonical
    assert parsed.frozen_assets_root == frozen_assets


def test_existing_fine_grained_scripts_are_mapped_with_logs_and_remain_importable(tmp_path):
    pipeline = _pipeline()
    definition = pipeline.load_pipeline_definition()
    modules_by_stage = {
        name: {subtask.module for subtask in stage.subtasks}
        for name, stage in definition.stages.items()
    }

    assert "bgpkb.ingestion.source_ingest" in modules_by_stage["source-ingest"]
    assert "bgpkb.ingestion.canonicalize_candidate" in modules_by_stage["canonicalize"]
    assert importlib.util.find_spec("bgpkb.ingestion.parse_documents") is not None
    assert "bgpkb.ingestion.semantic_build_candidate" in modules_by_stage["semantic-build"]
    assert importlib.util.find_spec("bgpkb.ingestion.semantic_build_dry_run") is not None
    assert "bgpkb.publishing.candidate_publish_index" in modules_by_stage["publish-index"]
    assert "bgpkb.publishing.build_published_knowledge_base" not in modules_by_stage["publish-index"]
    assert "bgpkb.indexing.build_rag_indexes" not in modules_by_stage["publish-index"]
    assert "bgpkb.indexing.build_bge_m3_index" in modules_by_stage["publish-index"]
    assert "bgpkb.indexing.build_fast_vector_index" in modules_by_stage["publish-index"]
    assert "bgpkb.pipeline.run_server_rag_performance_gate" in modules_by_stage["verify-release"]
    assert "bgpkb.pipeline.build_release_gate_evidence" in modules_by_stage["verify-release"]
    assert "bgpkb.pipeline.verify_candidate_release" in modules_by_stage["verify-release"]
    assert "bgpkb.workflows.check_release_readiness" not in modules_by_stage["verify-release"]
    assert importlib.util.find_spec("bgpkb.workflows.check_release_readiness") is not None
    assert importlib.util.find_spec("bgpkb.pipeline.run_pipeline") is not None
    assert importlib.util.find_spec("bgpkb.pipeline.build_fast_vector_index") is not None

    candidate_dir = tmp_path / "candidate"
    calls: list[tuple[str, str]] = []
    _run(candidate_dir, target_stage="source-ingest", calls=calls)
    manifest = json.loads(
        pipeline.stage_manifest_path(candidate_dir, "source-ingest").read_text(encoding="utf-8")
    )
    for subtask in manifest["subtasks"]:
        assert subtask["duration_ms"] >= 0
        assert (candidate_dir / subtask["stdout_log"]).is_file()
        assert (candidate_dir / subtask["stderr_log"]).is_file()
        assert "diagnostics" in subtask


def test_governance_bundle_includes_v3_states_and_migration_audit():
    from bgpkb.publishing import build_sqlite_knowledge_base

    assert "evidence_governance_states_v1" in build_sqlite_knowledge_base.GOVERNANCE_DATASET_FILES
    assert "evidence_governance_migration_v1" in build_sqlite_knowledge_base.GOVERNANCE_DATASET_FILES


def test_publish_index_checkpoint_binds_transitive_build_and_closure_code():
    pipeline = _pipeline()
    definition = pipeline.load_pipeline_definition()
    dependencies = {
        dependency
        for subtask in definition.stages["publish-index"].subtasks
        for dependency in subtask.code_dependencies
    }

    assert {
        "bgpkb.indexing.retrieval_documents",
        "bgpkb.infrastructure.fast_vector_index",
        "bgpkb.infrastructure.retrieval_model_client",
        "bgpkb.infrastructure.serving_bundle",
        "bgpkb.publishing.publish_index_closure",
    } <= dependencies


def test_semantic_build_binds_frozen_migration_and_governance_inputs(tmp_path):
    pipeline = _pipeline()
    candidate_dir = tmp_path / "candidate"
    legacy_chunks = tmp_path / "legacy-chunks"
    legacy_chunks.mkdir()
    (legacy_chunks / "fixture.jsonl").write_text('{"chunk_id":"old"}\n', encoding="utf-8")
    source_catalog = tmp_path / "source_catalog.jsonl"
    source_catalog.write_text('{"source_id":"fixture"}\n', encoding="utf-8")
    entity_evidence = tmp_path / "entity_source_evidence.jsonl"
    entity_evidence.write_text("", encoding="utf-8")
    observed = []

    def inspect_semantic_inputs(context):
        observed.append(context)
        _write_required_outputs(context)
        if context.stage.name == "semantic-build":
            assert str(legacy_chunks.resolve()) in context.command
            assert str(source_catalog.resolve()) in context.command
            assert str(entity_evidence.resolve()) in context.command
        return {"returncode": 0, "stdout": "isolated", "stderr": ""}

    result = pipeline.run_pipeline(
        candidate_dir=candidate_dir,
        target_stage="semantic-build",
        task_executor=inspect_semantic_inputs,
        code_fingerprint="sha256:code-v1",
        protected_paths=(),
        frozen_legacy_chunks_root=legacy_chunks,
        frozen_source_catalog_path=source_catalog,
        frozen_entity_evidence_path=entity_evidence,
    )

    assert result["status"] == "complete"
    checkpoint = json.loads(
        pipeline.checkpoint_path(candidate_dir, "semantic-build").read_text(encoding="utf-8")
    )
    external = checkpoint["fingerprint_components"]["inputs"]["external"]
    assert set(external) >= {
        "frozen_legacy_chunks_root",
        "frozen_source_catalog_path",
        "frozen_entity_evidence_path",
    }
    assert all(value.startswith("sha256:") for value in external.values())


def test_semantic_build_code_fingerprint_declares_transitive_modules_and_versioned_configs():
    pipeline = _pipeline()
    semantic = pipeline.load_pipeline_definition().stages["semantic-build"].subtasks[0]

    assert set(semantic.code_dependencies) >= {
        "bgpkb.domain.evidence_governance",
        "bgpkb.indexing.retrieval_documents",
        "bgpkb.ingestion.canonical_contract",
        "bgpkb.ingestion.semantic_chunk_quality",
        "bgpkb.ingestion.semantic_chunking_v3",
        "bgpkb.workflows.replay_governance_migration",
    }
    assert set(semantic.fingerprint_files) >= {
        "metadata/config/retrieval_eligibility_policy_v1.yaml",
        "metadata/config/retrieval_text_v1.yaml",
        "metadata/config/semantic_chunking_v3.yaml",
        "metadata/schemas/evidence_governance_state_v1.schema.json",
        "metadata/schemas/retrieval_document_v1.schema.json",
        "metadata/schemas/semantic_chunk_v3.schema.json",
    }


@pytest.mark.parametrize(
    ("changed_inputs", "changed_config", "changed_code", "expected_first_stage"),
    [
        ({"canonicalize": {"snapshot_manifest": "sha256:snapshot-v2"}}, {}, "sha256:code-v1", "canonicalize"),
        ({}, {"semantic-build": "sha256:semantic-config-v2"}, "sha256:code-v1", "semantic-build"),
        ({}, {}, "sha256:code-v2", "source-ingest"),
    ],
)
def test_fingerprint_changes_invalidate_from_first_affected_stage(
    tmp_path,
    changed_inputs,
    changed_config,
    changed_code,
    expected_first_stage,
):
    pipeline = _pipeline()
    candidate_dir = tmp_path / "candidate"
    initial_calls: list[tuple[str, str]] = []
    initial_inputs = {"canonicalize": {"snapshot_manifest": "sha256:snapshot-v1"}}
    initial_configs = {"semantic-build": "sha256:semantic-config-v1"}
    _run(
        candidate_dir,
        calls=initial_calls,
        external_input_fingerprints=initial_inputs,
        stage_config_fingerprints=initial_configs,
    )

    rerun_calls: list[tuple[str, str]] = []
    inputs = changed_inputs or initial_inputs
    configs = changed_config or initial_configs
    result = _run(
        candidate_dir,
        calls=rerun_calls,
        external_input_fingerprints=inputs,
        stage_config_fingerprints=configs,
        code_fingerprint=changed_code,
    )

    first_index = EXPECTED_STAGES.index(expected_first_stage)
    assert result["executed_stages"] == list(EXPECTED_STAGES[first_index:])
    assert result["reused_stages"] == list(EXPECTED_STAGES[:first_index])
    assert [stage for stage, _ in rerun_calls][0] == expected_first_stage


def test_matching_checkpoints_are_reused_and_first_missing_stage_resumes(tmp_path):
    pipeline = _pipeline()
    candidate_dir = tmp_path / "candidate"
    first_calls: list[tuple[str, str]] = []
    first = _run(candidate_dir, calls=first_calls)
    assert first["status"] == "complete"

    second_calls: list[tuple[str, str]] = []
    second = _run(candidate_dir, calls=second_calls)
    assert second["executed_stages"] == []
    assert second["reused_stages"] == list(EXPECTED_STAGES)
    assert second_calls == []

    pipeline.checkpoint_path(candidate_dir, "semantic-build").unlink()
    resumed_calls: list[tuple[str, str]] = []
    resumed = _run(candidate_dir, calls=resumed_calls)
    assert resumed["reused_stages"] == ["source-ingest", "canonicalize"]
    assert resumed["executed_stages"] == ["semantic-build", "publish-index", "verify-release"]

    checkpoint = json.loads(
        pipeline.checkpoint_path(candidate_dir, "semantic-build").read_text(encoding="utf-8")
    )
    assert checkpoint["schema_version"] == "pipeline_stage_checkpoint_v1"
    assert set(checkpoint["fingerprint_components"]) == {
        "inputs",
        "config",
        "code",
        "upstream_manifests",
    }
    assert checkpoint["output_manifest_hash"].startswith("sha256:")
