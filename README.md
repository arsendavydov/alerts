# Alerts Service - FastAPI backend для управления алертами мониторинга

Production-style backend-сервис для централизованного управления алертами: поиск, подписки, паузы, скриншоты/ссылки и интеграции.

## Для рекрутеров и hiring-менеджеров

Этот репозиторий показывает:
- реальную backend-разработку в домене мониторинга (не учебный CRUD),
- асинхронную архитектуру на FastAPI + PostgreSQL,
- понятное слоистое разделение (`Router -> Service -> Repository`),
- бизнес-процессы вокруг жизненного цикла алертов и подписок,
- тестирование на уровнях unit/integration/e2e.

Если у вас 2-3 минуты, посмотрите:
- `fastapi/app/` - код приложения,
- `fastapi/tests/` - структуру тестов,
- `PRD.md` - продуктовые и бизнес-требования.

## Ключевые возможности

- Поиск и фильтрация алертов (пагинация и сортировка)
- Управление подписками на алерты (пользователи/каналы/настройки)
- Управление паузами алертов (условные и безусловные)
- Создание и обновление карточки алерта
- Интеграции с внешними сущностями (скриншоты, ссылки, DT-связанные поля)
- Структурированная обработка ошибок и схемы ответов

## Технологический стек

- Python 3.10
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0 (async)
- Pydantic
- Uvicorn
- AppDynamics (интеграция мониторинга в контексте проекта)

## Архитектура

Сервис построен по слоистой архитектуре:

- `routers/` - HTTP-эндпоинты и валидация входных данных
- `services/` - бизнес-логика и оркестрация
- `repositories/` - слой доступа к данным (ORM/Core)
- `models/` - ORM-модели SQLAlchemy
- `schemas/` - pydantic-модели запросов и ответов
- `utils/` - вспомогательные модули (db/logging/errors/context)
- `contracts/` - интерфейсы на базе protocol-контрактов

Дополнительно:
- `fastapi/app/ARCHITECTURE_NOTES.md`
- `PRD.md`

## Структура проекта

```text
alerts/
├── PRD.md
├── README.md
└── fastapi/
    ├── app/
    │   ├── routers/
    │   ├── services/
    │   ├── repositories/
    │   ├── models/
    │   ├── schemas/
    │   ├── contracts/
    │   └── utils/
    ├── tests/
    │   ├── unit/
    │   ├── integration/
    │   └── e2e/
    └── README.md
```

## Быстрый старт

Из корня проекта:

```bash
pip install -r fastapi/requirements.txt
# настройте переменные окружения: db_host, db, db_login, db_password
python3.10 -m uvicorn --app-dir fastapi/app alerts:app --host 0.0.0.0 --port 8888
```

Документация API:
- [http://localhost:8888/alerts/docs](http://localhost:8888/alerts/docs)

