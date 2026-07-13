import json
import runpy
import sys
from pathlib import Path

from bgpkb import paths

import yaml


ROOT = paths.PROJECT_ROOT
CONFIG = paths.CONFIG_DIR / "semantic_identity.yaml"
CONTEXT = paths.PUBLISHED_DIR / "jsonld_context.json"
ID_MAP = paths.PUBLISHED_DIR / "semantic_id_map.jsonl"
REPORT = paths.report_path("semantic_identity_report")
SCRIPT = paths.PIPELINE_DIR / "build_semantic_identity.py"


def load_config():
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_semantic_identity_config_defines_namespace_uri_rules_and_field_mapping():
    data = load_config()

    assert data["version"] == "semantic_identity_v1"
    assert data["namespace"]["prefix"] == "bgpkb"
    assert data["namespace"]["base_uri"].startswith("https://")
    assert set(data["uri_patterns"]) >= {"entity", "source", "chunk", "relationship", "evidence"}
    assert data["field_mappings"]["id"]["jsonld"] == "@id"
    assert data["field_mappings"]["name"]["skos"] == "skos:prefLabel"
    assert data["field_mappings"]["source_refs"]["prov"] == "prov:wasDerivedFrom"


def test_semantic_identity_script_generates_context_id_map_and_report():
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(SCRIPT)]
        runpy.run_path(str(SCRIPT), run_name="__main__")
    finally:
        sys.argv = old_argv

    context = json.loads(CONTEXT.read_text(encoding="utf-8"))
    ctx = context["@context"]
    assert ctx["bgpkb"].startswith("https://")
    assert ctx["skos"] == "http://www.w3.org/2004/02/skos/core#"
    assert ctx["prov"] == "http://www.w3.org/ns/prov#"
    assert ctx["source_refs"]["@id"] == "prov:wasDerivedFrom"

    records = load_jsonl(ID_MAP)
    assert records
    resource_types = {record["resource_type"] for record in records}
    assert {"entity", "source", "chunk"} <= resource_types
    assert all(record["uri"].startswith(ctx["bgpkb"].replace("/vocab#", "/resource/")) for record in records)
    assert len({record["uri"] for record in records}) == len(records)
    assert any(record["resource_type"] == "entity" and record["local_id"] == "anomaly_route_leak" for record in records)
    assert any(record["resource_type"] == "source" and record["local_id"] == "rfc4271" for record in records)

    report = REPORT.read_text(encoding="utf-8")
    assert "# 语义标识前置报告" in report
    assert "## 命名空间与 URI 规则" in report
    assert "## JSON-LD Context" in report
    assert "## 字段映射草案" in report
    assert "## 下游使用边界" in report
