"""
Репозиторий для работы с паузами алертов.
Содержит асинхронные методы доступа к данным для таблицы pause_history.
"""

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone, tzinfo
from typing import Any, TypeVar, cast
from uuid import UUID

from models.alerts import AlertOrm, PauseHistoryOrm
from sqlalchemy import and_, delete, desc, func, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_db import async_session_scope, get_db_timezone

_R = TypeVar("_R")
_UNSET = object()


async def _run_with_session(
    session: AsyncSession | None,
    work: Callable[[AsyncSession], Awaitable[_R]],
) -> _R:
    if session is not None:
        return await work(session)
    async with async_session_scope() as s:
        return await work(s)


class PausesRepository:
    """Репозиторий для работы с паузами алертов."""

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

    @staticmethod
    def _pause_filter(alert_id: UUID, filter_type: str) -> Any:
        now = func.now()
        conditions: list[Any] = [PauseHistoryOrm.alert == alert_id]
        if filter_type == "active":
            conditions.append(
                and_(
                    PauseHistoryOrm.start_time <= now,
                    or_(
                        PauseHistoryOrm.end_time.is_(None),
                        PauseHistoryOrm.end_time >= now,
                    ),
                )
            )
        elif filter_type == "future":
            conditions.append(
                and_(
                    PauseHistoryOrm.start_time > now,
                    or_(
                        PauseHistoryOrm.end_time.is_(None),
                        PauseHistoryOrm.end_time > PauseHistoryOrm.start_time,
                    ),
                )
            )
        elif filter_type == "past":
            conditions.append(
                and_(
                    PauseHistoryOrm.end_time.is_not(None),
                    PauseHistoryOrm.end_time < now,
                )
            )
        return and_(*conditions)

    @staticmethod
    def _pause_row_to_db_tz(row: Any, db_tz: tzinfo) -> dict[str, Any]:
        """Поля времени из строки выборки - в таймзоне БД (для API)."""
        d = dict(row._mapping)
        start = d.get("start_time")
        end = d.get("end_time")
        if isinstance(start, datetime):
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            d["start_time"] = start.astimezone(db_tz)
        if isinstance(end, datetime):
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            d["end_time"] = end.astimezone(db_tz)
        return d

    async def get_pauses(
        self,
        alert_id: UUID,
        filter_type: str = "all",
        order_by: str = "start_time",
        order_dir: str = "desc",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Any], int]:
        """
        Получить паузы алерта с фильтрацией, сортировкой и пагинацией.

        Args:
            alert_id: ID алерта
            filter_type: Тип фильтрации (all, active, future, past)
            order_by: Поле сортировки
            order_dir: Направление сортировки
            limit: Количество записей
            offset: Смещение

        Returns:
            tuple[list[dict[str, Any]], int]: список словарей полей паузы (время в таймзоне БД), общее число записей.
        """
        filt = self._pause_filter(alert_id, filter_type)

        allowed_fields = {
            "start_time": PauseHistoryOrm.start_time,
            "end_time": PauseHistoryOrm.end_time,
            "start_user": PauseHistoryOrm.start_user,
            "end_user": PauseHistoryOrm.end_user,
        }
        order_col = allowed_fields[order_by]
        order_direction = order_dir.lower()

        base_cols = (
            PauseHistoryOrm.id,
            PauseHistoryOrm.start_time,
            PauseHistoryOrm.end_time,
            PauseHistoryOrm.start_user,
            PauseHistoryOrm.end_user,
            PauseHistoryOrm.comment,
        )
        data_stmt = select(*base_cols).where(filt)
        if order_direction == "desc":
            data_stmt = data_stmt.order_by(desc(order_col))
        else:
            data_stmt = data_stmt.order_by(order_col)
        data_stmt = data_stmt.limit(limit).offset(offset)

        count_stmt = (
            select(func.count()).select_from(PauseHistoryOrm).where(filt)
        )

        async with async_session_scope() as session:
            total = int((await session.execute(count_stmt)).scalar_one())
            rows = (await session.execute(data_stmt)).all()

        if not rows:
            return [], total

        db_tz = await get_db_timezone()
        mapped = [self._pause_row_to_db_tz(r, db_tz) for r in rows]
        return mapped, total

    async def create_pause(
        self,
        alert_id: UUID,
        login: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        use_now_for_start: bool = False,
        comment: str | None = None,
    ) -> UUID:
        """
        Создать паузу алерта.

        Args:
            alert_id: ID алерта
            login: Логин пользователя
            start_time: Время начала (если None и use_now_for_start=False, БД установит DEFAULT)
            end_time: Время окончания (если None, пауза бессрочная)
            use_now_for_start: Если True, использует now() в SQL для start_time

        Returns:
            UUID: ID созданной паузы
        """
        async with async_session_scope() as session:
            locked = (
                await session.execute(
                    select(AlertOrm.id)
                    .where(AlertOrm.id == alert_id)
                    .with_for_update()
                )
            ).scalar_one_or_none()
            if locked is None:
                raise ValueError("Алерт не найден")

            values: dict[str, Any] = {"alert": alert_id, "start_user": login}
            if use_now_for_start:
                values["start_time"] = func.now()
            elif start_time is not None:
                values["start_time"] = start_time

            if end_time is not None:
                values["end_time"] = end_time
                values["end_user"] = login
            if comment is not None:
                values["comment"] = comment

            stmt = (
                insert(PauseHistoryOrm)
                .values(**values)
                .returning(PauseHistoryOrm.id)
            )
            res = await session.execute(stmt)
            return cast("UUID", res.scalar_one())

    async def stop_all_active_pauses(
        self,
        alert_id: UUID,
        login: str,
        comment: Any = _UNSET,
        session: AsyncSession | None = None,
    ) -> int:
        """
        Остановить все активные паузы алерта.

        Args:
            alert_id: ID алерта
            login: Логин пользователя

        Returns:
            int: Количество остановленных пауз
        """

        async def _work(s: AsyncSession) -> int:
            values_to_set: dict[str, Any] = {
                "end_time": func.now(),
                "end_user": login,
            }
            if comment is not _UNSET:
                values_to_set["comment"] = comment
            result = await s.execute(
                update(PauseHistoryOrm)
                .where(
                    and_(
                        PauseHistoryOrm.alert == alert_id,
                        PauseHistoryOrm.start_time <= func.now(),
                        (
                            (PauseHistoryOrm.end_time.is_(None))
                            | (PauseHistoryOrm.end_time >= func.now())
                        ),
                    )
                )
                .values(**values_to_set)
            )
            rowcount = getattr(result, "rowcount", None)
            return int(rowcount or 0)

        return await _run_with_session(session, _work)

    async def get_pause_by_id(
        self,
        pause_id: UUID,
        alert_id: UUID,
        session: AsyncSession | None = None,
    ) -> Any | None:
        """
        Получить паузу по ID.

        Args:
            pause_id: ID паузы
            alert_id: ID алерта

        Returns:
            Optional[Any]: Данные паузы или None
        """
        stmt = select(
            PauseHistoryOrm.id,
            PauseHistoryOrm.start_time,
            PauseHistoryOrm.end_time,
            PauseHistoryOrm.start_user,
            PauseHistoryOrm.end_user,
            PauseHistoryOrm.comment,
        ).where(
            PauseHistoryOrm.id == pause_id, PauseHistoryOrm.alert == alert_id
        )

        async def _work(s: AsyncSession) -> Any | None:
            return (await s.execute(stmt)).one_or_none()

        return await _run_with_session(session, _work)

    async def update_pause(
        self,
        pause_id: UUID,
        alert_id: UUID,
        start_time: datetime | None = None,
        use_now_for_start: bool = False,
        end_time: datetime | None = None,
        end_time_set_to_none: bool = False,
        login: str | None = None,
        comment: Any = _UNSET,
    ) -> bool:
        """
        Обновить паузу.

        Args:
            pause_id: ID паузы
            alert_id: ID алерта
            start_time: Время начала (если указано)
            use_now_for_start: Если True, использует now() в SQL для start_time
            end_time: Время окончания (если указано)
            end_time_set_to_none: Если True, устанавливает end_time = NULL
            login: Логин пользователя (для start_user и end_user)

        Returns:
            bool: True при успехе

        Raises:
            ValueError: Если пауза не найдена
        """
        async with async_session_scope() as session:
            pause_obj = (
                await session.execute(
                    select(PauseHistoryOrm).where(
                        PauseHistoryOrm.id == pause_id,
                        PauseHistoryOrm.alert == alert_id,
                    )
                )
            ).scalar_one_or_none()
            if pause_obj is None:
                raise ValueError("Пауза не найдена")

            if use_now_for_start:
                pause_obj.start_time = datetime.now(timezone.utc)
                if login:
                    pause_obj.start_user = login
            elif start_time is not None:
                pause_obj.start_time = start_time
                if login:
                    pause_obj.start_user = login

            if end_time_set_to_none:
                pause_obj.end_time = None
                pause_obj.end_user = None
            elif end_time is not None:
                pause_obj.end_time = end_time
                if login:
                    pause_obj.end_user = login
            if comment is not _UNSET:
                pause_obj.comment = comment

            return True

    async def stop_specific_pause(
        self,
        pause_id: UUID,
        alert_id: UUID,
        login: str,
        comment: Any = _UNSET,
    ) -> bool:
        """
        Остановить конкретную паузу.

        Args:
            pause_id: ID паузы
            alert_id: ID алерта
            login: Логин пользователя

        Returns:
            bool: True при успехе
        """
        async with async_session_scope() as session:
            pause_obj = (
                await session.execute(
                    select(PauseHistoryOrm).where(
                        PauseHistoryOrm.id == pause_id,
                        PauseHistoryOrm.alert == alert_id,
                    )
                )
            ).scalar_one_or_none()
            if pause_obj is None:
                raise ValueError("Пауза не найдена")

            start_time = pause_obj.start_time
            end_time = pause_obj.end_time
            now = datetime.now(timezone.utc)

            if isinstance(start_time, datetime) and start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if (
                end_time is not None
                and isinstance(end_time, datetime)
                and end_time.tzinfo is None
            ):
                end_time = end_time.replace(tzinfo=timezone.utc)

            if end_time is not None and end_time < now:
                raise ValueError("Пауза уже завершена")

            if start_time > now:
                pause_obj.end_time = pause_obj.start_time
            else:
                # Используем время БД, чтобы избежать гонки/рассинхрона с проверкой paused через now() в SQL.
                pause_obj.end_time = func.now()
            pause_obj.end_user = login
            if comment is not _UNSET:
                pause_obj.comment = comment

            return True

    async def delete_pause(
        self,
        pause_id: UUID,
        alert_id: UUID,
        session: AsyncSession | None = None,
    ) -> bool:
        """
        Удалить паузу.

        Args:
            pause_id: ID паузы
            alert_id: ID алерта

        Returns:
            bool: True при успехе
        """

        async def _work(s: AsyncSession) -> bool:
            await s.execute(
                delete(PauseHistoryOrm).where(
                    PauseHistoryOrm.id == pause_id,
                    PauseHistoryOrm.alert == alert_id,
                )
            )
            return True

        return await _run_with_session(session, _work)

    async def toggle_alert_pause(
        self, alert_id: UUID, login: str, comment: str | None = None
    ) -> bool:
        """
        Переключение состояния паузы алерта (безусловная пауза).

        Логика работы:
        - Если алерт НЕ на паузе: создает новую запись в pause_history с start_user = login, end_user = NULL, end_time = NULL
        - Если алерт УЖЕ на паузе: закрывает все активные паузы, устанавливая end_user = login и end_time = now()

        Состояние паузы определяется по попаданию текущей даты в период хотя бы одной активной паузы
        (start_time <= now() AND (end_time IS NULL OR end_time >= now()))

        Args:
            alert_id: ID алерта
            login: Логин пользователя

        Returns:
            bool: True при успешном переключении

        Raises:
            ValueError: Если алерт не найден
        """
        async with async_session_scope() as session:
            alert_row = (
                await session.execute(
                    select(AlertOrm.id).where(AlertOrm.id == alert_id)
                )
            ).scalar_one_or_none()
            if alert_row is None:
                raise ValueError("Алерт не найден")

            active_stmt = (
                select(PauseHistoryOrm.id)
                .where(
                    PauseHistoryOrm.alert == alert_id,
                    PauseHistoryOrm.start_time <= func.now(),
                    or_(
                        PauseHistoryOrm.end_time.is_(None),
                        PauseHistoryOrm.end_time >= func.now(),
                    ),
                )
                .with_for_update()
            )
            active_ids = (await session.execute(active_stmt)).scalars().all()

            if active_ids:
                values_to_set: dict[str, Any] = {
                    "end_time": func.now(),
                    "end_user": login,
                }
                if comment is not None:
                    values_to_set["comment"] = comment
                await session.execute(
                    update(PauseHistoryOrm)
                    .where(
                        PauseHistoryOrm.alert == alert_id,
                        PauseHistoryOrm.start_time <= func.now(),
                        or_(
                            PauseHistoryOrm.end_time.is_(None),
                            PauseHistoryOrm.end_time >= func.now(),
                        ),
                    )
                    .values(**values_to_set)
                )
            else:
                values_to_insert: dict[str, Any] = {
                    "start_time": func.now(),
                    "start_user": login,
                    "alert": alert_id,
                }
                if comment is not None:
                    values_to_insert["comment"] = comment
                await session.execute(
                    insert(PauseHistoryOrm).values(**values_to_insert)
                )

            return True
