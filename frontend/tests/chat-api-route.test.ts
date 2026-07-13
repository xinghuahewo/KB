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
        citations: [{ source_id: "src-1", chunk_id: "chunk-1", title: "Route Leak" }],
        context_pack: {
          results: [{ chunk_id: "chunk-1", retrieval_method: "mock_hybrid", score: 0.91 }],
          citations: ["chunk-1"],
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
    expect(payload.citations).toHaveLength(1);
    expect(payload.retrieval.resultCount).toBe(1);
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
