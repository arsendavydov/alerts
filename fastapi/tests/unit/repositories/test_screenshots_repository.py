"""
Модульные тесты для ScreenshotsRepository.
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from repositories.screenshots_repository import ScreenshotsRepository

pytestmark = pytest.mark.asyncio


def _session_cm(session: AsyncMock):
    cm = AsyncMock()
    cm.__aenter__.return_value = session
    cm.__aexit__.return_value = None
    return cm


class TestScreenshotsRepository:
    """Тесты для ScreenshotsRepository."""

    @pytest.fixture
    def repo(self):
        return ScreenshotsRepository()

    @patch("repositories.screenshots_repository.async_session_scope")
    async def test_search_screenshots_with_query(
        self, mock_session_scope, repo
    ):
        screenshot_id = uuid4()
        row = Mock()
        row._mapping = {
            "id": screenshot_id,
            "name": "test",
            "description": "description",
            "image_data": '{"url": "test"}',
        }
        count_res = Mock()
        count_res.scalar_one.return_value = 1
        data_res = Mock()
        data_res.all.return_value = [row]
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_res, data_res])
        mock_session_scope.return_value = _session_cm(session)

        rows, total = await repo.search_screenshots(
            query="test", limit=50, offset=0
        )

        assert total == 1
        assert len(rows) == 1
        assert rows[0]._mapping["id"] == screenshot_id
        assert session.execute.await_count == 2

    @patch("repositories.screenshots_repository.async_session_scope")
    async def test_search_screenshots_without_query(
        self, mock_session_scope, repo
    ):
        screenshot_id = uuid4()
        row = Mock()
        row._mapping = {
            "id": screenshot_id,
            "name": "test",
            "description": "desc",
            "image_data": "[]",
        }
        count_res = Mock()
        count_res.scalar_one.return_value = 1
        data_res = Mock()
        data_res.all.return_value = [row]
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_res, data_res])
        mock_session_scope.return_value = _session_cm(session)

        rows, total = await repo.search_screenshots(limit=50, offset=0)

        assert total == 1
        assert len(rows) == 1

    @patch("repositories.screenshots_repository.async_session_scope")
    async def test_search_screenshots_with_sorting(
        self, mock_session_scope, repo
    ):
        screenshot_id = uuid4()
        row = Mock()
        row._mapping = {
            "id": screenshot_id,
            "name": "test",
            "description": "desc",
            "image_data": "[]",
        }
        count_res = Mock()
        count_res.scalar_one.return_value = 1
        data_res = Mock()
        data_res.all.return_value = [row]
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_res, data_res])
        mock_session_scope.return_value = _session_cm(session)

        _rows, total = await repo.search_screenshots(
            query="test", order_by="name", order_dir="desc", limit=50, offset=0
        )

        assert total == 1

    @patch("repositories.screenshots_repository.async_session_scope")
    async def test_get_screenshot_by_id(self, mock_session_scope, repo):
        screenshot_id = uuid4()
        row = Mock()
        row._mapping = {
            "id": screenshot_id,
            "name": "test",
            "description": "description",
            "image_data": '{"url": "test"}',
        }
        res = Mock()
        res.one_or_none.return_value = row
        session = AsyncMock()
        session.execute = AsyncMock(return_value=res)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.get_screenshot_by_id(screenshot_id)

        assert result is not None
        assert result._mapping["id"] == screenshot_id

    @patch("repositories.screenshots_repository.async_session_scope")
    async def test_get_screenshot_by_id_not_found(
        self, mock_session_scope, repo
    ):
        screenshot_id = uuid4()
        res = Mock()
        res.one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=res)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.get_screenshot_by_id(screenshot_id) is None

    @patch("repositories.screenshots_repository.async_session_scope")
    async def test_create_screenshot(self, mock_session_scope, repo):
        screenshot_id = uuid4()
        ins = Mock()
        ins.scalar_one.return_value = screenshot_id
        session = AsyncMock()
        session.execute = AsyncMock(return_value=ins)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.create_screenshot(
            "test", "description", '{"url": "test"}'
        )

        assert result == screenshot_id

    @patch("repositories.screenshots_repository.async_session_scope")
    async def test_check_screenshot_exists(self, mock_session_scope, repo):
        screenshot_id = uuid4()
        r = Mock()
        r.scalar_one_or_none.return_value = screenshot_id
        session = AsyncMock()
        session.execute = AsyncMock(return_value=r)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.check_screenshot_exists(screenshot_id) is True

    @patch("repositories.screenshots_repository.async_session_scope")
    async def test_check_screenshot_exists_not_found(
        self, mock_session_scope, repo
    ):
        screenshot_id = uuid4()
        r = Mock()
        r.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=r)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.check_screenshot_exists(screenshot_id) is False

    @patch("repositories.screenshots_repository.async_session_scope")
    async def test_update_screenshot(self, mock_session_scope, repo):
        screenshot_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock()
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.update_screenshot(
            screenshot_id=screenshot_id,
            name="updated_name",
            description="updated_desc",
        )
        session.execute.assert_awaited_once()

    async def test_update_screenshot_no_updates(self, repo):
        screenshot_id = uuid4()
        with patch(
            "repositories.screenshots_repository.async_session_scope"
        ) as mock_scope:
            assert (
                await repo.update_screenshot(screenshot_id=screenshot_id)
                is True
            )
            mock_scope.assert_not_called()

    @patch("repositories.screenshots_repository.async_session_scope")
    async def test_delete_screenshot(self, mock_session_scope, repo):
        screenshot_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock()
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.delete_screenshot(screenshot_id) is True
        session.execute.assert_awaited_once()

    @patch("repositories.screenshots_repository.async_session_scope")
    async def test_update_screenshot_with_image_data(
        self, mock_session_scope, repo
    ):
        screenshot_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock()
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.update_screenshot(
            screenshot_id=screenshot_id, image_data='{"url": "updated.jpg"}'
        )
        session.execute.assert_awaited_once()

    @patch("repositories.screenshots_repository.async_session_scope")
    async def test_update_screenshot_error(self, mock_session_scope, repo):
        screenshot_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("DB error"))
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(Exception, match="DB error"):
            await repo.update_screenshot(
                screenshot_id=screenshot_id, name="updated"
            )
