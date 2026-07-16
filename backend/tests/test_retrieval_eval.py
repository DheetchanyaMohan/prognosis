from pathlib import Path

from app.eval.retrieval_eval import (
    FIXTURES_PATH,
    LabeledQuery,
    evaluate_retrieval,
    load_labeled_queries,
)
from app.rag.schemas import ChunkMetadata, DocumentSource, RetrievedChunk


def _fake_chunk(source: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"{source}::chunk_0",
        text="irrelevant text",
        score=0.9,
        metadata=ChunkMetadata(
            source=source, source_type=DocumentSource.KNOWLEDGE_BASE, chunk_index=0
        ),
    )


def test_precision_and_recall_perfect_match() -> None:
    queries = [LabeledQuery(query="q1", relevant_sources=["a", "b"])]

    def retrieve_fn(query: str, k: int) -> list[RetrievedChunk]:
        return [_fake_chunk("a"), _fake_chunk("b")]

    report = evaluate_retrieval(retrieve_fn, queries=queries, k=2)
    assert report.mean_precision_at_k == 1.0
    assert report.mean_recall_at_k == 1.0


def test_precision_and_recall_partial_match() -> None:
    queries = [LabeledQuery(query="q1", relevant_sources=["a", "b"])]

    def retrieve_fn(query: str, k: int) -> list[RetrievedChunk]:
        return [_fake_chunk("a"), _fake_chunk("z")]  # 1 of 2 retrieved is relevant

    report = evaluate_retrieval(retrieve_fn, queries=queries, k=2)
    assert report.mean_precision_at_k == 0.5  # 1 relevant out of 2 retrieved
    assert report.mean_recall_at_k == 0.5  # 1 of 2 relevant docs found


def test_precision_and_recall_no_match() -> None:
    queries = [LabeledQuery(query="q1", relevant_sources=["a"])]

    def retrieve_fn(query: str, k: int) -> list[RetrievedChunk]:
        return [_fake_chunk("z")]

    report = evaluate_retrieval(retrieve_fn, queries=queries, k=1)
    assert report.mean_precision_at_k == 0.0
    assert report.mean_recall_at_k == 0.0


def test_empty_retrieval_does_not_crash() -> None:
    queries = [LabeledQuery(query="q1", relevant_sources=["a"])]

    def retrieve_fn(query: str, k: int) -> list[RetrievedChunk]:
        return []

    report = evaluate_retrieval(retrieve_fn, queries=queries, k=3)
    assert report.mean_precision_at_k == 0.0
    assert report.mean_recall_at_k == 0.0


def test_report_averages_across_multiple_queries() -> None:
    queries = [
        LabeledQuery(query="q1", relevant_sources=["a"]),
        LabeledQuery(query="q2", relevant_sources=["z"]),
    ]

    def retrieve_fn(query: str, k: int) -> list[RetrievedChunk]:
        return [_fake_chunk("a")]  # perfect for q1, zero for q2

    report = evaluate_retrieval(retrieve_fn, queries=queries, k=1)
    assert report.mean_precision_at_k == 0.5
    assert report.num_queries == 2


# --- fixture integrity -------------------------------------------------


def test_fixtures_file_exists() -> None:
    assert FIXTURES_PATH.exists()


def test_load_labeled_queries_has_15_to_20_entries() -> None:
    queries = load_labeled_queries()
    assert 15 <= len(queries) <= 20


def test_every_labeled_query_has_nonempty_fields() -> None:
    for q in load_labeled_queries():
        assert q.query.strip()
        assert len(q.relevant_sources) > 0


def test_every_relevant_source_matches_a_real_knowledge_doc() -> None:
    knowledge_dir = Path(__file__).resolve().parents[1] / "app" / "rag" / "knowledge_base"
    real_sources = {p.stem for p in knowledge_dir.glob("*.md")}

    for q in load_labeled_queries():
        for source in q.relevant_sources:
            assert source in real_sources, f"{source!r} in fixtures has no matching .md file"