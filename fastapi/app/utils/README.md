# Утилиты

- **logging.py** - настройка логгера по `LEVEL_LOG`, `correlation_id` через `ContextVar`, объект `log`.
- **Примечание:** обработчики исключений вынесены на уровень `app/exception_handlers.py` (по аналогии с `cron`).

Тесты: `tests/unit/test_utils.py`, `tests/unit/test_exception_handlers.py`.
