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
const ACTIVE_CONVERSATION_KEY = "bgp-chat-active-conversation";
const UNSYNCED_TURNS_KEY = "bgp-chat-unsynced-turns-v1";

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

export function loadActiveConversationId(storage: ConversationStorage | undefined = getBrowserStorage()) {
  return storage?.getItem(ACTIVE_CONVERSATION_KEY) || null;
}

export function saveActiveConversationId(id: string, storage: ConversationStorage | undefined = getBrowserStorage()) {
  storage?.setItem(ACTIVE_CONVERSATION_KEY, id);
}

export type UnsyncedTurn = {
  conversationId: string;
  requestId: string;
  query: string;
  userMessageId: string;
  assistantMessageId: string;
  lastSequence: number;
  createdAt: string;
};

export function loadUnsyncedTurns(storage: ConversationStorage | undefined = getBrowserStorage()): UnsyncedTurn[] {
  if (!storage) return [];
  try {
    const value = JSON.parse(storage.getItem(UNSYNCED_TURNS_KEY) || "[]") as unknown;
    return Array.isArray(value) ? value.filter(isUnsyncedTurn) : [];
  } catch {
    return [];
  }
}

export function saveUnsyncedTurn(turn: UnsyncedTurn, storage: ConversationStorage | undefined = getBrowserStorage()) {
  if (!storage) return;
  const turns = loadUnsyncedTurns(storage).filter((item) => item.requestId !== turn.requestId);
  turns.push(turn);
  storage.setItem(UNSYNCED_TURNS_KEY, JSON.stringify(turns));
}

export function removeUnsyncedTurn(requestId: string, storage: ConversationStorage | undefined = getBrowserStorage()) {
  if (!storage) return;
  const turns = loadUnsyncedTurns(storage).filter((item) => item.requestId !== requestId);
  if (turns.length) storage.setItem(UNSYNCED_TURNS_KEY, JSON.stringify(turns));
  else storage.removeItem(UNSYNCED_TURNS_KEY);
}

function isUnsyncedTurn(value: unknown): value is UnsyncedTurn {
  if (!value || typeof value !== "object") return false;
  const turn = value as Partial<UnsyncedTurn>;
  return Boolean(turn.conversationId && turn.requestId && turn.query && turn.userMessageId && turn.assistantMessageId);
}

function getBrowserStorage() {
  if (typeof window === "undefined") {
    return undefined;
  }
  return window.localStorage;
}
