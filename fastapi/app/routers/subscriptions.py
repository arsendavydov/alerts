from typing import Literal
from uuid import UUID

from contracts.service_protocols import SubscriptionsServiceProtocol
from dependencies import get_subscriptions_service

from fastapi import APIRouter, Body, Depends, Path, Query
from schemas.subscriptions import (
    AlertByUserListResponse,
    SubscribeRequest,
    SubscriptionByUserResponse,
    SubscriptionByUserUpdate,
    SubscriptionByUserUpdateRequest,
    SubscriptionUserListResponse,
    UnsubscribeRequest,
)

router = APIRouter(prefix="/alerts/api/v1", tags=["subscriptions"])


# Внутренняя функция для подписки (используется новыми методами)
async def subscribe(
    data: SubscribeRequest,
    service: SubscriptionsServiceProtocol = Depends(get_subscriptions_service),
) -> bool:
    """
    Подписка пользователя на алерт.

    Создает запись в alerts.alerts_contacts с полями из объекта contacts.
    Если подписка уже существует, возвращает ошибку 409.

    Args:
        data: Данные для подписки (alert_id, user_id, contacts)
        service: Сервис для работы с подписками

    Returns:
        bool: true при успешной подписке

    Raises:
        HTTPException: При ошибке валидации, отсутствии алерта/пользователя, или если подписка уже существует
    """
    return await service.subscribe(data)


# Внутренняя функция для отписки (используется новыми методами)
async def unsubscribe(
    data: UnsubscribeRequest,
    service: SubscriptionsServiceProtocol = Depends(get_subscriptions_service),
) -> bool:
    """
    Отписка пользователя от алерта.

    Удаляет запись из alerts.alerts_contacts и все связанные записи из alerts.alerts_contacts_status.

    Args:
        data: Данные для отписки (alert_id, user_id)
        service: Сервис для работы с подписками

    Returns:
        bool: true при успешной отписке

    Raises:
        HTTPException: При отсутствии подписки или ошибке БД
    """
    return await service.unsubscribe(data)


# Внутренняя функция для получения подписки (используется новыми методами, если нужно)
async def get_subscription_by_alert_and_user(
    alert_id: UUID,
    user_id: UUID,
    service: SubscriptionsServiceProtocol = Depends(get_subscriptions_service),
) -> SubscriptionByUserResponse:
    """
    Получение детальной информации о подписке пользователя на алерт.

    Возвращает:
    - subscription_id: ID подписки
    - notification_channels: Динамические поля из alerts.alerts_contacts (кроме id, alert, contact) - булевы флаги каналов доставки
    - statuses: Все статусы с send_notification=true. Если статус есть в alerts_contacts_status - возвращает repeat, если нет - None

    Args:
        alert_id: ID алерта
        user_id: ID пользователя
        service: Сервис для работы с подписками

    Returns:
        SubscriptionByUserResponse: Детальная информация о подписке

    Raises:
        HTTPException: При отсутствии подписки или ошибке БД
    """
    return await service.get_subscription_by_alert_and_user(alert_id, user_id)


# Внутренняя функция для обновления подписки (используется новыми методами)
async def update_subscription_by_alert_and_user(
    data: SubscriptionByUserUpdate,
    service: SubscriptionsServiceProtocol = Depends(get_subscriptions_service),
) -> bool:
    """
    Обновление подписки пользователя на алерт.

    Обновляет:
    - notification_channels: Динамические поля из alerts.alerts_contacts (булевы флаги каналов доставки)
    - statuses: Статусы из alerts.alerts_contacts_status
      - Если статус приходит с repeat (включая 0) - обновить или создать
      - Если статус приходит без repeat (поле отсутствует) - удалить, если был

    Args:
        data: Данные для обновления (alert_id, user_id, notification_channels, statuses)
        service: Сервис для работы с подписками

    Returns:
        bool: true при успешном обновлении

    Raises:
        HTTPException: При отсутствии подписки или ошибке БД
    """
    return await service.update_subscription_by_alert_and_user(data)


# Внутренняя функция для получения списка пользователей (используется новыми методами)
async def get_subscription_users(
    alert_id: UUID,
    query: str | None = None,
    limit: int = 50,
    offset: int = 0,
    order_by: str = "samAccountName",
    order_dir: str = "asc",
    subscribed_only: bool = False,
    groups: bool | None = None,
    service: SubscriptionsServiceProtocol = Depends(get_subscriptions_service),
) -> SubscriptionUserListResponse:
    """
    Получение списка всех пользователей для страницы подписок алерта.

    - Все пользователи сортируются по выбранному полю (по умолчанию samAccountName ASC)
    - Поддерживает поиск по имени пользователя (регистронезависимо, частичное совпадение)
    - Поддерживает фильтрацию только подписанных пользователей
    - Наличие подписки определяется по наличию полей notification_channels и statuses

    Args:
        alert_id: ID алерта
        query: Поисковый запрос по samAccountName или email (опционально)
        limit: Количество записей на странице
        offset: Смещение для пагинации
        order_by: Поле для сортировки (user_id, samAccountName, email)
        order_dir: Направление сортировки (asc/desc)
        subscribed_only: Показывать только пользователей с подпиской
        groups: Фильтр по полю group (True - группы, False - обычные пользователи)
        service: Сервис для работы с подписками

    Returns:
        SubscriptionUserListResponse: Список пользователей с информацией о подписке
    """
    return await service.get_subscription_users(
        alert_id=alert_id,
        query=query,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir,
        subscribed_only=subscribed_only,
        groups=groups,
    )


