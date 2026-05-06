from typing import Literal
from uuid import UUID

from contracts.service_protocols import PausesServiceProtocol
from dependencies import get_pauses_service

from fastapi import APIRouter, Body, Depends, Path, Query
from schemas.pauses import (
    AlertPauseRemoveRequest,
    AlertPauseScheduleRequest,
    AlertPauseUpdateRequest,
    PauseHistoryResponse,
)

router = APIRouter(prefix="/alerts/api/v1/alerts", tags=["pauses"])


@router.get(
    "/{alert_id}/pause",
    response_model=PauseHistoryResponse,
    summary="Получить историю пауз алерта",
    description="Возвращает паузы алерта с возможностью фильтрации по статусу (все, активные, будущие, прошлые), сортировки по полям и пагинации. По умолчанию сортировка по start_time DESC, 20 записей на странице. Даты возвращаются с таймзоной сервера БД (например: '2025-12-17T10:00:00+03:00').",
    response_model_exclude_none=True,
)
async def get_alert_pauses(
    alert_id: UUID = Path(..., description="ID алерта"),
    filter_type: Literal["all", "active", "future", "past"] = Query(
        "all",
        description="Тип фильтрации: all (все), active (активные), future (будущие), past (прошлые)",
    ),
    order_by: Literal[
        "start_time", "end_time", "start_user", "end_user"
    ] = Query("start_time", description="Поле сортировки"),
    order_dir: Literal["asc", "desc"] = Query(
        "desc", description="Направление сортировки"
    ),
    limit: int = Query(20, ge=1, le=100, description="Сколько пауз вернуть"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    service: PausesServiceProtocol = Depends(get_pauses_service),
) -> PauseHistoryResponse:
    """
    Получение истории пауз алерта с фильтрацией, сортировкой и пагинацией.

    Логика фильтрации:
    - all: все паузы
    - active: активные паузы (start_time <= now() AND (end_time IS NULL OR end_time >= now()))
    - future: будущие паузы (start_time > now() AND (end_time IS NULL OR end_time > start_time))
    - past: прошлые паузы (end_time IS NOT NULL AND end_time < now())

    Сортировка:
    - По умолчанию: start_time DESC
    - Доступные поля: start_time, end_time, start_user, end_user
    - Направление: asc или desc

    Пагинация:
    - По умолчанию: 20 записей на странице
    - limit: количество записей (от 1 до 100)
    - offset: смещение для пагинации

    Args:
        alert_id: ID алерта (из path)
        filter_type: Тип фильтрации (all, active, future, past)
        order_by: Поле сортировки (start_time, end_time, start_user, end_user)
        order_dir: Направление сортировки (asc, desc)
        limit: Количество записей на странице
        offset: Смещение для пагинации

    Returns:
        PauseHistoryResponse: Список пауз с метаданными (total - общее количество с учетом фильтра)

    Raises:
        HTTPException: При ошибке валидации, отсутствии алерта или БД
    """
    return await service.get_alert_pauses(
        alert_id=alert_id,
        filter_type=filter_type,
        order_by=order_by,
        order_dir=order_dir,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{alert_id}/pause",
    summary="Установить условную паузу алерта (алиас для /schedule)",
    description="Алиас для POST /{alert_id}/pause/schedule. Устанавливает паузу алерта с указанием времени начала и окончания. Даты должны передаваться с таймзоной (например: '2025-12-17T10:00:00+03:00'). Если start_time не указан или пустая строка, БД установит now(). Если end_time не указан (None) или пустая строка, пауза будет бессрочной (end_time = NULL). Возвращает true при успехе.",
    response_model_exclude_none=True,
    include_in_schema=False,  # Скрываем из Swagger, чтобы не дублировать
)
async def create_alert_pause(
    alert_id: UUID = Path(..., description="ID алерта"),
    data: AlertPauseScheduleRequest = Body(...),
    service: PausesServiceProtocol = Depends(get_pauses_service),
) -> bool:
    """Алиас для schedule_alert_pause для обратной совместимости с фронтендом."""
    return await service.schedule_alert_pause(alert_id, data)


@router.post(
    "/{alert_id}/pause/schedule",
    summary="Установить условную паузу алерта",
    description="Устанавливает паузу алерта с указанием времени начала и окончания. Даты должны передаваться с таймзоной (например: '2025-12-17T10:00:00+03:00'). Если start_time не указан или пустая строка, БД установит now(). Если end_time не указан (None) или пустая строка, пауза будет бессрочной (end_time = NULL). Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def schedule_alert_pause(
    alert_id: UUID = Path(..., description="ID алерта"),
    data: AlertPauseScheduleRequest = Body(...),
    service: PausesServiceProtocol = Depends(get_pauses_service),
) -> bool:
    """
    Установка условной паузы алерта с указанием времени начала и окончания.

    Логика работы:
    - Если start_time не указан или пустая строка - БД установит now()
    - Если end_time - пустая строка, пауза будет бессрочной (end_time = NULL, end_user = NULL)
    - login используется для start_user (всегда) и для end_user (если указан end_time и не пустая строка)
    - Создает новую запись в pause_history

    Args:
        alert_id: ID алерта (из path)
        data: Данные для установки паузы (start_time, end_time, login)

    Returns:
        bool: true при успешной установке паузы

    Raises:
        HTTPException: При ошибке валидации, отсутствии алерта или БД
    """
    return await service.schedule_alert_pause(alert_id, data)


@router.patch(
    "/{alert_id}/pause/stop",
    summary="Остановить все активные паузы алерта",
    description="Останавливает все активные паузы алерта, устанавливая end_time = now() и end_user. Если end_time уже был указан - перезаписывается на now(). Если end_user уже был указан - перезаписывается на переданный.",
)
async def stop_alert_pause(
    alert_id: UUID = Path(..., description="ID алерта"),
    data: AlertPauseRemoveRequest = Body(...),
    service: PausesServiceProtocol = Depends(get_pauses_service),
) -> bool:
    """Остановка всех активных пауз алерта."""
    return await service.stop_alert_pause(alert_id, data)


@router.patch(
    "/{alert_id}/pause/{pause_id}",
    summary="Изменить условную паузу алерта",
    description="Изменяет условную паузу алерта. Можно изменить start_time и/или end_time. Даты должны передаваться с таймзоной (например: '2025-12-17T10:00:00+03:00'). Если start_time - пустая строка, установится now(). Если end_time - пустая строка, пауза станет бессрочной (end_time = NULL, end_user = NULL). Если указан start_time или end_time (не пустая строка), обязательно указать login. Переданные поля перезаписываются в БД.",
    response_model_exclude_none=True,
)
async def update_alert_pause(
    alert_id: UUID = Path(..., description="ID алерта"),
    pause_id: UUID = Path(..., description="ID паузы"),
    data: AlertPauseUpdateRequest = Body(...),
    service: PausesServiceProtocol = Depends(get_pauses_service),
) -> bool:
    """Изменение условной паузы алерта."""
    return await service.update_alert_pause(alert_id, pause_id, data)


@router.patch(
    "/{alert_id}/pause/{pause_id}/stop",
    summary="Остановить конкретную паузу алерта",
    description="Останавливает конкретную паузу алерта. Если пауза активна - устанавливает end_time = now() и end_user. Если пауза в будущем - устанавливает end_time = start_time и end_user (пауза так и не начнется). Если пауза в прошлом - возвращает ошибку 400.",
)
async def stop_specific_alert_pause(
    alert_id: UUID = Path(..., description="ID алерта"),
    pause_id: UUID = Path(..., description="ID паузы"),
    data: AlertPauseRemoveRequest = Body(...),
    service: PausesServiceProtocol = Depends(get_pauses_service),
) -> bool:
    """Остановка конкретной паузы алерта."""
    return await service.stop_specific_alert_pause(alert_id, pause_id, data)


@router.delete(
    "/{alert_id}/pause/{pause_id}",
    summary="Удалить конкретную паузу из истории алерта",
    description="Удаляет конкретную паузу из истории алерта по её ID. Полностью удаляет запись из alerts.pause_history. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def delete_alert_pause(
    alert_id: UUID = Path(..., description="ID алерта"),
    pause_id: UUID = Path(..., description="ID паузы"),
    service: PausesServiceProtocol = Depends(get_pauses_service),
) -> bool:
    """Удаление конкретной паузы из истории алерта."""
    return await service.delete_alert_pause(alert_id, pause_id)
