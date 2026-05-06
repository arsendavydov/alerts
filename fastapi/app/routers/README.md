# Роутеры

HTTP endpoints. Принимают запросы, валидируют через Pydantic, вызывают сервисы через `Depends(get_*_service)`.

Файлы по доменам: alerts, pauses, subscriptions, users, screenshots, links, indicators, rules, feedback, dt. Тесты: `tests/unit/routers/`.
