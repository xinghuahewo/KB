import json
import runpy
import sys
from pathlib import Path

from bgpkb import paths

import yaml


ROOT = paths.PROJECT_ROOT
DOC = paths.DOCS_DIR / "governance" / "semantic_quality_v1.md"
CONFIG = paths.CONFIG_DIR / "semantic_quality_rules.yaml"
REPORT = paths.report_path("semantic_quality_report")
FINDINGS = paths.DATASETS_DIR / "semantic_quality_findings.jsonl"
SCRIPT = paths.PIPELINE_DIR / "build_semantic_quality_report.py"
PIPELINE = paths.PIPELINE_DIR / "run_pipeline.py"
ACCEPTANCE = paths.CONFIG_DIR / "stage_acceptance_gates.yaml"
DATA_MANAGEMENT = paths.CONFIG_DIR / "data_management_capabilities.yaml"

ALLOWED_SEVERITIES = {"blocker", "warning", "info"}
REQUIRED_RULES = {
    "anomaly_required_evidence_template_coverage",
    "evidence_template_field_mapping",
    "relationship_type_constraint",
    "case_anomaly_type_mapping",
    "datasource_field_lineage",
    "candidate_excluded_from_trusted_rag",
    "expired_validity_requires_action",
}
REQUIRED_FINDING_FIELDS = {
    "finding_id",
    "rule_id",
    "severity",
    "subject_type",
    "subject_id",
    "field",
    "message",
    "suggested_action",
    "lifecycle_status",
    "generated_by",
}


def run_semantic_quality_script():
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(SCRIPT)]
        runpy.run_path(str(SCRIPT), run_name="__main__")
    finally:
        sys.argv = old_argv


def test_semantic_quality_config_declares_required_rules_and_outputs():
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))

    assert data["version"] == "semantic_quality_v1"
    assert set(data["allowed_severities"]) == ALLOWED_SEVERITIES
    assert data["generated_policy"]["findings_path"] == "data/derived/datasets/semantic_quality_findings.jsonl"
    assert data["generated_policy"]["report_path"] == "data/generated/reports/knowledge/semantic_quality_report.md"
    assert REQUIRED_RULES <= {rule["id"] for rule in data["rules"]}


def test_semantic_quality_document_records_scope_and_non_goals():
    text = DOC.read_text(encoding="utf-8")

    assert "# 语义质量治理 v1" in text
    assert "结构质量可检查" in text
    assert "语义一致性可扫描" in text
    assert "不自动修改实体、关系、chunk、来源或发布包" in text
    assert "blocker、warning、info" in text
    assert "高可信默认集合" in text


def test_semantic_quality_script_generates_findings_and_report():
    run_semantic_quality_script()

    rows = [json.loads(line) for line in FINDINGS.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows
    assert all(REQUIRED_FINDING_FIELDS <= set(row) for row in rows)
    assert all(row["severity"] in ALLOWED_SEVERITIES for row in rows)
    assert any(row["rule_id"] == "candidate_excluded_from_trusted_rag" for row in rows)
    assert any(row["subject_id"] == "case_celerbridge_bgp_hijack" for row in rows)

    report = REPORT.read_text(encoding="utf-8")
    assert "# 语义质量治理报告" in report
    assert "## 语义问题总览" in report
    assert "## 等级统计" in report
    assert "## RAG 默认可信集合影响" in report
    assert "## 人工复核建议" in report
    assert "## 后续 RAG 可依赖集合" in report


def test_relationship_type_constraint_detects_invalid_synthetic_relationship():
    namespace = runpy.run_path(str(SCRIPT))
    check_relationship_type_constraints = namespace["check_relationship_type_constraints"]
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    entity_index = {
        "concept_as_path": {"entity_type": "BGPConcept", "id": "concept_as_path"},
        "field_prefix": {"entity_type": "DataField", "id": "field_prefix"},
    }
    lifecycle = {
        "concept_as_path": {"lifecycle_status": "approved"},
        "field_prefix": {"lifecycle_status": "approved"},
    }
    bad_relationships = [
        {
            "src_id": "concept_as_path",
            "src_type": "BGPConcept",
            "relation": "requires_evidence",
            "dst_id": "field_prefix",
            "dst_type": "DataField",
        }
    ]

    findings = check_relationship_type_constraints(bad_relationships, entity_index, lifecycle, config)

    assert findings
    assert findings[0]["rule_id"] == "relationship_type_constraint"
    assert findings[0]["severity"] == "blocker"


def test_semantic_quality_is_registered_in_pipeline_data_management_and_acceptance():
    pipeline_text = PIPELINE.read_text(encoding="utf-8")
    assert "构建语义质量治理报告" in pipeline_text
    assert "build_semantic_quality_report.py" in pipeline_text

    data_management = yaml.safe_load(DATA_MANAGEMENT.read_text(encoding="utf-8"))
    asset_ids = {group["id"] for group in data_management["asset_groups"]}
    capability_ids = {group["id"] for group in data_management["capability_groups"]}
    lifecycle = next(group for group in data_management["capability_groups"] if group["id"] == "lifecycle")
    assert "semantic_quality" in asset_ids
    assert "semantic_quality_governance" in capability_ids
    assert lifecycle["status"] == "achieved"

    data = yaml.safe_load(ACCEPTANCE.read_text(encoding="utf-8"))
    stages = {stage["id"]: stage for stage in data["stages"]}
    stage = stages["phase_3_semantic_quality_v1"]
    assert stage["name"] == "语义质量治理 v1"
    assert "docs/governance/semantic_quality_v1.md" in stage["required_files"]
    assert "data/generated/reports/knowledge/semantic_quality_report.md" in stage["required_files"]
    assert "data/derived/datasets/semantic_quality_findings.jsonl" in stage["required_files"]
    assert len(stage["effect_review"]["new_capabilities"]) >= 3
    assert len(stage["effect_review"]["user_can_now"]) >= 3
    assert len(stage["effect_review"]["downstream_dependencies"]) >= 3
