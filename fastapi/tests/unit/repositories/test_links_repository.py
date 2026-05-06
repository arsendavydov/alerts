"""
Модульные тесты для LinksRepository.
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from repositories.links_repository import LinksRepository

pytestmark = pytest.mark.asyncio


def _session_cm(session: AsyncMock):
    cm = AsyncMock()
    cm.__aenter__.return_value = session
    cm.__aexit__.return_value = None
    return cm


class TestLinksRepository:
    """Тесты для LinksRepository."""

    @pytest.fixture
    def repo(self):
        return LinksRepository()

    @pytest.fixture
    def test_uuid(self):
        return uuid4()

    @patch("repositories.links_repository.async_session_scope")
    async def test_get_links_by_alert(
        self, mock_session_scope, repo, test_uuid
    ):
        link_id = uuid4()
        row = Mock()
        row._mapping = {
            "id": link_id,
            "alert": test_uuid,
            "link_name": "Link 1",
            "link_url": "http://link1.com",
        }
        data_res = Mock()
        data_res.all.return_value = [row]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=data_res)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.get_links_by_alert(test_uuid)

        assert len(result) == 1
        assert result[0]._mapping["id"] == link_id
        session.execute.assert_awaited_once()

    @patch("repositories.links_repository.async_session_scope")
    async def test_get_links_by_alert_empty(
        self, mock_session_scope, repo, test_uuid
    ):
        data_res = Mock()
        data_res.all.return_value = []
        session = AsyncMock()
        session.execute = AsyncMock(return_value=data_res)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.get_links_by_alert(test_uuid)

        assert result == []

    @patch("repositories.links_repository.async_session_scope")
    async def test_get_link_by_id(self, mock_session_scope, repo, test_uuid):
        link_id = uuid4()
        alert_id = uuid4()
        row = Mock()
        row._mapping = {
            "id": link_id,
            "alert": alert_id,
            "alert_name": "Alert Name",
            "link_name": "Link Name",
            "link_url": "http://link.com",
        }
        data_res = Mock()
        data_res.one_or_none.return_value = row
        session = AsyncMock()
        session.execute = AsyncMock(return_value=data_res)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.get_link_by_id(link_id)

        assert result is not None
        assert result._mapping["id"] == link_id

    @patch("repositories.links_repository.async_session_scope")
    async def test_get_link_by_id_not_found(self, mock_session_scope, repo):
        link_id = uuid4()
        data_res = Mock()
        data_res.one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=data_res)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.get_link_by_id(link_id) is None

    @patch("repositories.links_repository.async_session_scope")
    async def test_create_link(self, mock_session_scope, repo, test_uuid):
        link_id = uuid4()
        ins_res = Mock()
        ins_res.scalar_one.return_value = link_id
        session = AsyncMock()
        session.execute = AsyncMock(return_value=ins_res)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.create_link(
            test_uuid, "Test Link", "http://test.com"
        )

        assert result == link_id
        session.execute.assert_awaited_once()

    @patch("repositories.links_repository.async_session_scope")
    async def test_create_link_error(
        self, mock_session_scope, repo, test_uuid
    ):
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("DB error"))
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(Exception, match="DB error"):
            await repo.create_link(test_uuid, "Test Link", "http://test.com")

    @patch("repositories.links_repository.async_session_scope")
    async def test_update_link(self, mock_session_scope, repo, test_uuid):
        link_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock()
        mock_session_scope.return_value = _session_cm(session)

        assert (
            await repo.update_link(link_id, link_name="Updated Link") is True
        )
        session.execute.assert_awaited_once()

    async def test_update_link_no_changes(self, repo, test_uuid):
        link_id = uuid4()
        with patch(
            "repositories.links_repository.async_session_scope"
        ) as mock_scope:
            assert await repo.update_link(link_id) is True
            mock_scope.assert_not_called()

    @patch("repositories.links_repository.async_session_scope")
    async def test_update_link_only_url(
        self, mock_session_scope, repo, test_uuid
    ):
        link_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock()
        mock_session_scope.return_value = _session_cm(session)

        assert (
            await repo.update_link(link_id, link_url="http://updated.com")
            is True
        )
        session.execute.assert_awaited_once()

    @patch("repositories.links_repository.async_session_scope")
    async def test_update_link_both_fields(
        self, mock_session_scope, repo, test_uuid
    ):
        link_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock()
        mock_session_scope.return_value = _session_cm(session)

        assert (
            await repo.update_link(
                link_id,
                link_name="Updated Name",
                link_url="http://updated.com",
            )
            is True
        )
        session.execute.assert_awaited_once()

    @patch("repositories.links_repository.async_session_scope")
    async def test_update_link_error(
        self, mock_session_scope, repo, test_uuid
    ):
        link_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("DB error"))
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(Exception, match="DB error"):
            await repo.update_link(link_id, link_name="Updated")

    @patch("repositories.links_repository.async_session_scope")
    async def test_delete_link(self, mock_session_scope, repo, test_uuid):
        link_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock()
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.delete_link(link_id) is True
        session.execute.assert_awaited_once()

    @patch("repositories.links_repository.async_session_scope")
    async def test_check_link_exists_true(
        self, mock_session_scope, repo, test_uuid
    ):
        link_id = uuid4()
        res = Mock()
        res.scalar_one_or_none.return_value = link_id
        session = AsyncMock()
        session.execute = AsyncMock(return_value=res)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.check_link_exists(link_id) is True

    @patch("repositories.links_repository.async_session_scope")
    async def test_check_link_exists_false(
        self, mock_session_scope, repo, test_uuid
    ):
        link_id = uuid4()
        res = Mock()
        res.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=res)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.check_link_exists(link_id) is False
