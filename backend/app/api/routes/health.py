"""Health check route.

Checks the app's real dependencies — database connectivity, Chroma
reachability, per-collection document counts, and whether an LLM
provider is configured. The LLM check is configuration-only: it never
constructs a chat model or calls the provider, since a health check
should be fast and side-effect-free.
"""

from __future__ import annotations

from chromadb.api import ClientAPI
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import DbSession
from app.api.schemas import CollectionStatus, HealthComponentStatus, HealthResponse
from app.core.config import get_settings
from app.rag.retriever import (
    KNOWLEDGE_COLLECTION_NAME,
    RUN_SUMMARY_COLLECTION_NAME,
    get_chroma_client,
)

router = APIRouter(tags=["system"])


def _check_database(db: Session) -> HealthComponentStatus:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - report any failure, don't crash the health check
        return HealthComponentStatus(status="error", detail=str(exc))
    return HealthComponentStatus(status="ok")


def _check_chroma(client: ClientAPI) -> HealthComponentStatus:
    """General connectivity only — per-collection document counts are
    reported separately below, since a reachable-but-empty store and an
    unreachable store are different problems and shouldn't look
    identical in this field."""
    try:
        client.heartbeat()
    except Exception as exc:  # noqa: BLE001
        return HealthComponentStatus(status="error", detail=str(exc))
    return HealthComponentStatus(status="ok")


def _check_collection(client: ClientAPI, collection_name: str) -> CollectionStatus:
    try:
        count = client.get_collection(collection_name).count()
    except Exception:  # noqa: BLE001 - collection not existing yet is not a real error
        return CollectionStatus(status="ok", document_count=0)
    return CollectionStatus(status="ok", document_count=count)


def _check_llm_provider() -> HealthComponentStatus:
    """Configuration check only — never constructs a ChatModel or calls
    the provider. See app.llm.client.get_chat_model for the real client."""
    settings = get_settings()

    provider = settings.llm_provider

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            return HealthComponentStatus(
                status="not_configured",
                detail="ANTHROPIC_API_KEY is not set",
            )

    elif provider == "gemini":
        if not settings.gemini_api_key:
            return HealthComponentStatus(
                status="not_configured",
                detail="GEMINI_API_KEY is not set",
            )

    else:
        return HealthComponentStatus(
            status="error",
            detail=f"Unknown LLM provider configured: {provider!r}",
        )

    return HealthComponentStatus(
        status="ok",
        detail=f"provider={provider}",
    )


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check(db: DbSession) -> HealthResponse:
    database_status = await run_in_threadpool(_check_database, db)

    client = get_chroma_client()
    chroma_status = await run_in_threadpool(_check_chroma, client)
    knowledge_docs_status = await run_in_threadpool(
        _check_collection, client, KNOWLEDGE_COLLECTION_NAME
    )
    run_summaries_status = await run_in_threadpool(
        _check_collection, client, RUN_SUMMARY_COLLECTION_NAME
    )
    llm_status = _check_llm_provider()  # pure config read, no I/O — safe to call directly

    overall_status = (
        "degraded"
        if database_status.status == "error" or chroma_status.status == "error"
        else "ok"
    )

    return HealthResponse(
        status=overall_status,
        database=database_status,
        chroma=chroma_status,
        knowledge_docs=knowledge_docs_status,
        run_summaries=run_summaries_status,
        llm_provider=llm_status,
    )