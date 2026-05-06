"""
Модульные тесты для роутера screenshots.
Используют моки сервисов для изоляции от БД.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from contracts.service_protocols import ScreenshotsServiceProtocol
from dependencies import get_screenshots_service
from httpx import AsyncClient

from fastapi import FastAPI
from routers.screenshots import router
from schemas.screenshots import ScreenshotDetail, ScreenshotSearchResponse


class TestScreenshotsRouter:
    """Тесты для роутера screenshots."""

    @pytest.fixture
    def mock_service(self):
        """Мок сервиса."""
        return AsyncMock(spec=ScreenshotsServiceProtocol)

    @pytest.fixture
    def app(self, mock_service):
        """Создает FastAPI приложение с моком сервиса."""
        app = FastAPI()
        app.include_router(router)

        # Переопределяем dependency для тестов
        def override_get_screenshots_service():
            return mock_service

        app.dependency_overrides[get_screenshots_service] = (
            override_get_screenshots_service
        )
        return app

    @pytest_asyncio.fixture
    async def client(self, app):
        """Асинхронный тестовый клиент."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_search_screenshots(self, client, mock_service):
        """Тест поиска скриншотов."""
        screenshot_id = uuid4()
        mock_service.search_screenshots.return_value = (
            ScreenshotSearchResponse(
                screenshots=[
                    {
                        "screenshot_id": screenshot_id,
                        "name": "test",
                        "description": "test description",
                        "image_data": '{"url": "test.jpg"}',
                    }
                ],
                total=1,
                limit=50,
                offset=0,
            )
        )

        response = await client.get(
            "/alerts/api/v1/screenshots/search?query=test&limit=50&offset=0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["limit"] == 50
        assert data["offset"] == 0
        assert len(data["screenshots"]) == 1

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_search_screenshots_without_query(
        self, client, mock_service
    ):
        """Тест поиска скриншотов без query."""
        screenshot_id = uuid4()
        mock_service.search_screenshots.return_value = (
            ScreenshotSearchResponse(
                screenshots=[
                    {
                        "screenshot_id": screenshot_id,
                        "name": "test",
                        "description": "test description",
                        "image_data": '{"url": "test.jpg"}',
                    }
                ],
                total=1,
                limit=50,
                offset=0,
            )
        )

        response = await client.get(
            "/alerts/api/v1/screenshots/search?limit=50&offset=0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_search_screenshots_with_sorting(self, client, mock_service):
        """Тест поиска скриншотов с сортировкой."""
        screenshot_id = uuid4()
        mock_service.search_screenshots.return_value = (
            ScreenshotSearchResponse(
                screenshots=[
                    {
                        "screenshot_id": screenshot_id,
                        "name": "test",
                        "description": "test description",
                        "image_data": '{"url": "test.jpg"}',
                    }
                ],
                total=1,
                limit=50,
                offset=0,
            )
        )

        response = await client.get(
            "/alerts/api/v1/screenshots/search?order_by=name&order_dir=desc"
        )

        assert response.status_code == 200
        mock_service.search_screenshots.assert_called_once_with(
            query=None, order_by="name", order_dir="desc", limit=1000, offset=0
        )

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_screenshot(self, client, mock_service):
        """Тест получения скриншота по ID."""
        screenshot_id = uuid4()
        mock_service.get_screenshot.return_value = ScreenshotDetail(
            screenshot_id=screenshot_id,
            name="test",
            description="test description",
            image_data='{"url": "test.jpg"}',
        )

        response = await client.get(
            f"/alerts/api/v1/screenshots/{screenshot_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["screenshot_id"] == str(screenshot_id)

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_create_screenshot(self, client, mock_service):
        """Тест создания скриншота."""
        screenshot_id = uuid4()
        mock_service.create_screenshot.return_value = screenshot_id

        data = {
            "name": "test",
            "description": "test description",
            "image_data": '{"url": "test.jpg"}',
        }

        response = await client.post("/alerts/api/v1/screenshots", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["screenshot_id"] == str(screenshot_id)

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_update_screenshot(self, client, mock_service):
        """Тест обновления скриншота."""
        screenshot_id = uuid4()
        mock_service.update_screenshot.return_value = True

        data = {"name": "updated"}

        response = await client.patch(
            f"/alerts/api/v1/screenshots/{screenshot_id}", json=data
        )

        assert response.status_code == 200
        assert response.json() is True

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_delete_screenshot(self, client, mock_service):
        """Тест удаления скриншота."""
        screenshot_id = uuid4()
        mock_service.delete_screenshot.return_value = True

        response = await client.delete(
            f"/alerts/api/v1/screenshots/{screenshot_id}"
        )

        assert response.status_code == 200
        assert response.json() is True
