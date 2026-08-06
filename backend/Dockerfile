FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first so this layer is cached unless pyproject.toml changes.
COPY pyproject.toml ./
COPY app ./app
COPY data ./data

RUN pip install --upgrade pip && pip install .

# Build both Chroma collections into the image itself (data/chroma/),
# so every deployment ships an identical, pre-populated vector store with
# zero manual post-deployment ingestion.
#
# knowledge_docs is rebuilt from app/rag/knowledge_base/.
# run_summaries is rebuilt from data/experiments/.../runs/.
#
# The two scripts intentionally remain separate:
#   • ingest_knowledge.py fails if no knowledge documents are ingested,
#     preventing an image from shipping with an empty knowledge base.
#   • ingest.py allows zero run summaries (a valid state before any runs
#     exist) while still rebuilding the collection deterministically.
#
# --reset is used only during Docker builds so every image starts from a
# completely clean run_summaries collection, eliminating stale or orphaned
# chunks. When run manually, scripts/ingest.py still defaults to
# incremental upserts, which is useful during development.
COPY scripts ./scripts

RUN python scripts/ingest_knowledge.py
RUN python scripts/ingest.py --reset

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
WORKDIR /app

# Install dependencies first so this layer is cached unless pyproject.toml changes.
COPY pyproject.toml ./
COPY app ./app
COPY data ./data
RUN pip install --upgrade pip && pip install .

# Builds both Chroma collections into the image itself (data/chroma/),
# baked at build time so every deployment ships an identical,
# pre-populated store with zero manual steps or runtime ingestion
# required. Both knowledge_docs and run_summaries are fully reproducible
# from what's already copied into the image above (app/rag/knowledge_base
# and data/experiments/.../runs respectively) — deliberately simple
# while that stays true; see app/rag/retriever.py's module docstring for
# when this would need revisiting.
#
# Two separate RUN steps, not one: ingest_knowledge.py exits non-zero on
# an empty result (the knowledge base must never ship empty), while
# ingest.py legitimately allows zero run summaries (no runs trained yet
# is a valid state) — keeping them separate preserves that distinction
# and each one's own failure semantics.
COPY scripts ./scripts
RUN python scripts/ingest_knowledge.py
RUN python scripts/ingest.py

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]