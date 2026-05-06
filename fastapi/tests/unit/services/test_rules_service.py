"""
Модульные тесты для RulesService.
"""

from typing import ClassVar
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from starlette.exceptions import HTTPException

from repositories.rules_repository import RulesRepository
from services.rules_service import RulesService

# Включаем поддержку async тестов
pytestmark = pytest.mark.asyncio


class TestRulesService:
    """Тесты для RulesService."""

    @pytest.fixture
    def mock_repo(self):
        """Мок репозитория."""
        return AsyncMock(spec=RulesRepository)

    @pytest.fixture
    def service(self, mock_repo):
        """Экземпляр RulesService с моком репозитория."""
        return RulesService(repository=mock_repo)

    async def test_autocomplete_group_rules_success(self, service, mock_repo):
        """Тест успешного автокомплита групп правил."""
        group_rule_id = uuid4()
        mock_repo.search_group_rules.return_value = (
            [
                {
                    "id": group_rule_id,
                    "description": "test_description",
                    "image": "test_image",
                }
            ],
            1,
        )
        result = await service.autocomplete_group_rules("test", 10)

        assert result.total == 1
        assert len(result.group_rules) == 1
        assert result.group_rules[0].group_rule_id == group_rule_id
        assert result.group_rules[0].description == "test_description"

    async def test_autocomplete_group_rules_empty(self, service, mock_repo):
        """Тест автокомплита без результатов."""
        mock_repo.search_group_rules.return_value = ([], 0)

        result = await service.autocomplete_group_rules("nonexistent", 10)

        assert result.total == 0
        assert len(result.group_rules) == 0

    async def test_autocomplete_group_rules_error(self, service, mock_repo):
        """Тест обработки ошибки при автокомплите."""
        mock_repo.search_group_rules.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.autocomplete_group_rules("test", 10)

        assert exc_info.value.status_code == 500

    async def test_autocomplete_group_rules_with_mapping_row(
        self, service, mock_repo
    ):
        """Покрыть _as_dict ветку _mapping."""

        class RowObj:
            _mapping: ClassVar[dict[str, object]] = {
                "id": uuid4(),
                "description": "D",
                "image": "I",
            }

        mock_repo.search_group_rules.return_value = ([RowObj()], 1)
        result = await service.autocomplete_group_rules("d", 10)
        assert result.total == 1
        assert result.group_rules[0].description == "D"

    async def test_autocomplete_group_rules_with_keys_row(
        self, service, mock_repo
    ):
        """Покрыть _as_dict ветку keys()/index."""

        class RowObj:
            def keys(self):
                return ["id", "description", "image"]

            def __getitem__(self, idx):
                return [uuid4(), "KD", "KI"][idx]

        mock_repo.search_group_rules.return_value = ([RowObj()], 1)
        result = await service.autocomplete_group_rules("k", 10)
        assert result.group_rules[0].description == "KD"

    async def test_as_dict_plain_object_returns_empty(self, service):
        """Покрыть финальную ветку _as_dict -> {}."""
        assert service._as_dict(object()) == {}

    async def test_as_dict_keys_index_error_returns_empty(self, service):
        """Покрыть ветку except внутри _as_dict."""

        class BadRow:
            def keys(self):
                return ["id"]

            def __getitem__(self, idx):
                raise IndexError("out")

        assert service._as_dict(BadRow()) == {}
