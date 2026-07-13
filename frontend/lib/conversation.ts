import type { AnswerStatus, ChatMessage, Citation, ContextPack, RetrievalSummary } from "@/lib/chat-types";

export function createPendingAssistantMessage(id: string, createdAt: string): ChatMessage {
  return {
    id,
    role: "assistant",
    content: "正在检索与整理本轮证据……",
    createdAt,
    answerStatus: "pending",
    evidence: { citations: [], retrieval: null, contextPack: null },
  };
}

export function completeAssistantMessage(
  message: ChatMessage,
  content: string,
  answerStatus: AnswerStatus,
  citations: Citation[],
  retrieval: RetrievalSummary | null,
  contextPack: ContextPack | null,
): ChatMessage {
  return { ...message, content, answerStatus, evidence: { citations, retrieval, contextPack } };
}
