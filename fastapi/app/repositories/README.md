# Репозитории

Доступ к данным через `SQLAlchemy AsyncSession`, ORM/Core-выражения и явные UoW-границы.

- Runtime-код приложения работает в ORM-first подходе.
- Reflection используется только там, где схема/набор колонок действительно динамический (например, notification channels в `alerts.alerts_contacts`).
- Legacy `asyncpg` helper-ветки в доменных репозиториях удалены.

Тесты: `tests/unit/repositories/`.
