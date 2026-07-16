import json
import os
import queue
import threading
import time
from typing import Annotated, Any, Literal, Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field

from bgpkb import paths

from bgpkb.infrastructure import database
from bgpkb.infrastructure.chat_store import ChatRepository, hash_client_id
from bgpkb.retrieval import repository
from bgpkb.retrieval.evidence_detail import evidence_detail

from .chat_models import ConversationCreateRequest, LegacyConversationImportRequest, TurnStreamRequest


Limit = Annotated[int, Query(ge=1, le=100)]
ClientIdHeader = Annotated[str, Header(alias="X-BGP-Client-ID", min_length=32, max_length=160)]


class RagAnswerRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(8, ge=1, le=20)


class RagAnswerResponse(BaseModel):
    """兼容旧字段并声明 grounding v1 的可选扩展。"""

    model_config = ConfigDict(extra="allow")

    query: str
    answer: str
    answer_status: str
    generated: bool = False
    citations: list[dict[str, Any]] = Field(default_factory=list)
    context_pack: dict[str, Any]
    claims: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    grounding_status: str = "unknown"
    model: str = ""
    model_revision: str = ""


_ACTIVE_TURNS: dict[tuple[str, str], threading.Event] = {}
_ACTIVE_TURNS_LOCK = threading.Lock()
_SSE_HEARTBEAT_SECONDS = float(os.environ.get("BGP_SSE_HEARTBEAT_SECONDS", "15"))

app = FastAPI(
    title="BGP 知识库服务",
    description="面向已发布 SQLite 知识库的只读查询服务。",
    version=database.SERVICE_VERSION,
)

BASE_DIR = paths.API_DIR
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def _connect_or_503():
    try:
        return database.connect()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc


def _client_hash(client_id: ClientIdHeader) -> str:
    if not client_id[0].isalnum() or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in client_id):
        raise HTTPException(status_code=422, detail="X-BGP-Client-ID 格式无效")
    return hash_client_id(client_id)


def _chat_repository_or_503() -> ChatRepository:
    try:
        chat_repository = ChatRepository()
        chat_repository.initialize()
        return chat_repository
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"chat history unavailable: {exc}") from exc


@app.get("/health")
def health():
    payload = database.health_status()
    try:
        payload["chat_history"] = ChatRepository().health()
    except Exception as exc:  # 会话库故障不得覆盖发布知识库健康状态
        payload["chat_history"] = {"writable": False, "error": str(exc)}
    return payload


@app.post("/api/v1/conversations", status_code=201)
def api_create_conversation(request: ConversationCreateRequest, client_id: ClientIdHeader):
    return _chat_repository_or_503().create_conversation(_client_hash(client_id), request.title)


@app.get("/api/v1/conversations")
def api_list_conversations(
    client_id: ClientIdHeader,
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
):
    try:
        return _chat_repository_or_503().list_conversations(_client_hash(client_id), limit=limit, cursor=cursor)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="会话分页游标无效") from exc


@app.get("/api/v1/conversations/{conversation_id}")
def api_get_conversation(conversation_id: str, client_id: ClientIdHeader):
    payload = _chat_repository_or_503().get_conversation(_client_hash(client_id), conversation_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="conversation not found")
    return payload


@app.get("/api/v1/conversations/{conversation_id}/messages/{message_id}/evidence/{citation_id}")
def api_get_message_evidence(
    conversation_id: str,
    message_id: str,
    citation_id: str,
    client_id: ClientIdHeader,
    scope: Literal["section", "document"] = "section",
    cursor: int = Query(default=0, ge=0),
    section_limit: int = Query(default=3, ge=1, le=10),
):
    chat_repository = _chat_repository_or_503()
    citation = chat_repository.get_scoped_evidence(
        _client_hash(client_id), conversation_id, message_id, citation_id
    )
    if citation is None:
        raise HTTPException(status_code=404, detail="evidence not found")
    return evidence_detail(citation, scope=scope, cursor=cursor, section_limit=section_limit)


@app.delete("/api/v1/conversations/{conversation_id}", status_code=204)
def api_delete_conversation(conversation_id: str, client_id: ClientIdHeader):
    deleted = _chat_repository_or_503().delete_conversation(_client_hash(client_id), conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="conversation not found")
    return Response(status_code=204)


@app.post("/api/v1/conversations/import", status_code=201)
def api_import_legacy_conversation(request: LegacyConversationImportRequest, client_id: ClientIdHeader):
    messages = [message.model_dump(exclude_none=True) for message in request.messages]
    first_question = next((message["content"] for message in messages if message["role"] == "user"), "历史会话")
    return _chat_repository_or_503().import_legacy(
        _client_hash(client_id),
        import_key=f"local-v2:{request.id}",
        title=request.title or first_question,
        messages=messages,
    )


