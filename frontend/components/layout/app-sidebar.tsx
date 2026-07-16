"use client";

import { History, LoaderCircle, MessageSquareText, Plus, Trash2, X } from "lucide-react";
import { useState } from "react";

import { ExamplePrompts } from "@/components/chat/example-prompts";
import type { ConversationSummary } from "@/lib/chat-types";


type Props = {
  conversations: ConversationSummary[];
  activeConversationId?: string;
  loading?: boolean;
  nextCursor?: string | null;
  onNew: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onLoadMore?: () => void;
  onExample: (prompt: string) => void;
  className?: string;
  onClose?: () => void;
};

export function AppSidebar({
  conversations,
  activeConversationId,
  loading = false,
  nextCursor,
  onNew,
  onSelect,
  onDelete,
  onLoadMore,
  onExample,
  className = "",
  onClose,
}: Props) {
  const [confirmingId, setConfirmingId] = useState<string>();
  function confirmDelete(id: string) {
    if (confirmingId !== id) {
      setConfirmingId(id);
      window.setTimeout(() => setConfirmingId((current) => current === id ? undefined : current), 4000);
      return;
    }
    onDelete(id);
    setConfirmingId(undefined);
  }

  return (
    <aside aria-label="历史会话" className={`flex min-h-0 flex-col bg-[var(--bg)] ${className}`}>
      <div className="flex items-center justify-between border-b border-[var(--line)] px-4 py-4">
        <div>
          <p className="eyebrow">对话档案</p>
          <p className="mt-1 flex items-center gap-2 text-sm font-semibold"><History className="h-4 w-4 text-[var(--green)]" aria-hidden="true" />历史会话</p>
        </div>
        <div className="flex gap-2">
          <button aria-label="新会话" className="icon-button" onClick={onNew} type="button"><Plus className="h-4 w-4" aria-hidden="true" /></button>
          {onClose ? <button aria-label="关闭会话抽屉" className="icon-button" onClick={onClose} type="button"><X className="h-4 w-4" aria-hidden="true" /></button> : null}
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 py-3">
        {loading && conversations.length === 0 ? (
          <p className="flex items-center gap-2 px-2 py-4 text-sm text-[var(--muted)]"><LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />正在恢复历史会话</p>
        ) : conversations.length === 0 ? (
          <p className="border-l-2 border-[var(--line-strong)] px-3 py-2 text-sm leading-6 text-[var(--muted)]">还没有历史记录。新建会话不会清除以后产生的对话。</p>
        ) : (
          <div className="space-y-1">
            {conversations.map((conversation) => {
              const active = conversation.conversation_id === activeConversationId;
              return (
                <article className={`group grid grid-cols-[1fr_auto] border ${active ? "border-[var(--green)] bg-white" : "border-transparent hover:border-[var(--line)] hover:bg-white/70"}`} key={conversation.conversation_id}>
                  <button className="min-w-0 px-3 py-3 text-left" onClick={() => onSelect(conversation.conversation_id)} type="button">
                    <span className="flex items-start gap-2"><MessageSquareText className={`mt-0.5 h-4 w-4 shrink-0 ${active ? "text-[var(--green)]" : "text-[var(--muted)]"}`} aria-hidden="true" /><span className="line-clamp-2 text-sm font-medium leading-5">{conversation.title}</span></span>
                    <span className="mt-2 block pl-6 text-[11px] text-[var(--muted)]">{conversation.message_count} 条消息 · {formatUpdatedAt(conversation.updated_at)}</span>
                  </button>
                  <button
                    aria-label={confirmingId === conversation.conversation_id ? `确认删除：${conversation.title}` : `删除会话：${conversation.title}`}
                    className={`m-2 h-9 w-9 self-center border text-xs ${confirmingId === conversation.conversation_id ? "border-[var(--red)] bg-red-50 text-[var(--red)]" : "border-transparent text-[var(--muted)] opacity-60 hover:border-[var(--line)] group-hover:opacity-100"}`}
                    onClick={() => confirmDelete(conversation.conversation_id)}
                    type="button"
                  >
                    <Trash2 className="mx-auto h-4 w-4" aria-hidden="true" />
                  </button>
                </article>
              );
            })}
          </div>
        )}
        {nextCursor && onLoadMore ? <button className="mt-3 min-h-10 w-full border border-[var(--line)] bg-white text-xs font-semibold hover:border-[var(--green)]" disabled={loading} onClick={onLoadMore} type="button">加载更早会话</button> : null}
        <div className="mt-7 border-t border-[var(--line)] pt-5">
          <p className="eyebrow mb-3">问题样本</p>
          <ExamplePrompts onPick={onExample} />
        </div>
      </div>
    </aside>
  );
}

function formatUpdatedAt(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "时间未知";
  return new Intl.DateTimeFormat("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(date);
}
