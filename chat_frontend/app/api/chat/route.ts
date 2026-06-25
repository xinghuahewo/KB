import { getDefaultBgpRagClient } from "@/lib/bgp-rag-client";
import type { AnswerStatus, ChatApiResponse, ChatMessage, Citation, RagAnswerPayload } from "@/lib/chat-types";

type ChatRequestBody = {
  messages?: ChatMessage[];
  options?: {
    limit?: number;
    showCitations?: boolean;
  };
};

export async function POST(request: Request) {
  let body: ChatRequestBody;

  try {
    body = (await request.json()) as ChatRequestBody;
  } catch {
    return json(errorResponse("请求体不是有效 JSON。"), 400);
  }

  const question = latestUserQuestion(body.messages || []);
  if (!question) {
    return json(errorResponse("请先输入一个问题。"), 400);
  }

  const limit = clampLimit(body.options?.limit);

  try {
    const ragPayload = await getDefaultBgpRagClient().answerQuestion(question, limit);
    return json(toChatResponse(ragPayload), 200);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return json(errorResponse("RAG 服务暂时不可用，请确认 FastAPI 服务已经启动后重试。", message), 502);
  }
}

function latestUserQuestion(messages: ChatMessage[]) {
  return [...messages]
    .reverse()
    .find((message) => message.role === "user" && message.content.trim())
    ?.content.trim();
}

function clampLimit(limit: unknown) {
  if (typeof limit !== "number" || Number.isNaN(limit)) {
    return 8;
  }
  return Math.min(20, Math.max(1, Math.trunc(limit)));
}

function toChatResponse(payload: RagAnswerPayload): ChatApiResponse {
  const answerStatus = normalizeAnswerStatus(payload.answer_status);
  const content = assistantContent(payload, answerStatus);

  return {
    message: {
      role: "assistant",
      content,
      createdAt: new Date().toISOString(),
    },
    answerStatus,
    citations: payload.citations || [],
    retrieval: summarizeRetrieval(payload),
    error: payload.error,
    raw: payload,
  };
}

function assistantContent(payload: RagAnswerPayload, status: AnswerStatus) {
  if (status === "answered" && payload.answer.trim()) {
    return payload.answer;
  }

  if (status === "no_evidence") {
    return "没有找到足够证据回答这个问题。请尝试换一种问法，或提供更具体的 BGP 术语、事件名称、RFC 或案例线索。";
  }

  if (status === "llm_unavailable") {
    return "模型暂时不可用，因此没有生成最终答案。已保留本次检索到的证据，可先查看右侧引用和 context pack。";
  }

  return "RAG 服务暂时不可用，请确认 FastAPI 服务已经启动后重试。";
}

function normalizeAnswerStatus(status: string): AnswerStatus {
  if (status === "answered" || status === "no_evidence" || status === "llm_unavailable") {
    return status;
  }
  return "error";
}

function summarizeRetrieval(payload: RagAnswerPayload) {
  const results = payload.context_pack?.results || [];
  const method = firstString(results, "retrieval_method") || "unknown";
  const sourceTypes = uniqueStrings([
    ...payload.citations.map((citation) => citation.source_type || citation.sourceType),
    ...results.map((result) => result.source_type),
  ]);

  return {
    vectorStatus: results.length > 0 ? ("complete" as const) : ("unknown" as const),
    resultCount: results.length,
    method,
    sourceTypes,
  };
}

function firstString(records: Array<Record<string, unknown>>, key: string) {
  for (const record of records) {
    const value = record[key];
    if (typeof value === "string" && value) {
      return value;
    }
  }
  return "";
}

function uniqueStrings(values: unknown[]) {
  return Array.from(new Set(values.filter((value): value is string => typeof value === "string" && value.length > 0)));
}

function errorResponse(content: string, error?: string): ChatApiResponse {
  return {
    message: {
      role: "assistant",
      content,
      createdAt: new Date().toISOString(),
    },
    answerStatus: "error",
    citations: [] as Citation[],
    retrieval: {
      vectorStatus: "unavailable",
      resultCount: 0,
      method: "none",
      sourceTypes: [],
    },
    error,
  };
}

function json(payload: ChatApiResponse, status: number) {
  return Response.json(payload, {
    status,
    headers: {
      "cache-control": "no-store",
    },
  });
}
