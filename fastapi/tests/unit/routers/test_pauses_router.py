"""
Модульные тесты для роутера pauses.
Используют моки сервисов для изоляции от БД.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from contracts.service_protocols import PausesServiceProtocol
from dependencies import get_pauses_service
from fastapi import FastAPI
from httpx import AsyncClient

from routers.pauses import router
from schemas.pauses import (
    AlertPauseRemoveRequest,
    AlertPauseScheduleRequest,
    AlertPauseUpdateRequest,
    PauseHistoryItem,
    PauseHistoryResponse,
)


class TestPausesRouter:
    """Тесты для роутера pauses."""

    @pytest.fixture
    def mock_service(self):
        """Мок сервиса."""
        return AsyncMock(spec=PausesServiceProtocol)

    @pytest.fixture
    def app(self, mock_service):
        """Создает FastAPI приложение с моком сервиса."""
        app = FastAPI()
        app.include_router(router)

        def override_get_pauses_service():
            return mock_service

        app.dependency_overrides[get_pauses_service] = (
            override_get_pauses_service
        )
        return app

    @pytest_asyncio.fixture
    async def client(self, app):
        """Асинхронный тестовый клиент."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_alert_pauses(self, client, mock_service):
        """Тест получения истории пауз."""
        alert_id = uuid4()
        mock_service.get_alert_pauses.return_value = PauseHistoryResponse(
            pauses=[
                PauseHistoryItem(
                    pause_id=uuid4(),
                    start_time=datetime.now(timezone.utc),
                    end_time=None,
                    start_user="user1",
                    end_user=None,
                )
            ],
            total=1,
        )

        response = await client.get(f"/alerts/api/v1/alerts/{alert_id}/pause")

        assert response.status_code == 200
        assert response.json()["total"] == 1
        mock_service.get_alert_pauses.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_create_alert_pause(self, client, mock_service):
        """Тест создания паузы (алиас)."""
        alert_id = uuid4()
        data = AlertPauseScheduleRequest(login="user1", comment="router create")
        mock_service.schedule_alert_pause.return_value = True

        response = await client.post(
            f"/alerts/api/v1/alerts/{alert_id}/pause",
            json=data.model_dump(exclude_none=True),
        )

        assert response.status_code == 200
        assert response.json() is True
        mock_service.schedule_alert_pause.assert_called_once()

    @pytest.mark.asyncio
    async def test_schedule_alert_pause(self, client, mock_service):
        """Тест установки паузы."""
        alert_id = uuid4()
        data = AlertPauseScheduleRequest(
            login="user1",
            start_time="2026-01-01T10:00:00+03:00",
            end_time="2026-01-01T18:00:00+03:00",
        )
        mock_service.schedule_alert_pause.return_value = True

        response = await client.post(
            f"/alerts/api/v1/alerts/{alert_id}/pause/schedule",
            json=data.model_dump(mode="json", exclude_none=True),
        )

        assert response.status_code == 200
        assert response.json() is True
        mock_service.schedule_alert_pause.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_alert_pause(self, client, mock_service):
        """Тест остановки всех активных пауз."""
        alert_id = uuid4()
        data = AlertPauseRemoveRequest(login="user1", comment="router stop all")
        mock_service.stop_alert_pause.return_value = True

        response = await client.patch(
            f"/alerts/api/v1/alerts/{alert_id}/pause/stop",
            json=data.model_dump(),
        )

        assert response.status_code == 200
        assert response.json() is True
        mock_service.stop_alert_pause.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_alert_pause(self, client, mock_service):
        """Тест обновления паузы."""
        alert_id = uuid4()
        pause_id = uuid4()
        data = AlertPauseUpdateRequest(
            login="user1", start_time="2026-01-01T10:00:00+03:00"
        )
        mock_service.update_alert_pause.return_value = True

        response = await client.patch(
            f"/alerts/api/v1/alerts/{alert_id}/pause/{pause_id}",
            json=data.model_dump(mode="json", exclude_none=True),
        )

        assert response.status_code == 200
        assert response.json() is True
        mock_service.update_alert_pause.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_stop_specific_alert_pause(self, client, mock_service):
        """Тест остановки конкретной паузы."""
        alert_id = uuid4()
        pause_id = uuid4()
        data = AlertPauseRemoveRequest(
            login="user1", comment="router stop one"
        )
        mock_service.stop_specific_alert_pause.return_value = True

        response = await client.patch(
            f"/alerts/api/v1/alerts/{alert_id}/pause/{pause_id}/stop",
            json=data.model_dump(),
        )

        assert response.status_code == 200
        assert response.json() is True
        mock_service.stop_specific_alert_pause.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_delete_alert_pause(self, client, mock_service):
        """Тест удаления паузы."""
        alert_id = uuid4()
        pause_id = uuid4()
        mock_service.delete_alert_pause.return_value = True

        response = await client.delete(
            f"/alerts/api/v1/alerts/{alert_id}/pause/{pause_id}"
        )

        assert response.status_code == 200
        assert response.json() is True
        mock_service.delete_alert_pause.assert_called_once()
