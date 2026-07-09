import { describe, expect, it, vi } from "vitest";

import { fetchRagAnswerStream } from "@/lib/rag-stream";

function streamFrom(chunks: string[]) {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
}

describe("fetchRagAnswerStream", () => {
  it("reports progress stages and resolves with the final RAG payload", async () => {
    const stages: string[] = [];
    const fetchImpl = vi.fn(async () =>
      new Response(
        streamFrom([
          'data: {"type":"stage","stage":"retrieval","message":"候选证据召回完成"}\n\n',
          'data: {"type":"done","payload":{"query":"route leak","answer":"ok","answer_status":"answered","citations":[],"context_pack":{"results":[]}}}\n\n',
        ]),
        { status: 200, headers: { "content-type": "text/event-stream" } },
      ),
    ) as unknown as typeof fetch;

    const payload = await fetchRagAnswerStream("route leak", {
      fetchImpl,
      onStage: (event) => stages.push(event.stage),
      timeoutMs: 10_000,
    });

    expect(stages).toEqual(["retrieval"]);
    expect(payload.answer_status).toBe("answered");
    expect(fetchImpl).toHaveBeenCalledWith(
      "/api/v1/rag/answer/stream",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ query: "route leak", limit: 8 }),
      }),
    );
  });

  it("throws a clear error when the stream closes before done", async () => {
    const fetchImpl = vi.fn(async () =>
      new Response(streamFrom(['data: {"type":"stage","stage":"retrieval"}\n\n']), {
        status: 200,
        headers: { "content-type": "text/event-stream" },
      }),
    ) as unknown as typeof fetch;

    await expect(fetchRagAnswerStream("route leak", { fetchImpl, timeoutMs: 10_000 })).rejects.toThrow(
      "RAG stream ended before a final answer",
    );
  });
});
