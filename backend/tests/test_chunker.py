from app.rag.chunker import chunk_markdown
from app.rag.schemas import DocumentSource


def test_splits_on_headers() -> None:
    text = "# Title\n\nIntro text.\n\n## Section A\n\nBody A.\n\n## Section B\n\nBody B."
    chunks = chunk_markdown(text, source="doc", source_type=DocumentSource.KNOWLEDGE_BASE)

    titles = [c.metadata.section_title for c in chunks]
    assert "Title" in titles
    assert "Section A" in titles
    assert "Section B" in titles


def test_chunk_indices_are_sequential_within_source() -> None:
    text = "# A\n\nbody\n\n# B\n\nbody\n\n# C\n\nbody"
    chunks = chunk_markdown(text, source="doc", source_type=DocumentSource.KNOWLEDGE_BASE)
    assert [c.metadata.chunk_index for c in chunks] == list(range(len(chunks)))


def test_chunk_ids_are_unique_and_reference_source() -> None:
    text = "# A\n\nbody\n\n# B\n\nbody"
    chunks = chunk_markdown(text, source="my_doc", source_type=DocumentSource.KNOWLEDGE_BASE)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))
    assert all(cid.startswith("my_doc::chunk_") for cid in ids)


def test_document_with_no_headers_still_produces_one_chunk() -> None:
    text = "Just a plain paragraph with no markdown headers at all."
    chunks = chunk_markdown(text, source="doc", source_type=DocumentSource.KNOWLEDGE_BASE)
    assert len(chunks) == 1
    assert chunks[0].metadata.section_title is None


def test_empty_document_produces_no_chunks() -> None:
    assert chunk_markdown("", source="doc", source_type=DocumentSource.KNOWLEDGE_BASE) == []


def test_oversized_section_is_split_into_multiple_chunks() -> None:
    long_body = "\n\n".join(
        f"Paragraph {i} with some filler content to add length." for i in range(60)
    )
    text = f"# Big Section\n\n{long_body}"
    chunks = chunk_markdown(
        text, source="doc", source_type=DocumentSource.KNOWLEDGE_BASE,
        max_chunk_chars=500, overlap_chars=50,
    )
    assert len(chunks) > 1
    assert all(c.metadata.section_title == "Big Section" for c in chunks)


def test_run_summary_chunks_carry_run_id() -> None:
    text = "## Summary\n\nRun details here."
    chunks = chunk_markdown(
        text, source="run_005", source_type=DocumentSource.RUN_SUMMARY, run_id="run_005"
    )
    assert all(c.metadata.run_id == "run_005" for c in chunks)
    assert all(c.metadata.source_type == DocumentSource.RUN_SUMMARY for c in chunks)


def test_knowledge_base_chunks_have_no_run_id() -> None:
    chunks = chunk_markdown("## X\n\nbody", source="doc", source_type=DocumentSource.KNOWLEDGE_BASE)
    assert all(c.metadata.run_id is None for c in chunks)