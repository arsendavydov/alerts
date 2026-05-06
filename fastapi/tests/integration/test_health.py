"""
Интеграционные тесты для health endpoint.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Тест health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.text.strip() == "OK"
