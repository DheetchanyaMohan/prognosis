"""FastAPI application entrypoint.

This module only assembles the app: settings, logging, middleware, and
router registration. Route logic itself lives under app/api/routes.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import diagnosis, experiments, health
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()

from pathlib import Path

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    chroma = Path("/app/data/chroma")

    print("\n===== STARTUP =====")

    print("sqlite exists:", (chroma / "chroma.sqlite3").exists())

    if (chroma / "chroma.sqlite3").exists():
        print("sqlite size:", (chroma / "chroma.sqlite3").stat().st_size)

    print("contents:")
    for p in sorted(chroma.iterdir()):
        print(" ", p.name)

    print("===================\n")

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

    # Health check is unprefixed (conventional for load balancer / k8s probes);
    # resource routes live under the versioned API prefix.
    app.include_router(health.router)
    app.include_router(experiments.router, prefix=settings.api_v1_prefix)
    app.include_router(diagnosis.router, prefix=settings.api_v1_prefix)

    return app

app = create_app()