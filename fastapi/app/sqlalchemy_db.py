"""
Инфраструктура SQLAlchemy Async для поэтапной миграции с raw SQL.

Unit of Work: `async_session_scope` открывает одну `AsyncSession` и фиксирует
транзакцию (commit при успешном выходе, rollback при исключении). Сервисы
для многошаговых сценариев оборачивают операции в один `async with
async_session_scope()` и передают ту же сессию в методы репозиториев
(параметр `session`), чтобы все шаги выполнились в одной транзакции.
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from utils import log

# Кеш таймзоны БД после первого SHOW TIMEZONE (datetime.timezone)
_db_timezone_cache: Any = None


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _build_db_url() -> str:
    host = _require_env("db_host")
    db_name = _require_env("db")
    user = _require_env("db_login")
    password = _require_env("db_password")
    return f"postgresql+psycopg2://{user}:{password}@{host}/{db_name}"


ASYNC_ENGINE = create_async_engine(
    _build_db_url().replace("postgresql+psycopg2://", "postgresql+asyncpg://"),
    future=True,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=ASYNC_ENGINE,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@asynccontextmanager
async def async_session_scope() -> AsyncIterator[AsyncSession]:
    """Контекст сессии с commit/rollback для бизнес-операции."""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db_timezone():
    """
    Таймзона, настроенная в PostgreSQL (SHOW TIMEZONE),
    через SQLAlchemy-сессию.
    Результат кешируется в модуле.
    """
    global _db_timezone_cache

    if _db_timezone_cache is not None:
        return _db_timezone_cache

    async with async_session_scope() as session:
        tz_name = (await session.execute(text("SHOW TIMEZONE"))).scalar_one()

    tz_name_str = str(tz_name)

    if tz_name_str.upper() in {"UTC", "ETC/UTC", "GMT"}:
        _db_timezone_cache = timezone.utc
    elif tz_name_str == "Europe/Moscow":
        _db_timezone_cache = timezone(timedelta(hours=3))
    else:
        log.warning(
            f"Unknown DB timezone '{tz_name_str}', falling back to UTC"
        )
        _db_timezone_cache = timezone.utc

    return _db_timezone_cache
