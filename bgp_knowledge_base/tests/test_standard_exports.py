import importlib
import importlib.util
import hashlib
import json
import os
import subprocess
import sys

import pytest
import yaml

from bgpkb import paths


MODULE = "bgpkb.pipeline.build_standard_exports"


def load_module():
    assert importlib.util.find_spec(MODULE) is not None, "阶段五标准出口生成器尚未实现"
    return importlib.import_module(MODULE)


def sample_config():
    return {
        "namespaces": {
            "bgpkb": "https://w3id.org/bgpkb/vocab#",
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "prov": "http://www.w3.org/ns/prov#",
        },
        "entity_type_mappings": {
            "BGPConcept": ["bgpkb:BGPConcept", "skos:Concept"],
        },
        "export_policy": {
            "include_review_statuses": ["approved", "pending"],
            "preserve_review_status": True,
        },
    }


def test_build_entity_jsonld_maps_skos_and_provenance():
    module = load_module()
    entity = {
        "entity_id": "concept_rpki",
        "entity_type": "BGPConcept",
        "name": "RPKI",
        "aliases": ["资源公钥基础设施"],
        "review_status": "approved",
        "source_refs": ["rfc6811"],
        "entity_payload": {"definition": "用于路由起源验证的资源证书体系。"},
    }

    result = module.build_entity_jsonld(
        entity,
        entity_uri="https://w3id.org/bgpkb/resource/entity/concept_rpki",
        source_uris={"rfc6811": "https://w3id.org/bgpkb/resource/source/rfc6811"},
        config=sample_config(),
    )

    assert result["@id"].endswith("/entity/concept_rpki")
    assert result["@type"] == ["bgpkb:BGPConcept", "skos:Concept"]
    assert result["skos:prefLabel"] == "RPKI"
    assert result["skos:altLabel"] == ["资源公钥基础设施"]
    assert result["skos:definition"] == "用于路由起源验证的资源证书体系。"
    assert result["prov:wasDerivedFrom"] == ["https://w3id.org/bgpkb/resource/source/rfc6811"]
    assert result["bgpkb:reviewStatus"] == "approved"


def test_build_source_jsonld_preserves_source_metadata():
    module = load_module()
    source = {
        "source_id": "rfc6811",
        "title": "RFC 6811",
        "url": "https://www.rfc-editor.org/rfc/rfc6811",
        "source_type": "standard",
        "review_status": "pending",
    }

    result = module.build_source_jsonld(
        source,
        source_uri="https://w3id.org/bgpkb/resource/source/rfc6811",
    )

    assert result == {
        "@id": "https://w3id.org/bgpkb/resource/source/rfc6811",
        "@type": ["prov:Entity", "schema:CreativeWork"],
        "dcterms:title": "RFC 6811",
        "dcterms:type": "standard",
        "schema:url": "https://www.rfc-editor.org/rfc/rfc6811",
        "bgpkb:reviewStatus": "pending",
    }


def test_build_provenance_records_links_entities_to_sources():
    module = load_module()
    entities = [{"entity_id": "concept_rpki", "source_refs": ["rfc6811", "missing_source"]}]

    records, unresolved = module.build_provenance_records(
        entities,
        entity_uris={"concept_rpki": "https://w3id.org/bgpkb/resource/entity/concept_rpki"},
        source_uris={"rfc6811": "https://w3id.org/bgpkb/resource/source/rfc6811"},
    )

    assert records == [{
        "record_id": "provenance_concept_rpki__rfc6811",
        "subject_uri": "https://w3id.org/bgpkb/resource/entity/concept_rpki",
        "predicate": "prov:wasDerivedFrom",
        "object_uri": "https://w3id.org/bgpkb/resource/source/rfc6811",
        "source_ref": "rfc6811",
        "generated_by": "src/bgpkb/pipeline/build_standard_exports.py",
    }]
    assert unresolved == [{"entity_id": "concept_rpki", "source_ref": "missing_source"}]


