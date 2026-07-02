import json
from pathlib import Path

import pytest

from bgpkb import paths
from bgpkb.cleaning_v2 import batch
from bgpkb.cleaning_v2.runtime_pipeline import build_stage_handlers, materialize_picture_assets
from bgpkb.pipeline import build_cleaning_v2


RUN_SCHEMA = paths.SCHEMAS_DIR / "cleaning_run_v2.schema.json"
STATUS_SCHEMA = paths.SCHEMAS_DIR / "cleaning_document_status_v2.schema.json"


def _write_source(root: Path, name: str = "doc.pdf", body: bytes = b"pdf") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    source = root / name
    source.write_bytes(body)
    return source


def _handlers(calls, failures=None):
    failures = failures or {}

    def handle(context):
        calls.append((context.doc_id, context.stage, context.attempt))
        failure = failures.get(context.stage)
        if isinstance(failure, list) and failure:
            item = failure.pop(0)
            if item:
                raise item
        elif failure:
            raise failure
        (context.temporary_dir / f"{context.stage}.txt").write_text(
            context.stage, encoding="utf-8"
        )
        return {
            "page_count": 2,
            "ocr_page_count": 1 if context.stage == "parsed" else 0,
            "gpu_peak_memory_mb": 1024 if context.stage == "parsed" else 0,
            "fallback_used": False,
            "output_counts": {"blocks": 3} if context.stage == "normalized" else {},
        }

    return {stage: handle for stage in batch.PROCESSING_STAGES}


def test_batch_schemas_are_closed_and_cover_state_error_retry_and_performance():
    run_schema = json.loads(RUN_SCHEMA.read_text(encoding="utf-8"))
    status_schema = json.loads(STATUS_SCHEMA.read_text(encoding="utf-8"))

    assert run_schema["additionalProperties"] is False
    assert status_schema["additionalProperties"] is False
    assert {"run_id", "started_at", "finished_at", "runtime", "summary", "documents"} <= set(
        run_schema["required"]
    )
    assert {
        "doc_id", "source_path", "processing_fingerprint", "state", "transitions",
        "errors", "retries", "performance", "output_summary",
    } <= set(status_schema["required"])
    assert set(status_schema["properties"]["state"]["enum"]) == set(batch.ALL_STATES)


def test_state_machine_rejects_skips_and_records_run_time_and_reason():
    status = batch.new_document_status("run-1", "doc", "doc.pdf", "fingerprint", now="2026-07-01T00:00:00Z")

    with pytest.raises(batch.InvalidStateTransition):
        batch.transition(status, "parsed", reason="越级", now="2026-07-01T00:00:01Z")

    batch.transition(status, "preflighted", reason="预检通过", now="2026-07-01T00:00:02Z")
    assert status["state"] == "preflighted"
    assert status["transitions"][-1] == {
        "from": "discovered", "to": "preflighted", "run_id": "run-1",
        "at": "2026-07-01T00:00:02Z", "reason": "预检通过",
    }


def test_processing_fingerprint_is_stable_and_config_changes_invalidate_it(tmp_path):
    source = _write_source(tmp_path, body=b"same")
    identity = {"image_digest": "sha256:image", "models": {"layout": "sha256:model"}}

    first = batch.processing_fingerprint(source, identity, {"version": "v1", "ocr": True})
    same = batch.processing_fingerprint(source, identity, {"ocr": True, "version": "v1"})
    changed = batch.processing_fingerprint(source, identity, {"version": "v2", "ocr": True})

    assert first == same
    assert changed != first


def test_document_identity_matches_corpus_stem_and_duplicate_stems_fail_closed(tmp_path):
    first = _write_source(tmp_path / "a", "same.pdf", b"a")
    second = _write_source(tmp_path / "b", "same.html", b"b")
    runner = batch.BatchRunner(
        output_root=tmp_path / "output", run_root=tmp_path / "runs",
        config={}, runtime_identity={}, handlers=_handlers([]),
    )

    assert batch.document_id(first) == "same"
    with pytest.raises(ValueError, match="重复 doc_id"):
        runner.run([first, second], run_id="duplicate")


def test_successful_document_advances_in_order_and_publishes_atomically(tmp_path):
    source = _write_source(tmp_path / "input")
    calls = []
    runner = batch.BatchRunner(
        output_root=tmp_path / "output",
        run_root=tmp_path / "runs",
        config={"retry": {"maximum_attempts": 2}},
        runtime_identity={"image_digest": "sha256:image"},
        handlers=_handlers(calls),
    )

    result = runner.run([source], run_id="run-success")
    document = result["documents"][0]

    assert document["state"] == "approved"
    assert [state for _, state, _ in calls] == list(batch.PROCESSING_STAGES)
    assert [row["to"] for row in document["transitions"]] == list(batch.SUCCESS_STATES[1:])
    authority = tmp_path / "output" / document["doc_id"]
    assert (authority / "validated.txt").is_file()
    assert json.loads((authority / "document_status.json").read_text(encoding="utf-8"))["state"] == "approved"
    assert not list((tmp_path / "output").glob(".*.tmp-*"))


