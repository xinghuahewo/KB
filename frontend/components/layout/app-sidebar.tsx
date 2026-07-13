"use client";

import { Plus, Trash2, X } from "lucide-react";
import { useState } from "react";
import { ExamplePrompts } from "@/components/chat/example-prompts";

type Props = { onClear: () => void; onExample: (prompt: string) => void; messageCount: number; className?: string; onClose?: () => void };

export function AppSidebar({ onClear, onExample, messageCount, className = "", onClose }: Props) {
  const [confirming, setConfirming] = useState(false);
  const clear = () => { if (!confirming) { setConfirming(true); window.setTimeout(() => setConfirming(false), 4000); return; } onClear(); setConfirming(false); };
  return <aside aria-label="会话与示例" className={`bg-[var(--bg)] ${className}`}><div className="flex items-center justify-between border-b border-[var(--line)] px-5 py-4"><div><p className="eyebrow">本地会话</p><p className="mt-1 text-sm font-semibold">{messageCount} 条消息</p></div>{onClose ? <button aria-label="关闭会话抽屉" className="icon-button" onClick={onClose} type="button"><X className="h-4 w-4" aria-hidden="true" /></button> : <button aria-label="新会话" className="icon-button" onClick={clear} type="button"><Plus className="h-4 w-4" aria-hidden="true" /></button>}</div><div className="p-5"><p className="eyebrow mb-3">可从这些问题开始</p><ExamplePrompts onPick={onExample} /><button className="mt-8 inline-flex min-h-11 w-full items-center justify-center gap-2 border border-[var(--line-strong)] bg-[var(--panel)] px-3 py-2 text-sm hover:bg-white" onClick={clear} type="button"><Trash2 className="h-4 w-4" aria-hidden="true" />{confirming ? "再次点击确认清空" : "清空本地会话"}</button></div></aside>;
}
