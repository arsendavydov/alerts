"""
Модульные тесты для роутера rules.
Используют моки сервисов для изоляции от БД.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from contracts.service_protocols import RulesServiceProtocol
from dependencies import get_rules_service
from httpx import AsyncClient

from fastapi import FastAPI
from routers.rules import router
from schemas.group_rules import (
    GroupRuleAutocompleteItem,
    GroupRuleAutocompleteResponse,
)


class TestRulesRouter:
    """Тесты для роутера rules."""

    @pytest.fixture
    def mock_service(self):
        """Мок сервиса."""
        return AsyncMock(spec=RulesServiceProtocol)

    @pytest.fixture
    def app(self, mock_service):
        """Создает FastAPI приложение с моком сервиса."""
        app = FastAPI()
        app.include_router(router)

        def override_get_rules_service():
            return mock_service

        app.dependency_overrides[get_rules_service] = (
            override_get_rules_service
        )
        return app

    @pytest_asyncio.fixture
    async def client(self, app):
        """Асинхронный тестовый клиент."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_autocomplete_group_rules(self, client, mock_service):
        """Тест автокомплита групп правил."""
        mock_service.autocomplete_group_rules.return_value = (
            GroupRuleAutocompleteResponse(
                group_rules=[
                    GroupRuleAutocompleteItem(
                        group_rule_id=uuid4(), description="Rule A", image=None
                    )
                ],
                total=1,
            )
        )

        response = await client.get(
            "/alerts/api/v1/group_rules/autocomplete?query=test&limit=10"
        )

        assert response.status_code == 200
        assert response.json()["total"] == 1
        mock_service.autocomplete_group_rules.assert_called_once_with(
            "test", 10
        )

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_autocomplete_group_rules_without_query(
        self, client, mock_service
    ):
        """Тест автокомплита групп правил без query."""
        mock_service.autocomplete_group_rules.return_value = (
            GroupRuleAutocompleteResponse(group_rules=[], total=0)
        )

        response = await client.get(
            "/alerts/api/v1/group_rules/autocomplete?limit=50"
        )

        assert response.status_code == 200
        assert response.json()["total"] == 0
        mock_service.autocomplete_group_rules.assert_called_once_with(None, 50)

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_autocomplete_group_rules_default_limit(
        self, client, mock_service
    ):
        """Тест автокомплита групп правил с дефолтным limit."""
        mock_service.autocomplete_group_rules.return_value = (
            GroupRuleAutocompleteResponse(group_rules=[], total=0)
        )

        response = await client.get(
            "/alerts/api/v1/group_rules/autocomplete?query=test"
        )

        assert response.status_code == 200
        mock_service.autocomplete_group_rules.assert_called_once_with(
            "test", 50
        )
