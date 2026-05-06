"""
Модульные тесты для роутера dt.
Используют моки сервисов для изоляции от БД.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from contracts.service_protocols import DTServiceProtocol
from dependencies import get_dt_service
from httpx import AsyncClient

from fastapi import FastAPI
from routers.dt import router
from schemas.dt import DTDetail, DTDetailCreate, DTDetailUpdate


class TestDTRouter:
    """Тесты для роутера dt."""

    @pytest.fixture
    def mock_service(self):
        """Мок сервиса."""
        return AsyncMock(spec=DTServiceProtocol)

    @pytest.fixture
    def app(self, mock_service):
        """Создает FastAPI приложение с моком сервиса."""
        app = FastAPI()
        app.include_router(router)

        def override_get_dt_service():
            return mock_service

        app.dependency_overrides[get_dt_service] = override_get_dt_service
        return app

    @pytest_asyncio.fixture
    async def client(self, app):
        """Асинхронный тестовый клиент."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_get_dt(self, client, mock_service):
        """Тест получения DT."""
        alert_id = uuid4()
        dt_id = uuid4()
        mock_service.get_dt.return_value = DTDetail(
            dt_id=dt_id,
            alert_id=alert_id,
            content={"key": "value"},
            auto_create=True,
            silence_time={"time": "1h"},
        )

        response = await client.get(f"/alerts/api/v1/alert/{alert_id}/dt")

        assert response.status_code == 200
        assert response.json()["dt_id"] == str(dt_id)
        mock_service.get_dt.assert_called_once_with(alert_id)

    @pytest.mark.asyncio
    async def test_create_dt(self, client, mock_service):
        """Тест создания DT."""
        alert_id = uuid4()
        data = DTDetailCreate(content='{"key": "value"}', auto_create=True)
        mock_service.create_dt.return_value = True

        response = await client.post(
            f"/alerts/api/v1/alert/{alert_id}/dt", json=data.model_dump()
        )

        assert response.status_code == 200
        assert response.json() is True
        mock_service.create_dt.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_dt(self, client, mock_service):
        """Тест обновления DT."""
        alert_id = uuid4()
        data = DTDetailUpdate(content='{"key": "updated"}')
        mock_service.update_dt.return_value = True

        response = await client.patch(
            f"/alerts/api/v1/alert/{alert_id}/dt",
            json=data.model_dump(exclude_none=True),
        )

        assert response.status_code == 200
        assert response.json() is True
        mock_service.update_dt.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_dt(self, client, mock_service):
        """Тест удаления DT."""
        alert_id = uuid4()
        mock_service.delete_dt.return_value = True

        response = await client.delete(f"/alerts/api/v1/alert/{alert_id}/dt")

        assert response.status_code == 200
        assert response.json() is True
        mock_service.delete_dt.assert_called_once_with(alert_id)
