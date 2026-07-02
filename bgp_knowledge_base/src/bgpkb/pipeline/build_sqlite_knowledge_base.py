#!/usr/bin/env python3
import json
import sqlite3
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
PUBLISHED_DIR = paths.PUBLISHED_DIR
REPORT = paths.report_path("sqlite_knowledge_base_report")
DB_PATH = PUBLISHED_DIR / "bgp_knowledge_base.sqlite"
SCHEMA_PATH = PUBLISHED_DIR / "sqlite_schema.sql"


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


SCHEMA = """
CREATE TABLE sources (
  source_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  source_type TEXT NOT NULL,
  domain TEXT NOT NULL,
  authority TEXT NOT NULL,
  organization TEXT NOT NULL,
  publish_date TEXT NOT NULL,
  language TEXT NOT NULL,
  path TEXT NOT NULL,
  url TEXT NOT NULL,
  trust_level TEXT NOT NULL,
  review_status TEXT NOT NULL,
  processing_status TEXT NOT NULL,
  parsed_status TEXT NOT NULL,
  cleaned_status TEXT NOT NULL,
  chunk_count INTEGER NOT NULL,
  case_observation_count INTEGER NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE TABLE entities (
  entity_id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  review_status TEXT NOT NULL,
  source_ref_count INTEGER NOT NULL,
  evidence_record_count INTEGER NOT NULL,
  chunk_count INTEGER NOT NULL,
  case_observation_count INTEGER NOT NULL,
  review_bucket TEXT NOT NULL,
  entity_file TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE TABLE entity_sources (
  entity_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  PRIMARY KEY (entity_id, source_id),
  FOREIGN KEY (entity_id) REFERENCES entities(entity_id),
  FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE chunks (
  chunk_id TEXT PRIMARY KEY,
  doc_id TEXT NOT NULL,
  title TEXT NOT NULL,
  source_type TEXT NOT NULL,
  chunk_type TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  language TEXT NOT NULL,
  review_status TEXT NOT NULL,
  content_chars INTEGER NOT NULL,
  content_preview TEXT NOT NULL,
  chunk_file TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE TABLE chunk_topics (
  chunk_id TEXT NOT NULL,
  topic TEXT NOT NULL,
  PRIMARY KEY (chunk_id, topic),
  FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id)
);

CREATE TABLE relationships (
  relationship_id TEXT PRIMARY KEY,
  src_id TEXT NOT NULL,
  src_type TEXT NOT NULL,
  relation TEXT NOT NULL,
  dst_id TEXT NOT NULL,
  dst_type TEXT NOT NULL,
  confidence REAL,
  source_refs_json TEXT NOT NULL
);

CREATE TABLE lexical_terms (
  term TEXT PRIMARY KEY
);

CREATE TABLE lexical_entity_refs (
  term TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  PRIMARY KEY (term, entity_id),
  FOREIGN KEY (term) REFERENCES lexical_terms(term),
  FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE lexical_source_refs (
  term TEXT NOT NULL,
  source_id TEXT NOT NULL,
  PRIMARY KEY (term, source_id),
  FOREIGN KEY (term) REFERENCES lexical_terms(term),
  FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE lexical_chunk_refs (
  term TEXT NOT NULL,
  chunk_id TEXT NOT NULL,
  PRIMARY KEY (term, chunk_id),
  FOREIGN KEY (term) REFERENCES lexical_terms(term),
  FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id)
);

CREATE TABLE entity_evidence (
  evidence_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_review_status TEXT NOT NULL,
  source_id TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_status TEXT NOT NULL,
  source_path TEXT NOT NULL,
  parsed_path TEXT NOT NULL,
  cleaned_path TEXT NOT NULL,
  chunk_count INTEGER NOT NULL,
  case_observation_count INTEGER NOT NULL,
  chunk_sample_ids_json TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY (entity_id) REFERENCES entities(entity_id),
  FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE review_packets (
  packet_id TEXT PRIMARY KEY,
  review_order INTEGER NOT NULL,
  entity_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  display_name TEXT NOT NULL,
  review_status TEXT NOT NULL,
  review_bucket TEXT NOT NULL,
  source_ref_count INTEGER NOT NULL,
  evidence_record_count INTEGER NOT NULL,
  total_chunk_count INTEGER NOT NULL,
  case_observation_count INTEGER NOT NULL,
  suggested_action TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE next_actions (
  action_id TEXT PRIMARY KEY,
  action_order INTEGER NOT NULL,
  priority INTEGER NOT NULL,
  action_type TEXT NOT NULL,
  status TEXT NOT NULL,
  scope_id TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  display_name TEXT NOT NULL,
  review_bucket TEXT NOT NULL,
  related_dataset TEXT NOT NULL,
  needs_llm INTEGER NOT NULL,
  blocking_reason TEXT NOT NULL,
  suggested_action TEXT NOT NULL,
  skip_reason TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE TABLE case_observations (
  observation_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL,
  title TEXT NOT NULL,
  observation_type TEXT NOT NULL,
  value TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  review_status TEXT NOT NULL,
  context TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE glossary (
  term_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  term TEXT NOT NULL,
  category TEXT NOT NULL,
  definition TEXT NOT NULL,
  aliases_json TEXT NOT NULL,
  source_refs_json TEXT NOT NULL,
  review_status TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE human_review_workbook (
  workbook_id TEXT PRIMARY KEY,
  review_order INTEGER NOT NULL,
  review_batch TEXT NOT NULL,
  priority INTEGER NOT NULL,
  entity_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  display_name TEXT NOT NULL,
  review_status TEXT NOT NULL,
  review_bucket TEXT NOT NULL,
  review_decision TEXT NOT NULL,
  needs_llm INTEGER NOT NULL,
  related_packet_id TEXT NOT NULL,
  related_action_id TEXT NOT NULL,
  decision_instructions TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE human_review_decision_audit (
  audit_id TEXT PRIMARY KEY,
  workbook_id TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  display_name TEXT NOT NULL,
  entity_file TEXT NOT NULL,
  current_review_status TEXT NOT NULL,
  review_decision TEXT NOT NULL,
  target_review_status TEXT NOT NULL,
  application_status TEXT NOT NULL,
  can_apply INTEGER NOT NULL,
  blocking_reason TEXT NOT NULL,
  needs_llm INTEGER NOT NULL,
  decision_source TEXT NOT NULL,
  decision_reviewer TEXT NOT NULL,
  decision_reviewed_at TEXT NOT NULL,
  decision_note TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY (entity_id) REFERENCES entities(entity_id),
  FOREIGN KEY (workbook_id) REFERENCES human_review_workbook(workbook_id)
);

CREATE TABLE human_review_decision_apply_preview (
  preview_id TEXT PRIMARY KEY,
  record_type TEXT NOT NULL,
  run_mode TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  entity_file TEXT NOT NULL,
  from_status TEXT NOT NULL,
  to_status TEXT NOT NULL,
  application_status TEXT NOT NULL,
  can_apply INTEGER NOT NULL,
  needs_llm INTEGER NOT NULL,
  count INTEGER NOT NULL,
  message TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE TABLE human_review_input_validation (
  validation_id TEXT PRIMARY KEY,
  check_order INTEGER NOT NULL,
  input_path TEXT NOT NULL,
  check_type TEXT NOT NULL,
  status TEXT NOT NULL,
  severity TEXT NOT NULL,
  checked_count INTEGER NOT NULL,
  issue_count INTEGER NOT NULL,
  affected_entity_ids_json TEXT NOT NULL,
  affected_rows_json TEXT NOT NULL,
  message TEXT NOT NULL,
  suggested_action TEXT NOT NULL,
  needs_llm INTEGER NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE TABLE human_review_progress (
  progress_id TEXT PRIMARY KEY,
  scope_type TEXT NOT NULL,
  scope_value TEXT NOT NULL,
  entity_count INTEGER NOT NULL,
  pending_count INTEGER NOT NULL,
  approved_count INTEGER NOT NULL,
  rejected_count INTEGER NOT NULL,
  unreviewed_decision_count INTEGER NOT NULL,
  approved_decision_count INTEGER NOT NULL,
  rejected_decision_count INTEGER NOT NULL,
  needs_source_decision_count INTEGER NOT NULL,
  needs_semantic_review_decision_count INTEGER NOT NULL,
  ready_to_apply_count INTEGER NOT NULL,
  manual_followup_count INTEGER NOT NULL,
  blocked_by_llm_count INTEGER NOT NULL,
  no_op_count INTEGER NOT NULL,
  completion_percent REAL NOT NULL,
  needs_llm_count INTEGER NOT NULL,
  next_step TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE TABLE historical_evidence_chunks (
  chunk_id TEXT PRIMARY KEY,
  chunk_file TEXT NOT NULL,
  doc_id TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  chunk_type TEXT NOT NULL,
  corpus_version TEXT NOT NULL
);

CREATE TABLE human_review_evidence_extracts (
  extract_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  display_name TEXT NOT NULL,
  review_order INTEGER NOT NULL,
  review_batch TEXT NOT NULL,
  review_bucket TEXT NOT NULL,
  chunk_rank INTEGER NOT NULL,
  chunk_id TEXT NOT NULL,
  chunk_file TEXT NOT NULL,
  doc_id TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  chunk_type TEXT NOT NULL,
  section_path_json TEXT NOT NULL,
  matched_terms_json TEXT NOT NULL,
  match_score INTEGER NOT NULL,
  excerpt TEXT NOT NULL,
  excerpt_char_count INTEGER NOT NULL,
  needs_llm INTEGER NOT NULL,
  llm_skip_reason TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY (entity_id) REFERENCES entities(entity_id),
  FOREIGN KEY (chunk_id) REFERENCES historical_evidence_chunks(chunk_id)
);

CREATE TABLE human_review_session_queue (
  session_item_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  session_order INTEGER NOT NULL,
  within_session_order INTEGER NOT NULL,
  global_review_order INTEGER NOT NULL,
  entity_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  display_name TEXT NOT NULL,
  review_batch TEXT NOT NULL,
  review_bucket TEXT NOT NULL,
  review_status TEXT NOT NULL,
  review_decision TEXT NOT NULL,
  application_status TEXT NOT NULL,
  queue_status TEXT NOT NULL,
  source_refs_json TEXT NOT NULL,
  cleaned_paths_json TEXT NOT NULL,
  parsed_paths_json TEXT NOT NULL,
  top_extract_ids_json TEXT NOT NULL,
  top_chunk_ids_json TEXT NOT NULL,
  top_match_scores_json TEXT NOT NULL,
  decision_input_path TEXT NOT NULL,
  next_step TEXT NOT NULL,
  needs_llm INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE human_review_session_status (
  session_status_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  session_order INTEGER NOT NULL,
  item_count INTEGER NOT NULL,
  awaiting_human_review_count INTEGER NOT NULL,
  ready_to_apply_count INTEGER NOT NULL,
  manual_followup_count INTEGER NOT NULL,
  blocked_by_llm_count INTEGER NOT NULL,
  unreviewed_decision_count INTEGER NOT NULL,
  approved_decision_count INTEGER NOT NULL,
  rejected_decision_count INTEGER NOT NULL,
  needs_source_decision_count INTEGER NOT NULL,
  needs_semantic_review_decision_count INTEGER NOT NULL,
  completion_percent REAL NOT NULL,
  next_entity_id TEXT NOT NULL,
  next_display_name TEXT NOT NULL,
  decision_input_path TEXT NOT NULL,
  needs_llm_count INTEGER NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE TABLE human_review_field_checklist (
  field_check_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  session_order INTEGER NOT NULL,
  within_session_order INTEGER NOT NULL,
  global_review_order INTEGER NOT NULL,
  field_order INTEGER NOT NULL,
  entity_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  display_name TEXT NOT NULL,
  entity_file TEXT NOT NULL,
  field_name TEXT NOT NULL,
  field_value_preview TEXT NOT NULL,
  verification_prompt TEXT NOT NULL,
  decision_input_path TEXT NOT NULL,
  review_decision TEXT NOT NULL,
  needs_llm INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE human_review_source_matrix (
  source_matrix_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL,
  source_title TEXT NOT NULL,
  source_type TEXT NOT NULL,
  processing_status TEXT NOT NULL,
  source_chunk_count INTEGER NOT NULL,
  evidence_record_count INTEGER NOT NULL,
  entity_count INTEGER NOT NULL,
  field_check_count INTEGER NOT NULL,
  session_ids_json TEXT NOT NULL,
  entity_types_json TEXT NOT NULL,
  sample_entity_ids_json TEXT NOT NULL,
  cleaned_paths_json TEXT NOT NULL,
  parsed_paths_json TEXT NOT NULL,
  chunk_sample_ids_json TEXT NOT NULL,
  decision_input_path TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE human_review_task_board (
  task_id TEXT PRIMARY KEY,
  task_order INTEGER NOT NULL,
  task_type TEXT NOT NULL,
  task_status TEXT NOT NULL,
  title TEXT NOT NULL,
  session_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  item_count INTEGER NOT NULL,
  field_check_count INTEGER NOT NULL,
  primary_input TEXT NOT NULL,
  secondary_input TEXT NOT NULL,
  suggested_command TEXT NOT NULL,
  write_command TEXT NOT NULL,
  needs_llm INTEGER NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE TABLE human_review_handoff (
  handoff_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  task_order INTEGER NOT NULL,
  task_type TEXT NOT NULL,
  handoff_status TEXT NOT NULL,
  title TEXT NOT NULL,
  primary_input TEXT NOT NULL,
  primary_input_exists INTEGER NOT NULL,
  secondary_input TEXT NOT NULL,
  secondary_input_exists INTEGER NOT NULL,
  expected_manual_output TEXT NOT NULL,
  dry_run_command TEXT NOT NULL,
  write_command TEXT NOT NULL,
  verification_command TEXT NOT NULL,
  can_write INTEGER NOT NULL,
  requires_human_decision INTEGER NOT NULL,
  needs_llm INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY (task_id) REFERENCES human_review_task_board(task_id)
);

CREATE TABLE meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_review_status ON entities(review_status);
CREATE INDEX idx_chunks_doc_id ON chunks(doc_id);
CREATE INDEX idx_chunks_source_type ON chunks(source_type);
CREATE INDEX idx_relationships_src ON relationships(src_id, relation);
CREATE INDEX idx_relationships_dst ON relationships(dst_id, relation);
CREATE INDEX idx_entity_sources_source ON entity_sources(source_id);
CREATE INDEX idx_chunk_topics_topic ON chunk_topics(topic);
CREATE INDEX idx_entity_evidence_entity ON entity_evidence(entity_id);
CREATE INDEX idx_entity_evidence_source ON entity_evidence(source_id);
CREATE INDEX idx_review_packets_entity ON review_packets(entity_id);
CREATE INDEX idx_next_actions_status ON next_actions(status, priority);
CREATE INDEX idx_next_actions_entity ON next_actions(entity_id);
CREATE INDEX idx_case_observations_source ON case_observations(source_id);
CREATE INDEX idx_case_observations_type_value ON case_observations(observation_type, value);
CREATE INDEX idx_glossary_entity ON glossary(entity_id);
CREATE INDEX idx_glossary_term ON glossary(term);
CREATE INDEX idx_human_review_workbook_entity ON human_review_workbook(entity_id);
CREATE INDEX idx_human_review_decision_audit_entity ON human_review_decision_audit(entity_id);
CREATE INDEX idx_human_review_decision_audit_status ON human_review_decision_audit(application_status, can_apply);
CREATE INDEX idx_human_review_apply_preview_type ON human_review_decision_apply_preview(record_type, run_mode);
CREATE INDEX idx_human_review_apply_preview_entity ON human_review_decision_apply_preview(entity_id);
CREATE INDEX idx_human_review_input_validation_status ON human_review_input_validation(status, severity);
CREATE INDEX idx_human_review_input_validation_order ON human_review_input_validation(check_order);
CREATE INDEX idx_human_review_progress_scope ON human_review_progress(scope_type, scope_value);
CREATE INDEX idx_human_review_extracts_entity ON human_review_evidence_extracts(entity_id, chunk_rank);
CREATE INDEX idx_human_review_extracts_chunk ON human_review_evidence_extracts(chunk_id);
CREATE INDEX idx_human_review_session_queue_session ON human_review_session_queue(session_id, within_session_order);
CREATE INDEX idx_human_review_session_queue_status ON human_review_session_queue(queue_status, session_order);
CREATE INDEX idx_human_review_session_queue_entity ON human_review_session_queue(entity_id);
CREATE INDEX idx_human_review_session_status_session ON human_review_session_status(session_id);
CREATE INDEX idx_human_review_session_status_order ON human_review_session_status(session_order);
CREATE INDEX idx_human_review_field_checklist_session ON human_review_field_checklist(session_id, within_session_order, field_order);
CREATE INDEX idx_human_review_field_checklist_entity ON human_review_field_checklist(entity_id, field_order);
CREATE INDEX idx_human_review_source_matrix_source ON human_review_source_matrix(source_id);
CREATE INDEX idx_human_review_source_matrix_counts ON human_review_source_matrix(entity_count, field_check_count);
CREATE INDEX idx_human_review_task_board_order ON human_review_task_board(task_order);
CREATE INDEX idx_human_review_task_board_type ON human_review_task_board(task_type, task_status);
CREATE INDEX idx_human_review_handoff_task ON human_review_handoff(task_id);
CREATE INDEX idx_human_review_handoff_type ON human_review_handoff(task_type, handoff_status);
"""


