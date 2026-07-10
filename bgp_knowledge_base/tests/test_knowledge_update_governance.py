import json
import runpy
import sys

from bgpkb import paths

import yaml


DEPENDENCIES = paths.CONFIG_DIR / "pipeline_dependencies.yaml"
LIFECYCLE_ACTIONS = paths.DATASETS_DIR / "lifecycle_action_queue.jsonl"
RELEASE_NOTES = paths.PUBLISHED_DIR / "release_notes.md"
INCREMENTAL_PLAN = paths.DATASETS_DIR / "incremental_run_plan.json"


def _run_script(script_name, *args):
    script = paths.PIPELINE_DIR / script_name
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(script), *args]
        runpy.run_path(str(script), run_name="__main__")
    finally:
        sys.argv = old_argv


def test_pipeline_dependency_config_declares_safe_incremental_boundaries():
    data = yaml.safe_load(DEPENDENCIES.read_text(encoding="utf-8"))
    steps = {step["id"]: step for step in data["steps"]}

    assert data["version"] == "knowledge_update_v1"
    assert data["default_mode"] == "plan_only"
    assert data["safety"]["never_auto_apply_human_review"] is True
    assert data["safety"]["never_download_sources_by_default"] is True
    assert data["safety"]["full_pipeline_remains_release_gate"] is True

    for required in {
        "parse_documents",
        "build_chunks",
        "build_published_knowledge_base",
        "build_bge_m3_index",
        "build_sqlite_knowledge_base",
        "build_lifecycle_report",
        "build_release_notes",
        "quality_check",
    }:
        assert required in steps

    for step in steps.values():
        assert step["command"].startswith("python3 -m bgpkb.pipeline.")
        assert isinstance(step["inputs"], list) and step["inputs"]
        assert isinstance(step["outputs"], list) and step["outputs"]
        assert step["safety"]["network"] == "disabled"
        assert step["safety"]["llm"] == "disabled"
        assert step["safety"]["writes_main_knowledge"] is False


def test_incremental_planner_recommends_transitive_downstream_steps():
    from bgpkb.pipeline import plan_incremental_run

    config = plan_incremental_run.load_config()
    plan = plan_incremental_run.build_plan(
        ["data/corpus/chunks_v2/standard_chunks.jsonl"],
        config=config,
    )
    step_ids = [step["id"] for step in plan["steps"]]

    assert step_ids[0] == "build_published_knowledge_base"
    assert "build_bge_m3_index" in step_ids
    assert "build_sqlite_knowledge_base" in step_ids
    assert "build_release_notes" in step_ids
    assert "quality_check" in step_ids
    assert plan["execution_mode"] == "plan_only"
    assert plan["requires_full_pipeline_gate"] is True


def test_incremental_planner_cli_writes_machine_and_human_outputs():
    _run_script(
        "plan_incremental_run.py",
        "--changed",
        "metadata/config/lifecycle_policy.yaml",
        "--write",
    )

    payload = json.loads(INCREMENTAL_PLAN.read_text(encoding="utf-8"))
    assert payload["changed_paths"] == ["metadata/config/lifecycle_policy.yaml"]
    assert any(step["id"] == "build_lifecycle_report" for step in payload["steps"])
    assert any(step["id"] == "build_release_notes" for step in payload["steps"])

    report = paths.report_path("incremental_run_plan_report").read_text(encoding="utf-8")
    assert "# 增量重跑计划" in report
    assert "只生成计划，不直接执行" in report


def test_lifecycle_report_generates_update_action_queue():
    _run_script("build_lifecycle_report.py")

    rows = [
        json.loads(line)
        for line in LIFECYCLE_ACTIONS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows
    assert all(row["generated_by"] == "src/bgpkb/pipeline/build_lifecycle_report.py" for row in rows)
    assert {"action_id", "entity_id", "action_type", "suggested_action"} <= rows[0].keys()
    assert any(row["action_type"] in {"lifecycle_review", "expired_validity_review"} for row in rows)


def test_release_notes_and_readiness_gate_are_registered_and_generated():
    policy = paths.report_policy()
    assert policy["release_notes"]["path"] == "data/published/release_notes.md"
    assert policy["release_readiness_report"]["path"] == "data/reports/gates/release_readiness_report.md"
    assert policy["incremental_run_plan_report"]["path"] == "data/generated/reports/publishing/incremental_run_plan_report.md"

    _run_script("build_release_notes.py")
    notes = RELEASE_NOTES.read_text(encoding="utf-8")
    assert "# 发布说明" in notes
    assert "## 实体变化" in notes
    assert "## 来源变化" in notes
    assert "## Chunk 变化" in notes
    assert "## 质量状态" in notes

    _run_script("check_release_readiness.py")
    report = paths.report_path("release_readiness_report").read_text(encoding="utf-8")
    assert "# 发布就绪检查报告" in report
    assert "非联网、非 LLM、非主知识写入" in report
