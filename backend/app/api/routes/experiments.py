"""Experiment and run routes.

Every handler resolves its data through app.tools — the same
abstraction boundary LangGraph nodes use — so no route touches
SQLAlchemy or a raw file path except through app.tools.experiment_tool's
RunArtifactPaths lookup, and even then only to hand the path to the same
loaders (app.config.loader, app.tools.metrics_analysis) everything else
in the project already uses.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import DbSession
from app.api.schemas import RunDetailResponse, RunSummaryResponse
from app.config.loader import load_run_config
from app.tools import experiment_tool
from app.tools.experiment_tool import ExperimentNotFoundError, RunNotFoundError
from app.tools.metrics_analysis import load_diagnostics
from app.tools.schemas import ExperimentRecord, RunArtifactPaths

router = APIRouter(tags=["experiments"])


@router.get("/experiments", response_model=list[ExperimentRecord])
async def list_experiments(db: DbSession) -> list[ExperimentRecord]:
    return await run_in_threadpool(experiment_tool.list_experiments, db)


@router.get("/experiments/{experiment_id}", response_model=ExperimentRecord)
async def get_experiment(experiment_id: str, db: DbSession) -> ExperimentRecord:
    """`experiment_id` is the experiment's name (e.g.
    'exp_001_cifar10_subset_study') — the same identifier used
    everywhere else in the project, not a separate numeric ID."""
    try:
        return await run_in_threadpool(experiment_tool.load_experiment, experiment_id, db)
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _load_summary(summary_path: str) -> RunSummaryResponse | None:
    path = Path(summary_path)
    if not path.exists():
        return None
    return RunSummaryResponse.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _load_run_detail(paths: RunArtifactPaths) -> RunDetailResponse:
    config_path = Path(paths.config_path)
    if not config_path.exists():
        raise HTTPException(
            status_code=500, detail=f"Run {paths.run_id!r} is missing its config.yaml on disk"
        )

    config = load_run_config(config_path)
    summary = _load_summary(paths.summary_path)

    diagnostics_path = Path(paths.diagnostics_path)
    diagnostics = load_diagnostics(diagnostics_path) if diagnostics_path.exists() else None

    return RunDetailResponse(
        run_id=paths.run_id, config=config, summary=summary, diagnostics=diagnostics
    )


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
async def get_run_detail(run_id: str, db: DbSession) -> RunDetailResponse:
    try:
        paths = await run_in_threadpool(experiment_tool.get_run_artifact_paths, run_id, db)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return await run_in_threadpool(_load_run_detail, paths)