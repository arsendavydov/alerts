from typing import Literal
from uuid import UUID

from contracts.service_protocols import ScreenshotsServiceProtocol
from dependencies import get_screenshots_service

from fastapi import APIRouter, Body, Depends, Path, Query
from schemas.screenshots import (
    ScreenshotCreate,
    ScreenshotDetail,
    ScreenshotSearchResponse,
    ScreenshotUpdate,
)

router = APIRouter(prefix="/alerts/api/v1/screenshots", tags=["screenshots"])


@router.get(
    "/search",
    response_model=ScreenshotSearchResponse,
    summary="Поиск скриншотов",
    description="Поиск скриншотов с полнотекстовым поиском по description, пагинацией и сортировкой. Поддерживает регистронезависимый поиск, русский и английский текст.",
    response_model_exclude_none=True,
)
async def search_screenshots(
    query: str | None = Query(
        None, min_length=1, description="Поиск по description"
    ),
    limit: int = Query(
        1000, ge=1, le=1000, description="Количество скриншотов на странице"
    ),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    order_by: Literal["description", "name"] = Query(
        "description", description="Поле сортировки"
    ),
    order_dir: Literal["asc", "desc"] = Query(
        "asc", description="Направление сортировки"
    ),
    service: ScreenshotsServiceProtocol = Depends(get_screenshots_service),
) -> ScreenshotSearchResponse:
    """
    Поиск скриншотов с полнотекстовым поиском, пагинацией и сортировкой.

    Args:
        query: Поисковый запрос по description
        limit: Количество записей на странице
        offset: Смещение для пагинации
        order_by: Поле для сортировки (description, name)
        order_dir: Направление сортировки (asc/desc)

    Returns:
        ScreenshotSearchResponse: Список скриншотов с метаданными пагинации

    Raises:
        HTTPException: При ошибке валидации параметров или БД
    """
    return await service.search_screenshots(
        query=query,
        order_by=order_by,
        order_dir=order_dir,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{screenshot_id}",
    response_model=ScreenshotDetail,
    summary="Получить скриншот по ID",
    description="Получить детальную информацию о скриншоте по ID.",
    response_model_exclude_none=True,
)
async def get_screenshot(
    screenshot_id: UUID = Path(..., description="ID скриншота"),
    service: ScreenshotsServiceProtocol = Depends(get_screenshots_service),
) -> ScreenshotDetail:
    """Получение скриншота по ID."""
    return await service.get_screenshot(screenshot_id)


@router.post(
    "",
    summary="Создать скриншот",
    description="Создать новый скриншот. Все поля обязательны. image_data должен быть валидным JSON (массив или объект). Возвращает ID созданного скриншота.",
    response_model_exclude_none=True,
)
async def create_screenshot(
    data: ScreenshotCreate = Body(...),
    service: ScreenshotsServiceProtocol = Depends(get_screenshots_service),
) -> dict:
    """Создание нового скриншота."""
    screenshot_id = await service.create_screenshot(data)
    return {"screenshot_id": screenshot_id}


@router.patch(
    "/{screenshot_id}",
    summary="Обновить скриншот",
    description="Обновить существующий скриншот. Все поля опциональны. Если передается image_data, он должен быть валидным JSON. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def update_screenshot(
    screenshot_id: UUID = Path(..., description="ID скриншота"),
    data: ScreenshotUpdate = Body(...),
    service: ScreenshotsServiceProtocol = Depends(get_screenshots_service),
) -> bool:
    """Обновление существующего скриншота."""
    return await service.update_screenshot(screenshot_id, data)


@router.delete(
    "/{screenshot_id}",
    summary="Удалить скриншот",
    description="Удалить скриншот по ID. Возвращает true при успехе.",
    response_model_exclude_none=True,
)
async def delete_screenshot(
    screenshot_id: UUID = Path(..., description="ID скриншота для удаления"),
    service: ScreenshotsServiceProtocol = Depends(get_screenshots_service),
) -> bool:
    """Удаление скриншота по ID."""
    return await service.delete_screenshot(screenshot_id)
