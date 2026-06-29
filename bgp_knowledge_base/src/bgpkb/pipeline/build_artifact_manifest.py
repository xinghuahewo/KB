#!/usr/bin/env python3
import csv
import json
import subprocess
from collections import Counter
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
DATASET_DIR = paths.DATASETS_DIR
REPORT = paths.report_path("artifact_manifest_report")
JSONL_OUTPUT = DATASET_DIR / "artifact_manifest.jsonl"
CSV_OUTPUT = DATASET_DIR / "artifact_manifest.csv"

SCAN_DIRS = [
    "data",
    "metadata",
    "src",
    "tests",
    "docs",
]

EXCLUDED_PATHS = {
    "data/derived/datasets/artifact_manifest.jsonl",
    "data/derived/datasets/artifact_manifest.csv",
    "data/generated/reports/publishing/artifact_manifest_report.md",
    "data/reports/gates/pipeline_report.md",
    "data/reports/gates/quality_report.md",
}


def relative_path(path):
    return path.relative_to(ROOT).as_posix()


def iter_artifact_paths():
    for dirname in SCAN_DIRS:
        base = ROOT / dirname
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if "__pycache__" in path.parts:
                continue
            if not path.is_file():
                continue
            rel = relative_path(path)
            if rel in EXCLUDED_PATHS:
                continue
            yield path


def is_binary_bytes(data):
    if b"\x00" in data:
        return True
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def line_count_for(data, is_binary):
    if is_binary:
        return 0
    if not data:
        return 0
    return len(data.decode("utf-8").splitlines())


