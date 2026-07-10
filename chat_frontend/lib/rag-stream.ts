import type { RagAnswerPayload } from "@/lib/chat-types";

export type RagStageEvent = {
  type?: "stage";
  stage: string;
  status?: string;
  message?: string;
  [key: string]: unknown;
};

type StreamOptions = {
  endpoint?: string;
  limit?: number;
  timeoutMs?: number;
  fetchImpl?: typeof fetch;
  onStage?: (event: RagStageEvent) => void;
  signal?: AbortSignal;
};

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
  if (options.signal?.aborted) {
    stopForUser();
  }

  try {
    const response = await fetchImpl(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ query, limit: options.limit ?? 8 }),
      signal: controller.signal,
    });
    if (!response.ok) {
      const detail = await response.text().catch(() => "");
      throw new Error(`知识库流式接口返回 ${response.status}${detail ? `：${detail}` : ""}`);
    }
    if (!response.body) {
      throw new Error("知识库流式接口没有返回响应体。");
    }

    return await readSsePayload(response.body, options.onStage);
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error(timedOut ? "RAG 请求超过 120 秒仍未完成，已停止等待。" : "已停止生成。");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
    options.signal?.removeEventListener("abort", stopForUser);
  }
}

async function readSsePayload(body: ReadableStream<Uint8Array>, onStage?: (event: RagStageEvent) => void) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() || "";

    for (const frame of frames) {
      const payload = parseFrame(frame);
      if (!payload) {
        continue;
      }
      if (payload.type === "stage" && typeof payload.stage === "string") {
        onStage?.(payload as RagStageEvent);
        continue;
      }
      if (payload.type === "done" && payload.payload && typeof payload.payload === "object") {
        return payload.payload as RagAnswerPayload;
      }
      if (payload.type === "error") {
        throw new Error(stringValue(payload.message) || stringValue(payload.error) || "RAG 服务暂时不可用。");
      }
    }
  }

  throw new Error("RAG stream ended before a final answer.");
}

function parseFrame(frame: string) {
  const data = frame
    .split("\n")
    .filter((line) => line.startsWith("data: "))
    .map((line) => line.slice(6))
    .join("");
  if (!data) {
    return null;
  }
  return JSON.parse(data) as Record<string, unknown>;
}

function stringValue(value: unknown) {
  return typeof value === "string" ? value : "";
}
