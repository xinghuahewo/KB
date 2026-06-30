import { Plus, Trash2 } from "lucide-react";

import { ExamplePrompts } from "@/components/chat/example-prompts";

type Props = {
  onClear: () => void;
  onExample: (prompt: string) => void;
  messageCount: number;
};

export function AppSidebar({ onClear, onExample, messageCount }: Props) {
  return (
    <aside className="border-r border-[var(--line)] bg-[var(--bg)] p-4 lg:h-screen">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted)]">Session</p>
          <p className="mt-1 text-sm font-semibold">{messageCount} messages</p>
        </div>
        <button
          className="inline-flex h-9 w-9 items-center justify-center border border-[var(--line-strong)] bg-[var(--panel)] hover:bg-white"
          onClick={onClear}
          title="新会话"
          type="button"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>

      <div className="mb-6">
        <p className="mb-2 text-xs uppercase tracking-[0.16em] text-[var(--muted)]">Prompts</p>
        <ExamplePrompts onPick={onExample} />
      </div>

      <button
        className="inline-flex w-full items-center justify-center gap-2 border border-[var(--line-strong)] bg-[var(--panel)] px-3 py-2 text-sm hover:bg-white"
        onClick={onClear}
        type="button"
      >
        <Trash2 className="h-4 w-4" aria-hidden="true" />
        清空会话
      </button>
    </aside>
  );
}
