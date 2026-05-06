"""
Модульные тесты для роутера indicators.
Используют моки сервисов для изоляции от БД.
"""

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from contracts.service_protocols import IndicatorsServiceProtocol
from dependencies import get_indicators_service
from httpx import AsyncClient

from fastapi import FastAPI
from routers.indicators import router


class TestIndicatorsRouter:
    """Тесты для роутера indicators."""

    @pytest.fixture
    def mock_service(self):
        """Мок сервиса."""
        return AsyncMock(spec=IndicatorsServiceProtocol)

    @pytest.fixture
    def app(self, mock_service):
        """Создает FastAPI приложение с моком сервиса."""
        app = FastAPI()
        app.include_router(router)

        def override_get_indicators_service():
            return mock_service

        app.dependency_overrides[get_indicators_service] = (
            override_get_indicators_service
        )
        return app

    @pytest_asyncio.fixture
    async def client(self, app):
        """Асинхронный тестовый клиент."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_indicators_autocomplete(self, client, mock_service):
        """Тест автодополнения индикаторов."""
        mock_service.get_indicators_autocomplete.return_value = {
            "indicators": [
                {"indicator_id": "id1", "indicator_name": "Indicator A"}
            ],
            "total": 1,
        }

        response = await client.get(
            "/alerts/api/v1/indicators/autocomplete?query=test&limit=10"
        )

        assert response.status_code == 200
        assert response.json()["total"] == 1
        mock_service.get_indicators_autocomplete.assert_called_once_with(
            "test", 10
        )

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_indicators_autocomplete_without_query(
        self, client, mock_service
    ):
        """Тест автодополнения индикаторов без query."""
        mock_service.get_indicators_autocomplete.return_value = {
            "indicators": [],
            "total": 0,
        }

        response = await client.get(
            "/alerts/api/v1/indicators/autocomplete?limit=20"
        )

        assert response.status_code == 200
        assert response.json()["total"] == 0
        mock_service.get_indicators_autocomplete.assert_called_once_with(
            None, 20
        )

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_indicators_autocomplete_default_limit(
        self, client, mock_service
    ):
        """Тест автодополнения индикаторов с дефолтным limit."""
        mock_service.get_indicators_autocomplete.return_value = {
            "indicators": [],
            "total": 0,
        }

        response = await client.get(
            "/alerts/api/v1/indicators/autocomplete?query=test"
        )

        assert response.status_code == 200
        mock_service.get_indicators_autocomplete.assert_called_once_with(
            "test", 10
        )
