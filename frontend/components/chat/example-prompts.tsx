const EXAMPLES = [
  "什么是 BGP 路由泄露？",
  "route leak 和 hijack 有什么区别？",
  "RPKI 如何帮助防止错误路由发布？",
];

export function ExamplePrompts({ onPick }: { onPick: (prompt: string) => void }) {
  return (
    <div className="space-y-2">
      {EXAMPLES.map((prompt) => (
        <button
          className="w-full border border-[var(--line)] bg-[var(--panel)] px-3 py-2 text-left text-sm text-[var(--ink)] transition hover:border-[var(--line-strong)] hover:bg-white"
          key={prompt}
          onClick={() => onPick(prompt)}
          type="button"
        >
          {prompt}
        </button>
      ))}
    </div>
  );
}
