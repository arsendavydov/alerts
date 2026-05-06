#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

# Проверяем, что Python 3.10 доступен
if ! command -v python3.10 &> /dev/null; then
    echo "❌ Python 3.10 не найден!"
    echo "Установите Python 3.10 или обновите PATH"
    exit 1
fi

# Проверяем, что ruff и pyright установлены
if ! python3.10 -m ruff --version &> /dev/null; then
    echo "❌ ruff не установлен!"
    echo "Установите зависимости: pip install -r fastapi/requirements.txt"
    exit 1
fi

if ! python3.10 -m pyright --version &> /dev/null; then
    echo "❌ pyright не установлен!"
    echo "Установите зависимости: pip install -r fastapi/requirements.txt"
    exit 1
fi

# По умолчанию выполняем check
if [ "$1" = "--fix" ]; then
    ACTION="fix"
else
    ACTION="check"
fi

case "$ACTION" in
    check)
        echo "🔍 Запуск ruff check..."
        python3.10 -m ruff check fastapi/
        
        echo ""
        echo "🔍 Запуск pyright для проверки типов..."
        cd fastapi
        python3.10 -m pyright .
        cd ..
        
        echo ""
        echo "✅ Все проверки завершены!"
        ;;
    fix)
        echo "🔧 Запуск ruff check --fix --unsafe-fixes..."
        python3.10 -m ruff check --fix --unsafe-fixes fastapi/
        
        echo ""
        echo "✨ Запуск ruff format..."
        python3.10 -m ruff format fastapi/
        
        echo ""
        echo "✅ Линтинг и форматирование завершены!"
        ;;
    *)
        echo "Использование: $0 [--fix]"
        echo ""
        echo "Команды:"
        echo "  (без аргументов)  - Проверить код (linting + type checking)"
        echo "  --fix             - Исправить и отформатировать код"
        echo ""
        exit 1
        ;;
esac
