"""Ingests the knowledge base and/or run summaries into the real,
persisted Chroma store.

This is the orchestration entrypoint identified in the RAG/agentic-layer
audit as the one missing piece connecting the fully-built ingestion
library (app.rag.ingest) to any real data — this script contains no
embedding, chunking, retrieval, or Chroma logic of its own. It only
decides what to call, based on CLI flags, and reports what happened.

Usage:
    python scripts/ingest.py                          # ingest both
    python scripts/ingest.py --knowledge-only
    python scripts/ingest.py --runs-only
    python scripts/ingest.py --dry-run
    python scripts/ingest.py --reset
    python scripts/ingest.py --stats
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from app.core.logging import configure_logging
from app.rag.ingest import (
    _build_run_summary_document,  # reused, not duplicated — see _dry_run_runs
    ingest_knowledge_documents,
    ingest_run_summaries,
)
from app.rag.retriever import (
    KNOWLEDGE_COLLECTION_NAME,
    RUN_SUMMARY_COLLECTION_NAME,
    get_chroma_client,
)

logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_NAME = "exp_001_cifar10_subset_study"

DEFAULT_KNOWLEDGE_DIR = BACKEND_ROOT / "app" / "rag" / "knowledge_base"
DEFAULT_RUNS_ROOT = BACKEND_ROOT / "data" / "experiments" / EXPERIMENT_NAME / "runs"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--knowledge-only", action="store_true", help="Ingest only the knowledge base"
    )
    parser.add_argument("--runs-only", action="store_true", help="Ingest only run summaries")
    parser.add_argument(
        "--knowledge-dir",
        type=Path,
        default=DEFAULT_KNOWLEDGE_DIR,
        help=f"Knowledge base directory (default: {DEFAULT_KNOWLEDGE_DIR})",
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=DEFAULT_RUNS_ROOT,
        help=f"Runs directory (default: {DEFAULT_RUNS_ROOT})",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the relevant collection(s) before ingesting (see docstring: upsert "
        "alone can't remove chunks from deleted/shrunk source files)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be ingested without loading embeddings or writing to Chroma",
    )
    parser.add_argument(
        "--stats", action="store_true", help="Report collection statistics after running"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable DEBUG logging")

    args = parser.parse_args(argv)
    if args.knowledge_only and args.runs_only:
        parser.error("cannot combine --knowledge-only and --runs-only")
    return args


def _phases_to_run(args: argparse.Namespace) -> tuple[bool, bool]:
    """Returns (run_knowledge, run_runs) given the mutually-adjusting
    --knowledge-only/--runs-only flags. With neither flag, both run."""
    if args.knowledge_only:
        return True, False
    if args.runs_only:
        return False, True
    return True, True


def _dry_run_knowledge_docs(knowledge_dir: Path) -> list[Path]:
    """Lists the .md files that would be ingested. Same glob pattern
    app.rag.ingest.ingest_knowledge_documents uses internally — read-only,
    no embedding, no writing."""
    return sorted(knowledge_dir.glob("*.md"))


def _dry_run_runs(runs_root: Path) -> tuple[list[str], list[str]]:
    """Returns (ready_run_ids, incomplete_run_ids) without embedding or
    writing anything. Reuses app.rag.ingest's own completeness check
    (_build_run_summary_document) rather than re-implementing "which
    three files are required" here."""
    ready: list[str] = []
    incomplete: list[str] = []
    for run_dir in sorted(p for p in runs_root.glob("run_*") if p.is_dir()):
        if _build_run_summary_document(run_dir) is not None:
            ready.append(run_dir.name)
        else:
            incomplete.append(run_dir.name)
    return ready, incomplete


def _reset_collection(collection_name: str) -> None:
    """Deletes `collection_name` if it exists. A collection that doesn't
    exist yet is not an error — there's simply nothing to clear."""
    client = get_chroma_client()
    try:
        client.delete_collection(collection_name)
        logger.info(f"Cleared existing collection {collection_name!r}")
    except Exception as exc:  # noqa: BLE001 - absence of the collection is expected, not fatal
        logger.info(f"No existing collection {collection_name!r} to clear ({exc})")


