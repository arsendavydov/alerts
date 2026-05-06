"""
Интеграционные тесты для links endpoints.
"""

import uuid
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture(scope="function")
async def test_alert_for_links(
    client: AsyncClient, created_resources: dict[str, list[UUID]]
) -> UUID:
    """Фикстура для создания тестового алерта для links."""
    # Получаем индикатор и group_rule
    indicators_response = await client.get(
        "/api/v1/indicators/autocomplete", params={"limit": 1}
    )
    if indicators_response.status_code != 200:
        raise Exception(
            f"Failed to get indicators: {indicators_response.status_code} - {indicators_response.text}"
        )
    indicators_data = indicators_response.json()
    if not indicators_data.get("indicators"):
        raise Exception("No indicators available")
    indicator_id = indicators_data["indicators"][0]["indicator_id"]

    groups_response = await client.get(
        "/api/v1/group_rules/autocomplete", params={"limit": 1}
    )
    if groups_response.status_code != 200:
        raise Exception(
            f"Failed to get group_rules: {groups_response.status_code} - {groups_response.text}"
        )
    groups_data = groups_response.json()
    if not groups_data.get("group_rules"):
        raise Exception("No group_rules available")
    group_rule_id = groups_data["group_rules"][0]["group_rule_id"]

    # Создаем алерт
    alert_data = {
        "alert_name": f"Test Alert for Links {uuid.uuid4().hex[:8]}",
        "indicator_id": indicator_id,
        "description": f"Test description {uuid.uuid4().hex[:8]}",
        "image": '{"type": "svg", "content": "<svg>Test</svg>"}',
        "tags": ["test"],
        "group_rule_id": group_rule_id,
    }

    create_response = await client.post(
        "/api/v1/alerts/detail", json=alert_data
    )
    if create_response.status_code != 200:
        raise Exception(
            f"Failed to create alert: {create_response.status_code} - {create_response.text}"
        )

    # Находим созданный алерт
    search_response = await client.get(
        "/api/v1/alerts/search", params={"query": alert_data["alert_name"]}
    )
    if search_response.status_code != 200:
        raise Exception(
            f"Failed to search alerts: {search_response.status_code} - {search_response.text}"
        )
    search_data = search_response.json()
    if not search_data.get("alerts"):
        raise Exception("Созданный алерт не найден")
    alert_id = search_data["alerts"][0]["alert_id"]
    created_resources["alerts"].append(alert_id)

    return alert_id


@pytest.mark.asyncio
async def test_create_link(
    client: AsyncClient,
    test_alert_for_links: UUID,
    created_resources: dict[str, list[UUID]],
):
    """Тест создания ссылки."""
    link_data = {
        "alert_id": str(test_alert_for_links),
        "link_name": f"Test Link {uuid.uuid4().hex[:8]}",
        "link_url": f"https://example.com/test-{uuid.uuid4().hex[:8]}",
    }

    response = await client.post("/api/v1/links/detail", json=link_data)
    assert response.status_code == 200
    assert response.json() is True

    # Находим созданную ссылку
    links_response = await client.get(
        "/api/v1/links/by_alert",
        params={"alert_id": str(test_alert_for_links)},
    )
    assert links_response.status_code == 200
    links_data = links_response.json()
    assert links_data.get("links")

    # Находим созданную ссылку
    created_link = None
    for link in links_data["links"]:
        if link.get("link_name") == link_data["link_name"]:
            created_link = link
            created_resources["links"].append(link["link_id"])
            break

    assert created_link is not None, "Созданный линк не найден"


@pytest.mark.asyncio
async def test_get_links_by_alert(
    client: AsyncClient,
    test_alert_for_links: UUID,
    created_resources: dict[str, list[UUID]],
):
    """Тест получения ссылок по алерту."""
    # Создаем ссылку
    link_data = {
        "alert_id": str(test_alert_for_links),
        "link_name": f"Test Link {uuid.uuid4().hex[:8]}",
        "link_url": f"https://example.com/test-{uuid.uuid4().hex[:8]}",
    }

    create_response = await client.post("/api/v1/links/detail", json=link_data)
    assert create_response.status_code == 200

    # Получаем ссылки
    response = await client.get(
        "/api/v1/links/by_alert",
        params={"alert_id": str(test_alert_for_links)},
    )
    assert response.status_code == 200
    data = response.json()
    assert "links" in data
    assert isinstance(data["links"], list)

    # Находим созданную ссылку
    created_link = None
    for link in data["links"]:
        if link.get("link_name") == link_data["link_name"]:
            created_link = link
            created_resources["links"].append(link["link_id"])
            break

    assert created_link is not None


