"""Diagnosis route.

The one route in this project that invokes the LangGraph agent. It does
no orchestration of its own — app.services.diagnosis_service.run_diagnosis
is the single implementation of "run the workflow and shape its output,"
shared unchanged with scripts/validate_agent.py. This module's only job
is the HTTP-specific part: resolving the request body, calling the
service in a threadpool (an LLM call is blocking I/O, same reasoning as
every other route in this project), and translating the service's
exceptions into status codes.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from app.api.schemas import DiagnoseRequest
from app.llm import LLMProviderError, StructuredOutputError
from app.services import DiagnosisResponse, run_diagnosis
from app.tools.experiment_tool import RunNotFoundError

router = APIRouter(tags=["diagnosis"])


@router.post("/runs/{run_id}/diagnose", response_model=DiagnosisResponse)
async def diagnose_run(run_id: str, request: DiagnoseRequest | None = None) -> DiagnosisResponse:
    query = request.query if request is not None else None

    try:
        return await run_in_threadpool(run_diagnosis, run_id, query)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(
            status_code=502, detail=f"LLM provider unavailable or failed: {exc}"
        ) from exc
    except StructuredOutputError as exc:
        raise HTTPException(
            status_code=502, detail=f"LLM returned malformed structured output: {exc}"
        ) from exc
    except Exception as exc:  # noqa: BLE001 - last-resort translation to a clean 500
        raise HTTPException(
            status_code=500, detail=f"Diagnosis workflow failed: {exc}"
        ) from exc