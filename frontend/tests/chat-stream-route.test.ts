import { describe, expect, it, vi } from "vitest";

import { POST } from "@/app/api/chat/stream/route";

vi.mock("@/lib/bgp-rag-client", () => ({
  getDefaultBgpRagClient: () => ({
    answerQuestion: vi.fn(async () => ({
      query: "route leak",
      answer: "Route leak 是错误传播路由的事件。",
      answer_status: "answered",
      generated: true,
      grounding_status: "validated",
      claims: [{
        schema_version: "grounded_claim_v1",
        claim_type: "factual",
        text: "Route leak 是错误传播路由的事件。",
        evidence_ids: ["evidence-1", "evidence-2"],
        confidence: 0.9,
      }],
      evidence: [
        { evidence_id: "evidence-1", chunk_id: "chunk-1", source_ref: "raw/standards/rfc7908.txt#6" },
        { evidence_id: "evidence-2", chunk_id: "chunk-2", source_ref: "raw/standards/rfc9234.txt#4" },
      ],
      citations: [
        { evidence_id: "evidence-1", source_ref: "raw/standards/rfc7908.txt#6", chunk_id: "chunk-1", title: "RFC 7908" },
        { evidence_id: "evidence-2", source_ref: "raw/standards/rfc9234.txt#4", chunk_id: "chunk-2", title: "RFC 9234" },
      ],
      context_pack: {
        results: [
          { chunk_id: "chunk-1", retrieval_method: "mock_hybrid", score: 0.9 },
          { chunk_id: "chunk-2", retrieval_method: "mock_hybrid", score: 0.88 },
        ],
        citations: ["chunk-1", "chunk-2"],
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
      citations: [{ chunk_id: "chunk-1" }, { chunk_id: "chunk-2" }],
      retrieval: { resultCount: 2, method: "mock_hybrid" },
      claims: [{ evidence_ids: ["evidence-1", "evidence-2"] }],
      evidence: [{ evidence_id: "evidence-1" }, { evidence_id: "evidence-2" }],
      groundingStatus: "validated",
    });
  });
});
