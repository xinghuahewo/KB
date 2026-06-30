import importlib

import yaml

from bgpkb import paths


def test_report_policy_and_artifact_producers_register_phase_a_outputs():
    policy = yaml.safe_load(paths.REPORT_POLICY_PATH.read_text(encoding="utf-8"))["reports"]
    manifest = importlib.import_module("bgpkb.pipeline.build_artifact_manifest")

    assert policy["corpus_profile_report"] == {
        "path": "data/generated/reports/corpus/corpus_profile_report.md",
        "category": "corpus",
        "retention": "generated",
        "human_entry": False,
    }
    assert manifest.producer_for("data/derived/datasets/corpus_profile.jsonl") == (
        "src/bgpkb/pipeline/profile_cleaned_corpus.py"
    )
    assert manifest.producer_for("data/derived/datasets/corpus_ocr_assessments.jsonl") == (
        "src/bgpkb/pipeline/assess_corpus_ocr_quality.py"
    )
    assert manifest.producer_for("data/generated/reports/corpus/corpus_profile_report.md") == (
        "src/bgpkb/pipeline/profile_cleaned_corpus.py"
    )


def test_quality_check_loads_phase_a_schemas_and_blocks_only_deterministic_issues():
    quality = importlib.import_module("bgpkb.pipeline.quality_check")
    schemas = quality.load_schemas()

    assert "corpus_profile" in schemas
    assert "corpus_ocr_assessment" in schemas
    assert quality.corpus_profile_blocking_issues([
        {"doc_id": "safe", "blocking_issues": [], "warnings": ["long_document"]},
        {"doc_id": "blocked", "blocking_issues": ["replacement_character"], "warnings": []},
    ]) == ["blocked -> replacement_character"]


def test_deterministic_pipeline_runs_profile_then_disabled_ocr_after_chunks():
    pipeline = importlib.import_module("bgpkb.pipeline.run_pipeline")
    scripts = [script for _, script in pipeline.STEPS]

    chunk_index = scripts.index("build_chunks.py")
    assert scripts[chunk_index + 1:chunk_index + 3] == [
        "profile_cleaned_corpus.py",
        "assess_corpus_ocr_quality.py",
    ]
    assert "corpus_profile_report" in pipeline.GENERATED_REPORT_IDS_TO_CLEAN


def test_phase_a_gate_declares_files_commands_reports_and_effects():
    config = yaml.safe_load(
        (paths.CONFIG_DIR / "stage_acceptance_gates.yaml").read_text(encoding="utf-8")
    )
    stages = {stage["id"]: stage for stage in config["stages"]}
    stage = stages["phase_a_corpus_profiling_v1"]

    assert stage["name"] == "语料质量画像 v1"
    assert "metadata/config/corpus_profiling.yaml" in stage["required_files"]
    assert "data/derived/datasets/corpus_profile.jsonl" in stage["required_files"]
    assert "data/derived/datasets/corpus_ocr_assessments.jsonl" in stage["required_files"]
    assert "data/generated/reports/corpus/corpus_profile_report.md" in stage["required_files"]
    command_ids = {command["id"] for command in stage["commands"]}
    assert {"corpus_profile", "corpus_ocr_mock", "corpus_profile_tests"} <= command_ids
    assert len(stage["effect_review"]["new_capabilities"]) >= 3
    assert len(stage["effect_review"]["user_can_now"]) >= 3
    assert len(stage["effect_review"]["downstream_dependencies"]) >= 3
