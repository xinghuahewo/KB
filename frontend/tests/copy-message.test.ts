import { describe, expect, it, vi } from "vitest";

import { copyMessage, copyText, serializeMessage } from "@/lib/copy-message";


describe("消息复制", () => {
  it("将结构化引用序列化为可读编号且排除内部标识", () => {
    const text = serializeMessage({
      role: "assistant",
      content: "不会使用的兼容正文",
      answerParts: [
        { type: "text", text: "RPKI 使用 ROA" },
        { type: "citation", citation_ids: ["ev_1"], label: "1" },
        { type: "text", text: "。\n\n- 可验证" },
      ],
    });

    expect(text).toBe("RPKI 使用 ROA[1]。\n\n- 可验证");
    expect(text).not.toContain("ev_1");
  });

  it("标准 Clipboard API 成功时不执行回退", async () => {
    const writeText = vi.fn(async () => undefined);
    const createElement = vi.fn();

    await expect(copyText("回答", { writeText }, { createElement } as never)).resolves.toBe(true);
    expect(writeText).toHaveBeenCalledWith("回答");
    expect(createElement).not.toHaveBeenCalled();
  });

  it("权限拒绝或 API 缺失时使用 textarea 回退并清理", async () => {
    const remove = vi.fn();
    const select = vi.fn();
    const textarea = { value: "", style: {}, setAttribute: vi.fn(), select, remove };
    const documentSource = {
      body: { appendChild: vi.fn() },
      createElement: vi.fn(() => textarea),
      execCommand: vi.fn(() => true),
      getSelection: vi.fn(() => null),
    };

    const result = await copyText(
      "回答",
      { writeText: vi.fn(async () => { throw new Error("denied"); }) },
      documentSource as never,
    );

    expect(result).toBe(true);
    expect(select).toHaveBeenCalled();
    expect(documentSource.execCommand).toHaveBeenCalledWith("copy");
    expect(remove).toHaveBeenCalled();
  });

  it("所有路径失败时返回 false 且不改变消息", async () => {
    const message = Object.freeze({ role: "user" as const, content: "原问题" });
    const before = JSON.stringify(message);
    const documentSource = {
      body: { appendChild: vi.fn() },
      createElement: vi.fn(() => ({
        value: "",
        style: {},
        setAttribute: vi.fn(),
        select: vi.fn(),
        remove: vi.fn(),
      })),
      execCommand: vi.fn(() => false),
      getSelection: vi.fn(() => null),
    };

    await expect(copyText("原问题", undefined, documentSource as never)).resolves.toBe(false);
    await copyMessage(message).catch(() => undefined);
    expect(JSON.stringify(message)).toBe(before);
  });
});
