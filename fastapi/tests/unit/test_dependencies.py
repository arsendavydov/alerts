"""
Модульные тесты для dependencies.py.
"""

from dependencies import (
    get_alerts_repository,
    get_alerts_service,
    get_dt_repository,
    get_dt_service,
    get_feedback_repository,
    get_feedback_service,
    get_indicators_repository,
    get_indicators_service,
    get_links_repository,
    get_links_service,
    get_pauses_repository,
    get_pauses_service,
    get_rules_repository,
    get_rules_service,
    get_screenshots_repository,
    get_screenshots_service,
    get_subscriptions_repository,
    get_subscriptions_service,
    get_users_repository,
    get_users_service,
)


class TestDependencies:
    """Тесты для функций dependency injection."""

    def test_get_dt_repository(self):
        """Тест создания DTRepository."""
        repo = get_dt_repository()
        assert repo is not None
        from repositories.dt_repository import DTRepository

        assert isinstance(repo, DTRepository)

    def test_get_alerts_repository(self):
        """Тест создания AlertsRepository."""
        repo = get_alerts_repository()
        assert repo is not None
        from repositories.alerts_repository import AlertsRepository

        assert isinstance(repo, AlertsRepository)

    def test_get_users_repository(self):
        """Тест создания UsersRepository."""
        repo = get_users_repository()
        assert repo is not None
        from repositories.users_repository import UsersRepository

        assert isinstance(repo, UsersRepository)

    def test_get_screenshots_repository(self):
        """Тест создания ScreenshotsRepository."""
        repo = get_screenshots_repository()
        assert repo is not None
        from repositories.screenshots_repository import ScreenshotsRepository

        assert isinstance(repo, ScreenshotsRepository)

    def test_get_feedback_repository(self):
        """Тест создания FeedbackRepository."""
        repo = get_feedback_repository()
        assert repo is not None
        from repositories.feedback_repository import FeedbackRepository

        assert isinstance(repo, FeedbackRepository)

    def test_get_indicators_repository(self):
        """Тест создания IndicatorsRepository."""
        repo = get_indicators_repository()
        assert repo is not None
        from repositories.indicators_repository import IndicatorsRepository

        assert isinstance(repo, IndicatorsRepository)

    def test_get_links_repository(self):
        """Тест создания LinksRepository."""
        repo = get_links_repository()
        assert repo is not None
        from repositories.links_repository import LinksRepository

        assert isinstance(repo, LinksRepository)

    def test_get_pauses_repository(self):
        """Тест создания PausesRepository."""
        repo = get_pauses_repository()
        assert repo is not None
        from repositories.pauses_repository import PausesRepository

        assert isinstance(repo, PausesRepository)

    def test_get_rules_repository(self):
        """Тест создания RulesRepository."""
        repo = get_rules_repository()
        assert repo is not None
        from repositories.rules_repository import RulesRepository

        assert isinstance(repo, RulesRepository)

    def test_get_dt_service(self):
        """Тест создания DTService с внедренным репозиторием."""
        service = get_dt_service()
        assert service is not None
        from services.dt_service import DTService

        assert isinstance(service, DTService)
        assert service.repository is not None

    def test_get_alerts_service(self):
        """Тест создания AlertsService с внедренным репозиторием."""
        service = get_alerts_service()
        assert service is not None
        from services.alerts_service import AlertsService

        assert isinstance(service, AlertsService)
        assert service.repository is not None

    def test_get_users_service(self):
        """Тест создания UsersService с внедренным репозиторием."""
        service = get_users_service()
        assert service is not None
        from services.users_service import UsersService

        assert isinstance(service, UsersService)
        assert service.repository is not None

    def test_get_screenshots_service(self):
        """Тест создания ScreenshotsService с внедренным репозиторием."""
        service = get_screenshots_service()
        assert service is not None
        from services.screenshots_service import ScreenshotsService

        assert isinstance(service, ScreenshotsService)
        assert service.repository is not None

    def test_get_feedback_service(self):
        """Тест создания FeedbackService с внедренным репозиторием."""
        service = get_feedback_service()
        assert service is not None
        from services.feedback_service import FeedbackService

        assert isinstance(service, FeedbackService)
        assert service.repository is not None

    def test_get_indicators_service(self):
        """Тест создания IndicatorsService с внедренным репозиторием."""
        service = get_indicators_service()
        assert service is not None
        from services.indicators_service import IndicatorsService

        assert isinstance(service, IndicatorsService)
        assert service.repository is not None

    def test_get_links_service(self):
        """Тест создания LinksService с внедренным репозиторием."""
        service = get_links_service()
        assert service is not None
        from services.links_service import LinksService

        assert isinstance(service, LinksService)
        assert service.repository is not None

    def test_get_pauses_service(self):
        """Тест создания PausesService с внедренным репозиторием."""
        service = get_pauses_service()
        assert service is not None
        from services.pauses_service import PausesService

        assert isinstance(service, PausesService)
        assert service.repository is not None

    def test_get_rules_service(self):
        """Тест создания RulesService с внедренным репозиторием."""
        service = get_rules_service()
        assert service is not None
        from services.rules_service import RulesService

        assert isinstance(service, RulesService)
        assert service.repository is not None

    def test_get_subscriptions_repository(self):
        """Тест создания SubscriptionsRepository."""
        repo = get_subscriptions_repository()
        assert repo is not None
        from repositories.subscriptions_repository import (
            SubscriptionsRepository,
        )

        assert isinstance(repo, SubscriptionsRepository)

    def test_get_subscriptions_service(self):
        """Тест создания SubscriptionsService с внедренным репозиторием."""
        service = get_subscriptions_service()
        assert service is not None
        from services.subscriptions_service import SubscriptionsService

        assert isinstance(service, SubscriptionsService)
        assert service.repository is not None
