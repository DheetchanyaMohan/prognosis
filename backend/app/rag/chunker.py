"""Markdown-aware chunking.

Splits on header boundaries first, so a chunk never straddles two
unrelated sections, then further splits any section still too large into
overlapping paragraph-aligned windows. Chunk size is measured in
characters (~4 chars/token) rather than a real tokenizer, since an exact
token count isn't load-bearing here — only "roughly 300-500 tokens".
"""

from __future__ import annotations

import re

from app.rag.schemas import Chunk, ChunkMetadata, DocumentSource

#: Target chunk size, approximating 300-500 tokens at ~4 chars/token.
MAX_CHUNK_CHARS = 1600

#: Character overlap carried into the next chunk when a section is split,
#: so context isn't lost right at a chunk boundary.
CHUNK_OVERLAP_CHARS = 150

_HEADER_PATTERN = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)


def _split_into_sections(markdown_text: str) -> list[tuple[str | None, str]]:
    """Splits markdown into (header_title, section_body) pairs. Content
    before the first header, if any, gets header_title=None."""
    matches = list(_HEADER_PATTERN.finditer(markdown_text))
    if not matches:
        stripped = markdown_text.strip()
        return [(None, stripped)] if stripped else []

    sections: list[tuple[str | None, str]] = []
    if matches[0].start() > 0:
        preamble = markdown_text[: matches[0].start()].strip()
        if preamble:
            sections.append((None, preamble))

    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown_text)
        body = markdown_text[start:end].strip()
        if body:
            sections.append((title, body))
    return sections


def _split_oversized_section(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    """Splits `text` into overlapping windows on paragraph boundaries,
    each at most `max_chars` long."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    windows: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            windows.append(current)
            # Carry the tail of the previous window forward for continuity.
            current = f"{current[-overlap_chars:]}\n\n{paragraph}" if overlap_chars else paragraph
        else:
            # A single paragraph longer than max_chars is kept whole rather
            # than cut mid-sentence; the embedding model handles longer
            # inputs fine, this just isn't a "clean" chunk size anymore.
            windows.append(paragraph)
            current = ""
    if current:
        windows.append(current)
    return windows


def chunk_markdown(
    markdown_text: str,
    source: str,
    source_type: DocumentSource,
    run_id: str | None = None,
    max_chunk_chars: int = MAX_CHUNK_CHARS,
    overlap_chars: int = CHUNK_OVERLAP_CHARS,
) -> list[Chunk]:
    """Chunks one markdown document, each chunk carrying provenance back
    to `source` (and `run_id`, for run-summary documents)."""
    sections = _split_into_sections(markdown_text)

    chunks: list[Chunk] = []
    chunk_index = 0
    for title, body in sections:
        pieces = (
            [body]
            if len(body) <= max_chunk_chars
            else _split_oversized_section(body, max_chunk_chars, overlap_chars)
        )
        for piece in pieces:
            chunk_text = f"{title}\n\n{piece}" if title else piece
            chunks.append(
                Chunk(
                    chunk_id=f"{source}::chunk_{chunk_index}",
                    text=chunk_text,
                    metadata=ChunkMetadata(
                        source=source,
                        source_type=source_type,
                        section_title=title,
                        chunk_index=chunk_index,
                        run_id=run_id,
                    ),
                )
            )
            chunk_index += 1
    return chunks