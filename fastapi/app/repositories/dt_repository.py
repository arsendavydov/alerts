"""
Репозиторий для работы с DT (Decision Table).
Содержит асинхронные методы доступа к данным для DT.
"""

from typing import Any, cast
from uuid import UUID

from models.alerts import AlertDtOrm, AlertOrm
from sqlalchemy import delete, insert, select
from sqlalchemy_db import async_session_scope


class DTRepository:
    """Репозиторий для работы с DT."""

    async def check_alert_exists(self, alert_id: UUID) -> bool:
        """Проверить существование алерта."""
        async with async_session_scope() as session:
            r = (
                await session.execute(
                    select(AlertOrm.id).where(AlertOrm.id == alert_id)
                )
            ).scalar_one_or_none()
            return r is not None

    async def get_dt_by_alert_id(self, alert_id: UUID) -> Any | None:
        """Получить DT по ID алерта."""
        stmt = select(
            AlertDtOrm.id,
            AlertDtOrm.alert,
            AlertDtOrm.content,
            AlertDtOrm.auto_create,
            AlertDtOrm.silence_time,
        ).where(AlertDtOrm.alert == alert_id)
        async with async_session_scope() as session:
            return (await session.execute(stmt)).one_or_none()

    async def check_dt_exists(self, alert_id: UUID) -> bool:
        """Проверить существование DT для алерта."""
        async with async_session_scope() as session:
            r = (
                await session.execute(
                    select(AlertDtOrm.id).where(AlertDtOrm.alert == alert_id)
                )
            ).scalar_one_or_none()
            return r is not None

    async def create_dt(
        self,
        alert_id: UUID,
        content: str,
        auto_create: bool,
        silence_time: str | None = None,
    ) -> UUID:
        """Создать DT."""
        values: dict[str, Any] = {
            "alert": alert_id,
            "content": content,
            "auto_create": auto_create,
        }
        if silence_time is not None:
            values["silence_time"] = silence_time
        stmt = insert(AlertDtOrm).values(**values).returning(AlertDtOrm.id)
        async with async_session_scope() as session:
            return cast("UUID", (await session.execute(stmt)).scalar_one())

    async def update_dt(
        self,
        alert_id: UUID,
        content: str | None = None,
        auto_create: bool | None = None,
        silence_time: str | None = None,
    ) -> bool:
        """Обновить DT."""
        async with async_session_scope() as session:
            row = (
                await session.execute(
                    select(AlertDtOrm).where(AlertDtOrm.alert == alert_id)
                )
            ).scalar_one_or_none()
            if row is None:
                raise ValueError("DT для алерта не найден")

            if content is not None:
                row.content = content
            if auto_create is not None:
                row.auto_create = auto_create
            if silence_time is not None:
                if silence_time.strip():
                    row.silence_time = silence_time
                else:
                    row.silence_time = None

            return True

    async def delete_dt(self, alert_id: UUID) -> bool:
        """Удалить DT."""
        async with async_session_scope() as session:
            dt_id = (
                await session.execute(
                    select(AlertDtOrm.id).where(AlertDtOrm.alert == alert_id)
                )
            ).scalar_one_or_none()
            if dt_id is None:
                raise ValueError("DT для алерта не найден")
            await session.execute(
                delete(AlertDtOrm).where(AlertDtOrm.id == dt_id)
            )
            return True
