import { describe, expect, it } from "vitest";

import { completeAssistantMessage, createPendingAssistantMessage } from "@/lib/conversation";

describe("回答轮次状态", () => {
  it("将检索结果写入对应的 assistant 消息而不影响其他轮次", () => {
    const first = completeAssistantMessage(
      createPendingAssistantMessage("a1", "2026-07-10T00:00:00.000Z"),
      "第一轮回答",
      "answered",
      [{ source_ref: "rfc-7908#2" }],
      { vectorStatus: "complete", resultCount: 1, method: "hybrid", sourceTypes: [], sourceCount: 1 },
      null,
    );
    const second = createPendingAssistantMessage("a2", "2026-07-10T00:01:00.000Z");

    expect(first.evidence?.citations).toHaveLength(1);
    expect(second.evidence).toEqual({ citations: [], retrieval: null, contextPack: null });
    expect(second.answerStatus).toBe("pending");
  });
});
