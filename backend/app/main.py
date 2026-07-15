"""FastAPI application entrypoint.

This module only assembles the app: settings, logging, middleware, and a
health check. Feature routers (experiments, runs, agent, eval) are added
in a later phase under app/api/routes and included here.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    yield


def create_app() -> FastAPI:
    """Application factory. Keeps app construction testable and explicit."""
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        """Liveness check. Does not touch the database or any external service."""
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
