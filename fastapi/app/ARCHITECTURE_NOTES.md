# Архитектурные заметки

## Разделение инфраструктуры: `app/utils` vs отдельные модули

### Оставить в `app/utils`

- `db.py` - минимальные DB-утилиты (например, `add_pagination_to_query`), без asyncpg pool/helper API.
- `exceptions.py` - доменные исключения и вспомогательные типы ошибок.
- `logging.py` - базовая конфигурация логирования и context correlation-id.

### Вынести/держать отдельными модулями

- `sqlalchemy_db.py` - единый инфраструктурный модуль AsyncEngine/AsyncSession.
- `middlewares/request_context.py` - observability middleware (correlation-id + latency).
- `contracts/*` - границы слоев (Protocol).
- `repositories/mappers/*` - data mapper слой для преобразований ORM/row -> schema.

## Стратегия миграции

- Основной этап вертикальной миграции завершен: runtime-код работает через SQLAlchemy ORM/Core.
- Для фронта сохранены действующие HTTP-контракты (включая legacy lazy-сценарии).
- Reflection в runtime используется только для действительно динамических схем/колонок.
