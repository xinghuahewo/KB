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
        <h2 className="mt-1 text-lg font-semibold">本轮证据</h2>
        <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
          {retrieval?.evidenceLabel || "答案会优先依据可追溯资料生成。"}
        </p>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-2 text-xs">
        <Metric label="证据" value={String(citations.length)} />
        <Metric label="来源" value={String(retrieval?.sourceCount ?? retrieval?.sourceTypes.length ?? 0)} />
        <Metric label="相关章节" value={String(retrieval?.contextUnitCount ?? contextUnits(contextPack).length)} />
        <Metric label="状态" value={retrieval?.hasSectionContext ? "已结合上下文" : retrieval?.methodLabel || "待检索"} />
      </div>

      <ContextUnitList contextPack={contextPack} />

      <div className="mt-5 space-y-3">
        <h3 className="text-sm font-semibold">引用</h3>
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
          <summary className="cursor-pointer text-sm font-semibold">开发调试：原始检索记录</summary>
          <pre className="mono mt-3 max-h-72 overflow-auto whitespace-pre-wrap text-xs leading-5 text-[var(--muted)]">
            {JSON.stringify(
              {
                resolved_query_type: contextPack.resolved_query_type,
                token_budget: contextPack.token_budget,
                degraded: contextPack.degraded,
                degraded_reason: contextPack.degraded_reason,
                results: contextPack.results.slice(0, 4),
              },
              null,
              2,
            )}
          </pre>
        </details>
      ) : null}
    </aside>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-[var(--line)] bg-white p-2">
      <div className="text-[var(--muted)]">{label}</div>
      <div className="mt-1 truncate font-semibold">{value}</div>
    </div>
  );
}

function ContextUnitList({ contextPack }: { contextPack?: ContextPack | null }) {
  const units = contextUnits(contextPack);
  if (units.length === 0) {
    return null;
  }

  return (
    <section className="border border-[var(--line)] bg-white p-3">
      <div className="mb-3">
        <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted)]">Context</p>
        <h3 className="mt-1 text-sm font-semibold">相关章节</h3>
      </div>
      <div className="space-y-2">
        {units.slice(0, 4).map((unit, index) => (
          <article className="border border-[var(--line)] bg-[var(--panel)] p-3" key={contextUnitKey(unit, index)}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">{stringValue(unit.parent_section_heading) || `相关章节 ${index + 1}`}</p>
                <p className="mt-1 text-xs leading-5 text-[var(--muted)]">{sectionPath(unit.section_path)}</p>
              </div>
              <span className="shrink-0 border border-[var(--line)] bg-white px-2 py-1 text-xs text-[var(--muted)]">
                {modeLabel(unit.mode)}
              </span>
            </div>
            <div className="mt-3 flex flex-wrap gap-2 text-xs text-[var(--muted)]">
              <span className="border border-[var(--line)] bg-white px-2 py-1">片段 {arrayLength(unit.included_chunk_ids)}</span>
              <span className="border border-[var(--line)] bg-white px-2 py-1">约 {numberValue(unit.estimated_tokens) || "?"} tokens</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function CitationItem({ citation, index }: { citation: Citation; index: number }) {
  const sourceId = stringValue(citation.source_id || citation.sourceId || citation.source_ref);
  const sourceLinkId = stringValue(citation.source_id || citation.sourceId);
  const chunkId = stringValue(citation.chunk_id || citation.chunkId);
  const title = stringValue(citation.title) || `引用 ${index + 1}`;
  const preview = stringValue(citation.content_preview || citation.contentPreview || citation.text);
  const score = typeof citation.score === "number" ? citation.score.toFixed(3) : "";
  const sourceBaseUrl = process.env.NEXT_PUBLIC_BGP_RAG_BASE_URL?.replace(/\/+$/, "") || "";

  return (
    <article className="border border-[var(--line)] bg-white p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold">{title}</h3>
          <p className="mono mt-1 break-all text-xs text-[var(--muted)]">{chunkId || "chunk unknown"}</p>
        </div>
        {sourceLinkId ? (
          <a
            className="inline-flex h-8 w-8 shrink-0 items-center justify-center border border-[var(--line)] hover:bg-[var(--bg)]"
            href={`${sourceBaseUrl}/sources/${sourceLinkId}`}
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

function contextUnits(contextPack?: ContextPack | null) {
  const units = contextPack?.context_units || contextPack?.contextUnits || [];
  return Array.isArray(units) ? units.filter((unit): unit is Record<string, unknown> => Boolean(unit && typeof unit === "object")) : [];
}

function contextUnitKey(unit: Record<string, unknown>, index: number) {
  return `${stringValue(unit.context_id) || stringValue(unit.parent_section_id) || "context"}-${index}`;
}

function sectionPath(value: unknown) {
  if (Array.isArray(value)) {
    return value.filter((item): item is string => typeof item === "string" && item.length > 0).join(" / ") || "章节路径未记录";
  }
  if (typeof value === "string" && value) {
    return value;
  }
  return "章节路径未记录";
}

function modeLabel(value: unknown) {
  const mode = stringValue(value);
  if (mode === "full_section") return "完整章节";
  if (mode === "parent_span") return "章节片段";
  if (mode === "summary") return "章节摘要";
  return "精确片段";
}

function arrayLength(value: unknown) {
  return Array.isArray(value) ? value.length : 0;
}

function numberValue(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}
