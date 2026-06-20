#!/usr/bin/env python3
import argparse
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "published" / "bgp_knowledge_base.sqlite"


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


def print_json(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def entity(conn, entity_id):
    row = conn.execute(
        """
        SELECT entity_id, entity_type, name, category, review_status,
               source_ref_count, evidence_record_count, chunk_count,
               case_observation_count, review_bucket, entity_file, payload_json
        FROM entities
        WHERE entity_id = ?
        """,
        (entity_id,),
    ).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))
    result["sources"] = rows_to_dicts(conn.execute(
        """
        SELECT s.source_id, s.title, s.source_type, s.trust_level, s.processing_status, s.path, s.url
        FROM entity_sources es
        JOIN sources s ON s.source_id = es.source_id
        WHERE es.entity_id = ?
        ORDER BY s.source_type, s.source_id
        """,
        (entity_id,),
    ))
    result["outgoing_relationships"] = rows_to_dicts(conn.execute(
        """
        SELECT relation, dst_id, dst_type, confidence, source_refs_json
        FROM relationships
        WHERE src_id = ?
        ORDER BY relation, dst_id
        """,
        (entity_id,),
    ))
    result["incoming_relationships"] = rows_to_dicts(conn.execute(
        """
        SELECT relation, src_id, src_type, confidence, source_refs_json
        FROM relationships
        WHERE dst_id = ?
        ORDER BY relation, src_id
        """,
        (entity_id,),
    ))
    result["evidence"] = rows_to_dicts(conn.execute(
        """
        SELECT evidence_id, source_id, source_type, source_status, source_path,
               parsed_path, cleaned_path, chunk_count, case_observation_count,
               chunk_sample_ids_json
        FROM entity_evidence
        WHERE entity_id = ?
        ORDER BY source_status, source_type, source_id
        """,
        (entity_id,),
    ))
    result["review_packets"] = rows_to_dicts(conn.execute(
        """
        SELECT packet_id, review_order, review_bucket, evidence_record_count,
               total_chunk_count, suggested_action
        FROM review_packets
        WHERE entity_id = ?
        ORDER BY review_order
        """,
        (entity_id,),
    ))
    result["actions"] = rows_to_dicts(conn.execute(
        """
        SELECT action_id, action_order, priority, action_type, status,
               needs_llm, suggested_action
        FROM next_actions
        WHERE entity_id = ?
        ORDER BY priority, action_order
        """,
        (entity_id,),
    ))
    return result


def term(conn, term, limit):
    normalized = term.lower()
    return {
        "term": normalized,
        "entities": rows_to_dicts(conn.execute(
            """
            SELECT e.entity_id, e.entity_type, e.name, e.review_status
            FROM lexical_entity_refs ler
            JOIN entities e ON e.entity_id = ler.entity_id
            WHERE ler.term = ?
            ORDER BY e.entity_type, e.name
            LIMIT ?
            """,
            (normalized, limit),
        )),
        "sources": rows_to_dicts(conn.execute(
            """
            SELECT s.source_id, s.title, s.source_type, s.processing_status
            FROM lexical_source_refs lsr
            JOIN sources s ON s.source_id = lsr.source_id
            WHERE lsr.term = ?
            ORDER BY s.source_type, s.source_id
            LIMIT ?
            """,
            (normalized, limit),
        )),
        "chunks": rows_to_dicts(conn.execute(
            """
            SELECT c.chunk_id, c.doc_id, c.title, c.source_type, c.content_chars, c.content_preview
            FROM lexical_chunk_refs lcr
            JOIN chunks c ON c.chunk_id = lcr.chunk_id
            WHERE lcr.term = ?
            ORDER BY c.doc_id, c.chunk_id
            LIMIT ?
            """,
            (normalized, limit),
        )),
    }


