"""
Обработчики исключений для FastAPI приложения.
Транзакции БД управляются автоматически через контекстные менеджеры,
поэтому ручной rollback не требуется.
"""

import os
import traceback

from fastapi.responses import JSONResponse

from schemas.response_error import MessageError, ResponseStatus, response_error
from utils import log


def _error_response(
    type_name: str,
    error_text: str,
    status_code: int,
    include_trace: bool = False,
) -> JSONResponse:
    """Формирует JSONResponse с единым форматом ошибки."""
    trace_str = traceback.format_exc() if include_trace else None
    err = response_error(
        status=ResponseStatus.error,
        message=MessageError(
            type=type_name, error=error_text, trace=trace_str
        ),
    )
    return JSONResponse(err.model_dump(), status_code=status_code)


async def http_exception_handler(request, exc) -> JSONResponse:
    """Обработчик HTTP исключений (HTTPException)."""
    return _error_response(
        type(exc).__name__, str(exc.detail), exc.status_code
    )


async def validation_exception_handler(request, exc) -> JSONResponse:
    """Обработчик ошибок валидации (RequestValidationError)."""
    return _error_response(type(exc).__name__, str(exc), 400)


async def global_exception_handler(request, exc) -> JSONResponse:
    """Глобальный обработчик всех исключений."""
    full_traceback = traceback.format_exc()
    log.error(
        f"[GlobalExceptionHandler] Unhandled exception: {type(exc).__name__}\n"
        f"Error: {exc}\n"
        f"Traceback:\n{full_traceback}"
    )
    client_error_text = (
        "Внутренняя ошибка сервера. Обратитесь к администратору."
    )
    include_trace = os.getenv("LEVEL_LOG", "").lower() == "debug"
    return _error_response(
        type_name=type(exc).__name__,
        error_text=client_error_text,
        status_code=500,
        include_trace=include_trace,
    )
