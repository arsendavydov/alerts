"""
Интеграционные тесты для screenshots endpoints.
"""

import json
import uuid
from uuid import UUID

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_screenshots_search(client: AsyncClient):
    """Тест поиска скриншотов."""
    response = await client.get(
        "/api/v1/screenshots/search", params={"limit": 50, "offset": 0}
    )
    assert response.status_code == 200
    data = response.json()
    assert "screenshots" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert isinstance(data["screenshots"], list)

    if data["screenshots"]:
        first_screenshot = data["screenshots"][0]
        assert "screenshot_id" in first_screenshot
        assert "name" in first_screenshot
        assert "description" in first_screenshot
        assert "image_data" in first_screenshot


@pytest.mark.asyncio
async def test_screenshots_search_with_query(client: AsyncClient):
    """Тест поиска скриншотов с запросом."""
    # Сначала получаем список скриншотов
    response = await client.get(
        "/api/v1/screenshots/search", params={"limit": 10}
    )
    if response.status_code == 200:
        data = response.json()
        if data.get("screenshots"):
            # Берем часть description из первого скриншота для поиска
            first_desc = data["screenshots"][0].get("description", "")
            if first_desc and len(first_desc) > 3:
                search_query = first_desc[:3]
                search_response = await client.get(
                    "/api/v1/screenshots/search",
                    params={"query": search_query, "limit": 50},
                )
                assert search_response.status_code == 200
                search_data = search_response.json()
                assert "screenshots" in search_data


@pytest.mark.asyncio
async def test_screenshots_search_with_sorting(client: AsyncClient):
    """Тест поиска скриншотов с сортировкой."""
    response = await client.get(
        "/api/v1/screenshots/search",
        params={"order_by": "name", "order_dir": "desc", "limit": 50},
    )
    assert response.status_code == 200
    data = response.json()
    assert "screenshots" in data


@pytest.mark.asyncio
async def test_screenshots_search_pagination(client: AsyncClient):
    """Тест пагинации скриншотов."""
    page1_response = await client.get(
        "/api/v1/screenshots/search", params={"limit": 10, "offset": 0}
    )
    assert page1_response.status_code == 200
    page1_data = page1_response.json()

    if page1_data.get("total", 0) > 10:
        page2_response = await client.get(
            "/api/v1/screenshots/search", params={"limit": 10, "offset": 10}
        )
        assert page2_response.status_code == 200
        page2_data = page2_response.json()

        # Проверяем что результаты разные
        page1_ids = {s["screenshot_id"] for s in page1_data["screenshots"]}
        page2_ids = {s["screenshot_id"] for s in page2_data["screenshots"]}
        assert page1_ids != page2_ids, "Pagination returned same results"


@pytest.mark.asyncio
async def test_create_screenshot_with_array_json(
    client: AsyncClient, created_resources: dict[str, list[UUID]]
):
    """Тест создания скриншота с JSON массивом."""
    screenshot_data = {
        "name": f"Test Screenshot Array {uuid.uuid4().hex[:8]}",
        "description": f"Test Description Array {uuid.uuid4().hex[:8]}",
        "image_data": '["https://example.com/image1.png", "https://example.com/image2.png"]',
    }

    response = await client.post("/api/v1/screenshots", json=screenshot_data)
    assert response.status_code == 200
    data = response.json()
    assert "screenshot_id" in data
    created_resources["screenshots"].append(data["screenshot_id"])


@pytest.mark.asyncio
async def test_create_screenshot_with_object_json(
    client: AsyncClient, created_resources: dict[str, list[UUID]]
):
    """Тест создания скриншота с JSON объектом."""
    screenshot_data = {
        "name": f"Test Screenshot Object {uuid.uuid4().hex[:8]}",
        "description": f"Test Description Object {uuid.uuid4().hex[:8]}",
        "image_data": '{"url": "https://example.com/image.png", "width": 1000, "height": 500}',
    }

    response = await client.post("/api/v1/screenshots", json=screenshot_data)
    assert response.status_code == 200
    data = response.json()
    assert "screenshot_id" in data
    created_resources["screenshots"].append(data["screenshot_id"])


