"use client";

import { ExternalLink, FileSearch, LoaderCircle, RotateCcw, X } from "lucide-react";
import { useEffect, useRef } from "react";

import { groupCitationsByDocument } from "@/lib/evidence";
import type { ChatMessage, Citation, EvidenceDetail } from "@/lib/chat-types";


type Props = {
  message?: ChatMessage;
  activeCitationId?: string;
  detail?: EvidenceDetail;
  loading?: boolean;
  error?: string;
  className?: string;
  onRetry?: () => void;
  onLoadDocument?: (cursor?: number) => void;
  onClose?: () => void;
};

export function CitationPanel({
  message,
  activeCitationId,
  detail,
  loading = false,
  error,
  className = "",
  onRetry,
  onLoadDocument,
  onClose,
}: Props) {
  const evidence = message?.evidence;
  const citations = evidence?.citations || [];
  const groups = groupCitationsByDocument(citations);
  const retrieval = evidence?.retrieval;
  const targetRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!activeCitationId) return;
    window.setTimeout(() => targetRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 0);
  }, [activeCitationId, detail]);

  return (
    <aside aria-label="本轮证据" className={`flex min-h-0 flex-col bg-[var(--panel)] ${className}`}>
      <header className="flex items-start justify-between gap-3 border-b border-[var(--line)] px-5 py-4">
        <div>
          <p className="eyebrow">本轮证据</p>
          <h2 className="editorial-heading mt-1 text-xl">可追溯资料</h2>
          <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{retrieval?.evidenceLabel || "这轮回答尚未获得可展示的资料。"}</p>
        </div>
        {onClose ? <button aria-label="关闭证据抽屉" className="icon-button" onClick={onClose} type="button"><X className="h-4 w-4" aria-hidden="true" /></button> : null}
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-5 py-4">
        <div className="grid grid-cols-2 gap-px bg-[var(--line)] text-xs">
          <Metric label="文档" value={String(groups.length)} />
          <Metric label="证据片段" value={String(citations.length)} />
          <Metric label="相关章节" value={String(retrieval?.contextUnitCount ?? 0)} />
          <Metric label="检索状态" value={retrieval?.methodLabel || "历史证据快照"} />
        </div>
        <section className="mt-6">
          <h3 className="text-sm font-semibold">引用文档</h3>
          {groups.length === 0 ? (
            <p className="mt-3 border-l-2 border-[var(--line-strong)] pl-3 text-sm leading-6 text-[var(--muted)]">本轮还没有可展示引用。</p>
          ) : (
            <div className="mt-3 space-y-3">
              {groups.map((group) => (
                <CitationGroup
                  activeCitationId={activeCitationId}
                  detail={detail}
                  error={error}
                  group={group}
                  key={group.key}
                  loading={loading}
                  onLoadDocument={onLoadDocument}
                  onRetry={onRetry}
                  targetRef={targetRef}
                />
              ))}
            </div>
          )}
        </section>
      </div>
    </aside>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="min-w-0 bg-white p-3"><div className="text-[var(--muted)]">{label}</div><div className="mt-1 truncate font-semibold text-[var(--ink)]">{value}</div></div>;
}

