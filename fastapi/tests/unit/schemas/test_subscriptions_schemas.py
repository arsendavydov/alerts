"""
Модульные тесты для валидации схем Subscriptions.
"""

import sys
from pathlib import Path
from uuid import uuid4

# Добавляем путь к app для импортов
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "app"))
from schemas.subscriptions import (
    AlertByUserItem,
    AlertByUserListResponse,
    SubscribeRequest,
    SubscriptionByUserResponse,
    SubscriptionByUserUpdate,
    SubscriptionByUserUpdateRequest,
    SubscriptionContacts,
    SubscriptionStatusItem,
    SubscriptionStatusUpdateItem,
    SubscriptionUserItem,
    SubscriptionUserListResponse,
    UnsubscribeRequest,
)


class TestSubscriptionContacts:
    """Тесты для SubscriptionContacts."""

    def test_valid_contacts(self):
        """Тест валидных контактов."""
        data = SubscriptionContacts()
        # extra='allow' позволяет добавлять любые поля
        assert data.model_config.get("extra") == "allow"

    def test_with_channels(self):
        """Тест с каналами уведомлений."""
        data = SubscriptionContacts(telegram=True, email=False)
        # Проверяем что поля доступны
        assert hasattr(data, "telegram") or "telegram" in data.model_dump()


class TestSubscribeRequest:
    """Тесты для SubscribeRequest."""

    def test_valid_request(self):
        """Тест валидного запроса."""
        alert_id = uuid4()
        user_id = uuid4()
        data = SubscribeRequest(alert_id=alert_id, user_id=user_id)
        assert data.alert_id == alert_id
        assert data.user_id == user_id


class TestUnsubscribeRequest:
    """Тесты для UnsubscribeRequest."""

    def test_valid_request(self):
        """Тест валидного запроса."""
        alert_id = uuid4()
        user_id = uuid4()
        data = UnsubscribeRequest(alert_id=alert_id, user_id=user_id)
        assert data.alert_id == alert_id
        assert data.user_id == user_id


class TestSubscriptionStatusItem:
    """Тесты для SubscriptionStatusItem."""

    def test_valid_item(self):
        """Тест валидного элемента."""
        data = SubscriptionStatusItem(status_id="1", status_name="Test Status")
        assert data.status_id == "1"
        assert data.status_name == "Test Status"
        assert data.repeat is None

    def test_with_repeat(self):
        """Тест с repeat."""
        data = SubscriptionStatusItem(
            status_id="1", status_name="Test Status", repeat=5
        )
        assert data.repeat == 5


class TestSubscriptionUserItem:
    """Тесты для SubscriptionUserItem."""

    def test_valid_item(self):
        """Тест валидного элемента."""
        user_id = uuid4()
        data = SubscriptionUserItem(
            user_id=user_id, samAccountName="test_user", group=False
        )
        assert data.user_id == user_id
        assert data.samAccountName == "test_user"
        assert data.group is False
        # По умолчанию нет статусов
        assert data.statuses is None

    def test_with_subscription_info(self):
        """Тест с информацией о подписке."""
        user_id = uuid4()
        contacts = SubscriptionContacts(telegram=True)
        status = SubscriptionStatusItem(
            status_id="1", status_name="Test Status"
        )
        data = SubscriptionUserItem(
            user_id=user_id,
            samAccountName="test_user",
            group=False,
            notification_channels=contacts,
            statuses=[status],
        )
        assert data.notification_channels is not None
        assert len(data.statuses) == 1


class TestSubscriptionUserListResponse:
    """Тесты для SubscriptionUserListResponse."""

    def test_valid_response(self):
        """Тест валидного ответа."""
        user_id = uuid4()
        item = SubscriptionUserItem(
            user_id=user_id, samAccountName="test_user", group=False
        )
        data = SubscriptionUserListResponse(users=[item], total=1)
        assert len(data.users) == 1
        assert data.total == 1


