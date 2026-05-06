"""
Интеграционные тесты для pauses endpoints.
"""

from datetime import datetime, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_toggle_alert_pause(client: AsyncClient, test_alert_id: UUID):
    """Тест переключения паузы алерта."""
    pause_data = {"alert_id": str(test_alert_id), "login": "test_user"}

    response = await client.patch("/api/v1/alerts/pause", json=pause_data)
    assert response.status_code == 200
    assert response.json() is True

    # Проверяем состояние через alerts/search
    search_response = await client.get("/api/v1/alerts/search")
    assert search_response.status_code == 200
    alerts = search_response.json()["alerts"]
    alert = next((a for a in alerts if a["alert_id"] == test_alert_id), None)
    assert alert is not None
    # Пауза должна быть активна
    assert alert.get("paused") is True


@pytest.mark.asyncio
async def test_schedule_alert_pause(
    client: AsyncClient,
    test_alert_id: UUID,
    created_resources: dict[str, list[UUID]],
):
    """Тест установки паузы с расписанием."""
    start_time = (datetime.now() + timedelta(hours=1)).isoformat()
    end_time = (datetime.now() + timedelta(hours=2)).isoformat()

    pause_data = {
        "login": "test_user",
        "start_time": start_time,
        "end_time": end_time,
    }

    response = await client.post(
        f"/api/v1/alerts/{test_alert_id}/pause/schedule", json=pause_data
    )
    assert response.status_code == 200
    assert response.json() is True


@pytest.mark.asyncio
async def test_stop_alert_pause(client: AsyncClient, test_alert_id: UUID):
    """Тест остановки всех активных пауз."""
    # Сначала устанавливаем паузу
    pause_data = {"alert_id": str(test_alert_id), "login": "test_user"}
    await client.patch("/api/v1/alerts/pause", json=pause_data)

    # Останавливаем паузу
    stop_data = {"login": "test_user"}

    response = await client.patch(
        f"/api/v1/alerts/{test_alert_id}/pause/stop", json=stop_data
    )
    assert response.status_code == 200
    assert response.json() is True


@pytest.mark.asyncio
async def test_get_alert_pauses(client: AsyncClient, test_alert_id: UUID):
    """Тест получения истории пауз алерта."""
    response = await client.get(f"/api/v1/alerts/{test_alert_id}/pause")
    assert response.status_code == 200
    data = response.json()
    assert "pauses" in data
    assert "total" in data
    assert isinstance(data["pauses"], list)


@pytest.mark.asyncio
async def test_get_alert_pauses_with_filters(
    client: AsyncClient, test_alert_id: UUID
):
    """Тест получения пауз с фильтрами."""
    # Фильтр active
    active_response = await client.get(
        f"/api/v1/alerts/{test_alert_id}/pause",
        params={"filter_type": "active"},
    )
    assert active_response.status_code == 200

    # Фильтр future
    future_response = await client.get(
        f"/api/v1/alerts/{test_alert_id}/pause",
        params={"filter_type": "future"},
    )
    assert future_response.status_code == 200

    # Фильтр past
    past_response = await client.get(
        f"/api/v1/alerts/{test_alert_id}/pause", params={"filter_type": "past"}
    )
    assert past_response.status_code == 200
