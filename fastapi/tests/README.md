# Тесты

Запуск из корня `alerts`:

```bash
python3.10 -m pytest fastapi/tests/unit/ -v
python3.10 -m pytest fastapi/tests/integration/ -v
python3.10 -m pytest fastapi/tests/e2e/ -v -s
```

## Структура

| Папка          | Назначение |
|----------------|------------|
| `unit/`        | Модульные тесты с моками (БД не нужна) |
| `integration/` | Запросы к запущенному API (нужен сервис и БД) |
| `e2e/`         | Полные сценарии по API (нужен сервис и БД) |

## Переменные окружения

- **Unit:** не требуются (всё мокается).
- **Integration / E2E:** опционально `TEST_API_URL` (по умолчанию `http://localhost:8888/alerts`).

