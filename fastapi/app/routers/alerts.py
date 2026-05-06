from typing import Literal
from uuid import UUID

from contracts.service_protocols import (
    AlertsServiceProtocol,
    PausesServiceProtocol,
)
from dependencies import get_alerts_service, get_pauses_service
from fastapi import APIRouter, Body, Depends, Path, Query

from schemas.alerts import (
    AlertAutocompleteResponse,
    AlertDetail,
    AlertDetailCreate,
    AlertDetailUpdate,
    AlertListResponse,
    TagCloudResponse,
)
from schemas.pauses import AlertPauseRequest

router = APIRouter(prefix="/alerts/api/v1/alerts", tags=["alerts"])
duplicate_router = APIRouter(prefix="/alerts/api/v1", tags=["alerts"])


@router.get(
    "/search",
    response_model=AlertListResponse,
    summary="Поиск алертов",
    description="Поиск, фильтрация и пагинация алертов с JOIN на связанные таблицы. Поддерживает поиск по alert_name и фильтр по тегам.",
    response_model_exclude_none=True,
)
async def get_alerts_search(
    query: str | None = Query(
        None, min_length=1, description="Поиск по alert_name"
    ),
    tags: str | None = Query(None, description="Теги через запятую"),
    limit: int = Query(
        50, ge=1, le=100, description="Сколько алертов вернуть"
    ),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    order_by: Literal[
        "alert_name",
        "indicator_name",
        "alert_description",
        "indicator_description",
        "status_id",
        "paused",
    ] = Query("alert_name", description="Поле сортировки"),
    order_dir: Literal["asc", "desc"] = Query(
        "asc", description="Направление сортировки"
    ),
    service: AlertsServiceProtocol = Depends(get_alerts_service),
) -> AlertListResponse:
    """
    Поиск и фильтрация алертов с пагинацией и сортировкой.

    Args:
        query: Поисковый запрос по имени алерта
        tags: Список тегов для фильтрации (через запятую)
        limit: Количество записей на странице
        offset: Смещение для пагинации
        order_by: Поле для сортировки
        order_dir: Направление сортировки (asc/desc)

    Returns:
        AlertListResponse: Список алертов с метаданными пагинации

    Raises:
        HTTPException: При ошибке валидации параметров или БД
    """
    return await service.search_alerts(
        query=query,
        tags=tags,
        order_by=order_by,
        order_dir=order_dir,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/autocomplete",
    response_model=AlertAutocompleteResponse,
    summary="Автодополнение алертов",
    description="Автодополнение по alert_name для поиска алертов.",
    response_model_exclude_none=True,
)
async def autocomplete_alerts(
    query: str | None = Query(None, description="Поиск по alert_name"),
    limit: int = Query(
        10, ge=1, le=50, description="Максимальное количество результатов"
    ),
    service: AlertsServiceProtocol = Depends(get_alerts_service),
):
    """
    Автодополнение алертов - возвращает только id и имена алертов.
    """
    return await service.autocomplete_alerts(query, limit)


@router.get(
    "/detail",
    response_model=AlertDetail,
    summary="Получить детали алерта",
    description="Получить подробную информацию об алерте по ID.",
    response_model_exclude_none=True,
)
async def get_alert_detail(
    alert_id: UUID = Query(..., description="ID алерта"),
    service: AlertsServiceProtocol = Depends(get_alerts_service),
):
    return await service.get_alert_detail(alert_id)


@router.post(
    "/detail",
    summary="Создать новый алерт",
    description="Создать новый алерт с указанными параметрами. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def create_alert(
    data: AlertDetailCreate = Body(...),
    service: AlertsServiceProtocol = Depends(get_alerts_service),
) -> bool:
    """
    Создание нового алерта.

    Args:
        data: Данные для создания алерта

    Returns:
        bool: true при успешном создании

    Raises:
        HTTPException: При ошибке валидации, дублировании имени или БД
    """
    return await service.create_alert(data)


@router.patch(
    "/detail",
    summary="Обновить алерт",
    description="Обновить существующий алерт по ID. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def update_alert(
    data: AlertDetailUpdate = Body(...),
    service: AlertsServiceProtocol = Depends(get_alerts_service),
) -> bool:
    """
    Обновление существующего алерта.

    Args:
        data: Данные для обновления алерта

    Returns:
        bool: true при успешном обновлении

    Raises:
        HTTPException: При ошибке валидации, отсутствии алерта или БД
    """
    return await service.update_alert(data)


