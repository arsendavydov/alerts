from typing import TYPE_CHECKING, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from schemas.users import UserContacts
else:
    from schemas.users import UserContacts  # noqa: TC001 - для model_rebuild()


class SubscriptionContacts(BaseModel):
    """Контактная информация для подписки (динамические поля из alerts.alerts_contacts, кроме id, alert, contact)."""

    model_config = ConfigDict(exclude_none=True, extra="allow")
    # Все поля из alerts.alerts_contacts (кроме id, alert, contact) попадают сюда динамически
    telegram: bool | None = None
    email: bool | None = None


class SubscribeRequest(BaseModel):
    """Запрос на подписку пользователя на алерт."""

    model_config = ConfigDict(exclude_none=True)

    alert_id: UUID
    user_id: UUID
    # contacts автоматически берутся из alerts.contacts для этого пользователя


class UnsubscribeRequest(BaseModel):
    """Запрос на отписку пользователя от алерта."""

    model_config = ConfigDict(exclude_none=True)

    alert_id: UUID
    user_id: UUID


class SubscriptionUserItem(BaseModel):
    """Элемент списка пользователей для страницы подписок алерта."""

    model_config = ConfigDict(exclude_none=True)

    user_id: UUID
    samAccountName: str  # В БД хранится как user_name
    group: bool
    contacts: Optional["UserContacts"] = (
        None  # Динамические поля из alerts.contacts (кроме id, user_name, group) для всех пользователей
    )
    notification_channels: SubscriptionContacts | None = (
        None  # Динамические поля из alerts.alerts_contacts (кроме id, alert, contact) только для подписанных пользователей. Наличие этого поля означает, что пользователь подписан.
    )
    statuses: list["SubscriptionStatusItem"] | None = (
        None  # Статусы с send_notification=true; отсутствует/None, если пользователь не подписан или статусов нет.
    )


class SubscriptionUserListResponse(BaseModel):
    """Ответ со списком пользователей для страницы подписок алерта."""

    model_config = ConfigDict(exclude_none=True)

    users: list[SubscriptionUserItem]
    total: int


class SubscriptionStatusItem(BaseModel):
    """Элемент статуса в подписке."""

    model_config = ConfigDict(exclude_none=True)

    status_id: str
    status_name: str
    repeat: int | None = None  # None если статуса нет в alerts_contacts_status


class SubscriptionByUserResponse(BaseModel):
    """Ответ с детальной информацией о подписке пользователя на алерт."""

    model_config = ConfigDict(exclude_none=True)

    subscription_id: UUID
    notification_channels: SubscriptionContacts | None = (
        None  # Динамические поля из alerts.alerts_contacts (булевы флаги каналов доставки)
    )
    statuses: list[
        SubscriptionStatusItem
    ]  # Все статусы с send_notification, если нет в alerts_contacts_status - repeat=None


class AlertByUserItem(BaseModel):
    """Элемент списка алертов для пользователя."""

    model_config = ConfigDict(exclude_none=True)

    alert_id: UUID
    alert_name: str
    notification_channels: SubscriptionContacts | None = None
    statuses: list[SubscriptionStatusItem] | None = (
        None  # Статусы с send_notification; отсутствует/None, если пользователь не подписан.
    )


class AlertByUserListResponse(BaseModel):
    """Ответ со списком алертов, на которые подписан пользователь."""

    model_config = ConfigDict(exclude_none=True)

    alerts: list[AlertByUserItem]
    total: int


class SubscriptionStatusUpdateItem(BaseModel):
    """Элемент статуса для обновления подписки."""

    model_config = ConfigDict(exclude_none=True)

    status_id: str
    repeat: int | None = (
        None  # Если None или отсутствует - удалить статус, если был. Если указан (включая 0) - обновить/создать
    )


class SubscriptionByUserUpdate(BaseModel):
    """Запрос на обновление подписки пользователя на алерт."""

    model_config = ConfigDict(exclude_none=True)

    alert_id: UUID
    user_id: UUID
    notification_channels: SubscriptionContacts | None = (
        None  # Динамические поля из alerts.alerts_contacts для обновления (булевы флаги каналов доставки)
    )
    statuses: list[SubscriptionStatusUpdateItem] | None = (
        None  # Список статусов для обновления
    )


class SubscriptionByUserUpdateRequest(BaseModel):
    """Тело запроса для обновления подписки пользователя на алерт (без alert_id и user_id, они берутся из пути)."""

    model_config = ConfigDict(exclude_none=True)

    notification_channels: SubscriptionContacts | None = (
        None  # Динамические поля из alerts.alerts_contacts для обновления (булевы флаги каналов доставки)
    )
    statuses: list[SubscriptionStatusUpdateItem] | None = (
        None  # Список статусов для обновления
    )


# Разрешаем forward references для UserContacts и SubscriptionStatusItem
if not TYPE_CHECKING:
    SubscriptionUserItem.model_rebuild()
