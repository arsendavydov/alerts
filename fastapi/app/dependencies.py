"""
Dependency Injection для FastAPI.
Создает и управляет зависимостями между слоями приложения.
"""

from contracts.repository_protocols import (
    AlertsRepositoryProtocol,
    DTRepositoryProtocol,
    FeedbackRepositoryProtocol,
    IndicatorsRepositoryProtocol,
    LinksRepositoryProtocol,
    PausesRepositoryProtocol,
    RulesRepositoryProtocol,
    ScreenshotsRepositoryProtocol,
    SubscriptionsRepositoryProtocol,
    UsersRepositoryProtocol,
)
from contracts.service_protocols import (
    AlertsServiceProtocol,
    DTServiceProtocol,
    FeedbackServiceProtocol,
    IndicatorsServiceProtocol,
    LinksServiceProtocol,
    PausesServiceProtocol,
    RulesServiceProtocol,
    ScreenshotsServiceProtocol,
    SubscriptionsServiceProtocol,
    UsersServiceProtocol,
)

from fastapi import Depends
from repositories.alerts_repository import AlertsRepository
from repositories.dt_repository import DTRepository
from repositories.feedback_repository import FeedbackRepository
from repositories.indicators_repository import IndicatorsRepository
from repositories.links_repository import LinksRepository
from repositories.pauses_repository import PausesRepository
from repositories.rules_repository import RulesRepository
from repositories.screenshots_repository import ScreenshotsRepository
from repositories.subscriptions_repository import SubscriptionsRepository
from repositories.users_repository import UsersRepository
from services.alerts_service import AlertsService
from services.dt_service import DTService
from services.feedback_service import FeedbackService
from services.indicators_service import IndicatorsService
from services.links_service import LinksService
from services.pauses_service import PausesService
from services.rules_service import RulesService
from services.screenshots_service import ScreenshotsService
from services.subscriptions_service import SubscriptionsService
from services.users_service import UsersService


def get_dt_repository() -> DTRepositoryProtocol:
    """DI-провайдер репозитория DT."""
    return DTRepository()


def get_dt_service(
    repository: DTRepositoryProtocol = Depends(get_dt_repository),
) -> DTServiceProtocol:
    """DI-провайдер сервиса DT."""
    return DTService(repository=repository)


def get_alerts_repository() -> AlertsRepositoryProtocol:
    """DI-провайдер репозитория alerts."""
    return AlertsRepository()


def get_alerts_service(
    repository: AlertsRepositoryProtocol = Depends(get_alerts_repository),
) -> AlertsServiceProtocol:
    """DI-провайдер сервиса alerts."""
    return AlertsService(repository=repository)


def get_users_repository() -> UsersRepositoryProtocol:
    """DI-провайдер репозитория users."""
    return UsersRepository()


def get_users_service(
    repository: UsersRepositoryProtocol = Depends(get_users_repository),
) -> UsersServiceProtocol:
    """DI-провайдер сервиса users."""
    return UsersService(repository=repository)


def get_screenshots_repository() -> ScreenshotsRepositoryProtocol:
    """DI-провайдер репозитория screenshots."""
    return ScreenshotsRepository()


def get_screenshots_service(
    repository: ScreenshotsRepositoryProtocol = Depends(
        get_screenshots_repository
    ),
) -> ScreenshotsServiceProtocol:
    """DI-провайдер сервиса screenshots."""
    return ScreenshotsService(repository=repository)


def get_feedback_repository() -> FeedbackRepositoryProtocol:
    """DI-провайдер репозитория feedback."""
    return FeedbackRepository()


def get_feedback_service(
    repository: FeedbackRepositoryProtocol = Depends(get_feedback_repository),
) -> FeedbackServiceProtocol:
    """DI-провайдер сервиса feedback."""
    return FeedbackService(repository=repository)


def get_indicators_repository() -> IndicatorsRepositoryProtocol:
    """DI-провайдер репозитория indicators."""
    return IndicatorsRepository()


def get_indicators_service(
    repository: IndicatorsRepositoryProtocol = Depends(
        get_indicators_repository
    ),
) -> IndicatorsServiceProtocol:
    """DI-провайдер сервиса indicators."""
    return IndicatorsService(repository=repository)


def get_links_repository() -> LinksRepositoryProtocol:
    """DI-провайдер репозитория links."""
    return LinksRepository()


def get_links_service(
    repository: LinksRepositoryProtocol = Depends(get_links_repository),
) -> LinksServiceProtocol:
    """DI-провайдер сервиса links."""
    return LinksService(repository=repository)


def get_pauses_repository() -> PausesRepositoryProtocol:
    """DI-провайдер репозитория pauses."""
    return PausesRepository()


def get_pauses_service(
    repository: PausesRepositoryProtocol = Depends(get_pauses_repository),
) -> PausesServiceProtocol:
    """DI-провайдер сервиса pauses."""
    return PausesService(repository=repository)


def get_rules_repository() -> RulesRepositoryProtocol:
    """DI-провайдер репозитория rules."""
    return RulesRepository()


def get_rules_service(
    repository: RulesRepositoryProtocol = Depends(get_rules_repository),
) -> RulesServiceProtocol:
    """DI-провайдер сервиса rules."""
    return RulesService(repository=repository)


def get_subscriptions_repository() -> SubscriptionsRepositoryProtocol:
    """DI-провайдер репозитория subscriptions."""
    return SubscriptionsRepository()


def get_subscriptions_service(
    repository: SubscriptionsRepositoryProtocol = Depends(
        get_subscriptions_repository
    ),
) -> SubscriptionsServiceProtocol:
    """DI-провайдер сервиса subscriptions."""
    return SubscriptionsService(repository=repository)


__all__ = [
    "get_alerts_repository",
    "get_alerts_service",
    "get_dt_repository",
    "get_dt_service",
    "get_feedback_repository",
    "get_feedback_service",
    "get_indicators_repository",
    "get_indicators_service",
    "get_links_repository",
    "get_links_service",
    "get_pauses_repository",
    "get_pauses_service",
    "get_rules_repository",
    "get_rules_service",
    "get_screenshots_repository",
    "get_screenshots_service",
    "get_subscriptions_repository",
    "get_subscriptions_service",
    "get_users_repository",
    "get_users_service",
]
