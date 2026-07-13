#!/usr/bin/env python3
import csv
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import jsonschema

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
ENTITY_DIR = paths.ENTITIES_DIR
CHUNK_DIR = paths.CHUNKS_DIR
DATASET_DIR = paths.DATASETS_DIR
PARSED_DIR = paths.PARSED_DIR
CLEANED_DIR = paths.CLEANED_DIR
RELATIONSHIP_FILE = paths.RELATIONSHIPS_DIR / "relationships.jsonl"
REPORT_FILE = paths.report_path("quality_report")


REQUIRED_FIELDS = {
    "BGPConcept": ["id", "entity_type", "name", "definition", "source_refs", "review_status"],
    "RoutingMechanism": ["id", "entity_type", "name", "definition", "source_refs"],
    "AnomalyType": ["id", "entity_type", "name", "definition", "required_evidence", "possible_false_positives", "source_refs"],
    "DataSource": ["id", "entity_type", "name", "description", "suitable_for", "limitations", "source_refs"],
    "DataField": ["id", "entity_type", "name", "meaning", "source_refs"],
    "EvidenceTemplate": ["id", "entity_type", "applies_to", "required_evidence", "false_positive_checks"],
    "FalsePositivePattern": ["id", "entity_type", "name", "definition", "applies_to", "checks", "source_refs"],
    "PaperMethod": ["id", "entity_type", "paper", "problem", "input", "process", "output", "source_refs"],
    "Case": ["id", "entity_type", "name", "event_type", "date", "source_refs"],
}

REQUIRED_CHUNK_FIELDS = [
    "chunk_id",
    "doc_id",
    "source_type",
    "title",
    "section_path",
    "chunk_type",
    "topics",
    "content",
    "source_ref",
    "language",
    "review_status",
]

REQUIRED_CASE_OBSERVATION_FIELDS = [
    "source_id",
    "title",
    "observation_type",
    "value",
    "context",
    "source_ref",
    "review_status",
]

REQUIRED_SOURCE_PROCESSING_STATUS_FIELDS = [
    "source_id",
    "source_type",
    "raw_status",
    "parseable",
    "parsed_status",
    "cleaned_status",
    "chunk_count",
    "case_observation_count",
    "processing_status",
]

REQUIRED_ARTIFACT_MANIFEST_FIELDS = [
    "artifact_path",
    "artifact_group",
    "extension",
    "size_bytes",
    "line_count",
    "is_binary",
    "sha256",
    "generated_by",
]

REQUIRED_PARSED_DOCUMENT_FIELDS = [
    "doc_id",
    "source_path",
    "source_format",
    "title",
    "sections",
]

REQUIRED_PARSED_SECTION_FIELDS = [
    "section_id",
    "heading",
    "content",
]

REQUIRED_GLOSSARY_FIELDS = [
    "term_id",
    "entity_id",
    "entity_type",
    "term",
    "definition",
    "category",
    "source_refs",
    "review_status",
    "generated_by",
]

REQUIRED_ENTITY_REVIEW_QUEUE_FIELDS = [
    "queue_id",
    "entity_id",
    "entity_type",
    "name",
    "review_status",
    "source_refs",
    "source_ref_count",
    "source_processing_statuses",
    "suggested_action",
    "generated_by",
]

REQUIRED_SOURCE_GAP_QUEUE_FIELDS = [
    "gap_id",
    "source_id",
    "source_type",
    "processing_status",
    "gap_type",
    "suggested_action",
    "generated_by",
]

REQUIRED_ENTITY_SOURCE_EVIDENCE_FIELDS = [
    "evidence_id",
    "entity_id",
    "entity_type",
    "entity_review_status",
    "source_id",
    "source_type",
    "source_status",
    "source_path",
    "parsed_path",
    "cleaned_path",
    "chunk_count",
    "chunk_sample_ids",
    "case_observation_count",
    "generated_by",
]

REQUIRED_ENTITY_REVIEW_PACKET_FIELDS = [
    "packet_id",
    "review_order",
    "entity_id",
    "entity_type",
    "display_name",
    "review_status",
    "review_bucket",
    "source_refs",
    "source_ref_count",
    "non_manual_source_count",
    "manual_note_source_count",
    "evidence_record_count",
    "total_chunk_count",
    "case_observation_count",
    "source_paths",
    "parsed_paths",
    "cleaned_paths",
    "chunk_sample_ids",
    "entity_payload",
    "review_checklist",
    "suggested_action",
    "generated_by",
]

REQUIRED_AUTHORITATIVE_SOURCE_REQUIREMENT_FIELDS = [
    "requirement_id",
    "entity_id",
    "entity_type",
    "display_name",
    "review_bucket",
    "current_source_refs",
    "current_source_ref_count",
    "requirement_type",
    "required_source_categories",
    "candidate_source_hints",
    "suggested_action",
    "llm_skip_note",
    "download_scope_note",
    "generated_by",
]

REQUIRED_NEXT_ACTION_FIELDS = [
    "action_id",
    "action_order",
    "priority",
    "action_type",
    "status",
    "scope_id",
    "display_name",
    "review_bucket",
    "related_dataset",
    "blocking_reason",
    "suggested_action",
    "needs_llm",
    "generated_by",
]

REQUIRED_HUMAN_REVIEW_WORKBOOK_FIELDS = [
    "workbook_id",
    "review_order",
    "review_batch",
    "priority",
    "entity_id",
    "entity_type",
    "display_name",
    "review_status",
    "review_bucket",
    "review_decision",
    "source_refs",
    "source_paths",
    "parsed_paths",
    "cleaned_paths",
    "chunk_sample_ids",
    "related_packet_id",
    "related_action_id",
    "needs_llm",
    "llm_skip_reason",
    "decision_instructions",
    "generated_by",
]

REQUIRED_HUMAN_REVIEW_DECISION_AUDIT_FIELDS = [
    "audit_id",
    "workbook_id",
    "entity_id",
    "entity_type",
    "display_name",
    "entity_file",
    "current_review_status",
    "review_decision",
    "target_review_status",
    "application_status",
    "can_apply",
    "blocking_reason",
    "needs_llm",
    "decision_source",
    "decision_reviewer",
    "decision_reviewed_at",
    "decision_note",
    "generated_by",
]

REQUIRED_HUMAN_REVIEW_DECISION_APPLY_PREVIEW_FIELDS = [
    "preview_id",
    "record_type",
    "run_mode",
    "application_status",
    "can_apply",
    "needs_llm",
    "count",
    "message",
    "generated_by",
]

REQUIRED_HUMAN_REVIEW_INPUT_VALIDATION_FIELDS = [
    "validation_id",
    "check_order",
    "input_path",
    "check_type",
    "status",
    "severity",
    "checked_count",
    "issue_count",
    "affected_entity_ids",
    "affected_rows",
    "message",
    "suggested_action",
    "needs_llm",
    "generated_by",
]

REQUIRED_HUMAN_REVIEW_PROGRESS_FIELDS = [
    "progress_id",
    "scope_type",
    "scope_value",
    "entity_count",
    "pending_count",
    "approved_count",
    "rejected_count",
    "unreviewed_decision_count",
    "approved_decision_count",
    "rejected_decision_count",
    "needs_source_decision_count",
    "needs_semantic_review_decision_count",
    "ready_to_apply_count",
    "manual_followup_count",
    "blocked_by_llm_count",
    "no_op_count",
    "completion_percent",
    "needs_llm_count",
    "next_step",
    "generated_by",
]

REQUIRED_HUMAN_REVIEW_EVIDENCE_EXTRACT_FIELDS = [
    "extract_id",
    "entity_id",
    "entity_type",
    "display_name",
    "review_order",
    "review_batch",
    "review_bucket",
    "chunk_rank",
    "chunk_id",
    "chunk_file",
    "doc_id",
    "source_ref",
    "chunk_type",
    "section_path",
    "matched_terms",
    "match_score",
    "excerpt",
    "excerpt_char_count",
    "needs_llm",
    "llm_skip_reason",
    "generated_by",
]

REQUIRED_HUMAN_REVIEW_SESSION_QUEUE_FIELDS = [
    "session_item_id",
    "session_id",
    "session_order",
    "within_session_order",
    "global_review_order",
    "entity_id",
    "entity_type",
    "display_name",
    "review_batch",
    "review_bucket",
    "review_status",
    "review_decision",
    "application_status",
    "queue_status",
    "source_refs",
    "cleaned_paths",
    "parsed_paths",
    "top_extract_ids",
    "top_chunk_ids",
    "top_match_scores",
    "decision_input_path",
    "next_step",
    "needs_llm",
    "generated_by",
]

REQUIRED_HUMAN_REVIEW_SESSION_STATUS_FIELDS = [
    "session_status_id",
    "session_id",
    "session_order",
    "item_count",
    "awaiting_human_review_count",
    "ready_to_apply_count",
    "manual_followup_count",
    "blocked_by_llm_count",
    "unreviewed_decision_count",
    "approved_decision_count",
    "rejected_decision_count",
    "needs_source_decision_count",
    "needs_semantic_review_decision_count",
    "completion_percent",
    "next_entity_id",
    "next_display_name",
    "decision_input_path",
    "needs_llm_count",
    "generated_by",
]

REQUIRED_HUMAN_REVIEW_SESSION_DECISION_TEMPLATE_FIELDS = [
    "entity_id",
    "review_decision",
    "reviewer",
    "reviewed_at",
    "decision_note",
    "session_id",
    "within_session_order",
    "entity_type",
    "display_name",
    "queue_status",
    "review_status",
    "review_batch",
    "review_bucket",
    "source_refs",
    "cleaned_paths",
    "parsed_paths",
    "top_extract_ids",
    "decision_instructions",
]

REQUIRED_HUMAN_REVIEW_FIELD_CHECKLIST_FIELDS = [
    "field_check_id",
    "session_id",
    "session_order",
    "within_session_order",
    "global_review_order",
    "field_order",
    "entity_id",
    "entity_type",
    "display_name",
    "entity_file",
    "field_name",
    "field_value_json",
    "field_value_preview",
    "verification_prompt",
    "decision_input_path",
    "review_decision",
    "needs_llm",
    "generated_by",
]

REQUIRED_HUMAN_REVIEW_SOURCE_MATRIX_FIELDS = [
    "source_matrix_id",
    "source_id",
    "source_title",
    "source_type",
    "source_path",
    "trust_level",
    "inventory_review_status",
    "processing_status",
    "raw_status",
    "parsed_status",
    "cleaned_status",
    "source_chunk_count",
    "evidence_record_count",
    "entity_count",
    "field_check_count",
    "session_ids",
    "entity_types",
    "sample_entity_ids",
    "cleaned_paths",
    "parsed_paths",
    "chunk_sample_ids",
    "decision_input_path",
    "generated_by",
]

REQUIRED_HUMAN_REVIEW_TASK_BOARD_FIELDS = [
    "task_id",
    "task_order",
    "task_type",
    "task_status",
    "title",
    "session_id",
    "source_id",
    "entity_id",
    "item_count",
    "field_check_count",
    "priority_reason",
    "primary_input",
    "secondary_input",
    "suggested_command",
    "write_command",
    "needs_llm",
    "generated_by",
]

REQUIRED_HUMAN_REVIEW_HANDOFF_FIELDS = [
    "handoff_id",
    "task_id",
    "task_order",
    "task_type",
    "handoff_status",
    "title",
    "primary_input",
    "primary_input_exists",
    "secondary_input",
    "secondary_input_exists",
    "expected_manual_output",
    "dry_run_command",
    "write_command",
    "verification_command",
    "can_write",
    "requires_human_decision",
    "needs_llm",
    "skip_note",
    "generated_by",
]

CLEANED_MANUAL_NOTES = {
    "data/corpus/cleaned/notes/context_summary.md": "context_2026",
}

ARTIFACT_SCAN_ROOTS = [
    paths.DATA_DIR,
    paths.METADATA_DIR,
    paths.PROJECT_ROOT / "src",
    paths.TESTS_DIR,
    paths.DOCS_DIR,
]

ARTIFACT_EXCLUDED_PATHS = {
    "data/derived/datasets/artifact_manifest.jsonl",
    "data/derived/datasets/artifact_manifest.csv",
    "data/generated/reports/publishing/artifact_manifest_report.md",
    "data/reports/gates/pipeline_report.md",
    "data/reports/gates/quality_report.md",
}

ALLOWED_REPORTS_TOP_LEVEL = {"README.md", "gates", "reference", "actions"}
ALLOWED_CURATED_REPORT_DIRS = {"gates", "reference", "actions"}

SCHEMA_BY_ENTITY_TYPE = {
    "AnomalyType": "anomaly_type.schema.json",
    "BGPConcept": "concept.schema.json",
    "Case": "case.schema.json",
    "DataField": "data_field.schema.json",
    "DataSource": "data_source.schema.json",
    "EvidenceTemplate": "evidence_template.schema.json",
    "FalsePositivePattern": "false_positive_pattern.schema.json",
    "PaperMethod": "paper.schema.json",
    "RoutingMechanism": "routing_mechanism.schema.json",
}


def load_jsonl(path):
    records = []
    errors = []
    if not path.exists():
        return records, errors
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            errors.append(f"{paths.rel(path)}:{lineno}: invalid JSON: {exc}")
    return records, errors


