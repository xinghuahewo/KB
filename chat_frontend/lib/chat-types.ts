export type ChatRole = "user" | "assistant" | "system";

export type ChatMessage = {
  id?: string;
  role: ChatRole;
  content: string;
  createdAt?: string;
};

export type AnswerStatus = "answered" | "no_evidence" | "llm_unavailable" | "error";

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

export type ContextPack = {
  query?: string;
  normalized_query?: string;
  results?: Array<Record<string, unknown>>;
  citations?: unknown[];
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
  citations: Citation[];
  context_pack: ContextPack;
  guardrails?: Record<string, unknown>;
  usage?: Record<string, unknown>;
};

export type RetrievalSummary = {
  vectorStatus: "complete" | "unavailable" | "unknown";
  resultCount: number;
  method: string;
  sourceTypes: string[];
};

export type ChatApiResponse = {
  message: ChatMessage;
  answerStatus: AnswerStatus;
  citations: Citation[];
  retrieval: RetrievalSummary;
  error?: string;
  raw?: RagAnswerPayload;
};
