"""
Интеграционные тесты для alerts endpoints.
"""

import json
import uuid
from uuid import UUID

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_alerts_search(client: AsyncClient):
    """Тест поиска алертов."""
    response = await client.get("/api/v1/alerts/search")
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert "total" in data
    assert isinstance(data["alerts"], list)
    assert isinstance(data["total"], int)


@pytest.mark.asyncio
async def test_alerts_autocomplete(client: AsyncClient):
    """Тест автодополнения алертов."""
    response = await client.get("/api/v1/alerts/autocomplete")
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert isinstance(data["alerts"], list)


@pytest.mark.asyncio
async def test_alerts_tags_cloud(client: AsyncClient):
    """Тест получения облака тегов."""
    response = await client.get("/api/v1/alerts/tags/cloud")
    assert response.status_code == 200
    data = response.json()
    assert "tags" in data
    assert isinstance(data["tags"], list)


@pytest.mark.asyncio
async def test_alerts_tags_cloud_with_filters_and_and_excludes_filter_tags(
    client: AsyncClient, created_resources: dict[str, list[UUID]]
):
    """Тест cloud тегов: AND по tags и исключение тегов фильтра из ответа."""
    # Готовим уникальный токен, чтобы под условие попали только наши алерты
    token = uuid.uuid4().hex[:10]
    alert_name_prefix = f"TagCloudTest_{token}"

    indicators_response = await client.get(
        "/api/v1/indicators/autocomplete", params={"limit": 1}
    )
    assert indicators_response.status_code == 200
    indicator_id = indicators_response.json()["indicators"][0]["indicator_id"]

    groups_response = await client.get(
        "/api/v1/group_rules/autocomplete", params={"limit": 1}
    )
    assert groups_response.status_code == 200
    group_rule_id = groups_response.json()["group_rules"][0]["group_rule_id"]

    alert_1_name = f"{alert_name_prefix}_1"
    alert_2_name = f"{alert_name_prefix}_2"

    # Создаем 2 алерта:
    # 1) tags: ["cdi", "api"]
    # 2) tags: ["cdi", "user_api"]
    for alert_name, tags in (
        (alert_1_name, ["cdi", "api"]),
        (alert_2_name, ["cdi", "user_api"]),
    ):
        resp = await client.post(
            "/api/v1/alerts/detail",
            json={
                "alert_name": alert_name,
                "indicator_id": indicator_id,
                "description": "tag cloud filter test",
                "image": '{"type": "svg", "content": "<svg>test</svg>"}',
                "tags": tags,
                "group_rule_id": group_rule_id,
            },
        )
        assert resp.status_code == 200
        assert resp.json() is True

        # Находим созданный алерт по alert_name
        search_response = await client.get(
            "/api/v1/alerts/search", params={"query": alert_name}
        )
        assert search_response.status_code == 200
        found = search_response.json().get("alerts", [])
        assert found, "Created alert not found in /alerts/search"
        created_resources["alerts"].append(found[0]["alert_id"])

    # 1) Без фильтра tags: должны быть ВСЕ теги среди найденных алертов
    resp_all = await client.get(
        "/api/v1/alerts/tags/cloud",
        params={"alert_name": alert_name_prefix},
    )
    assert resp_all.status_code == 200
    data_all = resp_all.json()
    assert set(data_all["tags"]) == {"cdi", "api", "user_api"}
    assert data_all["total"] == 3

    # 2) tags=cdi: cloud считается после фильтра, но теги фильтра исключаются из ответа
    resp_cdi = await client.get(
        "/api/v1/alerts/tags/cloud",
        params={"alert_name": alert_name_prefix, "tags": "cdi"},
    )
    assert resp_cdi.status_code == 200
    data_cdi = resp_cdi.json()
    assert set(data_cdi["tags"]) == {"api", "user_api"}
    assert data_cdi["total"] == 2
    assert "cdi" not in data_cdi["tags"]

    # 3) tags=cdi,api (AND): матчится только 1-й алерт => после исключения (cdi, api) cloud пустой
    resp_cdi_api = await client.get(
        "/api/v1/alerts/tags/cloud",
        params={"alert_name": alert_name_prefix, "tags": "cdi,api"},
    )
    assert resp_cdi_api.status_code == 200
    data_cdi_api = resp_cdi_api.json()
    assert data_cdi_api["tags"] == []
    assert data_cdi_api["total"] == 0


