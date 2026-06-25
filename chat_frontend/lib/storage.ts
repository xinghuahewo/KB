import type { ChatMessage, Citation, RetrievalSummary } from "@/lib/chat-types";

export type StoredConversation = {
  id: string;
  messages: ChatMessage[];
  citations: Citation[];
  retrieval: RetrievalSummary | null;
  updatedAt: string;
};

const STORAGE_KEY = "bgp-chat-conversation";

type ConversationStorage = Pick<Storage, "getItem" | "setItem" | "removeItem">;

export function loadStoredConversation(storage: ConversationStorage | undefined = getBrowserStorage()) {
  if (!storage) {
    return null;
  }

  const raw = storage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as StoredConversation;
  } catch {
    return null;
  }
}

export function saveStoredConversation(
  conversation: StoredConversation,
  storage: ConversationStorage | undefined = getBrowserStorage(),
) {
  if (!storage) {
    return;
  }

  storage.setItem(STORAGE_KEY, JSON.stringify(conversation));
}

export function clearStoredConversation(storage: ConversationStorage | undefined = getBrowserStorage()) {
  storage?.removeItem(STORAGE_KEY);
}

function getBrowserStorage() {
  if (typeof window === "undefined") {
    return undefined;
  }
  return window.localStorage;
}
