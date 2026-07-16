import { afterEach, describe, expect, it, vi } from "vitest";

import {
  clearStoredConversation,
  loadActiveConversationId,
  loadStoredConversation,
  loadUnsyncedTurns,
  removeUnsyncedTurn,
  saveActiveConversationId,
  saveStoredConversation,
  saveUnsyncedTurn,
} from "@/lib/storage";
import type { StoredConversation } from "@/lib/storage";

function createMemoryStorage() {
  const store = new Map<string, string>();
  return {
    getItem: vi.fn((key: string) => store.get(key) ?? null),
    setItem: vi.fn((key: string, value: string) => store.set(key, value)),
    removeItem: vi.fn((key: string) => store.delete(key)),
  };
}

describe("conversation storage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("saves and loads a conversation snapshot", () => {
    const storage = createMemoryStorage();
    const conversation: StoredConversation = {
      version: 2,
      id: "conversation-1",
      messages: [{ role: "user", content: "什么是路由泄露？" }],
      citations: [{ source_id: "src-1", chunk_id: "chunk-1" }],
      retrieval: {
        vectorStatus: "complete",
        resultCount: 1,
        method: "mock_hybrid",
        sourceTypes: ["case"],
      },
      updatedAt: "2026-06-23T00:00:00.000Z",
    };

    saveStoredConversation(conversation, storage);

    expect(loadStoredConversation(storage)).toEqual(conversation);
  });

  it("returns null when stored JSON is damaged", () => {
    const storage = createMemoryStorage();
    storage.setItem("bgp-chat-conversation", "{bad json");

    expect(loadStoredConversation(storage)).toBeNull();
  });

  it("migrates legacy global evidence onto its assistant message and preserves the conversation id", () => {
    const storage = createMemoryStorage();
    storage.setItem(
      "bgp-chat-conversation",
      JSON.stringify({
        id: "legacy-conversation",
        messages: [
          { id: "u1", role: "user", content: "问题" },
          { id: "a1", role: "assistant", content: "回答" },
        ],
        citations: [{ source_ref: "rfc-7908#2", chunk_id: "chunk-1" }],
        retrieval: { vectorStatus: "complete", resultCount: 1, method: "hybrid", sourceTypes: [] },
        updatedAt: "2026-06-23T00:00:00.000Z",
      }),
    );

    const conversation = loadStoredConversation(storage);

    expect(conversation).toMatchObject({ version: 2, id: "legacy-conversation" });
    expect(conversation?.messages[1]).toMatchObject({
      evidence: { citations: [{ source_ref: "rfc-7908#2", chunk_id: "chunk-1" }] },
    });
  });

  it("clears the stored conversation", () => {
    const storage = createMemoryStorage();
    storage.setItem("bgp-chat-conversation", "{}");

    clearStoredConversation(storage);

    expect(loadStoredConversation(storage)).toBeNull();
  });

  it("只在本地保存活动会话标识和可幂等恢复的未同步请求", () => {
    const storage = createMemoryStorage();
    saveActiveConversationId("conversation-2", storage);
    saveUnsyncedTurn({
      conversationId: "conversation-2",
      requestId: "request-1",
      query: "问题",
      userMessageId: "u1",
      assistantMessageId: "a1",
      lastSequence: 8,
      createdAt: "now",
    }, storage);
    saveUnsyncedTurn({
      conversationId: "conversation-2",
      requestId: "request-1",
      query: "问题",
      userMessageId: "u1",
      assistantMessageId: "a1",
      lastSequence: 9,
      createdAt: "now",
    }, storage);

    expect(loadActiveConversationId(storage)).toBe("conversation-2");
    expect(loadUnsyncedTurns(storage)).toHaveLength(1);
    expect(loadUnsyncedTurns(storage)[0].lastSequence).toBe(9);
    removeUnsyncedTurn("request-1", storage);
    expect(loadUnsyncedTurns(storage)).toEqual([]);
  });
});
