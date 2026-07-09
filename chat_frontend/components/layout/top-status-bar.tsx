import { Activity, LibraryBig } from "lucide-react";

type Props = {
  busy: boolean;
  statusText: string;
};

export function TopStatusBar({ busy, statusText }: Props) {
  return (
    <header className="flex min-h-14 items-center justify-between border-b border-[var(--line)] bg-[var(--panel)] px-4">
      <div className="flex items-center gap-3">
        <LibraryBig className="h-5 w-5 text-[var(--green)]" aria-hidden="true" />
        <div>
          <h1 className="text-sm font-semibold">BGP 证据问答</h1>
          <p className="text-xs text-[var(--muted)]">先查资料，再组织答案</p>
        </div>
      </div>
      <div className="inline-flex items-center gap-2 border border-[var(--line)] bg-white px-3 py-1 text-xs">
        <Activity className={`h-3.5 w-3.5 ${busy ? "text-[var(--amber)]" : "text-[var(--green)]"}`} aria-hidden="true" />
        {statusText}
      </div>
    </header>
  );
}
