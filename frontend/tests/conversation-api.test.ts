import { describe, expect, it, vi } from "vitest";

import { createConversationApi, messagesFromDetail } from "@/lib/conversation-api";


describe("会话 API 客户端", () => {
  it("为 CRUD 请求携带匿名客户端命名空间并保留服务端排序", async () => {
    const fetchImpl = vi.fn(async (_url: string, init?: RequestInit) => new Response(JSON.stringify({
      items: [
        { conversation_id: "c2", title: "较新", created_at: "a", updated_at: "z", message_count: 2, sync_status: "synced" },
        { conversation_id: "c1", title: "较早", created_at: "a", updated_at: "a", message_count: 1, sync_status: "synced" },
      ],
      next_cursor: null,
    }), { status: 200 })) as unknown as typeof fetch;
    const api = createConversationApi("client-12345678901234567890123456789012", { fetchImpl, baseUrl: "http://kb" });

    const page = await api.list();

    expect(page.items.map((item) => item.conversation_id)).toEqual(["c2", "c1"]);
    expect(fetchImpl).toHaveBeenCalledWith(
      "http://kb/api/v1/conversations?limit=30",
      expect.objectContaining({ headers: expect.objectContaining({ "X-BGP-Client-ID": "client-12345678901234567890123456789012" }) }),
    );
  });

  it("把历史消息恢复为每轮隔离的证据模型", () => {
    const messages = messagesFromDetail({
      conversation_id: "c1",
      title: "会话",
      created_at: "now",
      updated_at: "now",
      message_count: 2,
      sync_status: "synced",
      messages: [
        { message_id: "u1", role: "user", content: "问题", created_at: "now", updated_at: "now" },
        {
          message_id: "a1",
          role: "assistant",
          content: "回答[1]",
          answer_status: "answered",
          answer_parts: [{ type: "text", text: "回答" }, { type: "citation", citation_ids: ["ev_1"], label: "1" }],
          citations: [{ citation_id: "ev_1", chunk_id: "chunk-1", source_id: "rfc1" }],
          created_at: "now",
          updated_at: "now",
        },
      ],
    });

    expect(messages[1].evidence?.citations[0].citation_id).toBe("ev_1");
    expect(messages[1].answerParts?.[1]).toMatchObject({ type: "citation", label: "1" });
    expect(messages[0].evidence).toBeUndefined();
  });
});
