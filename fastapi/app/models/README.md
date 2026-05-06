# ORM-модели и карта таблиц

## Цель

Файл фиксирует целевую карту миграции `alerts` на SQLAlchemy ORM по аналогии с `cron`.

## Текущий статус по доменам

| Домен | Таблицы | ORM статус |
|---|---|---|
| alerts | `alerts.alerts`, `alerts.group_rules`, `alerts.pause_history`, `alerts.status_history`, `alerts.alerts_links`, `alerts.alerts_contacts`, `alerts.alerts_contacts_status`, `alerts.alerts_dt` | ✅ Реализовано в `models/alerts.py` |
| indicators | `dictionary.events` | ✅ Реализовано в `models/dictionary.py` |
| pauses | `alerts.pause_history` | ✅ Реализовано в `models/alerts.py` |
| subscriptions | `alerts.alerts_contacts`, `alerts.alerts_contacts_status`, `alerts.contacts` | ✅ Реализовано в `models/alerts.py` |
| screenshots | `alerts.screenshots` | ✅ Реализовано в `models/alerts.py` |
| dt | `alerts.alerts_dt` | ✅ Реализовано в `models/alerts.py` |
| users | `alerts.contacts`, `telegram_bot.spr_users` | ✅ Реализовано в `models/alerts.py` |
| links | `alerts.alerts_links` | ✅ Реализовано в `models/alerts.py` |
| feedback | `alerts.feedback` | ✅ Реализовано в `models/alerts.py` |
| rules | `alerts.group_rules` | ✅ Реализовано в `models/alerts.py` |

## Примечания по runtime

- Приложение использует ORM-модели как основной источник схемы для статических таблиц.
- Reflection таблиц в runtime оставлена только для динамических колонок, которые нельзя стабильно зафиксировать в ORM-модели (например, каналы уведомлений в `alerts.alerts_contacts`).

## Принципы для новых ORM-моделей

- UUID генерируются на стороне БД через `server_default=text("gen_random_uuid()")`.
- Nullable и текстовые/JSON-поля отражаются 1:1 с контрактом API.
- Любая новая ORM-модель добавляется в `models/__init__.py`.
