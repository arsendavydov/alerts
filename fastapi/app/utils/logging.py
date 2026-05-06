"""Утилиты для логирования."""

import logging
import os
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path

from schemas.level_log import LevelLog

_correlation_id_ctx_var: ContextVar[str] = ContextVar(
    "correlation_id", default="-"
)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _int_env(name: str, default: int) -> int:
    """Безопасно читает integer-переменную окружения."""
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def _resolve_log_file_path() -> Path:
    """Возвращает абсолютный путь к файлу логов."""
    configured_path = os.getenv("LOG_FILE_PATH", "logs/alerts.log")
    path_obj = Path(configured_path)
    if path_obj.is_absolute():
        return path_obj
    return _PROJECT_ROOT / path_obj


LOG_FILE_PATH = _resolve_log_file_path()
LOG_FILE_MAX_BYTES = _int_env("LOG_FILE_MAX_BYTES", 10 * 1024 * 1024)
LOG_FILE_BACKUP_COUNT = _int_env("LOG_FILE_BACKUP_COUNT", 5)


class CorrelationIdFilter(logging.Filter):
    """Добавляет correlation_id в записи лога."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = _correlation_id_ctx_var.get()
        return True


def set_correlation_id(correlation_id: str) -> None:
    """Устанавливает correlation-id в контекст текущего запроса."""
    _correlation_id_ctx_var.set(correlation_id)


def get_correlation_id() -> str:
    """Возвращает correlation-id из контекста текущего запроса."""
    return _correlation_id_ctx_var.get()


def setup_logging():
    """
    Настройка логирования на основе переменной окружения LEVEL_LOG.
    """
    try:
        level_name = os.getenv("LEVEL_LOG", "notset").lower()
        level = LevelLog[level_name].value
    except Exception:
        level = LevelLog.notset.value
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(correlation_id)s - %(message)s"
    formatter = logging.Formatter(log_format)
    correlation_filter = CorrelationIdFilter()
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(correlation_filter)
    root_logger.addHandler(stream_handler)

    log_dir = LOG_FILE_PATH.parent
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=LOG_FILE_PATH,
        maxBytes=LOG_FILE_MAX_BYTES,
        backupCount=LOG_FILE_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(correlation_filter)
    root_logger.addHandler(file_handler)


setup_logging()
log = logging.getLogger("alerts")
