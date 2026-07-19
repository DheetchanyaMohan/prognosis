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
    except Exception as exc:  # noqa: BLE001
        return HealthComponentStatus(status="error", detail=str(exc))
    return HealthComponentStatus(status="ok")


def _check_llm_provider() -> HealthComponentStatus:
    """Configuration check only — never constructs a ChatModel or calls
    the provider. See app.llm.client.get_chat_model for the real client."""
    settings = get_settings()

    if settings.llm_provider != "anthropic":
        return HealthComponentStatus(
            status="error", detail=f"Unknown LLM provider configured: {settings.llm_provider!r}"
        )
    if not settings.anthropic_api_key:
        return HealthComponentStatus(status="not_configured", detail="ANTHROPIC_API_KEY is not set")
    return HealthComponentStatus(status="ok", detail=f"provider={settings.llm_provider}")


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