def create_fts_tables(conn):
    try:
        conn.executescript(
            """
            CREATE VIRTUAL TABLE entity_fts USING fts5(
              entity_id UNINDEXED,
              name,
              entity_type,
              category,
              payload_json
            );
            CREATE VIRTUAL TABLE chunk_fts USING fts5(
              chunk_id UNINDEXED,
              title,
              source_type,
              chunk_type,
              content_preview
            );
            """
        )
    except sqlite3.OperationalError:
        return False
    return True


def insert_sources(conn, sources):
    conn.executemany(
        """
        INSERT INTO sources VALUES (
          :source_id, :title, :source_type, :domain, :authority, :organization,
          :publish_date, :language, :path, :url, :trust_level, :review_status,
          :processing_status, :parsed_status, :cleaned_status, :chunk_count,
          :case_observation_count, :payload_json
        )
        """,
        [{**record, "payload_json": dump_json(record)} for record in sources],
    )


def insert_entities(conn, entities, fts_enabled):
    rows = []
    source_rows = []
    fts_rows = []
    for record in entities:
        rows.append({
            "entity_id": record["entity_id"],
            "entity_type": record["entity_type"],
            "name": record["name"],
            "category": record.get("category", ""),
            "review_status": record["review_status"],
            "source_ref_count": record["source_ref_count"],
            "evidence_record_count": record["evidence_record_count"],
            "chunk_count": record["chunk_count"],
            "case_observation_count": record["case_observation_count"],
            "review_bucket": record.get("review_bucket", ""),
            "entity_file": record["entity_file"],
            "payload_json": dump_json(record),
        })
        for source_id in record.get("source_refs", []):
            source_rows.append((record["entity_id"], source_id))
        if fts_enabled:
            fts_rows.append((
                record["entity_id"],
                record["name"],
                record["entity_type"],
                record.get("category", ""),
                dump_json(record.get("entity_payload", {})),
            ))

    conn.executemany(
        """
        INSERT INTO entities VALUES (
          :entity_id, :entity_type, :name, :category, :review_status,
          :source_ref_count, :evidence_record_count, :chunk_count,
          :case_observation_count, :review_bucket, :entity_file, :payload_json
        )
        """,
        rows,
    )
    conn.executemany("INSERT OR IGNORE INTO entity_sources VALUES (?, ?)", source_rows)
    if fts_enabled:
        conn.executemany("INSERT INTO entity_fts VALUES (?, ?, ?, ?, ?)", fts_rows)


