import { AlertTriangle, CheckCircle2, CircleHelp, ServerCrash } from "lucide-react";

import type { AssistantAnswerStatus, RetrievalSummary } from "@/lib/chat-types";

type Props = {
  status: AssistantAnswerStatus;
  retrieval?: RetrievalSummary | null;
  citationCount?: number;
};

const STATUS_LABEL: Record<AssistantAnswerStatus, string> = {
  answered: "已回答",
  no_evidence: "证据不足",
  llm_unavailable: "仅显示证据",
  error: "服务异常",
  stopped: "已停止",
  pending: "正在检索",
};

export function RetrievalStatus({ status, retrieval, citationCount = 0 }: Props) {
  const Icon = statusIcon(status);

  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      <span className={`inline-flex items-center gap-1 border px-2 py-1 ${statusClass(status)}`}>
        <Icon className="h-3.5 w-3.5" aria-hidden="true" />
        {STATUS_LABEL[status]}
      </span>
      <span className="border border-[var(--line)] bg-white px-2 py-1 text-[var(--muted)]">证据 {citationCount}</span>
      {retrieval ? (
        <>
          <span className="border border-[var(--line)] bg-white px-2 py-1 text-[var(--muted)]">
            来源 {retrieval.sourceCount ?? retrieval.sourceTypes.length}
          </span>
          <span className="border border-[var(--line)] bg-white px-2 py-1 text-[var(--muted)]">
            {retrieval.hasSectionContext ? "已结合章节上下文" : retrieval.methodLabel || "证据检索"}
          </span>
        </>
      ) : null}
    </div>
  );
}

function statusIcon(status: AssistantAnswerStatus) {
  if (status === "answered") return CheckCircle2;
  if (status === "error") return ServerCrash;
  if (status === "llm_unavailable") return AlertTriangle;
  if (status === "pending") return CircleHelp;
  return CircleHelp;
}

function statusClass(status: AssistantAnswerStatus) {
  if (status === "answered") return "border-emerald-700 bg-emerald-50 text-emerald-800";
  if (status === "no_evidence") return "border-amber-700 bg-amber-50 text-amber-800";
  if (status === "llm_unavailable") return "border-sky-700 bg-sky-50 text-sky-800";
  if (status === "stopped") return "border-amber-700 bg-amber-50 text-amber-800";
  if (status === "pending") return "border-[var(--line-strong)] bg-[var(--bg)] text-[var(--muted)]";
  return "border-red-700 bg-red-50 text-red-800";
}
