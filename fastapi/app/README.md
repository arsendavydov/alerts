# Alerts Service - приложение

FastAPI-приложение для управления алертами.

## Структура

```
app/
├── routers/       # HTTP endpoints
├── services/      # Бизнес-логика
├── contracts/     # Protocol-контракты
├── repositories/  # Работа с БД (SQLAlchemy/ORM)
├── models/        # SQLAlchemy ORM-модели
├── middlewares/   # Request context (correlation-id + latency)
├── schemas/       # Pydantic-модели
├── utils/         # Логирование
├── sqlalchemy_db.py
├── exception_handlers.py
└── dependencies.py
```

- **Роутеры** - тонкий слой: валидация и вызов сервисов.
- **Сервисы** - логика, работа с репозиториями через DI.
- **Контракты** - типобезопасные Protocol-интерфейсы для DI.
- **Репозитории** - асинхронный доступ к PostgreSQL через SQLAlchemy AsyncSession.
- **Models** - отражение таблиц в ORM-модели.
- **Middlewares** - `X-Correlation-ID` + лог latency.
- **Схемы** - валидация запросов/ответов.
- **utils** - `logging.py`.

## Запуск

Из корня `alerts`:

```bash
python3.10 -m uvicorn --app-dir fastapi/app alerts:app --host 0.0.0.0 --port 8888
```

Альтернатива (из директории `fastapi`):

```bash
python3.10 -m uvicorn app.alerts:app --host 0.0.0.0 --port 8888
```

Документация: `/alerts/docs`, `/alerts/redoc`, `/alerts/openapi.json`.

## Переменные окружения

| Переменная    | Описание        |
|---------------|-----------------|
| `db_host`     | Хост БД         |
| `db`          | Имя БД          |
| `db_login`    | Пользователь БД |
| `db_password` | Пароль БД       |
| `LEVEL_LOG`   | Уровень логов (`debug/info/warning/error`, по умолчанию: `notset`) |
| `LOG_FILE_PATH` | Путь к файлу логов (по умолчанию: `logs/alerts.log` относительно `fastapi/`) |
| `LOG_FILE_MAX_BYTES` | Размер ротации файла логов |
| `LOG_FILE_BACKUP_COUNT` | Количество backup-файлов при ротации |

## Особенности

- Асинхронный код (async/await), SQLAlchemy AsyncSession.
- Валидация через Pydantic, DI через FastAPI Depends и Protocol-контракты.
- Централизованные обработчики исключений c debug/non-debug политикой trace.
- `X-Correlation-ID` в каждом ответе и correlation-id в логах.