def insert_chunks(conn, chunks, fts_enabled):
    rows = []
    topic_rows = []
    fts_rows = []
    for record in chunks:
        rows.append({
            "chunk_id": record["chunk_id"],
            "doc_id": record["doc_id"],
            "title": record["title"],
            "source_type": record["source_type"],
            "chunk_type": record["chunk_type"],
            "source_ref": record["source_ref"],
            "language": record["language"],
            "review_status": record["review_status"],
            "content_chars": record["content_chars"],
            "content_preview": record["content_preview"],
            "chunk_file": record["chunk_file"],
            "payload_json": dump_json(record),
        })
        for topic in record.get("topics", []):
            topic_rows.append((record["chunk_id"], topic))
        if fts_enabled:
            fts_rows.append((
                record["chunk_id"],
                record["title"],
                record["source_type"],
                record["chunk_type"],
                record["content_preview"],
            ))

    conn.executemany(
        """
        INSERT INTO chunks VALUES (
          :chunk_id, :doc_id, :title, :source_type, :chunk_type, :source_ref,
          :language, :review_status, :content_chars, :content_preview,
          :chunk_file, :payload_json
        )
        """,
        rows,
    )
    conn.executemany("INSERT OR IGNORE INTO chunk_topics VALUES (?, ?)", topic_rows)
    if fts_enabled:
        conn.executemany("INSERT INTO chunk_fts VALUES (?, ?, ?, ?, ?)", fts_rows)


