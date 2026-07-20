"""Retrieval evaluation: precision@k / recall@k against a small set of
hand-labeled queries.

Labeled at the *source document* level (see LabeledQuery.relevant_sources),
not exact chunk_id — so this stays valid as the knowledge base is edited,
re-chunked, or grown. A query's ground truth is "which documents should
show up", not "which exact chunk", which is what "reusable as the corpus
grows" requires.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.rag.schemas import RetrievedChunk

FIXTURES_PATH = Path(__file__).resolve().parent / "fixtures" / "knowledge_retrieval_queries.json"

RetrieveFn = Callable[[str, int], list[RetrievedChunk]]


class LabeledQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    relevant_sources: list[str] = Field(
        description="Source document names (ChunkMetadata.source) considered relevant to this query"
    )


class QueryEvalResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    k: int
    precision_at_k: float
    recall_at_k: float
    retrieved_sources: list[str]
    relevant_sources: list[str]


class RetrievalEvalReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    k: int
    num_queries: int
    mean_precision_at_k: float
    mean_recall_at_k: float
    per_query: list[QueryEvalResult]


def load_labeled_queries(path: Path = FIXTURES_PATH) -> list[LabeledQuery]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [LabeledQuery.model_validate(item) for item in raw]


def _precision_recall_at_k(
    retrieved_sources: list[str], relevant_sources: set[str], k: int
) -> tuple[float, float]:
    top_k = retrieved_sources[:k]
    hits = sum(1 for s in top_k if s in relevant_sources)
    precision = hits / len(top_k) if top_k else 0.0
    recall = hits / len(relevant_sources) if relevant_sources else 0.0
    return precision, recall


def evaluate_retrieval(
    retrieve_fn: RetrieveFn,
    queries: list[LabeledQuery] | None = None,
    k: int = 3,
) -> RetrievalEvalReport:
    """Runs every labeled query through `retrieve_fn(query, k)` and scores
    precision@k / recall@k against each query's `relevant_sources`.

    `retrieve_fn` is injected rather than hardcoding
    app.rag.retrieve_knowledge, so this evaluator can be pointed at any
    retrieval function with the same (query, k) -> list[RetrievedChunk]
    signature — including a future reranked or hybrid retriever — without
    any change to this module.
    """
    queries = queries if queries is not None else load_labeled_queries()

    per_query: list[QueryEvalResult] = []
    for labeled in queries:
        retrieved = retrieve_fn(labeled.query, k)
        retrieved_sources = [chunk.metadata.source for chunk in retrieved]
        precision, recall = _precision_recall_at_k(
            retrieved_sources, set(labeled.relevant_sources), k
        )
        per_query.append(
            QueryEvalResult(
                query=labeled.query,
                k=k,
                precision_at_k=precision,
                recall_at_k=recall,
                retrieved_sources=retrieved_sources,
                relevant_sources=labeled.relevant_sources,
            )
        )

    mean_precision = sum(r.precision_at_k for r in per_query) / len(per_query) if per_query else 0.0
    mean_recall = sum(r.recall_at_k for r in per_query) / len(per_query) if per_query else 0.0

    return RetrievalEvalReport(
        k=k,
        num_queries=len(per_query),
        mean_precision_at_k=mean_precision,
        mean_recall_at_k=mean_recall,
        per_query=per_query,
    )