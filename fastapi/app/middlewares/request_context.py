"""Middleware для correlation-id и latency."""

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

import utils
from fastapi import Request, Response

logger = logging.getLogger("alerts")
CORRELATION_ID_HEADER = "X-Correlation-ID"


async def request_context_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Добавляет correlation-id в контекст и измеряет latency запроса."""
    start_time = time.perf_counter()
    status_code = 500
    correlation_id = request.headers.get(CORRELATION_ID_HEADER) or str(
        uuid.uuid4()
    )
    request.state.correlation_id = correlation_id
    utils.set_correlation_id(correlation_id)

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response
    finally:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "Request completed: %s %s status=%s latency_ms=%.2f",
            request.method,
            request.url.path,
            status_code,
            latency_ms,
        )
        utils.set_correlation_id("-")
