from __future__ import annotations

from typing import Any

import pytest

from app.agent.nodes import retrieve_context as retrieve_context_module
from app.agent.state import AgentState
from app.rag.schemas import ChunkMetadata, DocumentSource, RetrievedChunk


def _chunk(
    source: str, source_type: DocumentSource = DocumentSource.KNOWLEDGE_BASE
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"{source}::chunk_0",
        text="text",
        score=0.5,
        metadata=ChunkMetadata(source=source, source_type=source_type, chunk_index=0),
    )


def test_populates_both_evidence_lists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        retrieve_context_module.retrieval_tool,
        "retrieve_knowledge",
        lambda query, top_k=5, metadata_filter=None: [_chunk("overfitting")],
    )
    monkeypatch.setattr(
        retrieve_context_module.retrieval_tool,
        "retrieve_similar_runs",
        lambda query, top_k=5, metadata_filter=None: [
            _chunk("run_003", DocumentSource.RUN_SUMMARY)
        ],
    )

    state: AgentState = {"user_query": "why is my model overfitting?", "selected_run": "run_005"}
    result = retrieve_context_module.retrieve_context_node(state)

    assert len(result["retrieved_knowledge"]) == 1
    assert result["retrieved_knowledge"][0].metadata.source == "overfitting"
    assert len(result["similar_runs"]) == 1
    assert result["similar_runs"][0].metadata.source == "run_003"
    assert len(result["trace"]) == 1
    assert result["trace"][0].node == "retrieve_context"


def test_no_analysis_or_recommendations_produced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        retrieve_context_module.retrieval_tool, "retrieve_knowledge",
        lambda query, top_k=5, metadata_filter=None: [],
    )
    monkeypatch.setattr(
        retrieve_context_module.retrieval_tool, "retrieve_similar_runs",
        lambda query, top_k=5, metadata_filter=None: [],
    )

    result = retrieve_context_module.retrieve_context_node({"user_query": "anything"})

    assert set(result.keys()) == {"retrieved_knowledge", "similar_runs", "trace"}


def test_excludes_selected_run_from_similar_runs_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_retrieve_similar_runs(
        query: str, top_k: int = 5, metadata_filter: dict[str, Any] | None = None
    ) -> list[RetrievedChunk]:
        captured["metadata_filter"] = metadata_filter
        return []

    monkeypatch.setattr(
        retrieve_context_module.retrieval_tool, "retrieve_knowledge",
        lambda query, top_k=5, metadata_filter=None: [],
    )
    monkeypatch.setattr(
        retrieve_context_module.retrieval_tool, "retrieve_similar_runs", fake_retrieve_similar_runs
    )

    retrieve_context_module.retrieve_context_node(
        {"user_query": "why is this overfitting?", "selected_run": "run_005"}
    )

    assert captured["metadata_filter"] == {"run_id": {"$ne": "run_005"}}


def test_no_filter_when_no_run_selected(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_retrieve_similar_runs(
        query: str, top_k: int = 5, metadata_filter: dict[str, Any] | None = None
    ) -> list[RetrievedChunk]:
        captured["metadata_filter"] = metadata_filter
        return []

    monkeypatch.setattr(
        retrieve_context_module.retrieval_tool, "retrieve_knowledge",
        lambda query, top_k=5, metadata_filter=None: [],
    )
    monkeypatch.setattr(
        retrieve_context_module.retrieval_tool, "retrieve_similar_runs", fake_retrieve_similar_runs
    )

    retrieve_context_module.retrieve_context_node({"user_query": "what is dropout?"})

    assert captured["metadata_filter"] is None


def test_top_k_widens_on_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_top_ks: list[int] = []

    def fake_retrieve(
        query: str, top_k: int = 5, metadata_filter: dict[str, Any] | None = None
    ) -> list[RetrievedChunk]:
        captured_top_ks.append(top_k)
        return []

    monkeypatch.setattr(retrieve_context_module.retrieval_tool, "retrieve_knowledge", fake_retrieve)
    monkeypatch.setattr(
        retrieve_context_module.retrieval_tool, "retrieve_similar_runs", fake_retrieve
    )

    retrieve_context_module.retrieve_context_node({"user_query": "x", "retry_count": 0})
    retrieve_context_module.retrieve_context_node({"user_query": "x", "retry_count": 1})

    first_pass_top_k, second_pass_top_k = captured_top_ks[0], captured_top_ks[2]
    assert second_pass_top_k > first_pass_top_k


def test_unique_sources_deduplicates_preserving_order() -> None:
    chunks = [_chunk("a"), _chunk("b"), _chunk("a")]
    assert retrieve_context_module._unique_sources(chunks) == ["a", "b"]