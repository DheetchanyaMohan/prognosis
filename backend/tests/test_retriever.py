import chromadb
import pytest

from app.rag.ingest import ingest_knowledge_documents
from app.rag.retriever import Retriever, _distance_to_similarity
from app.rag.schemas import DocumentSource
from tests.conftest import FakeEmbedder

# --- _distance_to_similarity -------------------------------------------


def test_distance_to_similarity_conversion() -> None:
    assert _distance_to_similarity(0.0) == pytest.approx(1.0)  # identical
    assert _distance_to_similarity(1.0) == pytest.approx(0.0)  # orthogonal
    assert _distance_to_similarity(2.0) == pytest.approx(-1.0)  # opposite


# --- Retriever ---------------------------------------------------------


def test_retrieve_from_empty_collection_returns_empty_list(
    fake_embedder: FakeEmbedder, chroma_client: chromadb.ClientAPI
) -> None:
    retriever = Retriever(client=chroma_client, embedder=fake_embedder)
    assert retriever.retrieve_knowledge("anything") == []
    assert retriever.retrieve_similar_runs("anything") == []


def test_retrieve_knowledge_ranks_matching_topic_first(
    tmp_path, fake_embedder: FakeEmbedder, chroma_client: chromadb.ClientAPI
) -> None:
    knowledge_dir = tmp_path / "kb"
    knowledge_dir.mkdir()
    (knowledge_dir / "overfitting.md").write_text(
        "# Overfitting\n\nOverfitting happens when training loss keeps falling "
        "while validation loss stalls, indicating the model is memorizing."
    )
    (knowledge_dir / "optimization.md").write_text(
        "# Optimization\n\nGradient descent, batch size, and optimizer choice "
        "affect how quickly a model converges during training."
    )
    ingest_knowledge_documents(knowledge_dir, embedder=fake_embedder, client=chroma_client)

    retriever = Retriever(client=chroma_client, embedder=fake_embedder)
    results = retriever.retrieve_knowledge("overfitting memorizing training loss", top_k=2)

    assert len(results) == 2
    assert results[0].metadata.source == "overfitting"
    assert results[0].score >= results[1].score  # descending by similarity


def test_retrieve_knowledge_respects_top_k_larger_than_corpus(
    tmp_path, fake_embedder: FakeEmbedder, chroma_client: chromadb.ClientAPI
) -> None:
    knowledge_dir = tmp_path / "kb"
    knowledge_dir.mkdir()
    (knowledge_dir / "only_doc.md").write_text("# Only\n\nJust one document here.")
    ingest_knowledge_documents(knowledge_dir, embedder=fake_embedder, client=chroma_client)

    retriever = Retriever(client=chroma_client, embedder=fake_embedder)
    results = retriever.retrieve_knowledge("anything", top_k=50)

    assert len(results) == 1  # doesn't error even though top_k exceeds corpus size


def test_retrieved_chunks_carry_full_provenance(
    tmp_path, fake_embedder: FakeEmbedder, chroma_client: chromadb.ClientAPI
) -> None:
    knowledge_dir = tmp_path / "kb"
    knowledge_dir.mkdir()
    (knowledge_dir / "regularization.md").write_text(
        "# Regularization\n\nDropout and weight decay."
    )
    ingest_knowledge_documents(knowledge_dir, embedder=fake_embedder, client=chroma_client)

    retriever = Retriever(client=chroma_client, embedder=fake_embedder)
    results = retriever.retrieve_knowledge("dropout weight decay", top_k=1)

    assert len(results) == 1
    chunk = results[0]
    assert chunk.metadata.source == "regularization"
    assert chunk.metadata.source_type == DocumentSource.KNOWLEDGE_BASE
    assert chunk.metadata.section_title == "Regularization"
    assert isinstance(chunk.score, float)


def test_metadata_filter_restricts_results_to_matching_source(
    tmp_path, fake_embedder: FakeEmbedder, chroma_client: chromadb.ClientAPI
) -> None:
    knowledge_dir = tmp_path / "kb"
    knowledge_dir.mkdir()
    (knowledge_dir / "doc_a.md").write_text("# A\n\nShared vocabulary content here.")
    (knowledge_dir / "doc_b.md").write_text("# B\n\nShared vocabulary content here.")
    ingest_knowledge_documents(knowledge_dir, embedder=fake_embedder, client=chroma_client)

    retriever = Retriever(client=chroma_client, embedder=fake_embedder)
    results = retriever.retrieve_knowledge(
        "shared vocabulary content", top_k=5, metadata_filter={"source": "doc_a"}
    )

    assert len(results) == 1
    assert results[0].metadata.source == "doc_a"