def iter_relationship_rows(adjacency):
    seen = set()
    index = 1
    for src_id, node in sorted(adjacency.get("nodes", {}).items()):
        for edge in node.get("outgoing", []):
            key = (
                src_id,
                node.get("entity_type", ""),
                edge.get("relation", ""),
                edge.get("peer_id", ""),
                edge.get("peer_type", ""),
                dump_json(edge.get("source_refs", [])),
                edge.get("confidence"),
            )
            if key in seen:
                continue
            seen.add(key)
            yield {
                "relationship_id": f"rel_{index:05d}",
                "src_id": src_id,
                "src_type": node.get("entity_type", ""),
                "relation": edge.get("relation", ""),
                "dst_id": edge.get("peer_id", ""),
                "dst_type": edge.get("peer_type", ""),
                "confidence": edge.get("confidence"),
                "source_refs_json": dump_json(edge.get("source_refs", [])),
            }
            index += 1


def insert_relationships(conn, adjacency):
    conn.executemany(
        """
        INSERT INTO relationships VALUES (
          :relationship_id, :src_id, :src_type, :relation, :dst_id, :dst_type,
          :confidence, :source_refs_json
        )
        """,
        list(iter_relationship_rows(adjacency)),
    )


def insert_lexical_index(conn, lexical_index):
    terms = []
    entity_refs = []
    source_refs = []
    chunk_refs = []
    for term, refs in sorted(lexical_index.items()):
        terms.append((term,))
        entity_refs.extend((term, entity_id) for entity_id in refs.get("entities", []))
        source_refs.extend((term, source_id) for source_id in refs.get("sources", []))
        chunk_refs.extend((term, chunk_id) for chunk_id in refs.get("chunks", []))

    conn.executemany("INSERT INTO lexical_terms VALUES (?)", terms)
    conn.executemany("INSERT OR IGNORE INTO lexical_entity_refs VALUES (?, ?)", entity_refs)
    conn.executemany("INSERT OR IGNORE INTO lexical_source_refs VALUES (?, ?)", source_refs)
    conn.executemany("INSERT OR IGNORE INTO lexical_chunk_refs VALUES (?, ?)", chunk_refs)


