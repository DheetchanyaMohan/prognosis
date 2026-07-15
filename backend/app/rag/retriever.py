"""Retrieval service.

Retrieves evidence; never generates answers. Independent of LangGraph and
any LLM — this module answers "what's relevant" with scored, typed,
provenance-carrying results, nothing more.

Owns the Chroma client/collection access for the whole app.rag package;
app.rag.ingest imports get_chroma_client / get_or_create_collection from
here rather than opening its own connection.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

from app.rag.embed import Embedder, EmbeddingModel
from app.rag.schemas import ChunkMetadata, RetrievedChunk

CHROMA_PERSIST_DIR = Path(__file__).resolve().parents[2] / "data" / "chroma"

KNOWLEDGE_COLLECTION_NAME = "knowledge_docs"
RUN_SUMMARY_COLLECTION_NAME = "run_summaries"

#: Both collections are configured for cosine distance; retrieval scores
#: are reported as 1 - cosine_distance (1.0 = identical, 0.0 = orthogonal).
_COLLECTION_METADATA = {"hnsw:space": "cosine"}


def get_chroma_client(persist_dir: Path = CHROMA_PERSIST_DIR) -> ClientAPI:
    persist_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(persist_dir))


def get_or_create_collection(client: ClientAPI, name: str) -> Collection:
    return client.get_or_create_collection(name=name, metadata=_COLLECTION_METADATA)


def _distance_to_similarity(distance: float) -> float:
    """Converts Chroma's cosine distance (0=identical, 2=opposite) to a
    similarity score (1=identical, -1=opposite), since collections are
    configured with hnsw:space="cosine"."""
    return 1.0 - distance


def _row_to_retrieved_chunk(
    chunk_id: str, text: str, metadata: dict[str, Any], distance: float
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        text=text,
        score=_distance_to_similarity(distance),
        metadata=ChunkMetadata.model_validate(metadata),
    )


class Retriever:
    """Public retrieval interface. Holds one embedding model instance and
    one Chroma client for reuse across many queries — both are expensive
    to construct, so callers should keep one Retriever around rather than
    building a new one per query.
    """

    def __init__(
        self, client: ClientAPI | None = None, embedder: EmbeddingModel | None = None
    ) -> None:
        self._client = client or get_chroma_client()
        self._embedder: EmbeddingModel = embedder or Embedder()

    def knowledge_collection(self) -> Collection:
        return get_or_create_collection(self._client, KNOWLEDGE_COLLECTION_NAME)

    def run_summary_collection(self) -> Collection:
        return get_or_create_collection(self._client, RUN_SUMMARY_COLLECTION_NAME)

    def retrieve_knowledge(
        self, query: str, top_k: int = 5, metadata_filter: dict[str, Any] | None = None
    ) -> list[RetrievedChunk]:
        """Retrieves the top_k most relevant chunks from the curated
        knowledge base (overfitting, regularization, LR scheduling, etc.)."""
        return self._query(self.knowledge_collection(), query, top_k, metadata_filter)

    def retrieve_similar_runs(
        self, query: str, top_k: int = 5, metadata_filter: dict[str, Any] | None = None
    ) -> list[RetrievedChunk]:
        """Retrieves the top_k most relevant chunks from prior run summaries."""
        return self._query(self.run_summary_collection(), query, top_k, metadata_filter)

    def _query(
        self,
        collection: Collection,
        query: str,
        top_k: int,
        metadata_filter: dict[str, Any] | None,
    ) -> list[RetrievedChunk]:
        if collection.count() == 0:
            return []

        query_embedding = self._embedder.embed_query(query)
        results = collection.query(
            query_embeddings=cast(Any, [query_embedding]),
            n_results=min(top_k, collection.count()),
            where=metadata_filter,
            include=["documents", "metadatas", "distances"],
        )

        # We requested documents/metadatas/distances explicitly above, so
        # these are populated; assert rather than silently indexing an
        # Optional to keep mypy honest about why this is safe.
        assert results["ids"] is not None
        assert results["documents"] is not None
        assert results["metadatas"] is not None
        assert results["distances"] is not None

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        return [
            _row_to_retrieved_chunk(chunk_id, doc or "", dict(meta or {}), dist)
            for chunk_id, doc, meta, dist in zip(ids, documents, metadatas, distances, strict=True)
        ]


@lru_cache
def _default_retriever() -> Retriever:
    return Retriever()


def retrieve_knowledge(
    query: str, top_k: int = 5, metadata_filter: dict[str, Any] | None = None
) -> list[RetrievedChunk]:
    """Module-level convenience wrapping a lazily-created, cached default
    Retriever — the public entrypoint LangGraph tool nodes will call."""
    return _default_retriever().retrieve_knowledge(query, top_k, metadata_filter)


def retrieve_similar_runs(
    query: str, top_k: int = 5, metadata_filter: dict[str, Any] | None = None
) -> list[RetrievedChunk]:
    return _default_retriever().retrieve_similar_runs(query, top_k, metadata_filter)