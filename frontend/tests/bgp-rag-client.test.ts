import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createBgpRagClient } from "@/lib/bgp-rag-client";

const originalFetch = global.fetch;

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "content-type": "application/json" },
    ...init,
  });
}

describe("createBgpRagClient", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("posts questions to the RAG answer endpoint and preserves traceability fields", async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse({
        query: "route leak",
        answer: "Route leak 是错误传播路由的事件。",
        answer_status: "answered",
        generated: true,
        model_provider: "deepseek",
        model: "deepseek-chat",
        citations: [{ source_id: "src-1", chunk_id: "chunk-1", title: "Route Leak" }],
        context_pack: { results: [{ chunk_id: "chunk-1" }], citations: ["chunk-1"] },
      }),
    );
    global.fetch = fetchMock;

    const client = createBgpRagClient({ baseUrl: "http://rag.local", timeoutMs: 5000 });
    const payload = await client.answerQuestion("route leak", 3);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://rag.local/api/v1/rag/answer",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ query: "route leak", limit: 3 }),
      }),
    );
    expect(payload.answer_status).toBe("answered");
    expect(payload.citations).toHaveLength(1);
    expect(payload.context_pack.results).toHaveLength(1);
  });

  it("returns no_evidence answers without inventing content", async () => {
    global.fetch = vi.fn(async () =>
      jsonResponse({
        query: "imaginary",
        answer: "",
        answer_status: "no_evidence",
        generated: false,
        model_provider: "none",
        model: "",
        citations: [],
        context_pack: { results: [], citations: [] },
        guardrails: { blocked_reason: "no_citations" },
      }),
    );

    const client = createBgpRagClient({ baseUrl: "http://rag.local" });
    const payload = await client.answerQuestion("imaginary", 2);

    expect(payload.answer_status).toBe("no_evidence");
    expect(payload.answer).toBe("");
    expect(payload.citations).toEqual([]);
  });

  it("raises a readable error when the RAG service is unavailable", async () => {
    global.fetch = vi.fn(async () => jsonResponse({ detail: "database unavailable" }, { status: 503 }));

    const client = createBgpRagClient({ baseUrl: "http://rag.local" });

    await expect(client.answerQuestion("route leak", 3)).rejects.toThrow("RAG service returned 503");
  });

  it("queries context packs and hybrid search using the existing retrieval endpoints", async () => {
    const fetchMock = vi.fn(async (url: string | URL | Request) => {
      const href = String(url);
      if (href.includes("/context-pack")) {
        return jsonResponse({ query: "route leak", results: [], citations: [] });
      }
      return jsonResponse({ query: "route leak", results: [{ chunk_id: "chunk-1" }] });
    });
    global.fetch = fetchMock;

    const client = createBgpRagClient({ baseUrl: "http://rag.local/" });
    await client.getContextPack("route leak", 4);
    await client.hybridSearch("route leak", 4);

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "http://rag.local/api/v1/retrieval/context-pack?q=route+leak&limit=4",
      expect.any(Object),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "http://rag.local/api/v1/retrieval/search?q=route+leak&limit=4",
      expect.any(Object),
    );
  });
});
