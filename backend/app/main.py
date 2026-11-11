import os
import time
from collections import defaultdict

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.claude_client import ClaudeClient, claude_client_from_env
from app.db import load_entries
from app.embeddings import LocalEmbedder
from app.qa import answer_question
from app.store import VectorStore

load_dotenv()

RATE_LIMIT_PER_MINUTE = 20
RATE_LIMIT_WINDOW_SECONDS = 60.0

STOREFRONT_ORIGIN = os.environ.get("STOREFRONT_ORIGIN", "https://storefront.example.com")
DATABASE_URL = os.environ.get("DATABASE_URL")

_RATE_LIMIT_HITS: dict[str, list[float]] = defaultdict(list)


class RateLimitMiddleware:
    """IP-based rate limit: 20 req/min/IP, no per-request API key (ADR-0004)."""

    def __init__(self, app: ASGIApp, limit: int, window_seconds: float) -> None:
        self.app = app
        self.limit = limit
        self.window_seconds = window_seconds

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        ip = client[0] if client else "unknown"
        now = time.monotonic()
        hits = _RATE_LIMIT_HITS[ip]
        cutoff = now - self.window_seconds
        while hits and hits[0] < cutoff:
            hits.pop(0)

        if len(hits) >= self.limit:
            response = JSONResponse({"detail": "Too many requests"}, status_code=429)
            await response(scope, receive, send)
            return

        hits.append(now)
        await self.app(scope, receive, send)


app = FastAPI()

app.add_middleware(RateLimitMiddleware, limit=RATE_LIMIT_PER_MINUTE, window_seconds=RATE_LIMIT_WINDOW_SECONDS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[STOREFRONT_ORIGIN],
    allow_methods=["POST"],
    allow_headers=["*"],
)

_store = VectorStore()
_embedder = LocalEmbedder()
_claude_client: ClaudeClient = claude_client_from_env()

if DATABASE_URL:
    # The API never talks to Shopify or runs sync itself (#9); `python -m
    # app.sync` is the only writer, run manually or on a schedule (ADR-0002).
    for entry in load_entries(create_engine(DATABASE_URL)):
        _store.add(entry)


def get_store() -> VectorStore:
    return _store


def get_embedder() -> LocalEmbedder:
    return _embedder


def get_claude_client() -> ClaudeClient:
    return _claude_client


class QuestionRequest(BaseModel):
    question: str


@app.post("/api")
def api_answer(
    payload: QuestionRequest,
    store: VectorStore = Depends(get_store),
    embedder: LocalEmbedder = Depends(get_embedder),
    claude_client: ClaudeClient = Depends(get_claude_client),
) -> dict:
    result = answer_question(payload.question, store, embedder, claude_client)
    return {
        "answer": result.answer,
        "citations": [{"id": c.id, "kind": c.kind, "handle": c.handle} for c in result.citations],
        "deflected": result.deflected,
    }
