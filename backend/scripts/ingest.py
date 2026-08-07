"""Ingests completed runs' summaries into the runtime Chroma store.

This is the runtime counterpart to scripts/ingest_knowledge.py, which
builds the static knowledge_docs collection once, at Docker build time.
This script is the opposite kind of thing on purpose: run summaries are
generated continuously while the application operates, so ingesting
them is something that happens repeatedly, after deployment — never
during the image build.

Usage:
    python scripts/ingest.py
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
from app.rag.ingest import _build_run_summary_document, ingest_run_summaries
from app.rag.retriever import RUN_SUMMARY_COLLECTION_NAME, get_chroma_client

logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_NAME = "exp_001_cifar10_subset_study"

DEFAULT_RUNS_ROOT = BACKEND_ROOT / "data" / "experiments" / EXPERIMENT_NAME / "runs"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=DEFAULT_RUNS_ROOT,
        help=f"Runs directory (default: {DEFAULT_RUNS_ROOT})",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the run_summaries collection before ingesting (see docstring: upsert "
        "alone can't remove chunks from deleted/shrunk source runs)",
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

    return parser.parse_args(argv)


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


def _reset_collection() -> None:
    client = get_chroma_client()
    try:
        client.delete_collection(RUN_SUMMARY_COLLECTION_NAME)
        logger.info(f"Cleared existing collection {RUN_SUMMARY_COLLECTION_NAME!r}")
    except Exception as exc:  # noqa: BLE001 - absence of the collection is expected, not fatal
        logger.info(f"No existing collection {RUN_SUMMARY_COLLECTION_NAME!r} to clear ({exc})")


def _collection_count() -> int:
    client = get_chroma_client()
    try:
        return client.get_collection(RUN_SUMMARY_COLLECTION_NAME).count()
    except Exception:  # noqa: BLE001 - collection not existing yet reports as 0
        return 0


def _print_dry_run(runs_root: Path, reset: bool) -> None:
    print("=== Dry run: nothing will be embedded or written ===")
    if reset:
        print("(--reset was also requested: would clear the run_summaries collection first)")

    ready, incomplete = _dry_run_runs(runs_root)
    print(
        f"\nRun summaries ({runs_root}): {len(ready)} ready, {len(incomplete)} skipped (incomplete)"
    )
    for run_id in ready:
        print(f"  - {run_id}: ready")
    for run_id in incomplete:
        print(f"  - {run_id}: skipped (missing summary.json/diagnostics.json/config.yaml)")


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    configure_logging()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.runs_root.exists():
        sys.exit(f"Runs directory not found: {args.runs_root}")

    if args.dry_run:
        _print_dry_run(args.runs_root, args.reset)
        if args.stats:
            print(
                "\n=== Collection Statistics ===\n"
                f"{RUN_SUMMARY_COLLECTION_NAME}: {_collection_count()} chunk(s)"
            )
        return

    start = time.monotonic()

    ready, incomplete = _dry_run_runs(args.runs_root)

    client = get_chroma_client()

    try:
        if args.reset:
            try:
                client.delete_collection(RUN_SUMMARY_COLLECTION_NAME)
                logger.info(f"Cleared existing collection {RUN_SUMMARY_COLLECTION_NAME!r}")
            except Exception as exc:  # noqa: BLE001 - absence is expected
                logger.info(
                    f"No existing collection {RUN_SUMMARY_COLLECTION_NAME!r} to clear ({exc})"
                )

        run_chunk_count = ingest_run_summaries(
            args.runs_root,
            client=client,
        )

    finally:
        client.close()

    elapsed = time.monotonic() - start

    print("\n=== Ingestion Summary ===")
    total_runs = len(ready) + len(incomplete)
    print(
        f"Run summaries: {total_runs} run(s) found, {len(ready)} ingested, "
        f"{len(incomplete)} skipped, {run_chunk_count} chunk(s) written"
    )
    print(f"Elapsed: {elapsed:.2f}s")

    if args.stats:
        print(
            "\n=== Collection Statistics ===\n"
            f"{RUN_SUMMARY_COLLECTION_NAME}: {_collection_count()} chunk(s)"
        )


if __name__ == "__main__":
    main()