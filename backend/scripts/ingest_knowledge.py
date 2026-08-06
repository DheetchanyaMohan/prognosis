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

    try:
        client.delete_collection(KNOWLEDGE_COLLECTION_NAME)
        print(f"Cleared existing '{KNOWLEDGE_COLLECTION_NAME}' collection")
    except Exception:
        print(f"No existing '{KNOWLEDGE_COLLECTION_NAME}' collection to clear")

    try:
        chunk_count = ingest_knowledge_documents(
            DEFAULT_KNOWLEDGE_DIR,
            client=client,
        )
    except Exception as exc:
        print(f"Knowledge base ingestion failed: {exc}", file=sys.stderr)
        sys.exit(1)

    # ---------- DEBUG ----------
    print("\n===== POST-INGEST DEBUG =====")
    collections = client.list_collections()
    print("Collections:", [c.name for c in collections])

    try:
        collection = client.get_collection(KNOWLEDGE_COLLECTION_NAME)
        print("Collection count:", collection.count())
    except Exception as exc:
        print("Could not open collection:", exc)

    print("=============================\n")
    # ---------------------------

    doc_count = len(sorted(DEFAULT_KNOWLEDGE_DIR.glob("*.md")))

    if chunk_count == 0:
        print(
            "Knowledge base ingestion produced zero chunks "
            "— treating as a failure",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"Knowledge base ready: {doc_count} document(s), "
        f"{chunk_count} chunk(s)"
    )

if __name__ == "__main__":
    main()