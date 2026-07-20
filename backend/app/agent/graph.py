"""LangGraph state graph wiring for the diagnosis workflow.

This module only wires nodes together — router, retrieve_context,
analyze_metrics, generate_hypotheses, plan_experiments, self_check,
finalize. All node logic lives in app.agent.nodes.*; this file contains
no business logic, no tool calls, and no LLM calls of its own.

Node implementations are imported lazily (see _default_nodes), not at
module import time. That's what lets `import app.agent.graph` succeed —
and lets this module's structure be unit tested with stub node callables
— independent of whether app.agent.nodes.* exists yet.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agent.state import AgentState

#: Self-check may request one additional retrieval pass, never more —
#: this is what guarantees the graph terminates.
MAX_RETRIES = 1

#: Nodes return a partial state update (only the keys they touched),
#: which LangGraph merges into the running state — the idiomatic
#: LangGraph node signature, not a full-state return.
NodeFn = Callable[[AgentState], dict[str, Any]]

#: This graph has no runtime context object and uses AgentState for both
#: its input and output schema, so ContextT/InputT/OutputT collapse to
#: `Any`/`AgentState`/`AgentState` everywhere — named here once so the
#: rest of the module isn't repeating a four-parameter generic.
_Graph = StateGraph[AgentState, Any, AgentState, AgentState]
_CompiledGraph = CompiledStateGraph[AgentState, Any, AgentState, AgentState]


@dataclass(frozen=True)
class NodeFunctions:
    """Bundles the seven node callables the graph wires together.

    build_graph() accepts a NodeFunctions instance directly rather than
    always importing app.agent.nodes.* itself — that's what lets the
    graph's structure (edges, the self-check retry loop, termination) be
    tested against stub nodes before the real node implementations exist.
    """

    router: NodeFn
    retrieve_context: NodeFn
    analyze_metrics: NodeFn
    generate_hypotheses: NodeFn
    plan_experiments: NodeFn
    self_check: NodeFn
    finalize: NodeFn


def _default_nodes() -> NodeFunctions:
    """Imports the real node implementations from app.agent.nodes.*.

    Deferred to call time (not module import time) so `import
    app.agent.graph` never requires those modules to exist — kept as a
    deferred import for consistency and testability (build_graph() still
    accepts injected NodeFunctions for tests) now that all seven exist.
    """
    from app.agent.nodes.analyze_metrics import analyze_metrics_node
    from app.agent.nodes.finalize import finalize_node
    from app.agent.nodes.generate_hypotheses import generate_hypotheses_node
    from app.agent.nodes.plan_experiments import plan_experiments_node
    from app.agent.nodes.retrieve_context import retrieve_context_node
    from app.agent.nodes.router import router_node
    from app.agent.nodes.self_check import self_check_node

    return NodeFunctions(
        router=router_node,
        retrieve_context=retrieve_context_node,
        analyze_metrics=analyze_metrics_node,
        generate_hypotheses=generate_hypotheses_node,
        plan_experiments=plan_experiments_node,
        self_check=self_check_node,
        finalize=finalize_node,
    )


def _route_after_self_check(state: AgentState) -> str:
    """Conditional edge out of self_check.

    Trusts self_check's `needs_more_evidence` flag as the sole authority
    on whether to retry — self_check is what has both the current
    retry_count and the MAX_RETRIES cap available when it makes that
    decision. Re-deriving the cap check here against retry_count would be
    wrong: by the time this function runs, retry_count already reflects
    self_check's own update for *this* pass, so comparing it against
    MAX_RETRIES again here would be comparing the wrong snapshot in time
    and silently skip the one retry the cap is supposed to allow.
    """
    return "retry" if state.get("needs_more_evidence", False) else "finalize"


def _add_node(graph: _Graph, name: str, fn: NodeFn) -> None:
    """Thin wrapper around StateGraph.add_node.

    LangGraph's add_node overloads are Protocol-based and generic over
    NodeInputT; a plain `Callable[[AgentState], dict[str, Any]]` stored
    in a dataclass field satisfies that Protocol's runtime contract
    exactly, but mypy's overload resolution doesn't always match it
    against a TypedDict-parameterized Protocol when the callable is
    passed indirectly (via a field) rather than as a literal function.
    The cast is scoped to this one helper rather than repeated at every
    call site below.
    """
    graph.add_node(name, cast(Any, fn))


def build_graph(nodes: NodeFunctions | None = None) -> _CompiledGraph:
    """Builds and compiles the diagnosis workflow graph.

    With no arguments, wires up the real node implementations from
    app.agent.nodes. Pass a NodeFunctions of stub callables to verify the
    graph's structure and routing independent of node logic (see
    tests/test_agent_graph.py).
    """
    nodes = nodes or _default_nodes()

    graph: _Graph = StateGraph(AgentState)

    _add_node(graph, "router", nodes.router)
    _add_node(graph, "retrieve_context", nodes.retrieve_context)
    _add_node(graph, "analyze_metrics", nodes.analyze_metrics)
    _add_node(graph, "generate_hypotheses", nodes.generate_hypotheses)
    _add_node(graph, "plan_experiments", nodes.plan_experiments)
    _add_node(graph, "self_check", nodes.self_check)
    _add_node(graph, "finalize", nodes.finalize)

    graph.add_edge(START, "router")
    graph.add_edge("router", "retrieve_context")
    graph.add_edge("retrieve_context", "analyze_metrics")
    graph.add_edge("analyze_metrics", "generate_hypotheses")
    graph.add_edge("generate_hypotheses", "plan_experiments")
    graph.add_edge("plan_experiments", "self_check")

    graph.add_conditional_edges(
        "self_check",
        _route_after_self_check,
        {"retry": "retrieve_context", "finalize": "finalize"},
    )
    graph.add_edge("finalize", END)

    return graph.compile()