@app.get("/api/v1/stats")
def api_stats():
    with _connect_or_503() as conn:
        return repository.stats(conn)


@app.get("/api/v1/entities/{entity_id}")
def api_entity(entity_id: str):
    with _connect_or_503() as conn:
        payload = repository.entity(conn, entity_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="entity not found")
    return payload


@app.get("/api/v1/sources/{source_id}")
def api_source(source_id: str):
    with _connect_or_503() as conn:
        payload = repository.source(conn, source_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="source not found")
    return payload


@app.get("/api/v1/entities/{entity_id}/neighbors")
def api_neighbors(entity_id: str):
    with _connect_or_503() as conn:
        return repository.neighbors(conn, entity_id)


@app.get("/api/v1/entities/{entity_id}/evidence")
def api_evidence(entity_id: str):
    with _connect_or_503() as conn:
        return repository.evidence(conn, entity_id)


@app.get("/api/v1/search/entities")
def api_search_entities(q: str, limit: Limit = 10):
    with _connect_or_503() as conn:
        return repository.search_entities(conn, q, limit)


@app.get("/api/v1/search/chunks")
def api_search_chunks(q: str, limit: Limit = 10):
    with _connect_or_503() as conn:
        return repository.search_chunks(conn, q, limit)


@app.get("/api/v1/terms/{term}")
def api_term(term: str, limit: Limit = 10):
    with _connect_or_503() as conn:
        return repository.term(conn, term, limit)


@app.get("/api/v1/actions")
def api_actions(status: str = "", needs_llm: Optional[bool] = None, limit: Limit = 10):
    with _connect_or_503() as conn:
        return repository.actions(conn, status=status, needs_llm=needs_llm, limit=limit)


@app.get("/api/v1/progress")
def api_progress(scope_type: str = "", limit: Limit = 10):
    with _connect_or_503() as conn:
        return repository.progress(conn, scope_type=scope_type, limit=limit)


@app.get("/api/v1/retrieval/search")
def api_retrieval_search(q: str, limit: Limit = 10):
    return repository.retrieval_search(q, limit=limit)


@app.get("/api/v1/retrieval/evidence")
def api_retrieval_evidence(entity_id: str):
    return repository.retrieval_evidence(entity_id)


@app.get("/api/v1/retrieval/context-pack")
def api_retrieval_context_pack(q: str, limit: Limit = 8):
    return repository.retrieval_context_pack(q, limit=limit)


@app.get("/api/v1/hybrid/search")
def api_hybrid_search(q: str, limit: Limit = 20):
    return repository.hybrid_search(q, limit=limit)


@app.get("/api/v1/hybrid/context-pack")
def api_hybrid_context_pack(
    q: str,
    limit: Optional[int] = Query(default=None, ge=1, le=100),
    top_n: Optional[int] = Query(default=None, ge=5, le=8),
    query_type: Literal["fact", "procedure", "policy", "global", "auto"] = "auto",
    token_budget: int = Query(default=6000, ge=1, le=8000),
    require_model: bool = False,
):
    return repository.hybrid_context_pack(
        q,
        limit=limit,
        top_n=top_n,
        query_type=query_type,
        token_budget=token_budget,
        require_model=require_model,
    )


@app.post("/api/v1/rag/answer", response_model=RagAnswerResponse)
def api_rag_answer(request: RagAnswerRequest):
    return repository.rag_answer_payload(request.query, limit=request.limit)


@app.post("/api/v1/rag/answer/stream")
def api_rag_answer_stream(request: RagAnswerRequest):
    return StreamingResponse(
        _rag_answer_event_stream(request),
        media_type="text/event-stream",
        headers={
            "cache-control": "no-store, no-transform",
            "x-accel-buffering": "no",
            "connection": "keep-alive",
        },
    )


def _rag_answer_event_stream(request: RagAnswerRequest):
    def work(emit):
            emit({
                "type": "stage",
                "stage": "accepted",
                "status": "started",
                "message": "问题已提交，正在进入知识库检索",
            })
            payload = repository.rag_answer_stream_payload(request.query, limit=request.limit, progress=emit)
            emit({"type": "done", "payload": payload, "timings": payload.get("timings", {})})

    yield from _event_stream(work)