@pytest.mark.asyncio
async def test_get_screenshot(
    client: AsyncClient, created_resources: dict[str, list[UUID]]
):
    """Тест получения скриншота по ID."""
    # Создаем скриншот
    screenshot_data = {
        "name": f"Test Screenshot {uuid.uuid4().hex[:8]}",
        "description": f"Test Description {uuid.uuid4().hex[:8]}",
        "image_data": '{"url": "https://example.com/image.png"}',
    }

    create_response = await client.post(
        "/api/v1/screenshots", json=screenshot_data
    )
    assert create_response.status_code == 200
    screenshot_id = create_response.json()["screenshot_id"]
    created_resources["screenshots"].append(screenshot_id)

    # Получаем скриншот
    get_response = await client.get(f"/api/v1/screenshots/{screenshot_id}")
    assert get_response.status_code == 200
    data = get_response.json()

    assert data["screenshot_id"] == screenshot_id
    assert data["name"] == screenshot_data["name"]
    assert data["description"] == screenshot_data["description"]

    # Проверяем что image_data - валидный JSON
    json.loads(data["image_data"])


@pytest.mark.asyncio
async def test_update_screenshot(
    client: AsyncClient, created_resources: dict[str, list[UUID]]
):
    """Тест обновления скриншота."""
    # Создаем скриншот
    screenshot_data = {
        "name": f"Test Screenshot {uuid.uuid4().hex[:8]}",
        "description": f"Test Description {uuid.uuid4().hex[:8]}",
        "image_data": '{"url": "https://example.com/image.png"}',
    }

    create_response = await client.post(
        "/api/v1/screenshots", json=screenshot_data
    )
    assert create_response.status_code == 200
    screenshot_id = create_response.json()["screenshot_id"]
    created_resources["screenshots"].append(screenshot_id)

    # Обновляем скриншот
    update_data = {
        "name": f"Updated {screenshot_data['name']}",
        "image_data": '{"updated": true, "url": "https://updated.example.com/image.png"}',
    }

    update_response = await client.patch(
        f"/api/v1/screenshots/{screenshot_id}", json=update_data
    )
    assert update_response.status_code == 200
    assert update_response.json() is True

    # Проверяем обновление
    get_response = await client.get(f"/api/v1/screenshots/{screenshot_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["name"] == update_data["name"]


@pytest.mark.asyncio
async def test_delete_screenshot(
    client: AsyncClient, created_resources: dict[str, list[UUID]]
):
    """Тест удаления скриншота."""
    # Создаем скриншот
    screenshot_data = {
        "name": f"Test Screenshot {uuid.uuid4().hex[:8]}",
        "description": f"Test Description {uuid.uuid4().hex[:8]}",
        "image_data": '{"url": "https://example.com/image.png"}',
    }

    create_response = await client.post(
        "/api/v1/screenshots", json=screenshot_data
    )
    assert create_response.status_code == 200
    screenshot_id = create_response.json()["screenshot_id"]

    # Удаляем скриншот
    delete_response = await client.delete(
        f"/api/v1/screenshots/{screenshot_id}"
    )
    assert delete_response.status_code == 200
    assert delete_response.json() is True

    # Проверяем что скриншот удален
    get_response = await client.get(f"/api/v1/screenshots/{screenshot_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_create_screenshot_invalid_json(client: AsyncClient):
    """Тест создания скриншота с невалидным JSON."""
    invalid_data = {
        "name": f"Test Invalid {uuid.uuid4().hex[:8]}",
        "description": f"Test Invalid Desc {uuid.uuid4().hex[:8]}",
        "image_data": "not a valid json {",
    }

    response = await client.post("/api/v1/screenshots", json=invalid_data)
    assert response.status_code >= 400


@pytest.mark.asyncio
async def test_get_screenshot_not_found(client: AsyncClient):
    """Тест получения несуществующего скриншота."""
    fake_id = str(uuid.uuid4())
    response = await client.get(f"/api/v1/screenshots/{fake_id}")
    assert response.status_code == 404
