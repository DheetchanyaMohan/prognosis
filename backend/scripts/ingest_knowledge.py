"""Builds the knowledge_docs Chroma collection from the curated
markdown knowledge base. Runs once, at Docker build time — the
resulting collection is baked into the image and is byte-identical
across every deployment, since it never depends on runtime state (no
volume, no ingestion step required after deploy).

This is deliberately the ONLY thing this script does. Run summaries
(also build-time, per the current simplified architecture — see
scripts/ingest.py and app/rag/retriever.py's module docstring) are
ingested by a separate script for single-responsibility and idempotency
reasons, even though both now share one Chroma persist directory.

Usage (normally invoked from the Dockerfile, not by hand):
    python scripts/ingest_knowledge.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from app.core.logging import configure_logging
from app.rag.ingest import ingest_knowledge_documents
from app.rag.retriever import KNOWLEDGE_COLLECTION_NAME, get_chroma_client

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KNOWLEDGE_DIR = BACKEND_ROOT / "app" / "rag" / "knowledge_base"


def main() -> None:
    configure_logging()

    if not DEFAULT_KNOWLEDGE_DIR.exists():
        sys.exit(f"Knowledge directory not found: {DEFAULT_KNOWLEDGE_DIR}")

    client = get_chroma_client()

    # Idempotent by reconstruction, not by relying on upsert alone: upsert
    # can't remove chunks belonging to a deleted or shrunk source file, so
    # any existing collection (e.g. from a previous build) is dropped and
    # rebuilt fresh from the current source documents every time — never
    # an accumulation of old and new chunks.
    try:
        client.delete_collection(KNOWLEDGE_COLLECTION_NAME)
        print(f"Cleared existing '{KNOWLEDGE_COLLECTION_NAME}' collection")
    except Exception:  # noqa: BLE001 - nothing to clear is the common case, not an error
        print(f"No existing '{KNOWLEDGE_COLLECTION_NAME}' collection to clear")

    try:
        chunk_count = ingest_knowledge_documents(DEFAULT_KNOWLEDGE_DIR, client=client)
        print(
            "Collection count after ingest:",
            client.get_collection(KNOWLEDGE_COLLECTION_NAME).count(),
        )
    except Exception as exc:  # noqa: BLE001 - must exit non-zero, not raise, to fail the build
        print(f"Knowledge base ingestion failed: {exc}", file=sys.stderr)
        sys.exit(1)

    doc_count = len(sorted(DEFAULT_KNOWLEDGE_DIR.glob("*.md")))
    if chunk_count == 0:
        print(
            "Knowledge base ingestion produced zero chunks "
            "— treating as a failure",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Knowledge base ready: {doc_count} document(s), {chunk_count} chunk(s)")

    print("=== Persist directory contents ===")
    for root, dirs, files in os.walk(BACKEND_ROOT / "data" / "chroma"):
        print(root)
        for f in files:
            print(" ", f)


if __name__ == "__main__":
    main()