"use client";

import { ArrowDown } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { CitationPanel } from "@/components/chat/citation-panel";
import { MessageComposer } from "@/components/chat/message-composer";
import { MessageList } from "@/components/chat/message-list";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { TopStatusBar } from "@/components/layout/top-status-bar";
import { getOrCreateClientId, createClientId } from "@/lib/client-id";
import { createConversationApi, messagesFromDetail } from "@/lib/conversation-api";
import { createPendingAssistantMessage } from "@/lib/conversation";
import { RagStreamError, type RagStageEvent } from "@/lib/rag-stream";
import {
  clearStoredConversation,
  loadActiveConversationId,
  loadStoredConversation,
  loadUnsyncedTurns,
  removeUnsyncedTurn,
  saveActiveConversationId,
  saveUnsyncedTurn,
  type UnsyncedTurn,
} from "@/lib/storage";
import type {
  AnswerPart,
  AnswerStatus,
  ChatMessage,
  ContextPack,
  ConversationSummary,
  EvidenceDetail,
  RagAnswerPayload,
  RetrievalSummary,
} from "@/lib/chat-types";


type ActiveRequest = UnsyncedTurn & {
  controller: AbortController;
  stopAck?: Promise<boolean>;
};

export function ChatShell() {
  const [clientId] = useState(() => getOrCreateClientId());
  const api = useMemo(() => createConversationApi(clientId), [clientId]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [activeConversationId, setActiveConversationId] = useState<string>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [statusText, setStatusText] = useState("正在恢复历史会话");
  const [historyLoading, setHistoryLoading] = useState(true);
  const [selectedAssistantId, setSelectedAssistantId] = useState<string>();
  const [activeCitationId, setActiveCitationId] = useState<string>();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [evidenceCache, setEvidenceCache] = useState<Record<string, EvidenceDetail>>({});
  const [evidenceErrors, setEvidenceErrors] = useState<Record<string, string>>({});
  const [evidenceLoadingKey, setEvidenceLoadingKey] = useState<string>();
  const [showReturnLatest, setShowReturnLatest] = useState(false);
  const requestRef = useRef<ActiveRequest | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const nearBottomRef = useRef(true);
  const citationTriggerRef = useRef<HTMLElement | null>(null);

  const selectedMessage = useMemo(
    () => messages.find((message) => message.id === selectedAssistantId && message.role === "assistant"),
    [messages, selectedAssistantId],
  );
  const evidenceAvailable = Boolean(selectedMessage?.evidence?.citations.length || selectedMessage?.answerStatus === "pending");
  const evidenceKey = activeConversationId && selectedAssistantId && activeCitationId
    ? `${activeConversationId}:${selectedAssistantId}:${activeCitationId}`
    : undefined;
  const activeEvidence = evidenceKey ? evidenceCache[evidenceKey] : undefined;
  const activeEvidenceError = evidenceKey ? evidenceErrors[evidenceKey] : undefined;

  useEffect(() => {
    let cancelled = false;
    async function initialize() {
      let importedId: string | undefined;
      const legacy = loadStoredConversation();
      if (legacy) {
        try {
          const imported = await api.importLegacy(legacy);
          importedId = imported.conversation_id;
          clearStoredConversation();
        } catch {
          if (!cancelled) {
            setMessages(legacy.messages.map((message) => ({ ...message, syncStatus: "unsynced" })));
            setStatusText("旧会话尚未同步");
          }
        }
      }
      try {
        const page = await api.list();
        if (cancelled) return;
        let items = page.items;
        if (!items.length) {
          const created = await api.create();
          items = [created];
        }
        setConversations(items);
        setNextCursor(page.next_cursor);
        const storedActive = loadActiveConversationId();
        const preferred = importedId || (items.some((item) => item.conversation_id === storedActive) ? storedActive! : items[0].conversation_id);
        const detail = await api.get(preferred);
        if (cancelled) return;
        setActiveConversationId(preferred);
        saveActiveConversationId(preferred);
        const restored = messagesFromDetail(detail);
        setMessages(restored);
        setSelectedAssistantId([...restored].reverse().find((message) => message.role === "assistant")?.id);
        setStatusText("知识库就绪");
        const pending = loadUnsyncedTurns().find((turn) => turn.conversationId === preferred);
        if (pending) void executeTurn(pending, false);
      } catch (error) {
        if (!cancelled) setStatusText(`历史服务不可用：${error instanceof Error ? error.message : "连接失败"}`);
      } finally {
        if (!cancelled) setHistoryLoading(false);
      }
    }
    void initialize();
    return () => { cancelled = true; requestRef.current?.controller.abort(); };
    // 初始化只在匿名客户端命名空间确定后运行一次。
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api]);

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setSidebarOpen(false);
        closeEvidence();
      }
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);

  useEffect(() => {
    if (!evidenceKey || evidenceCache[evidenceKey] || evidenceLoadingKey === evidenceKey) return;
    setEvidenceLoadingKey(evidenceKey);
    api.evidence(activeConversationId!, selectedAssistantId!, activeCitationId!)
      .then((detail) => {
        setEvidenceCache((current) => ({ ...current, [evidenceKey]: detail }));
        setEvidenceErrors((current) => {
          const next = { ...current };
          delete next[evidenceKey];
          return next;
        });
      })
      .catch((error) => setEvidenceErrors((current) => ({ ...current, [evidenceKey]: error instanceof Error ? error.message : "证据加载失败" })))
      .finally(() => setEvidenceLoadingKey((current) => current === evidenceKey ? undefined : current));
  }, [activeCitationId, activeConversationId, api, evidenceCache, evidenceKey, evidenceLoadingKey, selectedAssistantId]);

  const lastMessageLength = messages[messages.length - 1]?.content.length || 0;
  useEffect(() => {
    if (!nearBottomRef.current) return;
    const frame = window.requestAnimationFrame(() => scrollToLatest(false));
    return () => window.cancelAnimationFrame(frame);
  }, [lastMessageLength, messages.length]);

  async function refreshHistory(cursor?: string) {
    setHistoryLoading(true);
    try {
      const page = await api.list(cursor);
      setConversations((current) => cursor
        ? [...current, ...page.items.filter((item) => !current.some((existing) => existing.conversation_id === item.conversation_id))]
        : page.items,
      );
      setNextCursor(page.next_cursor);
    } finally {
      setHistoryLoading(false);
    }
  }

  async function openConversation(id: string) {
    if (busy || id === activeConversationId) {
      setSidebarOpen(false);
      return;
    }
    setHistoryLoading(true);
    try {
      const detail = await api.get(id);
      const restored = messagesFromDetail(detail);
      setActiveConversationId(id);
      saveActiveConversationId(id);
      setMessages(restored);
      setSelectedAssistantId([...restored].reverse().find((message) => message.role === "assistant")?.id);
      setActiveCitationId(undefined);
      setEvidenceOpen(false);
      setSidebarOpen(false);
      setStatusText("历史会话已恢复");
    } finally {
      setHistoryLoading(false);
    }
  }

  async function newConversation() {
    if (busy) return;
    setHistoryLoading(true);
    try {
      const created = await api.create();
      setConversations((current) => [created, ...current]);
      setActiveConversationId(created.conversation_id);
      saveActiveConversationId(created.conversation_id);
      setMessages([]);
      setSelectedAssistantId(undefined);
      setActiveCitationId(undefined);
      setSidebarOpen(false);
      setStatusText("新会话已建立");
    } finally {
      setHistoryLoading(false);
    }
  }

  async function deleteConversation(id: string) {
    if (busy && id === activeConversationId) return;
    await api.delete(id);
    const remaining = conversations.filter((conversation) => conversation.conversation_id !== id);
    setConversations(remaining);
    if (id !== activeConversationId) return;
    if (remaining[0]) await openConversation(remaining[0].conversation_id);
    else await newConversation();
  }

  async function submit() {
    const query = input.trim();
    if (!query || busy) return;
    let conversationId = activeConversationId;
    if (!conversationId) {
      const created = await api.create();
      conversationId = created.conversation_id;
      setActiveConversationId(conversationId);
      setConversations((current) => [created, ...current]);
      saveActiveConversationId(conversationId);
    }
    const turn: UnsyncedTurn = {
      conversationId,
      requestId: createClientId("request"),
      query,
      userMessageId: createClientId("message"),
      assistantMessageId: createClientId("message"),
      lastSequence: 0,
      createdAt: new Date().toISOString(),
    };
    setInput("");
    await executeTurn(turn, true);
  }

  async function executeTurn(turn: UnsyncedTurn, appendOptimistic: boolean) {
    if (requestRef.current) return;
    const controller = new AbortController();
    requestRef.current = { ...turn, controller };
    setBusy(true);
    setStatusText(turn.lastSequence ? "正在恢复未完成回答" : "问题已提交");
    saveUnsyncedTurn(turn);
    if (appendOptimistic) {
      const userMessage: ChatMessage = {
        id: turn.userMessageId,
        role: "user",
        content: turn.query,
        createdAt: turn.createdAt,
        syncStatus: "syncing",
      };
      const assistant = {
        ...createPendingAssistantMessage(turn.assistantMessageId, turn.createdAt),
        requestId: turn.requestId,
      };
      setMessages((current) => [...current, userMessage, assistant]);
      setSelectedAssistantId(turn.assistantMessageId);
    } else {
      setMessages((current) => {
        if (current.some((message) => message.id === turn.assistantMessageId)) return current;
        return [
          ...current,
          { id: turn.userMessageId, role: "user", content: turn.query, createdAt: turn.createdAt, syncStatus: "unsynced" },
          { ...createPendingAssistantMessage(turn.assistantMessageId, turn.createdAt), requestId: turn.requestId, syncStatus: "unsynced" },
        ];
      });
    }
    let deltaBuffer = "";
    let flushTimer: number | undefined;
    let lastSequence = turn.lastSequence;
    let lastRecoveryWrite = 0;
    const flushDelta = () => {
      window.clearTimeout(flushTimer);
      flushTimer = undefined;
      if (!deltaBuffer) return;
      const delta = deltaBuffer;
      deltaBuffer = "";
      setMessages((current) => updateMessage(current, turn.assistantMessageId, (message) => appendText(message, delta)));
    };
    const scheduleDelta = (delta: string) => {
      deltaBuffer += delta;
      if (flushTimer === undefined) flushTimer = window.setTimeout(flushDelta, 40);
    };

    try {
      const payload = await api.streamTurn(
        turn.conversationId,
        {
          requestId: turn.requestId,
          query: turn.query,
          userMessageId: turn.userMessageId,
          assistantMessageId: turn.assistantMessageId,
          resumeAfterSequence: turn.lastSequence,
        },
        {
          signal: controller.signal,
          onEvent: (event) => {
            if (typeof event.sequence === "number") {
              lastSequence = event.sequence;
              const now = performance.now();
              if (now - lastRecoveryWrite >= 250 || event.type === "done" || event.type === "error") {
                saveUnsyncedTurn({ ...turn, lastSequence });
                lastRecoveryWrite = now;
              }
            }
          },
          onStage: (event) => {
            setStatusText(event.message || stageLabel(event));
            setMessages((current) => updateMessage(current, turn.assistantMessageId, (message) => applyStage(message, event)));
          },
          onAnswerDelta: (event) => scheduleDelta(event.delta),
          onCitationDelta: (event) => {
            flushDelta();
            setMessages((current) => updateMessage(current, turn.assistantMessageId, (message) => appendCitation(message, event.citation_ids, event.label)));
          },
          onAnswerSnapshot: (event) => {
            flushDelta();
            setMessages((current) => updateMessage(current, turn.assistantMessageId, (message) => ({
              ...message,
              content: event.answer,
              answerParts: event.answer_parts || [{ type: "text", text: event.answer }],
              streamMode: event.stream_mode || message.streamMode,
            })));
          },
        },
      );
      flushDelta();
      const status = normalizeAnswerStatus(payload.answer_status);
      setMessages((current) => updateMessage(current, turn.assistantMessageId, (message) => ({
        ...message,
        content: assistantContent(payload, status),
        answerParts: payload.answer_parts || (payload.answer ? [{ type: "text", text: payload.answer }] : message.answerParts),
        answerStatus: status,
        timings: payload.timings || null,
        streamMode: payload.stream_mode || "buffered",
        syncStatus: "synced",
        lastSequence,
        evidence: {
          citations: payload.citations || [],
          retrieval: summarizeRetrieval(payload),
          contextPack: payload.context_pack || null,
        },
      })));
      setMessages((current) => current.map((message) => message.id === turn.userMessageId ? { ...message, syncStatus: "synced" } : message));
      removeUnsyncedTurn(turn.requestId);
      setStatusText(status === "answered" ? "回答与证据已保存" : "本轮已完成");
      await refreshHistory();
    } catch (error) {
      flushDelta();
      const streamError = error instanceof RagStreamError ? error : undefined;
      const activeRequest = requestRef.current?.requestId === turn.requestId ? requestRef.current : undefined;
      const stoppedByServer = streamError?.event?.status === "stopped";
      const stopped = Boolean(activeRequest?.stopAck || stoppedByServer);
      const stopSynced = stoppedByServer || (activeRequest?.stopAck ? await activeRequest.stopAck : false);
      const partial = streamError?.event?.partial_answer;
      setMessages((current) => updateMessage(current, turn.assistantMessageId, (message) => ({
        ...message,
        content: partial || message.content || (stopped ? "" : "生成在首字前中断。"),
        answerParts: message.answerParts?.length ? message.answerParts : partial ? [{ type: "text", text: partial }] : [],
        answerStatus: stopped ? "stopped" : message.content || partial ? "interrupted" : "error",
        timings: streamError?.event?.timings || message.timings,
        syncStatus: stopSynced ? "synced" : "unsynced",
        lastSequence,
      })));
      setMessages((current) => current.map((message) => message.id === turn.userMessageId
        ? { ...message, syncStatus: stopSynced ? "synced" : "unsynced" }
        : message));
      if (stopSynced) {
        removeUnsyncedTurn(turn.requestId);
        setStatusText("已停止并保留部分回答");
        await refreshHistory();
      } else {
        saveUnsyncedTurn({ ...turn, lastSequence });
        setStatusText(stopped ? "已停止，本地回答尚未同步" : "连接中断，回答尚未同步");
      }
    } finally {
      window.clearTimeout(flushTimer);
      if (requestRef.current?.requestId === turn.requestId) requestRef.current = null;
      setBusy(false);
    }
  }

  function stop() {
    const active = requestRef.current;
    if (!active) return;
    setStatusText("正在停止生成");
    active.stopAck = api.stopTurn(active.conversationId, active.requestId).then(() => true, () => false);
    active.controller.abort();
  }

  function selectCitation(messageId: string, citationId: string) {
    citationTriggerRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setSelectedAssistantId(messageId);
    setActiveCitationId(citationId);
    setEvidenceOpen(true);
  }

  function selectEvidence(messageId: string) {
    const message = messages.find((item) => item.id === messageId);
    const firstCitation = message?.evidence?.citations[0];
    setSelectedAssistantId(messageId);
    setActiveCitationId(String(firstCitation?.citation_id || firstCitation?.citationId || "") || undefined);
    setEvidenceOpen(true);
  }

  function closeEvidence() {
    setEvidenceOpen(false);
    window.setTimeout(() => citationTriggerRef.current?.focus(), 0);
  }

  function retryEvidence() {
    if (!evidenceKey) return;
    setEvidenceCache((current) => {
      const next = { ...current };
      delete next[evidenceKey];
      return next;
    });
    setEvidenceErrors((current) => {
      const next = { ...current };
      delete next[evidenceKey];
      return next;
    });
  }

  async function loadDocument(cursor = 0) {
    if (!evidenceKey || !activeConversationId || !selectedAssistantId || !activeCitationId) return;
    setEvidenceLoadingKey(evidenceKey);
    try {
      const detail = await api.evidence(activeConversationId, selectedAssistantId, activeCitationId, "document", cursor);
      setEvidenceCache((current) => ({
        ...current,
        [evidenceKey]: cursor > 0 && current[evidenceKey]
          ? { ...detail, sections: [...current[evidenceKey].sections, ...detail.sections] }
          : detail,
      }));
    } catch (error) {
      setEvidenceErrors((current) => ({ ...current, [evidenceKey]: error instanceof Error ? error.message : "文档加载失败" }));
    } finally {
      setEvidenceLoadingKey(undefined);
    }
  }

  function onScroll() {
    const element = scrollRef.current;
    if (!element) return;
    const nearBottom = element.scrollHeight - element.scrollTop - element.clientHeight < 96;
    nearBottomRef.current = nearBottom;
    setShowReturnLatest(!nearBottom);
  }

  function scrollToLatest(smooth = true) {
    const element = scrollRef.current;
    if (!element) return;
    element.scrollTo({ top: element.scrollHeight, behavior: smooth ? "smooth" : "auto" });
    nearBottomRef.current = true;
    setShowReturnLatest(false);
  }

  const sidebarProps = {
    activeConversationId,
    conversations,
    loading: historyLoading,
    nextCursor,
    onDelete: deleteConversation,
    onExample: setInput,
    onLoadMore: nextCursor ? () => refreshHistory(nextCursor) : undefined,
    onNew: newConversation,
    onSelect: openConversation,
  };

  return (
    <main className={`grid h-[100dvh] overflow-hidden ${evidenceAvailable ? "xl:grid-cols-[280px_minmax(0,1fr)_390px]" : "xl:grid-cols-[280px_minmax(0,1fr)]"}`}>
      <AppSidebar {...sidebarProps} className="hidden min-h-0 border-r border-[var(--line)] xl:flex" />
      <section aria-label="对话" className="flex min-h-0 min-w-0 flex-col">
        <TopStatusBar busy={busy} evidenceAvailable={evidenceAvailable} onOpenEvidence={() => setEvidenceOpen(true)} onOpenSidebar={() => setSidebarOpen(true)} statusText={statusText} />
        <div className="relative min-h-0 flex-1">
          <div className="h-full overflow-y-auto overscroll-contain px-4 py-5 md:px-6" onScroll={onScroll} ref={scrollRef}>
            <MessageList activeCitationId={activeCitationId} messages={messages} onSelectCitation={selectCitation} onSelectEvidence={selectEvidence} selectedAssistantId={selectedAssistantId} />
          </div>
          {showReturnLatest ? <button className="absolute bottom-4 left-1/2 inline-flex min-h-10 -translate-x-1/2 items-center gap-2 border border-[var(--line-strong)] bg-white px-4 text-xs font-semibold shadow-lg" onClick={() => scrollToLatest()} type="button"><ArrowDown className="h-4 w-4" aria-hidden="true" />回到最新</button> : null}
        </div>
        <MessageComposer busy={busy} onChange={setInput} onStop={stop} onSubmit={submit} value={input} />
      </section>
      {evidenceAvailable ? <CitationPanel activeCitationId={activeCitationId} className="hidden min-h-0 border-l border-[var(--line)] xl:flex" detail={activeEvidence} error={activeEvidenceError} loading={evidenceLoadingKey === evidenceKey} message={selectedMessage} onLoadDocument={loadDocument} onRetry={retryEvidence} /> : null}
      {sidebarOpen ? <Drawer onClose={() => setSidebarOpen(false)}><AppSidebar {...sidebarProps} className="h-full" onClose={() => setSidebarOpen(false)} onExample={(prompt) => { setInput(prompt); setSidebarOpen(false); }} /></Drawer> : null}
      {evidenceOpen ? <Drawer align="right" onClose={closeEvidence}><CitationPanel activeCitationId={activeCitationId} className="h-full" detail={activeEvidence} error={activeEvidenceError} loading={evidenceLoadingKey === evidenceKey} message={selectedMessage} onClose={closeEvidence} onLoadDocument={loadDocument} onRetry={retryEvidence} /></Drawer> : null}
    </main>
  );
}

