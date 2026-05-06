"""
Репозиторий для работы с группами правил.
Содержит асинхронные методы доступа к данным для групп правил.
"""

from typing import Any

from models.alerts import GroupRuleOrm
from sqlalchemy import func, select
from sqlalchemy_db import async_session_scope


class RulesRepository:
    """Репозиторий для работы с группами правил."""

    @staticmethod
    def _escape_like(value: str) -> str:
        """Экранирование спецсимволов LIKE/ILIKE (совместимо с ESCAPE '\\\\' в PostgreSQL)."""
        return (
            value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )

    async def search_group_rules(
        self, query: str | None = None, limit: int = 50
    ) -> tuple[list[Any], int]:
        """Поиск групп правил."""
        cap = min(limit, 50)
        async with async_session_scope() as session:
            data_stmt = select(
                GroupRuleOrm.id, GroupRuleOrm.description, GroupRuleOrm.image
            )
            count_stmt = select(func.count()).select_from(GroupRuleOrm)
            if query:
                pattern = f"{self._escape_like(query)}%"
                filt = GroupRuleOrm.description.ilike(pattern, escape="\\")
                data_stmt = data_stmt.where(filt)
                count_stmt = count_stmt.where(filt)
            data_stmt = data_stmt.order_by(
                GroupRuleOrm.description.asc()
            ).limit(cap)
            total = int((await session.execute(count_stmt)).scalar_one())
            rows = (await session.execute(data_stmt)).all()
            return list(rows), total
