"""
Репозиторий для работы с линками алертов.
Содержит асинхронные методы доступа к данным для линков.
"""

from typing import Any, cast
from uuid import UUID

from models.alerts import AlertLinkOrm, AlertOrm
from sqlalchemy import delete, insert, select, update
from sqlalchemy_db import async_session_scope


class LinksRepository:
    """Репозиторий для работы с линками."""

    async def get_links_by_alert(self, alert_id: UUID) -> list[Any]:
        """Получить все линки алерта."""
        stmt = (
            select(
                AlertLinkOrm.id,
                AlertLinkOrm.alert,
                AlertLinkOrm.link_name,
                AlertLinkOrm.link_url,
            )
            .where(AlertLinkOrm.alert == alert_id)
            .order_by(AlertLinkOrm.link_name)
            .limit(100)
        )
        async with async_session_scope() as session:
            return list((await session.execute(stmt)).all())

    async def get_link_by_id(self, link_id: UUID) -> Any | None:
        """Получить линк по ID."""
        stmt = (
            select(
                AlertLinkOrm.id,
                AlertLinkOrm.alert,
                AlertOrm.alert_name,
                AlertLinkOrm.link_name,
                AlertLinkOrm.link_url,
            )
            .select_from(AlertLinkOrm)
            .outerjoin(AlertOrm, AlertLinkOrm.alert == AlertOrm.id)
            .where(AlertLinkOrm.id == link_id)
        )
        async with async_session_scope() as session:
            return (await session.execute(stmt)).one_or_none()

    async def create_link(
        self, alert_id: UUID, link_name: str, link_url: str
    ) -> UUID:
        """Создать линк."""
        stmt = (
            insert(AlertLinkOrm)
            .values(alert=alert_id, link_name=link_name, link_url=link_url)
            .returning(AlertLinkOrm.id)
        )
        async with async_session_scope() as session:
            res = await session.execute(stmt)
            return cast("UUID", res.scalar_one())

    async def update_link(
        self,
        link_id: UUID,
        link_name: str | None = None,
        link_url: str | None = None,
    ) -> bool:
        """Обновить линк."""
        if link_name is None and link_url is None:
            return True

        values: dict[str, Any] = {}
        if link_name is not None:
            values["link_name"] = link_name
        if link_url is not None:
            values["link_url"] = link_url

        async with async_session_scope() as session:
            await session.execute(
                update(AlertLinkOrm)
                .where(AlertLinkOrm.id == link_id)
                .values(**values)
            )
        return True

    async def delete_link(self, link_id: UUID) -> bool:
        """Удалить линк."""
        async with async_session_scope() as session:
            await session.execute(
                delete(AlertLinkOrm).where(AlertLinkOrm.id == link_id)
            )
        return True

    async def check_link_exists(self, link_id: UUID) -> bool:
        """Проверить существование линка."""
        stmt = select(AlertLinkOrm.id).where(AlertLinkOrm.id == link_id)
        async with async_session_scope() as session:
            found = (await session.execute(stmt)).scalar_one_or_none()
            return found is not None
