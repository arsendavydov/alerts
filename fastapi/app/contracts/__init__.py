"""Пакет контрактов (Protocol) для repositories и services."""

from .repository_protocols import AlertsRepositoryProtocol
from .service_protocols import (
    AlertsServiceProtocol,
    PausesServiceProtocol,
    SubscriptionsServiceProtocol,
)

__all__ = [
    "AlertsRepositoryProtocol",
    "AlertsServiceProtocol",
    "PausesServiceProtocol",
    "SubscriptionsServiceProtocol",
]
