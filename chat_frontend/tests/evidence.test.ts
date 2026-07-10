import { describe, expect, it } from "vitest";

import { groupCitationsByDocument } from "@/lib/evidence";

describe("证据归一化", () => {
  it("将同一文档的多个片段归为一个文档来源", () => {
    const groups = groupCitationsByDocument([
      { source_ref: "rfc-7908#section-2", chunk_id: "chunk-1", title: "RFC 7908" },
      { source_ref: "rfc-7908#section-3", chunk_id: "chunk-2", title: "RFC 7908" },
      { source_id: "case-123", chunk_id: "chunk-3", title: "案例" },
    ]);

    expect(groups).toHaveLength(2);
    expect(groups[0]).toMatchObject({ key: "rfc-7908", title: "RFC 7908", evidenceCount: 2 });
    expect(groups[1]).toMatchObject({ key: "case-123", evidenceCount: 1 });
  });
});
