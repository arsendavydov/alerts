"""
Модульные тесты для валидации схем ResponseError.
"""

import sys
from pathlib import Path

# Добавляем путь к app для импортов
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "app"))
from schemas.response_error import MessageError, ResponseStatus, response_error


class TestMessageError:
    """Тесты для MessageError."""

    def test_valid_error(self):
        """Тест валидной ошибки."""
        data = MessageError(
            type="ValidationError", error="Invalid input", trace="Traceback..."
        )
        assert data.type == "ValidationError"
        assert data.error == "Invalid input"
        assert data.trace == "Traceback..."


class TestResponseError:
    """Тесты для response_error."""

    def test_valid_error_response(self):
        """Тест валидного ответа с ошибкой."""
        message = MessageError(
            type="ValidationError", error="Invalid input", trace="Traceback..."
        )
        data = response_error(status=ResponseStatus.error, message=message)
        assert data.status == ResponseStatus.error
        assert data.message.type == "ValidationError"

    def test_with_ok_status(self):
        """Тест с ok статусом."""
        message = MessageError(type="Info", error="Success", trace="")
        data = response_error(status=ResponseStatus.ok, message=message)
        assert data.status == ResponseStatus.ok
