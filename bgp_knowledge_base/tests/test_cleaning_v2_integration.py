import importlib
import json

import yaml

from bgpkb import paths
from bgpkb.pipeline import build_cleaning_v2_release_gate


def test_release_gate_combines_migration_and_human_acceptance(tmp_path):
    migration = tmp_path / "migration.jsonl"
    migration.write_text(
        "".join(
            json.dumps(
                {
                    "doc_id": f"doc-{index}",
                    "state": "approved",
                    "gate_passed": True,
                    "blocking_issues": [],
                }
            )
            + "\n"
            for index in range(2)
        ),
        encoding="utf-8",
    )
    acceptance = tmp_path / "acceptance.json"
    acceptance.write_text(
        json.dumps(
            {
                "passed": True,
                "metrics": {
                    "heading_hierarchy_f1": 0.98,
                    "reading_order_accuracy": 1.0,
                    "table_structure_accuracy": 1.0,
                    "ocr_character_error_rate": 0.0,
                },
            }
        ),
        encoding="utf-8",
    )

    result = build_cleaning_v2_release_gate.build_gate(
        migration_path=migration,
        acceptance_path=acceptance,
        output_path=tmp_path / "gate.json",
        expected_document_count=2,
    )

    assert result["passed"] is True
    assert result["blocking_issues"] == []
    assert result["details"]["migration_gate_passed"] == 2


def test_project_integrations_register_cleaning_v2_outputs_and_pipeline_steps():
    manifest = importlib.import_module("bgpkb.pipeline.build_artifact_manifest")
    pipeline = importlib.import_module("bgpkb.pipeline.run_pipeline")
    quality = importlib.import_module("bgpkb.pipeline.quality_check")
    policy = yaml.safe_load(paths.REPORT_POLICY_PATH.read_text(encoding="utf-8"))["reports"]
    stage_gates = yaml.safe_load(
        (paths.CONFIG_DIR / "stage_acceptance_gates.yaml").read_text(encoding="utf-8")
    )["stages"]

    assert manifest.producer_for("data/derived/datasets/cleaning_v2_migration_diff.jsonl") == (
        "src/bgpkb/pipeline/build_cleaning_v2_migration.py"
    )
    assert manifest.producer_for("data/review_inputs/cleaning_v2_migration_decisions.jsonl") == (
        "src/bgpkb/pipeline/resolve_cleaning_v2_migration.py"
    )
    assert policy["cleaning_v2_migration_report"]["path"].endswith(
        "cleaning_v2_migration_report.md"
    )
    scripts = [script for _, script in pipeline.STEPS]
    assert scripts.index("resolve_cleaning_v2_migration.py") < scripts.index(
        "build_cleaning_v2_migration.py"
    ) < scripts.index("build_cleaning_v2_release_gate.py")
    assert "cleaning_v2_release_gate" in quality.load_schemas()
    assert any(stage["id"] == "docling_private_cleaning_v2" for stage in stage_gates)

    valid_gate = {
        "schema_version": "cleaning_v2_release_gate_v1",
        "passed": True,
        "blocking_issues": [],
        "details": {
            "migration_total": 54,
            "migration_gate_passed": 54,
            "quarantined_count": 0,
            "human_acceptance_passed": True,
        },
    }
    assert quality.validate_cleaning_v2_release_gate(
        valid_gate, quality.load_schemas()["cleaning_v2_release_gate"]
    ) == []
