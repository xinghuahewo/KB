"""会话历史 API 的输入 DTO。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ConversationCreateRequest(BaseModel):
    title: str = Field(default="新会话", max_length=200)


class TurnStreamRequest(BaseModel):
    request_id: str = Field(..., min_length=16, max_length=160, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]+$")
    query: str = Field(..., min_length=1, max_length=20_000)
    limit: int = Field(default=8, ge=1, le=20)
    user_message_id: str | None = Field(default=None, max_length=160)
    assistant_message_id: str | None = Field(default=None, max_length=160)
    resume_after_sequence: int = Field(default=0, ge=0)


class LegacyMessage(BaseModel):
    id: str | None = Field(default=None, max_length=160)
    role: Literal["user", "assistant", "system"]
    content: str = Field(default="", max_length=100_000)
    createdAt: str | None = None
    answerStatus: str | None = None
    timings: dict[str, Any] | None = None
    streamMode: str | None = None
    answerParts: list[dict[str, Any]] | None = None
    evidence: dict[str, Any] | None = None


class LegacyConversationImportRequest(BaseModel):
    version: Literal[2]
    id: str = Field(..., min_length=1, max_length=160)
    messages: list[LegacyMessage] = Field(default_factory=list, max_length=1000)
    updatedAt: str
    title: str | None = Field(default=None, max_length=200)
