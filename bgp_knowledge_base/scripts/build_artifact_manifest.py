#!/usr/bin/env python3
import csv
import json
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "datasets"
REPORT = ROOT / "reports" / "artifact_manifest_report.md"
JSONL_OUTPUT = DATASET_DIR / "artifact_manifest.jsonl"
CSV_OUTPUT = DATASET_DIR / "artifact_manifest.csv"

SCAN_DIRS = [
    "config",
    "inventory",
    "raw",
    "parsed",
    "cleaned",
    "chunks",
    "entities",
    "relationships",
    "published",
    "datasets",
    "review_inputs",
    "reports",
    "schemas",
    "scripts",
]

EXCLUDED_PATHS = {
    "datasets/artifact_manifest.jsonl",
    "datasets/artifact_manifest.csv",
    "reports/artifact_manifest_report.md",
    "reports/pipeline_report.md",
    "reports/quality_report.md",
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
    if rel.startswith("parsed/") or rel.startswith("cleaned/"):
        return "scripts/parse_documents.py"
    if rel.startswith("chunks/seeds/"):
        return "manual_seed"
    if rel.startswith("chunks/"):
        return "scripts/build_chunks.py"
    if rel.startswith("datasets/case_observations."):
        return "scripts/extract_case_observations.py"
    if rel.startswith("datasets/source_processing_status."):
        return "scripts/build_source_processing_status.py"
    if rel.startswith("datasets/source_gap_queue."):
        return "scripts/build_source_gap_queue.py"
    if rel.startswith("datasets/entity_review_queue."):
        return "scripts/build_entity_review_queue.py"
    if rel.startswith("datasets/entity_source_evidence."):
        return "scripts/build_entity_source_evidence.py"
    if rel.startswith("datasets/entity_review_packets."):
        return "scripts/build_entity_review_packets.py"
    if rel.startswith("datasets/authoritative_source_requirements."):
        return "scripts/build_authoritative_source_requirements.py"
    if rel.startswith("datasets/next_action_queue."):
        return "scripts/build_next_action_queue.py"
    if rel.startswith("datasets/human_review_workbook."):
        return "scripts/build_human_review_workbook.py"
    if rel.startswith("datasets/human_review_decision_audit."):
        return "scripts/build_human_review_decision_audit.py"
    if rel.startswith("datasets/human_review_decision_apply_preview."):
        return "scripts/apply_human_review_decisions.py"
    if rel.startswith("datasets/human_review_progress."):
        return "scripts/build_human_review_progress.py"
    if rel.startswith("datasets/human_review_evidence_extracts."):
        return "scripts/build_human_review_evidence_extracts.py"
    if rel.startswith("datasets/human_review_session_queue."):
        return "scripts/build_human_review_session_queue.py"
    if rel.startswith("datasets/human_review_session_status."):
        return "scripts/build_human_review_session_status.py"
    if rel.startswith("datasets/human_review_field_checklist."):
        return "scripts/build_human_review_field_checklist.py"
    if rel.startswith("datasets/human_review_source_matrix."):
        return "scripts/build_human_review_source_matrix.py"
    if rel.startswith("datasets/human_review_task_board."):
        return "scripts/build_human_review_task_board.py"
    if rel.startswith("datasets/human_review_handoff."):
        return "scripts/build_human_review_handoff.py"
    if rel.startswith("datasets/lifecycle_inventory."):
        return "scripts/build_lifecycle_report.py"
    if rel.startswith("datasets/semantic_quality_findings."):
        return "scripts/build_semantic_quality_report.py"
    if rel.startswith("datasets/chunk_enrichment_candidates."):
        return "scripts/build_llm_candidate_enrichment.py"
    if rel.startswith("datasets/entity_link_candidates."):
        return "scripts/build_llm_candidate_enrichment.py"
    if rel.startswith("datasets/rag_query_eval."):
        return "scripts/build_rag_readiness_report.py"
    if rel.startswith("datasets/rag_answer_eval_questions."):
        return "manual_eval_dataset"
    if rel.startswith("datasets/rag_answer_eval_results."):
        return "scripts/run_rag_answer_eval.py"
    if rel.startswith("datasets/deepseek_rag_answer_eval_results."):
        return "scripts/run_deepseek_rag_answer_eval.py"
    if rel.startswith("datasets/rag_answer_smoke_test_results."):
        return "scripts/run_rag_answer_smoke_test.py"
    if rel == "review_inputs/human_review_decisions_template.csv":
        return "scripts/build_human_review_decision_template.py"
    if rel.startswith("review_inputs/human_review_session_decision_templates/"):
        return "scripts/build_human_review_session_decision_templates.py"
    if rel == "review_inputs/human_review_decisions.csv":
        return "manual_human_review_input"
    if rel.startswith("datasets/glossary."):
        return "scripts/build_glossary.py"
    if rel.startswith("published/"):
        if rel in {"published/bgp_knowledge_base.sqlite", "published/sqlite_schema.sql"}:
            return "scripts/build_sqlite_knowledge_base.py"
        if rel == "published/integrity_summary.json":
            return "scripts/build_published_integrity_report.py"
        if rel == "published/readiness_summary.json":
            return "scripts/build_readiness_report.py"
        if rel == "published/data_dictionary.json":
            return "scripts/build_data_dictionary.py"
        if rel in {"published/jsonld_context.json", "published/semantic_id_map.jsonl"}:
            return "scripts/build_semantic_identity.py"
        if rel in {"published/embedding_manifest.json", "published/rag_mock_vector_index.jsonl", "published/rag_retrieval_index.json"}:
            return "scripts/build_rag_indexes.py"
        return "scripts/build_published_knowledge_base.py"
    if rel.startswith("reports/published_knowledge_base_report.md"):
        return "scripts/build_published_knowledge_base.py"
    if rel.startswith("reports/sqlite_knowledge_base_report.md"):
        return "scripts/build_sqlite_knowledge_base.py"
    if rel.startswith("reports/query_examples_report.md"):
        return "scripts/build_query_examples.py"
    if rel.startswith("reports/published_integrity_report.md"):
        return "scripts/build_published_integrity_report.py"
    if rel.startswith("reports/readiness_report.md"):
        return "scripts/build_readiness_report.py"
    if rel.startswith("reports/data_dictionary_report.md"):
        return "scripts/build_data_dictionary.py"
    if rel.startswith("reports/parse_report.md"):
        return "scripts/parse_documents.py"
    if rel.startswith("reports/case_observation_report.md"):
        return "scripts/extract_case_observations.py"
    if rel.startswith("reports/case_observation_guides/"):
        return "scripts/build_case_observation_guides.py"
    if rel.startswith("reports/source_processing_status_report.md"):
        return "scripts/build_source_processing_status.py"
    if rel.startswith("reports/source_gap_queue_report.md"):
        return "scripts/build_source_gap_queue.py"
    if rel.startswith("reports/entity_review_queue_report.md"):
        return "scripts/build_entity_review_queue.py"
    if rel.startswith("reports/entity_source_evidence_report.md"):
        return "scripts/build_entity_source_evidence.py"
    if rel.startswith("reports/entity_review_packet_report.md"):
        return "scripts/build_entity_review_packets.py"
    if rel.startswith("reports/authoritative_source_requirements_report.md"):
        return "scripts/build_authoritative_source_requirements.py"
    if rel.startswith("reports/next_action_queue_report.md"):
        return "scripts/build_next_action_queue.py"
    if rel.startswith("reports/human_review_workbook_report.md"):
        return "scripts/build_human_review_workbook.py"
    if rel.startswith("reports/human_review_decision_template_report.md"):
        return "scripts/build_human_review_decision_template.py"
    if rel.startswith("reports/human_review_decision_audit_report.md"):
        return "scripts/build_human_review_decision_audit.py"
    if rel.startswith("reports/human_review_progress_report.md"):
        return "scripts/build_human_review_progress.py"
    if rel.startswith("reports/human_review_evidence_extracts_report.md"):
        return "scripts/build_human_review_evidence_extracts.py"
    if rel.startswith("reports/human_review_session_queue_report.md"):
        return "scripts/build_human_review_session_queue.py"
    if rel.startswith("reports/human_review_session_status_report.md"):
        return "scripts/build_human_review_session_status.py"
    if rel.startswith("reports/human_review_field_checklist_report.md"):
        return "scripts/build_human_review_field_checklist.py"
    if rel.startswith("reports/human_review_source_matrix_report.md"):
        return "scripts/build_human_review_source_matrix.py"
    if rel.startswith("reports/human_review_task_board_report.md"):
        return "scripts/build_human_review_task_board.py"
    if rel.startswith("reports/human_review_handoff_report.md"):
        return "scripts/build_human_review_handoff.py"
    if rel.startswith("reports/lifecycle_report.md"):
        return "scripts/build_lifecycle_report.py"
    if rel.startswith("reports/semantic_quality_report.md"):
        return "scripts/build_semantic_quality_report.py"
    if rel.startswith("reports/semantic_identity_report.md"):
        return "scripts/build_semantic_identity.py"
    if rel.startswith("reports/rag_readiness_report.md"):
        return "scripts/build_rag_readiness_report.py"
    if rel.startswith("reports/rag_answer_eval_report.md"):
        return "scripts/run_rag_answer_eval.py"
    if rel.startswith("reports/deepseek_rag_answer_eval_report.md"):
        return "scripts/run_deepseek_rag_answer_eval.py"
    if rel.startswith("reports/rag_answer_failure_analysis_report.md"):
        return "scripts/build_rag_answer_failure_analysis.py"
    if rel.startswith("reports/rag_answer_smoke_test_report.md"):
        return "scripts/run_rag_answer_smoke_test.py"
    if rel.startswith("reports/human_review_session_decision_templates_report.md"):
        return "scripts/build_human_review_session_decision_templates.py"
    if rel.startswith("reports/human_review_session_guides/"):
        return "scripts/build_human_review_session_guides.py"
    if rel.startswith("reports/human_review_decision_apply_report.md"):
        return "scripts/apply_human_review_decisions.py"
    if rel.startswith("reports/human_review_guides/"):
        return "scripts/build_human_review_guides.py"
    if rel.startswith("reports/glossary_report.md"):
        return "scripts/build_glossary.py"
    if rel.startswith("reports/coverage_report.md"):
        return "scripts/build_coverage_report.py"
    if rel.startswith("relationships/"):
        return "manual_seed_or_scripts/build_relationships.py"
    if rel.startswith("entities/"):
        return "manual_seed"
    if rel.startswith("schemas/"):
        return "manual_schema"
    if rel.startswith("scripts/"):
        return "manual_script"
    if rel.startswith("raw/"):
        return "manual_or_collected_source"
    if rel.startswith("config/") or rel.startswith("inventory/"):
        return "manual_config"
    if rel.startswith("reports/"):
        return "manual_or_prior_step_report"
    return "unknown"


def build_record(path):
    rel = relative_path(path)
    data = path.read_bytes()
    binary = is_binary_bytes(data)
    return {
        "artifact_path": rel,
        "artifact_group": rel.split("/", 1)[0],
        "extension": path.suffix.lower() or "none",
        "size_bytes": len(data),
        "line_count": line_count_for(data, binary),
        "is_binary": binary,
        "sha256": sha256_for_path(path),
        "generated_by": producer_for(rel),
    }


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
        f"- JSONL 输出：`datasets/artifact_manifest.jsonl`",
        f"- CSV 输出：`datasets/artifact_manifest.csv`",
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
