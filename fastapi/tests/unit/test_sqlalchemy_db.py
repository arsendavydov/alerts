"""Точечные проверки модуля `sqlalchemy_db` (без подключения к БД)."""

from contextlib import asynccontextmanager
from datetime import timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


def test_module_docstring_describes_transaction_scope():
    """Документация модуля описывает область транзакции и передачу сессии в репозитории."""
    import sqlalchemy_db as m

    assert m.__doc__ is not None
    assert "async_session_scope" in m.__doc__
    assert "транзак" in m.__doc__.lower()


@pytest.fixture(autouse=True)
def _reset_sqlalchemy_db_timezone_cache():
    import sqlalchemy_db as m

    prev = m._db_timezone_cache
    m._db_timezone_cache = None
    yield
    m._db_timezone_cache = prev


@pytest.mark.asyncio
async def test_get_db_timezone_uses_session_and_caches(monkeypatch):
    import sqlalchemy_db as m

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = "UTC"
    mock_session.execute = AsyncMock(return_value=mock_result)

    @asynccontextmanager
    async def fake_scope():
        yield mock_session

    monkeypatch.setattr(m, "async_session_scope", fake_scope)

    tz1 = await m.get_db_timezone()
    assert tz1 is timezone.utc
    mock_session.execute.assert_called_once()

    tz2 = await m.get_db_timezone()
    assert tz2 is tz1
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_db_timezone_europe_moscow(monkeypatch):
    import sqlalchemy_db as m

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = "Europe/Moscow"
    mock_session.execute = AsyncMock(return_value=mock_result)

    @asynccontextmanager
    async def fake_scope():
        yield mock_session

    monkeypatch.setattr(m, "async_session_scope", fake_scope)

    tz = await m.get_db_timezone()
    assert tz == timezone(timedelta(hours=3))


@pytest.mark.asyncio
async def test_get_db_timezone_unknown_falls_back_to_utc(monkeypatch):
    import sqlalchemy_db as m

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = "Mars/Phobos"
    mock_session.execute = AsyncMock(return_value=mock_result)

    @asynccontextmanager
    async def fake_scope():
        yield mock_session

    monkeypatch.setattr(m, "async_session_scope", fake_scope)

    tz = await m.get_db_timezone()
    assert tz is timezone.utc


def test_require_env_raises_for_empty_value(monkeypatch):
    """Пустая env-переменная приводит к RuntimeError."""
    import sqlalchemy_db as m

    monkeypatch.setenv("db_host", "")
    with pytest.raises(RuntimeError, match="db_host"):
        m._require_env("db_host")


@pytest.mark.asyncio
async def test_async_session_scope_commits_and_closes(monkeypatch):
    """Контекст сессии делает commit и close при успехе."""
    import sqlalchemy_db as m

    session = AsyncMock()
    monkeypatch.setattr(m, "AsyncSessionLocal", lambda: session)

    async with m.async_session_scope() as s:
        assert s is session

    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()
    session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_session_scope_rollbacks_on_error(monkeypatch):
    """Контекст сессии делает rollback и close при ошибке."""
    import sqlalchemy_db as m

    session = AsyncMock()
    monkeypatch.setattr(m, "AsyncSessionLocal", lambda: session)

    with pytest.raises(ValueError, match="boom"):
        async with m.async_session_scope():
            raise ValueError("boom")

    session.commit.assert_not_awaited()
    session.rollback.assert_awaited_once()
    session.close.assert_awaited_once()
