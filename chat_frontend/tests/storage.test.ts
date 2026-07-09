import { afterEach, describe, expect, it, vi } from "vitest";

import { clearStoredConversation, loadStoredConversation, saveStoredConversation } from "@/lib/storage";
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

  it("clears the stored conversation", () => {
    const storage = createMemoryStorage();
    storage.setItem("bgp-chat-conversation", "{}");

    clearStoredConversation(storage);

    expect(loadStoredConversation(storage)).toBeNull();
  });
});
