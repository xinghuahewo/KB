"use client";

import { Send, Square } from "lucide-react";
import { useEffect, useRef } from "react";

type Props = { value: string; busy: boolean; onChange: (value: string) => void; onSubmit: () => void; onStop: () => void };

export function MessageComposer({ value, busy, onChange, onSubmit, onStop }: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  useEffect(() => { const textarea = textareaRef.current; if (textarea) { textarea.style.height = "auto"; textarea.style.height = `${Math.min(textarea.scrollHeight, 176)}px`; } }, [value]);
  return <div className="border-t border-[var(--line)] bg-[var(--bg)] px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3"><div className="mx-auto flex max-w-[820px] gap-2 border border-[var(--line-strong)] bg-[var(--panel)] p-2 shadow-[0_-8px_24px_rgba(54,46,34,0.04)]"><textarea aria-describedby="composer-hint" aria-label="输入 BGP 问题" className="min-h-12 max-h-44 flex-1 resize-none bg-transparent px-2 py-2 text-sm leading-6 outline-none" onChange={(event) => onChange(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); onSubmit(); } }} placeholder="例如：什么是路由泄露？" ref={textareaRef} value={value} />{busy ? <button aria-label="停止生成" className="inline-flex h-12 w-12 shrink-0 items-center justify-center bg-[var(--amber)] text-white" onClick={onStop} type="button"><Square className="h-4 w-4" aria-hidden="true" /></button> : <button aria-label="发送问题" className="inline-flex h-12 w-12 shrink-0 items-center justify-center bg-neutral-950 text-white transition hover:bg-neutral-800 disabled:cursor-not-allowed disabled:bg-neutral-400" disabled={!value.trim()} onClick={onSubmit} type="button"><Send className="h-4 w-4" aria-hidden="true" /></button>}</div><p className="mx-auto mt-2 max-w-[820px] px-1 text-xs text-[var(--muted)]" id="composer-hint">Enter 发送，Shift+Enter 换行</p></div>;
}
