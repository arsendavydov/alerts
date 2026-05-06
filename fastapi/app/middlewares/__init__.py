"""Пакет middleware приложения alerts."""

from .request_context import request_context_middleware

__all__ = ["request_context_middleware"]