def search_entities(conn, query, limit):
    try:
        rows = conn.execute(
            """
            SELECT e.entity_id, e.entity_type, e.name, e.review_status,
                   bm25(entity_fts) AS score
            FROM entity_fts
            JOIN entities e ON e.entity_id = entity_fts.entity_id
            WHERE entity_fts MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
    except sqlite3.OperationalError:
        rows = conn.execute(
            """
            SELECT entity_id, entity_type, name, review_status, 0.0 AS score
            FROM entities
            WHERE lower(name) LIKE ?
               OR lower(entity_type) LIKE ?
               OR lower(category) LIKE ?
               OR lower(payload_json) LIKE ?
            ORDER BY entity_type, name
            LIMIT ?
            """,
            tuple([f"%{query.lower()}%"] * 4) + (limit,),
        ).fetchall()
    return rows_to_dicts(rows)


def search_chunks(conn, query, limit):
    try:
        rows = conn.execute(
            """
            SELECT c.chunk_id, c.doc_id, c.title, c.source_type, c.chunk_type,
                   c.content_chars, c.content_preview, bm25(chunk_fts) AS score
            FROM chunk_fts
            JOIN chunks c ON c.chunk_id = chunk_fts.chunk_id
            WHERE chunk_fts MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
    except sqlite3.OperationalError:
        rows = conn.execute(
            """
            SELECT chunk_id, doc_id, title, source_type, chunk_type,
                   content_chars, content_preview, 0.0 AS score
            FROM chunks
            WHERE lower(title) LIKE ?
               OR lower(source_type) LIKE ?
               OR lower(chunk_type) LIKE ?
               OR lower(content_preview) LIKE ?
            ORDER BY doc_id, chunk_id
            LIMIT ?
            """,
            tuple([f"%{query.lower()}%"] * 4) + (limit,),
        ).fetchall()
    return rows_to_dicts(rows)


def source(conn, source_id):
    row = conn.execute(
        """
        SELECT source_id, title, source_type, domain, authority, organization,
               publish_date, language, path, url, trust_level, review_status,
               processing_status, parsed_status, cleaned_status, chunk_count,
               case_observation_count, payload_json
        FROM sources
        WHERE source_id = ?
        """,
        (source_id,),
    ).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))
    result["entities"] = rows_to_dicts(conn.execute(
        """
        SELECT e.entity_id, e.entity_type, e.name, e.review_status
        FROM entity_sources es
        JOIN entities e ON e.entity_id = es.entity_id
        WHERE es.source_id = ?
        ORDER BY e.entity_type, e.name
        """,
        (source_id,),
    ))
    result["chunks"] = rows_to_dicts(conn.execute(
        """
        SELECT chunk_id, doc_id, title, chunk_type, content_chars, content_preview
        FROM chunks
        WHERE doc_id = ?
        ORDER BY chunk_id
        LIMIT 20
        """,
        (source_id,),
    ))
    return result


def neighbors(conn, entity_id):
    return {
        "entity_id": entity_id,
        "outgoing": rows_to_dicts(conn.execute(
            """
            SELECT relation, dst_id AS peer_id, dst_type AS peer_type, confidence, source_refs_json
            FROM relationships
            WHERE src_id = ?
            ORDER BY relation, dst_id
            """,
            (entity_id,),
        )),
        "incoming": rows_to_dicts(conn.execute(
            """
            SELECT relation, src_id AS peer_id, src_type AS peer_type, confidence, source_refs_json
            FROM relationships
            WHERE dst_id = ?
            ORDER BY relation, src_id
            """,
            (entity_id,),
        )),
    }


def evidence(conn, entity_id):
    return {
        "entity_id": entity_id,
        "records": rows_to_dicts(conn.execute(
            """
            SELECT evidence_id, entity_type, entity_review_status, source_id,
                   source_type, source_status, source_path, parsed_path,
                   cleaned_path, chunk_count, case_observation_count,
                   chunk_sample_ids_json
            FROM entity_evidence
            WHERE entity_id = ?
            ORDER BY source_status, source_type, source_id
            """,
            (entity_id,),
        )),
    }


