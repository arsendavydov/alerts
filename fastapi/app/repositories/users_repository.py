"""
Репозиторий для работы с пользователями.
Содержит асинхронные методы доступа к данным для пользователей.
"""

from typing import Any, ClassVar
from uuid import UUID

from models.alerts import (
    AlertContactOrm,
    AlertContactStatusOrm,
    ContactOrm,
    TelegramSprUserOrm,
)
from sqlalchemy import (
    MetaData,
    Table,
    delete,
    func,
    insert,
    or_,
    select,
    update,
)
from sqlalchemy_db import async_session_scope


class UsersRepository:
    """Репозиторий для работы с пользователями."""

    _TABLE_CACHE: ClassVar[dict[tuple[str, str], Table]] = {}

    @staticmethod
    def _escape_like(value: str) -> str:
        """Экранирование спецсимволов LIKE/ILIKE (совместимо с ESCAPE '\\\\' в PostgreSQL)."""
        return (
            value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )

    async def _get_reflected_table(
        self, session, schema: str, table_name: str
    ) -> Table | None:
        """Получить отраженную SQLAlchemy Table с кешем; в моках возвращает None."""
        cache_key = (schema, table_name)
        cached = self._TABLE_CACHE.get(cache_key)
        if cached is not None:
            return cached

        run_sync = getattr(session, "run_sync", None)
        if run_sync is None:
            raise RuntimeError(
                "SQLAlchemy reflection unavailable: session.run_sync is required"
            )

        def _reflect(sync_session):
            bind = sync_session.get_bind()
            metadata = MetaData()
            return Table(
                table_name, metadata, schema=schema, autoload_with=bind
            )

        table = await run_sync(_reflect)
        if not isinstance(table, Table):
            raise RuntimeError(  # noqa: TRY004
                f"SQLAlchemy reflection failed for {schema}.{table_name}"
            )
        self._TABLE_CACHE[cache_key] = table
        return table

    async def get_telegram_by_login(self, login: str) -> Any | None:
        """Получить Telegram ID по логину."""
        async with async_session_scope() as session:
            stmt = (
                select(
                    TelegramSprUserOrm.login_name,
                    TelegramSprUserOrm.telegram_user_id,
                )
                .where(
                    func.lower(TelegramSprUserOrm.login_name)
                    == func.lower(login)
                )
                .limit(1)
            )
            return (await session.execute(stmt)).mappings().first()

    async def check_user_exists(self, user_id: UUID) -> bool:
        """Проверить существование пользователя."""
        async with async_session_scope() as session:
            found = (
                await session.execute(
                    select(ContactOrm.id).where(ContactOrm.id == user_id)
                )
            ).scalar_one_or_none()
            return found is not None

    async def get_available_columns(self) -> list:
        """Получить список доступных колонок в таблице contacts."""
        async with async_session_scope() as session:
            contacts_table = await self._get_reflected_table(
                session, "alerts", "contacts"
            )
            if contacts_table is None:
                raise RuntimeError(
                    "Не удалось получить таблицу alerts.contacts"
                )
            return [
                col.key for col in contacts_table.columns if col.key != "id"
            ]

    async def create_user(self, fields: list, values: list) -> UUID:
        """Создать пользователя."""
        if len(fields) != len(values):
            raise ValueError("fields и values должны совпадать по длине")
        async with async_session_scope() as session:
            contacts_table = await self._get_reflected_table(
                session, "alerts", "contacts"
            )
            if contacts_table is None:
                raise RuntimeError(
                    "Не удалось получить таблицу alerts.contacts"
                )
            payload: dict[str, Any] = {}
            for field, value in zip(fields, values, strict=True):
                if field in contacts_table.c:
                    payload[field] = value
            res = await session.execute(
                insert(contacts_table)
                .values(**payload)
                .returning(contacts_table.c.id)
            )
            return res.scalar_one()

    async def update_user(
        self, user_id: UUID, fields: list, values: list
    ) -> bool:
        """Обновить пользователя."""
        if not fields:
            return True
        if len(fields) != len(values):
            raise ValueError("fields и values должны совпадать по длине")
        async with async_session_scope() as session:
            contacts_table = await self._get_reflected_table(
                session, "alerts", "contacts"
            )
            if contacts_table is None:
                raise RuntimeError(
                    "Не удалось получить таблицу alerts.contacts"
                )
            payload: dict[str, Any] = {}
            for field, val in zip(fields, values, strict=True):
                if field in contacts_table.c:
                    payload[field] = val
            if payload:
                await session.execute(
                    update(contacts_table)
                    .where(contacts_table.c.id == user_id)
                    .values(**payload)
                )
        return True

    async def delete_user(self, user_id: UUID) -> bool:
        """Удалить пользователя."""
        async with async_session_scope() as session:
            subq = select(AlertContactOrm.id).where(
                AlertContactOrm.contact == user_id
            )
            await session.execute(
                delete(AlertContactStatusOrm).where(
                    AlertContactStatusOrm.alert_contact.in_(subq)
                )
            )
            await session.execute(
                delete(AlertContactOrm).where(
                    AlertContactOrm.contact == user_id
                )
            )
            await session.execute(
                delete(ContactOrm).where(ContactOrm.id == user_id)
            )
        return True

    async def search_users(
        self,
        query: str | None = None,
        groups: bool | None = None,
        order_by: str = "samAccountName",
        order_dir: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Any], int]:
        """
        Поиск пользователей для страницы 'Пользователи' с пагинацией и сортировкой.

        Поиск:
        - по user_name (samAccountName) ILIKE
        - по email ILIKE (если колонка есть)

        Фильтрация:
        - по "group" (True - только группы, False - только обычные пользователи)
        """
        async with async_session_scope() as session:
            contacts_table = await self._get_reflected_table(
                session, "alerts", "contacts"
            )
            if contacts_table is None:
                raise RuntimeError(
                    "Не удалось получить таблицу alerts.contacts"
                )

            conditions = []
            if query:
                query_param = f"%{self._escape_like(query)}%"
                conditions.append(
                    or_(
                        contacts_table.c.user_name.ilike(
                            query_param, escape="\\"
                        ),
                        func.coalesce(contacts_table.c.email, "").ilike(
                            query_param, escape="\\"
                        ),
                    )
                )
            if groups is not None:
                conditions.append(contacts_table.c["group"] == groups)

            count_stmt = select(func.count()).select_from(contacts_table)
            data_stmt = select(contacts_table)
            for condition in conditions:
                count_stmt = count_stmt.where(condition)
                data_stmt = data_stmt.where(condition)

            allowed_fields = {
                "user_id": contacts_table.c.id,
                "samAccountName": contacts_table.c.user_name,
                "email": contacts_table.c.email,
            }
            order_field = allowed_fields.get(
                order_by, contacts_table.c.user_name
            )
            if str(order_dir).lower() == "desc":
                order_expr = order_field.desc()
            else:
                order_expr = order_field.asc()
            data_stmt = (
                data_stmt.order_by(order_expr).limit(limit).offset(offset)
            )

            total = int((await session.execute(count_stmt)).scalar_one())
            rows = list((await session.execute(data_stmt)).mappings().all())
            return rows, total
