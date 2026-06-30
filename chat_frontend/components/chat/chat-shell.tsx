"use client";

import { useEffect, useMemo, useState } from "react";

import { CitationPanel } from "@/components/chat/citation-panel";
import { MessageComposer } from "@/components/chat/message-composer";
import { MessageList } from "@/components/chat/message-list";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { TopStatusBar } from "@/components/layout/top-status-bar";
import type { AnswerStatus, ChatMessage, Citation, ContextPack, RagAnswerPayload, RetrievalSummary } from "@/lib/chat-types";
import { clearStoredConversation, loadStoredConversation, saveStoredConversation } from "@/lib/storage";

export function ChatShell() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [answerStatus, setAnswerStatus] = useState<AnswerStatus | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [retrieval, setRetrieval] = useState<RetrievalSummary | null>(null);
  const [contextPack, setContextPack] = useState<ContextPack | null>(null);

  const conversationId = useMemo(() => crypto.randomUUID(), []);

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
      id: crypto.randomUUID(),
      role: "user",
      content: question,
      createdAt: new Date().toISOString(),
    };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput("");
    setBusy(true);
    setAnswerStatus(null);

    try {
      const assistantId = crypto.randomUUID();
      setMessages([
        ...nextMessages,
        {
          id: assistantId,
          role: "assistant",
          content: "",
          createdAt: new Date().toISOString(),
        },
      ]);

      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ messages: nextMessages, options: { limit: 8, showCitations: true } }),
      });

      if (!response.body) {
        throw new Error("浏览器不支持流式响应。");
      }

      await readChatStream(response.body, (event) => {
        if (event.type === "delta") {
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantId ? { ...message, content: `${message.content}${event.content || ""}` } : message,
            ),
          );
          return;
        }

        if (event.type === "done") {
          setAnswerStatus(event.answerStatus);
          setCitations(event.citations || []);
          setRetrieval(event.retrieval || null);
          setContextPack(event.raw?.context_pack || null);
          return;
        }

        if (event.type === "error") {
          setMessages((current) =>
            current.map((message) => (message.id === assistantId ? { ...message, content: event.content || "请求失败。" } : message)),
          );
          setAnswerStatus("error");
          setCitations([]);
          setRetrieval({ vectorStatus: "unavailable", resultCount: 0, method: "none", sourceTypes: [] });
          setContextPack(null);
        }
      });
    } catch (error) {
      const content = error instanceof Error ? error.message : "请求失败。";
      setMessages([
        ...nextMessages,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `RAG 服务暂时不可用：${content}`,
          createdAt: new Date().toISOString(),
        },
      ]);
      setAnswerStatus("error");
      setCitations([]);
      setRetrieval({ vectorStatus: "unavailable", resultCount: 0, method: "none", sourceTypes: [] });
      setContextPack(null);
    } finally {
      setBusy(false);
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
  }

  return (
    <main className="grid min-h-screen grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)_360px]">
      <AppSidebar messageCount={messages.length} onClear={clearConversation} onExample={setInput} />
      <section className="flex min-h-screen flex-col">
        <TopStatusBar busy={busy} statusText={busy ? "retrieving" : "ready"} />
        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <MessageList messages={messages} answerStatus={answerStatus} retrieval={retrieval} citationCount={citations.length} />
        </div>
        <MessageComposer busy={busy} onChange={setInput} onSubmit={submit} value={input} />
      </section>
      <CitationPanel citations={citations} contextPack={contextPack} retrieval={retrieval} />
    </main>
  );
}

type ChatStreamEvent =
  | {
      type: "delta";
      content: string;
    }
  | {
      type: "done";
      answerStatus: AnswerStatus;
      citations: Citation[];
      retrieval: RetrievalSummary;
      raw?: RagAnswerPayload;
    }
  | {
      type: "error";
      answerStatus: "error";
      content: string;
      error?: string;
    };

async function readChatStream(body: ReadableStream<Uint8Array>, onEvent: (event: ChatStreamEvent) => void) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() || "";

    for (const frame of frames) {
      const line = frame.trim();
      if (!line.startsWith("data: ")) {
        continue;
      }
      onEvent(JSON.parse(line.slice(6)) as ChatStreamEvent);
    }
  }

  if (buffer.trim().startsWith("data: ")) {
    onEvent(JSON.parse(buffer.trim().slice(6)) as ChatStreamEvent);
  }
}
