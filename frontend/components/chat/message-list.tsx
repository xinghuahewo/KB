import { Clipboard, FileText, UserRound } from "lucide-react";
import type { ReactNode } from "react";

import { RetrievalStatus } from "@/components/chat/retrieval-status";
import { groupCitationsByDocument } from "@/lib/evidence";
import type { ChatMessage } from "@/lib/chat-types";

type Props = { messages: ChatMessage[]; selectedAssistantId?: string; onSelectEvidence: (id: string) => void };

export function MessageList({ messages, selectedAssistantId, onSelectEvidence }: Props) {
  if (messages.length === 0) return <EmptyState />;
  return <div className="mx-auto max-w-[820px] space-y-5 pb-4">{messages.map((message, index) => <MessageCard key={message.id || `${message.role}-${index}`} message={message} selected={message.id === selectedAssistantId} onSelectEvidence={onSelectEvidence} />)}</div>;
}

function EmptyState() { return <div className="mx-auto flex min-h-[420px] max-w-[760px] items-center"><div className="border-l-4 border-[var(--green)] py-5 pl-6"><p className="eyebrow">BGP 知识库</p><h2 className="editorial-heading mt-2 text-3xl">从一条可验证的路由问题开始。</h2><p className="mt-4 max-w-xl text-sm leading-7 text-[var(--muted)]">输入 BGP、路由安全或互联网事件问题。系统会先检索资料，再以可追溯证据组织回答。</p></div></div>; }

function MessageCard({ message, selected, onSelectEvidence }: { message: ChatMessage; selected: boolean; onSelectEvidence: (id: string) => void }) {
  const isAssistant = message.role === "assistant";
  const citations = message.evidence?.citations || [];
  const documents = groupCitationsByDocument(citations).length;
  const copy = async () => { await navigator.clipboard?.writeText(message.content); };
  return <article className={`min-w-0 border ${isAssistant ? "bg-[var(--panel)] border-[var(--line)]" : "ml-auto max-w-[min(620px,100%)] border-neutral-900 bg-neutral-950 text-white"} ${selected ? "ring-1 ring-[var(--green)] ring-offset-2 ring-offset-[var(--bg)]" : ""}`}>
    <header className="flex items-center justify-between gap-3 border-b border-inherit px-4 py-3">
      <div className="flex items-center gap-2 text-xs font-medium"><UserRound className="h-4 w-4" aria-hidden="true" />{isAssistant ? "证据助手" : "你的问题"}</div>
      <button aria-label="复制消息" className="icon-button h-9 w-9 border-current/20 bg-transparent" onClick={copy} type="button"><Clipboard className="h-4 w-4" aria-hidden="true" /></button>
    </header>
    <div className="break-words px-4 py-4 text-sm leading-7"><Markdown content={message.content} /></div>
    {isAssistant && message.answerStatus ? <footer className="border-t border-[var(--line)] px-4 py-3"><RetrievalStatus status={message.answerStatus} retrieval={message.evidence?.retrieval} citationCount={citations.length} />{message.answerStatus !== "pending" ? <button className="mt-3 inline-flex min-h-11 items-center gap-2 text-sm font-semibold text-[var(--green)] underline decoration-[var(--green)] underline-offset-4" onClick={() => message.id && onSelectEvidence(message.id)} type="button"><FileText className="h-4 w-4" aria-hidden="true" />查看 {documents} 个文档 / {citations.length} 条证据</button> : null}</footer> : null}
  </article>;
}

function Markdown({ content }: { content: string }) {
  return <div className="space-y-3">{content.split(/\n{2,}/).map((block, index) => block.split("\n").every((line) => /^[-*]\s+/.test(line)) ? <ul className="list-disc space-y-1 pl-5" key={index}>{block.split("\n").map((line, lineIndex) => <li key={lineIndex}>{inlineMarkdown(line.replace(/^[-*]\s+/, ""))}</li>)}</ul> : <p key={index}>{block.split("\n").map((line, lineIndex) => <span key={lineIndex}>{lineIndex ? <br /> : null}{inlineMarkdown(line)}</span>)}</p>)}</div>;
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