function Drawer({ children, align = "left", onClose }: { children: React.ReactNode; align?: "left" | "right"; onClose: () => void }) {
  return <div className="fixed inset-0 z-50 xl:hidden"><button aria-label="关闭抽屉" className="absolute inset-0 cursor-default bg-black/30" onClick={onClose} type="button" /><div className={`absolute inset-y-0 w-[min(92vw,410px)] bg-[var(--panel)] shadow-2xl ${align === "right" ? "right-0" : "left-0"}`}>{children}</div></div>;
}

function updateMessage(messages: ChatMessage[], id: string, update: (message: ChatMessage) => ChatMessage) {
  return messages.map((message) => message.id === id ? update(message) : message);
}

function appendText(message: ChatMessage, delta: string): ChatMessage {
  const parts = [...(message.answerParts || [])];
  if (parts.length && parts[parts.length - 1].type === "text") {
    const last = parts[parts.length - 1] as Extract<AnswerPart, { type: "text" }>;
    parts[parts.length - 1] = { ...last, text: last.text + delta };
  } else {
    parts.push({ type: "text", text: delta });
  }
  return { ...message, content: message.content + delta, answerParts: parts };
}

function appendCitation(message: ChatMessage, citationIds: string[], label: string): ChatMessage {
  return {
    ...message,
    content: `${message.content}[${label}]`,
    answerParts: [...(message.answerParts || []), { type: "citation", citation_ids: citationIds, label }],
  };
}