def test_turtle_literal_escapes_special_characters():
    module = load_module()

    assert module.turtle_literal('路由 "泄露"\\案例\n第二行') == '"路由 \\"泄露\\"\\\\案例\\n第二行"'


def test_serialize_turtle_orders_triples():
    module = load_module()
    triples = [
        ("https://example/b", "skos:prefLabel", ("literal", "B")),
        ("https://example/a", "rdf:type", ("curie", "skos:Concept")),
    ]

    output = module.serialize_turtle(triples, {"skos": "http://www.w3.org/2004/02/skos/core#"})

    assert output.index("<https://example/a>") < output.index("<https://example/b>")
    assert '@prefix skos: <http://www.w3.org/2004/02/skos/core#> .' in output
    assert '<https://example/a> rdf:type skos:Concept .' in output


def test_build_provenance_chain_covers_source_artifacts_chunks_and_entity():
    module = load_module()
    sources = [{"source_id": "rfc6811", "path": "data/sources/raw/standards/rfc6811.txt"}]
    evidence = [{
        "evidence_id": "concept_rpki__rfc6811",
        "entity_id": "concept_rpki",
        "source_id": "rfc6811",
        "parsed_path": "data/corpus/parsed/standards/rfc6811.json",
        "cleaned_path": "data/corpus/cleaned/standards/rfc6811.md",
        "chunk_sample_ids": ["rfc6811_s001_1_001"],
    }]
    identities = [
        {"resource_type": "source", "local_id": "rfc6811", "uri": "https://example/source/rfc6811"},
        {"resource_type": "chunk", "local_id": "rfc6811_s001_1_001", "uri": "https://example/chunk/1"},
        {"resource_type": "entity", "local_id": "concept_rpki", "uri": "https://example/entity/rpki"},
        {"resource_type": "evidence", "local_id": "concept_rpki__rfc6811", "uri": "https://example/evidence/1"},
    ]

    records, unresolved = module.build_provenance_chain_records(sources, evidence, identities)
    links = {(row["subject_uri"], row["object_uri"]) for row in records}
    raw_uri = module.artifact_uri("data/sources/raw/standards/rfc6811.txt")
    parsed_uri = module.artifact_uri("data/corpus/parsed/standards/rfc6811.json")
    cleaned_uri = module.artifact_uri("data/corpus/cleaned/standards/rfc6811.md")

    assert (raw_uri, "https://example/source/rfc6811") in links
    assert (parsed_uri, raw_uri) in links
    assert (cleaned_uri, parsed_uri) in links
    assert ("https://example/chunk/1", cleaned_uri) in links
    assert ("https://example/evidence/1", "https://example/chunk/1") in links
    assert ("https://example/entity/rpki", "https://example/evidence/1") in links
    assert any(
        row["subject_uri"] == "https://example/evidence/1"
        and row["predicate"] == "prov:wasGeneratedBy"
        and row["object_uri"] == module.GENERATION_ACTIVITY_URI
        for row in records
    )
    assert any(
        row["subject_uri"] == module.GENERATION_ACTIVITY_URI
        and row["predicate"] == "rdf:type"
        and row["object_uri"] == "http://www.w3.org/ns/prov#Activity"
        for row in records
    )
    assert all(row["generated_by"] == "src/bgpkb/pipeline/build_standard_exports.py" for row in records)
    assert all(set(row) == {
        "record_id", "subject_uri", "predicate", "object_uri", "source_ref", "generated_by"
    } for row in records)
    assert unresolved == []


