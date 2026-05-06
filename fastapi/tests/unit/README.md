# Модульные тесты (Unit)

Изолированные тесты с моками. БД и запущенный сервис не нужны.

## Запуск (из корня alerts)

```bash
python3.10 -m pytest fastapi/tests/unit/ -v
python3.10 -m pytest fastapi/tests/unit/repositories/ -v
python3.10 -m pytest fastapi/tests/unit/services/ -v
python3.10 -m pytest fastapi/tests/unit/routers/ -v
python3.10 -m pytest fastapi/tests/unit/ --cov=fastapi/app --cov-report=html
```

## Структура

- `repositories/` - тесты репозиториев (моки `AsyncSession`/ORM и edge-сценариев совместимости)
- `services/` - тесты сервисов (моки репозиториев)
- `routers/` - тесты роутеров (AsyncClient, моки сервисов)
- `schemas/` - валидация Pydantic
- `test_utils.py`, `test_validators.py`, `test_exception_handlers.py` - утилиты и обработчики

Тесты асинхронные (`async def`, `@pytest.mark.asyncio`).