def review_packets(conn, entity_id, bucket, limit):
    clauses = []
    params = []
    if entity_id:
        clauses.append("entity_id = ?")
        params.append(entity_id)
    if bucket:
        clauses.append("review_bucket = ?")
        params.append(bucket)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return rows_to_dicts(conn.execute(
        f"""
        SELECT packet_id, review_order, entity_id, entity_type, display_name,
               review_status, review_bucket, source_ref_count,
               evidence_record_count, total_chunk_count,
               case_observation_count, suggested_action
        FROM review_packets
        {where}
        ORDER BY review_order, entity_type, display_name
        LIMIT ?
        """,
        params,
    ))


def workbook(conn, entity_id, batch, bucket, limit):
    clauses = []
    params = []
    if entity_id:
        clauses.append("entity_id = ?")
        params.append(entity_id)
    if batch:
        clauses.append("review_batch = ?")
        params.append(batch)
    if bucket:
        clauses.append("review_bucket = ?")
        params.append(bucket)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return rows_to_dicts(conn.execute(
        f"""
        SELECT workbook_id, review_order, review_batch, priority,
               entity_id, entity_type, display_name, review_status,
               review_bucket, review_decision, needs_llm,
               related_packet_id, related_action_id, decision_instructions
        FROM human_review_workbook
        {where}
        ORDER BY review_order, entity_type, display_name
        LIMIT ?
        """,
        params,
    ))


def extracts(conn, entity_id, limit):
    return {
        "entity_id": entity_id,
        "records": rows_to_dicts(conn.execute(
            """
            SELECT extract_id, entity_type, display_name, review_order,
                   review_batch, review_bucket, chunk_rank, chunk_id,
                   chunk_file, doc_id, source_ref, chunk_type,
                   section_path_json, matched_terms_json, match_score,
                   excerpt, excerpt_char_count, needs_llm, llm_skip_reason
            FROM human_review_evidence_extracts
            WHERE entity_id = ?
            ORDER BY chunk_rank, match_score DESC, chunk_id
            LIMIT ?
            """,
            (entity_id, limit),
        )),
    }


def sessions(conn, session_id, status, limit):
    clauses = []
    params = []
    if session_id:
        clauses.append("session_id = ?")
        params.append(session_id)
    if status:
        clauses.append("queue_status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return rows_to_dicts(conn.execute(
        f"""
        SELECT session_item_id, session_id, session_order, within_session_order,
               global_review_order, entity_id, entity_type, display_name,
               review_batch, review_bucket, review_status, review_decision,
               application_status, queue_status, source_refs_json,
               top_extract_ids_json, top_chunk_ids_json, top_match_scores_json,
               decision_input_path, next_step, needs_llm
        FROM human_review_session_queue
        {where}
        ORDER BY session_order, within_session_order, global_review_order
        LIMIT ?
        """,
        params,
    ))


def actions(conn, status, needs_llm, limit):
    clauses = []
    params = []
    if status:
        clauses.append("status = ?")
        params.append(status)
    if needs_llm is not None:
        clauses.append("needs_llm = ?")
        params.append(1 if needs_llm else 0)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return rows_to_dicts(conn.execute(
        f"""
        SELECT action_id, action_order, priority, action_type, status, scope_id,
               entity_id, entity_type, display_name, needs_llm, blocking_reason,
               suggested_action, skip_reason
        FROM next_actions
        {where}
        ORDER BY priority, action_order
        LIMIT ?
        """,
        params,
    ))


def observations(conn, source_id, observation_type, limit):
    clauses = []
    params = []
    if source_id:
        clauses.append("source_id = ?")
        params.append(source_id)
    if observation_type:
        clauses.append("observation_type = ?")
        params.append(observation_type)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return rows_to_dicts(conn.execute(
        f"""
        SELECT observation_id, source_id, title, observation_type, value,
               source_ref, review_status, context
        FROM case_observations
        {where}
        ORDER BY source_id, observation_type, value, observation_id
        LIMIT ?
        """,
        params,
    ))


def glossary(conn, query, limit):
    if query:
        like = f"%{query.lower()}%"
        params = (like, like, like, limit)
        where = "WHERE lower(term) LIKE ? OR lower(entity_id) LIKE ? OR lower(definition) LIKE ?"
    else:
        params = (limit,)
        where = ""
    return rows_to_dicts(conn.execute(
        f"""
        SELECT term_id, entity_id, entity_type, term, category, definition,
               aliases_json, source_refs_json, review_status
        FROM glossary
        {where}
        ORDER BY lower(term), entity_id
        LIMIT ?
        """,
        params,
    ))