def test_serialize_turtle_supports_all_v1_object_types_and_rejects_out_of_scope_values():
    module = load_module()
    output = module.serialize_turtle([
        ("urn:bgpkb:test", "prov:wasDerivedFrom", ("uri", "https://example/source")),
        ("urn:bgpkb:test", "rdf:type", ("curie", "skos:Concept")),
        ("urn:bgpkb:test", "skos:prefLabel", ("literal", "第一行\t第二行")),
    ], {
        "prov": "http://www.w3.org/ns/prov#",
        "skos": "http://www.w3.org/2004/02/skos/core#",
    })

    assert "<urn:bgpkb:test> prov:wasDerivedFrom <https://example/source> ." in output
    assert "<urn:bgpkb:test> rdf:type skos:Concept ." in output
    assert '"第一行\\t第二行"' in output
    with pytest.raises(ValueError, match="control character"):
        module.turtle_literal("非法\x00文本")
    with pytest.raises(ValueError, match="Unsupported Turtle object type"):
        module.serialize_turtle([("urn:test", "rdf:type", ("blank_node", "node1"))], {})
    with pytest.raises(ValueError, match="Invalid Turtle IRI"):
        module.serialize_turtle([("not an iri", "rdf:type", ("curie", "skos:Concept"))], {})
    with pytest.raises(ValueError, match="Invalid Turtle CURIE"):
        module.serialize_turtle([("urn:test", "not-a-curie", ("literal", "值"))], {})
    with pytest.raises(ValueError, match="Unknown Turtle CURIE prefix"):
        module.serialize_turtle([("urn:test", "rdf:type", ("curie", "unknown:Concept"))], {})


def test_report_includes_coverage_mapping_and_integrity_diagnostics():
    module = load_module()
    entities = [{
        "entity_id": "concept_rpki", "entity_type": "BGPConcept", "name": "RPKI",
        "review_status": "approved", "custom_field": "待映射", "entity_payload": {"definition": "定义"},
    }]
    sources = [{
        "source_id": "rfc6811", "title": "RFC 6811", "source_type": "standard",
        "review_status": "approved", "parsed_status": "error", "cleaned_status": "present",
    }]
    semantic = [
        {"resource_type": "entity", "local_id": "concept_rpki", "uri": "https://example/duplicate"},
        {"resource_type": "source", "local_id": "rfc6811", "uri": "https://example/duplicate"},
    ]
    relationships = [{"relation": "unknown_relation"}]
    entity_graph = [{
        "@id": "https://example/entity", "@type": ["skos:Concept"],
        "skos:prefLabel": "RPKI", "prov:wasDerivedFrom": ["https://example/source"],
        "bgpkb:reviewStatus": "approved",
    }]

    diagnostics = module.build_diagnostics(
        entities, sources, semantic, relationships, entity_graph, [{"predicate": "prov:wasDerivedFrom"}], sample_config()
    )
    report = module.build_report(1, 1, 1, [], 1, diagnostics)

    assert "SKOS 覆盖率：100.00%" in report
    assert "PROV-O 覆盖率：100.00%" in report
    assert "bgpkb 覆盖率：100.00%" in report
    assert "未映射字段" in report and "custom_field" in report
    assert "未映射关系" in report and "unknown_relation" in report
    assert "重复 URI：1 组" in report
    assert "来源解析错误：1 条" in report


