import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

describe("对话布局契约", () => {
  it("允许网格中的对话列收缩到移动端视口", () => {
    const source = readFileSync(
      new URL("../components/chat/chat-shell.tsx", import.meta.url),
      "utf8",
    );

    expect(source).toContain(
      '<section aria-label="对话" className="flex min-h-0 min-w-0 flex-col">',
    );
  });
});
