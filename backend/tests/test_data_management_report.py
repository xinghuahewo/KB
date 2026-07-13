import runpy
import sys
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
CONFIG = paths.CONFIG_DIR / "data_management_capabilities.yaml"
REPORT = paths.report_path("data_management_report")
SCRIPT = paths.PIPELINE_DIR / "build_data_management_report.py"

ALLOWED_STATUSES = {"achieved", "partial", "planned", "not_started", "deferred"}
REQUIRED_ASSET_GROUPS = {
    "entities",
    "relationships",
    "sources",
    "chunks",
    "glossary",
    "evidence_templates",
    "cases",
    "human_review_workbook",
    "next_action_queue",
    "published_package",
    "service_api",
    "rag_retrieval_framework",
}
REQUIRED_CAPABILITY_GROUPS = {
    "data_asset_inventory",
    "data_model_standards",
    "metadata_lineage",
    "quality_governance",
    "lifecycle",
    "service_access",
    "standard_exports",
    "rag_retrieval",
}
REQUIRED_REPORT_HEADINGS = [
    "## 数据资产清单",
    "## 数据模型标准覆盖",
    "## 元数据与溯源覆盖",
    "## 质量治理能力",
    "## 生命周期现状",
    "## 服务化访问现状",
    "## 标准化出口现状",
]


def load_capabilities():
    import yaml

    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def test_data_management_capabilities_yaml_is_valid():
    data = load_capabilities()

    assert data["version"] == "data_management_v1"
    assert set(data["allowed_statuses"]) == ALLOWED_STATUSES
    assert data["generated_policy"]["report_path"] == "data/generated/reports/knowledge/data_management_report.md"


def test_asset_groups_have_required_fields_and_valid_statuses():
    data = load_capabilities()

    for group in data["asset_groups"]:
        assert group["id"]
        assert group["name"]
        assert group["status"] in ALLOWED_STATUSES
        assert group["description"]
        assert group["paths"]
        assert group["evidence"]


def test_core_asset_and_capability_groups_are_registered():
    data = load_capabilities()

    asset_ids = {group["id"] for group in data["asset_groups"]}
    capability_ids = {group["id"] for group in data["capability_groups"]}

    assert REQUIRED_ASSET_GROUPS <= asset_ids
    assert REQUIRED_CAPABILITY_GROUPS <= capability_ids


def test_rag_framework_is_registered_with_offline_boundaries():
    data = load_capabilities()
    assets = {group["id"]: group for group in data["asset_groups"]}
    capabilities = {group["id"]: group for group in data["capability_groups"]}

    rag_asset = assets["rag_retrieval_framework"]
    assert rag_asset["status"] == "achieved"
    assert "metadata/config/rag_retrieval.yaml" in rag_asset["paths"]
    assert "data/generated/reports/rag/rag_readiness_report.md" in rag_asset["evidence"]

    rag_capability = capabilities["rag_retrieval"]
    assert rag_capability["status"] == "achieved"
    assert any("不运行模型" in item or "mock" in item for item in rag_capability["next_steps"])


def test_data_management_report_script_generates_required_sections():
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(SCRIPT)]
        runpy.run_path(str(SCRIPT), run_name="__main__")
    finally:
        sys.argv = old_argv

    report = REPORT.read_text(encoding="utf-8")
    assert "# 数据管理能力报告" in report
    assert "## 状态统计" in report
    assert "## 缺口与下一步建议" in report
    for heading in REQUIRED_REPORT_HEADINGS:
        assert heading in report
