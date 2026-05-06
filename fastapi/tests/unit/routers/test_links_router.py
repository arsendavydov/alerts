"""
Модульные тесты для роутера links.
Используют моки сервисов для изоляции от БД.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from contracts.service_protocols import LinksServiceProtocol
from dependencies import get_links_service
from httpx import AsyncClient

from fastapi import FastAPI
from routers.links import router
from schemas.links import (
    LinkByAlertListItem,
    LinkByAlertListResponse,
    LinkDetail,
    LinkDetailCreate,
    LinkDetailUpdate,
)


class TestLinksRouter:
    """Тесты для роутера links."""

    @pytest.fixture
    def mock_service(self):
        """Мок сервиса."""
        return AsyncMock(spec=LinksServiceProtocol)

    @pytest.fixture
    def app(self, mock_service):
        """Создает FastAPI приложение с моком сервиса."""
        app = FastAPI()
        app.include_router(router)

        def override_get_links_service():
            return mock_service

        app.dependency_overrides[get_links_service] = (
            override_get_links_service
        )
        return app

    @pytest_asyncio.fixture
    async def client(self, app):
        """Асинхронный тестовый клиент."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_get_links_by_alert(self, client, mock_service):
        """Тест получения линков по алерту."""
        alert_id = uuid4()
        mock_service.get_links_by_alert.return_value = LinkByAlertListResponse(
            links=[
                LinkByAlertListItem(
                    link_id=uuid4(),
                    link_name="Link 1",
                    link_url="http://link1.com",
                )
            ],
            total=1,
        )

        response = await client.get(
            f"/alerts/api/v1/links/by_alert?alert_id={alert_id}"
        )

        assert response.status_code == 200
        assert response.json()["total"] == 1
        mock_service.get_links_by_alert.assert_called_once_with(alert_id)

    @pytest.mark.asyncio
    async def test_get_link_detail(self, client, mock_service):
        """Тест получения деталей линка."""
        link_id = uuid4()
        alert_id = uuid4()
        mock_service.get_link_detail.return_value = LinkDetail(
            link_id=link_id,
            alert_id=alert_id,
            alert_name="Test Alert",
            link_name="Test Link",
            link_url="http://test.com",
        )

        response = await client.get(
            f"/alerts/api/v1/links/detail?link_id={link_id}"
        )

        assert response.status_code == 200
        assert response.json()["link_id"] == str(link_id)
        mock_service.get_link_detail.assert_called_once_with(link_id)

    @pytest.mark.asyncio
    async def test_create_link_detail(self, client, mock_service):
        """Тест создания линка."""
        alert_id = uuid4()
        data = LinkDetailCreate(
            alert_id=alert_id, link_name="New Link", link_url="http://new.com"
        )
        mock_service.create_link.return_value = True

        response = await client.post(
            "/alerts/api/v1/links/detail", json=data.model_dump(mode="json")
        )

        assert response.status_code == 200
        assert response.json() is True
        mock_service.create_link.assert_called_once()

    @pytest.mark.asyncio
    async def test_patch_link_detail(self, client, mock_service):
        """Тест обновления линка."""
        link_id = uuid4()
        data = LinkDetailUpdate(link_id=link_id, link_name="Updated Link")
        mock_service.update_link.return_value = True

        response = await client.patch(
            "/alerts/api/v1/links/detail",
            json=data.model_dump(mode="json", exclude_none=True),
        )

        assert response.status_code == 200
        assert response.json() is True
        mock_service.update_link.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_link_detail(self, client, mock_service):
        """Тест удаления линка."""
        link_id = uuid4()
        mock_service.delete_link.return_value = True

        response = await client.delete(
            f"/alerts/api/v1/links/detail?link_id={link_id}"
        )

        assert response.status_code == 200
        assert response.json() is True
        mock_service.delete_link.assert_called_once_with(link_id)
