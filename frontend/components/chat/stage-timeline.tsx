"use client";

import { Check, Circle, LoaderCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import type { AnswerTiming, AssistantAnswerStatus, StageProgress } from "@/lib/chat-types";


const STAGE_LABEL: Record<string, string> = {
  accepted: "已接收",
  retrieval: "候选召回",
  rerank: "证据精排",
  context_pack: "上下文组装",
  generation: "答案生成",
  persistence: "保存会话",
};

type Props = {
  stages?: StageProgress[];
  timings?: AnswerTiming | null;
  status?: AssistantAnswerStatus;
  streamMode?: "streaming" | "buffered";
};

export function StageTimeline({ stages = [], timings, status, streamMode }: Props) {
  const active = [...stages].reverse().find((stage) => stage.status === "started");
  const [now, setNow] = useState(() => performanceNow());
  useEffect(() => {
    if (!active || status !== "pending") return;
    const timer = window.setInterval(() => setNow(performanceNow()), 100);
    return () => window.clearInterval(timer);
  }, [active, status]);
  const stageRows = useMemo(() => collapseStages(stages), [stages]);

  if (status !== "pending" && timings) {
    return (
      <div className="mt-3 border-t border-dashed border-[var(--line)] pt-3 text-xs text-[var(--muted)]">
        <div className="flex flex-wrap gap-x-3 gap-y-1">
          <Timing label="召回" value={timings.retrieval_ms} />
          <Timing label="精排" value={timings.rerank_ms} />
          <Timing label="首字" value={timings.time_to_first_answer_ms} />
          <Timing label="生成" value={timings.generation_ms} />
          <Timing label="总计" value={timings.total_ms} strong />
        </div>
        {streamMode === "buffered" ? (
          <p className="mt-2 text-[var(--amber)]">当前 Provider 以完整快照返回，并非真实逐字流式。</p>
        ) : null}
      </div>
    );
  }

  if (!stageRows.length) return null;
  return (
    <div className="mb-4 border border-[var(--line)] bg-[#f7f3e9] px-3 py-3">
      <div className="flex flex-wrap gap-x-4 gap-y-2">
        {stageRows.map((stage) => {
          const running = stage.status === "started";
          const elapsed = running && stage.startedAt ? Math.max(0, now - stage.startedAt) : stage.durationMs;
          const Icon = running ? LoaderCircle : stage.status === "complete" ? Check : Circle;
          return (
            <span className="inline-flex items-center gap-1.5 text-xs" key={stage.stage}>
              <Icon className={`h-3.5 w-3.5 ${running ? "animate-spin text-[var(--amber)]" : "text-[var(--green)]"}`} aria-hidden="true" />
              <span>{STAGE_LABEL[stage.stage] || stage.message || stage.stage}</span>
              {elapsed !== undefined ? <span className="mono text-[var(--muted)]">{formatSeconds(elapsed)}</span> : null}
            </span>
          );
        })}
      </div>
      <p aria-live="polite" className="sr-only">
        {active ? `${STAGE_LABEL[active.stage] || active.message || active.stage}进行中` : status === "pending" ? "正在生成回答" : "回答完成"}
      </p>
    </div>
  );
}

function Timing({ label, value, strong = false }: { label: string; value?: number | null; strong?: boolean }) {
  if (typeof value !== "number") return null;
  return <span className={strong ? "font-semibold text-[var(--ink)]" : ""}>{label} {formatSeconds(value)}</span>;
}

export function formatSeconds(milliseconds: number) {
  return `${(Math.max(0, milliseconds) / 1000).toFixed(milliseconds < 1000 ? 2 : 1)} 秒`;
}

function collapseStages(stages: StageProgress[]) {
  const byStage = new Map<string, StageProgress>();
  for (const stage of stages) byStage.set(stage.stage, stage);
  return Array.from(byStage.values());
}

function performanceNow() {
  return typeof performance === "undefined" ? Date.now() : performance.now();
}
