"""
Сервис для работы с DT (Decision Table).
Содержит асинхронную бизнес-логику для работы с DT.
"""

import json
from typing import Any
from uuid import UUID

from contracts.repository_protocols import DTRepositoryProtocol
from fastapi import HTTPException

from schemas.dt import DTDetail, DTDetailCreate, DTDetailUpdate
from utils import log


class DTService:
    """Сервис для работы с DT."""

    def __init__(self, repository: DTRepositoryProtocol):
        """
        Инициализация сервиса.

        Args:
            repository: Репозиторий для работы с DT
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

    async def get_dt(self, alert_id: UUID) -> DTDetail:
        """Получить DT для алерта."""
        try:
            if not await self.repository.check_alert_exists(alert_id):
                raise HTTPException(status_code=404, detail="Алерт не найден")

            row = await self.repository.get_dt_by_alert_id(alert_id)
            if not row:
                raise HTTPException(
                    status_code=404, detail="DT не найден для данного алерта"
                )

            row_dict = self._as_dict(row)
            content_str = row_dict.get("content") or "{}"
            silence_time_str = row_dict.get("silence_time")
            dt_id = row_dict.get("id")
            alert_id_val = row_dict.get("alert")
            auto_create = row_dict.get("auto_create")
            try:
                content_obj = (
                    json.loads(content_str) if content_str.strip() else {}
                )
            except json.JSONDecodeError:
                content_obj = content_str

            silence_time_obj = None
            if silence_time_str is not None:
                try:
                    silence_time_obj = (
                        json.loads(silence_time_str)
                        if silence_time_str.strip()
                        else {}
                    )
                except json.JSONDecodeError:
                    silence_time_obj = silence_time_str

            return DTDetail(
                dt_id=dt_id,
                alert_id=alert_id_val,
                content=content_obj,
                auto_create=auto_create,
                silence_time=silence_time_obj,
            )
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[DTService.get_dt] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при получении DT: {e}"
            )

    async def create_dt(self, alert_id: UUID, data: DTDetailCreate) -> bool:
        """Создать DT для алерта."""
        try:
            if not await self.repository.check_alert_exists(alert_id):
                raise HTTPException(status_code=404, detail="Алерт не найден")

            if await self.repository.check_dt_exists(alert_id):
                raise HTTPException(
                    status_code=409,
                    detail="DT для данного алерта уже существует",
                )

            # Валидация content и silence_time уже выполнена в схеме через field_validator
            # Для создания: None означает установку NULL в БД (валидатор конвертирует пустые строки в None)
            silence_time = data.silence_time

            await self.repository.create_dt(
                alert_id, data.content, data.auto_create, silence_time
            )
            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[DTService.create_dt] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при создании DT: {e}"
            )

    async def update_dt(self, alert_id: UUID, data: DTDetailUpdate) -> bool:
        """Обновить DT для алерта."""
        try:
            if not await self.repository.check_alert_exists(alert_id):
                raise HTTPException(status_code=404, detail="Алерт не найден")

            if not await self.repository.check_dt_exists(alert_id):
                raise HTTPException(
                    status_code=404, detail="DT не найден для данного алерта"
                )

            # Валидация content и silence_time уже выполнена в схеме через field_validator
            # Для обновления:
            # - content: None означает "не обновлять", валидный JSON - обновить (поле NOT NULL, пустая строка недопустима)
            # - silence_time: None означает "не обновлять", "" означает "установить NULL в БД" (поле может быть NULL)
            content = (
                data.content
            )  # None означает не обновлять, валидный JSON - обновить
            silence_time = (
                data.silence_time
            )  # None означает не обновлять, "" означает установить NULL

            await self.repository.update_dt(
                alert_id, content, data.auto_create, silence_time
            )
            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[DTService.update_dt] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при обновлении DT: {e}"
            )

    async def delete_dt(self, alert_id: UUID) -> bool:
        """Удалить DT для алерта."""
        try:
            if not await self.repository.check_alert_exists(alert_id):
                raise HTTPException(status_code=404, detail="Алерт не найден")

            if not await self.repository.check_dt_exists(alert_id):
                raise HTTPException(
                    status_code=404, detail="DT не найден для данного алерта"
                )

            await self.repository.delete_dt(alert_id)
            return True
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"[DTService.delete_dt] Error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Ошибка при удалении DT: {e}"
            )
