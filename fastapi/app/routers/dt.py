from uuid import UUID

from contracts.service_protocols import DTServiceProtocol
from dependencies import get_dt_service

from fastapi import APIRouter, Body, Depends, Path
from schemas.dt import DTDetail, DTDetailCreate, DTDetailUpdate

router = APIRouter(prefix="/alerts/api/v1", tags=["dt"])


@router.get(
    "/alert/{alert_id}/dt",
    response_model=DTDetail,
    summary="Получить DT для алерта",
    description="Получить DT для указанного алерта.",
    response_model_exclude_none=True,
)
async def get_dt(
    alert_id: UUID = Path(..., description="ID алерта"),
    service: DTServiceProtocol = Depends(get_dt_service),
) -> DTDetail:
    """Получение DT для алерта."""
    return await service.get_dt(alert_id)


@router.post(
    "/alert/{alert_id}/dt",
    summary="Создать DT для алерта",
    description="Создать новый DT для указанного алерта. content и silence_time должны содержать корректный JSON. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def create_dt(
    alert_id: UUID = Path(..., description="ID алерта"),
    data: DTDetailCreate = Body(...),
    service: DTServiceProtocol = Depends(get_dt_service),
) -> bool:
    """Создание нового DT для алерта."""
    return await service.create_dt(alert_id, data)


@router.patch(
    "/alert/{alert_id}/dt",
    summary="Обновить DT для алерта",
    description="Обновить существующий DT для указанного алерта. content и silence_time должны содержать корректный JSON, если переданы. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def update_dt(
    alert_id: UUID = Path(..., description="ID алерта"),
    data: DTDetailUpdate = Body(...),
    service: DTServiceProtocol = Depends(get_dt_service),
) -> bool:
    """Обновление существующего DT для алерта."""
    return await service.update_dt(alert_id, data)


@router.delete(
    "/alert/{alert_id}/dt",
    summary="Удалить DT для алерта",
    description="Удалить DT для указанного алерта. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def delete_dt(
    alert_id: UUID = Path(..., description="ID алерта"),
    service: DTServiceProtocol = Depends(get_dt_service),
) -> bool:
    """Удаление DT для алерта."""
    return await service.delete_dt(alert_id)
