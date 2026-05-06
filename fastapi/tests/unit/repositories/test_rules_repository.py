"""
Модульные тесты для RulesRepository.
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from repositories.rules_repository import RulesRepository

pytestmark = pytest.mark.asyncio


def _session_cm(session: AsyncMock):
    cm = AsyncMock()
    cm.__aenter__.return_value = session
    cm.__aexit__.return_value = None
    return cm


class TestRulesRepository:
    """Тесты для RulesRepository."""

    @pytest.fixture
    def repo(self):
        return RulesRepository()

    @pytest.fixture
    def test_uuid(self):
        return uuid4()

    @patch("repositories.rules_repository.async_session_scope")
    async def test_search_group_rules_with_query(
        self, mock_session_scope, repo, test_uuid
    ):
        count_res = Mock()
        count_res.scalar_one.return_value = 2
        row_a = Mock()
        row_a._mapping = {
            "id": test_uuid,
            "description": "Rule A",
            "image": "image_a",
        }
        row_b = Mock()
        row_b._mapping = {
            "id": uuid4(),
            "description": "Rule B",
            "image": "image_b",
        }
        data_res = Mock()
        data_res.all.return_value = [row_a, row_b]
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_res, data_res])
        mock_session_scope.return_value = _session_cm(session)

        rows, total = await repo.search_group_rules("Rule", 50)

        assert len(rows) == 2
        assert total == 2
        assert session.execute.await_count == 2

    @patch("repositories.rules_repository.async_session_scope")
    async def test_search_group_rules_without_query(
        self, mock_session_scope, repo, test_uuid
    ):
        count_res = Mock()
        count_res.scalar_one.return_value = 1
        row = Mock()
        row._mapping = {
            "id": test_uuid,
            "description": "Rule A",
            "image": "image_a",
        }
        data_res = Mock()
        data_res.all.return_value = [row]
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_res, data_res])
        mock_session_scope.return_value = _session_cm(session)

        rows, total = await repo.search_group_rules(None, 50)

        assert len(rows) == 1
        assert total == 1
        assert session.execute.await_count == 2
