import importlib
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

from bgpkb import paths


CONFIG = paths.CONFIG_DIR / "corpus_profiling.yaml"
PROFILE_SCHEMA = paths.SCHEMAS_DIR / "corpus_profile.schema.json"
OCR_SCHEMA = paths.SCHEMAS_DIR / "corpus_ocr_assessment.schema.json"
MODULE = "bgpkb.pipeline.profile_cleaned_corpus"


def load_module():
    assert importlib.util.find_spec(MODULE) is not None, "阶段 A 语料画像生成器尚未实现"
    return importlib.import_module(MODULE)


def test_corpus_profiling_config_declares_deterministic_and_model_boundaries():
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))

    assert config["version"] == 1
    assert "**/README.md" in config["exclude_globs"]
    assert config["cleaned_doc_id_overrides"]["notes/context_summary.md"] == "context_2026"
    assert {
        "short_document_chars",
        "long_document_chars",
        "short_paragraph_chars",
        "abnormal_symbol_ratio",
    } <= set(config["thresholds"])
    assert {"minimum_pipe_count", "minimum_table_rows"} <= set(config["table_detection"])
    assert {
        "enabled_by_default",
        "allowed_providers",
        "prompt_version",
        "max_documents",
        "max_chars_per_document",
        "max_total_input_chars",
        "max_concurrency",
    } <= set(config["ocr_assessment"])
    assert config["ocr_assessment"]["enabled_by_default"] is False
    assert config["ocr_assessment"]["allowed_providers"] == ["mock", "deepseek"]


def test_profile_and_ocr_schemas_separate_blocking_from_model_risk():
    profile = json.loads(PROFILE_SCHEMA.read_text(encoding="utf-8"))
    ocr = json.loads(OCR_SCHEMA.read_text(encoding="utf-8"))

    assert profile["additionalProperties"] is False
    assert {
        "doc_id",
        "parsed_exists",
        "cleaned_exists",
        "chunks_exist",
        "metrics",
        "blocking_issues",
        "warnings",
        "generated_by",
    } <= set(profile["required"])
    assert profile["properties"]["blocking_issues"]["items"]["enum"] == [
        "duplicate_doc_id",
        "empty_cleaned_content",
        "orphan_chunk_document",
        "replacement_character",
    ]

    assert ocr["additionalProperties"] is False
    assert {
        "assessment_id",
        "doc_id",
        "input_fingerprint",
        "status",
        "risk_level",
        "reason",
        "recommendation",
        "provider",
        "model",
        "prompt_version",
        "generated_at",
        "error_code",
        "generated_by",
    } <= set(ocr["required"])
    assert ocr["properties"]["status"]["enum"] == ["completed", "failed", "skipped"]
    assert ocr["properties"]["risk_level"]["enum"] == ["low", "medium", "high", "unknown"]


def sample_config():
    return {
        "exclude_globs": ["**/README.md"],
        "thresholds": {
            "short_document_chars": 10,
            "long_document_chars": 100,
            "short_paragraph_chars": 3,
            "abnormal_symbol_ratio": 0.01,
        },
        "table_detection": {"minimum_pipe_count": 2, "minimum_table_rows": 2},
    }


