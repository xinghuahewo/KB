"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { CitationPanel } from "@/components/chat/citation-panel";
import { MessageComposer } from "@/components/chat/message-composer";
import { MessageList } from "@/components/chat/message-list";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { TopStatusBar } from "@/components/layout/top-status-bar";
import { createClientId } from "@/lib/client-id";
import { completeAssistantMessage, createPendingAssistantMessage } from "@/lib/conversation";
import type { AnswerStatus, ChatMessage, ContextPack, RagAnswerPayload, RetrievalSummary } from "@/lib/chat-types";
import { fetchRagAnswerStream, type RagStageEvent } from "@/lib/rag-stream";
import { clearStoredConversation, loadStoredConversation, saveStoredConversation } from "@/lib/storage";

export function ChatShell() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [progressLabel, setProgressLabel] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState(() => createClientId("conversation"));
  const [selectedAssistantId, setSelectedAssistantId] = useState<string>();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const requestController = useRef<AbortController | null>(null);

  const selectedMessage = useMemo(() => messages.find((message) => message.id === selectedAssistantId && message.role === "assistant"), [messages, selectedAssistantId]);
  const evidenceAvailable = Boolean(selectedMessage?.evidence?.citations.length || selectedMessage?.answerStatus === "pending");

  useEffect(() => {
    const stored = loadStoredConversation();
    if (!stored) return;
    setMessages(stored.messages);
    setConversationId(stored.id);
    setSelectedAssistantId([...stored.messages].reverse().find((message) => message.role === "assistant")?.id);
  }, []);

  useEffect(() => {
    if (busy || messages.length === 0) return;
    const timer = window.setTimeout(() => saveStoredConversation({ version: 2, id: conversationId, messages, citations: [], retrieval: null, updatedAt: new Date().toISOString() }), 300);
    return () => window.clearTimeout(timer);
  }, [busy, conversationId, messages]);

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") { setSidebarOpen(false); setEvidenceOpen(false); } };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);

  async function submit() {
    const question = input.trim();
    if (!question || busy) return;
    const userMessage: ChatMessage = { id: createClientId("message"), role: "user", content: question, createdAt: new Date().toISOString() };
    const assistantId = createClientId("message");
    const assistantMessage = createPendingAssistantMessage(assistantId, new Date().toISOString());
    setMessages((current) => [...current, userMessage, assistantMessage]);
    setSelectedAssistantId(assistantId);
    setInput(""); setBusy(true); setProgressLabel("问题已提交，正在进入知识库检索");
    const controller = new AbortController(); requestController.current = controller;
    try {
      const payload = await fetchRagAnswerWithProgress(question, (label) => { setProgressLabel(label); setMessages((current) => current.map((message) => message.id === assistantId ? { ...message, content: `${label}……` } : message)); }, controller.signal);
      const status = normalizeAnswerStatus(payload.answer_status);
      const retrieval = summarizeRetrieval(payload);
      setMessages((current) => current.map((message) => message.id === assistantId ? completeAssistantMessage(message, assistantContent(payload, status), status, payload.citations || [], retrieval, payload.context_pack || null) : message));
    } catch (error) {
      const stopped = error instanceof Error && error.message.includes("已停止生成");
      const content = stopped ? "已停止生成。你可以修改问题后重新发送。" : `RAG 服务暂时不可用：${error instanceof Error ? error.message : "请求失败。"}`;
      const status: AnswerStatus = stopped ? "stopped" : "error";
      setMessages((current) => current.map((message) => message.id === assistantId ? completeAssistantMessage(message, content, status, [], { vectorStatus: "unavailable", resultCount: 0, method: "none", methodLabel: stopped ? "请求已停止" : "连接失败", sourceTypes: [] }, null) : message));
    } finally { if (requestController.current === controller) requestController.current = null; setBusy(false); setProgressLabel(null); }
  }

  function stop() { requestController.current?.abort(); }
  function clearConversation() { requestController.current?.abort(); clearStoredConversation(); setMessages([]); setInput(""); setSelectedAssistantId(undefined); setProgressLabel(null); setSidebarOpen(false); setEvidenceOpen(false); setConversationId(createClientId("conversation")); }
  function selectEvidence(id: string) { setSelectedAssistantId(id); setEvidenceOpen(true); }

  return <main className={`grid h-[100dvh] overflow-hidden ${evidenceAvailable ? "xl:grid-cols-[260px_minmax(0,1fr)_360px]" : "xl:grid-cols-[260px_minmax(0,1fr)]"}`}>
    <AppSidebar className="hidden min-h-0 overflow-y-auto border-r border-[var(--line)] xl:block" messageCount={messages.length} onClear={clearConversation} onExample={setInput} />
    <section aria-label="对话" className="flex min-h-0 flex-col"><TopStatusBar busy={busy} evidenceAvailable={evidenceAvailable} onOpenEvidence={() => setEvidenceOpen(true)} onOpenSidebar={() => setSidebarOpen(true)} statusText={busy ? progressLabel || "正在查找资料" : "知识库就绪"} /><div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-5 md:px-6"><MessageList messages={messages} onSelectEvidence={selectEvidence} selectedAssistantId={selectedAssistantId} /></div><MessageComposer busy={busy} onChange={setInput} onStop={stop} onSubmit={submit} value={input} /></section>
    {evidenceAvailable ? <CitationPanel className="hidden min-h-0 border-l border-[var(--line)] xl:flex" message={selectedMessage} /> : null}
    {sidebarOpen ? <Drawer onClose={() => setSidebarOpen(false)}><AppSidebar className="h-full overflow-y-auto" messageCount={messages.length} onClear={clearConversation} onClose={() => setSidebarOpen(false)} onExample={(prompt) => { setInput(prompt); setSidebarOpen(false); }} /></Drawer> : null}
    {evidenceOpen ? <Drawer align="right" onClose={() => setEvidenceOpen(false)}><CitationPanel className="h-full" message={selectedMessage} onClose={() => setEvidenceOpen(false)} /></Drawer> : null}
  </main>;
}

