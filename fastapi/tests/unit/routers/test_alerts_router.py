"""
Модульные тесты для роутера alerts.
Используют моки сервисов для изоляции от БД.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from contracts.service_protocols import (
    AlertsServiceProtocol,
    PausesServiceProtocol,
)
from dependencies import get_alerts_service, get_pauses_service
from fastapi import FastAPI
from httpx import AsyncClient

from routers.alerts import duplicate_router, router
from schemas.alerts import (
    AlertAutocompleteResponse,
    AlertDetail,
    AlertListResponse,
    TagCloudResponse,
)


class TestAlertsRouter:
    """Тесты для роутера alerts."""

    @pytest.fixture
    def mock_service(self):
        """Мок сервиса."""
        return AsyncMock(spec=AlertsServiceProtocol)

    @pytest.fixture
    def mock_pauses_service(self):
        """Мок сервиса пауз."""
        return AsyncMock(spec=PausesServiceProtocol)

    @pytest.fixture
    def app(self, mock_service, mock_pauses_service):
        """Создает FastAPI приложение с моком сервиса."""
        app = FastAPI()
        app.include_router(router)
        app.include_router(duplicate_router)

        # Переопределяем dependency для тестов
        def override_get_alerts_service():
            return mock_service

        def override_get_pauses_service():
            return mock_pauses_service

        app.dependency_overrides[get_alerts_service] = (
            override_get_alerts_service
        )
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
    async def test_search_alerts(self, client, mock_service):
        """Тест поиска алертов."""
        alert_id = uuid4()
        mock_service.search_alerts.return_value = AlertListResponse(
            alerts=[
                {
                    "alert_id": alert_id,
                    "alert_name": "test_alert",
                    "indicator_name": "test_indicator",
                    "paused": False,
                }
            ],
            total=1,
        )

        response = await client.get("/alerts/api/v1/alerts/search?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_get_alert_detail(self, client, mock_service):
        """Тест получения деталей алерта."""
        alert_id = uuid4()
        mock_service.get_alert_detail.return_value = AlertDetail(
            alert_id=alert_id,
            alert_name="test_alert",
            indicator={"indicator_id": uuid4(), "indicator_name": "test"},
        )

        response = await client.get(
            f"/alerts/api/v1/alerts/detail?alert_id={alert_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["alert_id"] == str(alert_id)

    @pytest.mark.asyncio
    async def test_create_alert(self, client, mock_service):
        """Тест создания алерта."""
        mock_service.create_alert.return_value = True

        data = {
            "alert_name": "test_alert",
            "indicator_id": str(uuid4()),
            "description": "test",
            "image": "test.jpg",
            "group_rule_id": str(uuid4()),
        }

        response = await client.post("/alerts/api/v1/alerts/detail", json=data)

        assert response.status_code == 200
        assert response.json() is True

    @pytest.mark.asyncio
    async def test_update_alert(self, client, mock_service):
        """Тест обновления алерта."""
        alert_id = uuid4()
        mock_service.update_alert.return_value = True

        data = {"alert_id": str(alert_id), "alert_name": "updated_alert"}

        response = await client.patch(
            "/alerts/api/v1/alerts/detail", json=data
        )

        assert response.status_code == 200
        assert response.json() is True

    @pytest.mark.asyncio
    async def test_delete_alert(self, client, mock_service):
        """Тест удаления алерта."""
        alert_id = uuid4()
        mock_service.delete_alert.return_value = True

        response = await client.delete(
            f"/alerts/api/v1/alerts/detail?alert_id={alert_id}"
        )

        assert response.status_code == 200
        assert response.json() is True
        mock_service.delete_alert.assert_called_once_with(alert_id)

    @pytest.mark.asyncio
    async def test_autocomplete_alerts(self, client, mock_service):
        """Тест автодополнения алертов."""
        alert_id = uuid4()
        mock_service.autocomplete_alerts.return_value = (
            AlertAutocompleteResponse(
                alerts=[{"alert_id": alert_id, "alert_name": "test_alert"}],
                total=1,
            )
        )

        response = await client.get(
            "/alerts/api/v1/alerts/autocomplete?query=test&limit=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["alerts"]) == 1
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_get_tag_cloud(self, client, mock_service):
        """Тест получения облака тегов."""
        mock_service.get_tag_cloud.return_value = TagCloudResponse(
            tags=["tag1", "tag2"], total=2
        )

        response = await client.get("/alerts/api/v1/alerts/tags/cloud")

        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == 2
        assert data["total"] == 2
        mock_service.get_tag_cloud.assert_called_once_with(
            alert_name=None, tags=None
        )

    @pytest.mark.asyncio
    async def test_get_tag_cloud_with_filters(self, client, mock_service):
        """Тест облака тегов с фильтрацией по alert_name и tags (AND)."""
        mock_service.get_tag_cloud.return_value = TagCloudResponse(
            tags=["api"], total=1
        )

        response = await client.get(
            "/alerts/api/v1/alerts/tags/cloud",
            params={"alert_name": "CDI", "tags": "cdi,api"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == ["api"]
        assert data["total"] == 1
        mock_service.get_tag_cloud.assert_called_once_with(
            alert_name="CDI", tags="cdi,api"
        )

    @pytest.mark.asyncio
    async def test_duplicate_alert(self, client, mock_service):
        """Тест дублирования алерта."""
        alert_id = uuid4()
        mock_service.duplicate_alert.return_value = True

        response = await client.post(f"/alerts/api/v1/{alert_id}/duplicate")

        assert response.status_code == 200
        assert response.json() is True
        mock_service.duplicate_alert.assert_called_once_with(alert_id)

    @pytest.mark.asyncio
    async def test_toggle_alert_pause(self, client, mock_pauses_service):
        """Тест переключения паузы алерта."""
        mock_pauses_service.toggle_alert_pause.return_value = True

        data = {
            "alert_id": str(uuid4()),
            "login": "test_user",
            "comment": "pause reason",
        }

        response = await client.patch("/alerts/api/v1/alerts/pause", json=data)

        assert response.status_code == 200
        assert response.json() is True
        mock_pauses_service.toggle_alert_pause.assert_called_once()
        assert (
            mock_pauses_service.toggle_alert_pause.call_args.args[2]
            == "pause reason"
        )

    @pytest.mark.asyncio
    async def test_search_alerts_with_tags(self, client, mock_service):
        """Тест поиска алертов с тегами."""
        mock_service.search_alerts.return_value = AlertListResponse(
            alerts=[], total=0
        )

        response = await client.get(
            "/alerts/api/v1/alerts/search?tags=tag1,tag2&limit=10"
        )

        assert response.status_code == 200
        mock_service.search_alerts.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_alerts_invalid_order_by(self, client, mock_service):
        """Тест поиска алертов с неверным order_by."""
        response = await client.get(
            "/alerts/api/v1/alerts/search?order_by=invalid_field"
        )

        # Pydantic валидация возвращает 422 (Unprocessable Entity)
        assert response.status_code == 422
        detail = response.json()["detail"]
        # Проверяем что есть ошибка валидации для order_by
        assert any("order_by" in str(err).lower() for err in detail)

    @pytest.mark.asyncio
    async def test_search_alerts_invalid_order_dir(self, client, mock_service):
        """Тест поиска алертов с неверным order_dir."""
        response = await client.get(
            "/alerts/api/v1/alerts/search?order_dir=invalid"
        )

        # Pydantic валидация возвращает 422 (Unprocessable Entity)
        assert response.status_code == 422
        detail = response.json()["detail"]
        # Проверяем что есть ошибка валидации для order_dir
        assert any("order_dir" in str(err).lower() for err in detail)

    @pytest.mark.asyncio
    async def test_autocomplete_alerts_without_query(
        self, client, mock_service
    ):
        """Тест автодополнения алертов без query."""
        mock_service.autocomplete_alerts.return_value = (
            AlertAutocompleteResponse(alerts=[], total=0)
        )

        response = await client.get(
            "/alerts/api/v1/alerts/autocomplete?limit=20"
        )

        assert response.status_code == 200
        mock_service.autocomplete_alerts.assert_called_once_with(None, 20)
