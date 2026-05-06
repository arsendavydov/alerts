"""
Общие фикстуры для всех тестов.
"""

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла (если существует)
# .env файл всегда находится на уровень выше папки fastapi
fastapi_dir = Path(__file__).parent.parent
env_file = fastapi_dir.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Добавляем app в sys.path для импортов (работает на Windows и Mac)
# Это нужно, чтобы импорты from routers, from repositories и т.д. работали
app_dir = fastapi_dir / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

# Устанавливаем переменные окружения для импорта модулей
# Для модульных тестов БД мокируется, но переменные нужны для:
# - LEVEL_LOG: используется при импорте utils.logging для настройки логирования
# - db_*: устанавливаются для совместимости, но не используются (БД мокируется)
# Значения из .env имеют приоритет над дефолтными
os.environ.setdefault("LEVEL_LOG", "ERROR")
os.environ.setdefault("db_host", "localhost")
os.environ.setdefault("db", "test_db")
os.environ.setdefault("db_login", "test_user")
os.environ.setdefault("db_password", "test_password")


@pytest.fixture(scope="session")
def test_base_url():
    """Базовый URL для тестов API."""
    return os.getenv("TEST_API_URL", "http://localhost:8888/alerts")


@pytest.fixture(scope="session")
def test_db_config():
    """
    Конфигурация тестовой БД.
    В текущих интеграционных и E2E тестах не используется - они работают через HTTP API.
    Оставлена на случай будущих тестов, которые могут напрямую подключаться к БД.
    """
    return {
        "host": os.getenv("TEST_DB_HOST", "localhost"),
        "port": int(os.getenv("TEST_DB_PORT", "5432")),
        "database": os.getenv("TEST_DB_NAME", "alerts_test"),
        "user": os.getenv("TEST_DB_USER", "test_user"),
        "password": os.getenv("TEST_DB_PASSWORD", "test_password"),
    }
