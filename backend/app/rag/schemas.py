"""Structured types for the RAG subsystem.

Every chunk, retrieval result, and piece of provenance is a Pydantic
model — never a plain dict — so downstream consumers (LangGraph tool
nodes, the eval harness, the frontend) get a typed contract instead of
guessing dict keys against Chroma's raw response shape.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class DocumentSource(StrEnum):
    """Which of the two collections a chunk belongs to."""

    KNOWLEDGE_BASE = "knowledge_base"
    RUN_SUMMARY = "run_summary"


class ChunkMetadata(BaseModel):
    """Provenance for a single chunk. Every retrieved chunk carries this
    back to its caller — nothing is retrieved anonymously."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(
        description="Document identifier, e.g. 'overfitting' or a run_id like 'run_005'"
    )
    source_type: DocumentSource
    section_title: str | None = Field(
        default=None, description="Markdown header this chunk fell under, if any"
    )
    chunk_index: int = Field(description="Position of this chunk within its source document")
    run_id: str | None = Field(default=None, description="Populated only for RUN_SUMMARY chunks")


class Chunk(BaseModel):
    """One chunk of text, prior to embedding/storage."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    text: str
    metadata: ChunkMetadata


class RetrievedChunk(BaseModel):
    """One chunk returned from a retrieval query, with its similarity score."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    text: str
    score: float = Field(description="Cosine similarity, 1.0 = identical, 0.0 = orthogonal")
    metadata: ChunkMetadata