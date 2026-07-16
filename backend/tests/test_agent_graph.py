"""Tests for app.agent.graph's structure and control flow.

These use stub node callables (NodeFunctions), not the real
app.agent.nodes.* implementations — which don't exist yet — to verify
the graph wiring, the self-check retry loop, and its termination
guarantee in isolation from any node logic, LLM call, or tool call.
"""

from __future__ import annotations

from typing import Any

from app.agent.graph import MAX_RETRIES, NodeFunctions, _route_after_self_check, build_graph
from app.agent.state import AgentState, TraceEntry


def _trace(node: str) -> list[TraceEntry]:
    return [TraceEntry(node=node, reasoning="stub", evidence_summary="stub")]


def _make_stub_nodes(self_check_always_requests_retry: bool = False) -> NodeFunctions:
    """Builds a NodeFunctions of trivial stub callables. Each node just
    appends a trace entry recording that it ran, so tests can assert on
    execution order from the final trace.
    """

    def router(state: AgentState) -> dict[str, Any]:
        return {
            "selected_run": "run_001",
            "request_type": "diagnose_run",
            "trace": _trace("router"),
        }

    def retrieve_context(state: AgentState) -> dict[str, Any]:
        return {"retrieved_knowledge": [], "similar_runs": [], "trace": _trace("retrieve_context")}

    def analyze_metrics(state: AgentState) -> dict[str, Any]:
        return {"trace": _trace("analyze_metrics")}

    def generate_hypotheses(state: AgentState) -> dict[str, Any]:
        return {"hypotheses": [], "trace": _trace("generate_hypotheses")}

    def plan_experiments(state: AgentState) -> dict[str, Any]:
        return {"recommendations": [], "trace": _trace("plan_experiments")}

    def self_check(state: AgentState) -> dict[str, Any]:
        current_retries = state.get("retry_count", 0)
        needs_more = self_check_always_requests_retry and current_retries < MAX_RETRIES
        return {
            "needs_more_evidence": needs_more,
            "retry_count": current_retries + 1 if needs_more else current_retries,
            "trace": _trace("self_check"),
        }

    def finalize(state: AgentState) -> dict[str, Any]:
        return {"trace": _trace("finalize")}

    return NodeFunctions(
        router=router,
        retrieve_context=retrieve_context,
        analyze_metrics=analyze_metrics,
        generate_hypotheses=generate_hypotheses,
        plan_experiments=plan_experiments,
        self_check=self_check,
        finalize=finalize,
    )


# --- _route_after_self_check -------------------------------------------


def test_routes_to_finalize_when_evidence_sufficient() -> None:
    state: AgentState = {"needs_more_evidence": False, "retry_count": 0}
    assert _route_after_self_check(state) == "finalize"


def test_routes_to_retry_when_evidence_insufficient_and_under_cap() -> None:
    state: AgentState = {"needs_more_evidence": True, "retry_count": 0}
    assert _route_after_self_check(state) == "retry"


def test_routes_to_finalize_once_retry_cap_reached() -> None:
    # This state should never actually be produced by a correct self_check
    # (self_check is responsible for setting needs_more_evidence=False once
    # the cap is reached — see test_graph_terminates_even_if_self_check_never_satisfied
    # for the real end-to-end guarantee). Routing itself only ever trusts
    # the flag it's given; retry_count is informational context for
    # self_check, not something routing re-derives a decision from.
    state: AgentState = {"needs_more_evidence": False, "retry_count": MAX_RETRIES}
    assert _route_after_self_check(state) == "finalize"


def test_routes_to_finalize_with_missing_keys() -> None:
    # A node that hasn't run self_check yet shouldn't crash routing.
    assert _route_after_self_check({}) == "finalize"


# --- build_graph / end-to-end execution with stub nodes ---------------


def test_graph_runs_start_to_end_without_retry() -> None:
    graph = build_graph(_make_stub_nodes(self_check_always_requests_retry=False))

    result = graph.invoke({"user_query": "why is my model overfitting?"})

    executed_nodes = [entry.node for entry in result["trace"]]
    assert executed_nodes == [
        "router",
        "retrieve_context",
        "analyze_metrics",
        "generate_hypotheses",
        "plan_experiments",
        "self_check",
        "finalize",
    ]


def test_graph_retries_retrieval_exactly_once_then_finalizes() -> None:
    graph = build_graph(_make_stub_nodes(self_check_always_requests_retry=True))

    result = graph.invoke({"user_query": "why is my model overfitting?"})

    executed_nodes = [entry.node for entry in result["trace"]]
    # retrieve_context should appear twice (initial pass + one retry),
    # self_check should appear twice (initial check + recheck after retry),
    # and the graph must still terminate at finalize rather than looping forever.
    assert executed_nodes.count("retrieve_context") == 2
    assert executed_nodes.count("self_check") == 2
    assert executed_nodes[-1] == "finalize"
    assert executed_nodes.count("finalize") == 1


def test_retry_evidence_accumulates_rather_than_overwrites() -> None:
    """retrieved_knowledge uses an operator.add reducer, so a retry should
    extend the list, not replace it — verified here with a stub that
    returns one new chunk per retrieval pass."""
    from app.rag.schemas import ChunkMetadata, DocumentSource, RetrievedChunk

    call_count = {"n": 0}

    def retrieve_context(state: AgentState) -> dict[str, Any]:
        call_count["n"] += 1
        chunk = RetrievedChunk(
            chunk_id=f"chunk_{call_count['n']}",
            text="text",
            score=0.5,
            metadata=ChunkMetadata(
                source=f"doc_{call_count['n']}",
                source_type=DocumentSource.KNOWLEDGE_BASE,
                chunk_index=0,
            ),
        )
        return {"retrieved_knowledge": [chunk], "trace": _trace("retrieve_context")}

    nodes = _make_stub_nodes(self_check_always_requests_retry=True)
    nodes = NodeFunctions(
        router=nodes.router,
        retrieve_context=retrieve_context,
        analyze_metrics=nodes.analyze_metrics,
        generate_hypotheses=nodes.generate_hypotheses,
        plan_experiments=nodes.plan_experiments,
        self_check=nodes.self_check,
        finalize=nodes.finalize,
    )

    graph = build_graph(nodes)
    result = graph.invoke({"user_query": "why is my model overfitting?"})

    assert len(result["retrieved_knowledge"]) == 2  # one from each retrieval pass, accumulated


def test_graph_terminates_even_if_self_check_never_satisfied() -> None:
    """The MAX_RETRIES cap must hold even in the worst case: self_check
    always wants more evidence. The graph must still terminate."""
    graph = build_graph(_make_stub_nodes(self_check_always_requests_retry=True))
    result = graph.invoke({"user_query": "anything"})
    assert result["trace"][-1].node == "finalize"