"""
Репозиторий для работы с подписками пользователей на алерты.
Содержит асинхронные методы доступа к данным для подписок.

Все методы принимают опциональный `session`: при передаче одной и той же сессии
из сервиса несколько вызовов попадают в одну транзакцию (см. `async_session_scope`).
"""

from collections.abc import Awaitable, Callable
from typing import Any, ClassVar, TypeVar, cast
from uuid import UUID

from models.alerts import (
    AlertContactOrm,
    AlertContactStatusOrm,
    AlertOrm,
    AlertStatusOrm,
    ContactOrm,
    RulesChangeStatusOrm,
)
from sqlalchemy import (
    MetaData,
    Table,
    and_,
    case,
    delete,
    func,
    insert,
    literal,
    or_,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_db import async_session_scope

_R = TypeVar("_R")


async def _run_with_session(
    session: AsyncSession | None,
    work: Callable[[AsyncSession], Awaitable[_R]],
) -> _R:
    if session is not None:
        return await work(session)
    async with async_session_scope() as s:
        return await work(s)


class SubscriptionsRepository:
    """Репозиторий для работы с подписками."""

    _TABLE_CACHE: ClassVar[dict[tuple[str, str], Table]] = {}

    @staticmethod
    def _escape_like(value: str) -> str:
        return (
            value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )

    @staticmethod
    def _row_to_dict(row: Any) -> dict[str, Any]:
        mapping = getattr(row, "_mapping", None)
        if mapping is not None:
            return dict(mapping)
        return dict(row)

    async def _get_reflected_table(
        self, session: AsyncSession, schema: str, table_name: str
    ) -> Table | None:
        """
        Получить отраженную SQLAlchemy Table с кешированием.
        В юнит-тестах (где сессия замокана) мягко возвращаем None.
        """
        cache_key = (schema, table_name)
        cached = self._TABLE_CACHE.get(cache_key)
        if cached is not None:
            return cached

        run_sync = getattr(session, "run_sync", None)
        if run_sync is None:
            raise RuntimeError(
                "SQLAlchemy reflection unavailable: session.run_sync is required"
            )

        def _reflect(sync_session) -> Table:
            bind = sync_session.get_bind()
            metadata = MetaData()
            return Table(
                table_name, metadata, schema=schema, autoload_with=bind
            )

        reflected = await run_sync(_reflect)
        if not isinstance(reflected, Table):
            raise RuntimeError(  # noqa: TRY004
                f"SQLAlchemy reflection failed for {schema}.{table_name}"
            )
        self._TABLE_CACHE[cache_key] = reflected
        return reflected

    async def check_alert_exists(
        self, alert_id: UUID, session: AsyncSession | None = None
    ) -> bool:
        """Проверить существование алерта."""

        async def _work(s: AsyncSession) -> bool:
            result = (
                await s.execute(
                    select(AlertOrm.id).where(AlertOrm.id == alert_id)
                )
            ).scalar_one_or_none()
            return result is not None

        return await _run_with_session(session, _work)

    async def check_user_exists(
        self, user_id: UUID, session: AsyncSession | None = None
    ) -> bool:
        """Проверить существование пользователя."""

        async def _work(s: AsyncSession) -> bool:
            result = (
                await s.execute(
                    select(ContactOrm.id).where(ContactOrm.id == user_id),
                )
            ).scalar_one_or_none()
            return result is not None

        return await _run_with_session(session, _work)

    async def check_subscription_exists(
        self,
        alert_id: UUID,
        user_id: UUID,
        session: AsyncSession | None = None,
    ) -> UUID | None:
        """Проверить существование подписки и вернуть её ID."""

        async def _work(s: AsyncSession) -> UUID | None:
            found = (
                await s.execute(
                    select(AlertContactOrm.id).where(
                        AlertContactOrm.alert == alert_id,
                        AlertContactOrm.contact == user_id,
                    )
                )
            ).scalar_one_or_none()
            return cast("UUID | None", found)

        return await _run_with_session(session, _work)

    async def get_user_data(
        self, user_id: UUID, session: AsyncSession | None = None
    ) -> Any | None:
        """Получить все данные пользователя из alerts.contacts."""

        async def _work(s: AsyncSession) -> Any | None:
            contacts_table = await self._get_reflected_table(
                s, "alerts", "contacts"
            )
            if contacts_table is None:
                raise RuntimeError(
                    "Не удалось получить таблицу alerts.contacts"
                )
            return (
                (
                    await s.execute(
                        select(contacts_table).where(
                            contacts_table.c.id == user_id
                        )
                    )
                )
                .mappings()
                .one_or_none()
            )

        return await _run_with_session(session, _work)

    async def get_alerts_contacts_columns(
        self, session: AsyncSession | None = None
    ) -> list[str]:
        """Получить список всех колонок из alerts.alerts_contacts (кроме id, alert, contact)."""

        async def _work(s: AsyncSession) -> list[str]:
            alerts_contacts_table = await self._get_reflected_table(
                s, "alerts", "alerts_contacts"
            )
            if alerts_contacts_table is None:
                raise RuntimeError(
                    "Не удалось получить таблицу alerts.alerts_contacts"
                )
            return [
                col.key
                for col in alerts_contacts_table.columns
                if col.key not in {"id", "alert", "contact"}
            ]

        return await _run_with_session(session, _work)

    async def get_user_columns(
        self, session: AsyncSession | None = None
    ) -> list[str]:
        """Получить список всех колонок из alerts.contacts."""

        async def _work(s: AsyncSession) -> list[str]:
            contacts_table = await self._get_reflected_table(
                s, "alerts", "contacts"
            )
            if contacts_table is None:
                raise RuntimeError(
                    "Не удалось получить таблицу alerts.contacts"
                )
            return list(contacts_table.columns.keys())

        return await _run_with_session(session, _work)

    async def create_subscription(
        self,
        alert_id: UUID,
        user_id: UUID,
        contacts_dict: dict[str, Any],
        session: AsyncSession | None = None,
    ) -> UUID:
        """Создать подписку."""

        async def _work(s: AsyncSession) -> UUID:
            alerts_contacts_table = await self._get_reflected_table(
                s, "alerts", "alerts_contacts"
            )
            if alerts_contacts_table is None:
                raise RuntimeError(
                    "Не удалось получить таблицу alerts.alerts_contacts"
                )
            insert_payload: dict[str, Any] = {
                "alert": alert_id,
                "contact": user_id,
            }
            for key, value in contacts_dict.items():
                if key in alerts_contacts_table.c:
                    insert_payload[key] = value
            result = await s.execute(
                insert(alerts_contacts_table)
                .values(**insert_payload)
                .returning(alerts_contacts_table.c.id)
            )
            return result.scalar_one()

        return await _run_with_session(session, _work)

    async def delete_subscription_statuses(
        self, subscription_id: UUID, session: AsyncSession | None = None
    ) -> int:
        """Удалить все статусы подписки."""

        async def _work(s: AsyncSession) -> int:
            result = await s.execute(
                delete(AlertContactStatusOrm).where(
                    AlertContactStatusOrm.alert_contact == subscription_id
                )
            )
            rowcount = getattr(result, "rowcount", None)
            return int(rowcount or 0)

        return await _run_with_session(session, _work)

    async def delete_subscription(
        self, subscription_id: UUID, session: AsyncSession | None = None
    ) -> bool:
        """Удалить подписку."""

        async def _work(s: AsyncSession) -> bool:
            await s.execute(
                delete(AlertContactOrm).where(
                    AlertContactOrm.id == subscription_id
                )
            )
            return True

        return await _run_with_session(session, _work)

    async def get_subscription_by_id(
        self, subscription_id: UUID, session: AsyncSession | None = None
    ) -> Any | None:
        """Получить подписку по ID."""

        async def _work(s: AsyncSession) -> Any | None:
            alerts_contacts_table = await self._get_reflected_table(
                s, "alerts", "alerts_contacts"
            )
            if alerts_contacts_table is None:
                raise RuntimeError(
                    "Не удалось получить таблицу alerts.alerts_contacts"
                )
            row = (
                await s.execute(
                    select(alerts_contacts_table).where(
                        alerts_contacts_table.c.id == subscription_id
                    )
                )
            ).mappings().one_or_none()
            return self._row_to_dict(row) if row is not None else None

        return await _run_with_session(session, _work)

    async def get_all_notification_statuses(
        self, session: AsyncSession | None = None
    ) -> list[Any]:
        """Получить все статусы с send_notification=true."""

        async def _work(s: AsyncSession) -> list[Any]:
            stmt = (
                select(AlertStatusOrm.id, AlertStatusOrm.status_name)
                .distinct()
                .join(
                    RulesChangeStatusOrm,
                    AlertStatusOrm.id
                    == RulesChangeStatusOrm.new_alert_status,
                )
                .where(RulesChangeStatusOrm.send_notification.is_(True))
                .order_by(AlertStatusOrm.id)
            )
            rows = (await s.execute(stmt)).mappings().all()
            return [self._row_to_dict(row) for row in rows]

        return await _run_with_session(session, _work)

    async def get_subscription_statuses(
        self, subscription_id: UUID, session: AsyncSession | None = None
    ) -> dict[UUID, int]:
        """Получить статусы подписки."""

        async def _work(s: AsyncSession) -> dict[UUID, int]:
            rows = (
                await s.execute(
                    select(
                        AlertContactStatusOrm.status,
                        AlertContactStatusOrm.repeat,
                    ).where(
                        AlertContactStatusOrm.alert_contact == subscription_id
                    )
                )
            ).all()
            result: dict[UUID, int] = {}
            for row in rows:
                mapping = row._mapping if hasattr(row, "_mapping") else row
                status = (
                    mapping["status"] if isinstance(mapping, dict) else row[0]
                )
                repeat = (
                    mapping["repeat"] if isinstance(mapping, dict) else row[1]
                )
                result[status] = repeat
            return result

        return await _run_with_session(session, _work)

    async def update_subscription_channels(
        self,
        subscription_id: UUID,
        update_fields: list[str],
        update_values: list[Any],
        session: AsyncSession | None = None,
    ) -> bool:
        """Обновить каналы уведомлений подписки."""
        if not update_fields:
            return True

        async def _work(s: AsyncSession) -> bool:
            alerts_contacts_table = await self._get_reflected_table(
                s, "alerts", "alerts_contacts"
            )
            if alerts_contacts_table is None:
                raise RuntimeError(
                    "Не удалось получить таблицу alerts.alerts_contacts"
                )
            payload: dict[str, Any] = {}
            for field, value in zip(update_fields, update_values, strict=True):
                if field in alerts_contacts_table.c:
                    payload[field] = value
            if payload:
                await s.execute(
                    update(alerts_contacts_table)
                    .where(alerts_contacts_table.c.id == subscription_id)
                    .values(**payload)
                )
            return True

        return await _run_with_session(session, _work)

    async def get_current_subscription_statuses(
        self, subscription_id: UUID, session: AsyncSession | None = None
    ) -> dict[UUID, UUID]:
        """Получить текущие статусы подписки (status_id -> status_record_id)."""

        async def _work(s: AsyncSession) -> dict[UUID, UUID]:
            rows = (
                await s.execute(
                    select(
                        AlertContactStatusOrm.status, AlertContactStatusOrm.id
                    ).where(
                        AlertContactStatusOrm.alert_contact == subscription_id
                    )
                )
            ).all()
            result: dict[UUID, UUID] = {}
            for row in rows:
                mapping = row._mapping if hasattr(row, "_mapping") else row
                status = (
                    mapping["status"] if isinstance(mapping, dict) else row[0]
                )
                status_id = (
                    mapping["id"] if isinstance(mapping, dict) else row[1]
                )
                result[status] = status_id
            return result

        return await _run_with_session(session, _work)

    async def update_subscription_status(
        self,
        status_record_id: UUID,
        repeat: int,
        session: AsyncSession | None = None,
    ) -> bool:
        """Обновить статус подписки."""

        async def _work(s: AsyncSession) -> bool:
            await s.execute(
                update(AlertContactStatusOrm)
                .where(AlertContactStatusOrm.id == status_record_id)
                .values(repeat=repeat)
            )
            return True

        return await _run_with_session(session, _work)

    async def create_subscription_status(
        self,
        subscription_id: UUID,
        status_id: UUID,
        repeat: int,
        session: AsyncSession | None = None,
    ) -> bool:
        """Создать статус подписки."""

        async def _work(s: AsyncSession) -> bool:
            await s.execute(
                insert(AlertContactStatusOrm).values(
                    alert_contact=subscription_id,
                    status=status_id,
                    repeat=repeat,
                )
            )
            return True

        return await _run_with_session(session, _work)

    async def delete_subscription_status(
        self, status_record_id: UUID, session: AsyncSession | None = None
    ) -> bool:
        """Удалить статус подписки."""

        async def _work(s: AsyncSession) -> bool:
            await s.execute(
                delete(AlertContactStatusOrm).where(
                    AlertContactStatusOrm.id == status_record_id
                )
            )
            return True

        return await _run_with_session(session, _work)

    async def get_alerts_by_user(
        self,
        user_id: UUID,
        order_by: str = "alert_name",
        order_dir: str = "asc",
        limit: int = 50,
        offset: int = 0,
        subscribed_only: bool = False,
        session: AsyncSession | None = None,
    ) -> tuple[list[Any], int]:
        """
        Получить список алертов с информацией о подписке пользователя.

        По умолчанию возвращает все алерты, отсортированные по alert_name.
        Для подписанных заполнены данные из alerts.alerts_contacts (каналы уведомлений),
        для неподписанных подписка NULL. Если `subscribed_only=True`, возвращаются
        только алерты, где подписка существует (alerts.alerts_contacts не NULL).
        """

        async def _work(s: AsyncSession) -> tuple[list[Any], int]:
            alerts_contacts_table = await self._get_reflected_table(
                s, "alerts", "alerts_contacts"
            )
            if alerts_contacts_table is None:
                raise RuntimeError(
                    "Не удалось получить таблицу alerts.alerts_contacts"
                )

            join_stmt = AlertOrm.__table__.outerjoin(
                alerts_contacts_table,
                and_(
                    alerts_contacts_table.c.alert == AlertOrm.id,
                    alerts_contacts_table.c.contact == user_id,
                ),
            )

            count_stmt = select(func.count()).select_from(join_stmt)
            data_stmt = select(
                AlertOrm.id.label("alert_id"),
                AlertOrm.alert_name,
                alerts_contacts_table.c.id.label("subscription_id"),
                alerts_contacts_table,
            ).select_from(join_stmt)

            if subscribed_only:
                cond = alerts_contacts_table.c.id.is_not(None)
                count_stmt = count_stmt.where(cond)
                data_stmt = data_stmt.where(cond)

            allowed_fields = {
                "alert_name": AlertOrm.alert_name,
                "created_at": AlertOrm.id,
            }
            order_col = allowed_fields.get(order_by, AlertOrm.alert_name)
            if str(order_dir).lower() == "desc":
                order_expr = order_col.desc()
            else:
                order_expr = order_col.asc()

            data_stmt = (
                data_stmt.order_by(order_expr).limit(limit).offset(offset)
            )
            total = int((await s.execute(count_stmt)).scalar_one())
            rows = (await s.execute(data_stmt)).mappings().all()
            return [self._row_to_dict(row) for row in rows], total

        return await _run_with_session(session, _work)

    async def get_subscription_users(
        self,
        alert_id: UUID,
        query: str | None = None,
        groups: bool | None = None,
        subscribed_only: bool = False,
        order_by: str = "samAccountName",
        order_dir: str = "asc",
        limit: int = 50,
        offset: int = 0,
        session: AsyncSession | None = None,
    ) -> tuple[list[Any], int]:
        """Получить список пользователей для подписок с пагинацией."""

        async def _work(s: AsyncSession) -> tuple[list[Any], int]:
            contacts_table = await self._get_reflected_table(
                s, "alerts", "contacts"
            )
            alerts_contacts_table = await self._get_reflected_table(
                s, "alerts", "alerts_contacts"
            )
            if contacts_table is None or alerts_contacts_table is None:
                raise RuntimeError(
                    "Не удалось получить таблицы alerts.contacts / alerts.alerts_contacts"
                )
            join_stmt = contacts_table.outerjoin(
                alerts_contacts_table,
                and_(
                    contacts_table.c.id == alerts_contacts_table.c.contact,
                    alerts_contacts_table.c.alert == alert_id,
                ),
            )

            conditions = []
            if query:
                escaped = f"%{self._escape_like(query)}%"
                email_col = (
                    contacts_table.c.email
                    if "email" in contacts_table.c
                    else literal("", type_=contacts_table.c.user_name.type)
                )
                conditions.append(
                    or_(
                        contacts_table.c.user_name.ilike(escaped, escape="\\"),
                        func.coalesce(email_col, "").ilike(
                            escaped, escape="\\"
                        ),
                    )
                )
            if groups is not None:
                conditions.append(contacts_table.c["group"] == groups)
            if subscribed_only:
                conditions.append(alerts_contacts_table.c.id.is_not(None))

            count_stmt = select(func.count()).select_from(join_stmt)
            data_stmt = select(
                contacts_table,
                case(
                    (alerts_contacts_table.c.id.is_not(None), True),
                    else_=False,
                ).label("is_subscribed"),
                alerts_contacts_table.c.id.label("subscription_id"),
            ).select_from(join_stmt)

            for condition in conditions:
                count_stmt = count_stmt.where(condition)
                data_stmt = data_stmt.where(condition)

            allowed_fields = {
                "user_id": contacts_table.c.id,
                "samAccountName": contacts_table.c.user_name,
                "email": (
                    contacts_table.c.email
                    if "email" in contacts_table.c
                    else contacts_table.c.user_name
                ),
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

            total = int((await s.execute(count_stmt)).scalar_one())
            rows = (await s.execute(data_stmt)).mappings().all()
            return [self._row_to_dict(row) for row in rows], total

        return await _run_with_session(session, _work)
