import { getServerEnv } from "@/lib/env";
import type { ContextPack, RagAnswerPayload } from "@/lib/chat-types";

type ClientOptions = {
  baseUrl?: string;
  timeoutMs?: number;
  fetchImpl?: typeof fetch;
};

type BgpRagClient = {
  health: () => Promise<unknown>;
  answerQuestion: (query: string, limit?: number) => Promise<RagAnswerPayload>;
  getContextPack: (query: string, limit?: number) => Promise<ContextPack>;
  hybridSearch: (query: string, limit?: number) => Promise<Record<string, unknown>>;
};

const DEFAULT_TIMEOUT_MS = 15_000;

export function createBgpRagClient(options: ClientOptions = {}): BgpRagClient {
  const baseUrl = normalizeBaseUrl(options.baseUrl || getServerEnv().bgpRagBaseUrl);
  const fetchImpl = options.fetchImpl || fetch;
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;

  async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetchImpl(`${baseUrl}${path}`, {
        ...init,
        headers: {
          "content-type": "application/json",
          ...(init.headers || {}),
        },
        signal: controller.signal,
      });

      const payload = await readJsonSafely(response);
      if (!response.ok) {
        const detail = extractErrorDetail(payload);
        throw new Error(`RAG service returned ${response.status}${detail ? `: ${detail}` : ""}`);
      }
      return payload as T;
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error(`RAG service request timed out after ${timeoutMs}ms`);
      }
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  }

  return {
    health() {
      return requestJson("/health", { method: "GET" });
    },
    answerQuestion(query: string, limit = 8) {
      return requestJson<RagAnswerPayload>("/api/v1/rag/answer", {
        method: "POST",
        body: JSON.stringify({ query, limit }),
      });
    },
    getContextPack(query: string, limit = 8) {
      return requestJson<ContextPack>(withQuery("/api/v1/retrieval/context-pack", query, limit), {
        method: "GET",
      });
    },
    hybridSearch(query: string, limit = 8) {
      return requestJson<Record<string, unknown>>(withQuery("/api/v1/retrieval/search", query, limit), {
        method: "GET",
      });
    },
  };
}

export function getDefaultBgpRagClient() {
  return createBgpRagClient();
}

function normalizeBaseUrl(baseUrl: string) {
  return baseUrl.replace(/\/+$/, "");
}

function withQuery(path: string, query: string, limit: number) {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  return `${path}?${params.toString()}`;
}

async function readJsonSafely(response: Response) {
  const text = await response.text();
  if (!text) {
    return {};
  }

  try {
    return JSON.parse(text) as unknown;
  } catch {
    return { detail: text };
  }
}

function extractErrorDetail(payload: unknown) {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    return typeof detail === "string" ? detail : JSON.stringify(detail);
  }
  return "";
}