class TestSubscriptionByUserResponse:
    """Тесты для SubscriptionByUserResponse."""

    def test_valid_response(self):
        """Тест валидного ответа."""
        subscription_id = uuid4()
        status = SubscriptionStatusItem(
            status_id="1", status_name="Test Status"
        )
        data = SubscriptionByUserResponse(
            subscription_id=subscription_id, statuses=[status]
        )
        assert data.subscription_id == subscription_id
        assert len(data.statuses) == 1

    def test_with_notification_channels(self):
        """Тест с каналами уведомлений."""
        subscription_id = uuid4()
        contacts = SubscriptionContacts(telegram=True)
        data = SubscriptionByUserResponse(
            subscription_id=subscription_id,
            notification_channels=contacts,
            statuses=[],
        )
        assert data.notification_channels is not None


class TestSubscriptionStatusUpdateItem:
    """Тесты для SubscriptionStatusUpdateItem."""

    def test_valid_item(self):
        """Тест валидного элемента."""
        data = SubscriptionStatusUpdateItem(status_id="1")
        assert data.status_id == "1"
        assert data.repeat is None

    def test_with_repeat(self):
        """Тест с repeat."""
        data = SubscriptionStatusUpdateItem(status_id="1", repeat=5)
        assert data.repeat == 5

    def test_with_repeat_zero(self):
        """Тест с repeat=0 (тоже валидно)."""
        data = SubscriptionStatusUpdateItem(status_id="1", repeat=0)
        assert data.repeat == 0


class TestSubscriptionByUserUpdate:
    """Тесты для SubscriptionByUserUpdate."""

    def test_valid_update(self):
        """Тест валидного обновления."""
        alert_id = uuid4()
        user_id = uuid4()
        data = SubscriptionByUserUpdate(alert_id=alert_id, user_id=user_id)
        assert data.alert_id == alert_id
        assert data.user_id == user_id

    def test_with_notification_channels(self):
        """Тест с каналами уведомлений."""
        alert_id = uuid4()
        user_id = uuid4()
        contacts = SubscriptionContacts(telegram=True)
        data = SubscriptionByUserUpdate(
            alert_id=alert_id, user_id=user_id, notification_channels=contacts
        )
        assert data.notification_channels is not None


class TestSubscriptionByUserUpdateRequest:
    """Тесты для SubscriptionByUserUpdateRequest."""

    def test_all_fields_optional(self):
        """Тест что все поля опциональны."""
        data = SubscriptionByUserUpdateRequest()
        assert data.notification_channels is None
        assert data.statuses is None

    def test_with_fields(self):
        """Тест с полями."""
        contacts = SubscriptionContacts(telegram=True)
        status = SubscriptionStatusUpdateItem(status_id="1")
        data = SubscriptionByUserUpdateRequest(
            notification_channels=contacts, statuses=[status]
        )
        assert data.notification_channels is not None
        assert len(data.statuses) == 1


class TestAlertByUserSchemas:
    """Тесты для схем алертов по пользователю."""

    def test_alert_by_user_item_minimal(self):
        """Тест минимального элемента AlertByUserItem."""
        alert_id = uuid4()
        item = AlertByUserItem(
            alert_id=alert_id,
            alert_name="Test Alert",
        )
        assert item.alert_id == alert_id
        assert item.alert_name == "Test Alert"
        assert item.statuses is None
        assert item.notification_channels is None

    def test_alert_by_user_list_response(self):
        """Тест ответа AlertByUserListResponse."""
        alert_id = uuid4()
        item = AlertByUserItem(
            alert_id=alert_id,
            alert_name="Test Alert",
            notification_channels=SubscriptionContacts(telegram=True),
            statuses=[
                SubscriptionStatusItem(
                    status_id="1", status_name="Status 1", repeat=5
                ),
            ],
        )
        resp = AlertByUserListResponse(alerts=[item], total=1)
        assert resp.total == 1
        assert len(resp.alerts) == 1
        assert resp.alerts[0].alert_name == "Test Alert"
        assert resp.alerts[0].statuses is not None
        assert len(resp.alerts[0].statuses) == 1
        assert resp.alerts[0].statuses[0].repeat == 5
