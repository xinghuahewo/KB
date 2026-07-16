export function createClientId(prefix = "id") {
  const cryptoSource = globalThis.crypto;

  if (typeof cryptoSource?.randomUUID === "function") {
    return cryptoSource.randomUUID();
  }

  if (typeof cryptoSource?.getRandomValues === "function") {
    const bytes = new Uint8Array(16);
    cryptoSource.getRandomValues(bytes);
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0"));
    return `${hex.slice(0, 4).join("")}-${hex.slice(4, 6).join("")}-${hex.slice(6, 8).join("")}-${hex
      .slice(8, 10)
      .join("")}-${hex.slice(10, 16).join("")}`;
  }

  const fallbackRandom = Array.from({ length: 4 }, () => Math.random().toString(36).slice(2, 10)).join("");
  return `${prefix}-${Date.now().toString(36)}-${fallbackRandom}`;
}

const CLIENT_ID_KEY = "bgp-chat-client-id";

export function getOrCreateClientId(storage: Pick<Storage, "getItem" | "setItem"> | undefined = browserStorage()) {
  const existing = storage?.getItem(CLIENT_ID_KEY);
  if (existing && existing.length >= 32) return existing;
  const created = createClientId("client");
  storage?.setItem(CLIENT_ID_KEY, created);
  return created;
}

function browserStorage() {
  return typeof window === "undefined" ? undefined : window.localStorage;
}
