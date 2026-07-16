export type ChatRole = "user" | "assistant" | "system";
export type SyncStatus = "synced" | "syncing" | "unsynced";
export type StreamMode = "streaming" | "buffered";

export type AnswerTiming = {
  retrieval_ms?: number | null;
  rerank_ms?: number | null;
  context_pack_ms?: number | null;
  generation_ms?: number | null;
  persistence_ms?: number | null;
  model_ttft_ms?: number | null;
  time_to_first_answer_ms?: number | null;
  total_ms?: number | null;
};

export type AnswerPart =
  | { type: "text"; text: string }
  | { type: "citation"; citation_ids: string[]; label: string };

export type StageProgress = {
  stage: string;
  status: string;
  message?: string;
  durationMs?: number;
  elapsedMs?: number;
  startedAt?: number;
};

export type ChatMessage = {
  id?: string;
  role: ChatRole;
  content: string;
  createdAt?: string;
  updatedAt?: string;
  answerStatus?: AssistantAnswerStatus;
  evidence?: AnswerEvidence;
  answerParts?: AnswerPart[];
  timings?: AnswerTiming | null;
  streamMode?: StreamMode;
  syncStatus?: SyncStatus;
  requestId?: string;
  stages?: StageProgress[];
  lastSequence?: number;
};

export type AnswerStatus =
  | "answered"
  | "no_evidence"
  | "llm_unavailable"
  | "error"
  | "stopped"
  | "interrupted";
export type AssistantAnswerStatus = AnswerStatus | "pending";

export type Citation = {
  citation_id?: string;
  citationId?: string;
  source_id?: string;
  sourceId?: string;
  source_ref?: string;
  chunk_id?: string;
  chunkId?: string;
  section_id?: string;
  section_heading?: string;
  section?: string;
  title?: string;
  source_type?: string;
  sourceType?: string;
  score?: number;
  ranking?: number;
  content_preview?: string;
  contentPreview?: string;
  context_snapshot?: string;
  release_id?: string;
  [key: string]: unknown;
};

export type GroundedClaim = {
  schema_version: "grounded_claim_v1" | string;
  claim_type: "factual" | "qualification" | string;
  text: string;
  evidence_ids: string[];
  confidence: number;
};

export type GroundedEvidence = {
  schema_version?: "evidence_v1" | string;
  evidence_id: string;
  chunk_id: string;
  source_ref: string;
  content_hash?: string;
  title?: string;
  section_path?: string[];
  content?: string;
  governance?: Record<string, unknown>;
  member_boundary?: Record<string, unknown>;
  retrieval_scores?: Record<string, unknown>;
  [key: string]: unknown;
};

export type ContextPack = {
  query?: string;
  normalized_query?: string;
  results?: Array<Record<string, unknown>>;
  context_units?: Array<Record<string, unknown>>;
  contextUnits?: Array<Record<string, unknown>>;
  evidence?: GroundedEvidence[];
  context_groups?: Array<Record<string, unknown>>;
  citations?: unknown[];
  resolved_query_type?: string;
  token_budget?: number;
  degraded?: boolean;
  degraded_reason?: string;
  [key: string]: unknown;
};

export type RagAnswerPayload = {
  query: string;
  answer: string;
  answer_parts?: AnswerPart[];
  answer_status: AnswerStatus | string;
  inline_citation_status?: string;
  stream_mode?: StreamMode;
  timings?: AnswerTiming;
  conversation_id?: string;
  request_id?: string;
  message_id?: string;
  generated?: boolean;
  model_provider?: string;
  model?: string;
  error_code?: string;
  error?: string;
  claims?: GroundedClaim[];
  evidence?: GroundedEvidence[];
  grounding_status?: string;
  citations: Citation[];
  context_pack: ContextPack;
  guardrails?: Record<string, unknown>;
  usage?: Record<string, unknown>;
};

export type RetrievalSummary = {
  vectorStatus: "complete" | "unavailable" | "unknown";
  resultCount: number;
  method: string;
  methodLabel?: string;
  sourceTypes: string[];
  sourceCount?: number;
  contextUnitCount?: number;
  hasSectionContext?: boolean;
  evidenceLabel?: string;
};

export type AnswerEvidence = {
  citations: Citation[];
  retrieval: RetrievalSummary | null;
  contextPack: ContextPack | null;
};

export type ConversationSummary = {
  conversation_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  sync_status: SyncStatus;
};

export type ConversationDetail = ConversationSummary & {
  messages: Array<{
    message_id: string;
    role: ChatRole;
    content: string;
    answer_status?: AssistantAnswerStatus | null;
    answer_parts?: AnswerPart[];
    timings?: AnswerTiming | null;
    stream_mode?: StreamMode;
    sync_status?: SyncStatus;
    created_at: string;
    updated_at: string;
    citations?: Citation[];
  }>;
};

export type EvidenceSection = {
  section_id: string;
  heading: string;
  chunks: Array<{ chunk_id: string; content: string; is_highlight: boolean }>;
};

export type EvidenceDetail = {
  citation: Citation;
  available: boolean;
  complete_sentence: string;
  highlight_chunk_id?: string;
  source_id?: string;
  snapshot_release_id?: string;
  current_release_id?: string;
  release_mismatch?: boolean;
  sections: EvidenceSection[];
  next_cursor?: number | null;
  scope: "section" | "document";
  cursor: number;
  error?: string;
  error_code?: string;
};

export type ChatApiResponse = {
  message: ChatMessage;
  answerStatus: AnswerStatus;
  citations: Citation[];
  claims: GroundedClaim[];
  evidence: GroundedEvidence[];
  groundingStatus?: string;
  retrieval: RetrievalSummary;
  error?: string;
  raw?: RagAnswerPayload;
};
