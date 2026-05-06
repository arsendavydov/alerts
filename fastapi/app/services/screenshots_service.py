"""
Сервис для работы со скриншотами.
Содержит асинхронную бизнес-логику для работы со скриншотами.
"""

import json
from typing import Any
from uuid import UUID

from contracts.repository_protocols import ScreenshotsRepositoryProtocol
from fastapi import HTTPException

from schemas.screenshots import (
    ScreenshotCreate,
    ScreenshotDetail,
    ScreenshotSearchItem,
    ScreenshotSearchResponse,
    ScreenshotUpdate,
)
from utils import log


class ScreenshotsService:
    """Сервис для работы со скриншотами."""

    def __init__(self, repository: ScreenshotsRepositoryProtocol):
        """
        Инициализация сервиса.

        Args:
            repository: Репозиторий для работы со скриншотами
        """
        self.repository = repository

    @staticmethod
    def _as_dict(row: object) -> dict[str, Any]:
        if isinstance(row, dict):
            return row
        mapping = getattr(row, "_mapping", None)
        if mapping is not None:
            return dict(mapping)
        keys_method = getattr(row, "keys", None)
        if callable(keys_method):
            try:
                keys = list(keys_method())
                result: dict[str, Any] = {}
                for idx, key in enumerate(keys):
                    result[key] = row[idx]  # type: ignore[index]
                return result
            except Exception:
                return {}
        return {}

    async def search_screenshots(
        self,
        query: str | None = None,
        order_by: str = "description",
        order_dir: str = "asc",
        limit: int = 1000,
        offset: int = 0,
    ) -> ScreenshotSearchResponse:
        """
        Поиск скриншотов с полнотекстовым поиском по description, сортировкой и пагинацией.

        Args:
            query: Поисковый запрос по description (опциональный)
            order_by: Поле сортировки (description, name)
            order_dir: Направление сортировки (asc, desc)
            limit: Количество записей на странице
            offset: Смещение для пагинации

        Returns:
            ScreenshotSearchResponse: Список скриншотов с метаданными пагинации
        """
        try:
            rows, total = await self.repository.search_screenshots(
                query=query,
                order_by=order_by,
                order_dir=order_dir,
                limit=limit,
                offset=offset,
            )
            screenshots = []
            for row in rows:
                row_dict = self._as_dict(row)
                screenshots.append(
                    ScreenshotSearchItem(
                        screenshot_id=row_dict.get("id"),
                        name=row_dict.get("name") or "",
                        description=row_dict.get("description") or "",
                        image_data=row_dict.get("image_data") or "",
                    )
                )
            return ScreenshotSearchResponse(
                screenshots=screenshots,
                total=total,
                limit=limit,
                offset=offset,
            )
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[ScreenshotsService.search_screenshots] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при поиске скриншотов: {e}"
            )

    async def get_screenshot(self, screenshot_id: UUID) -> ScreenshotDetail:
        """
        Получить скриншот по ID.

        Args:
            screenshot_id: ID скриншота

        Returns:
            ScreenshotDetail: Детальная информация о скриншоте
        """
        try:
            row = await self.repository.get_screenshot_by_id(screenshot_id)
            if not row:
                raise HTTPException(
                    status_code=404, detail="Скриншот не найден"
                )
            row_dict = self._as_dict(row)
            return ScreenshotDetail(
                screenshot_id=row_dict.get("id"),
                name=row_dict.get("name") or "",
                description=row_dict.get("description") or "",
                image_data=row_dict.get("image_data") or "",
            )
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[ScreenshotsService.get_screenshot] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при получении скриншота: {e}"
            )

    async def create_screenshot(self, data: ScreenshotCreate) -> UUID:
        """
        Создать новый скриншот.

        Args:
            data: Данные для создания скриншота

        Returns:
            UUID: ID созданного скриншота
        """
        try:
            # Дополнительная валидация JSON (хотя уже есть в схеме)
            try:
                json.loads(data.image_data)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"image_data должен быть валидным JSON: {e}",
                )

            screenshot_id = await self.repository.create_screenshot(
                name=data.name,
                description=data.description,
                image_data=data.image_data,
            )
            return screenshot_id
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[ScreenshotsService.create_screenshot] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при создании скриншота: {e}"
            )

    async def update_screenshot(
        self, screenshot_id: UUID, data: ScreenshotUpdate
    ) -> bool:
        """
        Обновить скриншот.

        Args:
            screenshot_id: ID скриншота
            data: Данные для обновления

        Returns:
            bool: True при успехе
        """
        try:
            if not await self.repository.check_screenshot_exists(
                screenshot_id
            ):
                raise HTTPException(
                    status_code=404, detail="Скриншот не найден"
                )

            # Дополнительная валидация JSON, если image_data передан
            if data.image_data is not None:
                try:
                    json.loads(data.image_data)
                except json.JSONDecodeError as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"image_data должен быть валидным JSON: {e}",
                    )

            await self.repository.update_screenshot(
                screenshot_id=screenshot_id,
                name=data.name,
                description=data.description,
                image_data=data.image_data,
            )
            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[ScreenshotsService.update_screenshot] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при обновлении скриншота: {e}"
            )

    async def delete_screenshot(self, screenshot_id: UUID) -> bool:
        """
        Удалить скриншот.

        Args:
            screenshot_id: ID скриншота

        Returns:
            bool: True при успехе
        """
        try:
            if not await self.repository.check_screenshot_exists(
                screenshot_id
            ):
                raise HTTPException(
                    status_code=404, detail="Скриншот не найден"
                )

            await self.repository.delete_screenshot(screenshot_id)
            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[ScreenshotsService.delete_screenshot] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при удалении скриншота: {e}"
            )
