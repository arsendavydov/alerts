"""
Интеграционные тесты для indicators endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_indicators_autocomplete(client: AsyncClient):
    """Тест автодополнения индикаторов."""
    response = await client.get("/api/v1/indicators/autocomplete")
    assert response.status_code == 200
    data = response.json()
    assert "indicators" in data
    assert "total" in data
    assert isinstance(data["indicators"], list)
    assert isinstance(data["total"], int)


@pytest.mark.asyncio
async def test_indicators_autocomplete_with_query(client: AsyncClient):
    """Тест автодополнения индикаторов с запросом."""
    response = await client.get(
        "/api/v1/indicators/autocomplete", params={"query": "test"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "indicators" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_indicators_autocomplete_with_limit(client: AsyncClient):
    """Тест автодополнения индикаторов с лимитом."""
    response = await client.get(
        "/api/v1/indicators/autocomplete", params={"limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    assert "indicators" in data
    if data["indicators"]:
        assert len(data["indicators"]) <= 10
