"""
Модульные тесты для subscriptions router.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from contracts.service_protocols import SubscriptionsServiceProtocol
from dependencies import get_subscriptions_service
from fastapi import FastAPI
from httpx import AsyncClient

from routers.subscriptions import (
    get_subscription_by_alert_and_user as get_subscription_by_alert_and_user_fn,
)
from routers.subscriptions import (
    get_subscription_users as get_subscription_users_fn,
)
from routers.subscriptions import router
from routers.subscriptions import subscribe as subscribe_fn
from routers.subscriptions import unsubscribe as unsubscribe_fn
from routers.subscriptions import (
    update_subscription_by_alert_and_user as update_subscription_by_alert_and_user_fn,
)
from schemas.subscriptions import (
    AlertByUserItem,
    AlertByUserListResponse,
    SubscribeRequest,
    SubscriptionByUserResponse,
    SubscriptionByUserUpdate,
    SubscriptionByUserUpdateRequest,
    SubscriptionUserItem,
    SubscriptionUserListResponse,
    UnsubscribeRequest,
)


@pytest.fixture
def app():
    """Создает FastAPI приложение для тестирования."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def mock_service():
    """Мок сервиса."""
    return AsyncMock(spec=SubscriptionsServiceProtocol)


@pytest_asyncio.fixture
async def client(app, mock_service):
    """Асинхронный тестовый клиент с переопределенным сервисом."""
    # Переопределяем dependency для всех эндпоинтов
    app.dependency_overrides[get_subscriptions_service] = lambda: mock_service
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestSubscriptionsRouter:
    """Тесты для роутера subscriptions."""

    def test_router_included(self, app):
        """Тест, что роутер правильно включен в приложение."""
        routes = [r.path for r in app.routes]
        assert any("/subscriptions" in route for route in routes)

    @pytest.mark.asyncio
    async def test_get_subscription_users_by_alert(self, client, mock_service):
        """Тест получения списка пользователей для страницы подписок."""
        alert_id = uuid4()
        # Настраиваем мок для возврата правильного ответа
        mock_service.get_subscription_users.return_value = (
            SubscriptionUserListResponse(
                users=[
                    SubscriptionUserItem(
                        user_id=uuid4(),
                        samAccountName="test_user",
                        group=False,
                        notification_channels={},
                        statuses=[],
                    )
                ],
                total=1,
            )
        )

        response = await client.get(
            f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search"
        )

        assert response.status_code == 200
        assert response.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_get_subscription_users_by_alert_with_query(
        self, client, mock_service
    ):
        """Тест получения списка пользователей с поисковым запросом."""
        alert_id = uuid4()
        # Настраиваем мок для возврата пустого списка
        mock_service.get_subscription_users.return_value = (
            SubscriptionUserListResponse(users=[], total=0)
        )

        response = await client.get(
            f"/alerts/api/v1/alerts/{alert_id}/subscriptions/search",
            params={"query": "test", "limit": 20, "offset": 0},
        )

        assert response.status_code == 200
        assert response.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_subscribe_by_alert_and_user(self, client, mock_service):
        """Тест подписки пользователя на алерт."""
        alert_id = uuid4()
        user_id = uuid4()
        # Настраиваем мок для возврата True
        mock_service.subscribe.return_value = True

        response = await client.post(
            f"/alerts/api/v1/alerts/{alert_id}/subscriptions/users/{user_id}"
        )

        assert response.status_code == 200
        assert response.json() is True

    @pytest.mark.asyncio
    async def test_unsubscribe_by_alert_and_user(self, client, mock_service):
        """Тест отписки пользователя от алерта."""
        alert_id = uuid4()
        user_id = uuid4()
        # Настраиваем мок для возврата True
        mock_service.unsubscribe.return_value = True

        response = await client.delete(
            f"/alerts/api/v1/alerts/{alert_id}/subscriptions/users/{user_id}"
        )

        assert response.status_code == 200
        assert response.json() is True

    @pytest.mark.asyncio
    async def test_update_subscription_by_alert_and_user(
        self, client, mock_service
    ):
        """Тест обновления подписки пользователя на алерт."""
        alert_id = uuid4()
        user_id = uuid4()
        data = SubscriptionByUserUpdateRequest(
            notification_channels={"telegram": True}, statuses=[]
        )
        # Настраиваем мок для возврата True
        mock_service.update_subscription_by_alert_and_user.return_value = True

        response = await client.patch(
            f"/alerts/api/v1/alerts/{alert_id}/subscriptions/users/{user_id}",
            json=data.model_dump(exclude_none=True),
        )

        assert response.status_code == 200
        assert response.json() is True

    @pytest.mark.asyncio
    async def test_get_alerts_by_user(self, client, mock_service):
        """Тест получения списка алертов по пользователю."""
        user_id = uuid4()
        mock_service.get_alerts_by_user.return_value = AlertByUserListResponse(
            alerts=[
                AlertByUserItem(
                    alert_id=uuid4(),
                    alert_name="Test Alert",
                    notification_channels={"telegram": True},
                )
            ],
            total=1,
        )

        response = await client.get(
            f"/alerts/api/v1/users/{user_id}/subscriptions/search"
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert len(body["alerts"]) == 1

        # Проверяем, что сервис вызван с корректными параметрами по умолчанию
        mock_service.get_alerts_by_user.assert_awaited_once()
        _, kwargs = mock_service.get_alerts_by_user.await_args
        assert kwargs["user_id"] == user_id
        assert kwargs["subscribed_only"] is False

    @pytest.mark.asyncio
    async def test_internal_subscribe_function(self, mock_service):
        data = SubscribeRequest(alert_id=uuid4(), user_id=uuid4())
        mock_service.subscribe.return_value = True
        assert await subscribe_fn(data, mock_service) is True

    @pytest.mark.asyncio
    async def test_internal_unsubscribe_function(self, mock_service):
        data = UnsubscribeRequest(alert_id=uuid4(), user_id=uuid4())
        mock_service.unsubscribe.return_value = True
        assert await unsubscribe_fn(data, mock_service) is True

    @pytest.mark.asyncio
    async def test_internal_get_subscription_by_alert_and_user_function(
        self, mock_service
    ):
        alert_id = uuid4()
        user_id = uuid4()
        expected = SubscriptionByUserResponse(
            subscription_id=uuid4(), statuses=[]
        )
        mock_service.get_subscription_by_alert_and_user.return_value = expected
        result = await get_subscription_by_alert_and_user_fn(
            alert_id, user_id, mock_service
        )
        assert result is expected

    @pytest.mark.asyncio
    async def test_internal_update_subscription_by_alert_and_user_function(
        self, mock_service
    ):
        data = SubscriptionByUserUpdate(
            alert_id=uuid4(),
            user_id=uuid4(),
            notification_channels={"telegram": True},
        )
        mock_service.update_subscription_by_alert_and_user.return_value = True
        assert await update_subscription_by_alert_and_user_fn(data, mock_service)

    @pytest.mark.asyncio
    async def test_internal_get_subscription_users_function(self, mock_service):
        alert_id = uuid4()
        expected = SubscriptionUserListResponse(users=[], total=0)
        mock_service.get_subscription_users.return_value = expected
        result = await get_subscription_users_fn(
            alert_id=alert_id, service=mock_service
        )
        assert result is expected
