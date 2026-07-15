"""Retrieval tool.

This is the only interface LangGraph nodes use to reach the RAG
subsystem. Wraps app.rag.retrieve_knowledge / retrieve_similar_runs with
no change in behavior — the value here is a stable, tool-layer-owned
import path, so LangGraph code never imports app.rag or touches Chroma
directly. All retrieval logic (chunking, embedding, scoring, filtering)
lives in app.rag; nothing is duplicated here.
"""

from __future__ import annotations

from typing import Any

from app.rag import retrieve_knowledge as _retrieve_knowledge
from app.rag import retrieve_similar_runs as _retrieve_similar_runs
from app.rag.schemas import RetrievedChunk

__all__ = ["retrieve_knowledge", "retrieve_similar_runs"]


def retrieve_knowledge(
    query: str, top_k: int = 5, metadata_filter: dict[str, Any] | None = None
) -> list[RetrievedChunk]:
    """Retrieves the top_k most relevant chunks from the curated ML
    knowledge base (overfitting, regularization, LR scheduling, etc.)."""
    return _retrieve_knowledge(query, top_k=top_k, metadata_filter=metadata_filter)


def retrieve_similar_runs(
    query: str, top_k: int = 5, metadata_filter: dict[str, Any] | None = None
) -> list[RetrievedChunk]:
    """Retrieves the top_k most relevant chunks from prior run summaries."""
    return _retrieve_similar_runs(query, top_k=top_k, metadata_filter=metadata_filter)