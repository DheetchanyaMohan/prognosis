from __future__ import annotations

import pytest

from app.agent.nodes import router as router_module
from app.agent.state import AgentState
from app.tools.experiment_tool import RunNotFoundError
from app.tools.schemas import RunRecord


def _run_record(run_id: str) -> RunRecord:
    from datetime import UTC, datetime

    return RunRecord(
        run_id=run_id, experiment_name="exp_test", status="complete",
        created_at=datetime.now(UTC), total_epochs=20,
    )


def _patch_get_run(monkeypatch: pytest.MonkeyPatch, existing_ids: set[str]) -> None:
    def fake_get_run(run_id: str, db: object = None) -> RunRecord:
        if run_id not in existing_ids:
            raise RunNotFoundError(f"No run found with run_id={run_id!r}")
        return _run_record(run_id)

    monkeypatch.setattr(router_module.experiment_tool, "get_run", fake_get_run)


def _patch_list_recent_runs(monkeypatch: pytest.MonkeyPatch, run_ids: list[str]) -> None:
    def fake_list_recent_runs(limit: int = 10, db: object = None) -> list[RunRecord]:
        return [_run_record(r) for r in run_ids[:limit]]

    monkeypatch.setattr(router_module.experiment_tool, "list_recent_runs", fake_list_recent_runs)


# --- single run diagnosis -------------------------------------------------


def test_single_known_run_id_classified_as_diagnose(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_get_run(monkeypatch, existing_ids={"run_005"})
    state: AgentState = {"user_query": "why is run_005 overfitting?"}

    result = router_module.router_node(state)

    assert result["request_type"] == "diagnose_run"
    assert result["selected_run"] == "run_005"
    assert result["comparison_run"] is None
    assert len(result["trace"]) == 1
    assert result["trace"][0].node == "router"


def test_unknown_run_id_is_dropped_not_crashed(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_get_run(monkeypatch, existing_ids=set())
    state: AgentState = {"user_query": "what happened in run_999?"}

    result = router_module.router_node(state)

    assert result["request_type"] == "general_question"
    assert result["selected_run"] is None
    assert "run_999" in result["trace"][0].reasoning


# --- comparison -------------------------------------------------------


def test_two_run_ids_classified_as_compare(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_get_run(monkeypatch, existing_ids={"run_001", "run_002"})
    state: AgentState = {"user_query": "compare run_001 and run_002"}

    result = router_module.router_node(state)

    assert result["request_type"] == "compare_runs"
    assert result["selected_run"] == "run_001"
    assert result["comparison_run"] == "run_002"


def test_one_run_id_plus_comparison_keyword_finds_baseline(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_get_run(monkeypatch, existing_ids={"run_005"})
    _patch_list_recent_runs(monkeypatch, ["run_005", "run_004", "run_003"])
    state: AgentState = {"user_query": "how does run_005 compare to my other runs?"}

    result = router_module.router_node(state)

    assert result["request_type"] == "compare_runs"
    assert result["selected_run"] == "run_005"
    assert result["comparison_run"] == "run_004"  # first recent run that isn't run_005


def test_comparison_keyword_with_no_other_runs_falls_back_to_diagnose(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_get_run(monkeypatch, existing_ids={"run_005"})
    _patch_list_recent_runs(monkeypatch, ["run_005"])  # no other runs exist
    state: AgentState = {"user_query": "compare run_005 to previous runs"}

    result = router_module.router_node(state)

    assert result["request_type"] == "diagnose_run"
    assert result["comparison_run"] is None


# --- implicit "my most recent run" -----------------------------------------


def test_implicit_recent_run_phrase_resolves_to_latest(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_list_recent_runs(monkeypatch, ["run_007"])
    state: AgentState = {"user_query": "why is my model overfitting?"}

    result = router_module.router_node(state)

    assert result["request_type"] == "diagnose_run"
    assert result["selected_run"] == "run_007"


def test_implicit_recent_run_phrase_with_no_runs_falls_back_to_general(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_list_recent_runs(monkeypatch, [])
    state: AgentState = {"user_query": "why is my model overfitting?"}

    result = router_module.router_node(state)

    assert result["request_type"] == "general_question"
    assert result["selected_run"] is None


# --- pure general question -------------------------------------------------


def test_general_knowledge_question_has_no_run(monkeypatch: pytest.MonkeyPatch) -> None:
    state: AgentState = {"user_query": "what is dropout regularization?"}
    result = router_module.router_node(state)

    assert result["request_type"] == "general_question"
    assert result["selected_run"] is None
    assert result["comparison_run"] is None


# --- helper functions --------------------------------------------------


def test_extract_run_ids_deduplicates_preserving_order() -> None:
    ids = router_module._extract_run_ids("compare run_003 with run_001, also run_003 again")
    assert ids == ["run_003", "run_001"]


def test_extract_run_ids_empty_when_none_present() -> None:
    assert router_module._extract_run_ids("what is overfitting?") == []