def sha256_for_path(path):
    result = subprocess.run(
        ["shasum", "-a", "256", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"shasum failed for {path}: {result.stderr.strip()}")
    return result.stdout.split()[0]


def producer_for(rel):
    if rel.startswith("data/corpus/parsed/") or rel.startswith("data/corpus/cleaned/"):
        return "src/bgpkb/pipeline/parse_documents.py"
    if rel.startswith("data/corpus/chunks/seeds/"):
        return "manual_seed"
    if rel.startswith("data/corpus/chunks/"):
        return "src/bgpkb/pipeline/build_chunks.py"
    if rel.startswith("data/derived/datasets/case_observations."):
        return "src/bgpkb/pipeline/extract_case_observations.py"
    if rel.startswith("data/derived/datasets/source_processing_status."):
        return "src/bgpkb/pipeline/build_source_processing_status.py"
    if rel.startswith("data/derived/datasets/source_gap_queue."):
        return "src/bgpkb/pipeline/build_source_gap_queue.py"
    if rel.startswith("data/derived/datasets/entity_review_queue."):
        return "src/bgpkb/pipeline/build_entity_review_queue.py"
    if rel.startswith("data/derived/datasets/entity_source_evidence."):
        return "src/bgpkb/pipeline/build_entity_source_evidence.py"
    if rel.startswith("data/derived/datasets/entity_review_packets."):
        return "src/bgpkb/pipeline/build_entity_review_packets.py"
    if rel.startswith("data/derived/datasets/authoritative_source_requirements."):
        return "src/bgpkb/pipeline/build_authoritative_source_requirements.py"
    if rel.startswith("data/derived/datasets/next_action_queue."):
        return "src/bgpkb/pipeline/build_next_action_queue.py"
    if rel.startswith("data/derived/datasets/human_review_workbook."):
        return "src/bgpkb/pipeline/build_human_review_workbook.py"
    if rel.startswith("data/derived/datasets/human_review_decision_audit."):
        return "src/bgpkb/pipeline/build_human_review_decision_audit.py"
    if rel.startswith("data/derived/datasets/human_review_decision_apply_preview."):
        return "src/bgpkb/pipeline/apply_human_review_decisions.py"
    if rel.startswith("data/derived/datasets/human_review_progress."):
        return "src/bgpkb/pipeline/build_human_review_progress.py"
    if rel.startswith("data/derived/datasets/human_review_evidence_extracts."):
        return "src/bgpkb/pipeline/build_human_review_evidence_extracts.py"
    if rel.startswith("data/derived/datasets/human_review_session_queue."):
        return "src/bgpkb/pipeline/build_human_review_session_queue.py"
    if rel.startswith("data/derived/datasets/human_review_session_status."):
        return "src/bgpkb/pipeline/build_human_review_session_status.py"
    if rel.startswith("data/derived/datasets/human_review_field_checklist."):
        return "src/bgpkb/pipeline/build_human_review_field_checklist.py"
    if rel.startswith("data/derived/datasets/human_review_source_matrix."):
        return "src/bgpkb/pipeline/build_human_review_source_matrix.py"
    if rel.startswith("data/derived/datasets/human_review_task_board."):
        return "src/bgpkb/pipeline/build_human_review_task_board.py"
    if rel.startswith("data/derived/datasets/human_review_handoff."):
        return "src/bgpkb/pipeline/build_human_review_handoff.py"
    if rel.startswith("data/derived/datasets/lifecycle_inventory."):
        return "src/bgpkb/pipeline/build_lifecycle_report.py"
    if rel.startswith("data/derived/datasets/semantic_quality_findings."):
        return "src/bgpkb/pipeline/build_semantic_quality_report.py"
    if rel.startswith("data/derived/datasets/chunk_enrichment_candidates."):
        return "src/bgpkb/pipeline/build_llm_candidate_enrichment.py"
    if rel.startswith("data/derived/datasets/entity_link_candidates."):
        return "src/bgpkb/pipeline/build_llm_candidate_enrichment.py"
    if rel.startswith("data/derived/datasets/standard_mapping_candidate"):
        return "src/bgpkb/pipeline/build_standard_mapping_candidates.py"
    if rel.startswith("data/derived/datasets/standard_mapping_decision_audit."):
        return "src/bgpkb/pipeline/build_standard_mapping_decision_audit.py"
    if rel.startswith("data/derived/datasets/standard_mapping_apply_preview."):
        return "src/bgpkb/pipeline/apply_standard_mapping_decisions.py"
    if rel.startswith("data/derived/datasets/approved_standard_mappings."):
        return "src/bgpkb/pipeline/apply_standard_mapping_decisions.py"
    if rel.startswith("data/derived/datasets/rag_query_eval."):
        return "src/bgpkb/pipeline/build_rag_readiness_report.py"
    if rel.startswith("data/derived/datasets/rag_answer_eval_questions."):
        return "manual_eval_dataset"
    if rel.startswith("data/derived/datasets/rag_answer_eval_results."):
        return "src/bgpkb/pipeline/run_rag_answer_eval.py"
    if rel.startswith("data/derived/datasets/deepseek_rag_answer_eval_results."):
        return "src/bgpkb/pipeline/run_deepseek_rag_answer_eval.py"
    if rel.startswith("data/derived/datasets/rag_answer_smoke_test_results."):
        return "src/bgpkb/pipeline/run_rag_answer_smoke_test.py"
    if rel == "data/review_inputs/human_review_decisions_template.csv":
        return "src/bgpkb/pipeline/build_human_review_decision_template.py"
    if rel.startswith("data/review_inputs/human_review_session_decision_templates/"):
        return "src/bgpkb/pipeline/build_human_review_session_decision_templates.py"
    if rel == "data/review_inputs/human_review_decisions.csv":
        return "manual_human_review_input"
    if rel == "data/review_inputs/standard_mapping_decisions.csv":
        return "manual_standard_mapping_review_input"
    if rel.startswith("data/derived/datasets/glossary."):
        return "src/bgpkb/pipeline/build_glossary.py"
    if rel.startswith("data/published/"):
        if rel in {
            "data/published/entity_catalog.jsonld",
            "data/published/source_catalog.jsonld",
            "data/published/provenance_map.jsonl",
        } or rel.startswith("data/published/standard_exports/"):
            return "src/bgpkb/pipeline/build_standard_exports.py"
        if rel in {"data/published/bgp_knowledge_base.sqlite", "data/published/sqlite_schema.sql"}:
            return "src/bgpkb/pipeline/build_sqlite_knowledge_base.py"
        if rel == "data/published/integrity_summary.json":
            return "src/bgpkb/pipeline/build_published_integrity_report.py"
        if rel == "data/published/readiness_summary.json":
            return "src/bgpkb/pipeline/build_readiness_report.py"
        if rel == "data/published/data_dictionary.json":
            return "src/bgpkb/pipeline/build_data_dictionary.py"
        if rel in {"data/published/jsonld_context.json", "data/published/semantic_id_map.jsonl"}:
            return "src/bgpkb/pipeline/build_semantic_identity.py"
        if rel in {"data/published/embedding_manifest.json", "data/published/rag_mock_vector_index.jsonl", "data/published/rag_retrieval_index.json"}:
            return "src/bgpkb/pipeline/build_rag_indexes.py"
        return "src/bgpkb/pipeline/build_published_knowledge_base.py"
    if rel.startswith("data/generated/reports/publishing/published_knowledge_base_report.md"):
        return "src/bgpkb/pipeline/build_published_knowledge_base.py"
    if rel.startswith("data/generated/reports/publishing/sqlite_knowledge_base_report.md"):
        return "src/bgpkb/pipeline/build_sqlite_knowledge_base.py"
    if rel.startswith("data/reports/reference/query_examples_report.md"):
        return "src/bgpkb/pipeline/build_query_examples.py"
    if rel.startswith("data/reports/gates/published_integrity_report.md"):
        return "src/bgpkb/pipeline/build_published_integrity_report.py"
    if rel.startswith("data/reports/gates/readiness_report.md"):
        return "src/bgpkb/pipeline/build_readiness_report.py"
    if rel.startswith("data/reports/reference/data_dictionary_report.md"):
        return "src/bgpkb/pipeline/build_data_dictionary.py"
    if rel.startswith("data/generated/reports/corpus/parse_report.md"):
        return "src/bgpkb/pipeline/parse_documents.py"
    if rel.startswith("data/generated/reports/knowledge/case_observation_report.md"):
        return "src/bgpkb/pipeline/extract_case_observations.py"
    if rel.startswith("data/generated/reports/review/case_observation_guides/"):
        return "src/bgpkb/pipeline/build_case_observation_guides.py"
    if rel.startswith("data/generated/reports/sources/source_processing_status_report.md"):
        return "src/bgpkb/pipeline/build_source_processing_status.py"
    if rel.startswith("data/generated/reports/sources/source_gap_queue_report.md"):
        return "src/bgpkb/pipeline/build_source_gap_queue.py"
    if rel.startswith("data/generated/reports/knowledge/entity_review_queue_report.md"):
        return "src/bgpkb/pipeline/build_entity_review_queue.py"
    if rel.startswith("data/generated/reports/knowledge/entity_source_evidence_report.md"):
        return "src/bgpkb/pipeline/build_entity_source_evidence.py"
    if rel.startswith("data/generated/reports/knowledge/entity_review_packet_report.md"):
        return "src/bgpkb/pipeline/build_entity_review_packets.py"
    if rel.startswith("data/generated/reports/knowledge/authoritative_source_requirements_report.md"):
        return "src/bgpkb/pipeline/build_authoritative_source_requirements.py"
    if rel.startswith("data/reports/actions/next_action_queue_report.md"):
        return "src/bgpkb/pipeline/build_next_action_queue.py"
    if rel.startswith("data/generated/reports/review/human_review_workbook_report.md"):
        return "src/bgpkb/pipeline/build_human_review_workbook.py"
    if rel.startswith("data/generated/reports/review/human_review_decision_template_report.md"):
        return "src/bgpkb/pipeline/build_human_review_decision_template.py"
    if rel.startswith("data/generated/reports/review/human_review_decision_audit_report.md"):
        return "src/bgpkb/pipeline/build_human_review_decision_audit.py"
    if rel.startswith("data/reports/actions/human_review_progress_report.md"):
        return "src/bgpkb/pipeline/build_human_review_progress.py"
    if rel.startswith("data/generated/reports/review/human_review_evidence_extracts_report.md"):
        return "src/bgpkb/pipeline/build_human_review_evidence_extracts.py"
    if rel.startswith("data/generated/reports/review/human_review_session_queue_report.md"):
        return "src/bgpkb/pipeline/build_human_review_session_queue.py"
    if rel.startswith("data/generated/reports/review/human_review_session_status_report.md"):
        return "src/bgpkb/pipeline/build_human_review_session_status.py"
    if rel.startswith("data/generated/reports/review/human_review_field_checklist_report.md"):
        return "src/bgpkb/pipeline/build_human_review_field_checklist.py"
    if rel.startswith("data/generated/reports/review/human_review_source_matrix_report.md"):
        return "src/bgpkb/pipeline/build_human_review_source_matrix.py"
    if rel.startswith("data/reports/actions/human_review_task_board_report.md"):
        return "src/bgpkb/pipeline/build_human_review_task_board.py"
    if rel.startswith("data/generated/reports/review/human_review_handoff_report.md"):
        return "src/bgpkb/pipeline/build_human_review_handoff.py"
    if rel.startswith("data/generated/reports/knowledge/lifecycle_report.md"):
        return "src/bgpkb/pipeline/build_lifecycle_report.py"
    if rel.startswith("data/generated/reports/knowledge/semantic_quality_report.md"):
        return "src/bgpkb/pipeline/build_semantic_quality_report.py"
    if rel.startswith("data/generated/reports/publishing/semantic_identity_report.md"):
        return "src/bgpkb/pipeline/build_semantic_identity.py"
    if rel.startswith("data/generated/reports/publishing/standardization_report.md"):
        return "src/bgpkb/pipeline/build_standard_exports.py"
    if rel.startswith("data/generated/reports/review/standard_mapping_candidate_report.md"):
        return "src/bgpkb/pipeline/build_standard_mapping_candidates.py"
    if rel.startswith("data/generated/reports/review/standard_mapping_decision_audit_report.md"):
        return "src/bgpkb/pipeline/build_standard_mapping_decision_audit.py"
    if rel.startswith("data/generated/reports/review/standard_mapping_decision_apply_report.md"):
        return "src/bgpkb/pipeline/apply_standard_mapping_decisions.py"
    if rel.startswith("data/generated/reports/rag/rag_readiness_report.md"):
        return "src/bgpkb/pipeline/build_rag_readiness_report.py"
    if rel.startswith("data/generated/reports/rag/rag_answer_eval_report.md"):
        return "src/bgpkb/pipeline/run_rag_answer_eval.py"
    if rel.startswith("data/generated/reports/rag/deepseek_rag_answer_eval_report.md"):
        return "src/bgpkb/pipeline/run_deepseek_rag_answer_eval.py"
    if rel.startswith("data/generated/reports/rag/rag_answer_failure_analysis_report.md"):
        return "src/bgpkb/pipeline/build_rag_answer_failure_analysis.py"
    if rel.startswith("data/generated/reports/rag/rag_answer_smoke_test_report.md"):
        return "src/bgpkb/pipeline/run_rag_answer_smoke_test.py"
    if rel.startswith("data/generated/reports/review/human_review_session_decision_templates_report.md"):
        return "src/bgpkb/pipeline/build_human_review_session_decision_templates.py"
    if rel.startswith("data/generated/reports/review/human_review_session_guides/"):
        return "src/bgpkb/pipeline/build_human_review_session_guides.py"
    if rel.startswith("data/generated/reports/review/human_review_decision_apply_report.md"):
        return "src/bgpkb/pipeline/apply_human_review_decisions.py"
    if rel.startswith("data/generated/reports/review/human_review_guides/"):
        return "src/bgpkb/pipeline/build_human_review_guides.py"
    if rel.startswith("data/generated/reports/knowledge/glossary_report.md"):
        return "src/bgpkb/pipeline/build_glossary.py"
    if rel.startswith("data/reports/reference/coverage_report.md"):
        return "src/bgpkb/pipeline/build_coverage_report.py"
    if rel.startswith("data/knowledge/relationships/"):
        return "manual_seed_or_scripts/build_relationships.py"
    if rel.startswith("data/knowledge/entities/"):
        return "manual_seed"
    if rel.startswith("metadata/schemas/"):
        return "manual_schema"
    if rel.startswith("src/bgpkb/pipeline/"):
        return "manual_script"
    if rel.startswith("data/sources/raw/"):
        return "manual_or_collected_source"
    if rel.startswith("metadata/config/") or rel.startswith("data/sources/inventory/"):
        return "manual_config"
    if rel.startswith("data/reports/"):
        return "manual_or_prior_step_report"
    if rel.startswith("data/generated/reports/"):
        return "generated_report"
    return "unknown"


def report_policy_for(rel):
    for report_id, meta in paths.report_policy().items():
        policy_path = meta["path"]
        if rel == policy_path or rel.startswith(f"{policy_path}/"):
            return report_id, meta
    return "", {}


def build_record(path):
    rel = relative_path(path)
    data = path.read_bytes()
    binary = is_binary_bytes(data)
    report_id, report_meta = report_policy_for(rel)
    record = {
        "artifact_path": rel,
        "artifact_group": rel.split("/", 1)[0],
        "extension": path.suffix.lower() or "none",
        "size_bytes": len(data),
        "line_count": line_count_for(data, binary),
        "is_binary": binary,
        "sha256": sha256_for_path(path),
        "generated_by": producer_for(rel),
    }
    if report_id:
        record["report_id"] = report_id
        record["report_category"] = report_meta["category"]
        record["report_retention"] = report_meta["retention"]
        record["report_human_entry"] = report_meta["human_entry"]
    return record


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "artifact_path",
        "artifact_group",
        "extension",
        "size_bytes",
        "line_count",
        "is_binary",
        "sha256",
        "generated_by",
        "report_id",
        "report_category",
        "report_retention",
        "report_human_entry",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def write_report(records):
    by_group = Counter(record["artifact_group"] for record in records)
    binary_count = sum(1 for record in records if record["is_binary"])
    total_size = sum(record["size_bytes"] for record in records)
    lines = [
        "# 制品清单报告",
        "",
        "## 范围",
        "",
        "本报告记录知识库目录内主要制品的文件级事实，包括路径、大小、行数、二进制标记和 SHA-256。该步骤不理解或归纳文件内容。",
        "",
        "为避免流水线尾部报告写入导致校验和反复变化，以下路径不纳入清单：",
        "",
    ]
    for rel in sorted(EXCLUDED_PATHS):
        lines.append(f"- `{rel}`")
    lines.extend([
        "",
        "## 摘要",
        "",
        f"- 清单记录数：{len(records)}",
        f"- 二进制文件数：{binary_count}",
        f"- 总字节数：{total_size}",
        f"- JSONL 输出：`data/derived/datasets/artifact_manifest.jsonl`",
        f"- CSV 输出：`data/derived/datasets/artifact_manifest.csv`",
        "",
        "## 按目录统计",
        "",
    ])
    for group, count in sorted(by_group.items()):
        lines.append(f"- {group}：{count}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    records = [build_record(path) for path in iter_artifact_paths()]
    records.sort(key=lambda item: item["artifact_path"])
    write_jsonl(records)
    write_csv(records)
    write_report(records)
    print(f"Wrote {JSONL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {CSV_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