def field_checks(conn, session_id, entity_id, limit):
    clauses = []
    params = []
    if session_id:
        clauses.append("session_id = ?")
        params.append(session_id)
    if entity_id:
        clauses.append("entity_id = ?")
        params.append(entity_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return rows_to_dicts(conn.execute(
        f"""
        SELECT field_check_id, session_id, session_order, within_session_order,
               global_review_order, field_order, entity_id, entity_type,
               display_name, field_name, field_value_preview,
               verification_prompt, decision_input_path, review_decision,
               needs_llm
        FROM human_review_field_checklist
        {where}
        ORDER BY session_order, within_session_order, field_order
        LIMIT ?
        """,
        params,
    ))


def decision_audit(conn, entity_id, status, limit):
    clauses = []
    params = []
    if entity_id:
        clauses.append("entity_id = ?")
        params.append(entity_id)
    if status:
        clauses.append("application_status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return rows_to_dicts(conn.execute(
        f"""
        SELECT audit_id, workbook_id, entity_id, entity_type, display_name,
               current_review_status, review_decision, target_review_status,
               application_status, can_apply, blocking_reason, needs_llm,
               decision_source, decision_reviewer, decision_reviewed_at,
               decision_note
        FROM human_review_decision_audit
        {where}
        ORDER BY application_status, entity_type, display_name, entity_id
        LIMIT ?
        """,
        params,
    ))


def input_validation(conn, status, severity, limit):
    clauses = []
    params = []
    if status:
        clauses.append("status = ?")
        params.append(status)
    if severity:
        clauses.append("severity = ?")
        params.append(severity)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return rows_to_dicts(conn.execute(
        f"""
        SELECT validation_id, check_order, input_path, check_type, status,
               severity, checked_count, issue_count,
               affected_entity_ids_json, affected_rows_json, message,
               suggested_action, needs_llm
        FROM human_review_input_validation
        {where}
        ORDER BY check_order
        LIMIT ?
        """,
        params,
    ))


def apply_preview(conn, record_type, run_mode, limit):
    clauses = []
    params = []
    if record_type:
        clauses.append("record_type = ?")
        params.append(record_type)
    if run_mode:
        clauses.append("run_mode = ?")
        params.append(run_mode)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return rows_to_dicts(conn.execute(
        f"""
        SELECT preview_id, record_type, run_mode, entity_id, entity_file,
               from_status, to_status, application_status, can_apply,
               needs_llm, count, message
        FROM human_review_decision_apply_preview
        {where}
        ORDER BY record_type, preview_id
        LIMIT ?
        """,
        params,
    ))


def progress(conn, scope_type, limit):
    clauses = []
    params = []
    if scope_type:
        clauses.append("scope_type = ?")
        params.append(scope_type)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return rows_to_dicts(conn.execute(
        f"""
        SELECT progress_id, scope_type, scope_value, entity_count,
               pending_count, approved_count, rejected_count,
               unreviewed_decision_count, approved_decision_count,
               rejected_decision_count, needs_source_decision_count,
               needs_semantic_review_decision_count, ready_to_apply_count,
               manual_followup_count, blocked_by_llm_count, no_op_count,
               completion_percent, needs_llm_count, next_step
        FROM human_review_progress
        {where}
        ORDER BY scope_type, scope_value
        LIMIT ?
        """,
        params,
    ))


