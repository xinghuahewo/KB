"use client";

import { Check, Clipboard, FileText, Link2, TriangleAlert, UserRound } from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";

import { RetrievalStatus } from "@/components/chat/retrieval-status";
import { StageTimeline } from "@/components/chat/stage-timeline";
import { copyMessage } from "@/lib/copy-message";
import { groupCitationsByDocument } from "@/lib/evidence";
import type { AnswerPart, ChatMessage, Citation } from "@/lib/chat-types";


type Props = {
  messages: ChatMessage[];
  selectedAssistantId?: string;
  activeCitationId?: string;
  onSelectEvidence: (id: string) => void;
  onSelectCitation: (messageId: string, citationId: string) => void;
};

export function MessageList({
  messages,
  selectedAssistantId,
  activeCitationId,
  onSelectEvidence,
  onSelectCitation,
}: Props) {
  if (messages.length === 0) return <EmptyState />;
  return (
    <div className="mx-auto max-w-[820px] space-y-5 pb-4">
      {messages.map((message, index) => (
        <MessageCard
          activeCitationId={message.id === selectedAssistantId ? activeCitationId : undefined}
          key={message.id || `${message.role}-${index}`}
          message={message}
          onSelectCitation={onSelectCitation}
          onSelectEvidence={onSelectEvidence}
          selected={message.id === selectedAssistantId}
        />
      ))}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="mx-auto flex min-h-[420px] max-w-[760px] items-center">
      <div className="border-l-4 border-[var(--green)] py-5 pl-6">
        <p className="eyebrow">BGP 知识库</p>
        <h2 className="editorial-heading mt-2 text-3xl">从一条可验证的路由问题开始。</h2>
        <p className="mt-4 max-w-xl text-sm leading-7 text-[var(--muted)]">输入 BGP、路由安全或互联网事件问题。系统会逐步检索、生成，并把每条引用连接到本轮证据。</p>
      </div>
    </div>
  );
}

