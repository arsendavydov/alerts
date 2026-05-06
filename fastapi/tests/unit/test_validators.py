"""
Модульные тесты для валидации через Pydantic Literal типы в роутерах.
Валидация теперь происходит автоматически через FastAPI/Pydantic, поэтому
эти тесты проверяют работу Literal типов в эндпоинтах.
"""

from typing import Literal

import pytest
import pytest_asyncio
from httpx import AsyncClient

from fastapi import FastAPI


@pytest.fixture
def app():
    """Создает тестовое FastAPI приложение."""
    app = FastAPI()

    @app.get("/test-order-by")
    async def test_order_by(
        order_by: Literal["field1", "field2", "field3"] = "field1",
        order_dir: Literal["asc", "desc"] = "asc",
    ):
        return {"order_by": order_by, "order_dir": order_dir}

    return app


@pytest_asyncio.fixture
async def client(app):
    """Асинхронный тестовый клиент."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestPydanticValidation:
    """Тесты для валидации через Pydantic Literal типы."""

    @pytest.mark.asyncio
    async def test_valid_order_by(self, client):
        """Тест валидных значений order_by."""
        response = await client.get("/test-order-by?order_by=field1")
        assert response.status_code == 200
        assert response.json()["order_by"] == "field1"

        response = await client.get("/test-order-by?order_by=field2")
        assert response.status_code == 200
        assert response.json()["order_by"] == "field2"

    @pytest.mark.asyncio
    async def test_invalid_order_by(self, client):
        """Тест невалидного значения order_by."""
        response = await client.get("/test-order-by?order_by=invalid_field")
        assert response.status_code == 422  # Pydantic validation error

    @pytest.mark.asyncio
    async def test_valid_order_dir(self, client):
        """Тест валидных значений order_dir."""
        response = await client.get("/test-order-by?order_dir=asc")
        assert response.status_code == 200
        assert response.json()["order_dir"] == "asc"

        response = await client.get("/test-order-by?order_dir=desc")
        assert response.status_code == 200
        assert response.json()["order_dir"] == "desc"

    @pytest.mark.asyncio
    async def test_invalid_order_dir(self, client):
        """Тест невалидного значения order_dir."""
        response = await client.get("/test-order-by?order_dir=invalid")
        assert response.status_code == 422  # Pydantic validation error

    @pytest.mark.asyncio
    async def test_default_values(self, client):
        """Тест значений по умолчанию."""
        response = await client.get("/test-order-by")
        assert response.status_code == 200
        assert response.json()["order_by"] == "field1"
        assert response.json()["order_dir"] == "asc"
