"""Health check route.

Checks the app's real dependencies — database connectivity, Chroma
reachability, and whether an LLM provider is configured. The LLM check
is configuration-only: it never constructs a chat model or calls the
provider, since a health check should be fast and side-effect-free.
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import DbSession
from app.api.schemas import HealthComponentStatus, HealthResponse
from app.core.config import get_settings
from app.rag.retriever import get_chroma_client

router = APIRouter(tags=["system"])


def _check_database(db: Session) -> HealthComponentStatus:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - report any failure, don't crash the health check
        return HealthComponentStatus(status="error", detail=str(exc))
    return HealthComponentStatus(status="ok")


def _check_chroma() -> HealthComponentStatus:
    try:
        client = get_chroma_client()
        client.heartbeat()

        from app.rag.retriever import (
            CHROMA_PERSIST_DIR,
            KNOWLEDGE_COLLECTION_NAME,
            RUN_SUMMARY_COLLECTION_NAME,
        )

        counts = {}
        for name in (KNOWLEDGE_COLLECTION_NAME, RUN_SUMMARY_COLLECTION_NAME):
            try:
                counts[name] = client.get_collection(name).count()
            except Exception:  # noqa: BLE001 - collection not existing yet reports as 0
                counts[name] = 0

        # TEMPORARY DIAGNOSTIC — remove once the Railway zero-retrieval
        # issue is root-caused and fixed. Reveals exactly what path and
        # collection state the *actual running container* sees, since
        # `railway run` executes locally against pulled env vars, not
        # inside the real container, and can't answer this question.
        detail = f"persist_dir={CHROMA_PERSIST_DIR} counts={counts}"
    except Exception as exc:  # noqa: BLE001
        return HealthComponentStatus(status="error", detail=str(exc))
    return HealthComponentStatus(status="ok", detail=detail)


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
    chroma_status = await run_in_threadpool(_check_chroma)
    llm_status = _check_llm_provider()  # pure config read, no I/O — safe to call directly

    # An unconfigured LLM provider is a normal dev-time state, not degradation;
    # database/chroma errors mean the app genuinely can't do its job.
    overall_status = (
        "degraded"
        if database_status.status == "error" or chroma_status.status == "error"
        else "ok"
    )

    return HealthResponse(
        status=overall_status,
        database=database_status,
        chroma=chroma_status,
        llm_provider=llm_status,
    )