def test_blocking_unresolved_references_only_write_report(tmp_path):
    module = load_module()
    config = sample_config() | {
        "outputs": {
            "entity_catalog": "data/published/entity_catalog.jsonld",
            "source_catalog": "data/published/source_catalog.jsonld",
            "provenance_map": "data/published/provenance_map.jsonl",
            "turtle_sample": "data/published/standard_exports/sample.ttl",
            "report": "data/generated/reports/publishing/standardization_report.md",
        },
        "relation_mappings": {},
    }
    fixtures = {
        "data/published/entity_catalog.jsonl": [{
            "entity_id": "concept_rpki", "entity_type": "BGPConcept", "name": "RPKI", "review_status": "approved"
        }],
        "data/published/source_catalog.jsonl": [{
            "source_id": "rfc6811", "title": "RFC 6811", "source_type": "standard", "review_status": "approved"
        }],
        "data/published/semantic_id_map.jsonl": [
            {"resource_type": "entity", "local_id": "concept_rpki", "uri": "https://example/entity/rpki"},
            {"resource_type": "source", "local_id": "rfc6811", "uri": "https://example/source/rfc6811"},
            {"resource_type": "evidence", "local_id": "concept_rpki__rfc6811", "uri": "https://example/evidence/good"},
        ],
        "data/derived/datasets/entity_source_evidence.jsonl": [
            {
                "evidence_id": "concept_rpki__missing", "entity_id": "concept_rpki", "source_id": "missing",
                "chunk_sample_ids": [],
            },
            {
                "evidence_id": "concept_rpki__rfc6811", "entity_id": "concept_rpki", "source_id": "rfc6811",
                "chunk_sample_ids": ["missing_chunk"],
            },
        ],
        "data/knowledge/relationships/relationships.jsonl": [],
    }
    for relative, records in fixtures.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
    formal_outputs = [tmp_path / config["outputs"][key] for key in (
        "entity_catalog", "source_catalog", "provenance_map", "turtle_sample"
    )]
    for path in formal_outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("正式产物不得覆盖", encoding="utf-8")

    exit_code = module.generate_standard_exports(tmp_path, config)

    assert exit_code != 0
    assert all(path.read_text(encoding="utf-8") == "正式产物不得覆盖" for path in formal_outputs)
    report = (tmp_path / config["outputs"]["report"]).read_text(encoding="utf-8")
    assert "结论：阻塞" in report
    assert "missing" in report and "missing_chunk" in report


def test_cli_generates_deterministic_standard_exports_without_changing_primary_inputs():
    root = paths.PROJECT_ROOT
    config = yaml.safe_load((root / "metadata/config/standard_exports.yaml").read_text(encoding="utf-8"))
    inputs = [
        root / "data/published/entity_catalog.jsonl",
        root / "data/published/source_catalog.jsonl",
        root / "data/published/semantic_id_map.jsonl",
        root / "data/derived/datasets/entity_source_evidence.jsonl",
        root / "data/knowledge/relationships/relationships.jsonl",
    ]
    outputs = [root / config["outputs"][key] for key in (
        "entity_catalog", "source_catalog", "provenance_map", "turtle_sample", "report"
    )]
    input_hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")

    first = subprocess.run(
        [sys.executable, "-m", MODULE], cwd=root, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=env,
    )
    assert first.returncode == 0, first.stdout + first.stderr
    first_bytes = {path: path.read_bytes() for path in outputs}

    second = subprocess.run(
        [sys.executable, "-m", MODULE], cwd=root, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=env,
    )
    assert second.returncode == 0, second.stdout + second.stderr
    assert {path: path.read_bytes() for path in outputs} == first_bytes
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs} == input_hashes

    entity_document = json.loads(outputs[0].read_text(encoding="utf-8"))
    source_document = json.loads(outputs[1].read_text(encoding="utf-8"))
    provenance = [json.loads(line) for line in outputs[2].read_text(encoding="utf-8").splitlines() if line]
    turtle = outputs[3].read_text(encoding="utf-8")
    report = outputs[4].read_text(encoding="utf-8")

    assert "@context" in entity_document and entity_document["@graph"]
    assert [row["@id"] for row in entity_document["@graph"]] == sorted(row["@id"] for row in entity_document["@graph"])
    assert "@context" in source_document and source_document["@graph"]
    assert provenance and {row["predicate"] for row in provenance} == {
        "prov:wasDerivedFrom", "prov:wasGeneratedBy", "rdf:type"
    }
    assert "@prefix prov:" in turtle and "prov:wasDerivedFrom" in turtle
    assert report.startswith("# 标准化出口报告\n")
    assert "实体 JSON-LD" in report and "来源 JSON-LD" in report and "PROV-O" in report
    assert "SKOS 覆盖率" in report and "未映射关系" in report and "重复 URI" in report

    report_policy = yaml.safe_load((root / "metadata/config/report_policy.yaml").read_text(encoding="utf-8"))
    assert report_policy["reports"]["standardization_report"] == {
        "path": "data/generated/reports/publishing/standardization_report.md",
        "category": "publishing",
        "retention": "generated",
        "human_entry": False,
    }
