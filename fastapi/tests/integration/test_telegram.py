"""
Интеграционные тесты для telegram endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_telegram_by_login(client: AsyncClient):
    """Тест получения telegram_id по логину."""
    # Используем существующий логин из lazy_tests
    response = await client.get("/api/v1/users/kskorneev/telegram")
    assert response.status_code == 200
    data = response.json()
    assert "telegram_id" in data
    assert data["telegram_id"] is not None
    assert isinstance(data["telegram_id"], str)


@pytest.mark.asyncio
async def test_telegram_by_login_not_found(client: AsyncClient):
    """Тест получения telegram_id для несуществующего пользователя."""
    response = await client.get(
        "/api/v1/users/nonexistent_user_12345/telegram"
    )
    assert response.status_code == 404
