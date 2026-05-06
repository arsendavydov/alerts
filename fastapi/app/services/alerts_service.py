"""
Сервис для работы с алертами.
Содержит асинхронную бизнес-логику для работы с алертами.
"""

import json
from typing import Any
from uuid import UUID

from contracts.repository_protocols import AlertsRepositoryProtocol
from fastapi import HTTPException
from sqlalchemy_db import async_session_scope

from repositories.alerts_repository import AlertsRepository
from schemas.alerts import (
    AlertAutocomplete,
    AlertAutocompleteResponse,
    AlertDetail,
    AlertDetailCreate,
    AlertDetailUpdate,
    AlertListItem,
    AlertListResponse,
    TagCloudResponse,
)
from utils import log


class AlertsService:
    """Сервис для работы с алертами."""

    def __init__(self, repository: AlertsRepositoryProtocol | None = None):
        """
        Инициализация сервиса.

        Args:
            repository: Репозиторий для работы с алертами
        """
        self.repository = repository or AlertsRepository()

    @staticmethod
    def _as_dict(row: object) -> dict[str, Any]:
        if isinstance(row, dict):
            return row
        mapping = getattr(row, "_mapping", None)
        if mapping is not None:
            return dict(mapping)
        if hasattr(row, "keys"):
            try:
                keys = list(row.keys())  # type: ignore[attr-defined]
                result: dict[str, Any] = {}
                for idx, key in enumerate(keys):
                    try:
                        result[key] = row[key]  # type: ignore[index]
                    except Exception:
                        result[key] = row[idx]  # type: ignore[index]
                return result
            except Exception:
                return {}
        return {}

    async def search_alerts(
        self,
        query: str | None = None,
        tags: str | None = None,
        order_by: str = "alert_name",
        order_dir: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> AlertListResponse:
        """
        Поиск алертов с фильтрацией, сортировкой и пагинацией.

        Args:
            query: Поисковый запрос по имени алерта
            tags: Теги через запятую
            order_by: Поле сортировки
            order_dir: Направление сортировки (asc/desc)
            limit: Количество записей на странице
            offset: Смещение для пагинации

        Returns:
            AlertListResponse: Список алертов с метаданными пагинации

        Raises:
            HTTPException: При ошибке валидации или БД
        """
        try:
            rows, total = await self.repository.search_alerts(
                query=query,
                tags=tags,
                order_by=order_by,
                order_dir=order_dir,
                limit=limit,
                offset=offset,
            )

            alerts = []
            for row in rows:
                row_dict = self._as_dict(row)
                tags = None
                row_tags = row_dict.get("tags")
                if row_tags:
                    try:
                        tags = (
                            json.loads(row_tags)
                            if isinstance(row_tags, str)
                            else row_tags
                        )
                    except (json.JSONDecodeError, TypeError):
                        tags = None
                alert_data = {
                    "alert_id": row_dict.get("id"),
                    "alert_name": row_dict.get("alert_name"),
                    "indicator_name": row_dict.get("indicator_name"),
                    "paused": bool(row_dict.get("paused")),
                }
                if row_dict.get("alert_description") is not None:
                    alert_data["alert_description"] = row_dict.get(
                        "alert_description"
                    )
                if row_dict.get("indicator_description") is not None:
                    alert_data["indicator_description"] = row_dict.get(
                        "indicator_description"
                    )
                if row_dict.get("status_id") is not None:
                    alert_data["status_id"] = str(row_dict.get("status_id"))
                if tags is not None:
                    alert_data["tags"] = tags
                alerts.append(AlertListItem(**alert_data))

            return AlertListResponse(alerts=alerts, total=total)
        except Exception as e:
            log.error(f"[AlertsService.search_alerts] Error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при получении списка алертов: {e}",
            )

    async def get_alert_detail(self, alert_id: UUID) -> AlertDetail:
        """
        Получить детали алерта.

        Args:
            alert_id: ID алерта

        Returns:
            AlertDetail: Детали алерта

        Raises:
            HTTPException: Если алерт не найден или ошибка БД
        """
        try:
            row = await self.repository.get_alert_by_id(alert_id)
            if not row:
                raise HTTPException(status_code=404, detail="Алерт не найден")
            row_dict = self._as_dict(row)

            tags = None
            row_tags = row_dict.get("tags")
            if row_tags:
                try:
                    tags = (
                        json.loads(row_tags)
                        if isinstance(row_tags, str)
                        else row_tags
                    )
                except (json.JSONDecodeError, TypeError):
                    tags = None
            row_alert_desc = row_dict.get("alert_description")
            row_alert_image = row_dict.get("alert_image")
            row_gr_desc = row_dict.get("group_rule_description")
            row_gr_image = row_dict.get("group_rule_image")
            row_silence = row_dict.get("silence_time")
            row_paused = row_dict.get("paused")
            alert_data = {
                "alert_id": row_dict.get("id"),
                "alert_name": row_dict.get("alert_name"),
                "indicator": {
                    "indicator_id": row_dict.get("event"),
                    "indicator_name": row_dict.get("event_name") or "Unknown",
                },
                "paused": bool(row_paused)
                if row_paused is not None
                else False,
            }
            if row_alert_desc is not None:
                alert_data["description"] = row_alert_desc
            if row_alert_image is not None:
                alert_data["image"] = row_alert_image
            if tags is not None:
                alert_data["tags"] = tags
            if row_dict.get("group_rules") is not None:
                alert_data["group_rule"] = {
                    "group_rule_id": row_dict.get("group_rules"),
                    "description": row_gr_desc,
                    "image": row_gr_image,
                }
            if row_silence is not None:
                silence_time_str = row_silence
                try:
                    silence_time_obj = (
                        json.loads(silence_time_str)
                        if isinstance(silence_time_str, str)
                        and silence_time_str.strip()
                        else {}
                    )
                except json.JSONDecodeError:
                    silence_time_obj = silence_time_str
                alert_data["silence_time"] = silence_time_obj

            return AlertDetail(**alert_data)
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[AlertsService.get_alert_detail] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при получении алерта: {e}"
            )

    async def create_alert(self, data: AlertDetailCreate) -> bool:
        """
        Создать новый алерт.

        Args:
            data: Данные для создания алерта

        Returns:
            bool: True при успешном создании

        Raises:
            HTTPException: При ошибке валидации, дублировании имени или БД
        """
        try:
            async with async_session_scope() as session:
                if await self.repository.check_alert_exists_by_name(
                    data.alert_name, session
                ):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Алерт с именем '{data.alert_name}' уже существует",
                    )

                if not await self.repository.check_group_rule_exists(
                    data.group_rule_id, session
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="Указанная группа правил не найдена",
                    )

                silence_time = data.silence_time

                await self.repository.create_alert(
                    alert_name=data.alert_name,
                    indicator_id=data.indicator_id,
                    description=data.description,
                    image=data.image,
                    tags=data.tags,
                    group_rule_id=data.group_rule_id,
                    silence_time=silence_time,
                    session=session,
                )

            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[AlertsService.create_alert] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при создании алерта: {e}"
            )

    async def update_alert(self, data: AlertDetailUpdate) -> bool:
        """
        Обновить алерт.

        Args:
            data: Данные для обновления алерта

        Returns:
            bool: True при успешном обновлении

        Raises:
            HTTPException: При ошибке валидации или БД
        """
        try:
            async with async_session_scope() as session:
                if not await self.repository.check_alert_exists_by_id(
                    data.alert_id, session
                ):
                    raise HTTPException(
                        status_code=404, detail="Алерт не найден"
                    )

                if data.alert_name is not None:
                    existing_alert = await self.repository.get_alert_by_id(
                        data.alert_id, session
                    )
                    existing_name = (
                        self._as_dict(existing_alert).get("alert_name")
                        if existing_alert
                        else None
                    )
                    if existing_alert and existing_name != data.alert_name:
                        if await self.repository.check_alert_exists_by_name(
                            data.alert_name, session
                        ):
                            raise HTTPException(
                                status_code=400,
                                detail=f"Алерт с именем '{data.alert_name}' уже существует",
                            )

                if data.group_rule_id is not None:
                    if not await self.repository.check_group_rule_exists(
                        data.group_rule_id, session
                    ):
                        raise HTTPException(
                            status_code=400,
                            detail="Указанная группа правил не найдена",
                        )

                silence_time = data.silence_time

                await self.repository.update_alert(
                    alert_id=data.alert_id,
                    alert_name=data.alert_name,
                    indicator_id=data.indicator_id,
                    description=data.description,
                    image=data.image,
                    tags=data.tags,
                    group_rule_id=data.group_rule_id,
                    silence_time=silence_time,
                    session=session,
                )

            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[AlertsService.update_alert] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при обновлении алерта: {e}"
            )

    async def delete_alert(self, alert_id: UUID) -> bool:
        """
        Удалить алерт со всеми связанными данными (каскадное удаление).

        Автоматически удаляет:
        - Линки (alerts.alerts_links)
        - Подписки (alerts.alerts_contacts) и их статусы (alerts.alerts_contacts_status)
        - История пауз (alerts.pause_history)
        - DT (alerts.alerts_dt)

        Args:
            alert_id: ID алерта

        Returns:
            bool: True при успешном удалении

        Raises:
            HTTPException: Если алерт не найден или ошибка БД
        """
        try:
            async with async_session_scope() as session:
                if not await self.repository.check_alert_exists_by_id(
                    alert_id, session
                ):
                    raise HTTPException(
                        status_code=404, detail="Алерт не найден"
                    )

                await self.repository.delete_alert_with_cascade(
                    alert_id, session
                )
            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[AlertsService.delete_alert] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при удалении алерта: {e}"
            )

    async def autocomplete_alerts(
        self, query: str | None, limit: int
    ) -> AlertAutocompleteResponse:
        """
        Автодополнение алертов.

        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов

        Returns:
            AlertAutocompleteResponse: Список алертов для автодополнения
        """
        try:
            rows = await self.repository.autocomplete_alerts(query, limit)
            alerts = []
            for row in rows:
                row_dict = self._as_dict(row)
                alerts.append(
                    AlertAutocomplete(
                        alert_id=row_dict.get("id"),
                        alert_name=row_dict.get("alert_name"),
                    )
                )
            return AlertAutocompleteResponse(alerts=alerts, total=len(alerts))
        except Exception as e:
            log.error(f"[AlertsService.autocomplete_alerts] Error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при получении автодополнения: {e}",
            )

    async def get_tag_cloud(
        self, alert_name: str | None = None, tags: str | None = None
    ) -> TagCloudResponse:
        """
        Получить облако тегов.

        Если переданы фильтры по алертам, облако считается среди алертов, попавших под фильтрацию.
        При фильтрации по `tags` теги из фильтра исключаются из возвращаемого облака.

        Returns:
            TagCloudResponse: Облако тегов
        """
        try:
            raw_tags = await self.repository.get_tag_cloud(
                alert_name=alert_name, tags=tags
            )
            # В репозитории теги уже DISTINCT, но оставляем дедупликацию на уровне сервиса.
            unique_tags = sorted(set(raw_tags))
            return TagCloudResponse(tags=unique_tags, total=len(unique_tags))
        except Exception as e:
            log.error(f"[AlertsService.get_tag_cloud] Error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при получении облака тегов: {e}",
            )

    async def duplicate_alert(self, alert_id: UUID) -> bool:
        """
        Дублировать алерт со всеми связанными данными.

        Args:
            alert_id: ID исходного алерта

        Returns:
            bool: True при успешном дублировании

        Raises:
            HTTPException: Если алерт не найден или ошибка БД
        """
        try:
            async with async_session_scope() as session:
                new_alert_id = await self.repository.duplicate_alert(
                    alert_id, session
                )
            log.info(
                f"Successfully duplicated alert {alert_id} to {new_alert_id}"
            )
            return True
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            log.error(f"[AlertsService.duplicate_alert] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при дублировании алерта: {e}"
            )
