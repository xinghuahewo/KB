import { describe, expect, it, vi } from "vitest";

import { POST } from "@/app/api/chat/route";

vi.mock("@/lib/bgp-rag-client", () => ({
  getDefaultBgpRagClient: () => ({
    answerQuestion: vi.fn(async (query: string) => {
      if (query === "no evidence") {
        return {
          query,
          answer: "",
          answer_status: "no_evidence",
          generated: false,
          citations: [],
          context_pack: { results: [], citations: [] },
        };
      }
      if (query === "offline") {
        throw new Error("RAG service returned 503: database unavailable");
      }
      return {
        query,
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
          { evidence_id: "evidence-1", chunk_id: "chunk-1", source_ref: "rfc7908#2" },
          { evidence_id: "evidence-2", chunk_id: "chunk-2", source_ref: "rfc9234#4" },
        ],
        citations: [
          { source_id: "src-1", source_ref: "rfc7908#2", chunk_id: "chunk-1", title: "Route Leak" },
          { source_id: "src-2", source_ref: "rfc9234#4", chunk_id: "chunk-2", title: "OTC" },
        ],
        context_pack: {
          results: [
            { chunk_id: "chunk-1", retrieval_method: "mock_hybrid", score: 0.91 },
            { chunk_id: "chunk-2", retrieval_method: "mock_hybrid", score: 0.89 },
          ],
          citations: ["chunk-1", "chunk-2"],
        },
      };
    }),
  }),
}));

function request(body: unknown) {
  return new Request("http://localhost/api/chat", {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" },
  });
}

describe("POST /api/chat", () => {
  it("extracts the latest user message and returns an assistant message with citations", async () => {
    const response = await POST(
      request({
        messages: [
          { role: "user", content: "old" },
          { role: "assistant", content: "previous" },
          { role: "user", content: "route leak" },
        ],
        options: { limit: 3 },
      }),
    );

    expect(response.status).toBe(200);
    const payload = await response.json();
    expect(payload.message).toMatchObject({
      role: "assistant",
      content: "Route leak 是错误传播路由的事件。",
    });
    expect(payload.answerStatus).toBe("answered");
    expect(payload.citations).toHaveLength(2);
    expect(payload.retrieval.resultCount).toBe(2);
    expect(payload.claims[0].evidence_ids).toEqual(["evidence-1", "evidence-2"]);
    expect(payload.evidence).toHaveLength(2);
    expect(payload.groundingStatus).toBe("validated");
    expect(payload.raw.context_pack.results).toHaveLength(2);
  });

  it("returns a refusal message for no_evidence without fabricating an answer", async () => {
    const response = await POST(request({ messages: [{ role: "user", content: "no evidence" }] }));

    expect(response.status).toBe(200);
    const payload = await response.json();
    expect(payload.answerStatus).toBe("no_evidence");
    expect(payload.message.content).toContain("没有找到足够证据");
    expect(payload.citations).toEqual([]);
  });

  it("returns a clear error payload when the RAG service is unavailable", async () => {
    const response = await POST(request({ messages: [{ role: "user", content: "offline" }] }));

    expect(response.status).toBe(502);
    const payload = await response.json();
    expect(payload.answerStatus).toBe("error");
    expect(payload.message.content).toContain("RAG 服务暂时不可用");
    expect(payload.error).toContain("RAG service returned 503");
  });

  it("rejects requests without a user question", async () => {
    const response = await POST(request({ messages: [{ role: "assistant", content: "hello" }] }));

    expect(response.status).toBe(400);
    const payload = await response.json();
    expect(payload.answerStatus).toBe("error");
  });
});
