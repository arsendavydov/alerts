"""
Модульные тесты для exception_handlers.py.
"""

import json
import os
from unittest.mock import Mock, patch

import pytest
import pytest_asyncio
from exception_handlers import (
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from httpx import AsyncClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from utils.logging import log


class TestExceptionHandlers:
    """Тесты для обработчиков исключений."""

    @pytest.fixture
    def app(self):
        """Создает FastAPI приложение."""
        app = FastAPI()
        app.add_exception_handler(
            StarletteHTTPException, http_exception_handler
        )
        app.add_exception_handler(
            RequestValidationError, validation_exception_handler
        )
        app.add_exception_handler(Exception, global_exception_handler)
        return app

    @pytest_asyncio.fixture
    async def client(self, app):
        """Асинхронный тестовый клиент."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_http_exception_handler(self, app, client):
        """Тест обработчика HTTP исключений."""

        @app.get("/test-http-exception")
        async def test_endpoint():
            raise HTTPException(status_code=404, detail="Not found")

        response = await client.get("/test-http-exception")
        assert response.status_code == 404
        assert "status" in response.json()
        assert "message" in response.json()

    @pytest.mark.asyncio
    async def test_validation_exception_handler(self, app, client):
        """Тест обработчика ошибок валидации."""

        @app.get("/test-validation")
        async def test_endpoint(param: int):
            return {"param": param}

        response = await client.get("/test-validation?param=not_a_number")
        assert response.status_code == 400
        assert "status" in response.json()
        assert "message" in response.json()

    @pytest.mark.asyncio
    async def test_global_exception_handler_direct(self):
        """Тест глобального обработчика исключений (прямой вызов)."""
        from starlette.requests import Request

        mock_request = Mock(spec=Request)
        exc = ValueError("Test error")
        with patch.dict(os.environ, {"LEVEL_LOG": "INFO"}, clear=False):
            response = await global_exception_handler(mock_request, exc)

        assert response.status_code == 500
        response_json = json.loads(response.body.decode())
        assert "status" in response_json
        # В не-debug режиме поле trace должно быть пустым
        assert response_json.get("message", {}).get("trace") is None

    @pytest.mark.asyncio
    async def test_global_exception_handler_logs_traceback(self):
        """Тест что глобальный обработчик логирует трейсбек на сервере."""
        from starlette.requests import Request

        mock_request = Mock(spec=Request)
        exc = ValueError("Test error message")

        with patch.object(log, "error") as mock_log_error:
            await global_exception_handler(mock_request, exc)

            # Проверяем что логирование было вызвано
            assert mock_log_error.called
            log_message = str(mock_log_error.call_args)
            # Проверяем что в логе есть тип исключения и трейсбек
            assert "ValueError" in log_message
            assert (
                "Traceback" in log_message
                or "traceback" in log_message.lower()
            )

    @pytest.mark.asyncio
    async def test_global_exception_handler_client_message(self):
        """Тест что клиенту возвращается короткое сообщение без деталей."""
        from starlette.requests import Request

        mock_request = Mock(spec=Request)
        exc = ValueError("Internal error details")

        response = await global_exception_handler(mock_request, exc)
        response_json = response.body.decode()

        # Клиент должен получить общее сообщение, а не детали ошибки
        assert "Внутренняя ошибка сервера" in response_json
        # Детали ошибки (текст исключения) не должны быть в ответе
        assert "Internal error details" not in response_json

    @pytest.mark.asyncio
    async def test_global_exception_handler_trace_in_debug(self):
        """Тест что в debug режиме trace попадает в ответ."""
        from starlette.requests import Request

        mock_request = Mock(spec=Request)
        exc = ValueError("debug details")
        with patch.dict(os.environ, {"LEVEL_LOG": "DEBUG"}):
            response = await global_exception_handler(mock_request, exc)
        response_json = response.body.decode()
        assert '"trace"' in response_json

    @pytest.mark.asyncio
    async def test_http_exception_no_traceback(self, app, client):
        """Тест что HTTPException не содержит трейсбек."""

        @app.get("/test-http-no-trace")
        async def test_endpoint():
            raise HTTPException(status_code=404, detail="Not found")

        response = await client.get("/test-http-no-trace")
        response_json = response.json()

        # HTTPException - ожидаемая ошибка, трейсбек не нужен
        assert response_json.get("message", {}).get("trace") is None

    @pytest.mark.asyncio
    async def test_validation_exception_no_traceback(self, app, client):
        """Тест что ValidationError не содержит трейсбек."""

        @app.get("/test-validation-no-trace")
        async def test_endpoint(param: int):
            return {"param": param}

        response = await client.get(
            "/test-validation-no-trace?param=not_a_number"
        )
        response_json = response.json()

        # ValidationError - ожидаемая ошибка, трейсбек не нужен
        assert response_json.get("message", {}).get("trace") is None
