"""Общая конфигурация модульных тестов alerts FastAPI."""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from dotenv import load_dotenv

# Корень сервиса (каталог `fastapi/`) и `app/` - как в cron: один явный sys.path
_FASTAPI_ROOT = Path(__file__).resolve().parents[2]
_APP_DIR = _FASTAPI_ROOT / "app"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

# `.env` лежит на уровень выше `fastapi/` (корень `alerts/`)
_env_file = _FASTAPI_ROOT.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file)

os.environ.setdefault("LEVEL_LOG", "ERROR")
os.environ.setdefault("db_host", "localhost")
os.environ.setdefault("db", "test_db")
os.environ.setdefault("db_login", "test_user")
os.environ.setdefault("db_password", "test_password")

_psycopg2_patcher = None
_register_uuid_patcher = None
_asyncpg_patcher = None


def pytest_configure(config):
    """Мокирует БД до импорта тестовых модулей (psycopg2, asyncpg)."""
    global _psycopg2_patcher, _register_uuid_patcher, _asyncpg_patcher

    mock_conn = MagicMock()
    mock_conn.autocommit = False
    mock_conn.rollback = MagicMock()
    mock_conn.commit = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    _psycopg2_patcher = patch("psycopg2.connect", return_value=mock_conn)
    _register_uuid_patcher = patch(
        "psycopg2.extras.register_uuid", MagicMock()
    )
    _psycopg2_patcher.start()
    _register_uuid_patcher.start()

    mock_pool_async = AsyncMock()
    mock_conn_async = AsyncMock()
    mock_conn_async.__aenter__ = AsyncMock(return_value=mock_conn_async)
    mock_conn_async.__aexit__ = AsyncMock(return_value=None)
    mock_transaction = AsyncMock()
    mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
    mock_transaction.__aexit__ = AsyncMock(return_value=None)
    mock_conn_async.transaction = Mock(return_value=mock_transaction)
    mock_pool_async.acquire = Mock(return_value=mock_conn_async)

    async def mock_create_pool(*args, **kwargs):
        return mock_pool_async

    _asyncpg_patcher = patch("asyncpg.create_pool", new=mock_create_pool)
    _asyncpg_patcher.start()


def pytest_unconfigure(config):
    """Снимает глобальные патчи."""
    if _psycopg2_patcher:
        _psycopg2_patcher.stop()
    if _register_uuid_patcher:
        _register_uuid_patcher.stop()
    if _asyncpg_patcher:
        _asyncpg_patcher.stop()
