"""
Конфигурация и фикстуры для интеграционных тестов.
"""

import contextlib
import os
import uuid
from collections.abc import AsyncGenerator
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import AsyncClient

# Отключаем прокси для интеграционных тестов (как в lazy тестах)
# httpx по умолчанию использует системные настройки прокси из переменных окружения,
# но lazy тесты используют requests, который работает по-другому
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Базовый URL API для тестов."""
    return os.getenv("TEST_API_URL", "http://localhost:8888/alerts")


@pytest_asyncio.fixture(scope="function")
async def client(api_base_url: str) -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP клиент для тестов.
    Scope: function - создается для каждого теста, чтобы избежать проблем с lifecycle на Windows.

    Примечание:
    - proxies=None отключает использование прокси
    - trust_env=False отключает чтение переменных окружения для прокси
    Это нужно, чтобы интеграционные тесты работали так же, как lazy тесты (которые используют requests.Session).
    """
    async with AsyncClient(
        base_url=api_base_url,
        timeout=30.0,
        proxies=None,  # Отключаем прокси
        trust_env=False,  # Не используем переменные окружения для прокси
    ) as ac:
        yield ac


@pytest.fixture(scope="function")
def created_resources() -> dict[str, list]:
    """
    Хранилище созданных ресурсов для очистки после тестов.
    Каждый тест получает свой экземпляр.

    Формат данных:
    - alerts: List[UUID] - список ID алертов
    - users: List[UUID] - список ID пользователей
    - subscriptions: List[Dict] - список подписок с ключами 'alert_id' и 'user_id'
    - links: List[UUID] - список ID линков
    - screenshots: List[UUID] - список ID скриншотов
    - dt: List[Dict] - список DT с ключом 'alert_id'
    - pauses: List[Dict] - список пауз с ключами 'alert_id' и 'pause_id' (опционально, т.к. удаляются каскадно с алертами)
    - feedback: List[Dict] - список feedback с ключами 'status_history' и 'user_fio' (опционально, т.к. не всегда доступны)
    """
    return {
        "alerts": [],
        "users": [],
        "subscriptions": [],
        "links": [],
        "screenshots": [],
        "dt": [],
        "pauses": [],
        "feedback": [],
    }


@pytest_asyncio.fixture(scope="function", autouse=True)
async def cleanup_created_resources(
    client: AsyncClient, created_resources: dict[str, list]
):
    """
    Автоматическая очистка созданных ресурсов после каждого теста.
    """
    yield

    # Очистка в обратном порядке зависимостей
    # Сначала удаляем зависимости, потом основные ресурсы

    # Удаляем feedback
    # Примечание: для удаления feedback нужны status_history и user_fio, но мы храним только feedback_id
    # Поэтому feedback удаляется автоматически при удалении связанных сущностей или остается в БД
    # Если нужно удалять feedback, нужно хранить полные данные (status_history, user_fio)
    for feedback_data in created_resources.get("feedback", []):
        try:
            if (
                isinstance(feedback_data, dict)
                and "status_history" in feedback_data
                and "user_fio" in feedback_data
            ):
                # httpx.AsyncClient.delete() не поддерживает json, используем request()
                await client.request(
                    "DELETE",
                    "/api/v1/feedback/detail",
                    json={
                        "status_history": str(feedback_data["status_history"]),
                        "user_fio": feedback_data["user_fio"],
                    },
                )
        except Exception:
            pass

    # Удаляем pauses
    # Примечание: для удаления pause нужны alert_id и pause_id
    # Если нужно удалять pauses, нужно хранить их как dict с alert_id и pause_id
    for pause_data in created_resources.get("pauses", []):
        try:
            if (
                isinstance(pause_data, dict)
                and "alert_id" in pause_data
                and "pause_id" in pause_data
            ):
                await client.delete(
                    f"/api/v1/alerts/{pause_data['alert_id']}/pause/{pause_data['pause_id']}"
                )
        except Exception:
            pass

    # Удаляем subscriptions
    for sub_data in created_resources.get("subscriptions", []):
        try:
            if (
                isinstance(sub_data, dict)
                and "alert_id" in sub_data
                and "user_id" in sub_data
            ):
                await client.delete(
                    f"/api/v1/alerts/{sub_data['alert_id']}/subscriptions/{sub_data['user_id']}"
                )
        except Exception:
            pass

    # Удаляем links (правильный endpoint: /api/v1/links/detail?link_id=...)
    for link_id in created_resources.get("links", []):
        with contextlib.suppress(Exception):
            await client.delete(
                "/api/v1/links/detail", params={"link_id": str(link_id)}
            )

    # Удаляем screenshots
    for screenshot_id in created_resources.get("screenshots", []):
        with contextlib.suppress(Exception):
            await client.delete(f"/api/v1/screenshots/{screenshot_id}")

    # Удаляем dt
    for dt_data in created_resources.get("dt", []):
        try:
            if isinstance(dt_data, dict) and "alert_id" in dt_data:
                await client.delete(f"/api/v1/alerts/{dt_data['alert_id']}/dt")
        except Exception:
            pass

    # Удаляем users
    for user_id in created_resources.get("users", []):
        with contextlib.suppress(Exception):
            await client.delete(f"/api/v1/users/{user_id}")

    # Удаляем alerts (последними, так как на них могут быть зависимости)
    # Правильный endpoint: /api/v1/alerts/detail?alert_id=...
    # Примечание: удаление алерта каскадно удаляет связанные данные (links, subscriptions, pauses, dt)
    for alert_id in created_resources.get("alerts", []):
        with contextlib.suppress(Exception):
            await client.delete(
                "/api/v1/alerts/detail", params={"alert_id": str(alert_id)}
            )


@pytest_asyncio.fixture(scope="function")
async def test_alert_id(
    client: AsyncClient, created_resources: dict[str, list]
) -> UUID:
    """
    Фикстура для создания тестового алерта.
    Scope: function - создается для каждого теста, который его использует.
    """
    # Получаем индикатор
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

    # Получаем group_rule
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
        "alert_name": f"Test Alert {uuid.uuid4().hex[:8]}",
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
