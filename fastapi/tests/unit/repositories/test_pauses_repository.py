"""
Модульные тесты для PausesRepository.
"""

from datetime import datetime, timedelta, timezone
from typing import ClassVar
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from repositories.pauses_repository import PausesRepository

pytestmark = pytest.mark.asyncio


def _session_cm(session: AsyncMock):
    cm = AsyncMock()
    cm.__aenter__.return_value = session
    cm.__aexit__.return_value = None
    return cm


class _CommittingSessionScope:
    """Имитирует async_session_scope: при успешном выходе вызывает session.commit()."""

    def __init__(self, session: AsyncMock):
        self._session = session

    async def __aenter__(self) -> AsyncMock:
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            await self._session.commit()


class TestPausesRepository:
    """Тесты для PausesRepository."""

    @pytest.fixture(autouse=True)
    def _patch_get_db_timezone_utc(self, monkeypatch):
        """В `get_pauses` вызывается `get_db_timezone`; без БД подменяем на UTC."""

        async def utc():
            return timezone.utc

        monkeypatch.setattr(
            "repositories.pauses_repository.get_db_timezone", utc
        )

    @pytest.fixture
    def repo(self):
        return PausesRepository()

    @pytest.fixture
    def test_uuid(self):
        return uuid4()

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_check_alert_exists_true(
        self, mock_session_scope, repo, test_uuid
    ):
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = test_uuid
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.check_alert_exists(test_uuid) is True

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_check_alert_exists_false(
        self, mock_session_scope, repo, test_uuid
    ):
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.check_alert_exists(test_uuid) is False

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_get_pauses(self, mock_session_scope, repo, test_uuid):
        pause_id = uuid4()
        now = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        row = Mock()
        row._mapping = {
            "id": pause_id,
            "start_time": now,
            "end_time": None,
            "start_user": "user1",
            "end_user": None,
            "comment": "repo comment",
        }
        count_res = Mock()
        count_res.scalar_one.return_value = 1
        data_res = Mock()
        data_res.all.return_value = [row]
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_res, data_res])
        mock_session_scope.return_value = _session_cm(session)

        rows, total = await repo.get_pauses(test_uuid)

        assert total == 1
        assert len(rows) == 1
        assert rows[0]["start_time"] == now
        assert rows[0]["comment"] == "repo comment"
        assert session.execute.await_count == 2

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_get_pauses_converts_utc_to_moscow_db_tz(
        self, mock_session_scope, repo, test_uuid, monkeypatch
    ):
        async def moscow_tz():
            return timezone(timedelta(hours=3))

        monkeypatch.setattr(
            "repositories.pauses_repository.get_db_timezone", moscow_tz
        )

        pause_id = uuid4()
        utc_dt = datetime(2026, 2, 25, 12, 0, 0, tzinfo=timezone.utc)
        row = Mock()
        row._mapping = {
            "id": pause_id,
            "start_time": utc_dt,
            "end_time": None,
            "start_user": "user1",
            "end_user": None,
        }
        count_res = Mock()
        count_res.scalar_one.return_value = 1
        data_res = Mock()
        data_res.all.return_value = [row]
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_res, data_res])
        mock_session_scope.return_value = _session_cm(session)

        rows, total = await repo.get_pauses(test_uuid)

        assert total == 1
        assert rows[0]["start_time"].hour == 15
        assert rows[0]["start_time"].utcoffset() == timedelta(hours=3)

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_get_pauses_with_order(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        now = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        row = Mock()
        row._mapping = {
            "id": pause_id,
            "start_time": now,
            "end_time": None,
            "start_user": "u",
            "end_user": None,
        }
        count_res = Mock()
        count_res.scalar_one.return_value = 1
        data_res = Mock()
        data_res.all.return_value = [row]
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_res, data_res])
        mock_session_scope.return_value = _session_cm(session)

        rows, total = await repo.get_pauses(
            test_uuid,
            filter_type="all",
            order_by="end_time",
            order_dir="asc",
            limit=10,
            offset=0,
        )

        assert total == 1
        assert len(rows) == 1
        assert rows[0]["start_time"] == now

    @pytest.mark.parametrize("filter_type", ("active", "future", "past"))
    @patch("repositories.pauses_repository.async_session_scope")
    async def test_get_pauses_filters(
        self, mock_session_scope, filter_type, repo, test_uuid
    ):
        count_res = Mock()
        count_res.scalar_one.return_value = 0
        data_res = Mock()
        data_res.all.return_value = []
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_res, data_res])
        mock_session_scope.return_value = _session_cm(session)

        rows, total = await repo.get_pauses(test_uuid, filter_type=filter_type)

        assert total == 0
        assert rows == []

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_create_pause_use_now(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        lock_res = Mock()
        lock_res.scalar_one_or_none.return_value = test_uuid
        ins_res = Mock()
        ins_res.scalar_one.return_value = pause_id
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[lock_res, ins_res])
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.create_pause(
            test_uuid, "user1", use_now_for_start=True
        )

        assert result == pause_id
        assert session.execute.await_count == 2

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_create_pause_default_start_time(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        lock_res = Mock()
        lock_res.scalar_one_or_none.return_value = test_uuid
        ins_res = Mock()
        ins_res.scalar_one.return_value = pause_id
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[lock_res, ins_res])
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.create_pause(test_uuid, "user1")

        assert result == pause_id

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_create_pause_with_start_time(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        start_time = datetime.now(timezone.utc)
        lock_res = Mock()
        lock_res.scalar_one_or_none.return_value = test_uuid
        ins_res = Mock()
        ins_res.scalar_one.return_value = pause_id
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[lock_res, ins_res])
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.create_pause(
            test_uuid, "user1", start_time=start_time
        )

        assert result == pause_id

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_create_pause_with_end_time(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=1)
        lock_res = Mock()
        lock_res.scalar_one_or_none.return_value = test_uuid
        ins_res = Mock()
        ins_res.scalar_one.return_value = pause_id
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[lock_res, ins_res])
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.create_pause(
            test_uuid, "user1", start_time=start_time, end_time=end_time
        )

        assert result == pause_id

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_create_pause_with_comment(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        lock_res = Mock()
        lock_res.scalar_one_or_none.return_value = test_uuid
        ins_res = Mock()
        ins_res.scalar_one.return_value = pause_id
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[lock_res, ins_res])
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.create_pause(
            test_uuid, "user1", comment="pause note"
        )

        assert result == pause_id

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_create_pause_alert_not_found(
        self, mock_session_scope, repo, test_uuid
    ):
        lock_res = Mock()
        lock_res.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=lock_res)
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(ValueError, match="не найден"):
            await repo.create_pause(test_uuid, "user1")

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_create_pause_insert_error(
        self, mock_session_scope, repo, test_uuid
    ):
        lock_res = Mock()
        lock_res.scalar_one_or_none.return_value = test_uuid
        session = AsyncMock()
        session.execute = AsyncMock(
            side_effect=[lock_res, Exception("Ошибка БД")]
        )
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(Exception, match="Ошибка БД"):
            await repo.create_pause(test_uuid, "user1")

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_toggle_alert_pause_activate(
        self, mock_session_scope, repo, test_uuid
    ):
        alert_res = Mock()
        alert_res.scalar_one_or_none.return_value = test_uuid
        active_scalars = Mock()
        active_scalars.all.return_value = []
        active_res = Mock()
        active_res.scalars.return_value = active_scalars
        ins_res = Mock()
        session = AsyncMock()
        session.execute = AsyncMock(
            side_effect=[alert_res, active_res, ins_res]
        )
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.toggle_alert_pause(test_uuid, "user1") is True
        assert session.execute.await_count == 3

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_toggle_alert_pause_accepts_comment(
        self, mock_session_scope, repo, test_uuid
    ):
        alert_res = Mock()
        alert_res.scalar_one_or_none.return_value = test_uuid
        active_scalars = Mock()
        active_scalars.all.return_value = []
        active_res = Mock()
        active_res.scalars.return_value = active_scalars
        ins_res = Mock()
        session = AsyncMock()
        session.execute = AsyncMock(
            side_effect=[alert_res, active_res, ins_res]
        )
        mock_session_scope.return_value = _session_cm(session)

        assert (
            await repo.toggle_alert_pause(
                test_uuid, "user1", comment="toggle note"
            )
            is True
        )

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_toggle_alert_pause_deactivate(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_row_id = uuid4()
        alert_res = Mock()
        alert_res.scalar_one_or_none.return_value = test_uuid
        active_scalars = Mock()
        active_scalars.all.return_value = [pause_row_id]
        active_res = Mock()
        active_res.scalars.return_value = active_scalars
        upd_res = Mock()
        session = AsyncMock()
        session.execute = AsyncMock(
            side_effect=[alert_res, active_res, upd_res]
        )
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.toggle_alert_pause(test_uuid, "user1") is True

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_toggle_alert_pause_alert_not_found(
        self, mock_session_scope, repo, test_uuid
    ):
        alert_res = Mock()
        alert_res.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=alert_res)
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(ValueError, match="не найден"):
            await repo.toggle_alert_pause(test_uuid, "user1")

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_update_pause(self, mock_session_scope, repo, test_uuid):
        pause_id = uuid4()
        pause_obj = Mock()
        pause_obj.start_time = datetime.now(timezone.utc)
        pause_obj.end_time = None
        pause_obj.start_user = "user1"
        pause_obj.end_user = None
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = pause_obj
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        mock_session_scope.return_value = _session_cm(session)

        new_start = datetime.now(timezone.utc) + timedelta(minutes=5)
        assert await repo.update_pause(
            pause_id=pause_id,
            alert_id=test_uuid,
            start_time=new_start,
            login="user2",
        )
        assert pause_obj.start_time == new_start
        assert pause_obj.start_user == "user2"

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_update_pause_not_found(
        self, mock_session_scope, repo, test_uuid
    ):
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(ValueError, match="не найдена"):
            await repo.update_pause(
                pause_id=uuid4(), alert_id=test_uuid, login="user1"
            )

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_update_pause_end_time_set_to_none(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        pause_obj = Mock()
        pause_obj.start_time = datetime.now(timezone.utc)
        pause_obj.end_time = datetime.now(timezone.utc)
        pause_obj.start_user = "user1"
        pause_obj.end_user = "user2"
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = pause_obj
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.update_pause(
            pause_id=pause_id,
            alert_id=test_uuid,
            end_time_set_to_none=True,
        )
        assert pause_obj.end_time is None
        assert pause_obj.end_user is None

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_update_pause_with_end_time(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        pause_obj = Mock()
        pause_obj.start_time = datetime.now(timezone.utc)
        pause_obj.end_time = None
        pause_obj.start_user = "user1"
        pause_obj.end_user = None
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = pause_obj
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        mock_session_scope.return_value = _session_cm(session)

        end_time = datetime.now(timezone.utc) + timedelta(hours=1)
        assert await repo.update_pause(
            pause_id=pause_id,
            alert_id=test_uuid,
            end_time=end_time,
            login="user2",
        )
        assert pause_obj.end_time == end_time
        assert pause_obj.end_user == "user2"

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_update_pause_with_comment(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        pause_obj = Mock()
        pause_obj.comment = None
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = pause_obj
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.update_pause(
            pause_id=pause_id,
            alert_id=test_uuid,
            comment="updated comment",
        )
        assert pause_obj.comment == "updated comment"

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_update_pause_use_now_for_start_with_login(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        old_start = datetime.now(timezone.utc) - timedelta(hours=1)
        pause_obj = Mock()
        pause_obj.start_time = old_start
        pause_obj.end_time = None
        pause_obj.start_user = "user1"
        pause_obj.end_user = None
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = pause_obj
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.update_pause(
            pause_id=pause_id,
            alert_id=test_uuid,
            use_now_for_start=True,
            login="user2",
        )
        assert pause_obj.start_user == "user2"
        assert pause_obj.start_time != old_start

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_update_pause_without_login(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        pause_obj = Mock()
        pause_obj.start_time = datetime.now(timezone.utc)
        pause_obj.end_time = None
        pause_obj.start_user = "user1"
        pause_obj.end_user = None
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = pause_obj
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        mock_session_scope.return_value = _session_cm(session)

        new_start = datetime.now(timezone.utc) + timedelta(minutes=1)
        assert await repo.update_pause(
            pause_id=pause_id,
            alert_id=test_uuid,
            start_time=new_start,
        )
        assert pause_obj.start_time == new_start
        assert pause_obj.start_user == "user1"

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_update_pause_no_field_changes(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        pause_obj = Mock()
        pause_obj.start_time = datetime.now(timezone.utc)
        pause_obj.end_time = None
        pause_obj.start_user = "user1"
        pause_obj.end_user = None
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = pause_obj
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        mock_session_scope.return_value = _session_cm(session)

        assert (
            await repo.update_pause(pause_id=pause_id, alert_id=test_uuid)
            is True
        )
        session.execute.assert_awaited_once()

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_update_pause_end_time_none_explicit(
        self, mock_session_scope, repo, test_uuid
    ):
        """end_time=None без флага end_time_set_to_none не сбрасывает поле в БД-логике репозитория."""
        pause_id = uuid4()
        pause_obj = Mock()
        pause_obj.start_time = datetime.now(timezone.utc)
        pause_obj.end_time = None
        pause_obj.start_user = "user1"
        pause_obj.end_user = None
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = pause_obj
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.update_pause(
            pause_id=pause_id,
            alert_id=test_uuid,
            login="user1",
            start_time=datetime.now(timezone.utc),
            end_time=None,
        )

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_update_pause_commit_error(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        pause_obj = Mock()
        pause_obj.start_time = datetime.now(timezone.utc)
        pause_obj.end_time = None
        pause_obj.start_user = "u"
        pause_obj.end_user = None
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = pause_obj
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        session.commit = AsyncMock(side_effect=Exception("Ошибка БД"))
        mock_session_scope.return_value = _CommittingSessionScope(session)

        with pytest.raises(Exception, match="Ошибка БД"):
            await repo.update_pause(
                pause_id=pause_id,
                alert_id=test_uuid,
                login="user1",
                start_time=datetime.now(timezone.utc),
            )

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_stop_specific_pause_active(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        pause_obj = Mock()
        pause_obj.start_time = start_time
        pause_obj.end_time = None
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = pause_obj
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        mock_session_scope.return_value = _session_cm(session)

        assert (
            await repo.stop_specific_pause(pause_id, test_uuid, "user2")
            is True
        )
        assert pause_obj.end_user == "user2"
        assert pause_obj.end_time is not None

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_stop_specific_pause_updates_comment(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        pause_obj = Mock()
        pause_obj.start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        pause_obj.end_time = None
        pause_obj.comment = None
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = pause_obj
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.stop_specific_pause(
            pause_id, test_uuid, "user2", comment="stop note"
        )
        assert pause_obj.comment == "stop note"

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_stop_specific_pause_future(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        pause_obj = Mock()
        pause_obj.start_time = start_time
        pause_obj.end_time = None
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = pause_obj
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        mock_session_scope.return_value = _session_cm(session)

        assert (
            await repo.stop_specific_pause(pause_id, test_uuid, "user2")
            is True
        )
        assert pause_obj.end_time == start_time

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_stop_specific_pause_past(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        start_time = datetime.now(timezone.utc) - timedelta(hours=2)
        end_time = datetime.now(timezone.utc) - timedelta(hours=1)
        pause_obj = Mock()
        pause_obj.start_time = start_time
        pause_obj.end_time = end_time
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = pause_obj
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(ValueError, match="уже завершена"):
            await repo.stop_specific_pause(pause_id, test_uuid, "user2")

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_stop_specific_pause_not_found(
        self, mock_session_scope, repo, test_uuid
    ):
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(ValueError, match="не найдена"):
            await repo.stop_specific_pause(uuid4(), test_uuid, "user1")

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_stop_specific_pause_naive_datetimes(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        start_time = datetime.now(timezone.utc).replace(tzinfo=None)
        pause_obj = Mock()
        pause_obj.start_time = start_time
        pause_obj.end_time = None
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = pause_obj
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        mock_session_scope.return_value = _session_cm(session)

        assert (
            await repo.stop_specific_pause(pause_id, test_uuid, "user2")
            is True
        )

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_stop_specific_pause_naive_end_time_branch(
        self, mock_session_scope, repo, test_uuid
    ):
        """Покрыть ветку end_time.replace(tzinfo=UTC)."""
        pause_id = uuid4()
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        end_time = datetime.now().replace(tzinfo=None) + timedelta(hours=1)
        pause_obj = Mock()
        pause_obj.start_time = start_time
        pause_obj.end_time = end_time
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = pause_obj
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.stop_specific_pause(pause_id, test_uuid, "user2") is True

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_stop_specific_pause_commit_error(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        pause_obj = Mock()
        pause_obj.start_time = start_time
        pause_obj.end_time = None
        load_res = Mock()
        load_res.scalar_one_or_none.return_value = pause_obj
        session = AsyncMock()
        session.execute = AsyncMock(return_value=load_res)
        session.commit = AsyncMock(side_effect=Exception("Ошибка БД"))
        mock_session_scope.return_value = _CommittingSessionScope(session)

        with pytest.raises(Exception, match="Ошибка БД"):
            await repo.stop_specific_pause(pause_id, test_uuid, "user1")

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_stop_all_active_pauses(
        self, mock_session_scope, repo, test_uuid
    ):
        execute_result = Mock()
        execute_result.rowcount = 2
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.stop_all_active_pauses(test_uuid, "user1") == 2

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_stop_all_active_pauses_with_comment(
        self, mock_session_scope, repo, test_uuid
    ):
        execute_result = Mock()
        execute_result.rowcount = 1
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        mock_session_scope.return_value = _session_cm(session)

        assert (
            await repo.stop_all_active_pauses(
                test_uuid, "user1", comment="bulk close"
            )
            == 1
        )

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_stop_all_active_pauses_none(
        self, mock_session_scope, repo, test_uuid
    ):
        execute_result = Mock()
        execute_result.rowcount = 0
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.stop_all_active_pauses(test_uuid, "user1") == 0

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_get_pause_by_id(self, mock_session_scope, repo, test_uuid):
        pause_id = uuid4()
        start_time = datetime.now(timezone.utc)

        class PauseRow:
            _values = (pause_id, start_time, None, "user1", None)
            _mapping: ClassVar[dict[str, object]] = {
                "id": pause_id,
                "start_time": start_time,
                "end_time": None,
                "start_user": "user1",
                "end_user": None,
            }

            def __getitem__(self, idx):
                return self._values[idx]

        execute_result = Mock()
        execute_result.one_or_none.return_value = PauseRow()
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.get_pause_by_id(pause_id, test_uuid)

        assert result is not None
        assert result[0] == pause_id

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_get_pause_by_id_not_found(
        self, mock_session_scope, repo, test_uuid
    ):
        pause_id = uuid4()
        execute_result = Mock()
        execute_result.one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.get_pause_by_id(pause_id, test_uuid) is None

    @patch("repositories.pauses_repository.async_session_scope")
    async def test_delete_pause(self, mock_session_scope, repo, test_uuid):
        pause_id = uuid4()
        session = AsyncMock()
        session.execute = AsyncMock()
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.delete_pause(pause_id, test_uuid) is True
        session.execute.assert_awaited_once()

    async def test_check_alert_exists_with_explicit_session(
        self, repo, test_uuid
    ):
        """Покрыть _run_with_session с переданной сессией."""
        execute_result = Mock()
        execute_result.scalar_one_or_none.return_value = test_uuid
        session = AsyncMock()
        session.execute = AsyncMock(return_value=execute_result)
        assert await repo.check_alert_exists(test_uuid, session) is True

    async def test_pause_row_to_db_tz_with_naive_end_time(self, repo):
        """Покрыть ветку нормализации naive end_time."""
        row = Mock()
        row._mapping = {
            "id": uuid4(),
            "start_time": datetime.now(timezone.utc),
            "end_time": datetime.now().replace(tzinfo=None),
            "start_user": "u1",
            "end_user": "u2",
        }
        converted = repo._pause_row_to_db_tz(
            row, timezone(timedelta(hours=3))
        )
        assert converted["end_time"].tzinfo is not None

    async def test_pause_row_to_db_tz_with_naive_start_time(self, repo):
        """Покрыть ветку нормализации naive start_time."""
        row = Mock()
        row._mapping = {
            "id": uuid4(),
            "start_time": datetime.now().replace(tzinfo=None),
            "end_time": None,
            "start_user": "u1",
            "end_user": None,
        }
        converted = repo._pause_row_to_db_tz(
            row, timezone(timedelta(hours=3))
        )
        assert converted["start_time"].tzinfo is not None
