from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

import app.services.diagnosis_service as diagnosis_service_module
from app.agent.state import TraceEntry
from app.llm import Hypothesis, LLMProviderError, Recommendation
from app.services.diagnosis_service import run_diagnosis
from app.tools.experiment_tool import RunNotFoundError


class _FakeCompiledGraph:
    def __init__(self, result: dict[str, Any] | Exception) -> None:
        self._result = result

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


def _patch_get_run(monkeypatch: pytest.MonkeyPatch, existing: bool) -> None:
    def fake_get_run(run_id: str, db: object = None) -> object:
        if not existing:
            raise RunNotFoundError(f"No run found with run_id={run_id!r}")
        return object()

    monkeypatch.setattr(diagnosis_service_module.experiment_tool, "get_run", fake_get_run)


def _patch_build_graph(monkeypatch: pytest.MonkeyPatch, result: dict[str, Any] | Exception) -> None:
    monkeypatch.setattr(
        diagnosis_service_module, "build_graph", lambda: _FakeCompiledGraph(result)
    )


def _full_agent_result() -> dict[str, Any]:
    return {
        "request_type": "diagnose_run",
        "selected_run": "run_005",
        "comparison_run": None,
        "retrieved_knowledge": [],
        "similar_runs": [],
        "diagnostics": None,
        "run_summary": None,
        "comparison": None,
        "hypotheses": [
            Hypothesis(
                title="Overfitting", explanation="Gap widening",
                supporting_evidence=["x"], confidence=0.8,
            )
        ],
        "recommendations": [
            Recommendation(
                title="Add dropout", rationale="x", supporting_evidence=["e"],
                expected_benefit="b", estimated_effort="low", confidence=0.8,
                provenance=["diagnostics:generalization_gap"],
            )
        ],
        "retry_count": 0,
        "needs_more_evidence": False,
        "trace": [
            TraceEntry(node="router", reasoning="resolved run_005", evidence_summary="ok")
        ],
    }


# --- run existence validation -------------------------------------------


def test_raises_for_unknown_run_before_invoking_graph(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_get_run(monkeypatch, existing=False)
    graph_was_called = {"value": False}

    class _ExplodingGraph:
        def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
            graph_was_called["value"] = True
            raise AssertionError("graph should never be invoked for an unknown run")

    monkeypatch.setattr(diagnosis_service_module, "build_graph", lambda: _ExplodingGraph())

    with pytest.raises(RunNotFoundError):
        run_diagnosis("run_999")

    assert graph_was_called["value"] is False


# --- query construction --------------------------------------------------


def test_uses_default_query_template_when_none_given(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_get_run(monkeypatch, existing=True)
    captured: dict[str, Any] = {}

    class _CapturingGraph:
        def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
            captured["state"] = state
            return _full_agent_result()

    monkeypatch.setattr(diagnosis_service_module, "build_graph", lambda: _CapturingGraph())

    result = run_diagnosis("run_005")

    assert "run_005" in captured["state"]["user_query"]
    assert result.user_query == captured["state"]["user_query"]


def test_uses_custom_query_when_given(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_get_run(monkeypatch, existing=True)
    captured: dict[str, Any] = {}

    class _CapturingGraph:
        def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
            captured["state"] = state
            return _full_agent_result()

    monkeypatch.setattr(diagnosis_service_module, "build_graph", lambda: _CapturingGraph())

    result = run_diagnosis("run_005", query="compare run_005 and run_004")

    assert captured["state"]["user_query"] == "compare run_005 and run_004"
    assert result.user_query == "compare run_005 and run_004"


# --- response construction ------------------------------------------------


def test_builds_complete_response_from_full_graph_result(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_get_run(monkeypatch, existing=True)
    _patch_build_graph(monkeypatch, _full_agent_result())

    before = datetime.now(UTC)
    result = run_diagnosis("run_005")
    after = datetime.now(UTC)

    assert result.run_id == "run_005"
    assert before <= result.generated_at <= after
    assert result.request_type == "diagnose_run"
    assert result.selected_run == "run_005"
    assert len(result.hypotheses) == 1
    assert result.hypotheses[0].title == "Overfitting"
    assert len(result.recommendations) == 1
    assert len(result.trace) == 1
    assert result.trace[0].node == "router"
    assert result.retry_count == 0
    assert result.needs_more_evidence is False


def test_response_defaults_missing_keys_to_empty_rather_than_raising(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A general_question result legitimately has no diagnostics, no
    hypotheses, etc. — the response must default these rather than
    KeyError on a partial AgentState dict."""
    _patch_get_run(monkeypatch, existing=True)
    minimal_result = {
        "request_type": "general_question",
        "selected_run": None,
        "comparison_run": None,
        "trace": [],
    }
    _patch_build_graph(monkeypatch, minimal_result)

    result = run_diagnosis("run_005")

    assert result.diagnostics is None
    assert result.run_summary is None
    assert result.comparison is None
    assert result.hypotheses == []
    assert result.recommendations == []
    assert result.retrieved_knowledge == []
    assert result.similar_runs == []
    assert result.retry_count == 0
    assert result.needs_more_evidence is False


# --- exception propagation --------------------------------------------------


def test_llm_provider_error_propagates_unwrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    """The service does not catch or reinterpret graph-execution
    failures — that classification is the API route's job."""
    _patch_get_run(monkeypatch, existing=True)
    _patch_build_graph(monkeypatch, LLMProviderError("provider is down"))

    with pytest.raises(LLMProviderError, match="provider is down"):
        run_diagnosis("run_005")