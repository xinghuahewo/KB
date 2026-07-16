import type { AnswerPart, ChatMessage } from "@/lib/chat-types";


const INTERNAL_CITATION = /\[\[cite:[^\]]*\]\]/g;
const INTERNAL_URL = /https?:\/\/[^\s)]*\/api\/v1\/conversations\/[^\s)]*/g;

export function serializeMessage(message: ChatMessage) {
  const parts = message.answerParts;
  const text = parts?.length ? serializeParts(parts) : message.content;
  return text
    .replace(INTERNAL_CITATION, "")
    .replace(INTERNAL_URL, "")
    .replace(/[ \t]+\n/g, "\n")
    .trim();
}

function serializeParts(parts: AnswerPart[]) {
  return parts
    .map((part) => (part.type === "text" ? part.text : `[${part.label}]`))
    .join("");
}

type ClipboardLike = { writeText?: (text: string) => Promise<void> };
type DocumentLike = Pick<Document, "body" | "createElement" | "execCommand" | "getSelection">;

export async function copyText(
  text: string,
  clipboard: ClipboardLike | undefined = typeof navigator === "undefined" ? undefined : navigator.clipboard,
  documentSource: DocumentLike | undefined = typeof document === "undefined" ? undefined : document,
) {
  if (clipboard?.writeText) {
    try {
      await clipboard.writeText(text);
      return true;
    } catch {
      // 权限拒绝时继续兼容回退。
    }
  }
  if (!documentSource) return false;
  const textarea = documentSource.createElement("textarea");
  const selection = documentSource.getSelection?.();
  const ranges = selection ? Array.from({ length: selection.rangeCount }, (_, index) => selection.getRangeAt(index)) : [];
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  documentSource.body.appendChild(textarea);
  try {
    textarea.select();
    return documentSource.execCommand("copy") === true;
  } catch {
    return false;
  } finally {
    textarea.remove();
    if (selection) {
      selection.removeAllRanges();
      for (const range of ranges) selection.addRange(range);
    }
  }
}

export async function copyMessage(message: ChatMessage) {
  return copyText(serializeMessage(message));
}
