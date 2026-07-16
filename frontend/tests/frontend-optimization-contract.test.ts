import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";


describe("前端优化交互契约", () => {
  it("历史侧栏的新建、切换和删除是独立操作", () => {
    const source = readFileSync(new URL("../components/layout/app-sidebar.tsx", import.meta.url), "utf8");
    expect(source).toContain("onNew");
    expect(source).toContain("onSelect");
    expect(source).toContain("onDelete");
    expect(source).toMatch(/再次|确认删除/);
  });

  it("流式回答批量提交、滚离后停止跟随并提供回到最新", () => {
    const source = readFileSync(new URL("../components/chat/chat-shell.tsx", import.meta.url), "utf8");
    expect(source).toContain("window.setTimeout(flushDelta, 40)");
    expect(source).toContain("nearBottomRef");
    expect(source).toContain("回到最新");
    expect(source).toContain("partial_answer");
    expect(source).toContain("stopAck");
    expect(source).toContain('message.id === turn.userMessageId');
    expect(source).toContain('await refreshHistory()');
  });

  it("行内引用以按钮打开所属消息证据并支持移动抽屉", () => {
    const messages = readFileSync(new URL("../components/chat/message-list.tsx", import.meta.url), "utf8");
    const shell = readFileSync(new URL("../components/chat/chat-shell.tsx", import.meta.url), "utf8");
    expect(messages).toContain("查看引用");
    expect(messages).toContain("onSelectCitation(messageId, citationId)");
    expect(shell).toContain("setSelectedAssistantId(messageId)");
    expect(shell).toContain('align="right"');
  });
});
