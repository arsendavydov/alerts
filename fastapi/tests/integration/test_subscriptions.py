"""
Интеграционные тесты для subscriptions endpoints.
"""

import uuid
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_subscriptions_search(
    client: AsyncClient, test_alert_id: UUID, test_user_id: UUID
):
    """Тест поиска пользователей для подписок."""
    response = await client.get(
        f"/api/v1/alerts/{test_alert_id}/subscriptions/search"
    )
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "total" in data
    assert isinstance(data["users"], list)


@pytest.mark.asyncio
async def test_subscribe_user(
    client: AsyncClient,
    test_alert_id: UUID,
    test_user_id: UUID,
    created_resources: dict[str, list[UUID]],
):
    """Тест подписки пользователя на алерт."""
    # Отписываем если уже подписан
    await client.delete(
        f"/api/v1/alerts/{test_alert_id}/subscriptions/users/{test_user_id}"
    )

    # Подписываем
    response = await client.post(
        f"/api/v1/alerts/{test_alert_id}/subscriptions/users/{test_user_id}"
    )
    assert response.status_code == 200
    assert response.json() is True

    created_resources["subscriptions"].append(
        {"alert_id": test_alert_id, "user_id": test_user_id}
    )


@pytest.mark.asyncio
async def test_unsubscribe_user(
    client: AsyncClient, test_alert_id: UUID, test_user_id: UUID
):
    """Тест отписки пользователя от алерта."""
    # Сначала подписываем
    await client.post(
        f"/api/v1/alerts/{test_alert_id}/subscriptions/users/{test_user_id}"
    )

    # Отписываем
    response = await client.delete(
        f"/api/v1/alerts/{test_alert_id}/subscriptions/users/{test_user_id}"
    )
    assert response.status_code == 200
    assert response.json() is True


@pytest.mark.asyncio
async def test_subscriptions_search_subscribed_only(
    client: AsyncClient, test_alert_id: UUID, test_user_id: UUID
):
    """Тест поиска только подписанных пользователей."""
    # Подписываем пользователя
    await client.post(
        f"/api/v1/alerts/{test_alert_id}/subscriptions/users/{test_user_id}"
    )

    # Ищем только подписанных
    response = await client.get(
        f"/api/v1/alerts/{test_alert_id}/subscriptions/search",
        params={"subscribed_only": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert "users" in data

    # Проверяем что все пользователи имеют подписку
    for user in data["users"]:
        assert user.get("notification_channels") or user.get("statuses"), (
            "User in subscribed_only list has no subscription"
        )


@pytest.mark.asyncio
async def test_subscriptions_search_groups_filter(
    client: AsyncClient, test_alert_id: UUID
):
    """Тест фильтрации по группам."""
    # Фильтр groups=true
    groups_response = await client.get(
        f"/api/v1/alerts/{test_alert_id}/subscriptions/search",
        params={"groups": True},
    )
    assert groups_response.status_code == 200
    groups_data = groups_response.json()
    if groups_data.get("users"):
        assert all(user.get("group") for user in groups_data["users"])

    # Фильтр groups=false
    non_groups_response = await client.get(
        f"/api/v1/alerts/{test_alert_id}/subscriptions/search",
        params={"groups": False},
    )
    assert non_groups_response.status_code == 200
    non_groups_data = non_groups_response.json()
    if non_groups_data.get("users"):
        assert all(not user.get("group") for user in non_groups_data["users"])


@pytest.mark.asyncio
async def test_update_subscription(
    client: AsyncClient, test_alert_id: UUID, test_user_id: UUID
):
    """Тест обновления подписки."""
    # Подписываем пользователя
    subscribe_response = await client.post(
        f"/api/v1/alerts/{test_alert_id}/subscriptions/users/{test_user_id}"
    )
    assert subscribe_response.status_code == 200, (
        f"Failed to subscribe: {subscribe_response.status_code} - {subscribe_response.text}"
    )

    # Получаем список доступных статусов через GET подписки (если endpoint существует)
    # Или используем известный статус из системы
    # Для теста используем минимальный набор данных
    update_data = {
        "notification_channels": {"telegram": True, "email": False}
        # Убираем statuses, так как может не быть статуса "1" в системе
        # Если нужно тестировать statuses, нужно сначала получить список доступных статусов
    }

    response = await client.patch(
        f"/api/v1/alerts/{test_alert_id}/subscriptions/users/{test_user_id}",
        json=update_data,
    )
    assert response.status_code == 200, (
        f"Failed to update subscription: {response.status_code} - {response.text}"
    )
    assert response.json() is True


@pytest_asyncio.fixture(scope="function")
async def test_user_id(
    client: AsyncClient,
    created_resources: dict[str, list[UUID]],
    test_alert_id: UUID,
) -> UUID:
    """Фикстура для создания тестового пользователя."""
    user_data = {
        "samAccountName": f"Test User {uuid.uuid4().hex[:8]}",
        "group": False,
        "contacts": {
            "telegram_id": f"test_telegram_{uuid.uuid4().hex[:8]}",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        },
    }

    response = await client.post("/api/v1/users", json=user_data)
    if response.status_code != 200:
        raise Exception(
            f"Failed to create user: {response.status_code} - {response.text}"
        )

    # Находим пользователя через subscriptions/search
    users_response = await client.get(
        f"/api/v1/alerts/{test_alert_id}/subscriptions/search",
        params={"query": user_data["samAccountName"], "limit": 100},
    )
    if users_response.status_code != 200:
        raise Exception(
            f"Failed to search users: {users_response.status_code} - {users_response.text}"
        )

    users_data = users_response.json()
    user_id = None
    for user in users_data.get("users", []):
        if user.get("samAccountName") == user_data["samAccountName"]:
            user_id = user["user_id"]
            break

    if user_id is None:
        raise Exception(
            f"Созданный пользователь не найден: {user_data['samAccountName']}"
        )

    created_resources["users"].append(user_id)

    return user_id