def source_matrix(conn, source_id, limit):
    clauses = []
    params = []
    if source_id:
        clauses.append("source_id = ?")
        params.append(source_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return rows_to_dicts(conn.execute(
        f"""
        SELECT source_matrix_id, source_id, source_title, source_type,
               processing_status, source_chunk_count, evidence_record_count,
               entity_count, field_check_count, session_ids_json,
               entity_types_json, sample_entity_ids_json, cleaned_paths_json,
               parsed_paths_json, chunk_sample_ids_json, decision_input_path
        FROM human_review_source_matrix
        {where}
        ORDER BY entity_count DESC, field_check_count DESC, source_id
        LIMIT ?
        """,
        params,
    ))


def task_board(conn, task_type, limit):
    clauses = []
    params = []
    if task_type:
        clauses.append("task_type = ?")
        params.append(task_type)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return rows_to_dicts(conn.execute(
        f"""
        SELECT task_id, task_order, task_type, task_status, title, session_id,
               source_id, entity_id, item_count, field_check_count,
               primary_input, secondary_input, suggested_command,
               write_command, needs_llm
        FROM human_review_task_board
        {where}
        ORDER BY task_order
        LIMIT ?
        """,
        params,
    ))


def handoff(conn, task_type, limit):
    clauses = []
    params = []
    if task_type:
        clauses.append("task_type = ?")
        params.append(task_type)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    return rows_to_dicts(conn.execute(
        f"""
        SELECT handoff_id, task_id, task_order, task_type, handoff_status,
               title, primary_input, primary_input_exists, secondary_input,
               secondary_input_exists, expected_manual_output,
               dry_run_command, write_command, verification_command,
               can_write, requires_human_decision, needs_llm
        FROM human_review_handoff
        {where}
        ORDER BY task_order
        LIMIT ?
        """,
        params,
    ))


def stats(conn):
    tables = [
        "sources",
        "entities",
        "entity_sources",
        "chunks",
        "chunk_topics",
        "relationships",
        "lexical_terms",
        "lexical_entity_refs",
        "lexical_source_refs",
        "lexical_chunk_refs",
        "entity_evidence",
        "review_packets",
        "next_actions",
        "case_observations",
        "glossary",
        "human_review_workbook",
        "human_review_decision_audit",
        "human_review_decision_apply_preview",
        "human_review_input_validation",
        "human_review_progress",
        "human_review_evidence_extracts",
        "human_review_session_queue",
        "human_review_session_status",
        "human_review_field_checklist",
        "human_review_source_matrix",
        "human_review_task_board",
        "human_review_handoff",
    ]
    result = {table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables}
    result["entity_types"] = {
        row["entity_type"]: row["count"]
        for row in conn.execute("SELECT entity_type, COUNT(*) AS count FROM entities GROUP BY entity_type")
    }
    result["review_statuses"] = {
        row["review_status"]: row["count"]
        for row in conn.execute("SELECT review_status, COUNT(*) AS count FROM entities GROUP BY review_status")
    }
    result["integrity_check"] = conn.execute("PRAGMA integrity_check").fetchone()[0]
    return result


def build_parser():
    parser = argparse.ArgumentParser(description="Query the published BGP knowledge base SQLite database.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("stats", help="Show database table counts and status counts.")

    p = sub.add_parser("entity", help="Show one entity with sources and relationships.")
    p.add_argument("entity_id")

    p = sub.add_parser("term", help="Look up a lexical index term.")
    p.add_argument("term")
    p.add_argument("--limit", type=int, default=10)

    p = sub.add_parser("search-entities", help="Full-text search entity names and payloads.")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=10)

    p = sub.add_parser("search-chunks", help="Full-text search chunk previews.")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=10)

    p = sub.add_parser("source", help="Show one source with linked entities and sample chunks.")
    p.add_argument("source_id")

    p = sub.add_parser("neighbors", help="Show incoming and outgoing relationship neighbors.")
    p.add_argument("entity_id")

    p = sub.add_parser("evidence", help="Show evidence records for one entity.")
    p.add_argument("entity_id")

    p = sub.add_parser("review-packets", help="List deterministic entity review packet summaries.")
    p.add_argument("--entity-id", default="")
    p.add_argument("--bucket", default="")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("workbook", help="List deterministic human-review workbook rows.")
    p.add_argument("--entity-id", default="")
    p.add_argument("--batch", default="")
    p.add_argument("--bucket", default="")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("extracts", help="Show deterministic human-review evidence extracts for one entity.")
    p.add_argument("entity_id")
    p.add_argument("--limit", type=int, default=10)

    p = sub.add_parser("sessions", help="List deterministic human-review session queue items.")
    p.add_argument("--session-id", default="")
    p.add_argument("--status", default="")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("actions", help="List next actions.")
    p.add_argument("--status", default="")
    p.add_argument("--needs-llm", choices=["true", "false"], default=None)
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("observations", help="List deterministic case observations.")
    p.add_argument("--source-id", default="")
    p.add_argument("--type", default="")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("glossary", help="List glossary terms.")
    p.add_argument("query", nargs="?")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("field-checks", help="List deterministic human-review field checklist rows.")
    p.add_argument("--session-id", default="")
    p.add_argument("--entity-id", default="")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("decision-audit", help="List deterministic human-review decision audit rows.")
    p.add_argument("--entity-id", default="")
    p.add_argument("--status", default="")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("input-validation", help="List deterministic human-review input validation checks.")
    p.add_argument("--status", default="")
    p.add_argument("--severity", default="")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("apply-preview", help="List deterministic human-review apply dry-run preview rows.")
    p.add_argument("--record-type", default="")
    p.add_argument("--run-mode", default="")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("progress", help="List deterministic human-review progress rows.")
    p.add_argument("--scope-type", default="")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("source-matrix", help="List deterministic human-review source matrix rows.")
    p.add_argument("--source-id", default="")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("task-board", help="List deterministic human-review task board rows.")
    p.add_argument("--type", default="")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("handoff", help="List deterministic human-review handoff rows.")
    p.add_argument("--type", default="")
    p.add_argument("--limit", type=int, default=20)

    return parser


