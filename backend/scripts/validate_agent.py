"""Runs the complete LangGraph diagnosis agent end-to-end against real
data and prints everything it produced.

This calls the exact same app.services.diagnosis_service.run_diagnosis
that POST /api/v1/runs/{run_id}/diagnose calls — there is only one
implementation of the diagnosis workflow. This script is a thin
formatter over its DiagnosisResponse, not a second orchestration path.
No HTTP is involved here; this is a direct Python call into the service.

Usage:
    python scripts/validate_agent.py --run-id run_005
    python scripts/validate_agent.py --run-id run_005 --query "compare run_005 and run_004"
"""

from __future__ import annotations

import argparse
import logging

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.llm.models import Hypothesis, Recommendation
from app.rag.schemas import RetrievedChunk
from app.services import DiagnosisResponse, run_diagnosis

logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-id", required=True, help="Run to diagnose, e.g. run_005"
    )
    parser.add_argument(
        "--query", help="Custom question to send instead of the default diagnostic phrasing"
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "gemini"],
        help="Display which provider is configured (does not override settings.llm_provider)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable DEBUG logging")
    return parser.parse_args()


def _print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def _print_evidence_list(label: str, chunks: list[RetrievedChunk]) -> None:
    print(f"{label} ({len(chunks)} chunk(s)):")
    if not chunks:
        print("  (none retrieved)")
        return
    for chunk in chunks:
        snippet = chunk.text.replace("\n", " ")[:100]
        print(f"  [{chunk.score:.3f}] {chunk.metadata.source}: {snippet}...")


def _print_hypotheses(hypotheses: list[Hypothesis]) -> None:
    if not hypotheses:
        print("(none produced)")
        return
    for i, h in enumerate(hypotheses, start=1):
        print(f"{i}. {h.title} (confidence={h.confidence:.2f})")
        print(f"   {h.explanation}")
        print(f"   evidence: {h.supporting_evidence}")


def _print_recommendations(recommendations: list[Recommendation]) -> None:
    if not recommendations:
        print("(none produced)")
        return
    for i, r in enumerate(recommendations, start=1):
        print(f"{i}. {r.title} (effort={r.estimated_effort}, confidence={r.confidence:.2f})")
        print(f"   rationale: {r.rationale}")
        print(f"   expected benefit: {r.expected_benefit}")
        print(f"   provenance: {r.provenance}")


def _print_result(result: DiagnosisResponse) -> None:
    _print_header("Query")
    print(result.user_query)

    _print_header("Router")
    print(f"request_type: {result.request_type}")
    print(f"selected_run: {result.selected_run}")
    print(f"comparison_run: {result.comparison_run}")

    _print_header("Retrieved Evidence")
    _print_evidence_list("Knowledge base", result.retrieved_knowledge)
    _print_evidence_list("Similar runs", result.similar_runs)

    _print_header("Hypotheses")
    _print_hypotheses(result.hypotheses)

    _print_header("Recommendations")
    _print_recommendations(result.recommendations)

    _print_header("Execution Trace")
    for i, entry in enumerate(result.trace, start=1):
        print(f"{i}. [{entry.node}] {entry.reasoning}")
        if entry.tools_called:
            print(f"   tools: {entry.tools_called}")
        print(f"   evidence: {entry.evidence_summary}")

    print()


def main() -> None:
    args = _parse_args()
    configure_logging()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    settings = get_settings()
    provider = args.provider or settings.llm_provider
    print(f"LLM provider: {provider}")

    result = run_diagnosis(run_id=args.run_id, query=args.query)
    _print_result(result)


if __name__ == "__main__":
    main()