"""
Модульные тесты для IndicatorsService.
"""

from typing import ClassVar
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from starlette.exceptions import HTTPException

from repositories.indicators_repository import IndicatorsRepository
from services.indicators_service import IndicatorsService

# Включаем поддержку async тестов
pytestmark = pytest.mark.asyncio


class TestIndicatorsService:
    """Тесты для IndicatorsService."""

    @pytest.fixture
    def mock_repo(self):
        """Мок репозитория."""
        return AsyncMock(spec=IndicatorsRepository)

    @pytest.fixture
    def service(self, mock_repo):
        """Экземпляр IndicatorsService с моком репозитория."""
        return IndicatorsService(repository=mock_repo)

    async def test_get_indicators_autocomplete_success(
        self, service, mock_repo
    ):
        """Тест успешного автодополнения индикаторов."""
        indicator_id = uuid4()
        mock_repo.autocomplete_indicators.return_value = [
            {"id": indicator_id, "indicator_name": "test_indicator"}
        ]

        result = await service.get_indicators_autocomplete("test", 10)

        assert len(result["indicators"]) == 1
        assert result["indicators"][0]["indicator_id"] == str(indicator_id)
        assert result["indicators"][0]["indicator_name"] == "test_indicator"
        assert result["total"] == 1

    async def test_get_indicators_autocomplete_empty(self, service, mock_repo):
        """Тест автодополнения без результатов."""
        mock_repo.autocomplete_indicators.return_value = []

        result = await service.get_indicators_autocomplete("nonexistent", 10)

        assert result["total"] == 0
        assert len(result["indicators"]) == 0

    async def test_get_indicators_autocomplete_error(self, service, mock_repo):
        """Тест обработки ошибки при автодополнении."""
        mock_repo.autocomplete_indicators.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.get_indicators_autocomplete("test", 10)

        assert exc_info.value.status_code == 500

    async def test_get_indicators_autocomplete_with_mapping_row(
        self, service, mock_repo
    ):
        """Покрыть ветку _as_dict через _mapping."""

        class RowObj:
            _mapping: ClassVar[dict[str, object]] = {
                "id": uuid4(),
                "indicator_name": "mapped",
            }

        mock_repo.autocomplete_indicators.return_value = [RowObj()]
        result = await service.get_indicators_autocomplete("m", 10)
        assert result["total"] == 1
        assert result["indicators"][0]["indicator_name"] == "mapped"

    async def test_get_indicators_autocomplete_with_keys_row(
        self, service, mock_repo
    ):
        """Покрыть ветку _as_dict через keys()/index."""

        class RowObj:
            def keys(self):
                return ["id", "indicator_name"]

            def __getitem__(self, idx):
                return [uuid4(), "keyed"][idx]

        mock_repo.autocomplete_indicators.return_value = [RowObj()]
        result = await service.get_indicators_autocomplete("k", 10)
        assert result["indicators"][0]["indicator_name"] == "keyed"

    async def test_get_indicators_autocomplete_with_broken_keys_row(
        self, service, mock_repo
    ):
        """Покрыть ветку _as_dict с исключением внутри keys()/index."""

        class BadRow:
            def keys(self):
                raise RuntimeError("broken")

        mock_repo.autocomplete_indicators.return_value = [BadRow()]
        result = await service.get_indicators_autocomplete("x", 10)
        assert result["total"] == 1

    async def test_as_dict_plain_object_returns_empty(self, service):
        """Покрыть финальную ветку _as_dict -> {}."""
        assert service._as_dict(object()) == {}