function CitationGroup({
  group,
  activeCitationId,
  detail,
  loading,
  error,
  onRetry,
  onLoadDocument,
  targetRef,
}: {
  group: ReturnType<typeof groupCitationsByDocument>[number];
  activeCitationId?: string;
  detail?: EvidenceDetail;
  loading: boolean;
  error?: string;
  onRetry?: () => void;
  onLoadDocument?: (cursor?: number) => void;
  targetRef: React.RefObject<HTMLDivElement>;
}) {
  const first = group.citations[0];
  const sourceId = stringValue(first.source_id || first.sourceId);
  const sourceBaseUrl = process.env.NEXT_PUBLIC_BGP_RAG_BASE_URL?.replace(/\/+$/, "") || "";
  const ownsActive = group.citations.some((citation) => citationId(citation) === activeCitationId);
  return (
    <article className={`border bg-white p-4 ${ownsActive ? "border-[var(--green)]" : "border-[var(--line)]"}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0"><h4 className="break-words text-sm font-semibold">{group.title}</h4><p className="mt-1 text-xs text-[var(--muted)]">{group.evidenceCount} 条证据片段</p></div>
        {sourceId ? <a aria-label={`打开外部来源：${group.title}`} className="icon-button shrink-0" href={`${sourceBaseUrl}/sources/${encodeURIComponent(sourceId)}`} rel="noreferrer" target="_blank"><ExternalLink className="h-4 w-4" aria-hidden="true" /></a> : null}
      </div>
      <div className="mt-3 space-y-3">
        {group.citations.map((citation, index) => {
          const active = citationId(citation) === activeCitationId;
          return (
            <div key={citationKey(citation, index)} ref={active ? targetRef : undefined}>
              <EvidenceExcerpt active={active} citation={citation} index={index} />
              {active ? (
                <EvidenceDocument
                  detail={detail}
                  error={error}
                  loading={loading}
                  onLoadDocument={onLoadDocument}
                  onRetry={onRetry}
                />
              ) : null}
            </div>
          );
        })}
      </div>
    </article>
  );
}

function EvidenceExcerpt({ citation, index, active }: { citation: Citation; index: number; active: boolean }) {
  const preview = stringValue(citation.content_preview || citation.contentPreview);
  const section = stringValue(citation.section_heading || citation.section || citation.source_ref).split("#").pop();
  return (
    <div className={`border-l-2 pl-3 ${active ? "border-[var(--green)] bg-emerald-50/50 py-2 pr-2" : "border-[var(--line-strong)]"}`}>
      <p className="text-xs font-medium text-[var(--muted)]">{section || `证据 ${index + 1}`}</p>
      {preview ? <p className="mt-1 break-words text-sm leading-6">{preview}</p> : null}
    </div>
  );
}

function EvidenceDocument({
  detail,
  loading,
  error,
  onRetry,
  onLoadDocument,
}: {
  detail?: EvidenceDetail;
  loading: boolean;
  error?: string;
  onRetry?: () => void;
  onLoadDocument?: (cursor?: number) => void;
}) {
  if (loading) return <div className="mt-3 space-y-2 border-t border-dashed border-[var(--line)] pt-3"><p className="flex items-center gap-2 text-xs text-[var(--muted)]"><LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />正在读取相关章节</p><div className="h-3 animate-pulse bg-[var(--bg)]" /><div className="h-3 w-4/5 animate-pulse bg-[var(--bg)]" /></div>;
  if (error || detail?.error) return <div className="mt-3 border border-red-200 bg-red-50 p-3 text-xs text-[var(--red)]"><p>{error || detail?.error}</p>{onRetry ? <button className="mt-2 inline-flex min-h-9 items-center gap-1 font-semibold underline" onClick={onRetry} type="button"><RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />重试加载</button> : null}</div>;
  if (!detail) return null;
  return (
    <div className="mt-3 border-t border-dashed border-[var(--line)] pt-3">
      {detail.release_mismatch ? <p className="mb-3 border border-amber-300 bg-amber-50 p-2 text-xs text-[var(--amber)]">该证据生成于 {detail.snapshot_release_id}，当前知识库为 {detail.current_release_id}。以下优先保留历史快照。</p> : null}
      {detail.complete_sentence ? <blockquote className="border-l-2 border-[var(--blue)] pl-3 text-sm leading-6">{detail.complete_sentence}</blockquote> : null}
      {detail.sections.map((section) => (
        <section className="mt-4" key={section.section_id}>
          <h5 className="text-xs font-semibold text-[var(--muted)]">{section.heading}</h5>
          <div className="mt-2 space-y-2">
            {section.chunks.map((chunk) => <p className={`break-words text-sm leading-6 ${chunk.is_highlight ? "bg-[#fff2b8] px-2 py-1" : ""}`} key={chunk.chunk_id}>{chunk.content}</p>)}
          </div>
        </section>
      ))}
      {onLoadDocument ? <button className="mt-4 inline-flex min-h-10 items-center gap-2 border border-[var(--line-strong)] px-3 text-xs font-semibold hover:border-[var(--green)]" onClick={() => onLoadDocument(detail.scope === "document" ? detail.next_cursor ?? undefined : 0)} disabled={detail.scope === "document" && detail.next_cursor == null} type="button"><FileSearch className="h-4 w-4" aria-hidden="true" />{detail.scope === "section" ? "查看完整文档" : detail.next_cursor == null ? "文档已加载完" : "继续加载文档"}</button> : null}
    </div>
  );
}

function citationId(citation: Citation) { return stringValue(citation.citation_id || citation.citationId); }
function citationKey(citation: Citation, index: number) { return `${citationId(citation) || citation.chunk_id || citation.chunkId || "citation"}-${index}`; }
function stringValue(value: unknown) { return typeof value === "string" ? value : ""; }
