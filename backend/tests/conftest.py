"""Shared pytest fixtures."""

from __future__ import annotations

import hashlib
import re
from collections.abc import AsyncIterator, Iterator

import chromadb
import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (registers models on Base.metadata)
from app.db.base import Base


@pytest.fixture
def db_session() -> Iterator[Session]:
    # StaticPool (not just check_same_thread=False) is required: the
    # default sqlite pool hands out one connection per thread, and a
    # separate connection to ":memory:" is a separate, empty database.
    # API routes run their DB calls via run_in_threadpool on a worker
    # thread, so without StaticPool that thread would see an empty DB
    # with no tables at all.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
async def api_client(db_session: Session) -> AsyncIterator[httpx.AsyncClient]:
    """An async client for the real FastAPI app, with the DB dependency
    overridden to the isolated in-memory `db_session` fixture rather than
    the real persisted database.

    Uses httpx.ASGITransport directly rather than
    starlette.testclient.TestClient — the TestClient wrapper is broken in
    the currently installed starlette/httpx combination in this
    environment (a `TypeError: 'module' object is not callable` from deep
    inside its portal-based sync wrapper), while calling the ASGI app
    directly through httpx works reliably.
    """
    from app.db.session import get_db
    from app.main import app as fastapi_app

    def _override_get_db() -> Iterator[Session]:
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    fastapi_app.dependency_overrides.clear()


class FakeEmbedder:
    """Deterministic bag-of-words embedder used in place of the real
    bge-small-en-v1.5 model, which requires downloading weights from
    Hugging Face Hub — not reachable from this test environment. Uses
    hashlib (not the builtin hash(), which is randomized per-process) so
    embeddings are stable and reproducible. This has no real semantic
    understanding, but two texts sharing more words do get higher cosine
    similarity than two texts sharing none, which is enough to test
    retrieval ordering, filtering, and scoring mechanics end-to-end.
    """

    DIM = 64

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.DIM
        for word in re.findall(r"\w+", text.lower()):
            bucket = int(hashlib.md5(word.encode()).hexdigest(), 16) % self.DIM
            vector[bucket] += 1.0
        norm = sum(v * v for v in vector) ** 0.5
        return [v / norm for v in vector] if norm > 0 else vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def chroma_client() -> Iterator[chromadb.ClientAPI]:
    """An in-memory Chroma client, reset before and after each test.

    chromadb.EphemeralClient() caches its underlying System by settings,
    so two calls in the same process can silently share state — an
    explicit reset() is what actually gives each test isolation.
    """
    client = chromadb.EphemeralClient(settings=chromadb.config.Settings(allow_reset=True))
    client.reset()
    yield client
    client.reset()