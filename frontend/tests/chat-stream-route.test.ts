import { describe, expect, it, vi } from "vitest";

import { POST } from "@/app/api/chat/stream/route";

vi.mock("@/lib/bgp-rag-client", () => ({
  getDefaultBgpRagClient: () => ({
    answerQuestion: vi.fn(async () => ({
      query: "route leak",
      answer: "Route leak 是错误传播路由的事件。",
      answer_status: "answered",
      generated: true,
      citations: [{ source_ref: "raw/standards/rfc7908.txt#6", chunk_id: "chunk-1", title: "RFC 7908" }],
      context_pack: {
        results: [{ chunk_id: "chunk-1", retrieval_method: "mock_hybrid", score: 0.9 }],
        citations: ["chunk-1"],
      },
    })),
  }),
}));

function request(body: unknown) {
  return new Request("http://localhost/api/chat/stream", {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" },
  });
}

describe("POST /api/chat/stream", () => {
  it("streams assistant text chunks and finishes with traceability metadata", async () => {
    const response = await POST(request({ messages: [{ role: "user", content: "route leak" }] }));

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("text/event-stream");

    const body = await response.text();
    const events = body
      .trim()
      .split("\n\n")
      .map((line) => JSON.parse(line.replace(/^data: /, "")));

    expect(events.some((event) => event.type === "delta" && event.content.length > 0)).toBe(true);
    expect(events.at(-1)).toMatchObject({
      type: "done",
      answerStatus: "answered",
      citations: [{ chunk_id: "chunk-1" }],
      retrieval: { resultCount: 1, method: "mock_hybrid" },
    });
  });
});