def test_identical_approved_fingerprint_is_skipped_but_changed_config_reprocesses(tmp_path):
    source = _write_source(tmp_path / "input")
    calls = []
    common = dict(
        output_root=tmp_path / "output",
        run_root=tmp_path / "runs",
        runtime_identity={"image_digest": "sha256:image"},
        handlers=_handlers(calls),
    )
    batch.BatchRunner(config={"version": "v1"}, **common).run([source], run_id="run-1")
    first_count = len(calls)
    skipped = batch.BatchRunner(config={"version": "v1"}, **common).run([source], run_id="run-2")
    assert len(calls) == first_count
    assert skipped["documents"][0]["skip_reason"] == "identical_approved_fingerprint"

    batch.BatchRunner(config={"version": "v2"}, **common).run([source], run_id="run-3")
    assert len(calls) == first_count * 2


def test_resume_continues_after_last_successful_stage(tmp_path):
    source = _write_source(tmp_path / "input")
    calls = []
    failure = batch.BatchFailure("process_interrupted", "进程中断", retryable=False, quarantine=False)
    runner = batch.BatchRunner(
        output_root=tmp_path / "output",
        run_root=tmp_path / "runs",
        config={}, runtime_identity={},
        handlers=_handlers(calls, {"normalized": failure}),
    )
    with pytest.raises(batch.RunInterrupted):
        runner.run([source], run_id="resume-run")

    resumed_calls = []
    resumed = batch.BatchRunner(
        output_root=tmp_path / "output", run_root=tmp_path / "runs",
        config={}, runtime_identity={}, handlers=_handlers(resumed_calls),
    ).run([source], run_id="resume-run", resume=True)

    assert resumed["documents"][0]["state"] == "approved"
    assert [stage for _, stage, _ in resumed_calls] == ["normalized", "validated", "approved"]


def test_retryable_failure_is_limited_and_nonretryable_failure_is_quarantined(tmp_path):
    sources = [
        _write_source(tmp_path / "input", "oom.pdf", b"oom"),
        _write_source(tmp_path / "input", "bad.pdf", b"bad"),
        _write_source(tmp_path / "input", "good.pdf", b"good"),
    ]
    calls = []

    def handler(context):
        calls.append((context.doc_id, context.stage, context.attempt))
        if context.doc_id.startswith("oom") and context.stage == "parsed":
            raise batch.BatchFailure("gpu_oom", "显存不足", retryable=True)
        if context.doc_id.startswith("bad") and context.stage == "preflighted":
            raise batch.BatchFailure("invalid_content", "文件损坏", retryable=False)
        (context.temporary_dir / f"{context.stage}.txt").write_text("ok", encoding="utf-8")
        return {}

    runner = batch.BatchRunner(
        output_root=tmp_path / "output", run_root=tmp_path / "runs",
        config={"retry": {"maximum_attempts": 2}}, runtime_identity={},
        handlers={stage: handler for stage in batch.PROCESSING_STAGES},
    )
    result = runner.run(sources, run_id="isolated")
    by_id = {row["doc_id"].split("-")[0]: row for row in result["documents"]}

    assert by_id["oom"]["state"] == "quarantined"
    assert len(by_id["oom"]["retries"]) == 1
    assert [attempt for doc, stage, attempt in calls if doc.startswith("oom") and stage == "parsed"] == [1, 2]
    assert by_id["bad"]["state"] == "quarantined"
    assert by_id["bad"]["retries"] == []
    assert by_id["good"]["state"] == "approved"


def test_batch_generates_machine_records_and_chinese_capacity_report(tmp_path):
    sources = [_write_source(tmp_path / "input", "a.pdf", b"a"), _write_source(tmp_path / "input", "b.pdf", b"b")]
    result = batch.BatchRunner(
        output_root=tmp_path / "output", run_root=tmp_path / "runs",
        config={}, runtime_identity={"gpu": "TITAN RTX"}, handlers=_handlers([]),
    ).run(sources, run_id="report-run")
    run_dir = tmp_path / "runs" / "report-run"

    assert (run_dir / "cleaning_run.json").is_file()
    report = (run_dir / "cleaning_run_report.md").read_text(encoding="utf-8")
    assert "# Docling 清洗批次报告" in report
    assert all(label in report for label in ["吞吐量", "p50", "p95", "失败率", "GPU 峰值显存", "OCR 页数", "fallback"])
    assert result["summary"]["document_count"] == 2
    assert result["summary"]["approved_count"] == 2
    assert result["summary"]["ocr_page_count"] == 2
    assert result["summary"]["gpu_peak_memory_mb"] == 1024


