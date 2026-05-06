"""
Интеграционные тесты для users endpoints.
"""

import uuid
from uuid import UUID

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user(
    client: AsyncClient, created_resources: dict[str, list[UUID]]
):
    """Тест создания пользователя с динамическими полями контактов."""
    user_data = {
        "samAccountName": f"Test User {uuid.uuid4().hex[:8]}",
        "group": False,
        "contacts": {
            "telegram_id": f"test_telegram_{uuid.uuid4().hex[:8]}",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "pachca_id": f"test_pachca_{uuid.uuid4().hex[:8]}",
        },
    }

    response = await client.post("/api/v1/users", json=user_data)
    assert response.status_code == 200
    assert response.json() is True
    # Находим созданного пользователя через /users/search, чтобы потом удалить его в cleanup
    search_response = await client.get(
        "/api/v1/users/search",
        params={"query": user_data["samAccountName"], "limit": 1},
    )
    assert search_response.status_code == 200
    data = search_response.json()
    assert data.get("users"), (
        "Созданный пользователь не найден в /users/search"
    )

    user_id_str = data["users"][0]["user_id"]
    created_resources["users"].append(UUID(user_id_str))


@pytest.mark.asyncio
async def test_create_and_find_user(
    client: AsyncClient,
    created_resources: dict[str, list[UUID]],
    test_alert_id: UUID,
):
    """Тест создания пользователя и поиска его через subscriptions."""
    user_data = {
        "samAccountName": f"Test User {uuid.uuid4().hex[:8]}",
        "group": False,
        "contacts": {
            "telegram_id": f"test_telegram_{uuid.uuid4().hex[:8]}",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        },
    }

    # Создаем пользователя
    response = await client.post("/api/v1/users", json=user_data)
    assert response.status_code == 200

    # Ищем пользователя через subscriptions/search
    search_response = await client.get(
        f"/api/v1/alerts/{test_alert_id}/subscriptions/search",
        params={"query": user_data["samAccountName"], "limit": 100},
    )
    assert search_response.status_code == 200
    data = search_response.json()
    assert "users" in data

    # Находим созданного пользователя
    user_id = None
    for user in data["users"]:
        if user.get("samAccountName") == user_data["samAccountName"]:
            user_id = user["user_id"]
            break

    assert user_id is not None, (
        "Созданный пользователь не найден в результатах поиска"
    )
    created_resources["users"].append(user_id)

    # Обновляем пользователя
    update_data = {
        "samAccountName": f"Updated {user_data['samAccountName']}",
        "group": True,
        "contacts": {
            "telegram_id": f"updated_telegram_{uuid.uuid4().hex[:8]}",
            "email": f"updated_{uuid.uuid4().hex[:8]}@example.com",
        },
    }

    update_response = await client.patch(
        f"/api/v1/users/{user_id}", json=update_data
    )
    assert update_response.status_code == 200
    assert update_response.json() is True


# Фикстура test_alert_id перенесена в conftest.py
