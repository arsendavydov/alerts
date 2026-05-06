"""
Репозиторий для работы с индикаторами.
Содержит асинхронные методы доступа к данным для индикаторов.
"""

from typing import Any

from models.dictionary import EventOrm
from sqlalchemy import case, func, select
from sqlalchemy_db import async_session_scope


class IndicatorsRepository:
    """Репозиторий для работы с индикаторами."""

    @staticmethod
    def _escape_like(value: str) -> str:
        """Экранирование спецсимволов LIKE/ILIKE (совместимо с ESCAPE '\\\\' в PostgreSQL)."""
        return (
            value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )

    async def autocomplete_indicators(
        self, query: str | None = None, limit: int = 10
    ) -> list[Any]:
        """Автодополнение индикаторов."""
        async with async_session_scope() as session:
            if query:
                q_escaped = self._escape_like(query)
                pattern_anywhere = f"%{q_escaped}%"
                pattern_start = f"{q_escaped}%"
                order_expr = case(
                    (func.lower(EventOrm.event_name) == func.lower(query), 0),
                    (EventOrm.event_name.ilike(pattern_start, escape="\\"), 1),
                    else_=2,
                )
                stmt = (
                    select(
                        EventOrm.id,
                        EventOrm.event_name.label("indicator_name"),
                    )
                    .where(
                        EventOrm.event_name.ilike(
                            pattern_anywhere, escape="\\"
                        )
                    )
                    .order_by(order_expr, EventOrm.event_name.asc())
                    .limit(limit)
                )
            else:
                stmt = (
                    select(
                        EventOrm.id,
                        EventOrm.event_name.label("indicator_name"),
                    )
                    .order_by(EventOrm.event_name.asc())
                    .limit(limit)
                )
            return list((await session.execute(stmt)).all())
