"""RAG retrieval subsystem.

Retrieves evidence; never generates answers. Independent of LangGraph and
any LLM. Two Chroma collections: knowledge_docs (curated ML documentation)
and run_summaries (built from summary.json + diagnostics.json + selected
config fields for each completed run — never raw logs or metrics CSVs).
"""

from app.rag.embed import Embedder, EmbeddingModel
from app.rag.ingest import ingest_knowledge_documents, ingest_run_summaries
from app.rag.retriever import Retriever, retrieve_knowledge, retrieve_similar_runs
from app.rag.schemas import Chunk, ChunkMetadata, DocumentSource, RetrievedChunk

__all__ = [
    "ingest_knowledge_documents",
    "ingest_run_summaries",
    "retrieve_knowledge",
    "retrieve_similar_runs",
    "Retriever",
    "Embedder",
    "EmbeddingModel",
    "Chunk",
    "ChunkMetadata",
    "DocumentSource",
    "RetrievedChunk",
]