@app.post("/api/v1/conversations/{conversation_id}/turns/stream")
def api_conversation_turn_stream(
    conversation_id: str,
    request: TurnStreamRequest,
    client_id: ClientIdHeader,
):
    chat_repository = _chat_repository_or_503()
    client_hash = _client_hash(client_id)
    handle = chat_repository.begin_turn(
        client_hash,
        conversation_id,
        request.request_id,
        request.query,
        user_message_id=request.user_message_id,
        assistant_message_id=request.assistant_message_id,
    )
    if handle is None:
        raise HTTPException(status_code=404, detail="conversation not found")
    return StreamingResponse(
        _conversation_turn_event_stream(chat_repository, client_hash, handle, request),
        media_type="text/event-stream",
        headers={
            "cache-control": "no-store, no-transform",
            "x-accel-buffering": "no",
            "connection": "keep-alive",
        },
    )


@app.post("/api/v1/conversations/{conversation_id}/turns/{request_id}/stop")
def api_stop_conversation_turn(conversation_id: str, request_id: str, client_id: ClientIdHeader):
    client_hash = _client_hash(client_id)
    stopped = _chat_repository_or_503().mark_turn_stopped(client_hash, conversation_id, request_id)
    if not stopped:
        raise HTTPException(status_code=404, detail="turn not found")
    with _ACTIVE_TURNS_LOCK:
        event = _ACTIVE_TURNS.get((conversation_id, request_id))
    if event is not None:
        event.set()
    return {"conversation_id": conversation_id, "request_id": request_id, "status": "stopped"}


def _conversation_turn_event_stream(chat_repository, client_hash, handle, request):
    def work(emit):
        if handle.existing:
            _emit_existing_turn_until_terminal(chat_repository, client_hash, handle, emit, request.resume_after_sequence)
            return
        stopped = threading.Event()
        key = (handle.conversation_id, handle.request_id)
        with _ACTIVE_TURNS_LOCK:
            _ACTIVE_TURNS[key] = stopped
        partial: list[str] = []
        last_sequence = 0
        last_checkpoint = 0.0
        started = time.perf_counter_ns()

        def progress(event):
            nonlocal last_sequence, last_checkpoint
            if event.get("type") == "answer_delta":
                partial.append(str(event.get("delta") or ""))
            elif event.get("type") == "citation_delta":
                partial.append(f"[{event.get('label', '')}]")
            last_sequence = emit(event)
            now = time.monotonic()
            if event.get("type") in {"answer_delta", "citation_delta"} and (
                event.get("type") == "citation_delta" or now - last_checkpoint >= 0.25
            ):
                chat_repository.checkpoint_turn(
                    handle.conversation_id,
                    handle.request_id,
                    "".join(partial),
                    last_sequence,
                )
                last_checkpoint = now

        try:
            progress({
                "type": "stage",
                "stage": "accepted",
                "status": "started",
                "message": "本轮问题已记录，正在进入知识库检索",
            })
            payload = repository.rag_answer_stream_payload(
                request.query,
                limit=request.limit,
                progress=progress,
                stop_requested=stopped.is_set,
            )
            if stopped.is_set():
                payload["answer_status"] = "stopped"
                payload["answer"] = "".join(partial) or payload.get("answer", "")
            persistence_started = time.perf_counter_ns()
            timings = dict(payload.get("timings") or {})
            message = chat_repository.finalize_turn(
                handle.conversation_id,
                handle.request_id,
                content=payload.get("answer", ""),
                answer_status=payload.get("answer_status", "error"),
                timings=timings,
                stream_mode=payload.get("stream_mode", "buffered"),
                answer_parts=payload.get("answer_parts", []),
                citations=payload.get("citations", []),
                last_sequence=last_sequence,
                error_code=payload.get("error_code"),
            )
            timings["persistence_ms"] = round((time.perf_counter_ns() - persistence_started) / 1_000_000, 3)
            timings["total_ms"] = round((time.perf_counter_ns() - started) / 1_000_000, 3)
            chat_repository.update_message_timings(handle.assistant_message_id, timings)
            payload.update({
                "conversation_id": handle.conversation_id,
                "request_id": handle.request_id,
                "message_id": handle.assistant_message_id,
                "timings": timings,
            })
            if message is not None:
                message["timings"] = timings
            emit({"type": "done", "payload": payload, "message": message, "timings": timings})
        except Exception as exc:  # 保留已确认的部分正文和准确错误终态
            timings = {"total_ms": round((time.perf_counter_ns() - started) / 1_000_000, 3)}
            message = chat_repository.finalize_turn(
                handle.conversation_id,
                handle.request_id,
                content="".join(partial),
                answer_status="stopped" if stopped.is_set() else "error",
                timings=timings,
                stream_mode="streaming",
                answer_parts=[{"type": "text", "text": "".join(partial)}] if partial else [],
                citations=[],
                last_sequence=last_sequence,
                error_code="stopped" if stopped.is_set() else "stream_error",
            )
            emit({
                "type": "error",
                "status": "stopped" if stopped.is_set() else "error",
                "message": "已停止生成" if stopped.is_set() else "生成中断，已保留部分回答",
                "error": str(exc),
                "partial_answer": "".join(partial),
                "message_snapshot": message,
                "timings": timings,
            })
        finally:
            with _ACTIVE_TURNS_LOCK:
                _ACTIVE_TURNS.pop(key, None)

    yield from _event_stream(work, initial_sequence=request.resume_after_sequence)


