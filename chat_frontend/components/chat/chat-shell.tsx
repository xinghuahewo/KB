"use client";

import { useEffect, useMemo, useState } from "react";

import { CitationPanel } from "@/components/chat/citation-panel";
import { MessageComposer } from "@/components/chat/message-composer";
import { MessageList } from "@/components/chat/message-list";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { TopStatusBar } from "@/components/layout/top-status-bar";
import { createClientId } from "@/lib/client-id";
import type { AnswerStatus, ChatMessage, Citation, ContextPack, RagAnswerPayload, RetrievalSummary } from "@/lib/chat-types";
import { fetchRagAnswerStream, type RagStageEvent } from "@/lib/rag-stream";
import { clearStoredConversation, loadStoredConversation, saveStoredConversation } from "@/lib/storage";

export function ChatShell() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [answerStatus, setAnswerStatus] = useState<AnswerStatus | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [retrieval, setRetrieval] = useState<RetrievalSummary | null>(null);
  const [contextPack, setContextPack] = useState<ContextPack | null>(null);
  const [progressLabel, setProgressLabel] = useState<string | null>(null);

  const conversationId = useMemo(() => createClientId("conversation"), []);

  useEffect(() => {
    const stored = loadStoredConversation();
    if (!stored) {
      return;
    }
    setMessages(stored.messages);
    setCitations(stored.citations);
    setRetrieval(stored.retrieval);
  }, []);

  useEffect(() => {
    if (messages.length === 0) {
      return;
    }
    saveStoredConversation({
      id: conversationId,
      messages,
      citations,
      retrieval,
      updatedAt: new Date().toISOString(),
    });
  }, [citations, conversationId, messages, retrieval]);

  async function submit() {
    const question = input.trim();
    if (!question || busy) {
      return;
    }

    const userMessage: ChatMessage = {
      id: createClientId("message"),
      role: "user",
      content: question,
      createdAt: new Date().toISOString(),
    };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput("");
    setBusy(true);
    setAnswerStatus(null);
    setProgressLabel("问题已提交，正在进入知识库检索");

    try {
      const assistantId = createClientId("message");
      setMessages([
        ...nextMessages,
        {
          id: assistantId,
          role: "assistant",
          content: "问题已提交，正在进入知识库检索……",
          createdAt: new Date().toISOString(),
        },
      ]);

      const updateProgress = (label: string) => {
        setProgressLabel(label);
        setMessages((current) => current.map((message) => (message.id === assistantId ? { ...message, content: `${label}……` } : message)));
      };
      const payload = await fetchRagAnswerWithProgress(question, updateProgress);
      const status = normalizeAnswerStatus(payload.answer_status);
      const content = assistantContent(payload, status);
      setMessages((current) => current.map((message) => (message.id === assistantId ? { ...message, content } : message)));
      setAnswerStatus(status);
      setCitations(payload.citations || []);
      setRetrieval(summarizeRetrieval(payload));
      setContextPack(payload.context_pack || null);
    } catch (error) {
      const content = error instanceof Error ? error.message : "请求失败。";
      setMessages([
        ...nextMessages,
        {
          id: createClientId("message"),
          role: "assistant",
          content: `RAG 服务暂时不可用：${content}`,
          createdAt: new Date().toISOString(),
        },
      ]);
      setAnswerStatus("error");
      setCitations([]);
      setRetrieval({ vectorStatus: "unavailable", resultCount: 0, method: "none", methodLabel: "连接失败", sourceTypes: [] });
      setContextPack(null);
    } finally {
      setBusy(false);
      setProgressLabel(null);
    }
  }

  function clearConversation() {
    clearStoredConversation();
    setMessages([]);
    setInput("");
    setAnswerStatus(null);
    setCitations([]);
    setRetrieval(null);
    setContextPack(null);
    setProgressLabel(null);
  }

  return (
    <main className="grid min-h-screen grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)_360px]">
      <AppSidebar messageCount={messages.length} onClear={clearConversation} onExample={setInput} />
      <section className="flex min-h-screen flex-col">
        <TopStatusBar busy={busy} statusText={busy ? progressLabel || "正在查找资料" : "知识库就绪"} />
        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <MessageList messages={messages} answerStatus={answerStatus} retrieval={retrieval} citationCount={citations.length} />
        </div>
        <MessageComposer busy={busy} onChange={setInput} onSubmit={submit} value={input} />
      </section>
      <CitationPanel citations={citations} contextPack={contextPack} retrieval={retrieval} />
    </main>
  );
}

