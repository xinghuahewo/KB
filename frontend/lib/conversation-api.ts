import type {
  ChatMessage,
  ConversationDetail,
  ConversationSummary,
  EvidenceDetail,
  RetrievalSummary,
} from "@/lib/chat-types";
import { fetchRagAnswerStream, type StreamOptions } from "@/lib/rag-stream";
import type { StoredConversation } from "@/lib/storage";


type FetchOptions = { fetchImpl?: typeof fetch; baseUrl?: string };

export function createConversationApi(clientId: string, options: FetchOptions = {}) {
  const fetchImpl = options.fetchImpl || fetch;
  const baseUrl = (options.baseUrl ?? process.env.NEXT_PUBLIC_BGP_RAG_BASE_URL ?? "").replace(/\/+$/, "");
  const headers = { "content-type": "application/json", "X-BGP-Client-ID": clientId };

  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const response = await fetchImpl(`${baseUrl}${path}`, {
      ...init,
      headers: { ...headers, ...(init.headers || {}) },
    });
    if (!response.ok) {
      const payload = (await response.json().catch(() => ({}))) as { detail?: unknown };
      const detail = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail || payload);
      throw new Error(`会话服务返回 ${response.status}${detail ? `：${detail}` : ""}`);
    }
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  }

  return {
    create(title = "新会话") {
      return request<ConversationSummary>("/api/v1/conversations", {
        method: "POST",
        body: JSON.stringify({ title }),
      });
    },
    list(cursor?: string, limit = 30) {
      const params = new URLSearchParams({ limit: String(limit) });
      if (cursor) params.set("cursor", cursor);
      return request<{ items: ConversationSummary[]; next_cursor: string | null }>(
        `/api/v1/conversations?${params}`,
      );
    },
    get(conversationId: string) {
      return request<ConversationDetail>(`/api/v1/conversations/${encodeURIComponent(conversationId)}`);
    },
    delete(conversationId: string) {
      return request<void>(`/api/v1/conversations/${encodeURIComponent(conversationId)}`, { method: "DELETE" });
    },
    importLegacy(conversation: StoredConversation) {
      return request<ConversationDetail>("/api/v1/conversations/import", {
        method: "POST",
        body: JSON.stringify(conversation),
      });
    },
    streamTurn(
      conversationId: string,
      input: {
        requestId: string;
        query: string;
        userMessageId: string;
        assistantMessageId: string;
        resumeAfterSequence?: number;
      },
      streamOptions: StreamOptions,
    ) {
      return fetchRagAnswerStream(input.query, {
        ...streamOptions,
        fetchImpl,
        endpoint: `${baseUrl}/api/v1/conversations/${encodeURIComponent(conversationId)}/turns/stream`,
        headers,
        body: {
          request_id: input.requestId,
          query: input.query,
          limit: 8,
          user_message_id: input.userMessageId,
          assistant_message_id: input.assistantMessageId,
          resume_after_sequence: input.resumeAfterSequence || 0,
        },
        initialSequence: input.resumeAfterSequence || 0,
      });
    },
    stopTurn(conversationId: string, requestId: string) {
      return request<{ status: string }>(
        `/api/v1/conversations/${encodeURIComponent(conversationId)}/turns/${encodeURIComponent(requestId)}/stop`,
        { method: "POST", body: "{}" },
      );
    },
    evidence(
      conversationId: string,
      messageId: string,
      citationId: string,
      scope: "section" | "document" = "section",
      cursor = 0,
    ) {
      const params = new URLSearchParams({ scope, cursor: String(cursor) });
      return request<EvidenceDetail>(
        `/api/v1/conversations/${encodeURIComponent(conversationId)}/messages/${encodeURIComponent(messageId)}` +
          `/evidence/${encodeURIComponent(citationId)}?${params}`,
      );
    },
  };
}

export function messagesFromDetail(detail: ConversationDetail): ChatMessage[] {
  return detail.messages.map((message) => ({
    id: message.message_id,
    role: message.role,
    content: message.content,
    createdAt: message.created_at,
    updatedAt: message.updated_at,
    answerStatus: message.answer_status || undefined,
    answerParts: message.answer_parts || [],
    timings: message.timings || null,
    streamMode: message.stream_mode,
    syncStatus: message.sync_status || "synced",
    evidence: message.role === "assistant"
      ? {
          citations: message.citations || [],
          retrieval: historicalRetrieval(message.citations || []),
          contextPack: null,
        }
      : undefined,
  }));
}

function historicalRetrieval(citations: ConversationDetail["messages"][number]["citations"]): RetrievalSummary {
  const sourceCount = new Set((citations || []).map((citation) => citation.source_id || citation.source_ref).filter(Boolean)).size;
  return {
    vectorStatus: citations?.length ? "complete" : "unknown",
    resultCount: citations?.length || 0,
    method: "persisted",
    methodLabel: "历史证据快照",
    sourceTypes: [],
    sourceCount,
    evidenceLabel: citations?.length
      ? `已恢复 ${sourceCount} 个文档 / ${citations.length} 条证据`
      : "本轮没有持久化证据",
  };
}
