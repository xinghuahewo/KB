import { afterEach, describe, expect, it, vi } from "vitest";

import { createClientId } from "@/lib/client-id";

const originalCrypto = globalThis.crypto;

afterEach(() => {
  Object.defineProperty(globalThis, "crypto", {
    configurable: true,
    value: originalCrypto,
  });
  vi.restoreAllMocks();
});

describe("createClientId", () => {
  it("uses crypto.randomUUID when available", () => {
    Object.defineProperty(globalThis, "crypto", {
      configurable: true,
      value: {
        randomUUID: () => "00000000-0000-4000-8000-000000000000",
      },
    });

    expect(createClientId("message")).toBe("00000000-0000-4000-8000-000000000000");
  });

  it("falls back to getRandomValues when randomUUID is unavailable", () => {
    Object.defineProperty(globalThis, "crypto", {
      configurable: true,
      value: {
        getRandomValues: (bytes: Uint8Array) => {
          bytes.set(Array.from({ length: bytes.length }, (_, index) => index));
          return bytes;
        },
      },
    });

    expect(createClientId("message")).toBe("00010203-0405-4607-8809-0a0b0c0d0e0f");
  });

  it("falls back to timestamp and Math.random when Web Crypto is unavailable", () => {
    Object.defineProperty(globalThis, "crypto", {
      configurable: true,
      value: undefined,
    });
    vi.spyOn(Date, "now").mockReturnValue(1_735_689_600_000);
    vi.spyOn(Math, "random").mockReturnValue(0.123456789);

    expect(createClientId("message")).toMatch(/^message-[a-z0-9]+-[a-z0-9]+$/);
  });
});