async function fetchRagAnswerWithProgress(query: string, onProgress: (label: string) => void) {
  const configuredBaseUrl = process.env.NEXT_PUBLIC_BGP_RAG_BASE_URL?.replace(/\/+$/, "");
  const endpoint = configuredBaseUrl ? `${configuredBaseUrl}/api/v1/rag/answer/stream` : "/api/v1/rag/answer/stream";
  try {
    return await fetchRagAnswerStream(query, {
      endpoint,
      limit: 8,
      onStage: (event) => onProgress(stageLabel(event)),
    });
  } catch (error) {
    if (error instanceof Error && /返回 (404|405)/.test(error.message)) {
      onProgress("流式状态不可用，正在等待最终回答");
      return fetchRagAnswer(query);
    }
    throw error;
  }
}

async function fetchRagAnswer(query: string) {
  const configuredBaseUrl = process.env.NEXT_PUBLIC_BGP_RAG_BASE_URL?.replace(/\/+$/, "");
  const endpoint = configuredBaseUrl ? `${configuredBaseUrl}/api/v1/rag/answer` : "/api/v1/rag/answer";
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ query, limit: 8 }),
  });
  const payload = (await response.json().catch(() => ({}))) as Partial<RagAnswerPayload> & { detail?: unknown };
  if (!response.ok) {
    const detail = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail || payload);
    throw new Error(`知识库服务返回 ${response.status}${detail ? `：${detail}` : ""}`);
  }
  return payload as RagAnswerPayload;
}

function stageLabel(event: RagStageEvent) {
  if (event.message) {
    return event.message;
  }
  if (event.stage === "retrieval" && event.status === "complete") {
    return "候选证据召回完成";
  }
  if (event.stage === "rerank") {
    return "正在精排证据";
  }
  if (event.stage === "context_pack") {
    return "正在组装引用上下文";
  }
  if (event.stage === "generation") {
    return "正在生成回答";
  }
  return "正在查找知识库资料";
}

function normalizeAnswerStatus(status: string): AnswerStatus {
  if (status === "answered" || status === "no_evidence" || status === "llm_unavailable") {
    return status;
  }
  return "error";
}

function assistantContent(payload: RagAnswerPayload, status: AnswerStatus) {
  if (status === "answered" && payload.answer.trim()) {
    return payload.answer;
  }
  if (status === "no_evidence") {
    return "没有找到足够证据回答这个问题。请尝试换一种问法，或提供更具体的 BGP 术语、事件名称、RFC 或案例线索。";
  }
  if (status === "llm_unavailable") {
    return "模型暂时不可用，因此没有生成最终答案。已保留本次检索到的证据，可先查看右侧引用和相关章节。";
  }
  return "RAG 服务暂时不可用，请确认知识库服务已经启动后重试。";
}

function summarizeRetrieval(payload: RagAnswerPayload): RetrievalSummary {
  const results = payload.context_pack?.results || [];
  const units = contextUnitsFrom(payload.context_pack);
  const method = firstString(results, "retrieval_method") || "hybrid";
  const sourceTypes = uniqueStrings([
    ...payload.citations.map((citation) => citation.source_type || citation.sourceType),
    ...results.map((result) => result.source_type),
  ]);
  const sourceCount = uniqueStrings([
    ...payload.citations.map((citation) => citation.source_id || citation.sourceId || citation.source_ref),
    ...results.map((result) => result.source_id || result.source_ref || result.doc_id),
  ]).length;
  const hasSectionContext = units.some((unit) => {
    const mode = String(unit.mode || "");
    return Boolean(unit.parent_section_heading || unit.parent_section_id || mode === "parent_span" || mode === "full_section");
  });
  return {
    vectorStatus: results.length > 0 ? "complete" : "unknown",
    resultCount: results.length,
    method,
    methodLabel: payload.context_pack?.degraded ? "已降级检索" : "混合证据检索",
    sourceTypes,
    sourceCount,
    contextUnitCount: units.length,
    hasSectionContext,
    evidenceLabel:
      results.length === 0
        ? "暂未找到证据"
        : hasSectionContext
          ? `已结合章节上下文 · ${sourceCount || 1} 个来源`
          : `已找到 ${results.length} 条证据`,
  };
}

function contextUnitsFrom(contextPack: ContextPack | null | undefined) {
  const units = contextPack?.context_units || contextPack?.contextUnits || [];
  return Array.isArray(units) ? units.filter((unit): unit is Record<string, unknown> => Boolean(unit && typeof unit === "object")) : [];
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
