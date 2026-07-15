import json
import queue
import threading
from typing import Annotated, Any, Literal, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field

from bgpkb import paths

from bgpkb.infrastructure import database
from bgpkb.retrieval import repository


Limit = Annotated[int, Query(ge=1, le=100)]


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


@app.get("/health")
def health():
    return database.health_status()


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
        headers={"cache-control": "no-store"},
    )


def _rag_answer_event_stream(request: RagAnswerRequest):
    events = queue.Queue()
    sentinel = object()

    def emit(payload):
        events.put({"type": "stage", **payload})

    def worker():
        try:
            emit({
                "stage": "accepted",
                "status": "started",
                "message": "问题已提交，正在进入知识库检索",
            })
            payload = repository.rag_answer_payload(request.query, limit=request.limit, progress=emit)
            events.put({"type": "done", "payload": payload})
        except Exception as exc:  # pragma: no cover - defensive streaming boundary
            events.put({
                "type": "error",
                "stage": "error",
                "status": "failed",
                "message": "RAG 服务暂时不可用",
                "error": str(exc),
            })
        finally:
            events.put(sentinel)

    threading.Thread(target=worker, daemon=True).start()
    while True:
        event = events.get()
        if event is sentinel:
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
