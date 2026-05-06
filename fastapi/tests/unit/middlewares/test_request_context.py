"""Тесты middleware correlation-id / latency."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from middlewares.request_context import (
    CORRELATION_ID_HEADER,
    request_context_middleware,
)

from fastapi import Response

pytestmark = pytest.mark.asyncio


async def test_request_context_sets_header_and_state():
    """Ответ содержит X-Correlation-ID; в request.state записан тот же id."""
    request = MagicMock()
    request.headers = {}
    request.state = MagicMock()
    request.method = "GET"
    request.url.path = "/alerts/api/v1/ping"

    inner = AsyncMock(return_value=Response(status_code=200, content=b"{}"))

    response = await request_context_middleware(request, inner)

    assert response.status_code == 200
    cid = response.headers[CORRELATION_ID_HEADER]
    assert cid
    assert request.state.correlation_id == cid
    inner.assert_awaited_once_with(request)


async def test_request_context_preserves_incoming_correlation_id():
    """Если клиент передал X-Correlation-ID, он сохраняется в ответе."""
    existing = "550e8400-e29b-41d4-a716-446655440000"
    request = MagicMock()
    request.headers = {CORRELATION_ID_HEADER: existing}
    request.state = MagicMock()
    request.method = "POST"
    request.url.path = "/alerts/api/v1/alerts/search"

    inner = AsyncMock(return_value=Response(status_code=201, content=b"{}"))

    response = await request_context_middleware(request, inner)

    assert response.headers[CORRELATION_ID_HEADER] == existing
    assert request.state.correlation_id == existing