@pytest.mark.asyncio
async def test_create_alert(
    client: AsyncClient, created_resources: dict[str, list[UUID]]
):
    """Тест создания алерта."""
    # Получаем индикатор
    indicators_response = await client.get(
        "/api/v1/indicators/autocomplete", params={"limit": 1}
    )
    assert indicators_response.status_code == 200
    indicators_data = indicators_response.json()
    assert indicators_data.get("indicators"), "No indicators available"
    indicator_id = indicators_data["indicators"][0]["indicator_id"]

    # Получаем group_rule
    groups_response = await client.get(
        "/api/v1/group_rules/autocomplete", params={"limit": 1}
    )
    assert groups_response.status_code == 200
    groups_data = groups_response.json()
    assert groups_data.get("group_rules"), "No group_rules available"
    group_rule_id = groups_data["group_rules"][0]["group_rule_id"]

    # Создаем алерт
    alert_data = {
        "alert_name": f"Test Alert {uuid.uuid4().hex[:8]}",
        "indicator_id": indicator_id,
        "description": f"Test description {uuid.uuid4().hex[:8]}",
        "image": '{"type": "svg", "content": "<svg>Test</svg>"}',
        "tags": ["test", "api"],
        "group_rule_id": group_rule_id,
        "silence_time": '{"start": "09:00", "end": "18:00"}',
    }

    response = await client.post("/api/v1/alerts/detail", json=alert_data)
    assert response.status_code == 200
    assert response.json() is True

    # Находим созданный алерт
    search_response = await client.get(
        "/api/v1/alerts/search", params={"query": alert_data["alert_name"]}
    )
    assert search_response.status_code == 200
    search_data = search_response.json()
    assert search_data.get("alerts"), "Созданный алерт не найден"

    alert_id = search_data["alerts"][0]["alert_id"]
    created_resources["alerts"].append(alert_id)

    # Проверяем детали алерта
    detail_response = await client.get(
        "/api/v1/alerts/detail", params={"alert_id": alert_id}
    )
    assert detail_response.status_code == 200
    detail_data = detail_response.json()

    # Проверяем структуру group_rule
    assert "group_rule" in detail_data
    group_rule = detail_data["group_rule"]
    assert "group_rule_id" in group_rule
    assert "description" in group_rule
    assert "image" in group_rule

    # Проверяем silence_time
    if "silence_time" in detail_data:
        expected_silence_time = json.loads(alert_data["silence_time"])
        assert detail_data["silence_time"] == expected_silence_time


