"""
Репозиторий для работы со скриншотами.
Содержит асинхронные методы доступа к данным для таблицы dt_screenshot.
"""

from typing import Any, cast
from uuid import UUID

from models.alerts import DtScreenshotOrm
from sqlalchemy import delete, desc, func, insert, select, update
from sqlalchemy_db import async_session_scope


class ScreenshotsRepository:
    """Репозиторий для работы со скриншотами."""

    @staticmethod
    def _escape_like(value: str) -> str:
        """Экранирование спецсимволов LIKE/ILIKE (совместимо с ESCAPE '\\\\' в PostgreSQL)."""
        return (
            value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )

    async def search_screenshots(
        self,
        query: str | None = None,
        order_by: str = "description",
        order_dir: str = "asc",
        limit: int = 1000,
        offset: int = 0,
    ) -> tuple[list[Any], int]:
        """
        Поиск скриншотов по description с сортировкой и пагинацией.

        Args:
            query: Поисковый запрос по description (опциональный)
            order_by: Поле сортировки (description, name)
            order_dir: Направление сортировки (asc, desc)
            limit: Количество записей на странице
            offset: Смещение для пагинации

        Returns:
            Tuple[List[Any], int]: (список строк (id, name, description, image_data), общее количество)
        """
        allowed_fields = {
            "description": DtScreenshotOrm.description,
            "name": DtScreenshotOrm.name,
        }
        order_col = allowed_fields[order_by]
        dir_desc = str(order_dir).lower() == "desc"

        cols = (
            DtScreenshotOrm.id,
            DtScreenshotOrm.name,
            DtScreenshotOrm.description,
            DtScreenshotOrm.image_data,
        )
        if query:
            pattern = f"%{self._escape_like(query)}%"
            filt = DtScreenshotOrm.description.ilike(pattern, escape="\\")
            count_stmt = (
                select(func.count()).select_from(DtScreenshotOrm).where(filt)
            )
            data_stmt = select(*cols).where(filt)
        else:
            count_stmt = select(func.count()).select_from(DtScreenshotOrm)
            data_stmt = select(*cols)
        if dir_desc:
            data_stmt = data_stmt.order_by(desc(order_col))
        else:
            data_stmt = data_stmt.order_by(order_col)
        data_stmt = data_stmt.limit(limit).offset(offset)

        async with async_session_scope() as session:
            total = int((await session.execute(count_stmt)).scalar_one())
            rows = (await session.execute(data_stmt)).all()
            return list(rows), total

    async def get_screenshot_by_id(self, screenshot_id: UUID) -> Any | None:
        """Получить скриншот по ID."""
        stmt = select(
            DtScreenshotOrm.id,
            DtScreenshotOrm.name,
            DtScreenshotOrm.description,
            DtScreenshotOrm.image_data,
        ).where(DtScreenshotOrm.id == screenshot_id)
        async with async_session_scope() as session:
            return (await session.execute(stmt)).one_or_none()

    async def create_screenshot(
        self, name: str, description: str, image_data: str
    ) -> UUID:
        """Создать новый скриншот."""
        stmt = (
            insert(DtScreenshotOrm)
            .values(name=name, description=description, image_data=image_data)
            .returning(DtScreenshotOrm.id)
        )
        async with async_session_scope() as session:
            return cast("UUID", (await session.execute(stmt)).scalar_one())

    async def update_screenshot(
        self,
        screenshot_id: UUID,
        name: str | None = None,
        description: str | None = None,
        image_data: str | None = None,
    ) -> bool:
        """Обновить скриншот."""
        if name is None and description is None and image_data is None:
            return True

        values: dict[str, Any] = {}
        if name is not None:
            values["name"] = name
        if description is not None:
            values["description"] = description
        if image_data is not None:
            values["image_data"] = image_data

        async with async_session_scope() as session:
            await session.execute(
                update(DtScreenshotOrm)
                .where(DtScreenshotOrm.id == screenshot_id)
                .values(**values)
            )
        return True

    async def delete_screenshot(self, screenshot_id: UUID) -> bool:
        """Удалить скриншот."""
        async with async_session_scope() as session:
            await session.execute(
                delete(DtScreenshotOrm).where(
                    DtScreenshotOrm.id == screenshot_id
                )
            )
        return True

    async def check_screenshot_exists(self, screenshot_id: UUID) -> bool:
        """Проверить существование скриншота."""
        stmt = select(DtScreenshotOrm.id).where(
            DtScreenshotOrm.id == screenshot_id
        )
        async with async_session_scope() as session:
            return (
                await session.execute(stmt)
            ).scalar_one_or_none() is not None
