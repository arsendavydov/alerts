from uuid import UUID

from contracts.service_protocols import LinksServiceProtocol
from dependencies import get_links_service

from fastapi import APIRouter, Body, Depends, Query
from schemas.links import (
    LinkByAlertListResponse,
    LinkDetail,
    LinkDetailCreate,
    LinkDetailUpdate,
)

router = APIRouter(prefix="/alerts/api/v1/links", tags=["links"])


@router.get(
    "/by_alert",
    response_model=LinkByAlertListResponse,
    summary="Получить линки алерта",
    description="Получить все линки для конкретного алерта в упрощенном формате.",
    response_model_exclude_none=True,
)
async def get_links_by_alert(
    alert_id: UUID, service: LinksServiceProtocol = Depends(get_links_service)
) -> LinkByAlertListResponse:
    """Получение всех линков для конкретного алерта."""
    return await service.get_links_by_alert(alert_id)


@router.get(
    "/detail",
    response_model=LinkDetail,
    summary="Получить детали линка",
    description="Получить подробную информацию о линке по ID.",
    response_model_exclude_none=True,
)
async def get_link_detail(
    link_id: UUID = Query(..., description="ID линка"),
    service: LinksServiceProtocol = Depends(get_links_service),
) -> LinkDetail:
    """Получение детальной информации о линке по ID."""
    return await service.get_link_detail(link_id)


@router.post(
    "/detail",
    summary="Создать линк",
    description="Создать новый линк с указанными параметрами. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def create_link_detail(
    data: LinkDetailCreate = Body(...),
    service: LinksServiceProtocol = Depends(get_links_service),
) -> bool:
    """Создание нового линка."""
    return await service.create_link(data)


@router.patch(
    "/detail",
    summary="Обновить линк",
    description="Обновить существующий линк по ID. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def patch_link_detail(
    data: LinkDetailUpdate = Body(...),
    service: LinksServiceProtocol = Depends(get_links_service),
) -> bool:
    """Обновление существующего линка."""
    return await service.update_link(data)


@router.delete(
    "/detail",
    summary="Удалить линк",
    description="Удалить линк по ID. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def delete_link_detail(
    link_id: UUID = Query(..., description="ID линка для удаления"),
    service: LinksServiceProtocol = Depends(get_links_service),
) -> bool:
    """Удаление линка по ID."""
    return await service.delete_link(link_id)
