import json
import subprocess
import sys
from pathlib import Path

from bgpkb import paths

import yaml


ROOT = paths.PROJECT_ROOT
CONFIG = paths.CONFIG_DIR / "stage_acceptance_gates.yaml"
REPORT = paths.report_path("stage_acceptance_report")
RESULTS = paths.DATASETS_DIR / "stage_acceptance_results.jsonl"
SCRIPT = paths.PIPELINE_DIR / "run_stage_acceptance.py"


def load_config():
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def test_stage_acceptance_config_registers_phase_1_effect_checks():
    data = load_config()
    stages = {stage["id"]: stage for stage in data["stages"]}
    stage = stages["phase_1_data_management_v1"]

    assert stage["name"] == "数据管理体系 v1"
    assert stage["acceptance_mode"] == "deterministic_with_effect_review"
    assert "docs/governance/data_management_v1.md" in stage["required_files"]
    assert "data/generated/reports/knowledge/data_management_report.md" in stage["required_files"]
    assert len(stage["effect_review"]["new_capabilities"]) >= 3
    assert len(stage["effect_review"]["user_can_now"]) >= 3
    assert len(stage["effect_review"]["downstream_dependencies"]) >= 3


def test_stage_acceptance_config_registers_phase_3_5_semantic_identity():
    data = load_config()
    stages = {stage["id"]: stage for stage in data["stages"]}
    stage = stages["phase_3_5_semantic_identity_v1"]

    assert stage["name"] == "语义标识前置 v1"
    assert "metadata/config/semantic_identity.yaml" in stage["required_files"]
    assert "data/published/jsonld_context.json" in stage["required_files"]
    assert "data/published/semantic_id_map.jsonl" in stage["required_files"]
    assert any(command["id"] == "semantic_identity_report" for command in stage["commands"])
    assert len(stage["effect_review"]["new_capabilities"]) >= 3
    assert len(stage["effect_review"]["downstream_dependencies"]) >= 3


def test_stage_acceptance_config_registers_phase_4_rag_framework():
    data = load_config()
    stages = {stage["id"]: stage for stage in data["stages"]}
    stage = stages["phase_4_rag_framework_v1"]

    assert stage["name"] == "RAG 就绪框架 v1"
    assert "metadata/config/rag_retrieval.yaml" in stage["required_files"]
    assert "metadata/config/llm_candidate_enrichment.yaml" in stage["required_files"]
    assert "data/generated/reports/rag/rag_readiness_report.md" in stage["required_files"]
    assert any(command["id"] == "rag_framework_report" for command in stage["commands"])
    assert len(stage["effect_review"]["new_capabilities"]) >= 3
    assert len(stage["effect_review"]["downstream_dependencies"]) >= 3


def test_stage_acceptance_config_registers_phase_4_3_rag_answer_eval():
    data = load_config()
    stages = {stage["id"]: stage for stage in data["stages"]}
    stage = stages["phase_4_3_rag_answer_eval_v1"]

    assert stage["name"] == "RAG 答案质量评测 v1"
    assert "data/derived/datasets/rag_answer_eval_questions.jsonl" in stage["required_files"]
    assert "src/bgpkb/pipeline/run_rag_answer_eval.py" in stage["required_files"]
    assert "data/generated/reports/rag/rag_answer_eval_report.md" in stage["required_files"]
    assert any(command["id"] == "rag_answer_eval" for command in stage["commands"])
    assert len(stage["effect_review"]["new_capabilities"]) >= 3
    assert len(stage["effect_review"]["downstream_dependencies"]) >= 3


def test_stage_acceptance_config_registers_phase_4_4_deepseek_eval_analysis():
    data = load_config()
    stages = {stage["id"]: stage for stage in data["stages"]}
    stage = stages["phase_4_4_deepseek_eval_analysis_v1"]

    assert stage["name"] == "DeepSeek 批量评测与失败分析 v1"
    assert "src/bgpkb/pipeline/run_deepseek_rag_answer_eval.py" in stage["required_files"]
    assert "src/bgpkb/pipeline/build_rag_answer_failure_analysis.py" in stage["required_files"]
    assert "data/generated/reports/rag/rag_answer_failure_analysis_report.md" in stage["required_files"]
    assert any(command["id"] == "rag_answer_failure_analysis" for command in stage["commands"])
    assert len(stage["effect_review"]["new_capabilities"]) >= 3
    assert len(stage["effect_review"]["downstream_dependencies"]) >= 3


def test_stage_acceptance_agent_outputs_effect_oriented_report():
    result = subprocess.run(
        [sys.executable, "-m", "bgpkb.pipeline.run_stage_acceptance", "--stage", "phase_1_data_management_v1"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    report = REPORT.read_text(encoding="utf-8")
    assert "# 阶段验收报告" in report
    assert "## 效果验收" in report
    assert "### 新增能力" in report
    assert "### 使用者现在能做什么" in report
    assert "### 后续阶段能依赖什么" in report
    assert "## 风险与剩余人工事项" in report
    assert "结论：pass" in report

    rows = [json.loads(line) for line in RESULTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    phase_1 = [row for row in rows if row["stage_id"] == "phase_1_data_management_v1"]
    assert phase_1
    assert phase_1[-1]["decision"] == "pass"
    assert phase_1[-1]["effect_summary"]["new_capabilities_count"] >= 3