function Drawer({ children, align = "left", onClose }: { children: React.ReactNode; align?: "left" | "right"; onClose: () => void }) { return <div className="fixed inset-0 z-50 xl:hidden"><button aria-label="关闭抽屉" className="absolute inset-0 cursor-default bg-black/30" onClick={onClose} type="button" /><div className={`absolute inset-y-0 w-[min(88vw,380px)] bg-[var(--panel)] shadow-2xl ${align === "right" ? "right-0" : "left-0"}`}>{children}</div></div>; }

async function fetchRagAnswerWithProgress(query: string, onProgress: (label: string) => void, signal: AbortSignal) { const configuredBaseUrl = process.env.NEXT_PUBLIC_BGP_RAG_BASE_URL?.replace(/\/+$/, ""); const endpoint = configuredBaseUrl ? `${configuredBaseUrl}/api/v1/rag/answer/stream` : "/api/v1/rag/answer/stream"; try { return await fetchRagAnswerStream(query, { endpoint, limit: 8, signal, onStage: (event) => onProgress(stageLabel(event)) }); } catch (error) { if (error instanceof Error && /返回 (404|405)/.test(error.message)) { onProgress("流式状态不可用，正在等待最终回答"); return fetchRagAnswer(query, signal); } throw error; } }
async function fetchRagAnswer(query: string, signal: AbortSignal) { const configuredBaseUrl = process.env.NEXT_PUBLIC_BGP_RAG_BASE_URL?.replace(/\/+$/, ""); const endpoint = configuredBaseUrl ? `${configuredBaseUrl}/api/v1/rag/answer` : "/api/v1/rag/answer"; const response = await fetch(endpoint, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ query, limit: 8 }), signal }); const payload = (await response.json().catch(() => ({}))) as Partial<RagAnswerPayload> & { detail?: unknown }; if (!response.ok) { const detail = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail || payload); throw new Error(`知识库服务返回 ${response.status}${detail ? `：${detail}` : ""}`); } return payload as RagAnswerPayload; }
function stageLabel(event: RagStageEvent) { if (event.message) return event.message; if (event.stage === "retrieval" && event.status === "complete") return "候选证据召回完成"; if (event.stage === "rerank") return "正在精排证据"; if (event.stage === "context_pack") return "正在组装引用上下文"; if (event.stage === "generation") return "正在生成回答"; return "正在查找知识库资料"; }
function normalizeAnswerStatus(status: string): AnswerStatus { return status === "answered" || status === "no_evidence" || status === "llm_unavailable" ? status : "error"; }
function assistantContent(payload: RagAnswerPayload, status: AnswerStatus) { if (status === "answered" && payload.answer.trim()) return payload.answer; if (status === "no_evidence") return "没有找到足够证据回答这个问题。请尝试换一种问法，或提供更具体的 BGP 术语、事件名称、RFC 或案例线索。"; if (status === "llm_unavailable") return "模型暂时不可用，因此没有生成最终答案。已保留本次检索到的证据，可先查看本轮引用和相关章节。"; return "RAG 服务暂时不可用，请确认知识库服务已经启动后重试。"; }
function summarizeRetrieval(payload: RagAnswerPayload): RetrievalSummary { const results = payload.context_pack?.results || []; const units = contextUnitsFrom(payload.context_pack); const method = firstString(results, "retrieval_method") || "hybrid"; const sourceTypes = uniqueStrings([...payload.citations.map((citation) => citation.source_type || citation.sourceType), ...results.map((result) => result.source_type)]); const sourceCount = new Set(payload.citations.map((citation) => String(citation.source_id || citation.sourceId || citation.source_ref || "").split(/[?#]/)[0]).filter(Boolean)).size; const hasSectionContext = units.some((unit) => Boolean(unit.parent_section_heading || unit.parent_section_id || unit.mode === "parent_span" || unit.mode === "full_section")); return { vectorStatus: results.length > 0 ? "complete" : "unknown", resultCount: results.length, method, methodLabel: payload.context_pack?.degraded ? "已降级检索" : "混合证据检索", sourceTypes, sourceCount, contextUnitCount: units.length, hasSectionContext, evidenceLabel: results.length === 0 ? "暂未找到证据" : `已找到 ${sourceCount} 个文档 / ${payload.citations.length} 条证据` }; }
function contextUnitsFrom(contextPack: ContextPack | null | undefined) { const units = contextPack?.context_units || contextPack?.contextUnits || []; return Array.isArray(units) ? units.filter((unit): unit is Record<string, unknown> => Boolean(unit && typeof unit === "object")) : []; }
function firstString(records: Array<Record<string, unknown>>, key: string) { for (const record of records) { const value = record[key]; if (typeof value === "string" && value) return value; } return ""; }
function uniqueStrings(values: unknown[]) { return Array.from(new Set(values.filter((value): value is string => typeof value === "string" && value.length > 0))); }
