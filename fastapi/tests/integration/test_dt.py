"""
Интеграционные тесты для DT endpoints.
"""

from uuid import UUID

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_dt(client: AsyncClient, test_alert_id: UUID):
    """Тест получения DT для алерта."""
    response = await client.get(f"/api/v1/alert/{test_alert_id}/dt")
    # Может быть 404 если DT не создан
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_create_dt(
    client: AsyncClient,
    test_alert_id: UUID,
    created_resources: dict[str, list[UUID]],
):
    """Тест создания DT для алерта."""
    dt_data = {
        "content": '{"test": "data"}',
        "auto_create": False,
        "silence_time": '{"start": "09:00", "end": "18:00"}',
    }

    response = await client.post(
        f"/api/v1/alert/{test_alert_id}/dt", json=dt_data
    )
    assert response.status_code == 200
    assert response.json() is True

    created_resources["dt"].append({"alert_id": test_alert_id})


@pytest.mark.asyncio
async def test_update_dt(
    client: AsyncClient,
    test_alert_id: UUID,
    created_resources: dict[str, list[UUID]],
):
    """Тест обновления DT."""
    # Создаем DT
    dt_data = {
        "content": '{"test": "data"}',
        "auto_create": False,
        "silence_time": '{"start": "09:00", "end": "18:00"}',
    }

    create_response = await client.post(
        f"/api/v1/alert/{test_alert_id}/dt", json=dt_data
    )
    assert create_response.status_code == 200
    created_resources["dt"].append({"alert_id": test_alert_id})

    # Обновляем DT
    update_data = {
        "content": '{"updated": "data"}',
        "silence_time": '{"start": "10:00", "end": "19:00"}',
    }

    update_response = await client.patch(
        f"/api/v1/alert/{test_alert_id}/dt", json=update_data
    )
    assert update_response.status_code == 200
    assert update_response.json() is True


@pytest.mark.asyncio
async def test_delete_dt(
    client: AsyncClient,
    test_alert_id: UUID,
    created_resources: dict[str, list[UUID]],
):
    """Тест удаления DT."""
    # Создаем DT
    dt_data = {"content": '{"test": "data"}', "auto_create": False}

    create_response = await client.post(
        f"/api/v1/alert/{test_alert_id}/dt", json=dt_data
    )
    assert create_response.status_code == 200

    # Удаляем DT
    delete_response = await client.delete(f"/api/v1/alert/{test_alert_id}/dt")
    assert delete_response.status_code == 200
    assert delete_response.json() is True

    # Проверяем что DT удален
    get_response = await client.get(f"/api/v1/alert/{test_alert_id}/dt")
    assert get_response.status_code == 404
