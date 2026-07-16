import pytest

from app.rag.schemas import ChunkMetadata, DocumentSource, RetrievedChunk
from app.tools import retrieval_tool


def _fake_chunk(source: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"{source}::chunk_0",
        text="text",
        score=0.5,
        metadata=ChunkMetadata(
            source=source, source_type=DocumentSource.KNOWLEDGE_BASE, chunk_index=0
        ),
    )


def test_retrieve_knowledge_forwards_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_retrieve_knowledge(query: str, top_k: int = 5, metadata_filter: dict | None = None):
        captured["query"] = query
        captured["top_k"] = top_k
        captured["metadata_filter"] = metadata_filter
        return [_fake_chunk("overfitting")]

    monkeypatch.setattr(retrieval_tool, "_retrieve_knowledge", fake_retrieve_knowledge)

    result = retrieval_tool.retrieve_knowledge(
        "why is my model overfitting", top_k=3, metadata_filter={"source": "overfitting"}
    )

    assert captured["query"] == "why is my model overfitting"
    assert captured["top_k"] == 3
    assert captured["metadata_filter"] == {"source": "overfitting"}
    assert result == [_fake_chunk("overfitting")]


def test_retrieve_similar_runs_forwards_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_retrieve_similar_runs(query: str, top_k: int = 5, metadata_filter: dict | None = None):
        captured["query"] = query
        captured["top_k"] = top_k
        return [_fake_chunk("run_005")]

    monkeypatch.setattr(retrieval_tool, "_retrieve_similar_runs", fake_retrieve_similar_runs)

    result = retrieval_tool.retrieve_similar_runs("severe overfitting run", top_k=2)

    assert captured["query"] == "severe overfitting run"
    assert captured["top_k"] == 2
    assert result[0].metadata.source == "run_005"


def test_retrieve_knowledge_uses_default_top_k(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_retrieve_knowledge(query: str, top_k: int = 5, metadata_filter: dict | None = None):
        captured["top_k"] = top_k
        return []

    monkeypatch.setattr(retrieval_tool, "_retrieve_knowledge", fake_retrieve_knowledge)
    retrieval_tool.retrieve_knowledge("some query")

    assert captured["top_k"] == 5