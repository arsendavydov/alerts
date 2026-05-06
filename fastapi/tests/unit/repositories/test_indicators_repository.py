"""
Модульные тесты для IndicatorsRepository.
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from repositories.indicators_repository import IndicatorsRepository

pytestmark = pytest.mark.asyncio


def _session_cm(session: AsyncMock):
    cm = AsyncMock()
    cm.__aenter__.return_value = session
    cm.__aexit__.return_value = None
    return cm


class TestIndicatorsRepository:
    """Тесты для IndicatorsRepository."""

    @pytest.fixture
    def repo(self):
        return IndicatorsRepository()

    @pytest.fixture
    def test_uuid(self):
        return uuid4()

    @patch("repositories.indicators_repository.async_session_scope")
    async def test_autocomplete_indicators_with_query(
        self, mock_session_scope, repo, test_uuid
    ):
        row_a = Mock()
        row_a._mapping = {"id": test_uuid, "indicator_name": "Indicator A"}
        row_b = Mock()
        row_b._mapping = {"id": uuid4(), "indicator_name": "Indicator B"}
        data_res = Mock()
        data_res.all.return_value = [row_a, row_b]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=data_res)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.autocomplete_indicators("Indicator", 10)

        assert len(result) == 2
        assert result[0]._mapping["indicator_name"] == "Indicator A"
        session.execute.assert_awaited_once()

    @patch("repositories.indicators_repository.async_session_scope")
    async def test_autocomplete_indicators_without_query(
        self, mock_session_scope, repo, test_uuid
    ):
        row = Mock()
        row._mapping = {"id": test_uuid, "indicator_name": "Indicator A"}
        data_res = Mock()
        data_res.all.return_value = [row]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=data_res)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.autocomplete_indicators(None, 10)

        assert len(result) == 1
        session.execute.assert_awaited_once()