def load_json_file(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [f"{paths.rel(path)}: invalid JSON: {exc}"]


def load_sources():
    path = paths.INVENTORY_DIR / "sources.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_schema(filename):
    return json.loads((paths.SCHEMAS_DIR / filename).read_text(encoding="utf-8"))


def load_schemas():
    schemas = {
        "chunk": load_schema("chunk.schema.json"),
        "relationship": load_schema("relationship.schema.json"),
        "source": load_schema("source.schema.json"),
        "case_observation": load_schema("case_observation.schema.json"),
        "source_processing_status": load_schema("source_processing_status.schema.json"),
        "artifact_manifest": load_schema("artifact_manifest.schema.json"),
        "parsed_document": load_schema("parsed_document.schema.json"),
        "glossary_entry": load_schema("glossary_entry.schema.json"),
        "entity_review_queue": load_schema("entity_review_queue.schema.json"),
        "entity_source_evidence": load_schema("entity_source_evidence.schema.json"),
        "entity_review_packet": load_schema("entity_review_packet.schema.json"),
        "authoritative_source_requirement": load_schema("authoritative_source_requirement.schema.json"),
        "next_action": load_schema("next_action.schema.json"),
        "human_review_workbook_entry": load_schema("human_review_workbook_entry.schema.json"),
        "human_review_decision_audit": load_schema("human_review_decision_audit.schema.json"),
        "human_review_decision_apply_preview": load_schema("human_review_decision_apply_preview.schema.json"),
        "human_review_input_validation": load_schema("human_review_input_validation.schema.json"),
        "human_review_progress": load_schema("human_review_progress.schema.json"),
        "human_review_evidence_extract": load_schema("human_review_evidence_extract.schema.json"),
        "human_review_session_queue": load_schema("human_review_session_queue.schema.json"),
        "human_review_session_status": load_schema("human_review_session_status.schema.json"),
        "human_review_field_checklist": load_schema("human_review_field_checklist.schema.json"),
        "human_review_source_matrix": load_schema("human_review_source_matrix.schema.json"),
        "human_review_task_board": load_schema("human_review_task_board.schema.json"),
        "human_review_handoff": load_schema("human_review_handoff.schema.json"),
        "source_gap_queue": load_schema("source_gap_queue.schema.json"),
        "corpus_profile": load_schema("corpus_profile.schema.json"),
        "corpus_ocr_assessment": load_schema("corpus_ocr_assessment.schema.json"),
        "cleaning_v2_release_gate": load_schema("cleaning_v2_release_gate.schema.json"),
        "section_catalog": load_schema("section_catalog.schema.json"),
    }
    for entity_type, filename in SCHEMA_BY_ENTITY_TYPE.items():
        schemas[entity_type] = load_schema(filename)
    return schemas


def validate_stage_b_hierarchy(
    *, corpus_version, generated_chunks, published_chunks, sections,
    minimum_resolution_rate=0.99, minimum_adjacent_context_accuracy=0.98,
):
    """纯函数：验证阶段 B 的生成覆盖率与发布层级完整性。"""
    if corpus_version != "v2":
        return {"passed": True, "skipped": True, "reason": "v1 不适用阶段 B 层级门禁"}

    empty_samples = not generated_chunks and not published_chunks and not sections
    errors = []
    if not generated_chunks:
        errors.append("v2 generated chunk 样本为空")
    section_schema = load_schema("section_catalog.schema.json")
    section_by_id = {}
    sections_by_doc = defaultdict(list)
    for section in sections:
        section_id = section.get("section_id", "<missing>")
        try:
            jsonschema.validate(section, section_schema)
        except jsonschema.ValidationError as exc:
            errors.append(f"section schema 错误 {section_id}: {exc.message}")
        if section_id in section_by_id:
            errors.append(f"重复 section_id: {section_id}")
        section_by_id[section_id] = section
        sections_by_doc[section.get("doc_id")].append(section)

    for doc_id, doc_sections in sections_by_doc.items():
        ordered = sorted(doc_sections, key=lambda row: (row.get("section_order", -1), row.get("section_id", "")))
        for index, section in enumerate(ordered):
            section_id = section.get("section_id")
            expected_previous = ordered[index - 1].get("section_id") if index else None
            expected_next = ordered[index + 1].get("section_id") if index + 1 < len(ordered) else None
            if section.get("previous_section_id") != expected_previous or section.get("next_section_id") != expected_next:
                errors.append(f"section 邻接不互反: {section_id}")
            parent_id = section.get("parent_section_id")
            if parent_id:
                parent = section_by_id.get(parent_id)
                if parent is None:
                    errors.append(f"parent section 不存在: {section_id} -> {parent_id}")
                elif parent.get("doc_id") != doc_id:
                    errors.append(f"section parent 跨文档: {section_id} -> {parent_id}")
                elif section_id not in parent.get("child_section_ids", []):
                    errors.append(f"parent/child section 不互反: {section_id}")
            for child_id in section.get("child_section_ids", []):
                child = section_by_id.get(child_id)
                if child is None:
                    errors.append(f"child section 不存在: {section_id} -> {child_id}")
                elif child.get("doc_id") != doc_id:
                    errors.append(f"child section 跨文档: {section_id} -> {child_id}")
                elif child.get("parent_section_id") != section_id:
                    errors.append(f"child/parent section 不互反: {section_id} -> {child_id}")

    generated_by_id = {}
    for chunk in generated_chunks:
        chunk_id = chunk.get("chunk_id", "<missing>")
        if chunk_id in generated_by_id:
            errors.append(f"重复 generated chunk_id: {chunk_id}")
        generated_by_id[chunk_id] = chunk
        if chunk.get("hierarchy_status") not in {"resolved", "unresolved"}:
            errors.append(
                f"generated hierarchy_status 非法: {chunk_id} -> "
                f"{chunk.get('hierarchy_status')!r}"
            )
    resolved = [chunk for chunk in generated_chunks if chunk.get("hierarchy_status") == "resolved"]
    resolution_rate = len(resolved) / len(generated_chunks) if generated_chunks else 1.0
    if resolution_rate < minimum_resolution_rate:
        errors.append(f"生成层级解析率 {resolution_rate:.2%} 低于 99% 门槛")

    def validate_resolved(chunks, *, label):
        traceable = 0
        adjacent_eligible = 0
        adjacent_correct = 0
        by_parent = defaultdict(list)
        seen = set()
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id", "<missing>")
            if chunk_id in seen:
                errors.append(f"重复 {label} chunk_id: {chunk_id}")
            seen.add(chunk_id)
            required = ("parent_section_id", "chunk_order", "previous_chunk_id", "next_chunk_id", "source_ref", "source_block_ids")
            if chunk.get("hierarchy_status") != "resolved" or any(field not in chunk for field in required):
                errors.append(f"{label} chunk 非 resolved 或缺层级字段: {chunk_id}")
                continue
            section = section_by_id.get(chunk.get("parent_section_id"))
            if section is None:
                errors.append(f"{label} parent section 不存在: {chunk_id}")
                continue
            if section.get("doc_id") != chunk.get("doc_id"):
                errors.append(f"{label} chunk/section 跨文档: {chunk_id}")
                continue
            if chunk_id not in section.get("child_chunk_ids", []):
                errors.append(f"{label} section/chunk 不一致: {chunk_id}")
                continue
            if not chunk.get("source_ref") or not chunk.get("source_block_ids"):
                errors.append(f"{label} source_ref/source_block 追溯为空: {chunk_id}")
                continue
            by_parent[chunk["parent_section_id"]].append(chunk)
            traceable += 1
        for parent_id, siblings in by_parent.items():
            orders = [chunk.get("chunk_order") for chunk in siblings]
            if len(set(orders)) != len(orders) or sorted(orders) != list(range(len(siblings))):
                errors.append(f"{label} chunk_order 不连续或重复: {parent_id}")
                continue
            ordered = sorted(siblings, key=lambda chunk: chunk["chunk_order"])
            for index, chunk in enumerate(ordered):
                previous = ordered[index - 1]["chunk_id"] if index else None
                following = ordered[index + 1]["chunk_id"] if index + 1 < len(ordered) else None
                adjacent_eligible += 2
                adjacent_correct += chunk.get("previous_chunk_id") == previous
                adjacent_correct += chunk.get("next_chunk_id") == following
        return traceable, adjacent_correct, adjacent_eligible

    _, adjacent_correct, adjacent_eligible = validate_resolved(resolved, label="generated")
    adjacent_accuracy = adjacent_correct / adjacent_eligible if adjacent_eligible else 1.0
    if adjacent_accuracy < minimum_adjacent_context_accuracy:
        errors.append(
            f"相邻上下文正确率 {adjacent_accuracy:.2%} 低于 "
            f"{minimum_adjacent_context_accuracy:.2%} 门槛"
        )

    published_traceable, _, _ = validate_resolved(published_chunks, label="published")
    published_rate = published_traceable / len(published_chunks) if published_chunks else 1.0
    if published_rate != 1.0:
        errors.append(f"published 父级/来源追溯率必须为 100%，当前 {published_rate:.2%}")

    resolved_ids = {chunk.get("chunk_id") for chunk in resolved}
    published_ids = {chunk.get("chunk_id") for chunk in published_chunks}
    if published_ids != resolved_ids:
        errors.append(
            "published chunk_id 未完整覆盖 resolved chunks: "
            f"缺失={sorted(resolved_ids - published_ids)}，多余={sorted(published_ids - resolved_ids)}"
        )
    for section in sections:
        for chunk_id in section.get("child_chunk_ids", []):
            chunk = generated_by_id.get(chunk_id)
            if chunk_id not in resolved_ids or chunk is None or chunk.get("parent_section_id") != section.get("section_id"):
                errors.append(f"section child_chunk_ids 与 generated chunk 不一致: {section.get('section_id')} -> {chunk_id}")

    return {
        "passed": not errors,
        "skipped": False,
        "generated_count": len(generated_chunks),
        "resolved_count": len(resolved),
        "unresolved_count": len(generated_chunks) - len(resolved),
        "resolution_rate": None if empty_samples else resolution_rate,
        "adjacent_context_eligible_count": adjacent_eligible,
        "adjacent_context_correct_count": adjacent_correct,
        "adjacent_context_accuracy": None if empty_samples else adjacent_accuracy,
        "published_count": len(published_chunks),
        "published_traceability_rate": None if empty_samples else published_rate,
        "errors": errors,
    }


def corpus_profile_blocking_issues(records):
    return sorted(
        f"{record.get('doc_id', '<missing doc_id>')} -> {issue}"
        for record in records
        for issue in record.get("blocking_issues", [])
    )


def validate_cleaning_v2_release_gate(record, schema):
    return validate_schema(
        record,
        schema,
        "cleaning_v2_release_gate",
        allow_empty_required=True,
    )


def parse_output_dirs(raw_path):
    rel = raw_path.as_posix()
    if rel.startswith("data/sources/raw/standards/"):
        return "standards", "standards"
    if rel.startswith("data/sources/raw/data_docs/") or rel.startswith("data/sources/raw/tools_docs/"):
        return "data_docs", "data_docs"
    if rel.startswith("data/sources/raw/papers/"):
        return "papers", "papers"
    if rel.startswith("data/sources/raw/cases/"):
        return "cases", "cases"
    return None, None


def is_parseable_raw_path(raw_path):
    return raw_path.suffix in {".txt", ".html", ".pdf", ".yaml", ".yml"}


def missing_or_empty(record, field):
    value = record.get(field)
    return value is None or value == "" or value == [] or value == {}


def type_matches(value, expected_type):
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    return True


def validate_schema(record, schema, label, allow_empty_required=False):
    errors = []
    if schema.get("type") and not type_matches(record, schema["type"]):
        errors.append(f"{label}: record type is not {schema['type']}")
        return errors

    for field in schema.get("required", []):
        if (
            field not in record
            or record[field] is None
            or (not allow_empty_required and missing_or_empty(record, field))
        ):
            errors.append(f"{label}: missing required {field}")

    properties = schema.get("properties", {})
    for field, rules in properties.items():
        if field not in record or record[field] is None:
            continue
        value = record[field]
        if "const" in rules and value != rules["const"]:
            errors.append(f"{label}: {field} expected const {rules['const']}, got {value}")
        if "enum" in rules and value not in rules["enum"]:
            errors.append(f"{label}: {field} value {value} not in enum")
        if "type" in rules and not type_matches(value, rules["type"]):
            errors.append(f"{label}: {field} type is not {rules['type']}")
            continue
        if rules.get("type") == "array" and "items" in rules:
            item_type = rules["items"].get("type")
            if item_type:
                for index, item in enumerate(value):
                    if not type_matches(item, item_type):
                        errors.append(f"{label}: {field}[{index}] type is not {item_type}")
    return errors


def source_path_from_ref(source_ref):
    if not source_ref:
        return None
    path_part = source_ref.split("#", 1)[0].split(":", 1)[0]
    if not path_part or path_part.startswith(("http://", "https://")):
        return None
    if path_part.startswith("../"):
        legacy_path = (ROOT / path_part).resolve()
        try:
            legacy_path.relative_to(ROOT.parent.resolve())
        except ValueError:
            return None
        return legacy_path
    return paths.resolve_logical_path(path_part)


def relative_path(path):
    return paths.rel(path)


def iter_artifact_paths():
    for base in ARTIFACT_SCAN_ROOTS:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if "__pycache__" in path.parts:
                continue
            if not path.is_file():
                continue
            rel = relative_path(path)
            if rel in ARTIFACT_EXCLUDED_PATHS:
                continue
            yield path


def report_policy_match(rel):
    for report_id, meta in paths.report_policy().items():
        policy_path = meta["path"]
        if rel == policy_path or rel.startswith(f"{policy_path}/"):
            return report_id, meta
    return None, None


def check_report_policy():
    policy = paths.report_policy()
    registered_paths = {meta["path"] for meta in policy.values()}
    layout_violations = []
    missing_policy_paths = []
    unregistered_reports = []
    empty_old_report_dirs = []
    invalid_generated_categories = []

    if paths.REPORTS_DIR.exists():
        for child in sorted(paths.REPORTS_DIR.iterdir()):
            if child.name not in ALLOWED_REPORTS_TOP_LEVEL:
                layout_violations.append(paths.rel(child))
        for directory_name in ALLOWED_CURATED_REPORT_DIRS:
            directory = paths.REPORTS_DIR / directory_name
            if not directory.exists():
                layout_violations.append(f"{paths.rel(directory)} missing")
                continue
            for child in sorted(directory.iterdir()):
                if child.is_dir():
                    layout_violations.append(f"{paths.rel(child)} must not be a nested curated report directory")
        for path in sorted(paths.REPORTS_DIR.rglob("*")):
            if not path.is_file() or path.name == "README.md":
                continue
            rel = paths.rel(path)
            report_id, meta = report_policy_match(rel)
            if not report_id:
                unregistered_reports.append(rel)
                continue
            if meta.get("retention") != "curated":
                layout_violations.append(f"{rel} registered retention is {meta.get('retention')}, expected curated")

    if paths.GENERATED_REPORTS_DIR.exists():
        allowed_categories = {
            meta["category"]
            for meta in policy.values()
            if meta.get("retention") in {"generated", "snapshot"}
        }
        for child in sorted(paths.GENERATED_REPORTS_DIR.iterdir()):
            if child.is_dir() and child.name not in allowed_categories:
                invalid_generated_categories.append(paths.rel(child))
        for path in sorted(paths.GENERATED_REPORTS_DIR.rglob("*")):
            if not path.is_file():
                continue
            rel = paths.rel(path)
            report_id, _ = report_policy_match(rel)
            if not report_id:
                unregistered_reports.append(rel)

    for report_id, meta in sorted(policy.items()):
        rel = meta["path"]
        path = paths.resolve_logical_path(rel)
        if path.exists():
            continue
        if not path.suffix:
            empty_old_report_dirs.append(f"{report_id} -> {rel}")
        else:
            missing_policy_paths.append(f"{report_id} -> {rel}")

    return {
        "registered_paths": registered_paths,
        "layout_violations": layout_violations,
        "missing_policy_paths": missing_policy_paths,
        "unregistered_reports": unregistered_reports,
        "empty_old_report_dirs": empty_old_report_dirs,
        "invalid_generated_categories": invalid_generated_categories,
    }


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


def first_content_line(lines):
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                lines = lines[index + 1:]
                break
    return next((line for line in lines if line.strip()), "")


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


def main():
    schemas = load_schemas()
    records = []
    errors = []
    by_file_counts = {}
    for path in sorted(ENTITY_DIR.glob("*.jsonl")):
        loaded, file_errors = load_jsonl(path)
        records.extend(loaded)
        errors.extend(file_errors)
        by_file_counts[path.name] = len(loaded)

    relationships, relationship_errors = load_jsonl(RELATIONSHIP_FILE)
    errors.extend(relationship_errors)

    chunk_records = []
    chunk_errors = []
    chunk_file_counts = {}
    for path in sorted(CHUNK_DIR.glob("*.jsonl")):
        loaded, file_errors = load_jsonl(path)
        chunk_records.extend(loaded)
        chunk_errors.extend(file_errors)
        chunk_file_counts[path.name] = len(loaded)
    errors.extend(chunk_errors)

    case_observations, case_observation_errors = load_jsonl(DATASET_DIR / "case_observations.jsonl")
    errors.extend(case_observation_errors)

    source_processing_statuses, source_processing_status_errors = load_jsonl(DATASET_DIR / "source_processing_status.jsonl")
    errors.extend(source_processing_status_errors)

    source_gap_queue_items, source_gap_queue_errors = load_jsonl(DATASET_DIR / "source_gap_queue.jsonl")
    errors.extend(source_gap_queue_errors)

    entity_review_queue_items, entity_review_queue_errors = load_jsonl(DATASET_DIR / "entity_review_queue.jsonl")
    errors.extend(entity_review_queue_errors)

    entity_source_evidence_items, entity_source_evidence_errors = load_jsonl(DATASET_DIR / "entity_source_evidence.jsonl")
    errors.extend(entity_source_evidence_errors)

    entity_review_packet_items, entity_review_packet_errors = load_jsonl(DATASET_DIR / "entity_review_packets.jsonl")
    errors.extend(entity_review_packet_errors)

    authoritative_source_requirements, authoritative_source_requirement_errors = load_jsonl(
        DATASET_DIR / "authoritative_source_requirements.jsonl"
    )
    errors.extend(authoritative_source_requirement_errors)

    next_action_items, next_action_errors = load_jsonl(DATASET_DIR / "next_action_queue.jsonl")
    errors.extend(next_action_errors)

    human_review_workbook_items, human_review_workbook_errors = load_jsonl(DATASET_DIR / "human_review_workbook.jsonl")
    errors.extend(human_review_workbook_errors)

    human_review_decision_audit_items, human_review_decision_audit_errors = load_jsonl(
        DATASET_DIR / "human_review_decision_audit.jsonl"
    )
    errors.extend(human_review_decision_audit_errors)

    human_review_decision_apply_preview_items, human_review_decision_apply_preview_errors = load_jsonl(
        DATASET_DIR / "human_review_decision_apply_preview.jsonl"
    )
    errors.extend(human_review_decision_apply_preview_errors)

    human_review_input_validation_items, human_review_input_validation_errors = load_jsonl(
        DATASET_DIR / "human_review_input_validation.jsonl"
    )
    errors.extend(human_review_input_validation_errors)

    human_review_progress_items, human_review_progress_errors = load_jsonl(
        DATASET_DIR / "human_review_progress.jsonl"
    )
    errors.extend(human_review_progress_errors)

    human_review_evidence_extract_items, human_review_evidence_extract_errors = load_jsonl(
        DATASET_DIR / "human_review_evidence_extracts.jsonl"
    )
    errors.extend(human_review_evidence_extract_errors)

    human_review_session_queue_items, human_review_session_queue_errors = load_jsonl(
        DATASET_DIR / "human_review_session_queue.jsonl"
    )
    errors.extend(human_review_session_queue_errors)

    human_review_session_status_items, human_review_session_status_errors = load_jsonl(
        DATASET_DIR / "human_review_session_status.jsonl"
    )
    errors.extend(human_review_session_status_errors)

    human_review_field_checklist_items, human_review_field_checklist_errors = load_jsonl(
        DATASET_DIR / "human_review_field_checklist.jsonl"
    )
    errors.extend(human_review_field_checklist_errors)

    human_review_source_matrix_items, human_review_source_matrix_errors = load_jsonl(
        DATASET_DIR / "human_review_source_matrix.jsonl"
    )
    errors.extend(human_review_source_matrix_errors)

    human_review_task_board_items, human_review_task_board_errors = load_jsonl(
        DATASET_DIR / "human_review_task_board.jsonl"
    )
    errors.extend(human_review_task_board_errors)

    human_review_handoff_items, human_review_handoff_errors = load_jsonl(
        DATASET_DIR / "human_review_handoff.jsonl"
    )
    errors.extend(human_review_handoff_errors)

    glossary_entries, glossary_errors = load_jsonl(DATASET_DIR / "glossary.jsonl")
    errors.extend(glossary_errors)

    artifact_manifest_records, artifact_manifest_errors = load_jsonl(DATASET_DIR / "artifact_manifest.jsonl")
    errors.extend(artifact_manifest_errors)

    corpus_profiles, corpus_profile_errors = load_jsonl(DATASET_DIR / "corpus_profile.jsonl")
    errors.extend(corpus_profile_errors)
    corpus_ocr_assessments, corpus_ocr_errors = load_jsonl(
        DATASET_DIR / "corpus_ocr_assessments.jsonl"
    )
    errors.extend(corpus_ocr_errors)
    cleaning_v2_release_gate, cleaning_v2_release_gate_errors = load_json_file(
        DATASET_DIR / "cleaning_v2_release_gate.json"
    )
    errors.extend(cleaning_v2_release_gate_errors)

    parsed_documents = []
    parsed_document_counts_by_subdir = Counter()
    for path in sorted(PARSED_DIR.glob("*/*.json")):
        loaded, file_errors = load_json_file(path)
        errors.extend(file_errors)
        if loaded is not None:
            parsed_documents.append((path, loaded))
            parsed_document_counts_by_subdir[path.parent.name] += 1

    cleaned_documents = sorted(CLEANED_DIR.glob("*/*.md"))
    cleaned_document_counts_by_subdir = Counter(path.parent.name for path in cleaned_documents)

    ids = [record.get("id") for record in records if record.get("id")]
    id_counts = Counter(ids)
    duplicate_ids = sorted([id_ for id_, count in id_counts.items() if count > 1])
    id_set = set(ids)
    source_rows = load_sources()
    source_ids = {row["source_id"] for row in source_rows}
    source_id_counts = Counter(row["source_id"] for row in source_rows if row.get("source_id"))
    duplicate_source_ids = sorted([id_ for id_, count in source_id_counts.items() if count > 1])

    inventory_missing_paths = []
    inventory_missing_raw_files = []
    inventory_parseable_missing_parsed = []
    inventory_parseable_missing_cleaned = []
    inventory_paths = set()
    for row in source_rows:
        source_id = row.get("source_id", "<missing source_id>")
        source_path = row.get("path", "")
        if not source_path:
            inventory_missing_paths.append(source_id)
            continue
        resolved = paths.resolve_logical_path(source_path)
        if not resolved.exists():
            inventory_missing_raw_files.append(f"{source_id} -> {source_path}")
            continue
        try:
            rel_path = Path(paths.rel(resolved))
        except ValueError:
            continue
        if rel_path.as_posix().startswith("data/sources/raw/"):
            inventory_paths.add(rel_path.as_posix())
            if is_parseable_raw_path(rel_path):
                parsed_subdir, cleaned_subdir = parse_output_dirs(rel_path)
                if parsed_subdir and not (paths.PARSED_DIR / parsed_subdir / f"{rel_path.stem}.json").exists():
                    inventory_parseable_missing_parsed.append(f"{source_id} -> {rel_path.as_posix()}")
                if cleaned_subdir and not (paths.CLEANED_DIR / cleaned_subdir / f"{rel_path.stem}.md").exists():
                    inventory_parseable_missing_cleaned.append(f"{source_id} -> {rel_path.as_posix()}")

    raw_files = {
        paths.rel(path)
        for path in (paths.RAW_DIR).glob("*/*")
        if path.is_file()
    }
    raw_files_without_inventory = sorted(raw_files - inventory_paths)

    schema_errors = []
    for index, record in enumerate(corpus_profiles, start=1):
        schema_errors.extend(validate_schema(
            record, schemas["corpus_profile"], f"corpus_profile:{index}",
            allow_empty_required=True,
        ))
    for index, record in enumerate(corpus_ocr_assessments, start=1):
        schema_errors.extend(validate_schema(
            record, schemas["corpus_ocr_assessment"], f"corpus_ocr_assessment:{index}",
            allow_empty_required=True,
        ))
    corpus_profile_blockers = corpus_profile_blocking_issues(corpus_profiles)
    cleaning_v2_release_gate_blockers = []
    if cleaning_v2_release_gate is not None:
        schema_errors.extend(validate_cleaning_v2_release_gate(
            cleaning_v2_release_gate, schemas["cleaning_v2_release_gate"]
        ))
        if not cleaning_v2_release_gate.get("passed"):
            cleaning_v2_release_gate_blockers = list(
                cleaning_v2_release_gate.get("blocking_issues", [])
            )
    parsed_document_missing_fields = []
    parsed_document_duplicate_doc_ids = []
    parsed_document_unknown_doc_ids = []
    parsed_document_missing_source_paths = []
    parsed_document_unregistered_source_paths = []
    parsed_document_path_mismatches = []
    parsed_document_empty_sections = []
    parsed_section_missing_fields = []
    parsed_section_empty_content = []
    parsed_doc_ids = []
    for path, record in parsed_documents:
        label = paths.rel(path)
        schema_errors.extend(validate_schema(record, schemas["parsed_document"], label))
        for field in REQUIRED_PARSED_DOCUMENT_FIELDS:
            if missing_or_empty(record, field):
                parsed_document_missing_fields.append(f"{label} missing {field}")
        doc_id = record.get("doc_id")
        source_path = record.get("source_path")
        if doc_id:
            parsed_doc_ids.append(doc_id)
            if doc_id not in source_ids:
                parsed_document_unknown_doc_ids.append(f"{label} -> {doc_id}")
            if path.stem != doc_id:
                parsed_document_path_mismatches.append(f"{label}: filename stem != doc_id {doc_id}")
        if source_path:
            resolved = paths.resolve_logical_path(source_path)
            if not resolved.exists():
                parsed_document_missing_source_paths.append(f"{label} -> {source_path}")
            elif source_path not in inventory_paths:
                parsed_document_unregistered_source_paths.append(f"{label} -> {source_path}")
        sections = record.get("sections")
        if not isinstance(sections, list) or not sections:
            parsed_document_empty_sections.append(label)
            continue
        for section_index, section in enumerate(sections, start=1):
            section_label = f"{label}#section:{section_index}"
            if not isinstance(section, dict):
                parsed_section_missing_fields.append(f"{section_label} is not object")
                continue
            for field in REQUIRED_PARSED_SECTION_FIELDS:
                if missing_or_empty(section, field):
                    parsed_section_missing_fields.append(f"{section_label} missing {field}")
            content = section.get("content", "")
            if isinstance(content, str) and not content.strip():
                parsed_section_empty_content.append(section_label)
    parsed_doc_id_counts = Counter(parsed_doc_ids)
    parsed_document_duplicate_doc_ids = sorted(
        doc_id for doc_id, count in parsed_doc_id_counts.items() if count > 1
    )
    parsed_document_titles = {
        record.get("doc_id"): record.get("title", "")
        for _, record in parsed_documents
        if record.get("doc_id")
    }

    cleaned_document_missing_heading = []
    cleaned_document_empty_body = []
    cleaned_document_unknown_doc_ids = []
    cleaned_document_missing_parsed = []
    cleaned_document_unexpected_manual_notes = []
    cleaned_document_title_mismatches = []
    cleaned_document_replacement_chars = []
    cleaned_doc_ids = []
    for path in cleaned_documents:
        rel = paths.rel(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        first_line = first_content_line(lines)
        if not first_line.startswith("# "):
            cleaned_document_missing_heading.append(rel)
        body = "\n".join(lines[1:]).strip() if lines else ""
        if not body:
            cleaned_document_empty_body.append(rel)
        if "\ufffd" in text:
            cleaned_document_replacement_chars.append(rel)

        if rel in CLEANED_MANUAL_NOTES:
            doc_id = CLEANED_MANUAL_NOTES[rel]
            cleaned_doc_ids.append(doc_id)
            if doc_id not in source_ids:
                cleaned_document_unknown_doc_ids.append(f"{rel} -> {doc_id}")
            continue
        if path.parent.name == "notes":
            cleaned_document_unexpected_manual_notes.append(rel)
            continue

        doc_id = path.stem
        cleaned_doc_ids.append(doc_id)
        if doc_id not in source_ids:
            cleaned_document_unknown_doc_ids.append(f"{rel} -> {doc_id}")
        parsed_path = PARSED_DIR / path.parent.name / f"{doc_id}.json"
        if not parsed_path.exists():
            cleaned_document_missing_parsed.append(f"{rel} -> {paths.rel(parsed_path)}")
            continue
        parsed_title = parsed_document_titles.get(doc_id, "")
        if parsed_title and first_line != f"# {parsed_title}":
            cleaned_document_title_mismatches.append(f"{rel}: heading != parsed title")
    cleaned_doc_id_counts = Counter(cleaned_doc_ids)
    cleaned_document_duplicate_doc_ids = sorted(
        doc_id for doc_id, count in cleaned_doc_id_counts.items() if count > 1
    )

    missing_fields = []
    missing_source_refs = []
    unknown_source_refs = []
    pending_by_type = defaultdict(int)
    counts_by_type = defaultdict(int)

    for record in records:
        entity_type = record.get("entity_type", "UNKNOWN")
        counts_by_type[entity_type] += 1
        schema = schemas.get(entity_type)
        if schema:
            schema_errors.extend(validate_schema(record, schema, record.get("id", "<missing id>")))
        else:
            schema_errors.append(f"{record.get('id', '<missing id>')}: missing schema for entity_type {entity_type}")
        if record.get("review_status") == "pending":
            pending_by_type[entity_type] += 1
        for field in REQUIRED_FIELDS.get(entity_type, ["id", "entity_type"]):
            if missing_or_empty(record, field):
                missing_fields.append(f"{record.get('id', '<missing id>')} missing {field}")
        refs = record.get("source_refs", [])
        if "source_refs" in REQUIRED_FIELDS.get(entity_type, []) and not refs:
            missing_source_refs.append(record.get("id", "<missing id>"))
        for ref in refs:
            if ref not in source_ids:
                unknown_source_refs.append(f"{record.get('id', '<missing id>')} -> {ref}")

    entity_type_by_id = {
        record.get("id"): record.get("entity_type")
        for record in records
        if record.get("id")
    }
    source_status_by_id = {
        record.get("source_id"): record.get("processing_status")
        for record in source_processing_statuses
        if record.get("source_id")
    }
    incomplete_source_ids = {
        record.get("source_id")
        for record in source_processing_statuses
        if record.get("source_id") and record.get("processing_status") not in {"complete_deterministic", "manual_note"}
    }
    source_gap_queue_missing_fields = []
    source_gap_queue_duplicate_gap_ids = []
    source_gap_queue_unknown_source_ids = []
    source_gap_queue_status_mismatches = []
    source_gap_queue_missing_incomplete_sources = []
    source_gap_ids = []
    source_gap_source_ids = []
    for index, record in enumerate(source_gap_queue_items, start=1):
        record_label = f"source_gap_queue:{index}"
        schema_errors.extend(validate_schema(record, schemas["source_gap_queue"], record_label))
        for field in REQUIRED_SOURCE_GAP_QUEUE_FIELDS:
            if missing_or_empty(record, field):
                source_gap_queue_missing_fields.append(f"{record_label} missing {field}")
        gap_id = record.get("gap_id")
        source_id = record.get("source_id")
        if gap_id:
            source_gap_ids.append(gap_id)
        if source_id:
            source_gap_source_ids.append(source_id)
            if source_id not in source_ids:
                source_gap_queue_unknown_source_ids.append(f"{record_label} -> {source_id}")
            elif source_status_by_id.get(source_id) != record.get("processing_status"):
                source_gap_queue_status_mismatches.append(f"{record_label} -> {source_id}")
    source_gap_id_counts = Counter(source_gap_ids)
    source_gap_queue_duplicate_gap_ids = sorted(
        gap_id for gap_id, count in source_gap_id_counts.items() if count > 1
    )
    source_gap_queue_missing_incomplete_sources = sorted(
        incomplete_source_ids - set(source_gap_source_ids)
    )

    pending_entity_ids = {
        record.get("id")
        for record in records
        if record.get("id") and record.get("review_status") == "pending"
    }
    entity_review_queue_missing_fields = []
    entity_review_queue_duplicate_queue_ids = []
    entity_review_queue_unknown_entity_ids = []
    entity_review_queue_entity_type_mismatches = []
    entity_review_queue_unknown_source_refs = []
    entity_review_queue_source_count_mismatches = []
    entity_review_queue_status_mismatches = []
    entity_review_queue_missing_pending_entities = []
    queue_ids = []
    queue_entity_ids = []
    entity_review_status_by_id = {
        record.get("id"): record.get("review_status")
        for record in records
        if record.get("id")
    }
    for index, record in enumerate(entity_review_queue_items, start=1):
        record_label = f"entity_review_queue:{index}"
        schema_errors.extend(validate_schema(record, schemas["entity_review_queue"], record_label))
        for field in REQUIRED_ENTITY_REVIEW_QUEUE_FIELDS:
            if missing_or_empty(record, field):
                entity_review_queue_missing_fields.append(f"{record_label} missing {field}")
        queue_id = record.get("queue_id")
        entity_id = record.get("entity_id")
        if queue_id:
            queue_ids.append(queue_id)
        if entity_id:
            queue_entity_ids.append(entity_id)
            if entity_id not in id_set:
                entity_review_queue_unknown_entity_ids.append(f"{record_label} -> {entity_id}")
            elif record.get("entity_type") != entity_type_by_id.get(entity_id):
                entity_review_queue_entity_type_mismatches.append(f"{record_label} -> {entity_id}")
            if entity_review_status_by_id.get(entity_id) != record.get("review_status"):
                entity_review_queue_status_mismatches.append(f"{record_label} -> {entity_id}")
        source_refs = record.get("source_refs", [])
        if isinstance(source_refs, list):
            if record.get("source_ref_count") != len(source_refs):
                entity_review_queue_source_count_mismatches.append(f"{record_label}: source_ref_count mismatch")
            for ref in source_refs:
                if ref not in source_ids:
                    entity_review_queue_unknown_source_refs.append(f"{record_label} -> {ref}")
            expected_blocked = sorted(
                ref
                for ref in source_refs
                if source_status_by_id.get(ref) not in {"complete_deterministic", "manual_note"}
            )
            actual_blocked = sorted(record.get("blocked_source_refs", []))
            if expected_blocked != actual_blocked:
                entity_review_queue_status_mismatches.append(f"{record_label}: blocked_source_refs mismatch")
    queue_id_counts = Counter(queue_ids)
    entity_review_queue_duplicate_queue_ids = sorted(
        queue_id for queue_id, count in queue_id_counts.items() if count > 1
    )
    entity_review_queue_missing_pending_entities = sorted(pending_entity_ids - set(queue_entity_ids))

    glossary_missing_fields = []
    glossary_duplicate_term_ids = []
    glossary_unknown_entity_ids = []
    glossary_entity_type_mismatches = []
    glossary_unknown_source_refs = []
    glossary_missing_entity_ids = []
    glossary_term_ids = []
    glossary_entity_ids = []
    for index, record in enumerate(glossary_entries, start=1):
        record_label = f"glossary:{index}"
        schema_errors.extend(validate_schema(record, schemas["glossary_entry"], record_label))
        for field in REQUIRED_GLOSSARY_FIELDS:
            if missing_or_empty(record, field):
                glossary_missing_fields.append(f"{record_label} missing {field}")
        term_id = record.get("term_id")
        entity_id = record.get("entity_id")
        if term_id:
            glossary_term_ids.append(term_id)
        if entity_id:
            glossary_entity_ids.append(entity_id)
            if entity_id not in id_set:
                glossary_unknown_entity_ids.append(f"{record_label} -> {entity_id}")
            elif record.get("entity_type") != entity_type_by_id.get(entity_id):
                glossary_entity_type_mismatches.append(f"{record_label} -> {entity_id}")
        for ref in record.get("source_refs", []):
            if ref not in source_ids:
                glossary_unknown_source_refs.append(f"{record_label} -> {ref}")
    glossary_term_id_counts = Counter(glossary_term_ids)
    glossary_duplicate_term_ids = sorted(
        term_id for term_id, count in glossary_term_id_counts.items() if count > 1
    )
    glossary_missing_entity_ids = sorted(id_set - set(glossary_entity_ids))

    chunk_ids = [record.get("chunk_id") for record in chunk_records if record.get("chunk_id")]
    chunk_id_counts = Counter(chunk_ids)
    duplicate_chunk_ids = sorted([id_ for id_, count in chunk_id_counts.items() if count > 1])
    chunk_id_set = set(chunk_ids)
    chunk_by_id = {
        record.get("chunk_id"): record
        for record in chunk_records
        if record.get("chunk_id")
    }
    chunk_counts_by_doc_id = Counter(
        record.get("doc_id")
        for record in chunk_records
        if record.get("doc_id")
    )
    missing_chunk_fields = []
    unknown_chunk_doc_ids = []
    empty_chunk_content = []
    missing_chunk_source_paths = []
    oversized_chunks = []

    for record in chunk_records:
        chunk_id = record.get("chunk_id", "<missing chunk_id>")
        schema_errors.extend(validate_schema(record, schemas["chunk"], chunk_id))
        for field in REQUIRED_CHUNK_FIELDS:
            if missing_or_empty(record, field):
                missing_chunk_fields.append(f"{chunk_id} missing {field}")
        doc_id = record.get("doc_id")
        if doc_id and doc_id not in source_ids:
            unknown_chunk_doc_ids.append(f"{chunk_id} -> {doc_id}")
        content = record.get("content", "")
        if isinstance(content, str) and not content.strip():
            empty_chunk_content.append(chunk_id)
        if isinstance(content, str) and len(content) > 2500:
            oversized_chunks.append(f"{chunk_id}: {len(content)} chars")
        source_path = source_path_from_ref(record.get("source_ref"))
        if source_path and not source_path.exists():
            missing_chunk_source_paths.append(f"{chunk_id} -> {record.get('source_ref')}")

    expected_entity_source_pairs = {
        (record.get("id"), str(ref))
        for record in records
        for ref in record.get("source_refs", [])
        if record.get("id") and str(ref).strip()
    }
    entity_source_evidence_missing_fields = []
    entity_source_evidence_duplicate_ids = []
    entity_source_evidence_unknown_entity_ids = []
    entity_source_evidence_entity_type_mismatches = []
    entity_source_evidence_unknown_source_ids = []
    entity_source_evidence_status_mismatches = []
    entity_source_evidence_chunk_count_mismatches = []
    entity_source_evidence_unknown_chunk_sample_ids = []
    entity_source_evidence_missing_paths = []
    entity_source_evidence_unexpected_pairs = []
    entity_source_evidence_missing_pairs = []
    evidence_ids = []
    evidence_pairs = []
    for index, record in enumerate(entity_source_evidence_items, start=1):
        record_label = f"entity_source_evidence:{index}"
        schema_errors.extend(validate_schema(record, schemas["entity_source_evidence"], record_label))
        for field in REQUIRED_ENTITY_SOURCE_EVIDENCE_FIELDS:
            if missing_or_empty(record, field) and field not in {"source_path", "parsed_path", "cleaned_path"}:
                entity_source_evidence_missing_fields.append(f"{record_label} missing {field}")
        evidence_id = record.get("evidence_id")
        entity_id = record.get("entity_id")
        source_id = record.get("source_id")
        if evidence_id:
            evidence_ids.append(evidence_id)
        if entity_id:
            if entity_id not in id_set:
                entity_source_evidence_unknown_entity_ids.append(f"{record_label} -> {entity_id}")
            elif record.get("entity_type") != entity_type_by_id.get(entity_id):
                entity_source_evidence_entity_type_mismatches.append(f"{record_label} -> {entity_id}")
        if source_id:
            if source_id not in source_ids:
                entity_source_evidence_unknown_source_ids.append(f"{record_label} -> {source_id}")
            elif record.get("source_status") != source_status_by_id.get(source_id):
                entity_source_evidence_status_mismatches.append(f"{record_label} -> {source_id}")
            expected_chunk_count = chunk_counts_by_doc_id.get(source_id, 0)
            if record.get("chunk_count") != expected_chunk_count:
                entity_source_evidence_chunk_count_mismatches.append(
                    f"{record_label} -> {source_id}: expected {expected_chunk_count}, got {record.get('chunk_count')}"
                )
        pair = (entity_id, source_id)
        if entity_id and source_id:
            evidence_pairs.append(pair)
            if pair not in expected_entity_source_pairs:
                entity_source_evidence_unexpected_pairs.append(f"{record_label} -> {entity_id}:{source_id}")
        for path_field in ("source_path", "parsed_path", "cleaned_path"):
            path_value = record.get(path_field)
            if path_value and not paths.resolve_logical_path(path_value).exists():
                entity_source_evidence_missing_paths.append(f"{record_label} {path_field} -> {path_value}")
        chunk_sample_ids = record.get("chunk_sample_ids", [])
        if isinstance(chunk_sample_ids, list):
            for chunk_id in chunk_sample_ids:
                if chunk_id not in chunk_id_set:
                    entity_source_evidence_unknown_chunk_sample_ids.append(f"{record_label} -> {chunk_id}")
    evidence_id_counts = Counter(evidence_ids)
    entity_source_evidence_duplicate_ids = sorted(
        evidence_id for evidence_id, count in evidence_id_counts.items() if count > 1
    )
    entity_source_evidence_missing_pairs = sorted(
        f"{entity_id}:{source_id}"
        for entity_id, source_id in expected_entity_source_pairs - set(evidence_pairs)
    )

    entity_by_id = {
        record.get("id"): record
        for record in records
        if record.get("id")
    }
    evidence_records_by_entity = defaultdict(list)
    for record in entity_source_evidence_items:
        if record.get("entity_id"):
            evidence_records_by_entity[record["entity_id"]].append(record)
    entity_review_packet_missing_fields = []
    entity_review_packet_duplicate_packet_ids = []
    entity_review_packet_duplicate_orders = []
    entity_review_packet_unknown_entity_ids = []
    entity_review_packet_entity_type_mismatches = []
    entity_review_packet_status_mismatches = []
    entity_review_packet_source_ref_mismatches = []
    entity_review_packet_evidence_count_mismatches = []
    entity_review_packet_chunk_count_mismatches = []
    entity_review_packet_case_observation_mismatches = []
    entity_review_packet_source_bucket_mismatches = []
    entity_review_packet_unknown_source_refs = []
    entity_review_packet_unknown_chunk_sample_ids = []
    entity_review_packet_missing_paths = []
    entity_review_packet_missing_entities = []
    packet_ids = []
    packet_orders = []
    packet_entity_ids = []
    for index, record in enumerate(entity_review_packet_items, start=1):
        record_label = f"entity_review_packets:{index}"
        schema_errors.extend(validate_schema(record, schemas["entity_review_packet"], record_label))
        for field in REQUIRED_ENTITY_REVIEW_PACKET_FIELDS:
            if missing_or_empty(record, field) and field not in {"parsed_paths", "cleaned_paths", "chunk_sample_ids"}:
                entity_review_packet_missing_fields.append(f"{record_label} missing {field}")
        packet_id = record.get("packet_id")
        review_order = record.get("review_order")
        entity_id = record.get("entity_id")
        if packet_id:
            packet_ids.append(packet_id)
        if isinstance(review_order, int):
            packet_orders.append(review_order)
        if entity_id:
            packet_entity_ids.append(entity_id)
            entity = entity_by_id.get(entity_id)
            if entity is None:
                entity_review_packet_unknown_entity_ids.append(f"{record_label} -> {entity_id}")
            else:
                if record.get("entity_type") != entity.get("entity_type"):
                    entity_review_packet_entity_type_mismatches.append(f"{record_label} -> {entity_id}")
                if record.get("review_status") != entity.get("review_status"):
                    entity_review_packet_status_mismatches.append(f"{record_label} -> {entity_id}")
                expected_source_refs = [str(ref) for ref in entity.get("source_refs", [])]
                actual_source_refs = record.get("source_refs", [])
                if expected_source_refs != actual_source_refs or record.get("source_ref_count") != len(expected_source_refs):
                    entity_review_packet_source_ref_mismatches.append(f"{record_label} -> {entity_id}")
                payload = record.get("entity_payload", {})
                if isinstance(payload, dict) and payload.get("id") != entity_id:
                    entity_review_packet_entity_type_mismatches.append(f"{record_label} payload -> {entity_id}")
        source_refs = record.get("source_refs", [])
        if isinstance(source_refs, list):
            for ref in source_refs:
                if ref not in source_ids:
                    entity_review_packet_unknown_source_refs.append(f"{record_label} -> {ref}")
        evidence_records = evidence_records_by_entity.get(entity_id, [])
        expected_non_manual = sum(1 for item in evidence_records if item.get("source_status") != "manual_note")
        expected_manual = sum(1 for item in evidence_records if item.get("source_status") == "manual_note")
        if record.get("evidence_record_count") != len(evidence_records):
            entity_review_packet_evidence_count_mismatches.append(f"{record_label} -> {entity_id}")
        if record.get("non_manual_source_count") != expected_non_manual or record.get("manual_note_source_count") != expected_manual:
            entity_review_packet_source_bucket_mismatches.append(f"{record_label} -> {entity_id}")
        expected_bucket = "context_only_needs_authoritative_source"
        if expected_non_manual and expected_manual:
            expected_bucket = "ready_with_manual_note"
        elif expected_non_manual:
            expected_bucket = "ready_without_manual_note"
        if record.get("review_bucket") != expected_bucket:
            entity_review_packet_source_bucket_mismatches.append(f"{record_label} bucket -> {entity_id}")
        expected_chunk_total = sum(item.get("chunk_count", 0) for item in evidence_records)
        if record.get("total_chunk_count") != expected_chunk_total:
            entity_review_packet_chunk_count_mismatches.append(f"{record_label} -> {entity_id}")
        expected_case_observation_total = sum(item.get("case_observation_count", 0) for item in evidence_records)
        if record.get("case_observation_count") != expected_case_observation_total:
            entity_review_packet_case_observation_mismatches.append(f"{record_label} -> {entity_id}")
        for path_field in ("source_paths", "parsed_paths", "cleaned_paths"):
            values = record.get(path_field, [])
            if isinstance(values, list):
                for path_value in values:
                    if path_value and not paths.resolve_logical_path(path_value).exists():
                        entity_review_packet_missing_paths.append(f"{record_label} {path_field} -> {path_value}")
        chunk_sample_ids = record.get("chunk_sample_ids", [])
        if isinstance(chunk_sample_ids, list):
            for chunk_id in chunk_sample_ids:
                if chunk_id not in chunk_id_set:
                    entity_review_packet_unknown_chunk_sample_ids.append(f"{record_label} -> {chunk_id}")
    packet_id_counts = Counter(packet_ids)
    entity_review_packet_duplicate_packet_ids = sorted(
        packet_id for packet_id, count in packet_id_counts.items() if count > 1
    )
    packet_order_counts = Counter(packet_orders)
    entity_review_packet_duplicate_orders = sorted(
        str(order) for order, count in packet_order_counts.items() if count > 1
    )
    expected_orders = list(range(1, len(entity_review_packet_items) + 1))
    if sorted(packet_orders) != expected_orders:
        entity_review_packet_duplicate_orders.append("review_order not contiguous")
    entity_review_packet_missing_entities = sorted(id_set - set(packet_entity_ids))

    context_only_packet_ids = {
        record.get("entity_id")
        for record in entity_review_packet_items
        if record.get("entity_id") and record.get("review_bucket") == "context_only_needs_authoritative_source"
    }
    authoritative_source_requirement_missing_fields = []
    authoritative_source_requirement_duplicate_ids = []
    authoritative_source_requirement_unknown_entity_ids = []
    authoritative_source_requirement_entity_type_mismatches = []
    authoritative_source_requirement_source_ref_mismatches = []
    authoritative_source_requirement_unknown_source_refs = []
    authoritative_source_requirement_unexpected_entities = []
    authoritative_source_requirement_missing_entities = []
    authoritative_source_requirement_ids = []
    authoritative_source_requirement_entity_ids = []
    for index, record in enumerate(authoritative_source_requirements, start=1):
        record_label = f"authoritative_source_requirements:{index}"
        schema_errors.extend(validate_schema(record, schemas["authoritative_source_requirement"], record_label))
        for field in REQUIRED_AUTHORITATIVE_SOURCE_REQUIREMENT_FIELDS:
            if missing_or_empty(record, field) and field != "search_query":
                authoritative_source_requirement_missing_fields.append(f"{record_label} missing {field}")
        requirement_id = record.get("requirement_id")
        entity_id = record.get("entity_id")
        if requirement_id:
            authoritative_source_requirement_ids.append(requirement_id)
        if entity_id:
            authoritative_source_requirement_entity_ids.append(entity_id)
            entity = entity_by_id.get(entity_id)
            if entity is None:
                authoritative_source_requirement_unknown_entity_ids.append(f"{record_label} -> {entity_id}")
            else:
                if record.get("entity_type") != entity.get("entity_type"):
                    authoritative_source_requirement_entity_type_mismatches.append(f"{record_label} -> {entity_id}")
                expected_source_refs = [str(ref) for ref in entity.get("source_refs", [])]
                actual_source_refs = record.get("current_source_refs", [])
                if expected_source_refs != actual_source_refs or record.get("current_source_ref_count") != len(expected_source_refs):
                    authoritative_source_requirement_source_ref_mismatches.append(f"{record_label} -> {entity_id}")
            if entity_id not in context_only_packet_ids:
                authoritative_source_requirement_unexpected_entities.append(f"{record_label} -> {entity_id}")
        current_source_refs = record.get("current_source_refs", [])
        if isinstance(current_source_refs, list):
            for ref in current_source_refs:
                if ref not in source_ids:
                    authoritative_source_requirement_unknown_source_refs.append(f"{record_label} -> {ref}")
    authoritative_source_requirement_id_counts = Counter(authoritative_source_requirement_ids)
    authoritative_source_requirement_duplicate_ids = sorted(
        requirement_id
        for requirement_id, count in authoritative_source_requirement_id_counts.items()
        if count > 1
    )
    authoritative_source_requirement_missing_entities = sorted(
        context_only_packet_ids - set(authoritative_source_requirement_entity_ids)
    )

    expected_next_action_ids = {
        f"action_source_intake_{record.get('entity_id')}"
        for record in authoritative_source_requirements
        if record.get("entity_id")
    }
    expected_next_action_ids.update(
        f"action_entity_review_{record.get('entity_id')}"
        for record in entity_review_packet_items
        if record.get("entity_id") and record.get("review_bucket") in {"ready_without_manual_note", "ready_with_manual_note"}
    )
    expected_next_action_ids.update({
        "action_skipped_paper_method_expansion",
        "action_skipped_case_semantic_review",
    })
    next_action_missing_fields = []
    next_action_duplicate_ids = []
    next_action_duplicate_orders = []
    next_action_unknown_entity_ids = []
    next_action_unknown_source_refs = []
    next_action_unexpected_actions = []
    next_action_missing_expected_actions = []
    next_action_llm_flag_mismatches = []
    next_action_ids = []
    next_action_orders = []
    for index, record in enumerate(next_action_items, start=1):
        record_label = f"next_action_queue:{index}"
        schema_errors.extend(validate_schema(record, schemas["next_action"], record_label))
        for field in REQUIRED_NEXT_ACTION_FIELDS:
            if missing_or_empty(record, field):
                next_action_missing_fields.append(f"{record_label} missing {field}")
        action_id = record.get("action_id")
        if action_id:
            next_action_ids.append(action_id)
            if action_id not in expected_next_action_ids:
                next_action_unexpected_actions.append(action_id)
        action_order = record.get("action_order")
        if isinstance(action_order, int):
            next_action_orders.append(action_order)
        entity_id = record.get("entity_id")
        if entity_id and entity_id not in id_set:
            next_action_unknown_entity_ids.append(f"{record_label} -> {entity_id}")
        source_refs = record.get("source_refs", [])
        if isinstance(source_refs, list):
            for ref in source_refs:
                if ref not in source_ids:
                    next_action_unknown_source_refs.append(f"{record_label} -> {ref}")
        if record.get("action_type") == "semantic_task_skipped":
            if record.get("needs_llm") is not True or record.get("status") != "skipped_by_policy":
                next_action_llm_flag_mismatches.append(f"{record_label} -> {action_id}")
        elif record.get("needs_llm") is not False or record.get("status") != "open":
            next_action_llm_flag_mismatches.append(f"{record_label} -> {action_id}")
    next_action_id_counts = Counter(next_action_ids)
    next_action_duplicate_ids = sorted(
        action_id for action_id, count in next_action_id_counts.items() if count > 1
    )
    next_action_order_counts = Counter(next_action_orders)
    next_action_duplicate_orders = sorted(
        str(order) for order, count in next_action_order_counts.items() if count > 1
    )
    expected_next_action_orders = list(range(1, len(next_action_items) + 1))
    if sorted(next_action_orders) != expected_next_action_orders:
        next_action_duplicate_orders.append("action_order not contiguous")
    next_action_missing_expected_actions = sorted(expected_next_action_ids - set(next_action_ids))

    packet_ids_by_entity = {
        record.get("entity_id"): record.get("packet_id")
        for record in entity_review_packet_items
        if record.get("entity_id")
    }
    action_ids_by_entity = {
        record.get("entity_id"): record.get("action_id")
        for record in next_action_items
        if record.get("action_type") == "entity_human_review" and record.get("entity_id")
    }
    human_review_workbook_missing_fields = []
    human_review_workbook_duplicate_ids = []
    human_review_workbook_duplicate_orders = []
    human_review_workbook_unknown_entity_ids = []
    human_review_workbook_entity_type_mismatches = []
    human_review_workbook_source_ref_mismatches = []
    human_review_workbook_unknown_source_refs = []
    human_review_workbook_unknown_chunk_sample_ids = []
    human_review_workbook_missing_paths = []
    human_review_workbook_packet_mismatches = []
    human_review_workbook_action_mismatches = []
    human_review_workbook_decision_mismatches = []
    human_review_workbook_missing_entities = []
    workbook_ids = []
    workbook_orders = []
    workbook_entity_ids = []
    for index, record in enumerate(human_review_workbook_items, start=1):
        record_label = f"human_review_workbook:{index}"
        schema_errors.extend(validate_schema(record, schemas["human_review_workbook_entry"], record_label))
        for field in REQUIRED_HUMAN_REVIEW_WORKBOOK_FIELDS:
            if missing_or_empty(record, field) and field != "llm_skip_reason":
                human_review_workbook_missing_fields.append(f"{record_label} missing {field}")
        workbook_id = record.get("workbook_id")
        review_order = record.get("review_order")
        entity_id = record.get("entity_id")
        if workbook_id:
            workbook_ids.append(workbook_id)
        if isinstance(review_order, int):
            workbook_orders.append(review_order)
        if entity_id:
            workbook_entity_ids.append(entity_id)
            entity = entity_by_id.get(entity_id)
            if entity is None:
                human_review_workbook_unknown_entity_ids.append(f"{record_label} -> {entity_id}")
            else:
                if record.get("entity_type") != entity.get("entity_type"):
                    human_review_workbook_entity_type_mismatches.append(f"{record_label} -> {entity_id}")
                expected_source_refs = [str(ref) for ref in entity.get("source_refs", [])]
                if record.get("source_refs", []) != expected_source_refs:
                    human_review_workbook_source_ref_mismatches.append(f"{record_label} -> {entity_id}")
            if record.get("related_packet_id") != packet_ids_by_entity.get(entity_id):
                human_review_workbook_packet_mismatches.append(f"{record_label} -> {entity_id}")
            if record.get("related_action_id") != action_ids_by_entity.get(entity_id):
                human_review_workbook_action_mismatches.append(f"{record_label} -> {entity_id}")
        if record.get("review_decision") != "unreviewed" or record.get("needs_llm") is not False:
            human_review_workbook_decision_mismatches.append(record_label)
        source_refs = record.get("source_refs", [])
        if isinstance(source_refs, list):
            for ref in source_refs:
                if ref not in source_ids:
                    human_review_workbook_unknown_source_refs.append(f"{record_label} -> {ref}")
        for path_field in ("source_paths", "parsed_paths", "cleaned_paths"):
            values = record.get(path_field, [])
            if isinstance(values, list):
                for path_value in values:
                    if path_value and not paths.resolve_logical_path(path_value).exists():
                        human_review_workbook_missing_paths.append(f"{record_label} {path_field} -> {path_value}")
        chunk_sample_ids = record.get("chunk_sample_ids", [])
        if isinstance(chunk_sample_ids, list):
            for chunk_id in chunk_sample_ids:
                if chunk_id not in chunk_id_set:
                    human_review_workbook_unknown_chunk_sample_ids.append(f"{record_label} -> {chunk_id}")
    workbook_id_counts = Counter(workbook_ids)
    human_review_workbook_duplicate_ids = sorted(
        workbook_id for workbook_id, count in workbook_id_counts.items() if count > 1
    )
    workbook_order_counts = Counter(workbook_orders)
    human_review_workbook_duplicate_orders = sorted(
        str(order) for order, count in workbook_order_counts.items() if count > 1
    )
    expected_workbook_orders = list(range(1, len(human_review_workbook_items) + 1))
    if sorted(workbook_orders) != expected_workbook_orders:
        human_review_workbook_duplicate_orders.append("review_order not contiguous")
    human_review_workbook_missing_entities = sorted(set(packet_ids_by_entity) - set(workbook_entity_ids))

    workbook_by_entity = {
        record.get("entity_id"): record
        for record in human_review_workbook_items
        if record.get("entity_id")
    }
    review_input_decisions = {}
    review_input_invalid_rows = []
    review_input_path = paths.REVIEW_INPUTS_DIR / "human_review_decisions.csv"
    if review_input_path.exists():
        with review_input_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row_number, row in enumerate(reader, start=2):
                entity_id = (row.get("entity_id") or "").strip()
                decision = (row.get("review_decision") or "").strip()
                if not entity_id and not decision:
                    continue
                if not entity_id:
                    review_input_invalid_rows.append(f"row {row_number}: missing entity_id")
                    continue
                if not decision or decision == "unreviewed":
                    continue
                if decision not in {"approved", "rejected", "needs_source", "needs_semantic_review"}:
                    review_input_invalid_rows.append(f"row {row_number}: invalid review_decision {decision}")
                    continue
                if entity_id in review_input_decisions:
                    review_input_invalid_rows.append(f"row {row_number}: duplicate entity_id {entity_id}")
                    continue
                review_input_decisions[entity_id] = {
                    "review_decision": decision,
                    "reviewer": (row.get("reviewer") or "").strip(),
                    "reviewed_at": (row.get("reviewed_at") or "").strip(),
                    "decision_note": (row.get("decision_note") or "").strip(),
                }
    human_review_decision_audit_missing_fields = []
    human_review_decision_audit_duplicate_ids = []
    human_review_decision_audit_unknown_entity_ids = []
    human_review_decision_audit_entity_type_mismatches = []
    human_review_decision_audit_workbook_mismatches = []
    human_review_decision_audit_status_mismatches = []
    human_review_decision_audit_missing_entities = []
    audit_ids = []
    audit_entity_ids = []
    for index, record in enumerate(human_review_decision_audit_items, start=1):
        record_label = f"human_review_decision_audit:{index}"
        schema_errors.extend(validate_schema(record, schemas["human_review_decision_audit"], record_label))
        for field in REQUIRED_HUMAN_REVIEW_DECISION_AUDIT_FIELDS:
            if missing_or_empty(record, field) and field not in {"decision_reviewer", "decision_reviewed_at", "decision_note"}:
                human_review_decision_audit_missing_fields.append(f"{record_label} missing {field}")
        audit_id = record.get("audit_id")
        entity_id = record.get("entity_id")
        if audit_id:
            audit_ids.append(audit_id)
        if entity_id:
            audit_entity_ids.append(entity_id)
            entity = entity_by_id.get(entity_id)
            workbook = workbook_by_entity.get(entity_id)
            if entity is None:
                human_review_decision_audit_unknown_entity_ids.append(f"{record_label} -> {entity_id}")
            else:
                if record.get("entity_type") != entity.get("entity_type"):
                    human_review_decision_audit_entity_type_mismatches.append(f"{record_label} -> {entity_id}")
                if record.get("current_review_status") != entity.get("review_status"):
                    human_review_decision_audit_status_mismatches.append(f"{record_label} current -> {entity_id}")
            if workbook is None:
                human_review_decision_audit_workbook_mismatches.append(f"{record_label} missing workbook -> {entity_id}")
            else:
                input_decision = review_input_decisions.get(entity_id)
                expected_decision = (
                    input_decision["review_decision"]
                    if input_decision
                    else workbook.get("review_decision")
                )
                expected_source = "data/review_inputs/human_review_decisions.csv" if input_decision else "workbook_default"
                if record.get("workbook_id") != workbook.get("workbook_id"):
                    human_review_decision_audit_workbook_mismatches.append(f"{record_label} workbook_id -> {entity_id}")
                if record.get("review_decision") != expected_decision:
                    human_review_decision_audit_workbook_mismatches.append(f"{record_label} review_decision -> {entity_id}")
                if record.get("decision_source") != expected_source:
                    human_review_decision_audit_workbook_mismatches.append(f"{record_label} decision_source -> {entity_id}")
                expected_status = "no_op"
                expected_can_apply = False
                expected_needs_llm = expected_decision == "needs_semantic_review" or (
                    workbook.get("needs_llm") is True and not input_decision
                )
                expected_target = entity.get("review_status", "") if entity else ""
                if expected_decision in {"approved", "rejected"}:
                    expected_status = "ready_to_apply"
                    expected_can_apply = not expected_needs_llm
                    expected_target = expected_decision
                elif expected_decision == "needs_source":
                    expected_status = "manual_followup"
                elif expected_decision == "needs_semantic_review":
                    expected_status = "blocked_by_llm"
                if (
                    record.get("application_status") != expected_status
                    or record.get("can_apply") is not expected_can_apply
                    or record.get("needs_llm") is not expected_needs_llm
                    or record.get("target_review_status") != expected_target
                ):
                    human_review_decision_audit_status_mismatches.append(f"{record_label} application -> {entity_id}")
    audit_id_counts = Counter(audit_ids)
    human_review_decision_audit_duplicate_ids = sorted(
        audit_id for audit_id, count in audit_id_counts.items() if count > 1
    )
    human_review_decision_audit_missing_entities = sorted(set(workbook_by_entity) - set(audit_entity_ids))
    human_review_input_unknown_entities = sorted(set(review_input_decisions) - set(workbook_by_entity))

    human_review_apply_preview_missing_fields = []
    human_review_apply_preview_duplicate_ids = []
    human_review_apply_preview_missing_summary = []
    human_review_apply_preview_run_mode_mismatches = []
    human_review_apply_preview_count_mismatches = []
    apply_preview_ids = []
    apply_preview_summary = None
    for index, record in enumerate(human_review_decision_apply_preview_items, start=1):
        record_label = f"human_review_decision_apply_preview:{index}"
        schema_errors.extend(validate_schema(record, schemas["human_review_decision_apply_preview"], record_label))
        for field in REQUIRED_HUMAN_REVIEW_DECISION_APPLY_PREVIEW_FIELDS:
            if missing_or_empty(record, field):
                human_review_apply_preview_missing_fields.append(f"{record_label} missing {field}")
        preview_id = record.get("preview_id")
        if preview_id:
            apply_preview_ids.append(preview_id)
        if record.get("run_mode") != "dry_run":
            human_review_apply_preview_run_mode_mismatches.append(record_label)
        if record.get("record_type") == "summary":
            if apply_preview_summary is not None:
                human_review_apply_preview_count_mismatches.append(f"{record_label} duplicate summary")
            apply_preview_summary = record
    apply_preview_id_counts = Counter(apply_preview_ids)
    human_review_apply_preview_duplicate_ids = sorted(
        preview_id for preview_id, count in apply_preview_id_counts.items() if count > 1
    )
    if apply_preview_summary is None:
        human_review_apply_preview_missing_summary.append("summary")
    else:
        expected_apply_count = sum(
            1 for record in human_review_decision_audit_items
            if record.get("application_status") == "ready_to_apply"
            and record.get("can_apply") is True
            and record.get("needs_llm") is not True
            and record.get("target_review_status") in {"approved", "rejected"}
        )
        if apply_preview_summary.get("count") != expected_apply_count:
            human_review_apply_preview_count_mismatches.append("summary count")

    expected_validation_check_types = {
        "input_file_exists",
        "required_columns",
        "duplicate_entity_id",
        "missing_entity_id",
        "known_entity_id",
        "allowed_review_decision",
        "semantic_review_boundary",
        "ready_to_apply_preview",
    }
    human_review_input_validation_missing_fields = []
    human_review_input_validation_duplicate_ids = []
    human_review_input_validation_order_mismatches = []
    human_review_input_validation_missing_checks = []
    human_review_input_validation_failure_records = []
    human_review_input_validation_llm_mismatches = []
    validation_ids = []
    validation_orders = []
    validation_check_types = []
    for index, record in enumerate(human_review_input_validation_items, start=1):
        record_label = f"human_review_input_validation:{index}"
        schema_errors.extend(validate_schema(record, schemas["human_review_input_validation"], record_label))
        for field in REQUIRED_HUMAN_REVIEW_INPUT_VALIDATION_FIELDS:
            if missing_or_empty(record, field) and field not in {"affected_entity_ids", "affected_rows"}:
                human_review_input_validation_missing_fields.append(f"{record_label} missing {field}")
        validation_id = record.get("validation_id")
        check_order = record.get("check_order")
        check_type = record.get("check_type")
        if validation_id:
            validation_ids.append(validation_id)
        if isinstance(check_order, int):
            validation_orders.append(check_order)
        if check_type:
            validation_check_types.append(check_type)
        if record.get("input_path") != "data/review_inputs/human_review_decisions.csv":
            human_review_input_validation_missing_fields.append(f"{record_label} input_path")
        if record.get("status") == "fail":
            human_review_input_validation_failure_records.append(record_label)
        if check_type == "semantic_review_boundary" and record.get("needs_llm") != (record.get("issue_count", 0) > 0):
            human_review_input_validation_llm_mismatches.append(record_label)
        if record.get("severity") == "error" and record.get("issue_count", 0) > 0 and record.get("status") != "fail":
            human_review_input_validation_order_mismatches.append(f"{record_label} error status")
        if record.get("severity") == "warning" and record.get("issue_count", 0) > 0 and record.get("status") != "warning":
            human_review_input_validation_order_mismatches.append(f"{record_label} warning status")
    validation_id_counts = Counter(validation_ids)
    human_review_input_validation_duplicate_ids = sorted(
        validation_id for validation_id, count in validation_id_counts.items() if count > 1
    )
    if sorted(validation_orders) != list(range(1, len(human_review_input_validation_items) + 1)):
        human_review_input_validation_order_mismatches.append("check_order not contiguous")
    human_review_input_validation_missing_checks = sorted(
        expected_validation_check_types - set(validation_check_types)
    )

    human_review_progress_missing_fields = []
    human_review_progress_duplicate_ids = []
    human_review_progress_count_mismatches = []
    human_review_progress_missing_overall = []
    progress_ids = []
    overall_progress = None
    for index, record in enumerate(human_review_progress_items, start=1):
        record_label = f"human_review_progress:{index}"
        schema_errors.extend(validate_schema(record, schemas["human_review_progress"], record_label))
        for field in REQUIRED_HUMAN_REVIEW_PROGRESS_FIELDS:
            if missing_or_empty(record, field):
                human_review_progress_missing_fields.append(f"{record_label} missing {field}")
        progress_id = record.get("progress_id")
        if progress_id:
            progress_ids.append(progress_id)
        if record.get("scope_type") == "overall" and record.get("scope_value") == "all":
            overall_progress = record
        status_total = (
            record.get("pending_count", 0)
            + record.get("approved_count", 0)
            + record.get("rejected_count", 0)
        )
        decision_total = (
            record.get("unreviewed_decision_count", 0)
            + record.get("approved_decision_count", 0)
            + record.get("rejected_decision_count", 0)
            + record.get("needs_source_decision_count", 0)
            + record.get("needs_semantic_review_decision_count", 0)
        )
        if status_total != record.get("entity_count"):
            human_review_progress_count_mismatches.append(f"{record_label} status_total")
        if decision_total != record.get("entity_count"):
            human_review_progress_count_mismatches.append(f"{record_label} decision_total")
    progress_id_counts = Counter(progress_ids)
    human_review_progress_duplicate_ids = sorted(
        progress_id for progress_id, count in progress_id_counts.items() if count > 1
    )
    if overall_progress is None:
        human_review_progress_missing_overall.append("overall/all")
    else:
        if overall_progress.get("entity_count") != len(human_review_workbook_items):
            human_review_progress_count_mismatches.append("overall entity_count")
        if overall_progress.get("pending_count") != sum(
            1 for record in human_review_workbook_items if record.get("review_status") == "pending"
        ):
            human_review_progress_count_mismatches.append("overall pending_count")
        if overall_progress.get("ready_to_apply_count") != sum(
            1 for record in human_review_decision_audit_items if record.get("application_status") == "ready_to_apply"
        ):
            human_review_progress_count_mismatches.append("overall ready_to_apply_count")

    human_review_evidence_extract_missing_fields = []
    human_review_evidence_extract_duplicate_ids = []
    human_review_evidence_extract_unknown_entity_ids = []
    human_review_evidence_extract_entity_type_mismatches = []
    human_review_evidence_extract_unknown_chunk_ids = []
    human_review_evidence_extract_path_mismatches = []
    human_review_evidence_extract_length_mismatches = []
    human_review_evidence_extract_llm_mismatches = []
    extract_ids = []
    extract_entities = set()
    for index, record in enumerate(human_review_evidence_extract_items, start=1):
        record_label = f"human_review_evidence_extract:{index}"
        schema_errors.extend(validate_schema(record, schemas["human_review_evidence_extract"], record_label))
        for field in REQUIRED_HUMAN_REVIEW_EVIDENCE_EXTRACT_FIELDS:
            if missing_or_empty(record, field) and field not in {"matched_terms"}:
                human_review_evidence_extract_missing_fields.append(f"{record_label} missing {field}")
        extract_id = record.get("extract_id")
        entity_id = record.get("entity_id")
        chunk_id = record.get("chunk_id")
        if extract_id:
            extract_ids.append(extract_id)
        if entity_id:
            extract_entities.add(entity_id)
            entity = entity_by_id.get(entity_id)
            if entity is None:
                human_review_evidence_extract_unknown_entity_ids.append(f"{record_label} -> {entity_id}")
            elif record.get("entity_type") != entity.get("entity_type"):
                human_review_evidence_extract_entity_type_mismatches.append(f"{record_label} -> {entity_id}")
        if chunk_id:
            chunk = chunk_by_id.get(chunk_id)
            if chunk is None:
                human_review_evidence_extract_unknown_chunk_ids.append(f"{record_label} -> {chunk_id}")
            else:
                if record.get("doc_id") != chunk.get("doc_id"):
                    human_review_evidence_extract_path_mismatches.append(f"{record_label} doc_id -> {chunk_id}")
                if record.get("chunk_type") != chunk.get("chunk_type"):
                    human_review_evidence_extract_path_mismatches.append(f"{record_label} chunk_type -> {chunk_id}")
        excerpt = record.get("excerpt", "")
        if isinstance(excerpt, str) and record.get("excerpt_char_count") != len(excerpt):
            human_review_evidence_extract_length_mismatches.append(f"{record_label} excerpt_char_count")
        if record.get("needs_llm") is not False:
            human_review_evidence_extract_llm_mismatches.append(record_label)
    extract_id_counts = Counter(extract_ids)
    human_review_evidence_extract_duplicate_ids = sorted(
        extract_id for extract_id, count in extract_id_counts.items() if count > 1
    )
    human_review_evidence_extract_missing_entities = sorted(set(workbook_by_entity) - extract_entities)

    extract_id_set = {
        record.get("extract_id")
        for record in human_review_evidence_extract_items
        if record.get("extract_id")
    }
    human_review_session_queue_missing_fields = []
    human_review_session_queue_duplicate_ids = []
    human_review_session_queue_unknown_entity_ids = []
    human_review_session_queue_entity_type_mismatches = []
    human_review_session_queue_unknown_extract_ids = []
    human_review_session_queue_unknown_chunk_ids = []
    human_review_session_queue_order_mismatches = []
    human_review_session_queue_llm_mismatches = []
    session_item_ids = []
    session_global_orders = []
    session_entity_ids = []
    for index, record in enumerate(human_review_session_queue_items, start=1):
        record_label = f"human_review_session_queue:{index}"
        schema_errors.extend(validate_schema(record, schemas["human_review_session_queue"], record_label))
        for field in REQUIRED_HUMAN_REVIEW_SESSION_QUEUE_FIELDS:
            if missing_or_empty(record, field) and field not in {"top_extract_ids", "top_chunk_ids", "top_match_scores"}:
                human_review_session_queue_missing_fields.append(f"{record_label} missing {field}")
        session_item_id = record.get("session_item_id")
        entity_id = record.get("entity_id")
        if session_item_id:
            session_item_ids.append(session_item_id)
        if isinstance(record.get("global_review_order"), int):
            session_global_orders.append(record["global_review_order"])
        if entity_id:
            session_entity_ids.append(entity_id)
            entity = entity_by_id.get(entity_id)
            if entity is None:
                human_review_session_queue_unknown_entity_ids.append(f"{record_label} -> {entity_id}")
            elif record.get("entity_type") != entity.get("entity_type"):
                human_review_session_queue_entity_type_mismatches.append(f"{record_label} -> {entity_id}")
        for extract_id in record.get("top_extract_ids", []):
            if extract_id not in extract_id_set:
                human_review_session_queue_unknown_extract_ids.append(f"{record_label} -> {extract_id}")
        for chunk_id in record.get("top_chunk_ids", []):
            if chunk_id not in chunk_id_set:
                human_review_session_queue_unknown_chunk_ids.append(f"{record_label} -> {chunk_id}")
        expected_session_order = ((record.get("global_review_order", 1) - 1) // 10) + 1
        expected_within_order = ((record.get("global_review_order", 1) - 1) % 10) + 1
        if record.get("session_order") != expected_session_order:
            human_review_session_queue_order_mismatches.append(f"{record_label} session_order")
        if record.get("within_session_order") != expected_within_order:
            human_review_session_queue_order_mismatches.append(f"{record_label} within_session_order")
        if (record.get("queue_status") == "blocked_by_llm") != (record.get("needs_llm") is True):
            human_review_session_queue_llm_mismatches.append(record_label)
    session_item_id_counts = Counter(session_item_ids)
    human_review_session_queue_duplicate_ids = sorted(
        item_id for item_id, count in session_item_id_counts.items() if count > 1
    )
    expected_session_orders = list(range(1, len(human_review_session_queue_items) + 1))
    if sorted(session_global_orders) != expected_session_orders:
        human_review_session_queue_order_mismatches.append("global_review_order not contiguous")
    human_review_session_queue_missing_entities = sorted(set(workbook_by_entity) - set(session_entity_ids))

    queue_by_session = defaultdict(list)
    for record in human_review_session_queue_items:
        if record.get("session_id"):
            queue_by_session[record["session_id"]].append(record)

    human_review_session_status_missing_fields = []
    human_review_session_status_duplicate_ids = []
    human_review_session_status_unknown_sessions = []
    human_review_session_status_missing_sessions = []
    human_review_session_status_count_mismatches = []
    human_review_session_status_order_mismatches = []
    human_review_session_status_next_mismatches = []
    human_review_session_status_llm_mismatches = []
    session_status_ids = []
    status_session_ids = []
    status_priority = ["awaiting_human_review", "ready_to_apply", "manual_followup", "blocked_by_llm"]
    for index, record in enumerate(human_review_session_status_items, start=1):
        record_label = f"human_review_session_status:{index}"
        schema_errors.extend(validate_schema(record, schemas["human_review_session_status"], record_label))
        for field in REQUIRED_HUMAN_REVIEW_SESSION_STATUS_FIELDS:
            if missing_or_empty(record, field):
                human_review_session_status_missing_fields.append(f"{record_label} missing {field}")
        session_status_id = record.get("session_status_id")
        session_id = record.get("session_id")
        if session_status_id:
            session_status_ids.append(session_status_id)
        if session_id:
            status_session_ids.append(session_id)
        session_items = queue_by_session.get(session_id, [])
        if session_id and not session_items:
            human_review_session_status_unknown_sessions.append(f"{record_label} -> {session_id}")
            continue
        queue_counts = Counter(item.get("queue_status", "") for item in session_items)
        decision_counts = Counter(item.get("review_decision", "") for item in session_items)
        expected_item_count = len(session_items)
        if record.get("item_count") != expected_item_count:
            human_review_session_status_count_mismatches.append(f"{record_label} item_count")
        expected_queue_counts = {
            "awaiting_human_review_count": queue_counts["awaiting_human_review"],
            "ready_to_apply_count": queue_counts["ready_to_apply"],
            "manual_followup_count": queue_counts["manual_followup"],
            "blocked_by_llm_count": queue_counts["blocked_by_llm"],
        }
        expected_decision_counts = {
            "unreviewed_decision_count": decision_counts["unreviewed"],
            "approved_decision_count": decision_counts["approved"],
            "rejected_decision_count": decision_counts["rejected"],
            "needs_source_decision_count": decision_counts["needs_source"],
            "needs_semantic_review_decision_count": decision_counts["needs_semantic_review"],
        }
        for field, expected in {**expected_queue_counts, **expected_decision_counts}.items():
            if record.get(field) != expected:
                human_review_session_status_count_mismatches.append(f"{record_label} {field}")
        if sum(record.get(field, 0) for field in expected_queue_counts) != expected_item_count:
            human_review_session_status_count_mismatches.append(f"{record_label} queue status total")
        if sum(record.get(field, 0) for field in expected_decision_counts) != expected_item_count:
            human_review_session_status_count_mismatches.append(f"{record_label} decision total")
        completed = decision_counts["approved"] + decision_counts["rejected"]
        expected_completion = round((completed / expected_item_count) * 100, 2) if expected_item_count else 0.0
        if abs(float(record.get("completion_percent", -1)) - expected_completion) > 0.001:
            human_review_session_status_count_mismatches.append(f"{record_label} completion_percent")
        expected_order = session_items[0].get("session_order") if session_items else None
        if record.get("session_order") != expected_order:
            human_review_session_status_order_mismatches.append(record_label)
        expected_needs_llm = sum(1 for item in session_items if item.get("needs_llm") is True)
        if record.get("needs_llm_count") != expected_needs_llm:
            human_review_session_status_llm_mismatches.append(record_label)
        sorted_session_items = sorted(
            session_items,
            key=lambda item: (
                item.get("within_session_order", 999999),
                item.get("global_review_order", 999999),
                item.get("entity_id", ""),
            ),
        )
        expected_next = None
        for status in status_priority:
            expected_next = next((item for item in sorted_session_items if item.get("queue_status") == status), None)
            if expected_next is not None:
                break
        expected_next_id = expected_next.get("entity_id") if expected_next else "none"
        if record.get("next_entity_id") != expected_next_id:
            human_review_session_status_next_mismatches.append(record_label)
    status_id_counts = Counter(session_status_ids)
    human_review_session_status_duplicate_ids = sorted(
        status_id for status_id, count in status_id_counts.items() if count > 1
    )
    human_review_session_status_missing_sessions = sorted(set(queue_by_session) - set(status_session_ids))

    queue_by_entity_for_field_checklist = {
        record.get("entity_id"): record
        for record in human_review_session_queue_items
        if record.get("entity_id")
    }
    expected_field_names_by_entity = {
        entity_id: [field for field in sorted(entity) if field not in {"id", "entity_type", "review_status"}]
        for entity_id, entity in entity_by_id.items()
        if entity_id in queue_by_entity_for_field_checklist
    }
    checklist_by_entity = defaultdict(list)
    human_review_field_checklist_missing_fields = []
    human_review_field_checklist_duplicate_ids = []
    human_review_field_checklist_unknown_entity_ids = []
    human_review_field_checklist_entity_type_mismatches = []
    human_review_field_checklist_session_mismatches = []
    human_review_field_checklist_field_mismatches = []
    human_review_field_checklist_value_mismatches = []
    human_review_field_checklist_json_errors = []
    human_review_field_checklist_default_mismatches = []
    human_review_field_checklist_missing_entities = []
    field_check_ids = []
    for index, record in enumerate(human_review_field_checklist_items, start=1):
        record_label = f"human_review_field_checklist:{index}"
        schema_errors.extend(validate_schema(record, schemas["human_review_field_checklist"], record_label))
        for field in REQUIRED_HUMAN_REVIEW_FIELD_CHECKLIST_FIELDS:
            if missing_or_empty(record, field):
                human_review_field_checklist_missing_fields.append(f"{record_label} missing {field}")
        field_check_id = record.get("field_check_id")
        if field_check_id:
            field_check_ids.append(field_check_id)
        entity_id = record.get("entity_id")
        if entity_id:
            checklist_by_entity[entity_id].append(record)
        entity = entity_by_id.get(entity_id)
        queue_record = queue_by_entity_for_field_checklist.get(entity_id)
        if entity is None or queue_record is None:
            human_review_field_checklist_unknown_entity_ids.append(f"{record_label} -> {entity_id}")
            continue
        if record.get("entity_type") != entity.get("entity_type"):
            human_review_field_checklist_entity_type_mismatches.append(record_label)
        for field in ("session_id", "session_order", "within_session_order", "global_review_order"):
            if record.get(field) != queue_record.get(field):
                human_review_field_checklist_session_mismatches.append(f"{record_label} {field}")
        field_name = record.get("field_name")
        if field_name not in expected_field_names_by_entity.get(entity_id, []):
            human_review_field_checklist_field_mismatches.append(f"{record_label} {field_name}")
            continue
        try:
            decoded_value = json.loads(record.get("field_value_json", ""))
        except json.JSONDecodeError as exc:
            human_review_field_checklist_json_errors.append(f"{record_label}: {exc}")
            continue
        if decoded_value != entity.get(field_name):
            human_review_field_checklist_value_mismatches.append(f"{record_label} {field_name}")
        if record.get("review_decision") != "unreviewed" or record.get("needs_llm") is not False:
            human_review_field_checklist_default_mismatches.append(record_label)
    field_check_id_counts = Counter(field_check_ids)
    human_review_field_checklist_duplicate_ids = sorted(
        field_check_id for field_check_id, count in field_check_id_counts.items() if count > 1
    )
    for entity_id, expected_fields in expected_field_names_by_entity.items():
        actual_fields = sorted(record.get("field_name") for record in checklist_by_entity.get(entity_id, []))
        if actual_fields != expected_fields:
            human_review_field_checklist_field_mismatches.append(f"{entity_id} field set")
    human_review_field_checklist_missing_entities = sorted(
        set(expected_field_names_by_entity) - set(checklist_by_entity)
    )

    source_rows_by_id = {
        row.get("source_id"): row
        for row in source_rows
        if row.get("source_id")
    }
    source_status_by_id = {
        record.get("source_id"): record
        for record in source_processing_statuses
        if record.get("source_id")
    }
    field_count_by_entity_for_source_matrix = Counter(
        record.get("entity_id")
        for record in human_review_field_checklist_items
        if record.get("entity_id")
    )
    expected_source_matrix_evidence = defaultdict(list)
    for record in entity_source_evidence_items:
        entity_id = record.get("entity_id")
        source_id = record.get("source_id")
        if entity_id in queue_by_entity_for_field_checklist and source_id:
            expected_source_matrix_evidence[source_id].append(record)
    human_review_source_matrix_missing_fields = []
    human_review_source_matrix_duplicate_ids = []
    human_review_source_matrix_unknown_source_ids = []
    human_review_source_matrix_missing_sources = []
    human_review_source_matrix_count_mismatches = []
    human_review_source_matrix_context_mismatches = []
    human_review_source_matrix_list_mismatches = []
    source_matrix_ids = []
    source_matrix_source_ids = []
    for index, record in enumerate(human_review_source_matrix_items, start=1):
        record_label = f"human_review_source_matrix:{index}"
        schema_errors.extend(validate_schema(record, schemas["human_review_source_matrix"], record_label))
        for field in REQUIRED_HUMAN_REVIEW_SOURCE_MATRIX_FIELDS:
            if missing_or_empty(record, field) and field not in {"cleaned_paths", "parsed_paths", "chunk_sample_ids"}:
                human_review_source_matrix_missing_fields.append(f"{record_label} missing {field}")
        source_matrix_id = record.get("source_matrix_id")
        source_id = record.get("source_id")
        if source_matrix_id:
            source_matrix_ids.append(source_matrix_id)
        if source_id:
            source_matrix_source_ids.append(source_id)
        if source_id not in source_rows_by_id:
            human_review_source_matrix_unknown_source_ids.append(f"{record_label} -> {source_id}")
            continue
        evidence_records = expected_source_matrix_evidence.get(source_id, [])
        if not evidence_records:
            human_review_source_matrix_unknown_source_ids.append(f"{record_label} -> {source_id}")
            continue
        source_row = source_rows_by_id[source_id]
        source_status = source_status_by_id.get(source_id, {})
        expected_entity_ids = sorted({item.get("entity_id") for item in evidence_records if item.get("entity_id")})
        expected_queue_records = [
            queue_by_entity_for_field_checklist[entity_id]
            for entity_id in expected_entity_ids
            if entity_id in queue_by_entity_for_field_checklist
        ]
        expected_sessions = sorted({item.get("session_id") for item in expected_queue_records if item.get("session_id")})
        expected_entity_types = sorted({item.get("entity_type") for item in expected_queue_records if item.get("entity_type")})
        expected_cleaned_paths = sorted({item.get("cleaned_path") for item in evidence_records if item.get("cleaned_path")})
        expected_parsed_paths = sorted({item.get("parsed_path") for item in evidence_records if item.get("parsed_path")})
        expected_field_count = sum(field_count_by_entity_for_source_matrix.get(entity_id, 0) for entity_id in expected_entity_ids)
        expected_counts = {
            "evidence_record_count": len(evidence_records),
            "entity_count": len(expected_entity_ids),
            "field_check_count": expected_field_count,
            "source_chunk_count": source_status.get("chunk_count", 0),
        }
        for field, expected in expected_counts.items():
            if record.get(field) != expected:
                human_review_source_matrix_count_mismatches.append(f"{record_label} {field}")
        expected_context = {
            "source_title": source_row.get("title", source_id),
            "source_type": source_row.get("source_type") or source_status.get("source_type", ""),
            "source_path": source_row.get("path") or source_status.get("path", ""),
            "trust_level": source_row.get("trust_level", ""),
            "inventory_review_status": source_row.get("review_status", ""),
            "processing_status": source_status.get("processing_status", ""),
            "raw_status": source_status.get("raw_status", ""),
            "parsed_status": source_status.get("parsed_status", ""),
            "cleaned_status": source_status.get("cleaned_status", ""),
        }
        for field, expected in expected_context.items():
            if record.get(field) != expected:
                human_review_source_matrix_context_mismatches.append(f"{record_label} {field}")
        if record.get("session_ids") != expected_sessions:
            human_review_source_matrix_list_mismatches.append(f"{record_label} session_ids")
        if record.get("entity_types") != expected_entity_types:
            human_review_source_matrix_list_mismatches.append(f"{record_label} entity_types")
        if record.get("sample_entity_ids") != expected_entity_ids[:12]:
            human_review_source_matrix_list_mismatches.append(f"{record_label} sample_entity_ids")
        if record.get("cleaned_paths") != expected_cleaned_paths:
            human_review_source_matrix_list_mismatches.append(f"{record_label} cleaned_paths")
        if record.get("parsed_paths") != expected_parsed_paths:
            human_review_source_matrix_list_mismatches.append(f"{record_label} parsed_paths")
    source_matrix_id_counts = Counter(source_matrix_ids)
    human_review_source_matrix_duplicate_ids = sorted(
        matrix_id for matrix_id, count in source_matrix_id_counts.items() if count > 1
    )
    human_review_source_matrix_missing_sources = sorted(
        set(expected_source_matrix_evidence) - set(source_matrix_source_ids)
    )

    session_ids_from_status = {
        record.get("session_id")
        for record in human_review_session_status_items
        if record.get("session_id")
    }
    source_ids_from_matrix = {
        record.get("source_id")
        for record in human_review_source_matrix_items
        if record.get("source_id") and record.get("source_type") != "manual_note"
    }
    human_review_task_board_missing_fields = []
    human_review_task_board_duplicate_ids = []
    human_review_task_board_order_mismatches = []
    human_review_task_board_missing_session_tasks = []
    human_review_task_board_missing_workflow_tasks = []
    human_review_task_board_unknown_session_tasks = []
    human_review_task_board_unknown_source_tasks = []
    human_review_task_board_command_mismatches = []
    human_review_task_board_default_mismatches = []
    task_ids = []
    task_orders = []
    task_session_ids = []
    for index, record in enumerate(human_review_task_board_items, start=1):
        record_label = f"human_review_task_board:{index}"
        schema_errors.extend(validate_schema(record, schemas["human_review_task_board"], record_label))
        for field in REQUIRED_HUMAN_REVIEW_TASK_BOARD_FIELDS:
            if missing_or_empty(record, field) and field not in {"session_id", "source_id", "entity_id", "secondary_input", "write_command"}:
                human_review_task_board_missing_fields.append(f"{record_label} missing {field}")
        task_id = record.get("task_id")
        if task_id:
            task_ids.append(task_id)
        if isinstance(record.get("task_order"), int):
            task_orders.append(record["task_order"])
        if record.get("needs_llm") is not False:
            human_review_task_board_default_mismatches.append(f"{record_label} needs_llm")
        task_type = record.get("task_type")
        if task_type == "review_session":
            session_id = record.get("session_id")
            task_session_ids.append(session_id)
            if session_id not in session_ids_from_status:
                human_review_task_board_unknown_session_tasks.append(f"{record_label} -> {session_id}")
            expected_command = f"python3 -m bgpkb.pipeline.import_human_review_session_decisions --session-id {session_id}"
            if record.get("suggested_command") != expected_command:
                human_review_task_board_command_mismatches.append(f"{record_label} suggested_command")
            if record.get("write_command") != f"{expected_command} --write":
                human_review_task_board_command_mismatches.append(f"{record_label} write_command")
        elif task_type == "review_source":
            source_id = record.get("source_id")
            if source_id not in source_ids_from_matrix:
                human_review_task_board_unknown_source_tasks.append(f"{record_label} -> {source_id}")
            if "--write" in record.get("suggested_command", ""):
                human_review_task_board_command_mismatches.append(f"{record_label} suggested_command")
        else:
            if task_type == "validate_input" and record.get("suggested_command") != "python3 -m bgpkb.pipeline.build_human_review_input_validation":
                human_review_task_board_command_mismatches.append(f"{record_label} validate command")
            if task_type == "audit_decisions" and record.get("suggested_command") != "python3 -m bgpkb.pipeline.build_human_review_decision_audit":
                human_review_task_board_command_mismatches.append(f"{record_label} audit command")
            if task_type == "apply_decisions" and record.get("task_status") != "manual_explicit_only":
                human_review_task_board_default_mismatches.append(f"{record_label} apply status")
            if task_type == "apply_decisions" and record.get("suggested_command") != "python3 -m bgpkb.pipeline.apply_human_review_decisions":
                human_review_task_board_command_mismatches.append(f"{record_label} apply suggested_command")
            if task_type == "apply_decisions" and record.get("write_command") != "python3 -m bgpkb.pipeline.apply_human_review_decisions --write":
                human_review_task_board_command_mismatches.append(f"{record_label} apply write_command")
    task_id_counts = Counter(task_ids)
    human_review_task_board_duplicate_ids = sorted(
        task_id for task_id, count in task_id_counts.items() if count > 1
    )
    if sorted(task_orders) != list(range(1, len(human_review_task_board_items) + 1)):
        human_review_task_board_order_mismatches.append("task_order not contiguous")
    human_review_task_board_missing_session_tasks = sorted(
        session_ids_from_status - set(task_session_ids)
    )
    human_review_task_board_missing_workflow_tasks = sorted(
        {"task_validate_input", "task_audit_decisions", "task_apply_decisions_explicit"} - set(task_ids)
    )

    task_board_by_id = {
        record.get("task_id"): record
        for record in human_review_task_board_items
        if record.get("task_id")
    }
    human_review_handoff_missing_fields = []
    human_review_handoff_duplicate_ids = []
    human_review_handoff_duplicate_task_ids = []
    human_review_handoff_unknown_task_ids = []
    human_review_handoff_missing_task_ids = []
    human_review_handoff_context_mismatches = []
    human_review_handoff_path_mismatches = []
    human_review_handoff_command_mismatches = []
    human_review_handoff_default_mismatches = []
    handoff_ids = []
    handoff_task_ids = []
    for index, record in enumerate(human_review_handoff_items, start=1):
        record_label = f"human_review_handoff:{index}"
        schema_errors.extend(validate_schema(record, schemas["human_review_handoff"], record_label))
        for field in REQUIRED_HUMAN_REVIEW_HANDOFF_FIELDS:
            if missing_or_empty(record, field) and field not in {"secondary_input", "dry_run_command", "write_command"}:
                human_review_handoff_missing_fields.append(f"{record_label} missing {field}")
        handoff_id = record.get("handoff_id")
        task_id = record.get("task_id")
        if handoff_id:
            handoff_ids.append(handoff_id)
        if task_id:
            handoff_task_ids.append(task_id)
        task = task_board_by_id.get(task_id)
        if task is None:
            human_review_handoff_unknown_task_ids.append(f"{record_label} -> {task_id}")
            continue
        for field in ("task_order", "task_type", "title", "primary_input", "secondary_input", "write_command"):
            if record.get(field) != task.get(field):
                human_review_handoff_context_mismatches.append(f"{record_label} {field}")
        expected_primary_exists = bool(
            record.get("primary_input") and paths.resolve_logical_path(record["primary_input"]).exists()
        )
        expected_secondary_exists = bool(
            record.get("secondary_input") and paths.resolve_logical_path(record["secondary_input"]).exists()
        )
        if record.get("primary_input_exists") is not expected_primary_exists:
            human_review_handoff_path_mismatches.append(f"{record_label} primary_input_exists")
        if record.get("secondary_input_exists") is not expected_secondary_exists:
            human_review_handoff_path_mismatches.append(f"{record_label} secondary_input_exists")
        task_type = record.get("task_type")
        expected_dry_run = task.get("suggested_command", "")
        if record.get("dry_run_command") != expected_dry_run:
            human_review_handoff_command_mismatches.append(f"{record_label} dry_run_command")
        expected_can_write = bool(task.get("write_command") and task_type in {"review_session", "apply_decisions"})
        expected_requires_human = task_type in {"review_session", "review_source", "apply_decisions"}
        if record.get("can_write") is not expected_can_write:
            human_review_handoff_default_mismatches.append(f"{record_label} can_write")
        if record.get("requires_human_decision") is not expected_requires_human:
            human_review_handoff_default_mismatches.append(f"{record_label} requires_human_decision")
        if record.get("needs_llm") is not False:
            human_review_handoff_default_mismatches.append(f"{record_label} needs_llm")
        if record.get("handoff_status") != "ready_for_human":
            human_review_handoff_default_mismatches.append(f"{record_label} handoff_status")
    handoff_id_counts = Counter(handoff_ids)
    human_review_handoff_duplicate_ids = sorted(
        handoff_id for handoff_id, count in handoff_id_counts.items() if count > 1
    )
    handoff_task_id_counts = Counter(handoff_task_ids)
    human_review_handoff_duplicate_task_ids = sorted(
        task_id for task_id, count in handoff_task_id_counts.items() if count > 1
    )
    human_review_handoff_missing_task_ids = sorted(
        set(task_board_by_id) - set(handoff_task_ids)
    )

    template_dir = paths.REVIEW_INPUTS_DIR / "human_review_session_decision_templates"
    expected_template_paths = {
        session_id: template_dir / f"{session_id}_decisions_template.csv"
        for session_id in queue_by_session
    }
    human_review_session_decision_template_missing_files = []
    human_review_session_decision_template_extra_files = []
    human_review_session_decision_template_header_mismatches = []
    human_review_session_decision_template_row_mismatches = []
    human_review_session_decision_template_default_decision_mismatches = []
    human_review_session_decision_template_context_mismatches = []
    human_review_session_decision_template_read_errors = []
    expected_template_names = {path.name for path in expected_template_paths.values()}
    if not (template_dir / "README.md").exists():
        human_review_session_decision_template_missing_files.append("data/review_inputs/human_review_session_decision_templates/README.md")
    existing_template_paths = sorted(template_dir.glob("review_session_*_decisions_template.csv")) if template_dir.exists() else []
    for path in existing_template_paths:
        if path.name not in expected_template_names:
            human_review_session_decision_template_extra_files.append(paths.rel(path))
    for session_id, path in sorted(expected_template_paths.items()):
        expected_items = sorted(
            queue_by_session[session_id],
            key=lambda item: (item.get("within_session_order", 999999), item.get("entity_id", "")),
        )
        if not path.exists():
            human_review_session_decision_template_missing_files.append(paths.rel(path))
            continue
        try:
            with path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames != REQUIRED_HUMAN_REVIEW_SESSION_DECISION_TEMPLATE_FIELDS:
                    human_review_session_decision_template_header_mismatches.append(paths.rel(path))
                rows = list(reader)
        except csv.Error as exc:
            human_review_session_decision_template_read_errors.append(f"{paths.rel(path)}: {exc}")
            continue
        if len(rows) != len(expected_items):
            human_review_session_decision_template_row_mismatches.append(f"{session_id} row_count")
        if [row.get("entity_id", "") for row in rows] != [item.get("entity_id", "") for item in expected_items]:
            human_review_session_decision_template_row_mismatches.append(f"{session_id} entity_order")
        for row, expected in zip(rows, expected_items):
            row_label = f"{session_id}:{row.get('entity_id', '')}"
            for field in ("review_decision", "reviewer", "reviewed_at", "decision_note"):
                if row.get(field, ""):
                    human_review_session_decision_template_default_decision_mismatches.append(f"{row_label} {field}")
            expected_context = {
                "session_id": session_id,
                "within_session_order": str(expected.get("within_session_order", "")),
                "entity_type": expected.get("entity_type", ""),
                "display_name": expected.get("display_name", ""),
                "queue_status": expected.get("queue_status", ""),
                "review_status": expected.get("review_status", ""),
                "review_batch": expected.get("review_batch", ""),
                "review_bucket": expected.get("review_bucket", ""),
                "source_refs": "|".join(expected.get("source_refs", [])),
                "cleaned_paths": "|".join(expected.get("cleaned_paths", [])),
                "parsed_paths": "|".join(expected.get("parsed_paths", [])),
                "top_extract_ids": "|".join(expected.get("top_extract_ids", [])),
            }
            for field, value in expected_context.items():
                if row.get(field, "") != value:
                    human_review_session_decision_template_context_mismatches.append(f"{row_label} {field}")

    case_observation_missing_fields = []
    case_observation_unknown_source_ids = []
    case_observation_missing_source_paths = []
    case_observation_duplicate_keys = []
    observation_keys = []
    for index, record in enumerate(case_observations, start=1):
        record_label = f"case_observations:{index}"
        schema_errors.extend(validate_schema(record, schemas["case_observation"], record_label))
        for field in REQUIRED_CASE_OBSERVATION_FIELDS:
            if missing_or_empty(record, field):
                case_observation_missing_fields.append(f"{record_label} missing {field}")
        source_id = record.get("source_id")
        if source_id and source_id not in source_ids:
            case_observation_unknown_source_ids.append(f"{record_label} -> {source_id}")
        source_path = source_path_from_ref(record.get("source_ref"))
        if source_path and not source_path.exists():
            case_observation_missing_source_paths.append(f"{record_label} -> {record.get('source_ref')}")
        observation_keys.append((
            record.get("source_id"),
            record.get("observation_type"),
            record.get("value"),
        ))
    observation_key_counts = Counter(observation_keys)
    case_observation_duplicate_keys = sorted(
        f"{source_id}:{observation_type}:{value}"
        for (source_id, observation_type, value), count in observation_key_counts.items()
        if count > 1
    )

    source_status_missing_fields = []
    source_status_unknown_source_ids = []
    source_status_duplicate_source_ids = []
    source_status_missing_inventory_rows = []
    source_status_ids = []
    for index, record in enumerate(source_processing_statuses, start=1):
        record_label = f"source_processing_status:{index}"
        schema_errors.extend(validate_schema(record, schemas["source_processing_status"], record_label))
        for field in REQUIRED_SOURCE_PROCESSING_STATUS_FIELDS:
            if missing_or_empty(record, field):
                source_status_missing_fields.append(f"{record_label} missing {field}")
        source_id = record.get("source_id")
        if source_id:
            source_status_ids.append(source_id)
            if source_id not in source_ids:
                source_status_unknown_source_ids.append(f"{record_label} -> {source_id}")
    source_status_id_counts = Counter(source_status_ids)
    source_status_duplicate_source_ids = sorted(
        source_id for source_id, count in source_status_id_counts.items() if count > 1
    )
    source_status_missing_inventory_rows = sorted(source_ids - set(source_status_ids))

    artifact_missing_fields = []
    artifact_duplicate_paths = []
    artifact_missing_files = []
    artifact_unknown_files = []
    artifact_size_mismatches = []
    artifact_line_count_mismatches = []
    artifact_sha256_mismatches = []
    artifact_binary_flag_mismatches = []
    artifact_manifest_paths = []
    expected_artifact_paths = {relative_path(path) for path in iter_artifact_paths()}
    report_policy_status = check_report_policy()
    report_layout_violations = report_policy_status["layout_violations"]
    report_missing_policy_paths = report_policy_status["missing_policy_paths"]
    report_unregistered_files = report_policy_status["unregistered_reports"]
    report_missing_directory_paths = report_policy_status["empty_old_report_dirs"]
    report_invalid_generated_categories = report_policy_status["invalid_generated_categories"]
    for index, record in enumerate(artifact_manifest_records, start=1):
        record_label = f"artifact_manifest:{index}"
        schema_errors.extend(validate_schema(record, schemas["artifact_manifest"], record_label))
        for field in REQUIRED_ARTIFACT_MANIFEST_FIELDS:
            if missing_or_empty(record, field):
                artifact_missing_fields.append(f"{record_label} missing {field}")
        artifact_path = record.get("artifact_path")
        if not artifact_path:
            continue
        artifact_manifest_paths.append(artifact_path)
        if artifact_path not in expected_artifact_paths:
            artifact_unknown_files.append(artifact_path)
            continue
        resolved = paths.resolve_logical_path(artifact_path)
        if not resolved.exists():
            artifact_missing_files.append(artifact_path)
            continue
        data = resolved.read_bytes()
        binary = is_binary_bytes(data)
        line_count = line_count_for(data, binary)
        sha256 = sha256_for_path(resolved)
        if record.get("size_bytes") != len(data):
            artifact_size_mismatches.append(f"{artifact_path}: manifest={record.get('size_bytes')} actual={len(data)}")
        if record.get("line_count") != line_count:
            artifact_line_count_mismatches.append(f"{artifact_path}: manifest={record.get('line_count')} actual={line_count}")
        if record.get("is_binary") != binary:
            artifact_binary_flag_mismatches.append(f"{artifact_path}: manifest={record.get('is_binary')} actual={binary}")
        if record.get("sha256") != sha256:
            artifact_sha256_mismatches.append(f"{artifact_path}: sha256 mismatch")
    artifact_path_counts = Counter(artifact_manifest_paths)
    artifact_duplicate_paths = sorted(
        artifact_path for artifact_path, count in artifact_path_counts.items() if count > 1
    )
    artifact_unregistered_files = sorted(expected_artifact_paths - set(artifact_manifest_paths))

    orphan_relationships = []
    duplicate_relationships = []
    relationship_unknown_source_refs = []
    relationship_invalid_confidence = []
    relationship_keys = []
    for rel in relationships:
        label = f"{rel.get('src_id')} -[{rel.get('relation')}]-> {rel.get('dst_id')}"
        schema_errors.extend(validate_schema(rel, schemas["relationship"], label))
        relationship_keys.append((rel.get("src_id"), rel.get("relation"), rel.get("dst_id")))
        for side in ("src_id", "dst_id"):
            if rel.get(side) not in id_set:
                orphan_relationships.append(f"{rel.get('src_id')} -[{rel.get('relation')}]-> {rel.get('dst_id')} missing {side}={rel.get(side)}")
        for ref in rel.get("source_refs", []):
            if ref not in source_ids:
                relationship_unknown_source_refs.append(f"{label} -> {ref}")
        confidence = rel.get("confidence")
        if confidence is not None and not (0 <= confidence <= 1):
            relationship_invalid_confidence.append(f"{label}: {confidence}")
    relationship_key_counts = Counter(relationship_keys)
    duplicate_relationships = sorted(
        f"{src_id} -[{relation}]-> {dst_id}"
        for (src_id, relation, dst_id), count in relationship_key_counts.items()
        if count > 1
    )

    anomaly_ids = {record["id"] for record in records if record.get("entity_type") == "AnomalyType"}
    evidence_targets = {record.get("applies_to") for record in records if record.get("entity_type") == "EvidenceTemplate"}
    anomalies_without_templates = sorted(anomaly_ids - evidence_targets)

    data_sources_without_limitations = sorted(
        record["id"]
        for record in records
        if record.get("entity_type") == "DataSource" and not record.get("limitations")
    )

    for row in source_rows:
        label = row.get("source_id") or "<missing source_id>"
        schema_errors.extend(validate_schema(row, schemas["source"], label))

    lines = [
        "# 质量检查报告",
        "",
        "## 摘要",
        "",
        f"- 来源清单记录数：{len(source_rows)}",
        f"- 扫描实体文件数：{len(by_file_counts)}",
        f"- 扫描 chunk 文件数：{len(chunk_file_counts)}",
        f"- Parsed 文档记录数：{len(parsed_documents)}",
        f"- Cleaned 文档记录数：{len(cleaned_documents)}",
        f"- 实体记录数：{len(records)}",
        f"- Chunk 记录数：{len(chunk_records)}",
        f"- 案例观察值记录数：{len(case_observations)}",
        f"- 来源处理状态记录数：{len(source_processing_statuses)}",
        f"- 来源缺口队列记录数：{len(source_gap_queue_items)}",
        f"- 实体复核队列记录数：{len(entity_review_queue_items)}",
        f"- 实体来源证据索引记录数：{len(entity_source_evidence_items)}",
        f"- 实体人工复核包记录数：{len(entity_review_packet_items)}",
        f"- 权威来源补充需求记录数：{len(authoritative_source_requirements)}",
        f"- 下一步行动队列记录数：{len(next_action_items)}",
        f"- 人工复核工作簿记录数：{len(human_review_workbook_items)}",
        f"- 人工复核决策审计记录数：{len(human_review_decision_audit_items)}",
        f"- 人工复核决策应用预览记录数：{len(human_review_decision_apply_preview_items)}",
        f"- 人工复核输入校验记录数：{len(human_review_input_validation_items)}",
        f"- 人工复核进度记录数：{len(human_review_progress_items)}",
        f"- 人工复核证据摘录记录数：{len(human_review_evidence_extract_items)}",
        f"- 人工复核会话队列记录数：{len(human_review_session_queue_items)}",
        f"- 人工复核会话状态记录数：{len(human_review_session_status_items)}",
        f"- 人工复核逐字段清单记录数：{len(human_review_field_checklist_items)}",
        f"- 人工复核来源矩阵记录数：{len(human_review_source_matrix_items)}",
        f"- 人工复核任务板记录数：{len(human_review_task_board_items)}",
        f"- 人工复核交接清单记录数：{len(human_review_handoff_items)}",
        f"- 术语表记录数：{len(glossary_entries)}",
        f"- 制品清单记录数：{len(artifact_manifest_records)}",
        f"- 语料画像记录数：{len(corpus_profiles)}",
        f"- OCR 质量评估记录数：{len(corpus_ocr_assessments)}",
        f"- 语料画像阻断问题数：{len(corpus_profile_blockers)}",
        f"- 清洗 v2 发布门禁阻断问题数：{len(cleaning_v2_release_gate_blockers)}",
        f"- 报告策略登记数：{len(report_policy_status['registered_paths'])}",
        f"- 关系记录数：{len(relationships)}",
        f"- JSON 错误数：{len(errors)}",
        f"- Schema 错误数：{len(schema_errors)}",
        f"- 重复 source_id 数：{len(duplicate_source_ids)}",
        f"- 重复实体 ID 数：{len(duplicate_ids)}",
        f"- 重复 chunk ID 数：{len(duplicate_chunk_ids)}",
        f"- 未归档来源数：{len(inventory_missing_paths)}",
        f"- 来源清单本地文件缺失数：{len(inventory_missing_raw_files)}",
        f"- raw 文件未登记数：{len(raw_files_without_inventory)}",
        f"- 可解析来源缺失 parsed 数：{len(inventory_parseable_missing_parsed)}",
        f"- 可解析来源缺失 cleaned 数：{len(inventory_parseable_missing_cleaned)}",
        f"- Parsed 文档缺失字段数：{len(parsed_document_missing_fields)}",
        f"- Parsed 文档重复 doc_id 数：{len(parsed_document_duplicate_doc_ids)}",
        f"- Parsed 文档未知 doc_id 数：{len(parsed_document_unknown_doc_ids)}",
        f"- Parsed 文档缺失来源路径数：{len(parsed_document_missing_source_paths)}",
        f"- Parsed 文档未登记来源路径数：{len(parsed_document_unregistered_source_paths)}",
        f"- Parsed 文档路径不一致数：{len(parsed_document_path_mismatches)}",
        f"- Parsed 文档空 sections 数：{len(parsed_document_empty_sections)}",
        f"- Parsed section 缺失字段数：{len(parsed_section_missing_fields)}",
        f"- Parsed section 空内容数：{len(parsed_section_empty_content)}",
        f"- Cleaned 文档缺失标题数：{len(cleaned_document_missing_heading)}",
        f"- Cleaned 文档空正文数：{len(cleaned_document_empty_body)}",
        f"- Cleaned 文档未知 doc_id 数：{len(cleaned_document_unknown_doc_ids)}",
        f"- Cleaned 文档重复 doc_id 数：{len(cleaned_document_duplicate_doc_ids)}",
        f"- Cleaned 文档缺失 parsed 数：{len(cleaned_document_missing_parsed)}",
        f"- Cleaned 文档异常 manual note 数：{len(cleaned_document_unexpected_manual_notes)}",
        f"- Cleaned 文档标题不一致数：{len(cleaned_document_title_mismatches)}",
        f"- Cleaned 文档替换字符数：{len(cleaned_document_replacement_chars)}",
        f"- 缺失必填字段数：{len(missing_fields)}",
        f"- 缺失 chunk 必填字段数：{len(missing_chunk_fields)}",
        f"- 缺失来源引用数：{len(missing_source_refs)}",
        f"- 未知来源引用数：{len(unknown_source_refs)}",
        f"- 未知 chunk doc_id 数：{len(unknown_chunk_doc_ids)}",
        f"- 空 chunk 内容数：{len(empty_chunk_content)}",
        f"- 缺失 chunk 来源路径数：{len(missing_chunk_source_paths)}",
        f"- 超长 chunk 数：{len(oversized_chunks)}",
        f"- 案例观察值缺失字段数：{len(case_observation_missing_fields)}",
        f"- 案例观察值未知 source_id 数：{len(case_observation_unknown_source_ids)}",
        f"- 案例观察值缺失来源路径数：{len(case_observation_missing_source_paths)}",
        f"- 案例观察值重复键数：{len(case_observation_duplicate_keys)}",
        f"- 来源处理状态缺失字段数：{len(source_status_missing_fields)}",
        f"- 来源处理状态未知 source_id 数：{len(source_status_unknown_source_ids)}",
        f"- 来源处理状态重复 source_id 数：{len(source_status_duplicate_source_ids)}",
        f"- 来源处理状态缺失 inventory 行数：{len(source_status_missing_inventory_rows)}",
        f"- 来源缺口队列缺失字段数：{len(source_gap_queue_missing_fields)}",
        f"- 来源缺口队列重复 gap_id 数：{len(source_gap_queue_duplicate_gap_ids)}",
        f"- 来源缺口队列未知 source_id 数：{len(source_gap_queue_unknown_source_ids)}",
        f"- 来源缺口队列状态不一致数：{len(source_gap_queue_status_mismatches)}",
        f"- 来源缺口队列缺失未完成来源数：{len(source_gap_queue_missing_incomplete_sources)}",
        f"- 实体复核队列缺失字段数：{len(entity_review_queue_missing_fields)}",
        f"- 实体复核队列重复 queue_id 数：{len(entity_review_queue_duplicate_queue_ids)}",
        f"- 实体复核队列未知 entity_id 数：{len(entity_review_queue_unknown_entity_ids)}",
        f"- 实体复核队列 entity_type 不一致数：{len(entity_review_queue_entity_type_mismatches)}",
        f"- 实体复核队列未知来源引用数：{len(entity_review_queue_unknown_source_refs)}",
        f"- 实体复核队列 source_ref_count 不一致数：{len(entity_review_queue_source_count_mismatches)}",
        f"- 实体复核队列状态不一致数：{len(entity_review_queue_status_mismatches)}",
        f"- 实体复核队列缺失 pending 实体数：{len(entity_review_queue_missing_pending_entities)}",
        f"- 实体来源证据索引缺失字段数：{len(entity_source_evidence_missing_fields)}",
        f"- 实体来源证据索引重复 evidence_id 数：{len(entity_source_evidence_duplicate_ids)}",
        f"- 实体来源证据索引未知 entity_id 数：{len(entity_source_evidence_unknown_entity_ids)}",
        f"- 实体来源证据索引 entity_type 不一致数：{len(entity_source_evidence_entity_type_mismatches)}",
        f"- 实体来源证据索引未知 source_id 数：{len(entity_source_evidence_unknown_source_ids)}",
        f"- 实体来源证据索引状态不一致数：{len(entity_source_evidence_status_mismatches)}",
        f"- 实体来源证据索引 chunk_count 不一致数：{len(entity_source_evidence_chunk_count_mismatches)}",
        f"- 实体来源证据索引未知 chunk_sample_id 数：{len(entity_source_evidence_unknown_chunk_sample_ids)}",
        f"- 实体来源证据索引路径缺失数：{len(entity_source_evidence_missing_paths)}",
        f"- 实体来源证据索引异常实体来源对数：{len(entity_source_evidence_unexpected_pairs)}",
        f"- 实体来源证据索引缺失实体来源对数：{len(entity_source_evidence_missing_pairs)}",
        f"- 实体人工复核包缺失字段数：{len(entity_review_packet_missing_fields)}",
        f"- 实体人工复核包重复 packet_id 数：{len(entity_review_packet_duplicate_packet_ids)}",
        f"- 实体人工复核包重复或不连续 review_order 数：{len(entity_review_packet_duplicate_orders)}",
        f"- 实体人工复核包未知 entity_id 数：{len(entity_review_packet_unknown_entity_ids)}",
        f"- 实体人工复核包 entity_type 不一致数：{len(entity_review_packet_entity_type_mismatches)}",
        f"- 实体人工复核包 review_status 不一致数：{len(entity_review_packet_status_mismatches)}",
        f"- 实体人工复核包 source_refs 不一致数：{len(entity_review_packet_source_ref_mismatches)}",
        f"- 实体人工复核包 evidence_count 不一致数：{len(entity_review_packet_evidence_count_mismatches)}",
        f"- 实体人工复核包 chunk_count 不一致数：{len(entity_review_packet_chunk_count_mismatches)}",
        f"- 实体人工复核包 case_observation_count 不一致数：{len(entity_review_packet_case_observation_mismatches)}",
        f"- 实体人工复核包来源桶不一致数：{len(entity_review_packet_source_bucket_mismatches)}",
        f"- 实体人工复核包未知来源引用数：{len(entity_review_packet_unknown_source_refs)}",
        f"- 实体人工复核包未知 chunk_sample_id 数：{len(entity_review_packet_unknown_chunk_sample_ids)}",
        f"- 实体人工复核包路径缺失数：{len(entity_review_packet_missing_paths)}",
        f"- 实体人工复核包缺失实体覆盖数：{len(entity_review_packet_missing_entities)}",
        f"- 权威来源补充需求缺失字段数：{len(authoritative_source_requirement_missing_fields)}",
        f"- 权威来源补充需求重复 requirement_id 数：{len(authoritative_source_requirement_duplicate_ids)}",
        f"- 权威来源补充需求未知 entity_id 数：{len(authoritative_source_requirement_unknown_entity_ids)}",
        f"- 权威来源补充需求 entity_type 不一致数：{len(authoritative_source_requirement_entity_type_mismatches)}",
        f"- 权威来源补充需求 source_refs 不一致数：{len(authoritative_source_requirement_source_ref_mismatches)}",
        f"- 权威来源补充需求未知来源引用数：{len(authoritative_source_requirement_unknown_source_refs)}",
        f"- 权威来源补充需求异常实体数：{len(authoritative_source_requirement_unexpected_entities)}",
        f"- 权威来源补充需求缺失 context-only 实体数：{len(authoritative_source_requirement_missing_entities)}",
        f"- 下一步行动队列缺失字段数：{len(next_action_missing_fields)}",
        f"- 下一步行动队列重复 action_id 数：{len(next_action_duplicate_ids)}",
        f"- 下一步行动队列重复或不连续 action_order 数：{len(next_action_duplicate_orders)}",
        f"- 下一步行动队列未知 entity_id 数：{len(next_action_unknown_entity_ids)}",
        f"- 下一步行动队列未知来源引用数：{len(next_action_unknown_source_refs)}",
        f"- 下一步行动队列异常行动数：{len(next_action_unexpected_actions)}",
        f"- 下一步行动队列缺失期望行动数：{len(next_action_missing_expected_actions)}",
        f"- 下一步行动队列 LLM 标记不一致数：{len(next_action_llm_flag_mismatches)}",
        f"- 人工复核工作簿缺失字段数：{len(human_review_workbook_missing_fields)}",
        f"- 人工复核工作簿重复 workbook_id 数：{len(human_review_workbook_duplicate_ids)}",
        f"- 人工复核工作簿重复或不连续 review_order 数：{len(human_review_workbook_duplicate_orders)}",
        f"- 人工复核工作簿未知 entity_id 数：{len(human_review_workbook_unknown_entity_ids)}",
        f"- 人工复核工作簿 entity_type 不一致数：{len(human_review_workbook_entity_type_mismatches)}",
        f"- 人工复核工作簿 source_refs 不一致数：{len(human_review_workbook_source_ref_mismatches)}",
        f"- 人工复核工作簿未知来源引用数：{len(human_review_workbook_unknown_source_refs)}",
        f"- 人工复核工作簿未知 chunk_sample_id 数：{len(human_review_workbook_unknown_chunk_sample_ids)}",
        f"- 人工复核工作簿路径缺失数：{len(human_review_workbook_missing_paths)}",
        f"- 人工复核工作簿 packet 引用不一致数：{len(human_review_workbook_packet_mismatches)}",
        f"- 人工复核工作簿 action 引用不一致数：{len(human_review_workbook_action_mismatches)}",
        f"- 人工复核工作簿默认决策不一致数：{len(human_review_workbook_decision_mismatches)}",
        f"- 人工复核工作簿缺失实体覆盖数：{len(human_review_workbook_missing_entities)}",
        f"- 人工复核决策审计缺失字段数：{len(human_review_decision_audit_missing_fields)}",
        f"- 人工复核决策审计重复 audit_id 数：{len(human_review_decision_audit_duplicate_ids)}",
        f"- 人工复核决策审计未知 entity_id 数：{len(human_review_decision_audit_unknown_entity_ids)}",
        f"- 人工复核决策审计 entity_type 不一致数：{len(human_review_decision_audit_entity_type_mismatches)}",
        f"- 人工复核决策审计 workbook 引用不一致数：{len(human_review_decision_audit_workbook_mismatches)}",
        f"- 人工复核决策审计状态不一致数：{len(human_review_decision_audit_status_mismatches)}",
        f"- 人工复核决策审计缺失实体覆盖数：{len(human_review_decision_audit_missing_entities)}",
        f"- 人工复核决策输入非法行数：{len(review_input_invalid_rows)}",
        f"- 人工复核决策输入未知实体数：{len(human_review_input_unknown_entities)}",
        f"- 人工复核决策应用预览缺失字段数：{len(human_review_apply_preview_missing_fields)}",
        f"- 人工复核决策应用预览重复 preview_id 数：{len(human_review_apply_preview_duplicate_ids)}",
        f"- 人工复核决策应用预览缺失 summary 数：{len(human_review_apply_preview_missing_summary)}",
        f"- 人工复核决策应用预览运行模式不一致数：{len(human_review_apply_preview_run_mode_mismatches)}",
        f"- 人工复核决策应用预览计数不一致数：{len(human_review_apply_preview_count_mismatches)}",
        f"- 人工复核输入校验缺失字段数：{len(human_review_input_validation_missing_fields)}",
        f"- 人工复核输入校验重复 validation_id 数：{len(human_review_input_validation_duplicate_ids)}",
        f"- 人工复核输入校验顺序/状态不一致数：{len(human_review_input_validation_order_mismatches)}",
        f"- 人工复核输入校验缺失检查项数：{len(human_review_input_validation_missing_checks)}",
        f"- 人工复核输入校验失败记录数：{len(human_review_input_validation_failure_records)}",
        f"- 人工复核输入校验 LLM 边界不一致数：{len(human_review_input_validation_llm_mismatches)}",
        f"- 人工复核进度缺失字段数：{len(human_review_progress_missing_fields)}",
        f"- 人工复核进度重复 progress_id 数：{len(human_review_progress_duplicate_ids)}",
        f"- 人工复核进度计数不一致数：{len(human_review_progress_count_mismatches)}",
        f"- 人工复核进度缺失 overall 数：{len(human_review_progress_missing_overall)}",
        f"- 人工复核证据摘录缺失字段数：{len(human_review_evidence_extract_missing_fields)}",
        f"- 人工复核证据摘录重复 extract_id 数：{len(human_review_evidence_extract_duplicate_ids)}",
        f"- 人工复核证据摘录未知 entity_id 数：{len(human_review_evidence_extract_unknown_entity_ids)}",
        f"- 人工复核证据摘录 entity_type 不一致数：{len(human_review_evidence_extract_entity_type_mismatches)}",
        f"- 人工复核证据摘录未知 chunk_id 数：{len(human_review_evidence_extract_unknown_chunk_ids)}",
        f"- 人工复核证据摘录 chunk 元数据不一致数：{len(human_review_evidence_extract_path_mismatches)}",
        f"- 人工复核证据摘录长度不一致数：{len(human_review_evidence_extract_length_mismatches)}",
        f"- 人工复核证据摘录 LLM 标记不一致数：{len(human_review_evidence_extract_llm_mismatches)}",
        f"- 人工复核证据摘录缺失实体覆盖数：{len(human_review_evidence_extract_missing_entities)}",
        f"- 人工复核会话队列缺失字段数：{len(human_review_session_queue_missing_fields)}",
        f"- 人工复核会话队列重复 session_item_id 数：{len(human_review_session_queue_duplicate_ids)}",
        f"- 人工复核会话队列未知 entity_id 数：{len(human_review_session_queue_unknown_entity_ids)}",
        f"- 人工复核会话队列 entity_type 不一致数：{len(human_review_session_queue_entity_type_mismatches)}",
        f"- 人工复核会话队列未知 extract_id 数：{len(human_review_session_queue_unknown_extract_ids)}",
        f"- 人工复核会话队列未知 chunk_id 数：{len(human_review_session_queue_unknown_chunk_ids)}",
        f"- 人工复核会话队列顺序不一致数：{len(human_review_session_queue_order_mismatches)}",
        f"- 人工复核会话队列 LLM 标记不一致数：{len(human_review_session_queue_llm_mismatches)}",
        f"- 人工复核会话队列缺失实体覆盖数：{len(human_review_session_queue_missing_entities)}",
        f"- 人工复核会话状态缺失字段数：{len(human_review_session_status_missing_fields)}",
        f"- 人工复核会话状态重复 session_status_id 数：{len(human_review_session_status_duplicate_ids)}",
        f"- 人工复核会话状态未知 session 数：{len(human_review_session_status_unknown_sessions)}",
        f"- 人工复核会话状态缺失 session 覆盖数：{len(human_review_session_status_missing_sessions)}",
        f"- 人工复核会话状态计数不一致数：{len(human_review_session_status_count_mismatches)}",
        f"- 人工复核会话状态顺序不一致数：{len(human_review_session_status_order_mismatches)}",
        f"- 人工复核会话状态下一实体不一致数：{len(human_review_session_status_next_mismatches)}",
        f"- 人工复核会话状态 LLM 标记不一致数：{len(human_review_session_status_llm_mismatches)}",
        f"- 人工复核逐字段清单缺失字段数：{len(human_review_field_checklist_missing_fields)}",
        f"- 人工复核逐字段清单重复 field_check_id 数：{len(human_review_field_checklist_duplicate_ids)}",
        f"- 人工复核逐字段清单未知 entity_id 数：{len(human_review_field_checklist_unknown_entity_ids)}",
        f"- 人工复核逐字段清单 entity_type 不一致数：{len(human_review_field_checklist_entity_type_mismatches)}",
        f"- 人工复核逐字段清单 session 不一致数：{len(human_review_field_checklist_session_mismatches)}",
        f"- 人工复核逐字段清单字段覆盖不一致数：{len(human_review_field_checklist_field_mismatches)}",
        f"- 人工复核逐字段清单字段值不一致数：{len(human_review_field_checklist_value_mismatches)}",
        f"- 人工复核逐字段清单 JSON 值错误数：{len(human_review_field_checklist_json_errors)}",
        f"- 人工复核逐字段清单默认状态不一致数：{len(human_review_field_checklist_default_mismatches)}",
        f"- 人工复核逐字段清单缺失实体覆盖数：{len(human_review_field_checklist_missing_entities)}",
        f"- 人工复核来源矩阵缺失字段数：{len(human_review_source_matrix_missing_fields)}",
        f"- 人工复核来源矩阵重复 source_matrix_id 数：{len(human_review_source_matrix_duplicate_ids)}",
        f"- 人工复核来源矩阵未知 source_id 数：{len(human_review_source_matrix_unknown_source_ids)}",
        f"- 人工复核来源矩阵缺失来源覆盖数：{len(human_review_source_matrix_missing_sources)}",
        f"- 人工复核来源矩阵计数不一致数：{len(human_review_source_matrix_count_mismatches)}",
        f"- 人工复核来源矩阵上下文不一致数：{len(human_review_source_matrix_context_mismatches)}",
        f"- 人工复核来源矩阵列表不一致数：{len(human_review_source_matrix_list_mismatches)}",
        f"- 人工复核任务板缺失字段数：{len(human_review_task_board_missing_fields)}",
        f"- 人工复核任务板重复 task_id 数：{len(human_review_task_board_duplicate_ids)}",
        f"- 人工复核任务板顺序不一致数：{len(human_review_task_board_order_mismatches)}",
        f"- 人工复核任务板缺失 session 任务数：{len(human_review_task_board_missing_session_tasks)}",
        f"- 人工复核任务板缺失工作流任务数：{len(human_review_task_board_missing_workflow_tasks)}",
        f"- 人工复核任务板未知 session 任务数：{len(human_review_task_board_unknown_session_tasks)}",
        f"- 人工复核任务板未知 source 任务数：{len(human_review_task_board_unknown_source_tasks)}",
        f"- 人工复核任务板命令不一致数：{len(human_review_task_board_command_mismatches)}",
        f"- 人工复核任务板默认状态不一致数：{len(human_review_task_board_default_mismatches)}",
        f"- 人工复核交接清单缺失字段数：{len(human_review_handoff_missing_fields)}",
        f"- 人工复核交接清单重复 handoff_id 数：{len(human_review_handoff_duplicate_ids)}",
        f"- 人工复核交接清单重复 task_id 数：{len(human_review_handoff_duplicate_task_ids)}",
        f"- 人工复核交接清单未知 task_id 数：{len(human_review_handoff_unknown_task_ids)}",
        f"- 人工复核交接清单缺失 task_id 数：{len(human_review_handoff_missing_task_ids)}",
        f"- 人工复核交接清单上下文不一致数：{len(human_review_handoff_context_mismatches)}",
        f"- 人工复核交接清单路径标记不一致数：{len(human_review_handoff_path_mismatches)}",
        f"- 人工复核交接清单命令不一致数：{len(human_review_handoff_command_mismatches)}",
        f"- 人工复核交接清单默认状态不一致数：{len(human_review_handoff_default_mismatches)}",
        f"- 人工复核会话决策模板缺失文件数：{len(human_review_session_decision_template_missing_files)}",
        f"- 人工复核会话决策模板多余文件数：{len(human_review_session_decision_template_extra_files)}",
        f"- 人工复核会话决策模板表头不一致数：{len(human_review_session_decision_template_header_mismatches)}",
        f"- 人工复核会话决策模板行不一致数：{len(human_review_session_decision_template_row_mismatches)}",
        f"- 人工复核会话决策模板默认决策不一致数：{len(human_review_session_decision_template_default_decision_mismatches)}",
        f"- 人工复核会话决策模板上下文不一致数：{len(human_review_session_decision_template_context_mismatches)}",
        f"- 人工复核会话决策模板读取错误数：{len(human_review_session_decision_template_read_errors)}",
        f"- 术语表缺失字段数：{len(glossary_missing_fields)}",
        f"- 术语表重复 term_id 数：{len(glossary_duplicate_term_ids)}",
        f"- 术语表未知 entity_id 数：{len(glossary_unknown_entity_ids)}",
        f"- 术语表 entity_type 不一致数：{len(glossary_entity_type_mismatches)}",
        f"- 术语表未知来源引用数：{len(glossary_unknown_source_refs)}",
        f"- 术语表缺失实体覆盖数：{len(glossary_missing_entity_ids)}",
        f"- 制品清单缺失字段数：{len(artifact_missing_fields)}",
        f"- 制品清单重复路径数：{len(artifact_duplicate_paths)}",
        f"- 制品清单缺失文件数：{len(artifact_missing_files)}",
        f"- 制品清单未知文件数：{len(artifact_unknown_files)}",
        f"- 制品清单未登记文件数：{len(artifact_unregistered_files)}",
        f"- 制品清单大小不一致数：{len(artifact_size_mismatches)}",
        f"- 制品清单行数不一致数：{len(artifact_line_count_mismatches)}",
        f"- 制品清单二进制标记不一致数：{len(artifact_binary_flag_mismatches)}",
        f"- 制品清单 SHA-256 不一致数：{len(artifact_sha256_mismatches)}",
        f"- 报告目录布局违规数：{len(report_layout_violations)}",
        f"- 报告策略缺失文件数：{len(report_missing_policy_paths)}",
        f"- 报告策略缺失目录数：{len(report_missing_directory_paths)}",
        f"- 未登记报告文件数：{len(report_unregistered_files)}",
        f"- 非法 generated 报告分区数：{len(report_invalid_generated_categories)}",
        f"- 重复关系数：{len(duplicate_relationships)}",
        f"- 关系未知来源引用数：{len(relationship_unknown_source_refs)}",
        f"- 关系 confidence 越界数：{len(relationship_invalid_confidence)}",
        f"- 孤立关系数：{len(orphan_relationships)}",
        f"- 缺少证据模板的异常类型数：{len(anomalies_without_templates)}",
        f"- 缺少局限性说明的数据源数：{len(data_sources_without_limitations)}",
        "",
        "## 按实体类型统计",
        "",
    ]
    for entity_type, count in sorted(counts_by_type.items()):
        lines.append(f"- {entity_type}：{count} 条记录，{pending_by_type[entity_type]} 条 pending")

    lines.extend(["", "## 按 Chunk 文件统计", ""])
    for filename, count in sorted(chunk_file_counts.items()):
        lines.append(f"- {filename}：{count} 条记录")

    lines.extend(["", "## 按 Parsed 子目录统计", ""])
    for dirname, count in sorted(parsed_document_counts_by_subdir.items()):
        lines.append(f"- {dirname}：{count} 个文档")

    lines.extend(["", "## 按 Cleaned 子目录统计", ""])
    for dirname, count in sorted(cleaned_document_counts_by_subdir.items()):
        lines.append(f"- {dirname}：{count} 个文档")

    sections = [
        ("JSON 错误", errors),
        ("Schema 错误", schema_errors),
        ("语料画像阻断问题", corpus_profile_blockers),
        ("清洗 v2 发布门禁阻断问题", cleaning_v2_release_gate_blockers),
        ("重复 source_id", duplicate_source_ids),
        ("重复实体 ID", duplicate_ids),
        ("重复 chunk ID", duplicate_chunk_ids),
        ("未归档来源", inventory_missing_paths),
        ("来源清单本地文件缺失", inventory_missing_raw_files),
        ("raw 文件未登记", raw_files_without_inventory),
        ("可解析来源缺失 parsed", inventory_parseable_missing_parsed),
        ("可解析来源缺失 cleaned", inventory_parseable_missing_cleaned),
        ("Parsed 文档缺失字段", parsed_document_missing_fields),
        ("Parsed 文档重复 doc_id", parsed_document_duplicate_doc_ids),
        ("Parsed 文档未知 doc_id", parsed_document_unknown_doc_ids),
        ("Parsed 文档缺失来源路径", parsed_document_missing_source_paths),
        ("Parsed 文档未登记来源路径", parsed_document_unregistered_source_paths),
        ("Parsed 文档路径不一致", parsed_document_path_mismatches),
        ("Parsed 文档空 sections", parsed_document_empty_sections),
        ("Parsed section 缺失字段", parsed_section_missing_fields),
        ("Parsed section 空内容", parsed_section_empty_content),
        ("Cleaned 文档缺失标题", cleaned_document_missing_heading),
        ("Cleaned 文档空正文", cleaned_document_empty_body),
        ("Cleaned 文档未知 doc_id", cleaned_document_unknown_doc_ids),
        ("Cleaned 文档重复 doc_id", cleaned_document_duplicate_doc_ids),
        ("Cleaned 文档缺失 parsed", cleaned_document_missing_parsed),
        ("Cleaned 文档异常 manual note", cleaned_document_unexpected_manual_notes),
        ("Cleaned 文档标题不一致", cleaned_document_title_mismatches),
        ("Cleaned 文档替换字符", cleaned_document_replacement_chars),
        ("缺失必填字段", missing_fields),
        ("缺失 chunk 必填字段", missing_chunk_fields),
        ("缺失来源引用", missing_source_refs),
        ("未知来源引用", unknown_source_refs),
        ("未知 chunk doc_id", unknown_chunk_doc_ids),
        ("空 chunk 内容", empty_chunk_content),
        ("缺失 chunk 来源路径", missing_chunk_source_paths),
        ("超长 chunk", oversized_chunks),
        ("案例观察值缺失字段", case_observation_missing_fields),
        ("案例观察值未知 source_id", case_observation_unknown_source_ids),
        ("案例观察值缺失来源路径", case_observation_missing_source_paths),
        ("案例观察值重复键", case_observation_duplicate_keys),
        ("来源处理状态缺失字段", source_status_missing_fields),
        ("来源处理状态未知 source_id", source_status_unknown_source_ids),
        ("来源处理状态重复 source_id", source_status_duplicate_source_ids),
        ("来源处理状态缺失 inventory 行", source_status_missing_inventory_rows),
        ("来源缺口队列缺失字段", source_gap_queue_missing_fields),
        ("来源缺口队列重复 gap_id", source_gap_queue_duplicate_gap_ids),
        ("来源缺口队列未知 source_id", source_gap_queue_unknown_source_ids),
        ("来源缺口队列状态不一致", source_gap_queue_status_mismatches),
        ("来源缺口队列缺失未完成来源", source_gap_queue_missing_incomplete_sources),
        ("实体复核队列缺失字段", entity_review_queue_missing_fields),
        ("实体复核队列重复 queue_id", entity_review_queue_duplicate_queue_ids),
        ("实体复核队列未知 entity_id", entity_review_queue_unknown_entity_ids),
        ("实体复核队列 entity_type 不一致", entity_review_queue_entity_type_mismatches),
        ("实体复核队列未知来源引用", entity_review_queue_unknown_source_refs),
        ("实体复核队列 source_ref_count 不一致", entity_review_queue_source_count_mismatches),
        ("实体复核队列状态不一致", entity_review_queue_status_mismatches),
        ("实体复核队列缺失 pending 实体", entity_review_queue_missing_pending_entities),
        ("实体来源证据索引缺失字段", entity_source_evidence_missing_fields),
        ("实体来源证据索引重复 evidence_id", entity_source_evidence_duplicate_ids),
        ("实体来源证据索引未知 entity_id", entity_source_evidence_unknown_entity_ids),
        ("实体来源证据索引 entity_type 不一致", entity_source_evidence_entity_type_mismatches),
        ("实体来源证据索引未知 source_id", entity_source_evidence_unknown_source_ids),
        ("实体来源证据索引状态不一致", entity_source_evidence_status_mismatches),
        ("实体来源证据索引 chunk_count 不一致", entity_source_evidence_chunk_count_mismatches),
        ("实体来源证据索引未知 chunk_sample_id", entity_source_evidence_unknown_chunk_sample_ids),
        ("实体来源证据索引路径缺失", entity_source_evidence_missing_paths),
        ("实体来源证据索引异常实体来源对", entity_source_evidence_unexpected_pairs),
        ("实体来源证据索引缺失实体来源对", entity_source_evidence_missing_pairs),
        ("实体人工复核包缺失字段", entity_review_packet_missing_fields),
        ("实体人工复核包重复 packet_id", entity_review_packet_duplicate_packet_ids),
        ("实体人工复核包重复或不连续 review_order", entity_review_packet_duplicate_orders),
        ("实体人工复核包未知 entity_id", entity_review_packet_unknown_entity_ids),
        ("实体人工复核包 entity_type 不一致", entity_review_packet_entity_type_mismatches),
        ("实体人工复核包 review_status 不一致", entity_review_packet_status_mismatches),
        ("实体人工复核包 source_refs 不一致", entity_review_packet_source_ref_mismatches),
        ("实体人工复核包 evidence_count 不一致", entity_review_packet_evidence_count_mismatches),
        ("实体人工复核包 chunk_count 不一致", entity_review_packet_chunk_count_mismatches),
        ("实体人工复核包 case_observation_count 不一致", entity_review_packet_case_observation_mismatches),
        ("实体人工复核包来源桶不一致", entity_review_packet_source_bucket_mismatches),
        ("实体人工复核包未知来源引用", entity_review_packet_unknown_source_refs),
        ("实体人工复核包未知 chunk_sample_id", entity_review_packet_unknown_chunk_sample_ids),
        ("实体人工复核包路径缺失", entity_review_packet_missing_paths),
        ("实体人工复核包缺失实体覆盖", entity_review_packet_missing_entities),
        ("权威来源补充需求缺失字段", authoritative_source_requirement_missing_fields),
        ("权威来源补充需求重复 requirement_id", authoritative_source_requirement_duplicate_ids),
        ("权威来源补充需求未知 entity_id", authoritative_source_requirement_unknown_entity_ids),
        ("权威来源补充需求 entity_type 不一致", authoritative_source_requirement_entity_type_mismatches),
        ("权威来源补充需求 source_refs 不一致", authoritative_source_requirement_source_ref_mismatches),
        ("权威来源补充需求未知来源引用", authoritative_source_requirement_unknown_source_refs),
        ("权威来源补充需求异常实体", authoritative_source_requirement_unexpected_entities),
        ("权威来源补充需求缺失 context-only 实体", authoritative_source_requirement_missing_entities),
        ("下一步行动队列缺失字段", next_action_missing_fields),
        ("下一步行动队列重复 action_id", next_action_duplicate_ids),
        ("下一步行动队列重复或不连续 action_order", next_action_duplicate_orders),
        ("下一步行动队列未知 entity_id", next_action_unknown_entity_ids),
        ("下一步行动队列未知来源引用", next_action_unknown_source_refs),
        ("下一步行动队列异常行动", next_action_unexpected_actions),
        ("下一步行动队列缺失期望行动", next_action_missing_expected_actions),
        ("下一步行动队列 LLM 标记不一致", next_action_llm_flag_mismatches),
        ("人工复核工作簿缺失字段", human_review_workbook_missing_fields),
        ("人工复核工作簿重复 workbook_id", human_review_workbook_duplicate_ids),
        ("人工复核工作簿重复或不连续 review_order", human_review_workbook_duplicate_orders),
        ("人工复核工作簿未知 entity_id", human_review_workbook_unknown_entity_ids),
        ("人工复核工作簿 entity_type 不一致", human_review_workbook_entity_type_mismatches),
        ("人工复核工作簿 source_refs 不一致", human_review_workbook_source_ref_mismatches),
        ("人工复核工作簿未知来源引用", human_review_workbook_unknown_source_refs),
        ("人工复核工作簿未知 chunk_sample_id", human_review_workbook_unknown_chunk_sample_ids),
        ("人工复核工作簿路径缺失", human_review_workbook_missing_paths),
        ("人工复核工作簿 packet 引用不一致", human_review_workbook_packet_mismatches),
        ("人工复核工作簿 action 引用不一致", human_review_workbook_action_mismatches),
        ("人工复核工作簿默认决策不一致", human_review_workbook_decision_mismatches),
        ("人工复核工作簿缺失实体覆盖", human_review_workbook_missing_entities),
        ("人工复核决策审计缺失字段", human_review_decision_audit_missing_fields),
        ("人工复核决策审计重复 audit_id", human_review_decision_audit_duplicate_ids),
        ("人工复核决策审计未知 entity_id", human_review_decision_audit_unknown_entity_ids),
        ("人工复核决策审计 entity_type 不一致", human_review_decision_audit_entity_type_mismatches),
        ("人工复核决策审计 workbook 引用不一致", human_review_decision_audit_workbook_mismatches),
        ("人工复核决策审计状态不一致", human_review_decision_audit_status_mismatches),
        ("人工复核决策审计缺失实体覆盖", human_review_decision_audit_missing_entities),
        ("人工复核决策输入非法行", review_input_invalid_rows),
        ("人工复核决策输入未知实体", human_review_input_unknown_entities),
        ("人工复核决策应用预览缺失字段", human_review_apply_preview_missing_fields),
        ("人工复核决策应用预览重复 preview_id", human_review_apply_preview_duplicate_ids),
        ("人工复核决策应用预览缺失 summary", human_review_apply_preview_missing_summary),
        ("人工复核决策应用预览运行模式不一致", human_review_apply_preview_run_mode_mismatches),
        ("人工复核决策应用预览计数不一致", human_review_apply_preview_count_mismatches),
        ("人工复核输入校验缺失字段", human_review_input_validation_missing_fields),
        ("人工复核输入校验重复 validation_id", human_review_input_validation_duplicate_ids),
        ("人工复核输入校验顺序/状态不一致", human_review_input_validation_order_mismatches),
        ("人工复核输入校验缺失检查项", human_review_input_validation_missing_checks),
        ("人工复核输入校验失败记录", human_review_input_validation_failure_records),
        ("人工复核输入校验 LLM 边界不一致", human_review_input_validation_llm_mismatches),
        ("人工复核进度缺失字段", human_review_progress_missing_fields),
        ("人工复核进度重复 progress_id", human_review_progress_duplicate_ids),
        ("人工复核进度计数不一致", human_review_progress_count_mismatches),
        ("人工复核进度缺失 overall", human_review_progress_missing_overall),
        ("人工复核证据摘录缺失字段", human_review_evidence_extract_missing_fields),
        ("人工复核证据摘录重复 extract_id", human_review_evidence_extract_duplicate_ids),
        ("人工复核证据摘录未知 entity_id", human_review_evidence_extract_unknown_entity_ids),
        ("人工复核证据摘录 entity_type 不一致", human_review_evidence_extract_entity_type_mismatches),
        ("人工复核证据摘录未知 chunk_id", human_review_evidence_extract_unknown_chunk_ids),
        ("人工复核证据摘录 chunk 元数据不一致", human_review_evidence_extract_path_mismatches),
        ("人工复核证据摘录长度不一致", human_review_evidence_extract_length_mismatches),
        ("人工复核证据摘录 LLM 标记不一致", human_review_evidence_extract_llm_mismatches),
        ("人工复核证据摘录缺失实体覆盖", human_review_evidence_extract_missing_entities),
        ("人工复核会话队列缺失字段", human_review_session_queue_missing_fields),
        ("人工复核会话队列重复 session_item_id", human_review_session_queue_duplicate_ids),
        ("人工复核会话队列未知 entity_id", human_review_session_queue_unknown_entity_ids),
        ("人工复核会话队列 entity_type 不一致", human_review_session_queue_entity_type_mismatches),
        ("人工复核会话队列未知 extract_id", human_review_session_queue_unknown_extract_ids),
        ("人工复核会话队列未知 chunk_id", human_review_session_queue_unknown_chunk_ids),
        ("人工复核会话队列顺序不一致", human_review_session_queue_order_mismatches),
        ("人工复核会话队列 LLM 标记不一致", human_review_session_queue_llm_mismatches),
        ("人工复核会话队列缺失实体覆盖", human_review_session_queue_missing_entities),
        ("人工复核会话状态缺失字段", human_review_session_status_missing_fields),
        ("人工复核会话状态重复 session_status_id", human_review_session_status_duplicate_ids),
        ("人工复核会话状态未知 session", human_review_session_status_unknown_sessions),
        ("人工复核会话状态缺失 session 覆盖", human_review_session_status_missing_sessions),
        ("人工复核会话状态计数不一致", human_review_session_status_count_mismatches),
        ("人工复核会话状态顺序不一致", human_review_session_status_order_mismatches),
        ("人工复核会话状态下一实体不一致", human_review_session_status_next_mismatches),
        ("人工复核会话状态 LLM 标记不一致", human_review_session_status_llm_mismatches),
        ("人工复核逐字段清单缺失字段", human_review_field_checklist_missing_fields),
        ("人工复核逐字段清单重复 field_check_id", human_review_field_checklist_duplicate_ids),
        ("人工复核逐字段清单未知 entity_id", human_review_field_checklist_unknown_entity_ids),
        ("人工复核逐字段清单 entity_type 不一致", human_review_field_checklist_entity_type_mismatches),
        ("人工复核逐字段清单 session 不一致", human_review_field_checklist_session_mismatches),
        ("人工复核逐字段清单字段覆盖不一致", human_review_field_checklist_field_mismatches),
        ("人工复核逐字段清单字段值不一致", human_review_field_checklist_value_mismatches),
        ("人工复核逐字段清单 JSON 值错误", human_review_field_checklist_json_errors),
        ("人工复核逐字段清单默认状态不一致", human_review_field_checklist_default_mismatches),
        ("人工复核逐字段清单缺失实体覆盖", human_review_field_checklist_missing_entities),
        ("人工复核来源矩阵缺失字段", human_review_source_matrix_missing_fields),
        ("人工复核来源矩阵重复 source_matrix_id", human_review_source_matrix_duplicate_ids),
        ("人工复核来源矩阵未知 source_id", human_review_source_matrix_unknown_source_ids),
        ("人工复核来源矩阵缺失来源覆盖", human_review_source_matrix_missing_sources),
        ("人工复核来源矩阵计数不一致", human_review_source_matrix_count_mismatches),
        ("人工复核来源矩阵上下文不一致", human_review_source_matrix_context_mismatches),
        ("人工复核来源矩阵列表不一致", human_review_source_matrix_list_mismatches),
        ("人工复核任务板缺失字段", human_review_task_board_missing_fields),
        ("人工复核任务板重复 task_id", human_review_task_board_duplicate_ids),
        ("人工复核任务板顺序不一致", human_review_task_board_order_mismatches),
        ("人工复核任务板缺失 session 任务", human_review_task_board_missing_session_tasks),
        ("人工复核任务板缺失工作流任务", human_review_task_board_missing_workflow_tasks),
        ("人工复核任务板未知 session 任务", human_review_task_board_unknown_session_tasks),
        ("人工复核任务板未知 source 任务", human_review_task_board_unknown_source_tasks),
        ("人工复核任务板命令不一致", human_review_task_board_command_mismatches),
        ("人工复核任务板默认状态不一致", human_review_task_board_default_mismatches),
        ("人工复核交接清单缺失字段", human_review_handoff_missing_fields),
        ("人工复核交接清单重复 handoff_id", human_review_handoff_duplicate_ids),
        ("人工复核交接清单重复 task_id", human_review_handoff_duplicate_task_ids),
        ("人工复核交接清单未知 task_id", human_review_handoff_unknown_task_ids),
        ("人工复核交接清单缺失 task_id", human_review_handoff_missing_task_ids),
        ("人工复核交接清单上下文不一致", human_review_handoff_context_mismatches),
        ("人工复核交接清单路径标记不一致", human_review_handoff_path_mismatches),
        ("人工复核交接清单命令不一致", human_review_handoff_command_mismatches),
        ("人工复核交接清单默认状态不一致", human_review_handoff_default_mismatches),
        ("人工复核会话决策模板缺失文件", human_review_session_decision_template_missing_files),
        ("人工复核会话决策模板多余文件", human_review_session_decision_template_extra_files),
        ("人工复核会话决策模板表头不一致", human_review_session_decision_template_header_mismatches),
        ("人工复核会话决策模板行不一致", human_review_session_decision_template_row_mismatches),
        ("人工复核会话决策模板默认决策不一致", human_review_session_decision_template_default_decision_mismatches),
        ("人工复核会话决策模板上下文不一致", human_review_session_decision_template_context_mismatches),
        ("人工复核会话决策模板读取错误", human_review_session_decision_template_read_errors),
        ("术语表缺失字段", glossary_missing_fields),
        ("术语表重复 term_id", glossary_duplicate_term_ids),
        ("术语表未知 entity_id", glossary_unknown_entity_ids),
        ("术语表 entity_type 不一致", glossary_entity_type_mismatches),
        ("术语表未知来源引用", glossary_unknown_source_refs),
        ("术语表缺失实体覆盖", glossary_missing_entity_ids),
        ("制品清单缺失字段", artifact_missing_fields),
        ("制品清单重复路径", artifact_duplicate_paths),
        ("制品清单缺失文件", artifact_missing_files),
        ("制品清单未知文件", artifact_unknown_files),
        ("制品清单未登记文件", artifact_unregistered_files),
        ("制品清单大小不一致", artifact_size_mismatches),
        ("制品清单行数不一致", artifact_line_count_mismatches),
        ("制品清单二进制标记不一致", artifact_binary_flag_mismatches),
        ("制品清单 SHA-256 不一致", artifact_sha256_mismatches),
        ("报告目录布局违规", report_layout_violations),
        ("报告策略缺失文件", report_missing_policy_paths),
        ("报告策略缺失目录", report_missing_directory_paths),
        ("未登记报告文件", report_unregistered_files),
        ("非法 generated 报告分区", report_invalid_generated_categories),
        ("重复关系", duplicate_relationships),
        ("关系未知来源引用", relationship_unknown_source_refs),
        ("关系 confidence 越界", relationship_invalid_confidence),
        ("孤立关系", orphan_relationships),
        ("缺少证据模板的异常类型", anomalies_without_templates),
        ("缺少局限性说明的数据源", data_sources_without_limitations),
    ]
    for title, items in sections:
        lines.extend(["", f"## {title}", ""])
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append("- 无")

    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {paths.rel(REPORT_FILE)}")
    issue_count = sum(len(items) for _, items in sections)
    if issue_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
