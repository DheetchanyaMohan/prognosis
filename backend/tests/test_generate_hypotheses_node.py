from __future__ import annotations

import json

import pytest

from app.agent.nodes.generate_hypotheses import _build_evidence_sections, generate_hypotheses_node
from app.agent.state import AgentState
from app.llm import StructuredOutputError
from app.rag.schemas import ChunkMetadata, DocumentSource, RetrievedChunk


class FakeChatModel:
    """Implements the ChatModel protocol without any network access."""

    def __init__(self, response: str) -> None:
        self._response = response
        self.last_system_prompt: str | None = None
        self.last_user_prompt: str | None = None

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return self._response

    def stream_complete(self, system_prompt: str, user_prompt: str):
        yield self._response


_VALID_RESPONSE = json.dumps(
    [
        {
            "title": "Overfitting due to no regularization",
            "explanation": "The generalization gap is widening and dropout is 0.",
            "supporting_evidence": ["generalization_gap trend=widening", "dropout=0.0"],
            "confidence": 0.85,
        },
        {
            "title": "Dataset too small",
            "explanation": "train_size is only 1500 images.",
            "supporting_evidence": ["train_size=1500"],
            "confidence": 0.4,
        },
    ]
)


def _chunk(source: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"{source}::chunk_0", text=f"Some content about {source}.", score=0.7,
        metadata=ChunkMetadata(
            source=source, source_type=DocumentSource.KNOWLEDGE_BASE, chunk_index=0
        ),
    )


# --- generate_hypotheses_node -----------------------------------------


def test_produces_ranked_hypotheses_sorted_by_confidence() -> None:
    client = FakeChatModel(_VALID_RESPONSE)
    state: AgentState = {"user_query": "why is my model overfitting?"}

    result = generate_hypotheses_node(state, chat_model=client)

    hypotheses = result["hypotheses"]
    assert len(hypotheses) == 2
    assert hypotheses[0].confidence >= hypotheses[1].confidence
    assert hypotheses[0].title == "Overfitting due to no regularization"


def test_appends_exactly_one_trace_entry() -> None:
    client = FakeChatModel(_VALID_RESPONSE)
    result = generate_hypotheses_node({"user_query": "x"}, chat_model=client)

    assert len(result["trace"]) == 1
    assert result["trace"][0].node == "generate_hypotheses"
    assert result["trace"][0].tools_called == ["llm.generate_structured_list"]


def test_malformed_json_raises_structured_output_error() -> None:
    client = FakeChatModel("not valid json at all")
    with pytest.raises(StructuredOutputError, match="not valid JSON"):
        generate_hypotheses_node({"user_query": "x"}, chat_model=client)


def test_non_array_response_raises_structured_output_error() -> None:
    client = FakeChatModel(json.dumps({"not": "an array"}))
    with pytest.raises(StructuredOutputError, match="JSON array"):
        generate_hypotheses_node({"user_query": "x"}, chat_model=client)


def test_hypothesis_missing_required_field_raises() -> None:
    bad_response = json.dumps([{"title": "X", "explanation": "Y"}])  # missing confidence, evidence
    client = FakeChatModel(bad_response)
    with pytest.raises(StructuredOutputError):
        generate_hypotheses_node({"user_query": "x"}, chat_model=client)


def test_empty_hypothesis_list_is_valid() -> None:
    client = FakeChatModel(json.dumps([]))
    result = generate_hypotheses_node({"user_query": "x"}, chat_model=client)
    assert result["hypotheses"] == []


# --- _build_evidence_sections -------------------------------------------


def test_sections_include_retrieved_evidence() -> None:
    state: AgentState = {
        "user_query": "why is my model overfitting?",
        "retrieved_knowledge": [_chunk("overfitting")],
        "similar_runs": [_chunk("run_003")],
    }
    sections = _build_evidence_sections(state)
    headings = [h for h, _ in sections]

    assert "Retrieved documentation" in headings
    assert "Similar historical runs" in headings
    assert any("overfitting" in content for _, content in sections)
    assert any("run_003" in content for _, content in sections)


def test_sections_omitted_when_no_evidence() -> None:
    sections = _build_evidence_sections({"user_query": "what is dropout?"})
    assert sections == []


def test_llm_receives_the_built_prompt() -> None:
    client = FakeChatModel(_VALID_RESPONSE)
    state: AgentState = {"user_query": "why is my model overfitting?"}

    generate_hypotheses_node(state, chat_model=client)

    assert client.last_user_prompt is not None
    assert "why is my model overfitting?" in client.last_user_prompt
    assert client.last_system_prompt is not None
    assert "JSON array" in client.last_system_prompt