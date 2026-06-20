import json
import sqlite3

from . import rag_answer, retrieval_framework


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


def _json(value):
    return json.loads(value) if value else None


def stats(conn):
    tables = [
        "sources",
        "entities",
        "chunks",
        "relationships",
        "lexical_terms",
        "entity_evidence",
        "review_packets",
        "next_actions",
        "case_observations",
        "glossary",
        "human_review_progress",
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
    result["payload"] = _json(result.pop("payload_json"))
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
    result["evidence"] = evidence(conn, entity_id)["records"]
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
    result["payload"] = _json(result.pop("payload_json"))
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
        like = f"%{query.lower()}%"
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
            (like, like, like, like, limit),
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
        like = f"%{query.lower()}%"
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
            (like, like, like, like, limit),
        ).fetchall()
    return rows_to_dicts(rows)


def actions(conn, status="", needs_llm=None, limit=10):
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


def progress(conn, scope_type="", limit=10):
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
               ready_to_apply_count, manual_followup_count,
               blocked_by_llm_count, completion_percent, needs_llm_count, next_step
        FROM human_review_progress
        {where}
        ORDER BY scope_type, scope_value
        LIMIT ?
        """,
        params,
    ))


def retrieval_search(query, limit=10):
    return {
        "query": query,
        "results": retrieval_framework.search(query, limit=limit),
    }


def retrieval_evidence(entity_id):
    return retrieval_framework.evidence(entity_id)


def retrieval_context_pack(query, limit=8):
    return retrieval_framework.context_pack(query, limit=limit)


def rag_answer_payload(query, limit=8):
    return rag_answer.answer_question(query, limit=limit)
