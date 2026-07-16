import json
from pathlib import Path

import chromadb
import yaml

from app.rag.ingest import (
    _build_run_summary_document,
    ingest_knowledge_documents,
    ingest_run_summaries,
)
from app.rag.retriever import KNOWLEDGE_COLLECTION_NAME, RUN_SUMMARY_COLLECTION_NAME
from tests.conftest import FakeEmbedder


def _write_complete_run(run_dir: Path, run_id: str) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "summary.json").write_text(
        json.dumps({"run_id": run_id, "description": f"Run {run_id} completed normally."})
    )
    (run_dir / "diagnostics.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "generalization_gap": {
                    "epoch": 20, "loss_gap": 0.5, "loss_gap_pct": 40.0, "trend": "widening",
                },
                "plateau": {"plateaued": False, "plateau_start_epoch": None},
                "instability": {"is_unstable": False, "spike_epochs": []},
                "best_epoch": {"epoch": 15, "val_loss": 0.9},
            }
        )
    )
    (run_dir / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "dataset": {"train_size": 1500, "val_size": 1000, "augmentation": False},
                "model": {"dropout": 0.0},
                "training": {
                    "optimizer": "adam", "lr": 0.001, "lr_scheduler": "cosine",
                    "batch_size": 64, "weight_decay": 0.0, "epochs": 20,
                },
            }
        )
    )


# --- _build_run_summary_document -------------------------------------------


def test_build_run_summary_document_includes_expected_fields(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001"
    _write_complete_run(run_dir, "run_001")

    document = _build_run_summary_document(run_dir)

    assert document is not None
    assert "Run run_001 completed normally." in document
    assert "widening" in document
    assert "dropout=0.0" in document
    assert "lr=0.001" in document


def test_build_run_summary_document_returns_none_if_incomplete(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_002"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(json.dumps({"description": "partial"}))
    # diagnostics.json and config.yaml deliberately missing

    assert _build_run_summary_document(run_dir) is None


def test_build_run_summary_document_never_reads_logs_or_metrics(tmp_path: Path) -> None:
    """Documents are built only from summary/diagnostics/config — never
    from training.log or metrics.csv, even if those files are present."""
    run_dir = tmp_path / "run_003"
    _write_complete_run(run_dir, "run_003")
    (run_dir / "training.log").write_text("SECRET_LOG_MARKER_12345")
    (run_dir / "metrics.csv").write_text("epoch,train_loss\nSECRET_METRICS_MARKER_67890,0.1")

    document = _build_run_summary_document(run_dir)

    assert document is not None
    assert "SECRET_LOG_MARKER_12345" not in document
    assert "SECRET_METRICS_MARKER_67890" not in document


# --- ingest_knowledge_documents ---------------------------------------------


def test_ingest_knowledge_documents_writes_expected_chunk_count(
    tmp_path: Path, fake_embedder: FakeEmbedder, chroma_client: chromadb.ClientAPI
) -> None:
    knowledge_dir = tmp_path / "knowledge_base"
    knowledge_dir.mkdir()
    (knowledge_dir / "doc_a.md").write_text("# A\n\nSome content about topic A.")
    (knowledge_dir / "doc_b.md").write_text("# B\n\nSome content about topic B.")

    written = ingest_knowledge_documents(
        knowledge_dir, embedder=fake_embedder, client=chroma_client
    )

    assert written == 2
    collection = chroma_client.get_or_create_collection(KNOWLEDGE_COLLECTION_NAME)
    assert collection.count() == 2


def test_ingest_knowledge_documents_is_idempotent_via_upsert(
    tmp_path: Path, fake_embedder: FakeEmbedder, chroma_client: chromadb.ClientAPI
) -> None:
    knowledge_dir = tmp_path / "knowledge_base"
    knowledge_dir.mkdir()
    (knowledge_dir / "doc_a.md").write_text("# A\n\nContent.")

    ingest_knowledge_documents(knowledge_dir, embedder=fake_embedder, client=chroma_client)
    # re-run with the same source file; chunk_ids are identical so this should upsert, not duplicate
    ingest_knowledge_documents(knowledge_dir, embedder=fake_embedder, client=chroma_client)

    collection = chroma_client.get_or_create_collection(KNOWLEDGE_COLLECTION_NAME)
    assert collection.count() == 1  # same chunk_id both times -> upsert, not duplicate


# --- ingest_run_summaries ---------------------------------------------------


def test_ingest_run_summaries_skips_incomplete_runs(
    tmp_path: Path, fake_embedder: FakeEmbedder, chroma_client: chromadb.ClientAPI
) -> None:
    runs_root = tmp_path / "runs"
    _write_complete_run(runs_root / "run_001", "run_001")
    (runs_root / "run_002").mkdir(parents=True)  # incomplete: no files at all

    written = ingest_run_summaries(runs_root, embedder=fake_embedder, client=chroma_client)

    assert written > 0
    collection = chroma_client.get_or_create_collection(RUN_SUMMARY_COLLECTION_NAME)
    all_metadatas = collection.get(include=["metadatas"])["metadatas"]
    assert all_metadatas is not None
    run_ids = {m["run_id"] for m in all_metadatas}
    assert run_ids == {"run_001"}