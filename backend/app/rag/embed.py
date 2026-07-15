"""Local embedding via sentence-transformers (BAAI/bge-small-en-v1.5).

No cloud embedding APIs are used anywhere in this module — embeddings are
computed entirely on-device, once the model weights are cached locally.

BGE models use an asymmetric convention: passages are embedded as-is, but
queries should be prefixed with an instruction string for best retrieval
quality (see the model card). This wrapper applies that convention
automatically so callers never have to remember it or get it wrong.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol, cast

from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSION = 384

#: BGE's recommended instruction prefix for query-side embeddings only.
#: Document/passage embeddings use no prefix.
QUERY_INSTRUCTION_PREFIX = "Represent this sentence for searching relevant passages: "


class EmbeddingModel(Protocol):
    """The interface app.rag depends on. `Embedder` implements this
    against the real local model; tests can substitute a fake
    implementation with the same shape, with no network access needed.
    """

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


@lru_cache
def _get_model() -> SentenceTransformer:
    return cast(SentenceTransformer, SentenceTransformer(EMBEDDING_MODEL_NAME))


class Embedder:
    """Wraps the local embedding model, applying BGE's query/passage
    asymmetry automatically."""

    def __init__(self) -> None:
        self._model = _get_model()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        return [row.tolist() for row in embeddings]

    def embed_query(self, text: str) -> list[float]:
        prefixed = f"{QUERY_INSTRUCTION_PREFIX}{text}"
        embedding = self._model.encode(prefixed, normalize_embeddings=True, convert_to_numpy=True)
        return list(embedding.tolist())