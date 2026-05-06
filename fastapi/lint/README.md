# Линтинг и проверка типов

Запуск из **корня репозитория** (не из папки fastapi/):

```bash
./fastapi/lint/lint.sh
./fastapi/lint/lint.sh --fix
```

- Без аргументов или с `check` - ruff check + pyright.
- С `--fix` - ruff check --fix и ruff format.

## Что проверяется

- **ruff** - стиль и типичные ошибки (в т.ч. длина строки 79 по PEP8 для кода вне репозиториев/сервисов/тестов).
- **pyright** - типы.

Проверяется вся папка `fastapi/`.
