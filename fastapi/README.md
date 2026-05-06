# Alerts - сервис алертов мониторинга

API для управления алертами (поиск, подписки, паузы, скриншоты, DT и др.).


## Быстрый старт

```bash
pip install -r requirements.txt
# Настроить .env (db_host, db, db_login, db_password)
python3.10 -m uvicorn --app-dir fastapi/app alerts:app --host 0.0.0.0 --port 8888
```

Документация API: http://localhost:8888/alerts/docs

## Требования

- Python 3.10
- PostgreSQL
