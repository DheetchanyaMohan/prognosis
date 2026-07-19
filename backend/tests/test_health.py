from __future__ import annotations

import httpx
import pytest

from app.api.routes import health as health_module


async def test_health_returns_200(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/health")
    assert response.status_code == 200


async def test_health_reports_database_ok(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/health")
    body = response.json()
    assert body["database"]["status"] == "ok"


async def test_health_reports_overall_ok_when_database_and_chroma_healthy(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.get("/health")
    body = response.json()
    assert body["status"] == "ok"


async def test_health_response_shape(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/health")
    body = response.json()
    assert set(body.keys()) == {"status", "database", "chroma", "llm_provider"}
    for component in ("database", "chroma", "llm_provider"):
        assert "status" in body[component]
        assert "detail" in body[component]


# --- _check_database -----------------------------------------------------


def test_check_database_reports_error_on_failure() -> None:
    class BrokenSession:
        def execute(self, *args: object, **kwargs: object) -> None:
            raise RuntimeError("connection refused")

    result = health_module._check_database(BrokenSession())  # type: ignore[arg-type]
    assert result.status == "error"
    assert "connection refused" in (result.detail or "")


# --- _check_llm_provider ---------------------------------------------------


def test_check_llm_provider_not_configured_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")

    result = health_module._check_llm_provider()
    assert result.status == "not_configured"
    get_settings.cache_clear()


def test_check_llm_provider_ok_with_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")

    result = health_module._check_llm_provider()
    assert result.status == "ok"
    get_settings.cache_clear()


def test_check_llm_provider_unknown_provider_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("LLM_PROVIDER", "some_unsupported_provider")

    result = health_module._check_llm_provider()
    assert result.status == "error"
    get_settings.cache_clear()