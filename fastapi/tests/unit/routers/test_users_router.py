"""
Модульные тесты для роутера users.
Используют моки сервисов для изоляции от БД.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from contracts.service_protocols import UsersServiceProtocol
from dependencies import get_users_service
from httpx import AsyncClient

from fastapi import FastAPI
from routers.users import router
from schemas.users import (
    TelegramUserResponse,
    UserCreate,
    UserListResponse,
    UserUpdate,
)


class TestUsersRouter:
    """Тесты для роутера users."""

    @pytest.fixture
    def mock_service(self):
        """Мок сервиса."""
        return AsyncMock(spec=UsersServiceProtocol)

    @pytest.fixture
    def app(self, mock_service):
        """Создает FastAPI приложение с моком сервиса."""
        app = FastAPI()
        app.include_router(router)

        def override_get_users_service():
            return mock_service

        app.dependency_overrides[get_users_service] = (
            override_get_users_service
        )
        return app

    @pytest_asyncio.fixture
    async def client(self, app):
        """Асинхронный тестовый клиент."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_get_telegram_by_login(self, client, mock_service):
        """Тест получения Telegram ID по логину."""
        login = "test_user"
        mock_service.get_telegram_by_login.return_value = TelegramUserResponse(
            telegram_id="12345"
        )

        response = await client.get(f"/alerts/api/v1/users/{login}/telegram")

        assert response.status_code == 200
        assert response.json()["telegram_id"] == "12345"
        mock_service.get_telegram_by_login.assert_called_once_with(login)

    @pytest.mark.asyncio
    async def test_search_users(self, client, mock_service):
        """Тест поиска пользователей."""
        mock_service.search_users.return_value = UserListResponse(
            users=[], total=0
        )

        response = await client.get(
            "/alerts/api/v1/users/search",
            params={
                "query": "test",
                "limit": 10,
                "offset": 0,
                "order_by": "samAccountName",
                "order_dir": "asc",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert "users" in body
        assert "total" in body
        mock_service.search_users.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user(self, client, mock_service):
        """Тест создания пользователя."""
        data = UserCreate(samAccountName="test_user", group=False)
        mock_service.create_user.return_value = True

        response = await client.post(
            "/alerts/api/v1/users",
            json=data.model_dump(exclude_none=True),
        )

        assert response.status_code == 200
        assert response.json() is True
        mock_service.create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user(self, client, mock_service):
        """Тест обновления пользователя."""
        user_id = uuid4()
        data = UserUpdate(samAccountName="updated_user")
        mock_service.update_user.return_value = True

        response = await client.patch(
            f"/alerts/api/v1/users/{user_id}",
            json=data.model_dump(exclude_none=True),
        )

        assert response.status_code == 200
        assert response.json() is True
        mock_service.update_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user(self, client, mock_service):
        """Тест удаления пользователя."""
        user_id = uuid4()
        mock_service.delete_user.return_value = True

        response = await client.delete(f"/alerts/api/v1/users/{user_id}")

        assert response.status_code == 200
        assert response.json() is True
        mock_service.delete_user.assert_called_once_with(user_id)