def main():
    args = build_parser().parse_args()
    with connect() as conn:
        if args.command == "stats":
            payload = stats(conn)
        elif args.command == "entity":
            payload = entity(conn, args.entity_id)
        elif args.command == "term":
            payload = term(conn, args.term, args.limit)
        elif args.command == "search-entities":
            payload = search_entities(conn, args.query, args.limit)
        elif args.command == "search-chunks":
            payload = search_chunks(conn, args.query, args.limit)
        elif args.command == "source":
            payload = source(conn, args.source_id)
        elif args.command == "neighbors":
            payload = neighbors(conn, args.entity_id)
        elif args.command == "evidence":
            payload = evidence(conn, args.entity_id)
        elif args.command == "review-packets":
            payload = review_packets(conn, args.entity_id, args.bucket, args.limit)
        elif args.command == "workbook":
            payload = workbook(conn, args.entity_id, args.batch, args.bucket, args.limit)
        elif args.command == "extracts":
            payload = extracts(conn, args.entity_id, args.limit)
        elif args.command == "sessions":
            payload = sessions(conn, args.session_id, args.status, args.limit)
        elif args.command == "actions":
            needs_llm = None if args.needs_llm is None else args.needs_llm == "true"
            payload = actions(conn, args.status, needs_llm, args.limit)
        elif args.command == "observations":
            payload = observations(conn, args.source_id, args.type, args.limit)
        elif args.command == "glossary":
            payload = glossary(conn, args.query, args.limit)
        elif args.command == "field-checks":
            payload = field_checks(conn, args.session_id, args.entity_id, args.limit)
        elif args.command == "decision-audit":
            payload = decision_audit(conn, args.entity_id, args.status, args.limit)
        elif args.command == "input-validation":
            payload = input_validation(conn, args.status, args.severity, args.limit)
        elif args.command == "apply-preview":
            payload = apply_preview(conn, args.record_type, args.run_mode, args.limit)
        elif args.command == "progress":
            payload = progress(conn, args.scope_type, args.limit)
        elif args.command == "source-matrix":
            payload = source_matrix(conn, args.source_id, args.limit)
        elif args.command == "task-board":
            payload = task_board(conn, args.type, args.limit)
        elif args.command == "handoff":
            payload = handoff(conn, args.type, args.limit)
        else:
            raise SystemExit(f"unknown command: {args.command}")
    print_json(payload)


if __name__ == "__main__":
    main()
