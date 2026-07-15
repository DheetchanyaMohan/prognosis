"""Retrieve Context node.

Second node in the diagnosis graph. Calls
app.tools.retrieval_tool.retrieve_knowledge and
app.tools.retrieval_tool.retrieve_similar_runs to gather evidence for the
router's resolved request. Performs no reasoning, no metric analysis, and
produces no recommendations — purely retrieval.
"""

from __future__ import annotations

from typing import Any

from app.agent.state import AgentState, TraceEntry
from app.rag.schemas import RetrievedChunk
from app.tools import retrieval_tool

#: Chunks retrieved per collection on the first pass.
DEFAULT_TOP_K = 5

#: On a self_check-triggered retry, top_k widens rather than staying
#: fixed — re-running the identical query at the identical top_k would
#: just fetch the same chunks again (retrieved_knowledge accumulates via
#: an operator.add reducer in AgentState, so a literal repeat would show
#: up as duplicates rather than new evidence).
RETRY_TOP_K_MULTIPLIER = 2


def _unique_sources(chunks: list[RetrievedChunk]) -> list[str]:
    seen: dict[str, None] = {}
    for chunk in chunks:
        seen.setdefault(chunk.metadata.source, None)
    return list(seen.keys())


def retrieve_context_node(state: AgentState) -> dict[str, Any]:
    query = state.get("user_query", "")
    selected_run = state.get("selected_run")
    retry_count = state.get("retry_count", 0)

    top_k = DEFAULT_TOP_K * (RETRY_TOP_K_MULTIPLIER if retry_count > 0 else 1)

    knowledge_chunks = retrieval_tool.retrieve_knowledge(query, top_k=top_k)

    # Never surface the selected run as "similar" to itself.
    similar_runs_filter: dict[str, Any] | None = (
        {"run_id": {"$ne": selected_run}} if selected_run else None
    )
    similar_run_chunks = retrieval_tool.retrieve_similar_runs(
        query, top_k=top_k, metadata_filter=similar_runs_filter
    )

    reasoning = (
        f"Retrieved {len(knowledge_chunks)} knowledge chunk(s) "
        f"(sources: {_unique_sources(knowledge_chunks)}) and "
        f"{len(similar_run_chunks)} similar-run chunk(s) "
        f"(runs: {_unique_sources(similar_run_chunks)}) at top_k={top_k}."
    )
    if retry_count > 0:
        reasoning += f" This is a retry pass (retry_count={retry_count}), so top_k was widened."
    if selected_run:
        reasoning += f" Excluded {selected_run} from similar-run results."

    trace_entry = TraceEntry(
        node="retrieve_context",
        tools_called=["retrieval_tool.retrieve_knowledge", "retrieval_tool.retrieve_similar_runs"],
        reasoning=reasoning,
        evidence_summary=(
            f"{len(knowledge_chunks)} knowledge chunk(s), "
            f"{len(similar_run_chunks)} similar-run chunk(s)"
        ),
    )

    return {
        "retrieved_knowledge": knowledge_chunks,
        "similar_runs": similar_run_chunks,
        "trace": [trace_entry],
    }