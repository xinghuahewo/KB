import type { ChatMessage, Citation, RetrievalSummary } from "@/lib/chat-types";

export type StoredConversation = {
  version: 2;
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
    return migrateConversation(JSON.parse(raw) as Partial<StoredConversation> & LegacyConversation);
  } catch {
    return null;
  }
}

type LegacyConversation = {
  id?: string;
  messages?: ChatMessage[];
  citations?: Citation[];
  retrieval?: RetrievalSummary | null;
  updatedAt?: string;
};

function migrateConversation(value: Partial<StoredConversation> & LegacyConversation): StoredConversation | null {
  if (!value.id || !Array.isArray(value.messages) || !value.updatedAt) {
    return null;
  }
  if (value.version === 2) {
    return value as StoredConversation;
  }

  const assistantIndex = value.messages.map((message) => message.role).lastIndexOf("assistant");
  const messages = value.messages.map((message, index) =>
    index === assistantIndex
      ? {
          ...message,
          evidence: {
            citations: value.citations || [],
            retrieval: value.retrieval || null,
            contextPack: null,
          },
        }
      : message,
  );
  return {
    version: 2,
    id: value.id,
    messages,
    citations: [],
    retrieval: null,
    updatedAt: value.updatedAt,
  };
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