function applyStage(message: ChatMessage, event: RagStageEvent): ChatMessage {
  const current = message.stages || [];
  const previous = current.find((stage) => stage.stage === event.stage);
  const stage = {
    stage: event.stage,
    status: event.status || "started",
    message: event.message,
    durationMs: typeof event.duration_ms === "number" ? event.duration_ms : previous?.durationMs,
    elapsedMs: typeof event.elapsed_ms === "number" ? event.elapsed_ms : previous?.elapsedMs,
    startedAt: event.status === "started" ? performance.now() : previous?.startedAt,
  };
  return { ...message, stages: [...current.filter((item) => item.stage !== event.stage), stage] };
}

function normalizeAnswerStatus(status: string): AnswerStatus {
  return ["answered", "no_evidence", "llm_unavailable", "stopped", "interrupted"].includes(status)
    ? status as AnswerStatus
    : "error";
}

function assistantContent(payload: RagAnswerPayload, status: AnswerStatus) {
  if (payload.answer?.trim()) return payload.answer;
  if (status === "no_evidence") return "没有找到足够证据回答这个问题。请尝试换一种问法，或提供更具体的 BGP 术语、事件名称、RFC 或案例线索。";
  if (status === "llm_unavailable") return "模型暂时不可用，因此没有生成最终答案。已保留本次检索到的证据。";
  return "";
}