def test_runtime_stage_handlers_build_validated_canonical_outputs_from_docling(tmp_path):
    source = _write_source(tmp_path / "input", body=b"%PDF-1.7\n")
    fixture = json.loads(
        (Path(__file__).parent / "fixtures" / "docling" / "table_document.json").read_text(encoding="utf-8")
    )
    runtime = {"parser": "docling", "docling_version": "2.107.0", "image_digest": "sha256:image"}
    handlers = build_stage_handlers(
        config={"ocr": {}, "rules": {}},
        runtime_identity=runtime,
        docling_parser=lambda _source: fixture,
    )

    result = batch.BatchRunner(
        output_root=tmp_path / "output", run_root=tmp_path / "runs",
        config={"ocr": {}, "rules": {}}, runtime_identity=runtime, handlers=handlers,
    ).run([source], run_id="canonical-run")
    authority = tmp_path / "output" / result["documents"][0]["doc_id"]

    assert result["documents"][0]["state"] == "approved"
    assert (authority / "preflight.json").is_file()
    assert (authority / "parsed_document.json").is_file()
    cleaned = json.loads((authority / "cleaned_document.json").read_text(encoding="utf-8"))
    assert cleaned["blocks"][1]["block_type"] == "table"
    assert json.loads((authority / "validation.json").read_text(encoding="utf-8"))["valid"] is True


def test_document_can_be_approved_with_risky_picture_block_isolated(tmp_path):
    source = _write_source(tmp_path / "input", body=b"%PDF-1.7\n")
    fixture = {
        "body": {"children": [{"$ref": "#/texts/0"}, {"$ref": "#/pictures/0"}]},
        "texts": [{"self_ref": "#/texts/0", "label": "text", "text": "Approved body", "prov": []}],
        "pictures": [{"self_ref": "#/pictures/0", "label": "picture", "prov": []}],
    }
    runtime = {"parser": "docling", "docling_version": "2.107.0"}
    config = {"ocr": {}, "rules": {}}
    result = batch.BatchRunner(
        output_root=tmp_path / "output", run_root=tmp_path / "runs", config=config,
        runtime_identity=runtime,
        handlers=build_stage_handlers(config=config, runtime_identity=runtime, docling_parser=lambda _: fixture),
    ).run([source], run_id="partial-approval")
    authority = tmp_path / "output" / "doc"
    validation = json.loads((authority / "validation.json").read_text(encoding="utf-8"))

    assert result["documents"][0]["state"] == "approved"
    assert validation["valid"] is True
    assert validation["publishable_block_count"] == 1
    assert len(validation["review_queue"]) == 1


def test_runtime_applies_configured_heading_hierarchy_rule(tmp_path):
    source = _write_source(tmp_path / "input", body=b"%PDF-1.7\n")
    fixture = {
        "body": {"children": [{"$ref": "#/texts/0"}, {"$ref": "#/texts/1"}]},
        "texts": [
            {"self_ref": "#/texts/0", "label": "section_header", "text": "Paper", "level": 1, "prov": []},
            {"self_ref": "#/texts/1", "label": "section_header", "text": "1 Method", "level": 1, "prov": []},
        ],
    }
    runtime = {"parser": "docling", "docling_version": "2.107.0"}
    config = {
        "ocr": {},
        "rules": {
            "lossless": ["unicode_whitespace"],
            "structural": ["infer_heading_hierarchy"],
        },
    }

    result = batch.BatchRunner(
        output_root=tmp_path / "output",
        run_root=tmp_path / "runs",
        config=config,
        runtime_identity=runtime,
        handlers=build_stage_handlers(
            config=config, runtime_identity=runtime, docling_parser=lambda _: fixture
        ),
    ).run([source], run_id="heading-rule")
    cleaned = json.loads(
        (tmp_path / "output" / "doc" / "cleaned_document.json").read_text(encoding="utf-8")
    )

    assert result["documents"][0]["state"] == "approved"
    assert cleaned["blocks"][1]["heading_level"] == 2
    assert cleaned["blocks"][1]["review_status"] == "pending_review"
    assert cleaned["transformations"][-1]["rule_id"] == "infer_heading_hierarchy"


def test_runtime_materializes_embedded_picture_assets_with_stable_hash(tmp_path):
    payload = {
        "pictures": [
            {
                "self_ref": "#/pictures/0",
                "image": {"mimetype": "image/png", "uri": "data:image/png;base64,cGljdHVyZQ=="},
            }
        ]
    }

    materialize_picture_assets(payload, tmp_path / "assets", "doc-1")

    image = payload["pictures"][0]["image"]
    assert image["path"] == "assets/picture-0001.png"
    assert image["sha256"] == "2cea274d0bedc39ec4ab6ba9e59ec889e3ed6fb56a1cf088a64d9b383378dc97"
    assert (tmp_path / image["path"]).read_bytes() == b"picture"


def test_batch_cli_discovers_only_supported_sources_in_stable_order(tmp_path):
    _write_source(tmp_path, "z.pdf")
    _write_source(tmp_path, "a.html")
    _write_source(tmp_path, "ignore.png")

    sources = build_cleaning_v2.discover_sources(tmp_path, ["pdf", "html"])

    assert [path.name for path in sources] == ["a.html", "z.pdf"]


def test_batch_cli_legacy_fallback_preserves_explicit_yaml_evidence():
    source = paths.RAW_DIR / "data_docs" / "peeringdb_api_docs.yaml"

    document, text = build_cleaning_v2.legacy_fallback(source, "peeringdb_api_docs")

    assert document["doc_id"] == "peeringdb_api_docs"
    assert document["source_format"] == "yaml"
    assert document["sections"]
    assert "openapi:" in text
