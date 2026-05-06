"""
Модульные тесты для alerts.py (main FastAPI приложение).
"""

import runpy
import sys
from types import ModuleType

import pytest
import pytest_asyncio
from alerts import app, lifespan
from httpx import AsyncClient


class TestAlertsMain:
    """Тесты для главного приложения."""

    @pytest_asyncio.fixture
    async def client(self):
        """Асинхронный тестовый клиент."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Тест health endpoint."""
        response = await client.get("/alerts/health")
        assert response.status_code == 200
        assert response.text == "OK"
        assert "X-Correlation-ID" in response.headers

    @pytest.mark.asyncio
    async def test_openapi_endpoint(self, client):
        """Тест OpenAPI endpoint."""
        response = await client.get("/alerts/openapi.json")
        assert response.status_code == 200
        assert "openapi" in response.json()

    @pytest.mark.asyncio
    async def test_docs_endpoint(self, client):
        """Тест docs endpoint."""
        response = await client.get("/alerts/docs")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_redoc_endpoint(self, client):
        """Тест redoc endpoint."""
        response = await client.get("/alerts/redoc")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_lifespan_context_is_enterable(self):
        """Проверка, что lifespan-контекст корректно открывается/закрывается."""
        async with lifespan(app):
            assert True

    def test_main_block_runs_uvicorn(self, monkeypatch):
        """Проверка запуска uvicorn в __main__ ветке."""
        fake_uvicorn = ModuleType("uvicorn")
        called: dict[str, object] = {}

        def fake_run(application, host, port):
            called["application"] = application
            called["host"] = host
            called["port"] = port

        fake_uvicorn.__dict__["run"] = fake_run
        monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)

        runpy.run_module("alerts", run_name="__main__")

        assert called["host"] == "127.0.0.1"
        assert called["port"] == 8888
        assert called["application"] is not None
