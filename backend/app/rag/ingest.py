"""Ingestion pipeline.

Reads source documents, chunks them, embeds them locally, and writes them
into the appropriate Chroma collection. This module only writes —
app.rag.retriever is what everything else reads from.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, cast

import yaml
from chromadb.api import ClientAPI

from app.rag.chunker import chunk_markdown
from app.rag.embed import Embedder, EmbeddingModel
from app.rag.retriever import (
    KNOWLEDGE_COLLECTION_NAME,
    RUN_SUMMARY_COLLECTION_NAME,
    get_chroma_client,
    get_or_create_collection,
)
from app.rag.schemas import Chunk, DocumentSource

logger = logging.getLogger(__name__)


def _upsert_chunks(
    chunks: list[Chunk], collection_name: str, embedder: EmbeddingModel, client: ClientAPI
) -> int:
    if not chunks:
        return 0
    collection = get_or_create_collection(client, collection_name)

    embeddings = embedder.embed_documents([c.text for c in chunks])
    collection.upsert(
        ids=[c.chunk_id for c in chunks],
        documents=[c.text for c in chunks],
        embeddings=cast(Any, embeddings),
        metadatas=[c.metadata.model_dump(exclude_none=True) for c in chunks],
    )
    return len(chunks)


def ingest_knowledge_documents(
    knowledge_dir: Path,
    embedder: EmbeddingModel | None = None,
    client: ClientAPI | None = None,
) -> int:
    """Chunks and embeds every .md file under `knowledge_dir` into the
    knowledge_docs collection. Returns the number of chunks written."""
    embedder = embedder or Embedder()
    client = client or get_chroma_client()

    total = 0
    for md_path in sorted(knowledge_dir.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        chunks = chunk_markdown(
            text, source=md_path.stem, source_type=DocumentSource.KNOWLEDGE_BASE
        )
        written = _upsert_chunks(chunks, KNOWLEDGE_COLLECTION_NAME, embedder, client)
        logger.info(f"Ingested {written} chunks from {md_path.name}")
        total += written
    return total


def _build_run_summary_document(run_dir: Path) -> str | None:
    """Builds one markdown document from summary.json + diagnostics.json +
    selected config.yaml fields. Deliberately never reads training.log or
    metrics.csv — those are for the deterministic tools, not embedding.
    Returns None if the run is incomplete (any of the three files missing).
    """
    summary_path = run_dir / "summary.json"
    diagnostics_path = run_dir / "diagnostics.json"
    config_path = run_dir / "config.yaml"

    if not (summary_path.exists() and diagnostics_path.exists() and config_path.exists()):
        return None

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    gap = diagnostics["generalization_gap"]
    plateau = diagnostics["plateau"]
    instability = diagnostics["instability"]
    best = diagnostics["best_epoch"]

    plateau_note = (
        f" starting at epoch {plateau['plateau_start_epoch']}." if plateau["plateaued"] else "."
    )
    instability_note = (
        f", spikes at epochs {instability['spike_epochs']}." if instability["spike_epochs"] else "."
    )

    lines = [
        "## Summary",
        summary["description"],
        "",
        "## Diagnostics",
        f"Generalization gap at epoch {gap['epoch']}: {gap['loss_gap']:.4f} "
        f"({gap['loss_gap_pct']:.1f}%), trend {gap['trend']}.",
        f"Plateau detected: {plateau['plateaued']}{plateau_note}",
        f"Instability detected: {instability['is_unstable']}{instability_note}",
        f"Best epoch: {best['epoch']} with val_loss {best['val_loss']:.4f}.",
        "",
        "## Configuration",
        f"Dataset: {config['dataset']['train_size']} train / {config['dataset']['val_size']} val "
        f"images, augmentation={config['dataset']['augmentation']}.",
        f"Model: dropout={config['model']['dropout']}.",
        "Training: "
        f"optimizer={config['training']['optimizer']}, "
        f"lr={config['training']['lr']}, "
        f"lr_scheduler={config['training']['lr_scheduler']}, "
        f"batch_size={config['training']['batch_size']}, "
        f"weight_decay={config['training']['weight_decay']}, "
        f"epochs={config['training']['epochs']}.",
    ]
    return "\n".join(lines)


def ingest_run_summaries(
    runs_root: Path,
    embedder: EmbeddingModel | None = None,
    client: ClientAPI | None = None,
) -> int:
    """Builds one document per completed run from summary.json +
    diagnostics.json + selected config.yaml fields, chunks it, and embeds
    it into the run_summaries collection. Returns the number of chunks
    written. Runs missing any of the three source files are skipped.
    """
    embedder = embedder or Embedder()
    client = client or get_chroma_client()

    total = 0
    for run_dir in sorted(p for p in runs_root.glob("run_*") if p.is_dir()):
        document_text = _build_run_summary_document(run_dir)
        if document_text is None:
            logger.warning(
                f"Skipping {run_dir.name}: missing summary.json/diagnostics.json/config.yaml"
            )
            continue

        chunks = chunk_markdown(
            document_text,
            source=run_dir.name,
            source_type=DocumentSource.RUN_SUMMARY,
            run_id=run_dir.name,
        )
        written = _upsert_chunks(chunks, RUN_SUMMARY_COLLECTION_NAME, embedder, client)
        logger.info(f"Ingested {written} chunks from {run_dir.name}")
        total += written
    return total