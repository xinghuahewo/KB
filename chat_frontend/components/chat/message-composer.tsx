import { Send, Square } from "lucide-react";

type Props = {
  value: string;
  busy: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
};

export function MessageComposer({ value, busy, onChange, onSubmit }: Props) {
  return (
    <div className="border-t border-[var(--line)] bg-[var(--bg)] p-3">
      <div className="flex gap-2 border border-[var(--line-strong)] bg-[var(--panel)] p-2">
        <textarea
          className="max-h-44 min-h-14 flex-1 resize-none bg-transparent px-2 py-2 text-sm leading-6 outline-none"
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              onSubmit();
            }
          }}
          placeholder="输入问题..."
          value={value}
        />
        <button
          className="inline-flex h-12 w-12 shrink-0 items-center justify-center bg-neutral-950 text-white transition hover:bg-neutral-800 disabled:cursor-not-allowed disabled:bg-neutral-400"
          disabled={busy || !value.trim()}
          onClick={onSubmit}
          title={busy ? "正在生成" : "发送"}
          type="button"
        >
          {busy ? <Square className="h-4 w-4" aria-hidden="true" /> : <Send className="h-4 w-4" aria-hidden="true" />}
        </button>
      </div>
    </div>
  );
}