function MessageCard({
  message,
  selected,
  activeCitationId,
  onSelectEvidence,
  onSelectCitation,
}: {
  message: ChatMessage;
  selected: boolean;
  activeCitationId?: string;
  onSelectEvidence: (id: string) => void;
  onSelectCitation: (messageId: string, citationId: string) => void;
}) {
  const isAssistant = message.role === "assistant";
  const citations = message.evidence?.citations || [];
  const documents = groupCitationsByDocument(citations).length;
  const [copyState, setCopyState] = useState<"idle" | "success" | "error">("idle");
  const resetTimer = useRef<number>();
  useEffect(() => () => window.clearTimeout(resetTimer.current), []);

  async function copy() {
    const copied = await copyMessage(message);
    setCopyState(copied ? "success" : "error");
    window.clearTimeout(resetTimer.current);
    resetTimer.current = window.setTimeout(() => setCopyState("idle"), 2200);
  }

  return (
    <article
      className={`min-w-0 border ${
        isAssistant
          ? "border-[var(--line)] bg-[var(--panel)]"
          : "ml-auto max-w-[min(620px,100%)] border-neutral-900 bg-neutral-950 text-white"
      } ${selected ? "ring-1 ring-[var(--green)] ring-offset-2 ring-offset-[var(--bg)]" : ""}`}
    >
      <header className="flex items-center justify-between gap-3 border-b border-inherit px-4 py-3">
        <div className="flex items-center gap-2 text-xs font-medium">
          <UserRound className="h-4 w-4" aria-hidden="true" />
          {isAssistant ? "证据助手" : "你的问题"}
          {message.syncStatus && message.syncStatus !== "synced" ? (
            <span className="text-[var(--amber)]">{message.syncStatus === "syncing" ? "同步中" : "尚未同步"}</span>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          <span aria-live="polite" className={`text-xs ${copyState === "error" ? "text-[var(--red)]" : "text-[var(--green)]"}`}>
            {copyState === "success" ? "已复制" : copyState === "error" ? "复制失败" : ""}
          </span>
          <button
            aria-label={copyState === "success" ? "消息已复制" : copyState === "error" ? "复制失败，重试" : "复制消息"}
            className="icon-button h-9 w-9 border-current/20 bg-transparent"
            onClick={copy}
            type="button"
          >
            {copyState === "success" ? <Check className="h-4 w-4" aria-hidden="true" /> : copyState === "error" ? <TriangleAlert className="h-4 w-4" aria-hidden="true" /> : <Clipboard className="h-4 w-4" aria-hidden="true" />}
          </button>
        </div>
      </header>
      <div className="break-words px-4 py-4 text-sm leading-7">
        {isAssistant ? <StageTimeline stages={message.stages} status={message.answerStatus} streamMode={message.streamMode} timings={message.timings} /> : null}
        {message.answerParts?.length ? (
          <StructuredAnswer
            activeCitationId={activeCitationId}
            citations={citations}
            messageId={message.id || ""}
            onSelectCitation={onSelectCitation}
            parts={message.answerParts}
          />
        ) : message.content ? (
          <Markdown content={message.content} />
        ) : message.answerStatus === "pending" ? (
          <p className="flex items-center gap-2 text-[var(--muted)]"><span className="stream-caret" />等待模型首字</p>
        ) : null}
      </div>
      {isAssistant && message.answerStatus ? (
        <footer className="border-t border-[var(--line)] px-4 py-3">
          <RetrievalStatus citationCount={citations.length} retrieval={message.evidence?.retrieval} status={message.answerStatus} />
          {message.answerStatus !== "pending" && message.id ? (
            <button
              className="mt-3 inline-flex min-h-11 items-center gap-2 text-sm font-semibold text-[var(--green)] underline decoration-[var(--green)] underline-offset-4"
              onClick={() => onSelectEvidence(message.id!)}
              type="button"
            >
              <FileText className="h-4 w-4" aria-hidden="true" />
              查看 {documents} 个文档 / {citations.length} 条证据
            </button>
          ) : null}
        </footer>
      ) : null}
    </article>
  );
}

function StructuredAnswer({
  parts,
  citations,
  messageId,
  activeCitationId,
  onSelectCitation,
}: {
  parts: AnswerPart[];
  citations: Citation[];
  messageId: string;
  activeCitationId?: string;
  onSelectCitation: (messageId: string, citationId: string) => void;
}) {
  const citationById = new Map(citations.map((citation) => [citation.citation_id || citation.citationId, citation]));
  return (
    <div className="whitespace-pre-wrap">
      {parts.map((part, index) => {
        if (part.type === "text") return <span key={`text-${index}`}>{inlineMarkdown(part.text)}</span>;
        const citationId = part.citation_ids[0];
        const citation = citationById.get(citationId);
        const title = typeof citation?.title === "string" ? citation.title : "本轮证据";
        return (
          <button
            aria-label={`查看引用 ${part.label}：${title}`}
            aria-pressed={activeCitationId === citationId}
            className={`mx-1 inline-flex min-h-7 items-center gap-1 rounded-full border px-2 align-middle text-xs font-semibold transition ${
              activeCitationId === citationId
                ? "border-[var(--green)] bg-[var(--green)] text-white"
                : "border-[#c9d1cc] bg-[#eef2ef] text-[var(--green)] hover:border-[var(--green)] hover:bg-white"
            }`}
            key={`citation-${index}-${citationId}`}
            onClick={() => onSelectCitation(messageId, citationId)}
            type="button"
          >
            <Link2 className="h-3 w-3" aria-hidden="true" />
            {part.label}
          </button>
        );
      })}
    </div>
  );
}

function Markdown({ content }: { content: string }) {
  return (
    <div className="space-y-3">
      {content.split(/\n{2,}/).map((block, index) =>
        block.split("\n").every((line) => /^[-*]\s+/.test(line)) ? (
          <ul className="list-disc space-y-1 pl-5" key={index}>
            {block.split("\n").map((line, lineIndex) => <li key={lineIndex}>{inlineMarkdown(line.replace(/^[-*]\s+/, ""))}</li>)}
          </ul>
        ) : (
          <p key={index}>{block.split("\n").map((line, lineIndex) => <span key={lineIndex}>{lineIndex ? <br /> : null}{inlineMarkdown(line)}</span>)}</p>
        ),
      )}
    </div>
  );
}

function inlineMarkdown(text: string): ReactNode[] {
  const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\(https?:\/\/[^)]+\))/g);
  return parts.filter(Boolean).map((part, index) => {
    if (part.startsWith("`") && part.endsWith("`")) return <code className="mono rounded bg-black/5 px-1 py-0.5 text-[0.9em]" key={index}>{part.slice(1, -1)}</code>;
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={index}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("*") && part.endsWith("*")) return <em key={index}>{part.slice(1, -1)}</em>;
    const link = part.match(/^\[([^\]]+)\]\((https?:\/\/[^)]+)\)$/);
    if (link) return <a className="text-[var(--blue)] underline underline-offset-2" href={link[2]} key={index} rel="noreferrer" target="_blank">{link[1]}</a>;
    return <span key={index}>{part}</span>;
  });
}
