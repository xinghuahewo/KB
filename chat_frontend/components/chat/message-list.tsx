import { Clipboard, UserRound } from "lucide-react";

import { RetrievalStatus } from "@/components/chat/retrieval-status";
import type { AnswerStatus, ChatMessage, RetrievalSummary } from "@/lib/chat-types";

type Props = {
  messages: ChatMessage[];
  answerStatus: AnswerStatus | null;
  retrieval: RetrievalSummary | null;
  citationCount: number;
};

export function MessageList({ messages, answerStatus, retrieval, citationCount }: Props) {
  if (messages.length === 0) {
    return (
      <div className="flex min-h-[420px] items-center justify-center border border-dashed border-[var(--line-strong)] bg-[var(--panel)] p-8 text-center">
        <div>
          <p className="text-2xl font-semibold tracking-normal">向 BGP 知识库提问</p>
          <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--muted)]">
            输入一个 BGP、路由安全或互联网事件问题。系统会先查找资料、整理相关章节，再给出带引用的答案。
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {messages.map((message, index) => {
        const isAssistant = message.role === "assistant";
        return (
          <article
            className={`border p-4 shadow-sm ${
              isAssistant ? "border-[var(--line)] bg-[var(--panel)]" : "ml-auto border-neutral-900 bg-neutral-950 text-white"
            } max-w-[min(760px,100%)]`}
            key={message.id || `${message.role}-${index}`}
          >
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-xs uppercase tracking-[0.12em]">
                <UserRound className="h-4 w-4" aria-hidden="true" />
                {message.role}
              </div>
              <button
                className={`inline-flex h-8 w-8 items-center justify-center border ${
                  isAssistant ? "border-[var(--line)] hover:bg-white" : "border-white/25 hover:bg-white/10"
                }`}
                onClick={() => navigator.clipboard?.writeText(message.content)}
                title="复制消息"
                type="button"
              >
                <Clipboard className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>
            <p className="whitespace-pre-wrap text-sm leading-7">{message.content}</p>
            {isAssistant && answerStatus && index === messages.length - 1 ? (
              <div className="mt-4">
                <RetrievalStatus status={answerStatus} retrieval={retrieval} citationCount={citationCount} />
              </div>
            ) : null}
          </article>
        );
      })}
    </div>
  );
}
