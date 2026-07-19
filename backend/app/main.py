"""FastAPI application entrypoint.

This module only assembles the app: settings, logging, middleware, and
router registration. Route logic itself lives under app/api/routes.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import experiments, health
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

    # Health check is unprefixed (conventional for load balancer / k8s probes);
    # resource routes live under the versioned API prefix.
    app.include_router(health.router)
    app.include_router(experiments.router, prefix=settings.api_v1_prefix)

    return app


app = create_app()