function stageLabel(event: RagStageEvent) {
  if (event.stage === "retrieval") return "正在召回候选证据";
  if (event.stage === "rerank") return "正在精排证据";
  if (event.stage === "context_pack") return "正在组装引用上下文";
  if (event.stage === "generation") return "正在生成回答";
  return "正在处理本轮问题";
}

function summarizeRetrieval(payload: RagAnswerPayload): RetrievalSummary {
  const results = payload.context_pack?.results || [];
  const units = contextUnitsFrom(payload.context_pack);
  const sourceCount = new Set(payload.citations.map((citation) => citation.source_id || citation.source_ref).filter(Boolean)).size;
  return {
    vectorStatus: results.length ? "complete" : payload.citations.length ? "complete" : "unknown",
    resultCount: results.length,
    method: "hybrid",
    methodLabel: payload.context_pack?.degraded ? "已降级检索" : "混合证据检索",
    sourceTypes: [],
    sourceCount,
    contextUnitCount: units.length,
    hasSectionContext: units.length > 0,
    evidenceLabel: payload.citations.length
      ? `已找到 ${sourceCount} 个文档 / ${payload.citations.length} 条证据`
      : "暂未找到证据",
  };
}

function contextUnitsFrom(contextPack: ContextPack | null | undefined) {
  const units = contextPack?.context_units || contextPack?.contextUnits || [];
  return Array.isArray(units) ? units : [];
}
