"""
Интеграционные тесты для group_rules endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_group_rules_autocomplete(client: AsyncClient):
    """Тест автодополнения групповых правил."""
    response = await client.get("/api/v1/group_rules/autocomplete")
    assert response.status_code == 200
    data = response.json()
    assert "group_rules" in data
    assert "total" in data
    assert isinstance(data["group_rules"], list)
    assert isinstance(data["total"], int)


@pytest.mark.asyncio
async def test_group_rules_autocomplete_with_query(client: AsyncClient):
    """Тест автодополнения групповых правил с запросом."""
    response = await client.get(
        "/api/v1/group_rules/autocomplete", params={"query": "test"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "group_rules" in data


@pytest.mark.asyncio
async def test_group_rules_autocomplete_with_limit(client: AsyncClient):
    """Тест автодополнения групповых правил с лимитом."""
    response = await client.get(
        "/api/v1/group_rules/autocomplete", params={"limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    assert "group_rules" in data
    if data["group_rules"]:
        assert len(data["group_rules"]) <= 10
