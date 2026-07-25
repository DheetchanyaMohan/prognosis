from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

import app.api.routes.diagnosis as diagnosis_route_module
from app.llm import Hypothesis, LLMProviderError, Recommendation, StructuredOutputError
from app.services import DiagnosisResponse
from app.tools.experiment_tool import RunNotFoundError


def _fake_response(run_id: str = "run_005") -> DiagnosisResponse:
    return DiagnosisResponse(
        run_id=run_id,
        generated_at=datetime.now(UTC),
        user_query=(
            f"Why did {run_id} behave the way it did during training, "
            "and what should I try next?"
        ),
        request_type="diagnose_run",
        selected_run=run_id,
        comparison_run=None,
        retrieved_knowledge=[],
        similar_runs=[],
        diagnostics=None,
        run_summary=None,
        comparison=None,
        hypotheses=[
            Hypothesis(
                title="Overfitting", explanation="Gap widening",
                supporting_evidence=["x"], confidence=0.8,
            )
        ],
        recommendations=[
            Recommendation(
                title="Add dropout", rationale="x", supporting_evidence=["e"],
                expected_benefit="b", estimated_effort="low", confidence=0.8,
                provenance=["diagnostics:generalization_gap"],
            )
        ],
        retry_count=0,
        needs_more_evidence=False,
        trace=[],
    )


def _patch_run_diagnosis(monkeypatch: pytest.MonkeyPatch, effect: Any) -> None:
    def fake_run_diagnosis(run_id: str, query: str | None = None) -> DiagnosisResponse:
        if isinstance(effect, Exception):
            raise effect
        return effect

    monkeypatch.setattr(diagnosis_route_module, "run_diagnosis", fake_run_diagnosis)


# --- success --------------------------------------------------------------


async def test_diagnose_run_success(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_run_diagnosis(monkeypatch, _fake_response("run_005"))

    response = await api_client.post("/api/v1/runs/run_005/diagnose")

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == "run_005"
    assert body["request_type"] == "diagnose_run"
    assert len(body["hypotheses"]) == 1
    assert body["hypotheses"][0]["title"] == "Overfitting"
    assert len(body["recommendations"]) == 1


async def test_diagnose_run_accepts_empty_body(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_run_diagnosis(run_id: str, query: str | None = None) -> DiagnosisResponse:
        captured["run_id"] = run_id
        captured["query"] = query
        return _fake_response(run_id)

    monkeypatch.setattr(diagnosis_route_module, "run_diagnosis", fake_run_diagnosis)

    response = await api_client.post("/api/v1/runs/run_005/diagnose")

    assert response.status_code == 200
    assert captured["run_id"] == "run_005"
    assert captured["query"] is None


async def test_diagnose_run_forwards_custom_query(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_run_diagnosis(run_id: str, query: str | None = None) -> DiagnosisResponse:
        captured["query"] = query
        return _fake_response(run_id)

    monkeypatch.setattr(diagnosis_route_module, "run_diagnosis", fake_run_diagnosis)

    response = await api_client.post(
        "/api/v1/runs/run_005/diagnose", json={"query": "compare run_005 and run_004"}
    )

    assert response.status_code == 200
    assert captured["query"] == "compare run_005 and run_004"


async def test_diagnose_run_rejects_unknown_body_fields(api_client: httpx.AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/runs/run_005/diagnose", json={"not_a_real_field": "x"}
    )
    assert response.status_code == 422


# --- error translation ------------------------------------------------------


async def test_diagnose_run_not_found_returns_404(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_run_diagnosis(monkeypatch, RunNotFoundError("No run found with run_id='run_999'"))

    response = await api_client.post("/api/v1/runs/run_999/diagnose")

    assert response.status_code == 404
    assert "run_999" in response.json()["detail"]


async def test_diagnose_run_llm_provider_error_returns_502(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_run_diagnosis(monkeypatch, LLMProviderError("provider is down"))

    response = await api_client.post("/api/v1/runs/run_005/diagnose")

    assert response.status_code == 502
    assert "provider is down" in response.json()["detail"]


async def test_diagnose_run_structured_output_error_returns_502(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_run_diagnosis(monkeypatch, StructuredOutputError("bad json"))

    response = await api_client.post("/api/v1/runs/run_005/diagnose")

    assert response.status_code == 502
    assert "bad json" in response.json()["detail"]


async def test_diagnose_run_unexpected_error_returns_500(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_run_diagnosis(monkeypatch, RuntimeError("something broke"))

    response = await api_client.post("/api/v1/runs/run_005/diagnose")

    assert response.status_code == 500
    assert "something broke" in response.json()["detail"]


# --- OpenAPI registration ----------------------------------------------


async def test_diagnose_route_registered_in_openapi(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    path_item = schema["paths"].get("/api/v1/runs/{run_id}/diagnose")
    assert path_item is not None
    assert "post" in path_item

    post_spec = path_item["post"]
    assert post_spec["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "DiagnosisResponse"
    )


async def test_diagnosis_response_schema_registered_in_openapi(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.get("/openapi.json")
    schema = response.json()

    diagnosis_schema = schema["components"]["schemas"]["DiagnosisResponse"]
    for field in (
        "run_id", "request_type", "selected_run", "comparison_run",
        "retrieved_knowledge", "similar_runs", "diagnostics", "run_summary",
        "comparison", "hypotheses", "recommendations", "trace",
    ):
        assert field in diagnosis_schema["properties"], f"missing field: {field}"