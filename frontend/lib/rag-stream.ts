import type { AnswerPart, AnswerTiming, RagAnswerPayload } from "@/lib/chat-types";

export type RagStageEvent = {
  type: "stage";
  sequence?: number;
  stage: string;
  status: string;
  message?: string;
  duration_ms?: number;
  elapsed_ms?: number;
  [key: string]: unknown;
};

export type RagAnswerDeltaEvent = {
  type: "answer_delta";
  sequence: number;
  delta: string;
  elapsed_ms?: number;
};

export type RagCitationDeltaEvent = {
  type: "citation_delta";
  sequence: number;
  citation_ids: string[];
  label: string;
  elapsed_ms?: number;
};

export type RagAnswerSnapshotEvent = {
  type: "answer_snapshot";
  sequence: number;
  answer: string;
  answer_parts?: AnswerPart[];
  stream_mode?: "streaming" | "buffered";
  recovered?: boolean;
};

export type RagHeartbeatEvent = { type: "heartbeat"; sequence: number; elapsed_ms?: number };
export type RagDoneEvent = {
  type: "done";
  sequence?: number;
  payload: RagAnswerPayload;
  timings?: AnswerTiming;
  message?: Record<string, unknown>;
};
export type RagErrorEvent = {
  type: "error";
  sequence?: number;
  message?: string;
  error?: string;
  partial_answer?: string;
  timings?: AnswerTiming;
  message_snapshot?: Record<string, unknown>;
  [key: string]: unknown;
};

export type RagStreamEvent =
  | RagStageEvent
  | RagAnswerDeltaEvent
  | RagCitationDeltaEvent
  | RagAnswerSnapshotEvent
  | RagHeartbeatEvent
  | RagDoneEvent
  | RagErrorEvent;

export type StreamOptions = {
  endpoint?: string;
  limit?: number;
  timeoutMs?: number;
  fetchImpl?: typeof fetch;
  headers?: HeadersInit;
  body?: Record<string, unknown>;
  initialSequence?: number;
  onStage?: (event: RagStageEvent) => void;
  onAnswerDelta?: (event: RagAnswerDeltaEvent) => void;
  onCitationDelta?: (event: RagCitationDeltaEvent) => void;
  onAnswerSnapshot?: (event: RagAnswerSnapshotEvent) => void;
  onHeartbeat?: (event: RagHeartbeatEvent) => void;
  onDone?: (event: RagDoneEvent) => void;
  onEvent?: (event: RagStreamEvent) => void;
  signal?: AbortSignal;
};

export class RagStreamError extends Error {
  event?: RagErrorEvent;

  constructor(message: string, event?: RagErrorEvent) {
    super(message);
    this.name = "RagStreamError";
    this.event = event;
  }
}

const DEFAULT_ENDPOINT = "/api/v1/rag/answer/stream";
const DEFAULT_TIMEOUT_MS = 120_000;

export async function fetchRagAnswerStream(query: string, options: StreamOptions = {}) {
  const fetchImpl = options.fetchImpl || fetch;
  const endpoint = options.endpoint || DEFAULT_ENDPOINT;
  const controller = new AbortController();
  let timedOut = false;
  const stopForTimeout = () => {
    timedOut = true;
    controller.abort();
  };
  const timeout = setTimeout(stopForTimeout, options.timeoutMs ?? DEFAULT_TIMEOUT_MS);
  const stopForUser = () => controller.abort();
  options.signal?.addEventListener("abort", stopForUser, { once: true });
  if (options.signal?.aborted) stopForUser();

  try {
    const body = options.body || { query, limit: options.limit ?? 8 };
    const response = await fetchImpl(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json", ...(options.headers || {}) },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (!response.ok) {
      const detail = await response.text().catch(() => "");
      throw new Error(`知识库流式接口返回 ${response.status}${detail ? `：${detail}` : ""}`);
    }
    if (!response.body) throw new Error("知识库流式接口没有返回响应体。");

    return await readSsePayload(response.body, options);
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new RagStreamError(timedOut ? "RAG 请求超过 120 秒仍未完成，已停止等待。" : "已停止生成。");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
    options.signal?.removeEventListener("abort", stopForUser);
  }
}

export async function readSsePayload(body: ReadableStream<Uint8Array>, options: StreamOptions = {}) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let lastSequence = options.initialSequence ?? 0;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    const frames = buffer.split("\n\n");
    buffer = frames.pop() || "";

    for (const frame of frames) {
      const payload = parseFrame(frame);
      if (!payload) continue;
      const sequence = numberValue(payload.sequence);
      if (sequence !== undefined) {
        if (sequence <= lastSequence) continue;
        lastSequence = sequence;
      }
      const event = payload as unknown as RagStreamEvent;
      options.onEvent?.(event);
      if (event.type === "stage" && typeof event.stage === "string") {
        options.onStage?.(event);
        continue;
      }
      if (event.type === "answer_delta" && typeof event.delta === "string") {
        options.onAnswerDelta?.(event);
        continue;
      }
      if (event.type === "citation_delta") {
        options.onCitationDelta?.(event);
        continue;
      }
      if (event.type === "answer_snapshot") {
        options.onAnswerSnapshot?.(event);
        continue;
      }
      if (event.type === "heartbeat") {
        options.onHeartbeat?.(event);
        continue;
      }
      if (event.type === "done" && event.payload && typeof event.payload === "object") {
        options.onDone?.(event);
        return event.payload;
      }
      if (event.type === "error") {
        throw new RagStreamError(
          stringValue(event.message) || stringValue(event.error) || "RAG 服务暂时不可用。",
          event,
        );
      }
    }
  }

  throw new RagStreamError("RAG stream ended before a final answer.");
}

export function parseFrame(frame: string) {
  const data = frame
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trimStart())
    .join("");
  if (!data) return null;
  return JSON.parse(data) as Record<string, unknown>;
}

function stringValue(value: unknown) {
  return typeof value === "string" ? value : "";
}

function numberValue(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}