@pytest.mark.asyncio
async def test_alerts_search_escapes_like_wildcards(
    client: AsyncClient, created_resources: dict[str, list[UUID]]
):
    """
    Регресс-тест: '_' и '%' в query должны искаться как символы, а не wildcard (ILIKE + ESCAPE).
    Создаем пары алертов, которые "совпали бы" при wildcard-поиске, и убеждаемся, что совпадения нет.
    """
    indicators_response = await client.get(
        "/api/v1/indicators/autocomplete", params={"limit": 1}
    )
    assert indicators_response.status_code == 200
    indicators_data = indicators_response.json()
    assert indicators_data.get("indicators"), "No indicators available"
    indicator_id = indicators_data["indicators"][0]["indicator_id"]

    groups_response = await client.get(
        "/api/v1/group_rules/autocomplete", params={"limit": 1}
    )
    assert groups_response.status_code == 200
    groups_data = groups_response.json()
    assert groups_data.get("group_rules"), "No group_rules available"
    group_rule_id = groups_data["group_rules"][0]["group_rule_id"]

    token = uuid.uuid4().hex[:8]

    # '_' case: без экранирования "A_B" матчило бы и "AXB"
    name_underscore = f"LikeEscape_{token}_A_B"
    name_underscore_other = f"LikeEscape_{token}_AXB"

    for name in (name_underscore, name_underscore_other):
        resp = await client.post(
            "/api/v1/alerts/detail",
            json={
                "alert_name": name,
                "indicator_id": indicator_id,
                "description": "like escape test",
                "image": '{"type":"svg","content":"<svg>t</svg>"}',
                "tags": ["test", "like_escape"],
                "group_rule_id": group_rule_id,
            },
        )
        assert resp.status_code == 200
        assert resp.json() is True

        created = await client.get(
            "/api/v1/alerts/search", params={"query": name}
        )
        assert created.status_code == 200
        created_data = created.json()
        assert created_data.get("alerts"), (
            "Created alert not found after create"
        )
        created_resources["alerts"].append(
            created_data["alerts"][0]["alert_id"]
        )

    search_underscore = await client.get(
        "/api/v1/alerts/search", params={"query": name_underscore}
    )
    assert search_underscore.status_code == 200
    found_names = {
        a.get("alert_name") for a in search_underscore.json().get("alerts", [])
    }
    assert name_underscore in found_names
    assert name_underscore_other not in found_names

    # '%' case: без экранирования "P%Q" матчило бы и "PXQ"
    name_percent = f"LikeEscape_{token}_P%Q"
    name_percent_other = f"LikeEscape_{token}_PXQ"

    for name in (name_percent, name_percent_other):
        resp = await client.post(
            "/api/v1/alerts/detail",
            json={
                "alert_name": name,
                "indicator_id": indicator_id,
                "description": "like escape test",
                "image": '{"type":"svg","content":"<svg>t</svg>"}',
                "tags": ["test", "like_escape"],
                "group_rule_id": group_rule_id,
            },
        )
        assert resp.status_code == 200
        assert resp.json() is True

        created = await client.get(
            "/api/v1/alerts/search", params={"query": name}
        )
        assert created.status_code == 200
        created_data = created.json()
        assert created_data.get("alerts"), (
            "Created alert not found after create"
        )
        created_resources["alerts"].append(
            created_data["alerts"][0]["alert_id"]
        )

    search_percent = await client.get(
        "/api/v1/alerts/search", params={"query": name_percent}
    )
    assert search_percent.status_code == 200
    found_names = {
        a.get("alert_name") for a in search_percent.json().get("alerts", [])
    }
    assert name_percent in found_names
    assert name_percent_other not in found_names

    # Дополнительно: autocomplete не должен "схлопывать" '_' как wildcard
    auto = await client.get(
        "/api/v1/alerts/autocomplete",
        params={"query": name_underscore, "limit": 50},
    )
    assert auto.status_code == 200
    auto_names = {a.get("alert_name") for a in auto.json().get("alerts", [])}
    assert name_underscore in auto_names
    assert name_underscore_other not in auto_names


@pytest.mark.asyncio
async def test_update_alert(
    client: AsyncClient, created_resources: dict[str, list[UUID]]
):
    """Тест обновления алерта."""
    # Создаем алерт для обновления
    indicators_response = await client.get(
        "/api/v1/indicators/autocomplete", params={"limit": 1}
    )
    assert indicators_response.status_code == 200
    indicator_id = indicators_response.json()["indicators"][0]["indicator_id"]

    groups_response = await client.get(
        "/api/v1/group_rules/autocomplete", params={"limit": 1}
    )
    assert groups_response.status_code == 200
    group_rule_id = groups_response.json()["group_rules"][0]["group_rule_id"]

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
    assert create_response.status_code == 200

    # Находим созданный алерт
    search_response = await client.get(
        "/api/v1/alerts/search", params={"query": alert_data["alert_name"]}
    )
    alert_id = search_response.json()["alerts"][0]["alert_id"]
    created_resources["alerts"].append(alert_id)

    # Обновляем алерт
    update_data = {
        "alert_id": alert_id,
        "alert_name": f"Updated {alert_data['alert_name']}",
        "description": f"Updated {alert_data['description']}",
        "image": '{"type": "svg", "content": "<svg>Updated</svg>"}',
        "tags": ["updated", "test"],
        "silence_time": '{"start": "10:00", "end": "19:00"}',
    }

    update_response = await client.patch(
        "/api/v1/alerts/detail", json=update_data
    )
    assert update_response.status_code == 200
    assert update_response.json() is True

    # Проверяем обновление
    detail_response = await client.get(
        "/api/v1/alerts/detail", params={"alert_id": alert_id}
    )
    detail_data = detail_response.json()
    assert detail_data["alert_name"] == update_data["alert_name"]
    assert detail_data["description"] == update_data["description"]
    assert detail_data["tags"] == update_data["tags"]


