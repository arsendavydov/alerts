"""
Модульные тесты для SubscriptionsService.
"""

from typing import ClassVar
from unittest.mock import ANY, AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from repositories.subscriptions_repository import SubscriptionsRepository
from schemas.subscriptions import (
    AlertByUserListResponse,
    SubscribeRequest,
    SubscriptionByUserUpdate,
    SubscriptionContacts,
    UnsubscribeRequest,
)
from services.subscriptions_service import SubscriptionsService

# Включаем поддержку async тестов
pytestmark = pytest.mark.asyncio


class TestSubscriptionsService:
    """Тесты для SubscriptionsService."""

    @pytest.fixture(autouse=True)
    def _stub_uow_session(self):
        """Сервис использует async_session_scope - без реальной БД."""
        cm = AsyncMock()
        cm.__aenter__.return_value = None
        cm.__aexit__.return_value = None
        with patch(
            "services.subscriptions_service.async_session_scope",
            return_value=cm,
        ):
            yield

    @pytest.fixture
    def mock_repo(self):
        """Мок репозитория."""
        return AsyncMock(spec=SubscriptionsRepository)

    @pytest.fixture
    def service(self, mock_repo):
        """Экземпляр SubscriptionsService с моком репозитория."""
        return SubscriptionsService(repository=mock_repo)

    async def test_subscribe_success(self, service, mock_repo):
        """Тест успешной подписки."""
        alert_id = uuid4()
        user_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_subscription_exists.return_value = None
        mock_repo.get_user_data.return_value = {
            "id": user_id,
            "user_name": "user_name",
            "email": "email@test.com",
            "telegram": True,
            "telegram_id": True,
        }
        mock_repo.get_alerts_contacts_columns.return_value = [
            "telegram",
            "email",
        ]
        mock_repo.get_user_columns.return_value = [
            "id",
            "user_name",
            "email",
            "telegram",
            "telegram_id",
        ]
        mock_repo.create_subscription.return_value = uuid4()

        data = SubscribeRequest(alert_id=alert_id, user_id=user_id)

        result = await service.subscribe(data)

        assert result is True
        mock_repo.check_alert_exists.assert_called_once_with(alert_id, ANY)
        mock_repo.create_subscription.assert_called_once()

    async def test_subscribe_alert_not_found(self, service, mock_repo):
        """Тест подписки на несуществующий алерт."""
        alert_id = uuid4()
        user_id = uuid4()
        mock_repo.check_alert_exists.return_value = False

        data = SubscribeRequest(alert_id=alert_id, user_id=user_id)

        with pytest.raises(HTTPException) as exc_info:
            await service.subscribe(data)

        assert exc_info.value.status_code == 404
        assert "не найден" in exc_info.value.detail

    async def test_subscribe_already_exists(self, service, mock_repo):
        """Тест подписки, когда подписка уже существует."""
        alert_id = uuid4()
        user_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_subscription_exists.return_value = uuid4()

        data = SubscribeRequest(alert_id=alert_id, user_id=user_id)

        with pytest.raises(HTTPException) as exc_info:
            await service.subscribe(data)

        assert exc_info.value.status_code == 409
        assert "уже подписан" in exc_info.value.detail

    async def test_subscribe_user_not_found(self, service, mock_repo):
        """Тест подписки несуществующего пользователя."""
        alert_id = uuid4()
        user_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_subscription_exists.return_value = None
        mock_repo.get_user_data.return_value = None

        data = SubscribeRequest(alert_id=alert_id, user_id=user_id)

        with pytest.raises(HTTPException) as exc_info:
            await service.subscribe(data)

        assert exc_info.value.status_code == 404
        assert "не найден" in exc_info.value.detail

    async def test_unsubscribe_success(self, service, mock_repo):
        """Тест успешной отписки."""
        alert_id = uuid4()
        user_id = uuid4()
        subscription_id = uuid4()
        mock_repo.check_subscription_exists.return_value = subscription_id
        mock_repo.delete_subscription_statuses.return_value = 2
        mock_repo.delete_subscription.return_value = True

        data = UnsubscribeRequest(alert_id=alert_id, user_id=user_id)

        result = await service.unsubscribe(data)

        assert result is True
        mock_repo.delete_subscription_statuses.assert_called_once_with(
            subscription_id, ANY
        )
        mock_repo.delete_subscription.assert_called_once_with(
            subscription_id, ANY
        )

    async def test_unsubscribe_not_found(self, service, mock_repo):
        """Тест отписки несуществующей подписки."""
        alert_id = uuid4()
        user_id = uuid4()
        mock_repo.check_subscription_exists.return_value = None

        data = UnsubscribeRequest(alert_id=alert_id, user_id=user_id)

        with pytest.raises(HTTPException) as exc_info:
            await service.unsubscribe(data)

        assert exc_info.value.status_code == 404
        assert "не найдена" in exc_info.value.detail

    async def test_get_subscription_by_alert_and_user_success(
        self, service, mock_repo
    ):
        """Тест успешного получения подписки."""
        alert_id = uuid4()
        user_id = uuid4()
        subscription_id = uuid4()
        mock_repo.check_subscription_exists.return_value = subscription_id
        mock_repo.get_subscription_by_id.return_value = {
            "id": subscription_id,
            "alert": alert_id,
            "contact": user_id,
            "telegram": True,
            "email": True,
        }
        mock_repo.get_alerts_contacts_columns.return_value = [
            "telegram",
            "email",
        ]
        mock_repo.get_all_notification_statuses.return_value = [
            {"id": uuid4(), "status_name": "Status 1"},
            {"id": uuid4(), "status_name": "Status 2"},
        ]
        mock_repo.get_subscription_statuses.return_value = {}
        result = await service.get_subscription_by_alert_and_user(
            alert_id, user_id
        )

        assert result.subscription_id == subscription_id
        assert len(result.statuses) == 2

    async def test_get_subscription_by_alert_and_user_not_found(
        self, service, mock_repo
    ):
        """Тест получения несуществующей подписки."""
        alert_id = uuid4()
        user_id = uuid4()
        mock_repo.check_subscription_exists.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.get_subscription_by_alert_and_user(alert_id, user_id)

        assert exc_info.value.status_code == 404

    async def test_update_subscription_by_alert_and_user_success(
        self, service, mock_repo
    ):
        """Тест успешного обновления подписки."""
        alert_id = uuid4()
        user_id = uuid4()
        subscription_id = uuid4()
        status_id = uuid4()
        mock_repo.check_subscription_exists.return_value = subscription_id
        mock_repo.get_alerts_contacts_columns.return_value = [
            "telegram",
            "email",
        ]
        mock_repo.update_subscription_channels.return_value = True
        mock_repo.get_current_subscription_statuses.return_value = {}
        mock_repo.create_subscription_status.return_value = True

        from schemas.subscriptions import SubscriptionStatusUpdateItem

        data = SubscriptionByUserUpdate(
            alert_id=alert_id,
            user_id=user_id,
            notification_channels=SubscriptionContacts(telegram=True),
            statuses=[
                SubscriptionStatusUpdateItem(
                    status_id=str(status_id), repeat=5
                )
            ],
        )

        result = await service.update_subscription_by_alert_and_user(data)

        assert result is True
        mock_repo.update_subscription_channels.assert_called_once()
        mock_repo.create_subscription_status.assert_called_once()

    async def test_update_subscription_not_found(self, service, mock_repo):
        """Тест обновления несуществующей подписки."""
        alert_id = uuid4()
        user_id = uuid4()
        mock_repo.check_subscription_exists.return_value = None

        data = SubscriptionByUserUpdate(alert_id=alert_id, user_id=user_id)

        with pytest.raises(HTTPException) as exc_info:
            await service.update_subscription_by_alert_and_user(data)

        assert exc_info.value.status_code == 404

    async def test_get_subscription_users_success(self, service, mock_repo):
        """Тест успешного получения списка пользователей."""
        alert_id = uuid4()
        user_id = uuid4()
        subscription_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.get_subscription_users.return_value = (
            [
                {
                    "id": user_id,
                    "user_name": "user1",
                    "group": False,
                    "is_subscribed": True,
                    "subscription_id": subscription_id,
                }
            ],
            1,
        )
        mock_repo.get_user_columns.return_value = [
            "id",
            "user_name",
            "group",
            "email",
        ]
        mock_repo.get_subscription_by_id.return_value = {
            "id": subscription_id,
            "alert": alert_id,
            "contact": user_id,
            "telegram": True,
        }
        mock_repo.get_alerts_contacts_columns.return_value = ["telegram"]
        mock_repo.get_all_notification_statuses.return_value = [
            {"id": uuid4(), "status_name": "Status 1"}
        ]
        mock_repo.get_subscription_statuses.return_value = {}
        result = await service.get_subscription_users(alert_id)
        assert result.total == 1
        assert len(result.users) == 1

    async def test_get_subscription_users_alert_not_found(
        self, service, mock_repo
    ):
        """Тест получения пользователей для несуществующего алерта."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await service.get_subscription_users(alert_id)

        assert exc_info.value.status_code == 404

    # Тесты валидации order_by/order_dir удалены - валидация теперь происходит в роутерах через Pydantic Literal типы

    async def test_subscribe_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при подписке."""
        alert_id = uuid4()
        user_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_subscription_exists.return_value = None
        mock_repo.get_user_data.side_effect = Exception("Ошибка БД")

        data = SubscribeRequest(alert_id=alert_id, user_id=user_id)

        with pytest.raises(HTTPException) as exc_info:
            await service.subscribe(data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при подписке" in exc_info.value.detail

    async def test_unsubscribe_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при отписке."""
        alert_id = uuid4()
        user_id = uuid4()
        subscription_id = uuid4()
        mock_repo.check_subscription_exists.return_value = subscription_id
        mock_repo.delete_subscription_statuses.side_effect = Exception(
            "Ошибка БД"
        )

        data = UnsubscribeRequest(alert_id=alert_id, user_id=user_id)

        with pytest.raises(HTTPException) as exc_info:
            await service.unsubscribe(data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при отписке" in exc_info.value.detail

    async def test_update_subscription_by_alert_and_user_error_handling(
        self, service, mock_repo
    ):
        """Тест обработки ошибки при обновлении подписки."""
        alert_id = uuid4()
        user_id = uuid4()
        subscription_id = uuid4()
        mock_repo.check_subscription_exists = AsyncMock(
            return_value=subscription_id
        )
        mock_repo.get_alerts_contacts_columns = AsyncMock(
            side_effect=Exception("Ошибка БД")
        )

        data = SubscriptionByUserUpdate(
            alert_id=alert_id,
            user_id=user_id,
            notification_channels={"telegram": True},
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.update_subscription_by_alert_and_user(data)

        assert exc_info.value.status_code == 500
        assert "Ошибка при обновлении подписки" in exc_info.value.detail

    async def test_get_subscription_users_error_handling(
        self, service, mock_repo
    ):
        """Тест обработки ошибки при получении списка пользователей."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.get_subscription_users.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.get_subscription_users(alert_id)

        assert exc_info.value.status_code == 500
        assert (
            "Ошибка при получении списка пользователей"
            in exc_info.value.detail
        )

    async def test_get_subscription_users_with_subscription_data(
        self, service, mock_repo
    ):
        """Тест получения пользователей с данными подписки."""
        alert_id = uuid4()
        user_id = uuid4()
        subscription_id = uuid4()
        status_id = uuid4()

        # Мокируем данные пользователя с подпиской
        mock_repo.check_alert_exists.return_value = True
        mock_repo.get_subscription_users.return_value = (
            [
                {
                    "id": user_id,
                    "user_name": "user1",
                    "group": False,
                    "is_subscribed": True,
                    "subscription_id": subscription_id,
                    "email": "email@test.com",
                    "telegram": True,
                }
            ],
            1,
        )
        mock_repo.get_user_columns.return_value = [
            "id",
            "user_name",
            "group",
            "email",
            "telegram",
        ]
        mock_repo.get_subscription_by_id.return_value = {
            "id": subscription_id,
            "alert": alert_id,
            "contact": user_id,
            "telegram": True,
            "email": True,
        }
        mock_repo.get_alerts_contacts_columns.return_value = [
            "telegram",
            "email",
        ]
        mock_repo.get_all_notification_statuses.return_value = [
            {"id": status_id, "status_name": "Status 1"}
        ]
        mock_repo.get_subscription_statuses.return_value = {status_id: 5}

        result = await service.get_subscription_users(alert_id)

        assert result.total == 1
        assert len(result.users) == 1
        assert result.users[0].user_id == user_id
        assert result.users[0].notification_channels is not None
        assert len(result.users[0].statuses) == 1
        assert result.users[0].statuses[0].repeat == 5

    async def test_get_subscription_users_with_status_without_repeat(
        self, service, mock_repo
    ):
        """Тест получения пользователей со статусом без repeat."""
        alert_id = uuid4()
        user_id = uuid4()
        subscription_id = uuid4()
        status_id = uuid4()

        mock_repo.check_alert_exists.return_value = True
        mock_repo.get_subscription_users.return_value = (
            [
                {
                    "id": user_id,
                    "user_name": "user1",
                    "group": False,
                    "is_subscribed": True,
                    "subscription_id": subscription_id,
                }
            ],
            1,
        )
        mock_repo.get_user_columns.return_value = ["id", "user_name", "group"]
        mock_repo.get_subscription_by_id.return_value = {
            "id": subscription_id,
            "alert": alert_id,
            "contact": user_id,
            "telegram": True,
        }
        mock_repo.get_alerts_contacts_columns.return_value = ["telegram"]
        mock_repo.get_all_notification_statuses.return_value = [
            {"id": status_id, "status_name": "Status 1"}
        ]
        mock_repo.get_subscription_statuses.return_value = {}  # Нет repeat

        result = await service.get_subscription_users(alert_id)

        assert result.total == 1
        assert len(result.users[0].statuses) == 1
        assert result.users[0].statuses[0].repeat is None

    async def test_get_subscription_users_without_subscription(
        self, service, mock_repo
    ):
        """Тест получения пользователей без подписки."""
        alert_id = uuid4()
        user_id = uuid4()

        mock_repo.check_alert_exists.return_value = True
        mock_repo.get_subscription_users.return_value = (
            [
                {
                    "id": user_id,
                    "user_name": "user1",
                    "group": False,
                    "is_subscribed": False,
                    "subscription_id": None,
                }
            ],
            1,
        )
        mock_repo.get_user_columns.return_value = ["id", "user_name", "group"]

        result = await service.get_subscription_users(alert_id)

        assert result.total == 1
        assert result.users[0].notification_channels is None
        assert (
            result.users[0].statuses is None
            or len(result.users[0].statuses) == 0
        )

    async def test_get_subscription_by_alert_and_user_subscription_not_found(
        self, service, mock_repo
    ):
        """Тест получения подписки когда subscription_row не найден."""
        alert_id = uuid4()
        user_id = uuid4()
        subscription_id = uuid4()
        mock_repo.check_subscription_exists.return_value = subscription_id
        mock_repo.get_subscription_by_id.return_value = (
            None  # Подписка не найдена
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.get_subscription_by_alert_and_user(alert_id, user_id)

        assert exc_info.value.status_code == 404
        assert "не найдена" in exc_info.value.detail

    async def test_get_subscription_by_alert_and_user_error_handling(
        self, service, mock_repo
    ):
        """Тест обработки ошибки при получении подписки."""
        alert_id = uuid4()
        user_id = uuid4()
        subscription_id = uuid4()
        mock_repo.check_subscription_exists.return_value = subscription_id
        mock_repo.get_subscription_by_id.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.get_subscription_by_alert_and_user(alert_id, user_id)

        assert exc_info.value.status_code == 500
        assert "Ошибка при получении подписки" in exc_info.value.detail

    async def test_update_subscription_by_alert_and_user_update_existing_status(
        self, service, mock_repo
    ):
        """Тест обновления подписки с обновлением существующего статуса."""
        alert_id = uuid4()
        user_id = uuid4()
        subscription_id = uuid4()
        status_id = uuid4()
        status_record_id = uuid4()

        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_subscription_exists.return_value = subscription_id
        mock_repo.get_alerts_contacts_columns.return_value = ["telegram"]
        mock_repo.update_subscription_channels.return_value = True
        mock_repo.get_current_subscription_statuses.return_value = {
            status_id: status_record_id
        }
        mock_repo.update_subscription_status.return_value = True

        from schemas.subscriptions import SubscriptionStatusUpdateItem

        data = SubscriptionByUserUpdate(
            alert_id=alert_id,
            user_id=user_id,
            notification_channels={"telegram": True},
            statuses=[
                SubscriptionStatusUpdateItem(
                    status_id=str(status_id), repeat=10
                )
            ],
        )

        result = await service.update_subscription_by_alert_and_user(data)

        assert result is True
        mock_repo.update_subscription_status.assert_called_once_with(
            status_record_id, 10, ANY
        )

    async def test_update_subscription_by_alert_and_user_delete_status(
        self, service, mock_repo
    ):
        """Тест обновления подписки с удалением статуса (repeat не передан)."""
        alert_id = uuid4()
        user_id = uuid4()
        subscription_id = uuid4()
        status_id = uuid4()
        status_record_id = uuid4()

        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_subscription_exists.return_value = subscription_id
        mock_repo.get_alerts_contacts_columns.return_value = ["telegram"]
        mock_repo.update_subscription_channels.return_value = True
        mock_repo.get_current_subscription_statuses.return_value = {
            status_id: status_record_id
        }
        mock_repo.delete_subscription_status.return_value = True

        from schemas.subscriptions import SubscriptionStatusUpdateItem

        data = SubscriptionByUserUpdate(
            alert_id=alert_id,
            user_id=user_id,
            statuses=[
                SubscriptionStatusUpdateItem(status_id=str(status_id))
            ],  # Без repeat
        )

        result = await service.update_subscription_by_alert_and_user(data)

        assert result is True
        mock_repo.delete_subscription_status.assert_called_once_with(
            status_record_id, ANY
        )

    async def test_update_subscription_by_alert_and_user_create_new_status(
        self, service, mock_repo
    ):
        """Тест обновления подписки с созданием нового статуса."""
        alert_id = uuid4()
        user_id = uuid4()
        subscription_id = uuid4()
        status_id = uuid4()

        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_subscription_exists.return_value = subscription_id
        mock_repo.get_alerts_contacts_columns.return_value = ["telegram"]
        mock_repo.update_subscription_channels.return_value = True
        mock_repo.get_current_subscription_statuses.return_value = {}  # Статуса нет
        mock_repo.create_subscription_status.return_value = True

        from schemas.subscriptions import SubscriptionStatusUpdateItem

        data = SubscriptionByUserUpdate(
            alert_id=alert_id,
            user_id=user_id,
            statuses=[
                SubscriptionStatusUpdateItem(
                    status_id=str(status_id), repeat=5
                )
            ],
        )

        result = await service.update_subscription_by_alert_and_user(data)

        assert result is True
        mock_repo.create_subscription_status.assert_called_once_with(
            subscription_id, status_id, 5, ANY
        )

    async def test_update_subscription_by_alert_and_user_subscription_not_found(
        self, service, mock_repo
    ):
        """Тест обновления подписки когда подписка не найдена."""
        alert_id = uuid4()
        user_id = uuid4()
        mock_repo.check_subscription_exists.return_value = None

        data = SubscriptionByUserUpdate(alert_id=alert_id, user_id=user_id)

        with pytest.raises(HTTPException) as exc_info:
            await service.update_subscription_by_alert_and_user(data)

        assert exc_info.value.status_code == 404
        assert "не найдена" in exc_info.value.detail

    async def test_update_subscription_by_alert_and_user_with_repeat_zero(
        self, service, mock_repo
    ):
        """Тест обновления подписки с repeat=0 (создание нового статуса)."""
        alert_id = uuid4()
        user_id = uuid4()
        subscription_id = uuid4()
        status_id = uuid4()

        mock_repo.check_alert_exists.return_value = True
        mock_repo.check_subscription_exists.return_value = subscription_id
        mock_repo.get_alerts_contacts_columns.return_value = ["telegram"]
        mock_repo.update_subscription_channels.return_value = True
        mock_repo.get_current_subscription_statuses.return_value = {}  # Статуса нет
        mock_repo.create_subscription_status.return_value = True

        from schemas.subscriptions import SubscriptionStatusUpdateItem

        data = SubscriptionByUserUpdate(
            alert_id=alert_id,
            user_id=user_id,
            statuses=[
                SubscriptionStatusUpdateItem(
                    status_id=str(status_id), repeat=0
                )
            ],
        )

        result = await service.update_subscription_by_alert_and_user(data)

        assert result is True
        mock_repo.create_subscription_status.assert_called_once_with(
            subscription_id, status_id, 0, ANY
        )

    async def test_get_alerts_by_user_success(self, service, mock_repo):
        """Тест успешного получения списка алертов по пользователю (с notification_channels и statuses)."""
        user_id = uuid4()
        sub_id = uuid4()
        status_id = uuid4()
        mock_repo.check_user_exists.return_value = True
        mock_repo.get_alerts_contacts_columns.return_value = [
            "telegram",
            "email",
            "pachca",
        ]
        mock_repo.get_alerts_by_user.return_value = (
            [
                {
                    "alert_id": uuid4(),
                    "alert_name": "Test Alert",
                    "subscription_id": sub_id,
                    "telegram": True,
                    "email": False,
                    "pachca": True,
                }
            ],
            1,
        )
        mock_repo.get_all_notification_statuses.return_value = [
            {"id": status_id, "status_name": "Status 1"},
        ]
        mock_repo.get_subscription_statuses.return_value = {status_id: 3}

        result = await service.get_alerts_by_user(user_id)

        assert isinstance(result, AlertByUserListResponse)
        assert result.total == 1
        assert len(result.alerts) == 1
        assert result.alerts[0].alert_name == "Test Alert"
        assert result.alerts[0].notification_channels is not None
        assert result.alerts[0].notification_channels.telegram is True
        assert result.alerts[0].notification_channels.email is False
        assert result.alerts[0].statuses is not None
        assert len(result.alerts[0].statuses) == 1
        assert result.alerts[0].statuses[0].status_name == "Status 1"
        assert result.alerts[0].statuses[0].repeat == 3

    async def test_get_alerts_by_user_user_not_found(self, service, mock_repo):
        """Тест получения списка алертов, когда пользователь не найден."""
        user_id = uuid4()
        mock_repo.check_user_exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await service.get_alerts_by_user(user_id)

        assert exc_info.value.status_code == 404

    async def test_get_alerts_by_user_unsubscribed_alert_has_no_notification_channels(
        self, service, mock_repo
    ):
        """Тест: у неподписанного алерта notification_channels = None."""
        user_id = uuid4()
        mock_repo.check_user_exists.return_value = True
        mock_repo.get_alerts_contacts_columns.return_value = [
            "telegram",
            "email",
        ]
        mock_repo.get_alerts_by_user.return_value = (
            [
                {
                    "alert_id": uuid4(),
                    "alert_name": "Unsubscribed Alert",
                    "subscription_id": None,
                }
            ],
            1,
        )

        result = await service.get_alerts_by_user(user_id)

        assert result.total == 1
        assert result.alerts[0].alert_name == "Unsubscribed Alert"
        assert result.alerts[0].notification_channels is None
        # Для неподписанного алерта statuses в ответе отсутствует/None
        assert result.alerts[0].statuses is None

    async def test_get_alerts_by_user_error_handling(self, service, mock_repo):
        """Тест обработки ошибки при получении списка алертов по пользователю."""
        user_id = uuid4()
        mock_repo.check_user_exists.return_value = True
        mock_repo.get_alerts_by_user.side_effect = Exception("Ошибка БД")

        with pytest.raises(HTTPException) as exc_info:
            await service.get_alerts_by_user(user_id)

        assert exc_info.value.status_code == 500
        assert (
            "Ошибка при получении списка алертов по пользователю"
            in exc_info.value.detail
        )

    async def test_get_alerts_by_user_subscribed_only_passed_to_repo(
        self, service, mock_repo
    ):
        """Тест: subscribed_only передается в репозиторий."""
        user_id = uuid4()
        mock_repo.check_user_exists.return_value = True
        mock_repo.get_alerts_contacts_columns.return_value = []
        mock_repo.get_alerts_by_user.return_value = ([], 0)

        result = await service.get_alerts_by_user(
            user_id, subscribed_only=True
        )

        assert isinstance(result, AlertByUserListResponse)
        mock_repo.get_alerts_by_user.assert_awaited_once()
        _, kwargs = mock_repo.get_alerts_by_user.await_args
        assert kwargs["user_id"] == user_id
        assert kwargs["subscribed_only"] is True

    async def test_build_contacts_dict_for_subscribe_with_dict_row(
        self, service
    ):
        """Ветка: user_row уже dict."""
        result = service._build_contacts_dict_for_subscribe(
            alerts_contacts_columns=["telegram", "email"],
            user_column_names=["id", "telegram", "email_id"],
            user_row={"telegram": "abc", "email_id": "x"},
        )
        assert result == {"telegram": True, "email": True}

    async def test_apply_subscription_contact_columns_skips_empty_updates(
        self, service, mock_repo
    ):
        """Ветка: если валидных полей нет, update не вызывается."""
        subscription_id = uuid4()
        mock_repo.get_alerts_contacts_columns.return_value = ["telegram"]
        channels = SubscriptionContacts(email=True)
        await service._apply_subscription_contact_columns(
            None, subscription_id, channels
        )
        mock_repo.update_subscription_channels.assert_not_called()

    async def test_resolve_notification_status_id_by_name(
        self, service, mock_repo
    ):
        """Ветка: status_id строка-имя из справочника."""
        status_id = uuid4()
        mock_repo.get_all_notification_statuses.return_value = [
            {"id": status_id, "status_name": "CREATED"}
        ]
        resolved = await service._resolve_notification_status_id(None, "CREATED")
        assert resolved == status_id

    async def test_resolve_notification_status_id_not_found(
        self, service, mock_repo
    ):
        """Ветка: статус не найден -> HTTP 400."""
        mock_repo.get_all_notification_statuses.return_value = []
        with pytest.raises(HTTPException) as exc_info:
            await service._resolve_notification_status_id(None, "UNKNOWN")
        assert exc_info.value.status_code == 400

    async def test_get_subscription_by_alert_and_user_with_dict_row(
        self, service, mock_repo
    ):
        """Ветка: subscription_row как dict."""
        alert_id = uuid4()
        user_id = uuid4()
        subscription_id = uuid4()
        status_id = uuid4()
        mock_repo.check_subscription_exists.return_value = subscription_id
        mock_repo.get_subscription_by_id.return_value = {
            "id": subscription_id,
            "alert": alert_id,
            "contact": user_id,
            "telegram": True,
            "email": None,
        }
        mock_repo.get_alerts_contacts_columns.return_value = [
            "telegram",
            "email",
        ]
        mock_repo.get_all_notification_statuses.return_value = [
            {"id": status_id, "status_name": "S1"}
        ]
        mock_repo.get_subscription_statuses.return_value = {}

        result = await service.get_subscription_by_alert_and_user(
            alert_id, user_id
        )
        assert result.notification_channels is not None
        assert result.notification_channels.telegram is True

    async def test_get_subscription_users_with_dict_rows(
        self, service, mock_repo
    ):
        """Ветка: пользователи приходят dict-строками."""
        alert_id = uuid4()
        uid = uuid4()
        sub_id = uuid4()
        st_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.get_subscription_users.return_value = (
            [
                {
                    "id": uid,
                    "user_name": "u1",
                    "group": False,
                    "is_subscribed": True,
                    "subscription_id": sub_id,
                    "telegram": True,
                }
            ],
            1,
        )
        mock_repo.get_user_columns.return_value = ["id", "user_name", "group"]
        mock_repo.get_subscription_by_id.return_value = {
            "id": sub_id,
            "alert": alert_id,
            "contact": uid,
            "telegram": True,
        }
        mock_repo.get_alerts_contacts_columns.return_value = ["telegram"]
        mock_repo.get_all_notification_statuses.return_value = [
            {"id": st_id, "status_name": "S1"}
        ]
        mock_repo.get_subscription_statuses.return_value = {}

        result = await service.get_subscription_users(alert_id)
        assert result.total == 1
        assert result.users[0].notification_channels is not None

    async def test_get_alerts_by_user_skips_invalid_non_dict_rows(
        self, service, mock_repo
    ):
        """Ветка: не-dict row, где keys() падает -> row пропускается."""
        user_id = uuid4()

        class BadRow:
            def keys(self):
                raise RuntimeError("bad keys")

        mock_repo.check_user_exists.return_value = True
        mock_repo.get_alerts_contacts_columns.return_value = []
        mock_repo.get_alerts_by_user.return_value = ([BadRow()], 1)

        result = await service.get_alerts_by_user(user_id)
        assert result.total == 1
        assert result.alerts == []

    async def test_get_alerts_by_user_status_without_repeat(
        self, service, mock_repo
    ):
        """Ветка: статус без repeat попадает в ответ с repeat=None."""
        user_id = uuid4()
        sub_id = uuid4()
        st_id = uuid4()
        mock_repo.check_user_exists.return_value = True
        mock_repo.get_alerts_contacts_columns.return_value = ["telegram"]
        mock_repo.get_alerts_by_user.return_value = (
            [
                {
                    "alert_id": uuid4(),
                    "alert_name": "A",
                    "subscription_id": sub_id,
                    "telegram": True,
                }
            ],
            1,
        )
        mock_repo.get_all_notification_statuses.return_value = [
            {"id": st_id, "status_name": "S1"}
        ]
        mock_repo.get_subscription_statuses.return_value = {}

        result = await service.get_alerts_by_user(user_id)
        assert result.alerts[0].statuses is not None
        assert result.alerts[0].statuses[0].repeat is None

    async def test_get_alerts_by_user_with_non_dict_row_keys(
        self, service, mock_repo
    ):
        """Ветка: non-dict row со своими keys()/indexing успешно конвертируется."""
        user_id = uuid4()

        class SeqRow:
            _keys: ClassVar[list[str]] = [
                "alert_id",
                "alert_name",
                "subscription_id",
                "telegram",
            ]
            _vals: ClassVar[list[object]] = [uuid4(), "Alert X", None, True]

            def keys(self):
                return self._keys

            def __getitem__(self, idx):
                return self._vals[idx]

        mock_repo.check_user_exists.return_value = True
        mock_repo.get_alerts_contacts_columns.return_value = ["telegram"]
        mock_repo.get_alerts_by_user.return_value = ([SeqRow()], 1)

        result = await service.get_alerts_by_user(user_id)
        assert result.total == 1
        assert len(result.alerts) == 1
        assert result.alerts[0].alert_name == "Alert X"

    async def test_as_dict_with_mapping(self, service):
        """Покрыть ветку _as_dict: _mapping."""

        class RowObj:
            _mapping: ClassVar[dict[str, object]] = {
                "id": 1,
                "status_name": "S",
            }

        result = service._as_dict(RowObj())
        assert result["status_name"] == "S"

    async def test_as_dict_with_keys(self, service):
        """Покрыть ветку _as_dict: keys()/index."""

        class RowObj:
            def keys(self):
                return ["id", "status_name"]

            def __getitem__(self, idx):
                return [2, "K"][idx]

        result = service._as_dict(RowObj())
        assert result["status_name"] == "K"

    async def test_as_dict_plain_object_returns_empty(self, service):
        """Покрыть финальную ветку _as_dict -> {}."""
        assert service._as_dict(object()) == {}

    async def test_as_dict_keys_index_error_returns_empty(self, service):
        """Покрыть except внутри _as_dict."""

        class BadRow:
            def keys(self):
                return ["id"]

            def __getitem__(self, idx):
                raise IndexError("out")

        assert service._as_dict(BadRow()) == {}

    async def test_get_subscription_users_short_tuple_row(
        self, service, mock_repo
    ):
        """Intentional legacy edge: tuple-row для проверки IndexError fallback при парсинге contacts."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True
        mock_repo.get_subscription_users.return_value = (
            [
                (uuid4(), "u1", False)
            ],  # intentional legacy tuple: короткая строка без контактов
            1,
        )
        mock_repo.get_user_columns.return_value = [
            "id",
            "user_name",
            "group",
            "email",
        ]
        result = await service.get_subscription_users(alert_id)
        assert result.total == 1

    async def test_get_subscription_users_contacts_index_error_branch(
        self, service, mock_repo
    ):
        """Intentional legacy edge: покрыть except (ValueError, IndexError) при чтении contacts."""
        alert_id = uuid4()
        mock_repo.check_alert_exists.return_value = True

        class WeirdRow:
            def __len__(self):
                return 10

            def __getitem__(self, idx):
                if idx >= 3:
                    raise IndexError("out")
                return [uuid4(), "u", False][idx]

        mock_repo.get_subscription_users.return_value = ([WeirdRow()], 1)
        mock_repo.get_user_columns.return_value = [
            "id",
            "user_name",
            "group",
            "email",
        ]

        with pytest.raises(HTTPException) as exc_info:
            await service.get_subscription_users(alert_id)
        assert exc_info.value.status_code == 500
