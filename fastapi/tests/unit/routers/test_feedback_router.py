"""
Модульные тесты для роутера feedback.
Используют моки сервисов для изоляции от БД.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from contracts.service_protocols import FeedbackServiceProtocol
from dependencies import get_feedback_service
from httpx import AsyncClient

from fastapi import FastAPI
from routers.feedback import router
from schemas.feedback import FeedbackCreate, FeedbackDelete, FeedbackResponse


class TestFeedbackRouter:
    """Тесты для роутера feedback."""

    @pytest.fixture
    def mock_service(self):
        """Мок сервиса."""
        return AsyncMock(spec=FeedbackServiceProtocol)

    @pytest.fixture
    def app(self, mock_service):
        """Создает FastAPI приложение с моком сервиса."""
        app = FastAPI()
        app.include_router(router)

        def override_get_feedback_service():
            return mock_service

        app.dependency_overrides[get_feedback_service] = (
            override_get_feedback_service
        )
        return app

    @pytest_asyncio.fixture
    async def client(self, app):
        """Асинхронный тестовый клиент."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_create_feedback(self, client, mock_service):
        """Тест создания фидбека."""
        status_history_id = uuid4()
        data = FeedbackCreate(
            status_history=status_history_id, user_fio="test_user", score=5
        )
        mock_service.create_feedback.return_value = FeedbackResponse(
            message="Спасибо за обратную связь!"
        )

        response = await client.post(
            "/alerts/api/v1/feedback/detail", json=data.model_dump(mode="json")
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Спасибо за обратную связь!"
        mock_service.create_feedback.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_feedback(self, client, mock_service):
        """Тест удаления фидбека."""
        status_history_id = uuid4()
        data = FeedbackDelete(
            status_history=status_history_id, user_fio="test_user"
        )
        mock_service.delete_feedback.return_value = True

        # DELETE с Body - используем request() напрямую
        response = await client.request(
            "DELETE",
            "/alerts/api/v1/feedback/detail",
            json=data.model_dump(mode="json"),
        )

        assert response.status_code == 200
        assert response.json() is True
        mock_service.delete_feedback.assert_called_once()