def _emit_existing_turn_until_terminal(chat_repository, client_hash, handle, emit, resume_after_sequence):
    last_content = ""
    deadline = time.monotonic() + 125
    while time.monotonic() < deadline:
        turn = chat_repository.get_turn(client_hash, handle.conversation_id, handle.request_id)
        if turn is None:
            emit({"type": "error", "message": "turn not found"})
            return
        message = turn.get("assistant_message") or {}
        content = str(message.get("content") or "")
        if content and content != last_content:
            last_content = content
            emit({
                "type": "answer_snapshot",
                "answer": content,
                "answer_parts": message.get("answer_parts") or [{"type": "text", "text": content}],
                "stream_mode": message.get("stream_mode") or "streaming",
                "recovered": True,
            })
        if turn["status"] != "pending":
            payload = _stored_turn_payload(handle, message)
            emit({"type": "done", "payload": payload, "message": message, "timings": message.get("timings") or {}})
            return
        time.sleep(0.2)
    emit({"type": "error", "message": "恢复等待超时", "partial_answer": last_content})


def _stored_turn_payload(handle, message):
    return {
        "conversation_id": handle.conversation_id,
        "request_id": handle.request_id,
        "message_id": handle.assistant_message_id,
        "query": "",
        "answer": message.get("content", ""),
        "answer_parts": message.get("answer_parts", []),
        "answer_status": message.get("answer_status", handle.status),
        "stream_mode": message.get("stream_mode") or "streaming",
        "citations": message.get("citations", []),
        "context_pack": {},
        "timings": message.get("timings") or {},
    }


class _EventChannel:
    def __init__(self, initial_sequence=0):
        self.events = queue.Queue()
        self.sentinel = object()
        self.sequence = initial_sequence
        self.lock = threading.Lock()
        self.started = time.perf_counter_ns()

    def send(self, payload):
        with self.lock:
            self.sequence += 1
            sequence = self.sequence
        event = dict(payload)
        event["sequence"] = sequence
        event.setdefault("elapsed_ms", round((time.perf_counter_ns() - self.started) / 1_000_000, 3))
        self.events.put(event)
        return sequence


def _event_stream(work, initial_sequence=0):
    channel = _EventChannel(initial_sequence)

    def worker():
        try:
            work(channel.send)
        except Exception as exc:  # pragma: no cover - defensive streaming boundary
            channel.send({
                "type": "error",
                "stage": "error",
                "status": "failed",
                "message": "RAG 服务暂时不可用",
                "error": str(exc),
            })
        finally:
            channel.events.put(channel.sentinel)

    threading.Thread(target=worker, daemon=True).start()
    while True:
        try:
            event = channel.events.get(timeout=_SSE_HEARTBEAT_SECONDS)
        except queue.Empty:
            channel.send({"type": "heartbeat"})
            continue
        if event is channel.sentinel:
            break
        yield _sse(event)


def _sse(payload):
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    with _connect_or_503() as conn:
        payload = repository.stats(conn)
        open_actions = repository.actions(conn, status="open", limit=5)
        progress = repository.progress(conn, scope_type="overall", limit=1)
    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "stats": payload,
            "open_actions": open_actions,
            "progress": progress[0] if progress else None,
        },
    )


@app.get("/search", response_class=HTMLResponse)
def search_page(request: Request, q: str = "", limit: Limit = 10):
    entity_results = []
    chunk_results = []
    if q:
        with _connect_or_503() as conn:
            entity_results = repository.search_entities(conn, q, limit)
            chunk_results = repository.search_chunks(conn, q, limit)
    return templates.TemplateResponse(
        request,
        "search.html",
        {
            "query": q,
            "entity_results": entity_results,
            "chunk_results": chunk_results,
        },
    )


@app.get("/entities/{entity_id}", response_class=HTMLResponse)
def entity_page(request: Request, entity_id: str):
    with _connect_or_503() as conn:
        payload = repository.entity(conn, entity_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="entity not found")
    return templates.TemplateResponse(request, "entity.html", {"entity": payload})


@app.get("/sources/{source_id}", response_class=HTMLResponse)
def source_page(request: Request, source_id: str):
    with _connect_or_503() as conn:
        payload = repository.source(conn, source_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="source not found")
    return templates.TemplateResponse(request, "source.html", {"source": payload})