def write_parsed(path: Path, doc_id: str, sections=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "doc_id": doc_id,
        "source_path": f"data/sources/raw/{doc_id}.txt",
        "source_format": "txt",
        "title": doc_id,
        "sections": sections or [{"section_id": "s1", "heading": "标题", "content": "正文"}],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def write_cleaned(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_chunks(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_build_profiles_uses_union_excludes_readme_and_keeps_seed(tmp_path):
    module = load_module()
    parsed = tmp_path / "parsed"
    cleaned = tmp_path / "cleaned"
    chunks = tmp_path / "chunks"
    write_parsed(parsed / "parsed_only.json", "parsed_only")
    write_cleaned(cleaned / "cleaned_only.md", "# 标题\n\n这是 cleaned 正文。")
    write_cleaned(cleaned / "README.md", "目录说明")
    write_cleaned(cleaned / "seeds/context_seed.md", "# 上下文\n\n正式种子语料。")
    write_chunks(chunks / "chunks.jsonl", [
        {"chunk_id": "orphan_1", "doc_id": "chunk_only", "content": "孤儿 chunk"},
        {"chunk_id": "seed_1", "doc_id": "context_seed", "content": "种子 chunk"},
    ])

    profiles = module.build_corpus_profiles(parsed, cleaned, chunks, sample_config(), root=tmp_path)

    assert [row["doc_id"] for row in profiles] == [
        "chunk_only",
        "cleaned_only",
        "context_seed",
        "parsed_only",
    ]
    by_id = {row["doc_id"]: row for row in profiles}
    assert by_id["parsed_only"]["parsed_exists"] is True
    assert by_id["parsed_only"]["cleaned_exists"] is False
    assert by_id["cleaned_only"]["cleaned_exists"] is True
    assert by_id["context_seed"]["chunks_exist"] is True
    assert by_id["chunk_only"]["blocking_issues"] == ["orphan_chunk_document"]


def test_cleaned_doc_id_override_links_formal_seed_corpus(tmp_path):
    module = load_module()
    parsed = tmp_path / "parsed"
    cleaned = tmp_path / "cleaned"
    chunks = tmp_path / "chunks"
    parsed.mkdir()
    write_cleaned(cleaned / "notes/context_summary.md", "# 上下文\n\n正式种子语料。")
    write_chunks(chunks / "seeds/context.jsonl", [
        {"chunk_id": "context_1", "doc_id": "context_2026", "content": "种子"},
    ])
    config = sample_config() | {
        "cleaned_doc_id_overrides": {"notes/context_summary.md": "context_2026"},
    }

    [profile] = module.build_corpus_profiles(parsed, cleaned, chunks, config, root=tmp_path)

    assert profile["doc_id"] == "context_2026"
    assert profile["cleaned_exists"] is True
    assert "orphan_chunk_document" not in profile["blocking_issues"]


def test_build_profiles_calculates_metrics_and_classifies_issues(tmp_path):
    module = load_module()
    parsed = tmp_path / "parsed"
    cleaned = tmp_path / "cleaned"
    chunks = tmp_path / "chunks"
    sections = [
        {"section_id": "s1", "heading": "重复", "content": "第一节"},
        {"section_id": "s2", "heading": "重复", "content": "第二节"},
        {"section_id": "s3", "heading": "", "content": "第三节"},
    ]
    write_parsed(parsed / "doc.json", "doc", sections)
    write_parsed(parsed / "duplicate.json", "doc", sections)
    write_cleaned(cleaned / "doc.md", "# 标题\n\n甲|乙|丙\n---|---|---\n正文�\x00")
    write_chunks(chunks / "chunks.jsonl", [
        {"chunk_id": "doc_1", "doc_id": "doc", "content": "第一块"},
        {"chunk_id": "doc_2", "doc_id": "doc", "content": "第二块"},
    ])

    [profile] = module.build_corpus_profiles(parsed, cleaned, chunks, sample_config(), root=tmp_path)

    assert profile["metrics"] == {
        "character_count": 22,
        "paragraph_count": 1,
        "average_paragraph_chars": 22.0,
        "section_count": 6,
        "chunk_count": 2,
        "replacement_character_count": 1,
        "suspected_table_line_count": 2,
        "abnormal_symbol_count": 1,
        "abnormal_symbol_ratio": 0.045455,
        "empty_heading_count": 2,
        "duplicate_heading_count": 4,
    }
    assert profile["blocking_issues"] == ["duplicate_doc_id", "replacement_character"]
    assert profile["warnings"] == [
        "abnormal_symbols",
        "duplicate_heading",
        "empty_heading",
        "suspected_table",
    ]


def test_empty_cleaned_content_blocks_but_heuristics_only_warn(tmp_path):
    module = load_module()
    parsed = tmp_path / "parsed"
    cleaned = tmp_path / "cleaned"
    chunks = tmp_path / "chunks"
    write_parsed(parsed / "empty.json", "empty")
    write_cleaned(cleaned / "empty.md", "# 只有标题\n\n")
    chunks.mkdir()

    [profile] = module.build_corpus_profiles(parsed, cleaned, chunks, sample_config(), root=tmp_path)

    assert profile["blocking_issues"] == ["empty_cleaned_content"]
    assert "short_document" in profile["warnings"]


def test_write_profile_outputs_is_stable_and_reports_blocking_diagnostics(tmp_path):
    module = load_module()
    profiles = [{
        "doc_id": "doc",
        "parsed_exists": True,
        "cleaned_exists": True,
        "chunks_exist": False,
        "parsed_paths": ["parsed/doc.json"],
        "cleaned_paths": ["cleaned/doc.md"],
        "chunk_files": [],
        "metrics": {
            "character_count": 0,
            "paragraph_count": 0,
            "average_paragraph_chars": 0.0,
            "section_count": 1,
            "chunk_count": 0,
            "replacement_character_count": 0,
            "suspected_table_line_count": 0,
            "abnormal_symbol_count": 0,
            "abnormal_symbol_ratio": 0.0,
            "empty_heading_count": 0,
            "duplicate_heading_count": 0,
        },
        "blocking_issues": ["empty_cleaned_content"],
        "warnings": ["missing_chunks", "short_document"],
        "generated_by": module.GENERATED_BY,
    }]
    dataset = tmp_path / "corpus_profile.jsonl"
    report = tmp_path / "corpus_profile_report.md"

    module.write_profile_outputs(profiles, dataset, report)
    first_dataset = dataset.read_text(encoding="utf-8")
    first_report = report.read_text(encoding="utf-8")
    module.write_profile_outputs(profiles, dataset, report)

    assert dataset.read_text(encoding="utf-8") == first_dataset
    assert report.read_text(encoding="utf-8") == first_report
    assert json.loads(first_dataset) == profiles[0]
    assert "# 语料质量画像报告" in first_report
    assert "结论：阻断" in first_report
    assert "确定性阻断问题：1" in first_report
    assert "模型评估状态：未运行" in first_report


def test_input_parse_failure_preserves_existing_outputs(tmp_path):
    module = load_module()
    parsed = tmp_path / "parsed"
    cleaned = tmp_path / "cleaned"
    chunks = tmp_path / "chunks"
    parsed.mkdir()
    cleaned.mkdir()
    chunks.mkdir()
    (parsed / "broken.json").write_text("{broken", encoding="utf-8")
    dataset = tmp_path / "corpus_profile.jsonl"
    report = tmp_path / "corpus_profile_report.md"
    dataset.write_text("old dataset\n", encoding="utf-8")
    report.write_text("old report\n", encoding="utf-8")

    with pytest.raises(ValueError, match="broken.json"):
        module.run_profiling(
            parsed_dir=parsed,
            cleaned_dir=cleaned,
            chunk_dir=chunks,
            config=sample_config(),
            dataset_path=dataset,
            report_path=report,
            root=tmp_path,
        )

    assert dataset.read_text(encoding="utf-8") == "old dataset\n"
    assert report.read_text(encoding="utf-8") == "old report\n"
