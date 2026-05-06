"""
Модульные тесты для FeedbackRepository.
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from repositories.feedback_repository import FeedbackRepository

pytestmark = pytest.mark.asyncio


def _session_cm(session: AsyncMock):
    cm = AsyncMock()
    cm.__aenter__.return_value = session
    cm.__aexit__.return_value = None
    return cm


class TestFeedbackRepository:
    """Тесты для FeedbackRepository."""

    @pytest.fixture
    def repo(self):
        return FeedbackRepository()

    @pytest.fixture
    def test_uuid(self):
        return uuid4()

    @patch("repositories.feedback_repository.async_session_scope")
    async def test_get_feedback_by_status_and_contact(
        self, mock_session_scope, repo, test_uuid
    ):
        feedback_id = uuid4()
        row = Mock()
        row._mapping = {"id": feedback_id, "score": 5}
        res = Mock()
        res.one_or_none.return_value = row
        session = AsyncMock()
        session.execute = AsyncMock(return_value=res)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.get_feedback_by_status_and_contact(
            test_uuid, "test_user"
        )

        assert result is not None
        assert result._mapping["id"] == feedback_id
        session.execute.assert_awaited_once()

    @patch("repositories.feedback_repository.async_session_scope")
    async def test_get_feedback_by_status_and_contact_not_found(
        self, mock_session_scope, repo, test_uuid
    ):
        res = Mock()
        res.one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=res)
        mock_session_scope.return_value = _session_cm(session)

        assert (
            await repo.get_feedback_by_status_and_contact(
                test_uuid, "test_user"
            )
            is None
        )

    @patch("repositories.feedback_repository.async_session_scope")
    async def test_create_feedback(self, mock_session_scope, repo, test_uuid):
        feedback_id = uuid4()
        ins_res = Mock()
        ins_res.scalar_one.return_value = feedback_id
        session = AsyncMock()
        session.execute = AsyncMock(return_value=ins_res)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.create_feedback(
            feedback_id, test_uuid, "test_user", 5
        )

        assert result == feedback_id
        session.execute.assert_awaited_once()

    @patch("repositories.feedback_repository.async_session_scope")
    async def test_update_feedback(self, mock_session_scope, repo, test_uuid):
        feedback_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock()
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.update_feedback(feedback_id, 4) is True
        session.execute.assert_awaited_once()

    @patch("repositories.feedback_repository.async_session_scope")
    async def test_delete_feedback(self, mock_session_scope, repo, test_uuid):
        feedback_id = uuid4()
        first = Mock()
        first.scalar_one_or_none.return_value = feedback_id
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[first, Mock()])
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.delete_feedback(test_uuid, "test_user") is True
        assert session.execute.await_count == 2

    @patch("repositories.feedback_repository.async_session_scope")
    async def test_delete_feedback_not_found(
        self, mock_session_scope, repo, test_uuid
    ):
        first = Mock()
        first.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=first)
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(ValueError, match="Фидбек не найден"):
            await repo.delete_feedback(test_uuid, "test_user")

    @patch("repositories.feedback_repository.async_session_scope")
    async def test_create_feedback_error(
        self, mock_session_scope, repo, test_uuid
    ):
        feedback_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("DB error"))
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(Exception, match="DB error"):
            await repo.create_feedback(feedback_id, test_uuid, "test_user", 5)

    @patch("repositories.feedback_repository.async_session_scope")
    async def test_update_feedback_error(
        self, mock_session_scope, repo, test_uuid
    ):
        feedback_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("DB error"))
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(Exception, match="DB error"):
            await repo.update_feedback(feedback_id, 4)

    @patch("repositories.feedback_repository.async_session_scope")
    async def test_delete_feedback_error(
        self, mock_session_scope, repo, test_uuid
    ):
        feedback_id = uuid4()
        first = Mock()
        first.scalar_one_or_none.return_value = feedback_id
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[first, Exception("DB error")])
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(Exception, match="DB error"):
            await repo.delete_feedback(test_uuid, "test_user")

    @patch("repositories.feedback_repository.async_session_scope")
    async def test_create_feedback_different_scores(
        self, mock_session_scope, repo, test_uuid
    ):
        feedback_id = uuid4()
        ins_res = Mock()
        ins_res.scalar_one.return_value = feedback_id
        session = AsyncMock()
        session.execute = AsyncMock(return_value=ins_res)
        mock_session_scope.return_value = _session_cm(session)

        for score in [1, 3, 5]:
            result = await repo.create_feedback(
                uuid4(), test_uuid, "test_user", score
            )
            assert result == feedback_id
