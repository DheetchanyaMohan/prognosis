"""Shared pytest fixtures."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterator

import chromadb
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401  (registers models on Base.metadata)
from app.db.base import Base


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


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