@router.get(
    "/alerts/{alert_id}/subscriptions/search",
    response_model=SubscriptionUserListResponse,
    summary="Получить список пользователей для страницы подписок алерта",
    description="Возвращает всех пользователей с информацией о подписке на указанный алерт. Все пользователи сортируются по выбранному полю (по умолчанию samAccountName ASC). Поддерживает поиск по имени пользователя и фильтрацию только подписанных пользователей. Наличие подписки определяется по наличию полей notification_channels и statuses.",
    response_model_exclude_none=True,
)
async def get_subscription_users_by_alert(
    alert_id: UUID = Path(..., description="ID алерта"),
    query: str | None = Query(
        None,
        min_length=1,
        description="Поиск по samAccountName или email (регистронезависимо, частичное совпадение)",
    ),
    limit: int = Query(
        50, ge=1, le=100, description="Сколько пользователей вернуть"
    ),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    order_by: Literal["user_id", "samAccountName", "email"] = Query(
        "samAccountName", description="Поле сортировки"
    ),
    order_dir: Literal["asc", "desc"] = Query(
        "asc", description="Направление сортировки"
    ),
    subscribed_only: bool = Query(
        False, description="Показывать только пользователей с подпиской"
    ),
    groups: bool | None = Query(
        None,
        description="Фильтр по группам: true - только группы, false - только обычные пользователи",
    ),
    service: SubscriptionsServiceProtocol = Depends(get_subscriptions_service),
) -> SubscriptionUserListResponse:
    """Получение списка пользователей с новым форматом пути."""
    return await service.get_subscription_users(
        alert_id=alert_id,
        query=query,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir,
        subscribed_only=subscribed_only,
        groups=groups,
    )


@router.get(
    "/users/{user_id}/subscriptions/search",
    response_model=AlertByUserListResponse,
    summary="Получить список алертов для страницы подписок пользователя",
    description=(
        "Возвращает список алертов с пагинацией (все алерты, сортировка по имени или дате). "
        "У подписанных - notification_channels и statuses; у неподписанных - оба поля null."
    ),
    response_model_exclude_none=True,
)
async def get_alerts_by_user(
    user_id: UUID = Path(..., description="ID пользователя"),
    limit: int = Query(
        50, ge=1, le=100, description="Сколько алертов вернуть"
    ),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    order_by: Literal["alert_name", "created_at"] = Query(
        "alert_name",
        description="Поле сортировки: по имени алерта или по дате создания подписки (приближенно)",
    ),
    order_dir: Literal["asc", "desc"] = Query(
        "asc",
        description="Направление сортировки",
    ),
    subscribed_only: bool = Query(
        False,
        description="Показывать только алерты, на которые пользователь подписан",
    ),
    service: SubscriptionsServiceProtocol = Depends(get_subscriptions_service),
) -> AlertByUserListResponse:
    return await service.get_alerts_by_user(
        user_id=user_id,
        order_by=order_by,
        order_dir=order_dir,
        limit=limit,
        offset=offset,
        subscribed_only=subscribed_only,
    )


@router.patch(
    "/alerts/{alert_id}/subscriptions/users/{user_id}",
    summary="Обновить подписку пользователя на алерт",
    description="Обновляет динамические поля notification_channels (булевы флаги каналов доставки) и статусы. Если статус приходит без repeat - удаляется, если был. Если с repeat (включая 0) - обновляется/создается. alert_id и user_id берутся из пути, их не нужно передавать в теле запроса.",
    response_model_exclude_none=True,
)
async def update_subscription_by_alert_and_user_new(
    alert_id: UUID = Path(..., description="ID алерта"),
    user_id: UUID = Path(..., description="ID пользователя"),
    data: SubscriptionByUserUpdateRequest = Body(
        ..., description="Данные для обновления подписки"
    ),
    service: SubscriptionsServiceProtocol = Depends(get_subscriptions_service),
) -> bool:
    """Обновление подписки с новым форматом пути."""
    # Создаем объект SubscriptionByUserUpdate с данными из пути и тела запроса
    update_data = SubscriptionByUserUpdate(
        alert_id=alert_id,
        user_id=user_id,
        notification_channels=data.notification_channels,
        statuses=data.statuses,
    )
    return await service.update_subscription_by_alert_and_user(update_data)


@router.post(
    "/alerts/{alert_id}/subscriptions/users/{user_id}",
    summary="Подписать пользователя на алерт",
    description="Подписывает пользователя на алерт. alert_id и user_id берутся из пути. Контакты автоматически берутся из alerts.contacts для этого пользователя. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def subscribe_by_alert_and_user(
    alert_id: UUID = Path(..., description="ID алерта"),
    user_id: UUID = Path(..., description="ID пользователя"),
    service: SubscriptionsServiceProtocol = Depends(get_subscriptions_service),
) -> bool:
    """Подписка пользователя на алерт с новым форматом пути."""
    subscribe_data = SubscribeRequest(alert_id=alert_id, user_id=user_id)
    return await service.subscribe(subscribe_data)


@router.delete(
    "/alerts/{alert_id}/subscriptions/users/{user_id}",
    summary="Отписать пользователя от алерта",
    description="Отписывает пользователя от алерта. Удаляет подписку и все связанные статусы. alert_id и user_id берутся из пути. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def unsubscribe_by_alert_and_user(
    alert_id: UUID = Path(..., description="ID алерта"),
    user_id: UUID = Path(..., description="ID пользователя"),
    service: SubscriptionsServiceProtocol = Depends(get_subscriptions_service),
) -> bool:
    """Отписка пользователя от алерта с новым форматом пути."""
    unsubscribe_data = UnsubscribeRequest(alert_id=alert_id, user_id=user_id)
    return await service.unsubscribe(unsubscribe_data)