def _collection_counts() -> dict[str, int]:
    """Returns {collection_name: chunk_count} for both collections. A
    collection that doesn't exist yet reports 0, not an error."""
    client = get_chroma_client()
    counts: dict[str, int] = {}
    for name in (KNOWLEDGE_COLLECTION_NAME, RUN_SUMMARY_COLLECTION_NAME):
        try:
            counts[name] = client.get_collection(name).count()
        except Exception:  # noqa: BLE001 - collection not existing yet reports as 0
            counts[name] = 0
    return counts


def _print_dry_run(run_knowledge: bool, run_runs: bool, args: argparse.Namespace) -> None:
    print("=== Dry run: nothing will be embedded or written ===")
    if args.reset:
        print("(--reset was also requested: would clear the relevant collection(s) first)")

    if run_knowledge:
        md_files = _dry_run_knowledge_docs(args.knowledge_dir)
        print(f"\nKnowledge base ({args.knowledge_dir}): {len(md_files)} document(s) ready")
        for path in md_files:
            print(f"  - {path.name}")

    if run_runs:
        ready, incomplete = _dry_run_runs(args.runs_root)
        print(
            f"\nRun summaries ({args.runs_root}): "
            f"{len(ready)} ready, {len(incomplete)} skipped (incomplete)"
        )
        for run_id in ready:
            print(f"  - {run_id}: ready")
        for run_id in incomplete:
            print(f"  - {run_id}: skipped (missing summary.json/diagnostics.json/config.yaml)")


def _print_stats() -> None:
    print("\n=== Collection Statistics ===")
    for name, count in _collection_counts().items():
        print(f"{name}: {count} chunk(s)")


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    configure_logging()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    run_knowledge, run_runs = _phases_to_run(args)

    if run_knowledge and not args.knowledge_dir.exists():
        sys.exit(f"Knowledge directory not found: {args.knowledge_dir}")
    if run_runs and not args.runs_root.exists():
        sys.exit(f"Runs directory not found: {args.runs_root}")

    if args.dry_run:
        _print_dry_run(run_knowledge, run_runs, args)
        if args.stats:
            _print_stats()
        return

    start = time.monotonic()

    knowledge_doc_count = 0
    knowledge_chunk_count = 0
    runs_ready_count = 0
    runs_skipped_count = 0
    run_chunk_count = 0

    if args.reset:
        if run_knowledge:
            _reset_collection(KNOWLEDGE_COLLECTION_NAME)
        if run_runs:
            _reset_collection(RUN_SUMMARY_COLLECTION_NAME)

    if run_knowledge:
        knowledge_doc_count = len(_dry_run_knowledge_docs(args.knowledge_dir))
        knowledge_chunk_count = ingest_knowledge_documents(args.knowledge_dir)

    if run_runs:
        ready, incomplete = _dry_run_runs(args.runs_root)
        runs_ready_count, runs_skipped_count = len(ready), len(incomplete)
        run_chunk_count = ingest_run_summaries(args.runs_root)

    elapsed = time.monotonic() - start

    print("\n=== Ingestion Summary ===")
    if run_knowledge:
        print(
            f"Knowledge base: {knowledge_doc_count} document(s), "
            f"{knowledge_chunk_count} chunk(s) written"
        )
    if run_runs:
        total_runs = runs_ready_count + runs_skipped_count
        print(
            f"Run summaries: {total_runs} run(s) found, {runs_ready_count} ingested, "
            f"{runs_skipped_count} skipped, {run_chunk_count} chunk(s) written"
        )
    print(f"Elapsed: {elapsed:.2f}s")

    if args.stats:
        _print_stats()


if __name__ == "__main__":
    main()