@router.delete(
    "/detail",
    summary="Удалить алерт",
    description="Удалить алерт по ID. Автоматически удаляет все связанные данные: линки, подписки, историю пауз и DT. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def delete_alert(
    alert_id: UUID = Query(..., description="ID алерта для удаления"),
    service: AlertsServiceProtocol = Depends(get_alerts_service),
) -> bool:
    """
    Удаление алерта по ID.

    Автоматически удаляет все связанные данные:
    - Линки (alerts.alerts_links)
    - Подписки (alerts.alerts_contacts) и их статусы (alerts.alerts_contacts_status)
    - История пауз (alerts.pause_history)
    - DT (alerts.alerts_dt)

    Args:
        alert_id: UUID алерта для удаления
        service: Сервис для работы с алертами

    Returns:
        bool: true при успешном удалении

    Raises:
        HTTPException: При отсутствии алерта или ошибке БД
    """
    return await service.delete_alert(alert_id)


@duplicate_router.post(
    "/{alert_id}/duplicate",
    summary="Дублировать алерт",
    description="Создает точную копию алерта со всем содержимым: группами, подписками, статусами, DT и линками. Новое имя формируется как '{старое_имя} copy - {дата_время}'.",
)
async def duplicate_alert(
    alert_id: UUID = Path(..., description="ID алерта для дублирования"),
    service: AlertsServiceProtocol = Depends(get_alerts_service),
) -> bool:
    """
    Дублирование алерта со всем содержимым.

    Создает новый алерт с:
    - Всеми полями исходного алерта (кроме id и alert_name)
    - Скопированными линками
    - Скопированными подписками со всеми статусами
    - Скопированным DT (если есть)
    - Паузы не копируются

    Args:
        alert_id: ID исходного алерта
        service: Сервис для работы с алертами

    Returns:
        bool: true при успешном дублировании

    Raises:
        HTTPException: При отсутствии алерта или ошибке БД
    """
    return await service.duplicate_alert(alert_id)


@router.get(
    "/tags/cloud",
    response_model=TagCloudResponse,
    summary="Получить облако тегов",
    description="Возвращает актуальные уникальные теги как массив строк. Поддерживает фильтрацию по алертам через alert_name и tags.",
    response_model_exclude_none=True,
)
async def get_tag_cloud(
    alert_name: str | None = Query(
        None, min_length=1, description="Поиск по alert_name"
    ),
    tags: str | None = Query(None, description="Теги через запятую (AND)"),
    service: AlertsServiceProtocol = Depends(get_alerts_service),
) -> TagCloudResponse:
    """
    Получение облака тегов как массив уникальных строк.

    Если передан фильтр `tags`, то в облако не включаются теги из этого фильтра.

    Returns:
        dict: Словарь с массивом тегов и общим количеством

    Raises:
        HTTPException: При ошибке БД
    """
    return await service.get_tag_cloud(alert_name=alert_name, tags=tags)


@router.patch(
    "/pause",
    summary="Переключить состояние паузы алерта",
    description="Если алерт на паузе - снять с паузы, если не на паузе - поставить на паузу. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def toggle_alert_pause(
    data: AlertPauseRequest,
    pauses_service: PausesServiceProtocol = Depends(get_pauses_service),
) -> bool:
    """
    Переключение состояния паузы алерта (безусловная пауза).

    Логика работы:
    - Если алерт НЕ на паузе: создает новую запись в pause_history с start_user = login, end_user = NULL, end_time = NULL
    - Если алерт УЖЕ на паузе: закрывает все активные паузы, устанавливая end_user = login и end_time = now()

    Состояние паузы определяется по попаданию текущей даты в период хотя бы одной активной паузы
    (start_time <= now() AND (end_time IS NULL OR end_time >= now()))
    Независимо от того, указан ли end_user в записи паузы.

    Args:
        data: Данные для переключения паузы (alert_id и login)
        pauses_service: Сервис для работы с паузами

    Returns:
        bool: true при успешном переключении

    Raises:
        HTTPException: При ошибке валидации, отсутствии алерта или БД
    """
    return await pauses_service.toggle_alert_pause(
        data.alert_id, data.login, data.comment
    )