def insert_entity_evidence(conn, records):
    rows = []
    for record in records:
        rows.append({
            "evidence_id": record["evidence_id"],
            "entity_id": record["entity_id"],
            "entity_type": record["entity_type"],
            "entity_review_status": record["entity_review_status"],
            "source_id": record["source_id"],
            "source_type": record["source_type"],
            "source_status": record["source_status"],
            "source_path": record["source_path"],
            "parsed_path": record.get("parsed_path", ""),
            "cleaned_path": record.get("cleaned_path", ""),
            "chunk_count": record.get("chunk_count", 0),
            "case_observation_count": record.get("case_observation_count", 0),
            "chunk_sample_ids_json": dump_json(record.get("chunk_sample_ids", [])),
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO entity_evidence VALUES (
          :evidence_id, :entity_id, :entity_type, :entity_review_status,
          :source_id, :source_type, :source_status, :source_path, :parsed_path,
          :cleaned_path, :chunk_count, :case_observation_count,
          :chunk_sample_ids_json, :payload_json
        )
        """,
        rows,
    )


def insert_review_packets(conn, records):
    rows = []
    for record in records:
        rows.append({
            "packet_id": record["packet_id"],
            "review_order": record["review_order"],
            "entity_id": record["entity_id"],
            "entity_type": record["entity_type"],
            "display_name": record["display_name"],
            "review_status": record["review_status"],
            "review_bucket": record["review_bucket"],
            "source_ref_count": record["source_ref_count"],
            "evidence_record_count": record["evidence_record_count"],
            "total_chunk_count": record["total_chunk_count"],
            "case_observation_count": record["case_observation_count"],
            "suggested_action": record["suggested_action"],
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO review_packets VALUES (
          :packet_id, :review_order, :entity_id, :entity_type, :display_name,
          :review_status, :review_bucket, :source_ref_count,
          :evidence_record_count, :total_chunk_count, :case_observation_count,
          :suggested_action, :payload_json
        )
        """,
        rows,
    )


def insert_next_actions(conn, records):
    rows = []
    for record in records:
        rows.append({
            "action_id": record["action_id"],
            "action_order": record["action_order"],
            "priority": record["priority"],
            "action_type": record["action_type"],
            "status": record["status"],
            "scope_id": record["scope_id"],
            "entity_id": record.get("entity_id", ""),
            "entity_type": record.get("entity_type", ""),
            "display_name": record["display_name"],
            "review_bucket": record["review_bucket"],
            "related_dataset": record["related_dataset"],
            "needs_llm": 1 if record.get("needs_llm") else 0,
            "blocking_reason": record["blocking_reason"],
            "suggested_action": record["suggested_action"],
            "skip_reason": record.get("skip_reason", ""),
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO next_actions VALUES (
          :action_id, :action_order, :priority, :action_type, :status,
          :scope_id, :entity_id, :entity_type, :display_name, :review_bucket,
          :related_dataset, :needs_llm, :blocking_reason, :suggested_action,
          :skip_reason, :payload_json
        )
        """,
        rows,
    )


def insert_case_observations(conn, records):
    rows = []
    for index, record in enumerate(records, start=1):
        rows.append({
            "observation_id": f"case_observation_{index:05d}",
            "source_id": record["source_id"],
            "title": record["title"],
            "observation_type": record["observation_type"],
            "value": record["value"],
            "source_ref": record["source_ref"],
            "review_status": record["review_status"],
            "context": record.get("context", ""),
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO case_observations VALUES (
          :observation_id, :source_id, :title, :observation_type, :value,
          :source_ref, :review_status, :context, :payload_json
        )
        """,
        rows,
    )


def insert_glossary(conn, records):
    rows = []
    for record in records:
        rows.append({
            "term_id": record["term_id"],
            "entity_id": record["entity_id"],
            "entity_type": record["entity_type"],
            "term": record["term"],
            "category": record.get("category", ""),
            "definition": record["definition"],
            "aliases_json": dump_json(record.get("aliases", [])),
            "source_refs_json": dump_json(record.get("source_refs", [])),
            "review_status": record["review_status"],
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO glossary VALUES (
          :term_id, :entity_id, :entity_type, :term, :category, :definition,
          :aliases_json, :source_refs_json, :review_status, :payload_json
        )
        """,
        rows,
    )


def insert_human_review_workbook(conn, records):
    rows = []
    for record in records:
        rows.append({
            "workbook_id": record["workbook_id"],
            "review_order": record["review_order"],
            "review_batch": record["review_batch"],
            "priority": record["priority"],
            "entity_id": record["entity_id"],
            "entity_type": record["entity_type"],
            "display_name": record["display_name"],
            "review_status": record["review_status"],
            "review_bucket": record["review_bucket"],
            "review_decision": record["review_decision"],
            "needs_llm": 1 if record.get("needs_llm") else 0,
            "related_packet_id": record["related_packet_id"],
            "related_action_id": record["related_action_id"],
            "decision_instructions": record["decision_instructions"],
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO human_review_workbook VALUES (
          :workbook_id, :review_order, :review_batch, :priority, :entity_id,
          :entity_type, :display_name, :review_status, :review_bucket,
          :review_decision, :needs_llm, :related_packet_id, :related_action_id,
          :decision_instructions, :payload_json
        )
        """,
        rows,
    )


def insert_human_review_decision_audit(conn, records):
    rows = []
    for record in records:
        rows.append({
            "audit_id": record["audit_id"],
            "workbook_id": record["workbook_id"],
            "entity_id": record["entity_id"],
            "entity_type": record["entity_type"],
            "display_name": record["display_name"],
            "entity_file": record["entity_file"],
            "current_review_status": record["current_review_status"],
            "review_decision": record["review_decision"],
            "target_review_status": record["target_review_status"],
            "application_status": record["application_status"],
            "can_apply": 1 if record.get("can_apply") else 0,
            "blocking_reason": record["blocking_reason"],
            "needs_llm": 1 if record.get("needs_llm") else 0,
            "decision_source": record["decision_source"],
            "decision_reviewer": record.get("decision_reviewer", ""),
            "decision_reviewed_at": record.get("decision_reviewed_at", ""),
            "decision_note": record.get("decision_note", ""),
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO human_review_decision_audit VALUES (
          :audit_id, :workbook_id, :entity_id, :entity_type, :display_name,
          :entity_file, :current_review_status, :review_decision,
          :target_review_status, :application_status, :can_apply,
          :blocking_reason, :needs_llm, :decision_source, :decision_reviewer,
          :decision_reviewed_at, :decision_note, :payload_json
        )
        """,
        rows,
    )


def insert_human_review_decision_apply_preview(conn, records):
    rows = []
    for record in records:
        rows.append({
            "preview_id": record["preview_id"],
            "record_type": record["record_type"],
            "run_mode": record["run_mode"],
            "entity_id": record.get("entity_id", ""),
            "entity_file": record.get("entity_file", ""),
            "from_status": record.get("from_status", ""),
            "to_status": record.get("to_status", ""),
            "application_status": record["application_status"],
            "can_apply": 1 if record.get("can_apply") else 0,
            "needs_llm": 1 if record.get("needs_llm") else 0,
            "count": record["count"],
            "message": record["message"],
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO human_review_decision_apply_preview VALUES (
          :preview_id, :record_type, :run_mode, :entity_id, :entity_file,
          :from_status, :to_status, :application_status, :can_apply,
          :needs_llm, :count, :message, :payload_json
        )
        """,
        rows,
    )


def insert_human_review_input_validation(conn, records):
    rows = []
    for record in records:
        rows.append({
            "validation_id": record["validation_id"],
            "check_order": record["check_order"],
            "input_path": record["input_path"],
            "check_type": record["check_type"],
            "status": record["status"],
            "severity": record["severity"],
            "checked_count": record["checked_count"],
            "issue_count": record["issue_count"],
            "affected_entity_ids_json": dump_json(record.get("affected_entity_ids", [])),
            "affected_rows_json": dump_json(record.get("affected_rows", [])),
            "message": record["message"],
            "suggested_action": record["suggested_action"],
            "needs_llm": 1 if record.get("needs_llm") else 0,
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO human_review_input_validation VALUES (
          :validation_id, :check_order, :input_path, :check_type, :status,
          :severity, :checked_count, :issue_count,
          :affected_entity_ids_json, :affected_rows_json, :message,
          :suggested_action, :needs_llm, :payload_json
        )
        """,
        rows,
    )


def insert_human_review_progress(conn, records):
    rows = []
    for record in records:
        rows.append({
            "progress_id": record["progress_id"],
            "scope_type": record["scope_type"],
            "scope_value": record["scope_value"],
            "entity_count": record["entity_count"],
            "pending_count": record["pending_count"],
            "approved_count": record["approved_count"],
            "rejected_count": record["rejected_count"],
            "unreviewed_decision_count": record["unreviewed_decision_count"],
            "approved_decision_count": record["approved_decision_count"],
            "rejected_decision_count": record["rejected_decision_count"],
            "needs_source_decision_count": record["needs_source_decision_count"],
            "needs_semantic_review_decision_count": record["needs_semantic_review_decision_count"],
            "ready_to_apply_count": record["ready_to_apply_count"],
            "manual_followup_count": record["manual_followup_count"],
            "blocked_by_llm_count": record["blocked_by_llm_count"],
            "no_op_count": record["no_op_count"],
            "completion_percent": record["completion_percent"],
            "needs_llm_count": record["needs_llm_count"],
            "next_step": record["next_step"],
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO human_review_progress VALUES (
          :progress_id, :scope_type, :scope_value, :entity_count,
          :pending_count, :approved_count, :rejected_count,
          :unreviewed_decision_count, :approved_decision_count,
          :rejected_decision_count, :needs_source_decision_count,
          :needs_semantic_review_decision_count, :ready_to_apply_count,
          :manual_followup_count, :blocked_by_llm_count, :no_op_count,
          :completion_percent, :needs_llm_count, :next_step, :payload_json
        )
        """,
        rows,
    )


def build_historical_evidence_chunks(records, *, corpus_version):
    chunks = {}
    for record in records:
        chunk_id = record.get("chunk_id")
        if not chunk_id:
            continue
        chunks[chunk_id] = {
            "chunk_id": chunk_id,
            "chunk_file": record.get("chunk_file", ""),
            "doc_id": record.get("doc_id", ""),
            "source_ref": record.get("source_ref", ""),
            "chunk_type": record.get("chunk_type", ""),
            "corpus_version": corpus_version,
        }
    return [chunks[chunk_id] for chunk_id in sorted(chunks)]


def insert_historical_evidence_chunks(conn, records):
    conn.executemany(
        """
        INSERT INTO historical_evidence_chunks VALUES (
          :chunk_id, :chunk_file, :doc_id, :source_ref, :chunk_type,
          :corpus_version
        )
        """,
        records,
    )


def insert_human_review_evidence_extracts(conn, records):
    rows = []
    for record in records:
        rows.append({
            "extract_id": record["extract_id"],
            "entity_id": record["entity_id"],
            "entity_type": record["entity_type"],
            "display_name": record["display_name"],
            "review_order": record["review_order"],
            "review_batch": record["review_batch"],
            "review_bucket": record["review_bucket"],
            "chunk_rank": record["chunk_rank"],
            "chunk_id": record["chunk_id"],
            "chunk_file": record["chunk_file"],
            "doc_id": record["doc_id"],
            "source_ref": record["source_ref"],
            "chunk_type": record["chunk_type"],
            "section_path_json": dump_json(record.get("section_path", [])),
            "matched_terms_json": dump_json(record.get("matched_terms", [])),
            "match_score": record["match_score"],
            "excerpt": record["excerpt"],
            "excerpt_char_count": record["excerpt_char_count"],
            "needs_llm": 1 if record.get("needs_llm") else 0,
            "llm_skip_reason": record["llm_skip_reason"],
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO human_review_evidence_extracts VALUES (
          :extract_id, :entity_id, :entity_type, :display_name,
          :review_order, :review_batch, :review_bucket, :chunk_rank,
          :chunk_id, :chunk_file, :doc_id, :source_ref, :chunk_type,
          :section_path_json, :matched_terms_json, :match_score, :excerpt,
          :excerpt_char_count, :needs_llm, :llm_skip_reason, :payload_json
        )
        """,
        rows,
    )


def insert_human_review_session_queue(conn, records):
    rows = []
    for record in records:
        rows.append({
            "session_item_id": record["session_item_id"],
            "session_id": record["session_id"],
            "session_order": record["session_order"],
            "within_session_order": record["within_session_order"],
            "global_review_order": record["global_review_order"],
            "entity_id": record["entity_id"],
            "entity_type": record["entity_type"],
            "display_name": record["display_name"],
            "review_batch": record["review_batch"],
            "review_bucket": record["review_bucket"],
            "review_status": record["review_status"],
            "review_decision": record["review_decision"],
            "application_status": record["application_status"],
            "queue_status": record["queue_status"],
            "source_refs_json": dump_json(record.get("source_refs", [])),
            "cleaned_paths_json": dump_json(record.get("cleaned_paths", [])),
            "parsed_paths_json": dump_json(record.get("parsed_paths", [])),
            "top_extract_ids_json": dump_json(record.get("top_extract_ids", [])),
            "top_chunk_ids_json": dump_json(record.get("top_chunk_ids", [])),
            "top_match_scores_json": dump_json(record.get("top_match_scores", [])),
            "decision_input_path": record["decision_input_path"],
            "next_step": record["next_step"],
            "needs_llm": 1 if record.get("needs_llm") else 0,
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO human_review_session_queue VALUES (
          :session_item_id, :session_id, :session_order, :within_session_order,
          :global_review_order, :entity_id, :entity_type, :display_name,
          :review_batch, :review_bucket, :review_status, :review_decision,
          :application_status, :queue_status, :source_refs_json,
          :cleaned_paths_json, :parsed_paths_json, :top_extract_ids_json,
          :top_chunk_ids_json, :top_match_scores_json, :decision_input_path,
          :next_step, :needs_llm, :payload_json
        )
        """,
        rows,
    )


def insert_human_review_session_status(conn, records):
    rows = []
    for record in records:
        rows.append({
            "session_status_id": record["session_status_id"],
            "session_id": record["session_id"],
            "session_order": record["session_order"],
            "item_count": record["item_count"],
            "awaiting_human_review_count": record["awaiting_human_review_count"],
            "ready_to_apply_count": record["ready_to_apply_count"],
            "manual_followup_count": record["manual_followup_count"],
            "blocked_by_llm_count": record["blocked_by_llm_count"],
            "unreviewed_decision_count": record["unreviewed_decision_count"],
            "approved_decision_count": record["approved_decision_count"],
            "rejected_decision_count": record["rejected_decision_count"],
            "needs_source_decision_count": record["needs_source_decision_count"],
            "needs_semantic_review_decision_count": record["needs_semantic_review_decision_count"],
            "completion_percent": record["completion_percent"],
            "next_entity_id": record["next_entity_id"],
            "next_display_name": record["next_display_name"],
            "decision_input_path": record["decision_input_path"],
            "needs_llm_count": record["needs_llm_count"],
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO human_review_session_status VALUES (
          :session_status_id, :session_id, :session_order, :item_count,
          :awaiting_human_review_count, :ready_to_apply_count,
          :manual_followup_count, :blocked_by_llm_count,
          :unreviewed_decision_count, :approved_decision_count,
          :rejected_decision_count, :needs_source_decision_count,
          :needs_semantic_review_decision_count, :completion_percent,
          :next_entity_id, :next_display_name, :decision_input_path,
          :needs_llm_count, :payload_json
        )
        """,
        rows,
    )


def insert_human_review_field_checklist(conn, records):
    rows = []
    for record in records:
        rows.append({
            "field_check_id": record["field_check_id"],
            "session_id": record["session_id"],
            "session_order": record["session_order"],
            "within_session_order": record["within_session_order"],
            "global_review_order": record["global_review_order"],
            "field_order": record["field_order"],
            "entity_id": record["entity_id"],
            "entity_type": record["entity_type"],
            "display_name": record["display_name"],
            "entity_file": record["entity_file"],
            "field_name": record["field_name"],
            "field_value_preview": record["field_value_preview"],
            "verification_prompt": record["verification_prompt"],
            "decision_input_path": record["decision_input_path"],
            "review_decision": record["review_decision"],
            "needs_llm": 1 if record.get("needs_llm") else 0,
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO human_review_field_checklist VALUES (
          :field_check_id, :session_id, :session_order,
          :within_session_order, :global_review_order, :field_order,
          :entity_id, :entity_type, :display_name, :entity_file,
          :field_name, :field_value_preview, :verification_prompt,
          :decision_input_path, :review_decision, :needs_llm, :payload_json
        )
        """,
        rows,
    )


def insert_human_review_source_matrix(conn, records):
    rows = []
    for record in records:
        rows.append({
            "source_matrix_id": record["source_matrix_id"],
            "source_id": record["source_id"],
            "source_title": record["source_title"],
            "source_type": record["source_type"],
            "processing_status": record["processing_status"],
            "source_chunk_count": record["source_chunk_count"],
            "evidence_record_count": record["evidence_record_count"],
            "entity_count": record["entity_count"],
            "field_check_count": record["field_check_count"],
            "session_ids_json": dump_json(record.get("session_ids", [])),
            "entity_types_json": dump_json(record.get("entity_types", [])),
            "sample_entity_ids_json": dump_json(record.get("sample_entity_ids", [])),
            "cleaned_paths_json": dump_json(record.get("cleaned_paths", [])),
            "parsed_paths_json": dump_json(record.get("parsed_paths", [])),
            "chunk_sample_ids_json": dump_json(record.get("chunk_sample_ids", [])),
            "decision_input_path": record["decision_input_path"],
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO human_review_source_matrix VALUES (
          :source_matrix_id, :source_id, :source_title, :source_type,
          :processing_status, :source_chunk_count, :evidence_record_count,
          :entity_count, :field_check_count, :session_ids_json,
          :entity_types_json, :sample_entity_ids_json, :cleaned_paths_json,
          :parsed_paths_json, :chunk_sample_ids_json, :decision_input_path,
          :payload_json
        )
        """,
        rows,
    )


def insert_human_review_task_board(conn, records):
    rows = []
    for record in records:
        rows.append({
            "task_id": record["task_id"],
            "task_order": record["task_order"],
            "task_type": record["task_type"],
            "task_status": record["task_status"],
            "title": record["title"],
            "session_id": record.get("session_id", ""),
            "source_id": record.get("source_id", ""),
            "entity_id": record.get("entity_id", ""),
            "item_count": record["item_count"],
            "field_check_count": record["field_check_count"],
            "primary_input": record["primary_input"],
            "secondary_input": record.get("secondary_input", ""),
            "suggested_command": record["suggested_command"],
            "write_command": record.get("write_command", ""),
            "needs_llm": 1 if record.get("needs_llm") else 0,
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO human_review_task_board VALUES (
          :task_id, :task_order, :task_type, :task_status, :title,
          :session_id, :source_id, :entity_id, :item_count,
          :field_check_count, :primary_input, :secondary_input,
          :suggested_command, :write_command, :needs_llm, :payload_json
        )
        """,
        rows,
    )


def insert_human_review_handoff(conn, records):
    rows = []
    for record in records:
        rows.append({
            "handoff_id": record["handoff_id"],
            "task_id": record["task_id"],
            "task_order": record["task_order"],
            "task_type": record["task_type"],
            "handoff_status": record["handoff_status"],
            "title": record["title"],
            "primary_input": record["primary_input"],
            "primary_input_exists": 1 if record.get("primary_input_exists") else 0,
            "secondary_input": record.get("secondary_input", ""),
            "secondary_input_exists": 1 if record.get("secondary_input_exists") else 0,
            "expected_manual_output": record["expected_manual_output"],
            "dry_run_command": record.get("dry_run_command", ""),
            "write_command": record.get("write_command", ""),
            "verification_command": record["verification_command"],
            "can_write": 1 if record.get("can_write") else 0,
            "requires_human_decision": 1 if record.get("requires_human_decision") else 0,
            "needs_llm": 1 if record.get("needs_llm") else 0,
            "payload_json": dump_json(record),
        })
    conn.executemany(
        """
        INSERT INTO human_review_handoff VALUES (
          :handoff_id, :task_id, :task_order, :task_type, :handoff_status,
          :title, :primary_input, :primary_input_exists, :secondary_input,
          :secondary_input_exists, :expected_manual_output, :dry_run_command,
          :write_command, :verification_command, :can_write,
          :requires_human_decision, :needs_llm, :payload_json
        )
        """,
        rows,
    )


def insert_meta(conn, manifest, fts_enabled):
    rows = [
        ("generated_by", "src/bgpkb/pipeline/build_sqlite_knowledge_base.py"),
        ("source_manifest_generated_at", manifest.get("generated_at", "")),
        ("published_counts", dump_json(manifest.get("counts", {}))),
        ("boundary", dump_json(manifest.get("boundary", {}))),
        ("fts5_enabled", "true" if fts_enabled else "false"),
    ]
    conn.executemany("INSERT INTO meta VALUES (?, ?)", rows)


def table_count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def build_database():
    sources = load_jsonl(PUBLISHED_DIR / "source_catalog.jsonl")
    entities = load_jsonl(PUBLISHED_DIR / "entity_catalog.jsonl")
    chunks = load_jsonl(PUBLISHED_DIR / "chunk_catalog.jsonl")
    adjacency = load_json(PUBLISHED_DIR / "relationship_adjacency.json")
    lexical_index = load_json(PUBLISHED_DIR / "lexical_index.json")
    manifest = load_json(PUBLISHED_DIR / "manifest.json")
    entity_evidence = load_jsonl(paths.DATASETS_DIR / "entity_source_evidence.jsonl")
    review_packets = load_jsonl(paths.DATASETS_DIR / "entity_review_packets.jsonl")
    next_actions = load_jsonl(paths.DATASETS_DIR / "next_action_queue.jsonl")
    case_observations = load_jsonl(paths.DATASETS_DIR / "case_observations.jsonl")
    glossary = load_jsonl(paths.DATASETS_DIR / "glossary.jsonl")
    human_review_workbook = load_jsonl(paths.DATASETS_DIR / "human_review_workbook.jsonl")
    human_review_decision_audit = load_jsonl(paths.DATASETS_DIR / "human_review_decision_audit.jsonl")
    human_review_decision_apply_preview = load_jsonl(paths.DATASETS_DIR / "human_review_decision_apply_preview.jsonl")
    human_review_input_validation = load_jsonl(paths.DATASETS_DIR / "human_review_input_validation.jsonl")
    human_review_progress = load_jsonl(paths.DATASETS_DIR / "human_review_progress.jsonl")
    human_review_evidence_extracts = load_jsonl(paths.DATASETS_DIR / "human_review_evidence_extracts.jsonl")
    historical_evidence_chunks = build_historical_evidence_chunks(
        human_review_evidence_extracts,
        corpus_version=manifest.get("historical_review_evidence_corpus_version", "v1"),
    )
    human_review_session_queue = load_jsonl(paths.DATASETS_DIR / "human_review_session_queue.jsonl")
    human_review_session_status = load_jsonl(paths.DATASETS_DIR / "human_review_session_status.jsonl")
    human_review_field_checklist = load_jsonl(paths.DATASETS_DIR / "human_review_field_checklist.jsonl")
    human_review_source_matrix = load_jsonl(paths.DATASETS_DIR / "human_review_source_matrix.jsonl")
    human_review_task_board = load_jsonl(paths.DATASETS_DIR / "human_review_task_board.jsonl")
    human_review_handoff = load_jsonl(paths.DATASETS_DIR / "human_review_handoff.jsonl")

    if DB_PATH.exists():
        DB_PATH.unlink()
    if DB_PATH.with_suffix(".sqlite-shm").exists():
        DB_PATH.with_suffix(".sqlite-shm").unlink()
    if DB_PATH.with_suffix(".sqlite-wal").exists():
        DB_PATH.with_suffix(".sqlite-wal").unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)
        fts_enabled = create_fts_tables(conn)
        insert_sources(conn, sources)
        insert_entities(conn, entities, fts_enabled)
        insert_chunks(conn, chunks, fts_enabled)
        insert_relationships(conn, adjacency)
        insert_lexical_index(conn, lexical_index)
        insert_entity_evidence(conn, entity_evidence)
        insert_review_packets(conn, review_packets)
        insert_next_actions(conn, next_actions)
        insert_case_observations(conn, case_observations)
        insert_glossary(conn, glossary)
        insert_human_review_workbook(conn, human_review_workbook)
        insert_human_review_decision_audit(conn, human_review_decision_audit)
        insert_human_review_decision_apply_preview(conn, human_review_decision_apply_preview)
        insert_human_review_input_validation(conn, human_review_input_validation)
        insert_human_review_progress(conn, human_review_progress)
        insert_historical_evidence_chunks(conn, historical_evidence_chunks)
        insert_human_review_evidence_extracts(conn, human_review_evidence_extracts)
        insert_human_review_session_queue(conn, human_review_session_queue)
        insert_human_review_session_status(conn, human_review_session_status)
        insert_human_review_field_checklist(conn, human_review_field_checklist)
        insert_human_review_source_matrix(conn, human_review_source_matrix)
        insert_human_review_task_board(conn, human_review_task_board)
        insert_human_review_handoff(conn, human_review_handoff)
        insert_meta(conn, manifest, fts_enabled)
        conn.commit()
    finally:
        conn.close()

    schema_sql = SCHEMA.strip() + "\n"
    if fts_enabled:
        schema_sql += "\n-- FTS5 tables are enabled in this SQLite build.\n"
    else:
        schema_sql += "\n-- FTS5 tables are not enabled in this SQLite build.\n"
    SCHEMA_PATH.write_text(schema_sql, encoding="utf-8")

    conn = sqlite3.connect(DB_PATH)
    try:
        counts = {
            "sources": table_count(conn, "sources"),
            "entities": table_count(conn, "entities"),
            "entity_sources": table_count(conn, "entity_sources"),
            "chunks": table_count(conn, "chunks"),
            "chunk_topics": table_count(conn, "chunk_topics"),
            "relationships": table_count(conn, "relationships"),
            "lexical_terms": table_count(conn, "lexical_terms"),
            "lexical_entity_refs": table_count(conn, "lexical_entity_refs"),
            "lexical_source_refs": table_count(conn, "lexical_source_refs"),
            "lexical_chunk_refs": table_count(conn, "lexical_chunk_refs"),
            "entity_evidence": table_count(conn, "entity_evidence"),
            "review_packets": table_count(conn, "review_packets"),
            "next_actions": table_count(conn, "next_actions"),
            "case_observations": table_count(conn, "case_observations"),
            "glossary": table_count(conn, "glossary"),
            "human_review_workbook": table_count(conn, "human_review_workbook"),
            "human_review_decision_audit": table_count(conn, "human_review_decision_audit"),
            "human_review_decision_apply_preview": table_count(conn, "human_review_decision_apply_preview"),
            "human_review_input_validation": table_count(conn, "human_review_input_validation"),
            "human_review_progress": table_count(conn, "human_review_progress"),
            "human_review_evidence_extracts": table_count(conn, "human_review_evidence_extracts"),
            "historical_evidence_chunks": table_count(conn, "historical_evidence_chunks"),
            "human_review_session_queue": table_count(conn, "human_review_session_queue"),
            "human_review_session_status": table_count(conn, "human_review_session_status"),
            "human_review_field_checklist": table_count(conn, "human_review_field_checklist"),
            "human_review_source_matrix": table_count(conn, "human_review_source_matrix"),
            "human_review_task_board": table_count(conn, "human_review_task_board"),
            "human_review_handoff": table_count(conn, "human_review_handoff"),
        }
        if fts_enabled:
            counts["entity_fts"] = table_count(conn, "entity_fts")
            counts["chunk_fts"] = table_count(conn, "chunk_fts")
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        conn.close()

    return counts, integrity, fts_enabled


def write_report(counts, integrity, fts_enabled):
    lines = [
        "# SQLite 知识库报告",
        "",
        "## 范围",
        "",
        "`data/published/bgp_knowledge_base.sqlite` 从 `data/published/` 文件化入口确定性构建，用于本地 SQL 查询和程序化接入。",
        "",
        "该步骤不联网、不下载、不调用 LLM、不做语义抽取，也不改变实体审批状态。",
        "",
        "## 输出",
        "",
        "- `data/published/bgp_knowledge_base.sqlite`",
        "- `data/published/sqlite_schema.sql`",
        "",
        "## 校验",
        "",
        f"- PRAGMA integrity_check：{integrity}",
        f"- FTS5：{'enabled' if fts_enabled else 'not enabled'}",
        "",
        "## 表计数",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- {key}：{value}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    counts, integrity, fts_enabled = build_database()
    write_report(counts, integrity, fts_enabled)
    print(f"Wrote {DB_PATH.relative_to(ROOT)}")
    print(f"Wrote {SCHEMA_PATH.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    if integrity != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
