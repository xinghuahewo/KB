import hashlib
import json
from pathlib import Path


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "rag_evidence_pipeline_v2"


def test_migration_fixture_manifest_covers_required_document_and_attack_profiles():
    manifest = json.loads((FIXTURE_ROOT / "manifest.json").read_text(encoding="utf-8"))
    fixtures = manifest["fixtures"]

    assert {item["profile"] for item in fixtures} == {
        "rfc",
        "html",
        "pdf_table",
        "openapi_yaml",
        "duplicate_template",
        "prompt_injection",
    }
    for item in fixtures:
        path = FIXTURE_ROOT / item["path"]
        content = path.read_bytes()
        assert content
        assert hashlib.sha256(content).hexdigest() == item["sha256"]


def test_migration_fixtures_keep_expected_semantic_boundaries():
    rfc = (FIXTURE_ROOT / "rfc_excerpt.txt").read_text(encoding="utf-8")
    html = (FIXTURE_ROOT / "html_page.html").read_text(encoding="utf-8")
    pdf = json.loads((FIXTURE_ROOT / "pdf_table_canonical_v2.json").read_text(encoding="utf-8"))
    openapi = (FIXTURE_ROOT / "peeringdb_openapi.yaml").read_text(encoding="utf-8")
    duplicate = json.loads((FIXTURE_ROOT / "duplicate_templates.json").read_text(encoding="utf-8"))
    injection = (FIXTURE_ROOT / "prompt_injection.txt").read_text(encoding="utf-8")

    assert "2.  Route Leak Definition" in rfc
    assert "<nav" in html and "<main" in html and "<footer" in html
    assert any(block["block_type"] == "table" for block in pdf["blocks"])
    assert "/net/{id}" in openapi and "operationId: network_retrieve" in openapi
    assert len(duplicate["same_source_exact"]) == 2
    assert len(duplicate["cross_source_independent"]) == 2
    assert "ignore previous instructions" in injection.casefold()
