"""
Репозиторий для работы с алертами.
Содержит асинхронные методы доступа к данным для таблицы alerts.
"""

import inspect
import json
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar
from typing import cast as t_cast
from uuid import UUID

from models.alerts import AlertOrm, GroupRuleOrm
from models.dictionary import EventOrm
from sqlalchemy import (
    and_,
    asc,
    case,
    cast,
    delete,
    desc,
    func,
    insert,
    or_,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_db import async_session_scope

from utils import log

_R = TypeVar("_R")


async def _run_with_session(
    session: AsyncSession | None,
    work: Callable[[AsyncSession], Awaitable[_R]],
) -> _R:
    if session is not None:
        return await work(session)
    async with async_session_scope() as s:
        return await work(s)


class AlertsRepository:
    """Репозиторий для работы с алертами."""

    @staticmethod
    def _escape_like(value: str) -> str:
        return (
            value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )

    async def search_alerts(
        self,
        query: str | None = None,
        tags: str | None = None,
        order_by: str = "alert_name",
        order_dir: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
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
            Tuple[List[Tuple], int]: (список строк результатов, общее количество)
        """
        from models.alerts import PauseHistoryOrm, StatusHistoryOrm

        allowed_fields = {
            "alert_name": AlertOrm.alert_name,
            "indicator_name": EventOrm.event_name,
            "alert_description": AlertOrm.description,
            "indicator_description": EventOrm.description,
            "status_id": None,  # проставляется через subquery ниже
            "paused": None,  # проставляется через case ниже
        }

        active_pause_subquery = (
            select(PauseHistoryOrm.alert)
            .where(
                and_(
                    PauseHistoryOrm.start_time <= func.now(),
                    or_(
                        PauseHistoryOrm.end_time.is_(None),
                        PauseHistoryOrm.end_time >= func.now(),
                    ),
                )
            )
            .distinct()
            .subquery()
        )

        latest_status_subquery = select(
            StatusHistoryOrm.alert_id.label("alert_id"),
            StatusHistoryOrm.status_id.label("status_id"),
            func.row_number()
            .over(
                partition_by=StatusHistoryOrm.alert_id,
                order_by=StatusHistoryOrm.create_date.desc(),
            )
            .label("rn"),
        ).subquery()

        paused_expr = case(
            (active_pause_subquery.c.alert.is_not(None), True),
            else_=False,
        ).label("paused")
        status_expr = latest_status_subquery.c.status_id.label("status_id")

        async def _run_search(
            *, use_wildcards: bool
        ) -> tuple[list[dict[str, Any]], int]:
            stmt = (
                select(
                    AlertOrm.id,
                    AlertOrm.alert_name,
                    AlertOrm.description.label("alert_description"),
                    EventOrm.event_name.label("indicator_name"),
                    EventOrm.description.label("indicator_description"),
                    status_expr,
                    paused_expr,
                    AlertOrm.tags,
                )
                .join(EventOrm, AlertOrm.event == EventOrm.id)
                .outerjoin(
                    active_pause_subquery,
                    AlertOrm.id == active_pause_subquery.c.alert,
                )
                .outerjoin(
                    latest_status_subquery,
                    and_(
                        latest_status_subquery.c.alert_id == AlertOrm.id,
                        latest_status_subquery.c.rn == 1,
                    ),
                )
            )

            if query:
                if use_wildcards:
                    q_start = f"{query}%"
                    q_any = f"%{query}%"
                    stmt = stmt.where(
                        or_(
                            AlertOrm.alert_name.ilike(q_start),
                            AlertOrm.alert_name.ilike(q_any),
                        )
                    )
                    rank_case = case(
                        (
                            func.lower(AlertOrm.alert_name)
                            == func.lower(query),
                            0,
                        ),
                        (AlertOrm.alert_name.ilike(q_start), 1),
                        (AlertOrm.alert_name.ilike(q_any), 2),
                        else_=3,
                    )
                else:
                    q_escaped = self._escape_like(query)
                    q_start = f"{q_escaped}%"
                    q_any = f"%{q_escaped}%"
                    stmt = stmt.where(
                        or_(
                            AlertOrm.alert_name.ilike(q_start, escape="\\"),
                            AlertOrm.alert_name.ilike(q_any, escape="\\"),
                        )
                    )
                    rank_case = case(
                        (
                            func.lower(AlertOrm.alert_name)
                            == func.lower(query),
                            0,
                        ),
                        (AlertOrm.alert_name.ilike(q_start, escape="\\"), 1),
                        (AlertOrm.alert_name.ilike(q_any, escape="\\"), 2),
                        else_=3,
                    )
                stmt = stmt.order_by(rank_case)

            if tags:
                tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                for tag in tag_list:
                    stmt = stmt.where(
                        cast(AlertOrm.tags, JSONB).contains([tag])
                    )

            sort_column = allowed_fields.get(order_by)
            if order_by == "status_id":
                sort_column = status_expr
            elif order_by == "paused":
                sort_column = paused_expr
            if sort_column is None:
                sort_column = AlertOrm.alert_name

            if order_dir.lower() == "desc":
                stmt = stmt.order_by(desc(sort_column))
            else:
                stmt = stmt.order_by(asc(sort_column))

            count_stmt = select(func.count()).select_from(stmt.subquery())
            data_stmt = stmt.limit(limit).offset(offset)

            async with async_session_scope() as session:
                total = int((await session.execute(count_stmt)).scalar_one())
                rows = (await session.execute(data_stmt)).mappings().all()
            return [dict(row) for row in rows], total

        rows, total = await _run_search(use_wildcards=False)

        # Фоллбек для "шаблонного" поиска:
        # если query содержит '_'/'%' и буквальный (экранированный) поиск дал 0 результатов,
        # выполняем второй проход как шаблон (поведение, ожидаемое фронтом).
        if query and total == 0 and ("_" in query or "%" in query):
            return await _run_search(use_wildcards=True)

        return rows, total

    async def get_alert_by_id(
        self, alert_id: UUID, session: AsyncSession | None = None
    ) -> Any | None:
        """
        Получить алерт по ID.

        Args:
            alert_id: ID алерта

        Returns:
            Optional[Tuple]: Данные алерта или None
        """
        from models.alerts import PauseHistoryOrm

        active_pause_subquery = (
            select(PauseHistoryOrm.alert)
            .where(
                and_(
                    PauseHistoryOrm.start_time <= func.now(),
                    or_(
                        PauseHistoryOrm.end_time.is_(None),
                        PauseHistoryOrm.end_time >= func.now(),
                    ),
                )
            )
            .distinct()
            .subquery()
        )

        stmt = (
            select(
                AlertOrm.id,
                AlertOrm.alert_name,
                AlertOrm.event,
                EventOrm.event_name,
                AlertOrm.description.label("alert_description"),
                AlertOrm.image.label("alert_image"),
                AlertOrm.tags,
                AlertOrm.group_rules,
                GroupRuleOrm.description.label("group_rule_description"),
                GroupRuleOrm.image.label("group_rule_image"),
                AlertOrm.silence_time,
                case(
                    (active_pause_subquery.c.alert.is_not(None), True),
                    else_=False,
                ).label("paused"),
            )
            .outerjoin(EventOrm, AlertOrm.event == EventOrm.id)
            .outerjoin(GroupRuleOrm, AlertOrm.group_rules == GroupRuleOrm.id)
            .outerjoin(
                active_pause_subquery,
                AlertOrm.id == active_pause_subquery.c.alert,
            )
            .where(AlertOrm.id == alert_id)
        )

        async def _work(s: AsyncSession) -> Any | None:
            row = (await s.execute(stmt)).mappings().one_or_none()
            return dict(row) if row is not None else None

        return await _run_with_session(session, _work)

    async def check_alert_exists_by_name(
        self, alert_name: str, session: AsyncSession | None = None
    ) -> bool:
        """
        Проверить существование алерта по имени.

        Args:
            alert_name: Имя алерта

        Returns:
            bool: True если алерт существует
        """

        async def _work(s: AsyncSession) -> bool:
            aid = (
                await s.execute(
                    select(AlertOrm.id).where(
                        AlertOrm.alert_name == alert_name
                    )
                )
            ).scalar_one_or_none()
            return aid is not None

        return await _run_with_session(session, _work)

    async def check_alert_exists_by_id(
        self, alert_id: UUID, session: AsyncSession | None = None
    ) -> bool:
        """
        Проверить существование алерта по ID.

        Args:
            alert_id: ID алерта

        Returns:
            bool: True если алерт существует
        """

        async def _work(s: AsyncSession) -> bool:
            row_id = (
                await s.execute(
                    select(AlertOrm.id).where(AlertOrm.id == alert_id)
                )
            ).scalar_one_or_none()
            return row_id is not None

        return await _run_with_session(session, _work)

    async def create_alert(
        self,
        alert_name: str,
        indicator_id: UUID,
        description: str | None,
        image: str | None,
        tags: list[str] | None,
        group_rule_id: UUID,
        silence_time: str | None,
        session: AsyncSession | None = None,
    ) -> UUID:
        """
        Создать новый алерт.

        Args:
            alert_name: Имя алерта
            indicator_id: ID индикатора
            description: Описание
            image: Изображение
            tags: Теги
            group_rule_id: ID группы правил
            silence_time: Время тишины (JSON строка)

        Returns:
            UUID: ID созданного алерта
        """

        async def _work(s: AsyncSession) -> UUID:
            result = await s.execute(
                insert(AlertOrm)
                .values(
                    alert_name=alert_name,
                    event=indicator_id,
                    description=description if description is not None else "",
                    image=image if image is not None else "",
                    tags=json.dumps(tags) if tags else None,
                    group_rules=group_rule_id,
                    silence_time=silence_time,
                )
                .returning(AlertOrm.id)
            )
            aid = result.scalar_one_or_none()
            if inspect.isawaitable(aid):
                aid = await aid
            if aid is None:
                raise ValueError("Не удалось создать алерт")
            try:
                return UUID(str(aid))
            except (TypeError, ValueError) as exc:
                raise ValueError("Не удалось создать алерт") from exc

        return await _run_with_session(session, _work)

    async def update_alert(
        self,
        alert_id: UUID,
        alert_name: str | None = None,
        indicator_id: UUID | None = None,
        description: str | None = None,
        image: str | None = None,
        tags: list[str] | None = None,
        group_rule_id: UUID | None = None,
        silence_time: str | None = None,
        session: AsyncSession | None = None,
    ) -> bool:
        """
        Обновить алерт.

        Args:
            alert_id: ID алерта
            alert_name: Имя алерта
            indicator_id: ID индикатора
            description: Описание
            image: Изображение
            tags: Теги
            group_rule_id: ID группы правил
            silence_time: Время тишины (JSON строка)

        Returns:
            bool: True при успехе
        """

        async def _work(s: AsyncSession) -> bool:
            orm_obj = await s.get(AlertOrm, alert_id)
            if orm_obj is None:
                return True
            if alert_name is not None:
                orm_obj.alert_name = alert_name
            if indicator_id is not None:
                orm_obj.event = indicator_id  # type: ignore[assignment]
            if description is not None:
                orm_obj.description = description
            if image is not None:
                orm_obj.image = image
            if tags is not None:
                orm_obj.tags = json.dumps(tags)
            if group_rule_id is not None:
                orm_obj.group_rules = group_rule_id  # type: ignore[assignment]
            if silence_time is not None:
                orm_obj.silence_time = (
                    None if silence_time == "" else silence_time
                )
            await s.flush()
            return True

        return await _run_with_session(session, _work)

    async def delete_alert(self, alert_id: UUID) -> bool:
        """
        Удалить алерт (простое удаление без каскада).

        Args:
            alert_id: ID алерта

        Returns:
            bool: True при успехе
        """
        async with async_session_scope() as session:
            orm_obj = await session.get(AlertOrm, alert_id)
            if orm_obj is not None:
                await session.delete(orm_obj)
        return True

    async def delete_alert_with_cascade(
        self, alert_id: UUID, session: AsyncSession | None = None
    ) -> bool:
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
            bool: True при успехе
        """
        from models.alerts import (
            AlertContactOrm,
            AlertContactStatusOrm,
            AlertDtOrm,
            AlertLinkOrm,
            PauseHistoryOrm,
        )

        async def _work(s: AsyncSession) -> bool:
            contacts_subquery = select(AlertContactOrm.id).where(
                AlertContactOrm.alert == alert_id
            )

            await s.execute(
                delete(AlertContactStatusOrm).where(
                    AlertContactStatusOrm.alert_contact.in_(contacts_subquery)
                )
            )
            log.info(f"Deleted status records for alert {alert_id}")

            await s.execute(
                delete(AlertContactOrm).where(
                    AlertContactOrm.alert == alert_id
                )
            )
            log.info(f"Deleted subscriptions for alert {alert_id}")

            await s.execute(
                delete(AlertLinkOrm).where(AlertLinkOrm.alert == alert_id)
            )
            log.info(f"Deleted links for alert {alert_id}")

            await s.execute(
                delete(PauseHistoryOrm).where(
                    PauseHistoryOrm.alert == alert_id
                )
            )
            log.info(f"Deleted pause history records for alert {alert_id}")

            await s.execute(
                delete(AlertDtOrm).where(AlertDtOrm.alert == alert_id)
            )
            log.info(f"Deleted DT record(s) for alert {alert_id}")

            await s.execute(delete(AlertOrm).where(AlertOrm.id == alert_id))

            return True

        return await _run_with_session(session, _work)

    async def autocomplete_alerts(self, query: str | None, limit: int) -> list:
        """
        Автодополнение алертов.

        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов

        Returns:
            List: Список (id, alert_name)
        """

        async def _run_autocomplete(*, use_wildcards: bool) -> list:
            if not query:
                stmt = (
                    select(AlertOrm.id, AlertOrm.alert_name)
                    .order_by(AlertOrm.alert_name.asc())
                    .limit(limit)
                )
                async with async_session_scope() as session:
                    rows = (await session.execute(stmt)).mappings().all()
                return [dict(row) for row in rows]

            if use_wildcards:
                q_start_local = f"{query}%"
                q_any_local = f"%{query}%"
                rank_case = case(
                    (func.lower(AlertOrm.alert_name) == func.lower(query), 0),
                    (AlertOrm.alert_name.ilike(q_start_local), 1),
                    (AlertOrm.alert_name.ilike(q_any_local), 2),
                    else_=3,
                )
                stmt = (
                    select(AlertOrm.id, AlertOrm.alert_name)
                    .where(
                        or_(
                            AlertOrm.alert_name.ilike(q_start_local),
                            AlertOrm.alert_name.ilike(q_any_local),
                        )
                    )
                    .order_by(rank_case, AlertOrm.alert_name.asc())
                    .limit(limit)
                )
                async with async_session_scope() as session:
                    rows = (await session.execute(stmt)).mappings().all()
                return [dict(row) for row in rows]

            q_escaped_local = self._escape_like(query)
            q_start_local = f"{q_escaped_local}%"
            q_any_local = f"%{q_escaped_local}%"
            rank_case = case(
                (func.lower(AlertOrm.alert_name) == func.lower(query), 0),
                (AlertOrm.alert_name.ilike(q_start_local, escape="\\"), 1),
                (AlertOrm.alert_name.ilike(q_any_local, escape="\\"), 2),
                else_=3,
            )
            stmt = (
                select(AlertOrm.id, AlertOrm.alert_name)
                .where(
                    or_(
                        AlertOrm.alert_name.ilike(q_start_local, escape="\\"),
                        AlertOrm.alert_name.ilike(q_any_local, escape="\\"),
                    )
                )
                .order_by(rank_case, AlertOrm.alert_name.asc())
                .limit(limit)
            )
            async with async_session_scope() as session:
                rows = (await session.execute(stmt)).mappings().all()
            return [dict(row) for row in rows]

        results = await _run_autocomplete(use_wildcards=False)
        if query and not results and ("_" in query or "%" in query):
            return await _run_autocomplete(use_wildcards=True)
        return results

    async def get_tag_cloud(
        self, alert_name: str | None = None, tags: str | None = None
    ) -> list[str]:
        """
        Получить облако тегов.

        Если переданы фильтры по алертам (`alert_name` и/или `tags`), облако считается среди алертов,
        которые удовлетворяют фильтрам. При фильтрации по `tags` теги из фильтра исключаются
        из возвращаемого облака.

        Returns:
            List[str]: Список уникальных тегов
        """
        tag_list = None
        if tags:
            parsed = [t.strip() for t in tags.split(",") if t.strip()]
            tag_list = parsed if parsed else None

        async def _run(use_wildcards: bool) -> list[str]:
            stmt = select(AlertOrm.tags).where(
                AlertOrm.tags.is_not(None),
                AlertOrm.tags != "null",
                AlertOrm.tags != "[]",
            )
            if alert_name:
                if use_wildcards:
                    q_start_local = f"{alert_name}%"
                    q_any_local = f"%{alert_name}%"
                    stmt = stmt.where(
                        or_(
                            AlertOrm.alert_name.ilike(q_start_local),
                            AlertOrm.alert_name.ilike(q_any_local),
                        )
                    )
                else:
                    q_escaped_local = self._escape_like(alert_name)
                    q_start_local = f"{q_escaped_local}%"
                    q_any_local = f"%{q_escaped_local}%"
                    stmt = stmt.where(
                        or_(
                            AlertOrm.alert_name.ilike(
                                q_start_local, escape="\\"
                            ),
                            AlertOrm.alert_name.ilike(
                                q_any_local, escape="\\"
                            ),
                        )
                    )

            async with async_session_scope() as session:
                rows = (await session.execute(stmt)).all()

            result_tags: list[str] = []
            for row in rows:
                mapping = getattr(row, "_mapping", None)
                if mapping is not None:
                    tags_raw = dict(mapping).get("tags")
                else:
                    tags_raw = row[0]
                if not tags_raw:
                    continue
                try:
                    parsed_tags = (
                        json.loads(tags_raw)
                        if isinstance(tags_raw, str)
                        else tags_raw
                    )
                except (json.JSONDecodeError, TypeError):
                    continue
                if not isinstance(parsed_tags, list):
                    continue
                if tag_list and not all(
                    tag in parsed_tags for tag in tag_list
                ):
                    continue
                for tag in parsed_tags:
                    if isinstance(tag, str) and tag.strip():
                        result_tags.append(tag)

            unique_tags = sorted(set(result_tags))
            return unique_tags[:1000]

        tags_result = await _run(use_wildcards=False)

        # Если в запросе были wildcard-символы и буквальный поиск не дал результатов,
        # повторяем поиск как шаблон, чтобы сохранить поведение для фронта.
        if (
            alert_name
            and len(tags_result) == 0
            and ("_" in alert_name or "%" in alert_name)
        ):
            tags_result = await _run(use_wildcards=True)

        if tag_list:
            exclude = set(tag_list)
            tags_result = [t for t in tags_result if t not in exclude]

        return tags_result

    async def check_group_rule_exists(
        self, group_rule_id: UUID, session: AsyncSession | None = None
    ) -> bool:
        """
        Проверить существование группы правил.

        Args:
            group_rule_id: ID группы правил

        Returns:
            bool: True если группа правил существует
        """

        async def _work(s: AsyncSession) -> bool:
            row_id = (
                await s.execute(
                    select(GroupRuleOrm.id).where(
                        GroupRuleOrm.id == group_rule_id
                    )
                )
            ).scalar_one_or_none()
            return row_id is not None

        return await _run_with_session(session, _work)

    async def duplicate_alert(
        self, alert_id: UUID, session: AsyncSession | None = None
    ) -> UUID:
        """
        Дублировать алерт со всеми связанными данными.

        Копирует:
        - Сам алерт с новым именем "{старое_имя} copy - {дата_время}"
        - Линки (alerts.alerts_links)
        - Подписки (alerts.alerts_contacts) со всеми статусами (alerts.alerts_contacts_status)
        - DT (alerts.alerts_dt)

        Args:
            alert_id: ID исходного алерта

        Returns:
            UUID: ID нового алерта

        Raises:
            ValueError: Если исходный алерт не найден
        """
        from datetime import datetime
        from uuid import uuid4

        from models.alerts import (
            AlertContactOrm,
            AlertContactStatusOrm,
            AlertDtOrm,
            AlertLinkOrm,
        )

        async def _work(sess: AsyncSession) -> UUID:
            source_alert = await sess.get(AlertOrm, alert_id)
            if source_alert is None:
                raise ValueError("Алерт не найден")

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_alert_name = f"{source_alert.alert_name} copy - {timestamp}"

            existing_name_stmt = select(AlertOrm.id).where(
                AlertOrm.alert_name == new_alert_name
            )
            existing_name = (
                await sess.execute(existing_name_stmt)
            ).scalar_one_or_none()
            if existing_name:
                new_alert_name = f"{source_alert.alert_name} copy - {timestamp} - {uuid4().hex[:8]}"

            duplicated_alert = AlertOrm(
                alert_name=new_alert_name,
                event=source_alert.event,
                description=source_alert.description,
                image=source_alert.image,
                tags=source_alert.tags,
                group_rules=source_alert.group_rules,
                silence_time=source_alert.silence_time,
            )
            sess.add(duplicated_alert)
            await sess.flush()
            new_alert_id = duplicated_alert.id
            log.info(f"Created duplicate alert {new_alert_id} from {alert_id}")

            links_stmt = select(AlertLinkOrm).where(
                AlertLinkOrm.alert == alert_id
            )
            links = (await sess.execute(links_stmt)).scalars().all()
            for link in links:
                sess.add(
                    AlertLinkOrm(
                        alert=new_alert_id,
                        link_name=link.link_name,
                        link_url=link.link_url,
                    )
                )
            if links:
                log.info(f"Copied {len(links)} links to duplicate alert")

            subscriptions_stmt = select(AlertContactOrm).where(
                AlertContactOrm.alert == alert_id
            )
            subscriptions = (
                (await sess.execute(subscriptions_stmt)).scalars().all()
            )

            for old_subscription in subscriptions:
                contact_payload = {
                    col.name: getattr(old_subscription, col.name)
                    for col in AlertContactOrm.__table__.columns
                    if col.name not in {"id", "alert"}
                }
                new_subscription = AlertContactOrm(
                    alert=new_alert_id, **contact_payload
                )
                sess.add(new_subscription)
                await sess.flush()

                statuses_stmt = select(AlertContactStatusOrm).where(
                    AlertContactStatusOrm.alert_contact == old_subscription.id
                )
                statuses = (await sess.execute(statuses_stmt)).scalars().all()
                for status in statuses:
                    sess.add(
                        AlertContactStatusOrm(
                            alert_contact=new_subscription.id,
                            status=status.status,
                            repeat=status.repeat,
                        )
                    )

                if statuses:
                    log.info(
                        f"Copied subscription {new_subscription.id} with {len(statuses)} statuses"
                    )

            if subscriptions:
                log.info(
                    f"Copied {len(subscriptions)} subscriptions to duplicate alert"
                )

            dt_stmt = select(AlertDtOrm).where(AlertDtOrm.alert == alert_id)
            dt_row = (await sess.execute(dt_stmt)).scalar_one_or_none()
            if dt_row is not None:
                sess.add(
                    AlertDtOrm(
                        alert=new_alert_id,
                        content=dt_row.content,
                        auto_create=dt_row.auto_create,
                        silence_time=dt_row.silence_time,
                    )
                )
                log.info("Copied DT to duplicate alert")

            log.info(
                f"Successfully duplicated alert {alert_id} to {new_alert_id} with name '{new_alert_name}'"
            )
            return t_cast("UUID", new_alert_id)

        return await _run_with_session(session, _work)
