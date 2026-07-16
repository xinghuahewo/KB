export type ChatRole = "user" | "assistant" | "system";

export type ChatMessage = {
  id?: string;
  role: ChatRole;
  content: string;
  createdAt?: string;
  answerStatus?: AssistantAnswerStatus;
  evidence?: AnswerEvidence;
};

export type AnswerStatus = "answered" | "no_evidence" | "llm_unavailable" | "error" | "stopped";
export type AssistantAnswerStatus = AnswerStatus | "pending";

export type Citation = {
  source_id?: string;
  sourceId?: string;
  source_ref?: string;
  chunk_id?: string;
  chunkId?: string;
  title?: string;
  source_type?: string;
  sourceType?: string;
  score?: number;
  ranking?: number;
  content_preview?: string;
  contentPreview?: string;
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
  answer_status: Exclude<AnswerStatus, "error"> | string;
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
