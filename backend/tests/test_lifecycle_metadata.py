import json
import runpy
import sys
from pathlib import Path

from bgpkb import paths

import yaml


ROOT = paths.PROJECT_ROOT
DOC = paths.resolve_logical_path("docs/data-artifacts.md")
CONFIG = paths.CONFIG_DIR / "lifecycle_policy.yaml"
REPORT = paths.report_path("lifecycle_report")
INVENTORY = paths.DATASETS_DIR / "lifecycle_inventory.jsonl"
SCRIPT = paths.PIPELINE_DIR / "build_lifecycle_report.py"
PIPELINE = paths.PIPELINE_DIR / "run_pipeline.py"
ACCEPTANCE = paths.CONFIG_DIR / "stage_acceptance_gates.yaml"

EXPECTED_STATUSES = ["draft", "candidate", "reviewed", "approved", "deprecated", "archived"]


def run_lifecycle_script():
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(SCRIPT)]
        runpy.run_path(str(SCRIPT), run_name="__main__")
    finally:
        sys.argv = old_argv


def test_lifecycle_policy_defines_state_model_and_rules():
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))

    assert data["version"] == "lifecycle_metadata_v1"
    assert data["generated_policy"]["report_path"] == "data/generated/reports/knowledge/lifecycle_report.md"
    assert data["generated_policy"]["inventory_path"] == "data/derived/datasets/lifecycle_inventory.jsonl"
    assert [state["id"] for state in data["states"]] == EXPECTED_STATUSES
    assert {"review_status", "source_refs", "review_packet", "evidence_index", "next_action"} <= set(
        data["metadata_fields"]
    )
    rule_ids = {rule["id"] for rule in data["quality_rules"]}
    assert {
        "lifecycle_status_required",
        "approved_requires_review_evidence",
        "deprecated_or_archived_reference_warning",
        "expired_validity_requires_action",
        "review_lifecycle_consistency",
    } <= rule_ids


def test_lifecycle_document_records_scope_statuses_and_non_goals():
    text = DOC.read_text(encoding="utf-8")

    assert "# 数据与制品" in text
    assert "运行制品" in text
    assert "BGPKB_DATA_DIR" in text
    assert "不可变 release" in text
    assert "## 发布与回滚" in text


def test_lifecycle_script_generates_inventory_and_report():
    run_lifecycle_script()

    rows = [json.loads(line) for line in INVENTORY.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows
    assert all(row["entity_id"] for row in rows)
    assert all(row["lifecycle_status"] in EXPECTED_STATUSES for row in rows)
    assert all("review_status" in row for row in rows)
    assert all("lifecycle_reason" in row for row in rows)
    assert any(row["entity_id"] == "anomaly_route_leak" for row in rows)
    approved = [row for row in rows if row["lifecycle_status"] == "approved"]
    assert approved
    assert all(row["evidence_record_count"] >= 1 for row in approved)

    report = REPORT.read_text(encoding="utf-8")
    assert "# 生命周期治理报告" in report
    assert "## 生命周期状态统计" in report
    assert "## 元数据覆盖" in report
    assert "## 质量规则结果" in report
    assert "## 下一步行动" in report


def test_lifecycle_step_is_registered_in_pipeline_and_stage_acceptance():
    pipeline_text = PIPELINE.read_text(encoding="utf-8")
    assert "构建生命周期治理报告" in pipeline_text
    assert "build_lifecycle_report.py" in pipeline_text

    data = yaml.safe_load(ACCEPTANCE.read_text(encoding="utf-8"))
    stages = {stage["id"]: stage for stage in data["stages"]}
    stage = stages["phase_2_lifecycle_metadata_v1"]
    assert stage["name"] == "生命周期与元数据治理 v1"
    assert "docs/data-artifacts.md" in stage["required_files"]
    assert "data/generated/reports/knowledge/lifecycle_report.md" in stage["required_files"]
    assert "data/derived/datasets/lifecycle_inventory.jsonl" in stage["required_files"]
    assert len(stage["effect_review"]["new_capabilities"]) >= 3
    assert len(stage["effect_review"]["user_can_now"]) >= 3
    assert len(stage["effect_review"]["downstream_dependencies"]) >= 3
