import importlib
import importlib.util
import json


MODULE = "bgpkb.pipeline.assess_corpus_ocr_quality"
PROVIDER_MODULE = "bgpkb.service.corpus_ocr_provider"


def load_module():
    assert importlib.util.find_spec(MODULE) is not None, "OCR 质量评估流水线尚未实现"
    return importlib.import_module(MODULE)


def load_provider_module():
    assert importlib.util.find_spec(PROVIDER_MODULE) is not None, "OCR Provider 契约尚未实现"
    return importlib.import_module(PROVIDER_MODULE)


def assessment_config(**overrides):
    config = {
        "prompt_version": "corpus-ocr-quality-v1",
        "max_documents": 2,
        "max_chars_per_document": 30,
        "max_total_input_chars": 60,
        "max_concurrency": 1,
    }
    config.update(overrides)
    return config


class FakeProvider:
    name = "fake"
    model = "fake-model"

    def __init__(self, response=None):
        self.response = response or {
            "ok": True,
            "provider": self.name,
            "model": self.model,
            "content": json.dumps({
                "risk_level": "low",
                "reason": "文本连续且字符正常。",
                "recommendation": "无需额外处理。",
            }, ensure_ascii=False),
        }
        self.calls = []

    def assess(self, item, prompt_version):
        self.calls.append((item, prompt_version))
        return dict(self.response)


def test_sample_document_covers_head_middle_and_tail_within_limit():
    module = load_module()
    text = "HEAD-" + "a" * 40 + "-MIDDLE-" + "b" * 40 + "-TAIL"

    sample = module.sample_document(text, max_chars=36)

    assert len(sample) <= 36
    assert sample.startswith("HEAD-")
    assert "MIDDLE" in sample
    assert sample.endswith("-TAIL")


def test_assessment_budget_processes_stable_prefix_and_skips_remainder():
    module = load_module()
    provider = FakeProvider()
    documents = {"c": "c" * 50, "a": "a" * 50, "b": "b" * 50}

    records = module.assess_documents(
        documents,
        assessment_config(max_documents=1, max_total_input_chars=30),
        provider,
        generated_at="2026-06-30T00:00:00Z",
    )

    assert [row["doc_id"] for row in records] == ["a", "b", "c"]
    assert records[0]["status"] == "completed"
    assert records[1]["status"] == records[2]["status"] == "skipped"
    assert records[1]["error_code"] == records[2]["error_code"] == "budget_exceeded"
    assert len(provider.calls) == 1


def test_mock_provider_is_stable_and_never_uses_network():
    module = load_module()
    providers = load_provider_module()
    provider = providers.MockCorpusOcrProvider()
    documents = {"doc": "正常的中英文 cleaned 文本。BGP route."}

    first = module.assess_documents(
        documents, assessment_config(), provider, generated_at="2026-06-30T00:00:00Z"
    )
    second = module.assess_documents(
        documents, assessment_config(), provider, generated_at="2026-06-30T00:00:00Z"
    )

    assert first == second
    assert first[0]["status"] == "completed"
    assert first[0]["provider"] == "mock"
    assert first[0]["risk_level"] in {"low", "medium", "high"}


def test_deepseek_missing_key_is_skipped_without_exposing_secret():
    module = load_module()
    providers = load_provider_module()
    provider = providers.DeepSeekCorpusOcrProvider(api_key="")

    [record] = module.assess_documents(
        {"doc": "待评估文本"},
        assessment_config(),
        provider,
        generated_at="2026-06-30T00:00:00Z",
    )

    assert record["status"] == "skipped"
    assert record["error_code"] == "missing_api_key"
    assert "key" not in record["reason"].lower()
    assert "secret" not in json.dumps(record).lower()


def test_invalid_provider_response_is_failed_and_not_persisted_as_risk():
    module = load_module()
    provider = FakeProvider({
        "ok": True,
        "provider": "fake",
        "model": "fake-model",
        "content": json.dumps({"risk_level": "critical", "reason": "x"}),
    })

    [record] = module.assess_documents(
        {"doc": "待评估文本"},
        assessment_config(),
        provider,
        generated_at="2026-06-30T00:00:00Z",
    )

    assert record["status"] == "failed"
    assert record["risk_level"] == "unknown"
    assert record["error_code"] == "invalid_response"
    assert record["reason"] == ""
    assert record["recommendation"] == ""


def test_transient_failure_preserves_matching_completed_assessment():
    module = load_module()
    provider = FakeProvider()
    [completed] = module.assess_documents(
        {"doc": "同一份文本"},
        assessment_config(),
        provider,
        generated_at="2026-06-30T00:00:00Z",
    )
    failed_provider = FakeProvider({
        "ok": False,
        "provider": "fake",
        "model": "fake-model",
        "error_code": "request_failed",
        "error": "temporary failure",
    })

    records = module.assess_documents(
        {"doc": "同一份文本"},
        assessment_config(),
        failed_provider,
        generated_at="2026-07-01T00:00:00Z",
        existing_records=[completed],
    )

    assert records == [completed]


def test_high_model_risk_does_not_change_deterministic_report_conclusion():
    profiling = importlib.import_module("bgpkb.pipeline.profile_cleaned_corpus")
    profile = {
        "doc_id": "doc",
        "parsed_exists": True,
        "cleaned_exists": True,
        "chunks_exist": True,
        "parsed_paths": [],
        "cleaned_paths": [],
        "chunk_files": [],
        "metrics": {
            "character_count": 100,
            "paragraph_count": 1,
            "average_paragraph_chars": 100.0,
            "section_count": 1,
            "chunk_count": 1,
            "replacement_character_count": 0,
            "suspected_table_line_count": 0,
            "abnormal_symbol_count": 0,
            "abnormal_symbol_ratio": 0.0,
            "empty_heading_count": 0,
            "duplicate_heading_count": 0,
        },
        "blocking_issues": [],
        "warnings": [],
        "generated_by": profiling.GENERATED_BY,
    }
    assessment = {
        "status": "completed",
        "risk_level": "high",
        "provider": "mock",
        "model": "mock-v1",
        "prompt_version": "v1",
    }

    report = profiling.render_profile_report([profile], [assessment])

    assert "结论：通过" in report
    assert '"high": 1' in report
    assert "仅供人工复核，不参与确定性门禁" in report