@pytest.mark.asyncio
async def test_duplicate_alert(
    client: AsyncClient, created_resources: dict[str, list[UUID]]
):
    """Тест дублирования алерта."""
    # Создаем алерт для дублирования
    indicators_response = await client.get(
        "/api/v1/indicators/autocomplete", params={"limit": 1}
    )
    assert indicators_response.status_code == 200
    indicator_id = indicators_response.json()["indicators"][0]["indicator_id"]

    groups_response = await client.get(
        "/api/v1/group_rules/autocomplete", params={"limit": 1}
    )
    assert groups_response.status_code == 200
    group_rule_id = groups_response.json()["group_rules"][0]["group_rule_id"]

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
    assert create_response.status_code == 200

    # Находим созданный алерт
    search_response = await client.get(
        "/api/v1/alerts/search", params={"query": alert_data["alert_name"]}
    )
    alert_id = search_response.json()["alerts"][0]["alert_id"]
    created_resources["alerts"].append(alert_id)

    # Дублируем алерт
    duplicate_response = await client.post(f"/api/v1/{alert_id}/duplicate")
    assert duplicate_response.status_code == 200
    assert duplicate_response.json() is True

    # Проверяем что дубликат создан
    search_response = await client.get(
        "/api/v1/alerts/search", params={"query": alert_data["alert_name"]}
    )
    alerts = search_response.json()["alerts"]
    assert len(alerts) >= 2

    # Находим дублированный алерт
    duplicated_alert = None
    for alert in alerts:
        if alert["alert_id"] != alert_id and "copy -" in alert.get(
            "alert_name", ""
        ):
            duplicated_alert = alert
            created_resources["alerts"].append(alert["alert_id"])
            break

    assert duplicated_alert is not None, "Дублированный алерт не найден"


@pytest.mark.asyncio
async def test_get_alert_detail(
    client: AsyncClient, created_resources: dict[str, list[UUID]]
):
    """Тест получения деталей алерта."""
    # Создаем алерт
    indicators_response = await client.get(
        "/api/v1/indicators/autocomplete", params={"limit": 1}
    )
    assert indicators_response.status_code == 200
    indicator_id = indicators_response.json()["indicators"][0]["indicator_id"]

    groups_response = await client.get(
        "/api/v1/group_rules/autocomplete", params={"limit": 1}
    )
    assert groups_response.status_code == 200
    group_rule_id = groups_response.json()["group_rules"][0]["group_rule_id"]

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
    assert create_response.status_code == 200

    # Находим созданный алерт
    search_response = await client.get(
        "/api/v1/alerts/search", params={"query": alert_data["alert_name"]}
    )
    alert_id = search_response.json()["alerts"][0]["alert_id"]
    created_resources["alerts"].append(alert_id)

    # Получаем детали
    detail_response = await client.get(
        "/api/v1/alerts/detail", params={"alert_id": alert_id}
    )
    assert detail_response.status_code == 200
    detail_data = detail_response.json()

    assert detail_data["alert_id"] == alert_id
    assert detail_data["alert_name"] == alert_data["alert_name"]
    assert "group_rule" in detail_data
