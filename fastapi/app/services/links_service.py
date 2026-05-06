"""
Сервис для работы с линками алертов.
Содержит асинхронную бизнес-логику для работы с линками.
"""

from typing import Any
from uuid import UUID

from contracts.repository_protocols import LinksRepositoryProtocol
from fastapi import HTTPException

from schemas.links import (
    LinkByAlertListItem,
    LinkByAlertListResponse,
    LinkDetail,
    LinkDetailCreate,
    LinkDetailUpdate,
)
from utils import log


class LinksService:
    """Сервис для работы с линками."""

    def __init__(self, repository: LinksRepositoryProtocol):
        """
        Инициализация сервиса.

        Args:
            repository: Репозиторий для работы с линками
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

    async def get_links_by_alert(
        self, alert_id: UUID
    ) -> LinkByAlertListResponse:
        """Получить все линки алерта."""
        try:
            rows = await self.repository.get_links_by_alert(alert_id)
            links = []
            for row in rows:
                row_dict = self._as_dict(row)
                links.append(
                    LinkByAlertListItem(
                        link_id=row_dict.get("id"),
                        link_name=row_dict.get("link_name"),
                        link_url=row_dict.get("link_url"),
                    )
                )
            return LinkByAlertListResponse(links=links, total=len(links))
        except Exception as e:
            log.error(f"[LinksService.get_links_by_alert] Error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при получении линков алерта: {e}",
            )

    async def get_link_detail(self, link_id: UUID) -> LinkDetail:
        """Получить детали линка."""
        try:
            row = await self.repository.get_link_by_id(link_id)
            if not row:
                raise HTTPException(status_code=404, detail="Линк не найден")
            row_dict = self._as_dict(row)
            return LinkDetail(
                link_id=row_dict.get("id"),
                alert_id=row_dict.get("alert"),
                alert_name=row_dict.get("alert_name"),
                link_name=row_dict.get("link_name"),
                link_url=row_dict.get("link_url"),
            )
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[LinksService.get_link_detail] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при получении линка: {e}"
            )

    async def create_link(self, data: LinkDetailCreate) -> bool:
        """Создать линк."""
        try:
            await self.repository.create_link(
                data.alert_id, data.link_name, data.link_url
            )
            return True
        except Exception as e:
            log.error(f"[LinksService.create_link] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при создании линка: {e}"
            )

    async def update_link(self, data: LinkDetailUpdate) -> bool:
        """Обновить линк."""
        try:
            if not await self.repository.check_link_exists(data.link_id):
                raise HTTPException(status_code=404, detail="Линк не найден")

            await self.repository.update_link(
                data.link_id, data.link_name, data.link_url
            )
            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[LinksService.update_link] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при обновлении линка: {e}"
            )

    async def delete_link(self, link_id: UUID) -> bool:
        """Удалить линк."""
        try:
            if not await self.repository.check_link_exists(link_id):
                raise HTTPException(status_code=404, detail="Линк не найден")

            await self.repository.delete_link(link_id)
            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[LinksService.delete_link] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при удалении линка: {e}"
            )