@pytest.mark.asyncio
async def test_get_link_detail(
    client: AsyncClient,
    test_alert_for_links: UUID,
    created_resources: dict[str, list[UUID]],
):
    """Тест получения деталей ссылки."""
    # Создаем ссылку
    link_data = {
        "alert_id": str(test_alert_for_links),
        "link_name": f"Test Link {uuid.uuid4().hex[:8]}",
        "link_url": f"https://example.com/test-{uuid.uuid4().hex[:8]}",
    }

    create_response = await client.post("/api/v1/links/detail", json=link_data)
    assert create_response.status_code == 200

    # Находим созданную ссылку
    links_response = await client.get(
        "/api/v1/links/by_alert",
        params={"alert_id": str(test_alert_for_links)},
    )
    link_id = links_response.json()["links"][0]["link_id"]
    created_resources["links"].append(link_id)

    # Получаем детали
    detail_response = await client.get(
        "/api/v1/links/detail", params={"link_id": link_id}
    )
    assert detail_response.status_code == 200
    detail_data = detail_response.json()
    assert detail_data["link_id"] == link_id
    assert detail_data["link_name"] == link_data["link_name"]


@pytest.mark.asyncio
async def test_update_link(
    client: AsyncClient,
    test_alert_for_links: UUID,
    created_resources: dict[str, list[UUID]],
):
    """Тест обновления ссылки."""
    # Создаем ссылку
    link_data = {
        "alert_id": str(test_alert_for_links),
        "link_name": f"Test Link {uuid.uuid4().hex[:8]}",
        "link_url": f"https://example.com/test-{uuid.uuid4().hex[:8]}",
    }

    create_response = await client.post("/api/v1/links/detail", json=link_data)
    assert create_response.status_code == 200

    # Находим созданную ссылку
    links_response = await client.get(
        "/api/v1/links/by_alert",
        params={"alert_id": str(test_alert_for_links)},
    )
    link_id = links_response.json()["links"][0]["link_id"]
    created_resources["links"].append(link_id)

    # Обновляем ссылку
    update_data = {
        "link_id": link_id,
        "link_name": f"Updated {link_data['link_name']}",
        "link_url": f"https://updated.example.com/{uuid.uuid4().hex[:8]}",
    }

    update_response = await client.patch(
        "/api/v1/links/detail", json=update_data
    )
    assert update_response.status_code == 200
    assert update_response.json() is True

    # Проверяем обновление
    detail_response = await client.get(
        "/api/v1/links/detail", params={"link_id": link_id}
    )
    detail_data = detail_response.json()
    assert detail_data["link_name"] == update_data["link_name"]


@pytest.mark.asyncio
async def test_delete_link(
    client: AsyncClient,
    test_alert_for_links: UUID,
    created_resources: dict[str, list[UUID]],
):
    """Тест удаления ссылки."""
    # Создаем ссылку
    link_data = {
        "alert_id": str(test_alert_for_links),
        "link_name": f"Test Link {uuid.uuid4().hex[:8]}",
        "link_url": f"https://example.com/test-{uuid.uuid4().hex[:8]}",
    }

    create_response = await client.post("/api/v1/links/detail", json=link_data)
    assert create_response.status_code == 200

    # Находим созданную ссылку
    links_response = await client.get(
        "/api/v1/links/by_alert",
        params={"alert_id": str(test_alert_for_links)},
    )
    link_id = links_response.json()["links"][0]["link_id"]

    # Удаляем ссылку
    delete_response = await client.delete(
        "/api/v1/links/detail", params={"link_id": link_id}
    )
    assert delete_response.status_code == 200
    assert delete_response.json() is True

    # Проверяем что ссылка удалена
    detail_response = await client.get(
        "/api/v1/links/detail", params={"link_id": link_id}
    )
    assert detail_response.status_code == 404
