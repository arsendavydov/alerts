"""
Модульные тесты для DTRepository.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest

from repositories.dt_repository import DTRepository

pytestmark = pytest.mark.asyncio


def _session_cm(session: AsyncMock):
    cm = AsyncMock()
    cm.__aenter__.return_value = session
    cm.__aexit__.return_value = None
    return cm


def _dt_entity(dt_id, alert_id):
    m = MagicMock()
    m.id = dt_id
    m.alert = alert_id
    m.content = '{"old": "data"}'
    m.auto_create = False
    m.silence_time = None
    return m


class TestDTRepository:
    """Тесты для DTRepository."""

    @pytest.fixture
    def repo(self):
        return DTRepository()

    @pytest.fixture
    def test_uuid(self):
        return uuid4()

    @patch("repositories.dt_repository.async_session_scope")
    async def test_check_alert_exists_true(
        self, mock_session_scope, repo, test_uuid
    ):
        r = Mock()
        r.scalar_one_or_none.return_value = test_uuid
        session = AsyncMock()
        session.execute = AsyncMock(return_value=r)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.check_alert_exists(test_uuid) is True

    @patch("repositories.dt_repository.async_session_scope")
    async def test_check_alert_exists_false(
        self, mock_session_scope, repo, test_uuid
    ):
        r = Mock()
        r.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=r)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.check_alert_exists(test_uuid) is False

    @patch("repositories.dt_repository.async_session_scope")
    async def test_get_dt_by_alert_id(
        self, mock_session_scope, repo, test_uuid
    ):
        dt_id = uuid4()
        row = Mock()
        row._mapping = {
            "id": dt_id,
            "alert": test_uuid,
            "content": '{"key": "value"}',
            "auto_create": True,
            "silence_time": None,
        }
        res = Mock()
        res.one_or_none.return_value = row
        session = AsyncMock()
        session.execute = AsyncMock(return_value=res)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.get_dt_by_alert_id(test_uuid)

        assert result is not None
        assert result._mapping["id"] == dt_id

    @patch("repositories.dt_repository.async_session_scope")
    async def test_check_dt_exists_true(
        self, mock_session_scope, repo, test_uuid
    ):
        dt_id = uuid4()
        r = Mock()
        r.scalar_one_or_none.return_value = dt_id
        session = AsyncMock()
        session.execute = AsyncMock(return_value=r)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.check_dt_exists(test_uuid) is True

    @patch("repositories.dt_repository.async_session_scope")
    async def test_check_dt_exists_false(
        self, mock_session_scope, repo, test_uuid
    ):
        r = Mock()
        r.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=r)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.check_dt_exists(test_uuid) is False

    @patch("repositories.dt_repository.async_session_scope")
    async def test_create_dt_with_silence_time(
        self, mock_session_scope, repo, test_uuid
    ):
        dt_id = uuid4()
        ins = Mock()
        ins.scalar_one.return_value = dt_id
        session = AsyncMock()
        session.execute = AsyncMock(return_value=ins)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.create_dt(
            test_uuid, '{"key": "value"}', True, '{"time": "1h"}'
        )

        assert result == dt_id

    @patch("repositories.dt_repository.async_session_scope")
    async def test_create_dt_without_silence_time(
        self, mock_session_scope, repo, test_uuid
    ):
        dt_id = uuid4()
        ins = Mock()
        ins.scalar_one.return_value = dt_id
        session = AsyncMock()
        session.execute = AsyncMock(return_value=ins)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.create_dt(
            test_uuid, '{"key": "value"}', True, None
        )

        assert result == dt_id

    @patch("repositories.dt_repository.async_session_scope")
    async def test_update_dt(self, mock_session_scope, repo, test_uuid):
        dt_id = uuid4()
        entity = _dt_entity(dt_id, test_uuid)
        sel = Mock()
        sel.scalar_one_or_none.return_value = entity
        session = AsyncMock()
        session.execute = AsyncMock(return_value=sel)
        mock_session_scope.return_value = _session_cm(session)

        assert (
            await repo.update_dt(test_uuid, content='{"new": "data"}') is True
        )

    @patch("repositories.dt_repository.async_session_scope")
    async def test_update_dt_not_found(
        self, mock_session_scope, repo, test_uuid
    ):
        sel = Mock()
        sel.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=sel)
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(ValueError, match="DT для алерта не найден"):
            await repo.update_dt(test_uuid, content='{"new": "data"}')

    @patch("repositories.dt_repository.async_session_scope")
    async def test_delete_dt(self, mock_session_scope, repo, test_uuid):
        dt_id = uuid4()
        sel = Mock()
        sel.scalar_one_or_none.return_value = dt_id
        del_res = Mock()
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[sel, del_res])
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.delete_dt(test_uuid) is True
        assert session.execute.await_count == 2

    @patch("repositories.dt_repository.async_session_scope")
    async def test_delete_dt_not_found(
        self, mock_session_scope, repo, test_uuid
    ):
        sel = Mock()
        sel.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=sel)
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(ValueError, match="DT для алерта не найден"):
            await repo.delete_dt(test_uuid)

    @patch("repositories.dt_repository.async_session_scope")
    async def test_update_dt_with_silence_time_empty(
        self, mock_session_scope, repo, test_uuid
    ):
        dt_id = uuid4()
        entity = _dt_entity(dt_id, test_uuid)
        sel = Mock()
        sel.scalar_one_or_none.return_value = entity
        session = AsyncMock()
        session.execute = AsyncMock(return_value=sel)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.update_dt(test_uuid, silence_time="") is True
        assert entity.silence_time is None

    @patch("repositories.dt_repository.async_session_scope")
    async def test_update_dt_no_updates(
        self, mock_session_scope, repo, test_uuid
    ):
        dt_id = uuid4()
        entity = _dt_entity(dt_id, test_uuid)
        sel = Mock()
        sel.scalar_one_or_none.return_value = entity
        session = AsyncMock()
        session.execute = AsyncMock(return_value=sel)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.update_dt(test_uuid) is True

    @patch("repositories.dt_repository.async_session_scope")
    async def test_update_dt_only_auto_create(
        self, mock_session_scope, repo, test_uuid
    ):
        dt_id = uuid4()
        entity = _dt_entity(dt_id, test_uuid)
        sel = Mock()
        sel.scalar_one_or_none.return_value = entity
        session = AsyncMock()
        session.execute = AsyncMock(return_value=sel)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.update_dt(test_uuid, auto_create=True) is True
        assert entity.auto_create is True

    @patch("repositories.dt_repository.async_session_scope")
    async def test_update_dt_with_silence_time(
        self, mock_session_scope, repo, test_uuid
    ):
        dt_id = uuid4()
        entity = _dt_entity(dt_id, test_uuid)
        sel = Mock()
        sel.scalar_one_or_none.return_value = entity
        session = AsyncMock()
        session.execute = AsyncMock(return_value=sel)
        mock_session_scope.return_value = _session_cm(session)

        assert (
            await repo.update_dt(test_uuid, silence_time='{"time": "1h"}')
            is True
        )
        assert entity.silence_time == '{"time": "1h"}'

    @patch("repositories.dt_repository.async_session_scope")
    async def test_update_dt_all_fields(
        self, mock_session_scope, repo, test_uuid
    ):
        dt_id = uuid4()
        entity = _dt_entity(dt_id, test_uuid)
        sel = Mock()
        sel.scalar_one_or_none.return_value = entity
        session = AsyncMock()
        session.execute = AsyncMock(return_value=sel)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.update_dt(
            test_uuid,
            content='{"new": "data"}',
            auto_create=True,
            silence_time='{"time": "2h"}',
        )
        assert entity.content == '{"new": "data"}'
        assert entity.auto_create is True
        assert entity.silence_time == '{"time": "2h"}'

    @patch("repositories.dt_repository.async_session_scope")
    async def test_create_dt_rollback_on_error(
        self, mock_session_scope, repo, test_uuid
    ):
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("Ошибка БД"))
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(Exception, match="Ошибка БД"):
            await repo.create_dt(test_uuid, '{"key": "value"}', True)

    @patch("repositories.dt_repository.async_session_scope")
    async def test_update_dt_rollback_on_error(
        self, mock_session_scope, repo, test_uuid
    ):
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("Ошибка БД"))
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(Exception, match="Ошибка БД"):
            await repo.update_dt(test_uuid, content='{"new": "data"}')

    @patch("repositories.dt_repository.async_session_scope")
    async def test_delete_dt_rollback_on_error(
        self, mock_session_scope, repo, test_uuid
    ):
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("Ошибка БД"))
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(Exception, match="Ошибка БД"):
            await repo.delete_dt(test_uuid)
