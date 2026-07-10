import { ExternalLink, X } from "lucide-react";

import { groupCitationsByDocument } from "@/lib/evidence";
import type { ChatMessage, Citation } from "@/lib/chat-types";

type Props = {
  message?: ChatMessage;
  className?: string;
  onClose?: () => void;
};

export function CitationPanel({ message, className = "", onClose }: Props) {
  const evidence = message?.evidence;
  const citations = evidence?.citations || [];
  const groups = groupCitationsByDocument(citations);
  const retrieval = evidence?.retrieval;

  return (
    <aside aria-label="本轮证据" className={`flex min-h-0 flex-col bg-[var(--panel)] ${className}`}>
      <header className="flex items-start justify-between gap-3 border-b border-[var(--line)] px-5 py-4">
        <div>
          <p className="eyebrow">本轮证据</p>
          <h2 className="editorial-heading mt-1 text-xl">可追溯资料</h2>
          <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{retrieval?.evidenceLabel || "这轮回答尚未获得可展示的资料。"}</p>
        </div>
        {onClose ? (
          <button aria-label="关闭证据抽屉" className="icon-button" onClick={onClose} type="button">
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        ) : null}
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-5 py-4">
        <div className="grid grid-cols-2 gap-px bg-[var(--line)] text-xs">
          <Metric label="文档" value={String(groups.length)} />
          <Metric label="证据片段" value={String(citations.length)} />
          <Metric label="相关章节" value={String(retrieval?.contextUnitCount ?? 0)} />
          <Metric label="检索状态" value={retrieval?.methodLabel || "等待检索"} />
        </div>
        <section className="mt-6">
          <h3 className="text-sm font-semibold">引用文档</h3>
          {groups.length === 0 ? (
            <p className="mt-3 border-l-2 border-[var(--line-strong)] pl-3 text-sm leading-6 text-[var(--muted)]">本轮还没有可展示引用。</p>
          ) : (
            <div className="mt-3 space-y-3">
              {groups.map((group) => <CitationGroup key={group.key} group={group} />)}
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

function CitationGroup({ group }: { group: ReturnType<typeof groupCitationsByDocument>[number] }) {
  const first = group.citations[0];
  const sourceId = stringValue(first.source_id || first.sourceId);
  const sourceBaseUrl = process.env.NEXT_PUBLIC_BGP_RAG_BASE_URL?.replace(/\/+$/, "") || "";
  return (
    <article className="border border-[var(--line)] bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0"><h4 className="break-words text-sm font-semibold">{group.title}</h4><p className="mt-1 text-xs text-[var(--muted)]">{group.evidenceCount} 条证据片段</p></div>
        {sourceId ? <a aria-label={`打开来源：${group.title}`} className="icon-button shrink-0" href={`${sourceBaseUrl}/sources/${sourceId}`} rel="noreferrer" target="_blank"><ExternalLink className="h-4 w-4" aria-hidden="true" /></a> : null}
      </div>
      <div className="mt-3 space-y-3">
        {group.citations.map((citation, index) => <EvidenceExcerpt citation={citation} index={index} key={citationKey(citation, index)} />)}
      </div>
    </article>
  );
}

function EvidenceExcerpt({ citation, index }: { citation: Citation; index: number }) {
  const preview = stringValue(citation.content_preview || citation.contentPreview || citation.text);
  const section = stringValue(citation.section || citation.section_heading || citation.source_ref).split("#")[1];
  const chunkId = stringValue(citation.chunk_id || citation.chunkId);
  return <div className="border-l-2 border-[var(--green)] pl-3"><p className="text-xs font-medium text-[var(--muted)]">{section || `证据 ${index + 1}`}</p>{preview ? <p className="mt-1 break-words text-sm leading-6">{preview}</p> : null}<details className="mt-2 text-xs text-[var(--muted)]"><summary>技术详情</summary><p className="mono mt-2 break-all">{chunkId || "未记录片段标识"}</p></details></div>;
}

function citationKey(citation: Citation, index: number) { return `${citation.chunk_id || citation.chunkId || citation.source_ref || "citation"}-${index}`; }
function stringValue(value: unknown) { return typeof value === "string" ? value : ""; }
