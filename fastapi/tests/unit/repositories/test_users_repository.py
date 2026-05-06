"""
Модульные тесты для UsersRepository.
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy import Column, MetaData, String, Table, create_engine

from repositories.users_repository import UsersRepository

pytestmark = pytest.mark.asyncio


def _session_cm(session: AsyncMock):
    cm = AsyncMock()
    cm.__aenter__.return_value = session
    cm.__aexit__.return_value = None
    return cm


class TestUsersRepository:
    """Тесты для UsersRepository."""

    @pytest.fixture(autouse=True)
    def _mock_reflection_for_unit(self, request, monkeypatch):
        """Для unit-тестов мокируем reflection, кроме тестов самого _get_reflected_table."""
        if request.node.name.startswith("test_get_reflected_table"):
            return

        metadata = MetaData()
        tables = {
            ("alerts", "contacts"): Table(
                "contacts",
                metadata,
                Column("id", String),
                Column("user_name", String),
                Column("email", String),
                Column("group", String),
                Column("telegram", String),
                schema="alerts",
            ),
            ("telegram_bot", "spr_users"): Table(
                "spr_users",
                metadata,
                Column("login_name", String),
                Column("telegram_user_id", String),
                schema="telegram_bot",
            ),
        }

        async def fake_get_reflected_table(_self, _session, schema, table_name):
            return tables.get((schema, table_name))

        monkeypatch.setattr(
            UsersRepository,
            "_get_reflected_table",
            fake_get_reflected_table,
        )

    @pytest.fixture
    def repo(self):
        return UsersRepository()

    @pytest.fixture
    def test_uuid(self):
        return uuid4()

    @patch("repositories.users_repository.async_session_scope")
    async def test_get_telegram_by_login(self, mock_session_scope, repo):
        row = {"login_name": "test_login", "telegram_user_id": "12345"}
        res = Mock()
        res.mappings.return_value.first.return_value = row
        session = AsyncMock()
        session.execute = AsyncMock(return_value=res)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.get_telegram_by_login("test_login")

        assert result == row
        session.execute.assert_awaited_once()

    @patch("repositories.users_repository.async_session_scope")
    async def test_get_telegram_by_login_not_found(
        self, mock_session_scope, repo
    ):
        res = Mock()
        res.mappings.return_value.first.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=res)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.get_telegram_by_login("nonexistent") is None

    @patch("repositories.users_repository.async_session_scope")
    async def test_get_telegram_by_login_execute_error(
        self, mock_session_scope, repo
    ):
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("DB error"))
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(Exception, match="DB error"):
            await repo.get_telegram_by_login("nonexistent")

    @patch("repositories.users_repository.async_session_scope")
    async def test_check_user_exists_true(
        self, mock_session_scope, repo, test_uuid
    ):
        r = Mock()
        r.scalar_one_or_none.return_value = test_uuid
        session = AsyncMock()
        session.execute = AsyncMock(return_value=r)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.check_user_exists(test_uuid) is True

    @patch("repositories.users_repository.async_session_scope")
    async def test_check_user_exists_false(
        self, mock_session_scope, repo, test_uuid
    ):
        r = Mock()
        r.scalar_one_or_none.return_value = None
        session = AsyncMock()
        session.execute = AsyncMock(return_value=r)
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.check_user_exists(test_uuid) is False

    @patch("repositories.users_repository.async_session_scope")
    async def test_get_available_columns(self, mock_session_scope, repo):
        maps = Mock()
        maps.all.return_value = [
            {"column_name": "user_name"},
            {"column_name": "email"},
            {"column_name": "telegram"},
        ]
        res = Mock()
        res.mappings.return_value = maps
        session = AsyncMock()
        session.execute = AsyncMock(return_value=res)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.get_available_columns()

        assert "user_name" in result
        assert "email" in result
        assert "telegram" in result

    @patch("repositories.users_repository.async_session_scope")
    async def test_get_available_columns_empty(self, mock_session_scope, repo):
        maps = Mock()
        maps.all.return_value = []
        res = Mock()
        res.mappings.return_value = maps
        session = AsyncMock()
        session.execute = AsyncMock(return_value=res)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.get_available_columns()
        assert isinstance(result, list)
        assert "id" not in result

    @patch("repositories.users_repository.async_session_scope")
    async def test_get_available_columns_table_missing_raises(
        self, mock_session_scope, repo
    ):
        session = AsyncMock()
        mock_session_scope.return_value = _session_cm(session)
        with patch.object(
            repo, "_get_reflected_table", new=AsyncMock(return_value=None)
        ):
            with pytest.raises(RuntimeError, match=r"alerts\.contacts"):
                await repo.get_available_columns()

    @patch("repositories.users_repository.async_session_scope")
    async def test_create_user(self, mock_session_scope, repo, test_uuid):
        ins = Mock()
        ins.scalar_one.return_value = test_uuid
        session = AsyncMock()
        session.execute = AsyncMock(return_value=ins)
        mock_session_scope.return_value = _session_cm(session)

        result = await repo.create_user(
            ["user_name", "email"], ["test_user", "test@test.com"]
        )

        assert result == test_uuid
        session.execute.assert_awaited_once()

    async def test_create_user_len_mismatch_raises(self, repo):
        with pytest.raises(ValueError, match="совпадать по длине"):
            await repo.create_user(["user_name"], ["u", "extra"])

    @patch("repositories.users_repository.async_session_scope")
    async def test_create_user_table_missing_raises(
        self, mock_session_scope, repo
    ):
        session = AsyncMock()
        mock_session_scope.return_value = _session_cm(session)
        with patch.object(
            repo, "_get_reflected_table", new=AsyncMock(return_value=None)
        ):
            with pytest.raises(RuntimeError, match=r"alerts\.contacts"):
                await repo.create_user(["user_name"], ["u"])

    @patch("repositories.users_repository.async_session_scope")
    async def test_update_user(self, mock_session_scope, repo, test_uuid):
        session = AsyncMock()
        session.execute = AsyncMock()
        mock_session_scope.return_value = _session_cm(session)

        assert (
            await repo.update_user(test_uuid, ["user_name"], ["updated_user"])
            is True
        )
        session.execute.assert_awaited_once()

    async def test_update_user_len_mismatch_raises(self, repo, test_uuid):
        with pytest.raises(ValueError, match="совпадать по длине"):
            await repo.update_user(test_uuid, ["user_name"], ["a", "b"])

    @patch("repositories.users_repository.async_session_scope")
    async def test_update_user_table_missing_raises(
        self, mock_session_scope, repo, test_uuid
    ):
        session = AsyncMock()
        mock_session_scope.return_value = _session_cm(session)
        with patch.object(
            repo, "_get_reflected_table", new=AsyncMock(return_value=None)
        ):
            with pytest.raises(RuntimeError, match=r"alerts\.contacts"):
                await repo.update_user(test_uuid, ["user_name"], ["u"])

    async def test_update_user_no_fields(self, repo, test_uuid):
        with patch(
            "repositories.users_repository.async_session_scope"
        ) as mock_scope:
            assert await repo.update_user(test_uuid, [], []) is True
            mock_scope.assert_not_called()

    @patch("repositories.users_repository.async_session_scope")
    async def test_delete_user(self, mock_session_scope, repo, test_uuid):
        session = AsyncMock()
        session.execute = AsyncMock()
        mock_session_scope.return_value = _session_cm(session)

        assert await repo.delete_user(test_uuid) is True
        assert session.execute.await_count == 3

    @patch("repositories.users_repository.async_session_scope")
    async def test_create_user_error(
        self, mock_session_scope, repo, test_uuid
    ):
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("DB error"))
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(Exception, match="DB error"):
            await repo.create_user(["user_name"], ["test_user"])

    @patch("repositories.users_repository.async_session_scope")
    async def test_update_user_error(
        self, mock_session_scope, repo, test_uuid
    ):
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("DB error"))
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(Exception, match="DB error"):
            await repo.update_user(test_uuid, ["user_name"], ["updated"])

    @patch("repositories.users_repository.async_session_scope")
    async def test_delete_user_error(
        self, mock_session_scope, repo, test_uuid
    ):
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("DB error"))
        mock_session_scope.return_value = _session_cm(session)

        with pytest.raises(Exception, match="DB error"):
            await repo.delete_user(test_uuid)

    @patch("repositories.users_repository.async_session_scope")
    async def test_create_user_multiple_fields(
        self, mock_session_scope, repo, test_uuid
    ):
        ins = Mock()
        ins.scalar_one.return_value = test_uuid
        session = AsyncMock()
        session.execute = AsyncMock(return_value=ins)
        mock_session_scope.return_value = _session_cm(session)

        fields = ["user_name", "email", "telegram", "group"]
        values = ["test_user", "test@test.com", "12345", True]
        result = await repo.create_user(fields, values)

        assert result == test_uuid
        session.execute.assert_awaited_once()

    @patch("repositories.users_repository.async_session_scope")
    async def test_update_user_multiple_fields(
        self, mock_session_scope, repo, test_uuid
    ):
        session = AsyncMock()
        session.execute = AsyncMock()
        mock_session_scope.return_value = _session_cm(session)

        fields = ["user_name", "email"]
        values = ["updated_user", "updated@test.com"]
        assert await repo.update_user(test_uuid, fields, values) is True
        session.execute.assert_awaited_once()

    @patch("repositories.users_repository.async_session_scope")
    async def test_search_users_no_filters(self, mock_session_scope, repo):
        count_res = Mock()
        count_res.scalar_one.return_value = 1
        data_res = Mock()
        data_res.mappings.return_value.all.return_value = [
            {"id": uuid4(), "user_name": "u"}
        ]
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_res, data_res])
        mock_session_scope.return_value = _session_cm(session)

        rows, total = await repo.search_users()
        assert total == 1
        assert len(rows) == 1
        assert session.execute.await_count == 2

    @patch("repositories.users_repository.async_session_scope")
    async def test_search_users_with_query_and_groups(
        self, mock_session_scope, repo
    ):
        count_res = Mock()
        count_res.scalar_one.return_value = 0
        data_res = Mock()
        data_res.mappings.return_value.all.return_value = []
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[count_res, data_res])
        mock_session_scope.return_value = _session_cm(session)

        rows, total = await repo.search_users(
            query="ab", groups=True, order_by="email", order_dir="desc"
        )
        assert total == 0
        assert rows == []

    @patch("repositories.users_repository.async_session_scope")
    async def test_search_users_table_missing_raises(
        self, mock_session_scope, repo
    ):
        session = AsyncMock()
        mock_session_scope.return_value = _session_cm(session)
        with patch.object(
            repo, "_get_reflected_table", new=AsyncMock(return_value=None)
        ):
            with pytest.raises(RuntimeError, match=r"alerts\.contacts"):
                await repo.search_users()

    async def test_get_reflected_table_cache_hit(self, repo):
        """Покрыть возврат из _TABLE_CACHE."""
        key = ("alerts", "contacts")
        table = Table(
            "contacts", MetaData(), Column("id", String), schema="alerts"
        )
        repo._TABLE_CACHE[key] = table
        session = AsyncMock()
        result = await repo._get_reflected_table(session, *key)
        assert result is table

    async def test_get_reflected_table_run_sync_none_raises(self, repo):
        """В strict режиме run_sync обязателен."""
        repo._TABLE_CACHE.clear()
        session = AsyncMock()
        session.run_sync = None
        with pytest.raises(
            RuntimeError, match=r"session\.run_sync is required"
        ):
            await repo._get_reflected_table(session, "alerts", "contacts")

    async def test_get_reflected_table_run_sync_non_table_raises(
        self, repo
    ):
        """В strict режиме non-Table недопустим."""
        repo._TABLE_CACHE.clear()
        session = AsyncMock()
        session.run_sync = AsyncMock(return_value=object())
        with pytest.raises(
            RuntimeError, match="SQLAlchemy reflection failed"
        ):
            await repo._get_reflected_table(session, "alerts", "contacts")

    async def test_get_reflected_table_run_sync_none_raises_object_session(
        self, repo
    ):
        repo._TABLE_CACHE.clear()

        class SessionNoRunSync:
            pass

        with pytest.raises(
            RuntimeError, match=r"session\.run_sync is required"
        ):
            await repo._get_reflected_table(
                SessionNoRunSync(), "alerts", "contacts"
            )

    async def test_get_reflected_table_run_sync_returns_table_caches(
        self, repo
    ):
        repo._TABLE_CACHE.clear()
        reflected_table = Table(
            "contacts",
            MetaData(),
            Column("id", String),
            schema="alerts",
        )

        session = AsyncMock()
        session.run_sync = AsyncMock(return_value=reflected_table)
        result = await repo._get_reflected_table(session, "alerts", "contacts")
        assert result is not None

    async def test_get_reflected_table_executes_reflect_callback_lines(
        self, repo
    ):
        """Покрыть строки callback _reflect (bind/metadata/Table)."""
        repo._TABLE_CACHE.clear()
        engine = create_engine("sqlite+pysqlite:///:memory:")

        class SyncSession:
            def get_bind(self):
                return engine

        async def run_sync(fn):
            return fn(SyncSession())

        session = AsyncMock()
        session.run_sync = run_sync
        with pytest.raises(Exception):
            await repo._get_reflected_table(session, "alerts", "contacts")
