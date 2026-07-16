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

  it("reports a user-stopped request instead of a timeout", async () => {
    const controller = new AbortController();
    const fetchImpl = vi.fn(
      (_url: string, init: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
        }),
    ) as unknown as typeof fetch;

    const request = fetchRagAnswerStream("route leak", { fetchImpl, signal: controller.signal } as never);
    controller.abort();

    await expect(request).rejects.toThrow("已停止生成");
  });

  it("dispatches ordered deltas, citations, heartbeat and snapshot while ignoring duplicate sequence", async () => {
    const received: string[] = [];
    const fetchImpl = vi.fn(async () => new Response(streamFrom([
      'data: {"type":"answer_delta","sequence":1,"delta":"路由"}\n\n',
      'data: {"type":"answer_delta","sequence":1,"delta":"重复"}\n\n',
      'data: {"type":"citation_delta","sequence":2,"citation_ids":["ev_1"],"label":"1"}\n\n',
      'data: {"type":"heartbeat","sequence":3}\n\n',
      'data: {"type":"answer_snapshot","sequence":4,"answer":"路由[1]","answer_parts":[]}\n\n',
      'data: {"type":"done","sequence":5,"payload":{"query":"q","answer":"路由[1]","answer_status":"answered","citations":[],"context_pack":{}}}\n\n',
    ]), { status: 200 })) as unknown as typeof fetch;

    const payload = await fetchRagAnswerStream("q", {
      fetchImpl,
      onAnswerDelta: (event) => received.push(event.delta),
      onCitationDelta: (event) => received.push(`[${event.label}]`),
      onHeartbeat: () => received.push("heartbeat"),
      onAnswerSnapshot: (event) => received.push(event.answer),
    });

    expect(received).toEqual(["路由", "[1]", "heartbeat", "路由[1]"]);
    expect(payload.answer).toBe("路由[1]");
  });

  it("resumes after the previous sequence and exposes partial error snapshots", async () => {
    const fetchImpl = vi.fn(async () => new Response(streamFrom([
      'data: {"type":"answer_delta","sequence":8,"delta":"旧"}\n\n',
      'data: {"type":"answer_delta","sequence":9,"delta":"新"}\n\n',
      'data: {"type":"error","sequence":10,"message":"中断","partial_answer":"部分回答"}\n\n',
    ]), { status: 200 })) as unknown as typeof fetch;
    const deltas: string[] = [];

    const promise = fetchRagAnswerStream("q", {
      fetchImpl,
      initialSequence: 8,
      onAnswerDelta: (event) => deltas.push(event.delta),
    });

    await expect(promise).rejects.toMatchObject({ event: { partial_answer: "部分回答" } });
    expect(deltas).toEqual(["新"]);
  });
});
