import { ExternalLink } from "lucide-react";

import type { Citation, ContextPack, RetrievalSummary } from "@/lib/chat-types";

type Props = {
  citations: Citation[];
  contextPack?: ContextPack | null;
  retrieval?: RetrievalSummary | null;
};

export function CitationPanel({ citations, contextPack, retrieval }: Props) {
  return (
    <aside className="border-l border-[var(--line)] bg-[var(--panel)] p-4 lg:h-screen lg:overflow-y-auto">
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted)]">Evidence</p>
        <h2 className="mt-1 text-lg font-semibold">引用与检索</h2>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-2 text-xs">
        <Metric label="引用" value={String(citations.length)} />
        <Metric label="结果" value={String(retrieval?.resultCount ?? 0)} />
        <Metric label="方法" value={retrieval?.method || "none"} wide />
      </div>

      <div className="space-y-3">
        {citations.length === 0 ? (
          <p className="border border-dashed border-[var(--line-strong)] p-3 text-sm leading-6 text-[var(--muted)]">
            本轮还没有可展示引用。
          </p>
        ) : (
          citations.map((citation, index) => <CitationItem citation={citation} index={index} key={citationKey(citation, index)} />)
        )}
      </div>

      {contextPack?.results?.length ? (
        <details className="mt-5 border border-[var(--line)] bg-white p-3">
          <summary className="cursor-pointer text-sm font-semibold">context pack</summary>
          <pre className="mono mt-3 max-h-72 overflow-auto whitespace-pre-wrap text-xs leading-5 text-[var(--muted)]">
            {JSON.stringify(contextPack.results.slice(0, 4), null, 2)}
          </pre>
        </details>
      ) : null}
    </aside>
  );
}

function Metric({ label, value, wide = false }: { label: string; value: string; wide?: boolean }) {
  return (
    <div className={`border border-[var(--line)] bg-white p-2 ${wide ? "col-span-2" : ""}`}>
      <div className="text-[var(--muted)]">{label}</div>
      <div className="mt-1 truncate font-semibold">{value}</div>
    </div>
  );
}

function CitationItem({ citation, index }: { citation: Citation; index: number }) {
  const sourceId = stringValue(citation.source_id || citation.sourceId || citation.source_ref);
  const chunkId = stringValue(citation.chunk_id || citation.chunkId);
  const title = stringValue(citation.title) || `引用 ${index + 1}`;
  const preview = stringValue(citation.content_preview || citation.contentPreview || citation.text);
  const score = typeof citation.score === "number" ? citation.score.toFixed(3) : "";

  return (
    <article className="border border-[var(--line)] bg-white p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold">{title}</h3>
          <p className="mono mt-1 break-all text-xs text-[var(--muted)]">{chunkId || "chunk unknown"}</p>
        </div>
        {sourceId ? (
          <a
            className="inline-flex h-8 w-8 shrink-0 items-center justify-center border border-[var(--line)] hover:bg-[var(--bg)]"
            href={`${process.env.BGP_RAG_BASE_URL || "http://127.0.0.1:8000"}/sources/${sourceId}`}
            rel="noreferrer"
            target="_blank"
            title="打开来源"
          >
            <ExternalLink className="h-4 w-4" aria-hidden="true" />
          </a>
        ) : null}
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-xs text-[var(--muted)]">
        {sourceId ? <span className="border border-[var(--line)] px-2 py-1">{sourceId}</span> : null}
        {citation.source_type || citation.sourceType ? (
          <span className="border border-[var(--line)] px-2 py-1">{stringValue(citation.source_type || citation.sourceType)}</span>
        ) : null}
        {score ? <span className="border border-[var(--line)] px-2 py-1">score {score}</span> : null}
      </div>
      {preview ? <p className="mt-3 text-sm leading-6 text-[var(--muted)]">{preview}</p> : null}
    </article>
  );
}

function citationKey(citation: Citation, index: number) {
  return `${citation.chunk_id || citation.chunkId || citation.source_id || citation.sourceId || "citation"}-${index}`;
}

function stringValue(value: unknown) {
  return typeof value === "string" ? value : "";
}
