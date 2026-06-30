import { AlertTriangle, CheckCircle2, CircleHelp, ServerCrash } from "lucide-react";

import type { AnswerStatus, RetrievalSummary } from "@/lib/chat-types";

type Props = {
  status: AnswerStatus;
  retrieval?: RetrievalSummary | null;
  citationCount?: number;
};

const STATUS_LABEL: Record<AnswerStatus, string> = {
  answered: "answered",
  no_evidence: "no_evidence",
  llm_unavailable: "llm_unavailable",
  error: "error",
};

export function RetrievalStatus({ status, retrieval, citationCount = 0 }: Props) {
  const Icon = statusIcon(status);

  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      <span className={`inline-flex items-center gap-1 border px-2 py-1 ${statusClass(status)}`}>
        <Icon className="h-3.5 w-3.5" aria-hidden="true" />
        {STATUS_LABEL[status]}
      </span>
      <span className="border border-[var(--line)] bg-white px-2 py-1 text-[var(--muted)]">引用 {citationCount}</span>
      {retrieval ? (
        <>
          <span className="border border-[var(--line)] bg-white px-2 py-1 text-[var(--muted)]">
            结果 {retrieval.resultCount}
          </span>
          <span className="border border-[var(--line)] bg-white px-2 py-1 text-[var(--muted)]">
            {retrieval.method}
          </span>
        </>
      ) : null}
    </div>
  );
}

function statusIcon(status: AnswerStatus) {
  if (status === "answered") return CheckCircle2;
  if (status === "error") return ServerCrash;
  if (status === "llm_unavailable") return AlertTriangle;
  return CircleHelp;
}

function statusClass(status: AnswerStatus) {
  if (status === "answered") return "border-emerald-700 bg-emerald-50 text-emerald-800";
  if (status === "no_evidence") return "border-amber-700 bg-amber-50 text-amber-800";
  if (status === "llm_unavailable") return "border-sky-700 bg-sky-50 text-sky-800";
  return "border-red-700 bg-red-50 text-red-800";
}
